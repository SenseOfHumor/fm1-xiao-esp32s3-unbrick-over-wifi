// On-board TCP loopback test; does not join or change the Mac's Wi-Fi.
// This verifies actual firmware transport, not over-the-air Wi-Fi or USB
// timing.
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "mbedtls/sha256.h"
#include "net_transport.h"
#include "wire_protocol.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

static bool io(int fd, void *data, size_t n, bool send_it) {
  uint8_t *p = data;
  while (n) {
    int k = send_it ? send(fd, p, n, 0) : recv(fd, p, n, 0);
    if (k <= 0)
      return false;
    p += k;
    n -= k;
  }
  return true;
}
static bool send_frame(int fd, uint32_t seq, uint8_t *p, size_t n) {
  uint8_t h[16];
  fm1_frame_header(h, seq, p, n);
  // Deliberately split the header to exercise complete reads in the server.
  return io(fd, h, 3, true) && io(fd, h + 3, 13, true) && io(fd, p, n, true);
}
static bool receive(int fd, uint32_t seq, uint8_t *p, uint32_t *n) {
  uint8_t h[16];
  uint32_t crc;
  return io(fd, h, 16, false) && fm1_frame_parse(h, seq, n, &crc) &&
         io(fd, p, *n, false) && fm1_crc32(p, *n) == crc;
}
static int connect_local(void) {
  int fd = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
  struct timeval tv = {.tv_sec = 5};
  setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
  setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
  struct sockaddr_in a = {.sin_family = AF_INET,
                          .sin_port = htons(CONFIG_FM1_TCP_PORT),
                          .sin_addr.s_addr = htonl(INADDR_LOOPBACK)};
  if (fd < 0 || connect(fd, (void *)&a, sizeof(a))) {
    if (fd >= 0)
      close(fd);
    return -1;
  }
  return fd;
}
static bool authenticate(int fd, uint8_t *p) {
  uint32_t n;
  return send_frame(fd, 0, (uint8_t *)CONFIG_FM1_SESSION_SECRET,
                    strlen(CONFIG_FM1_SESSION_SECRET)) &&
         receive(fd, 0, p, &n) && n == 8 && !memcmp(p, "AUTH OK\n", 8);
}
static void selftest(void *arg) {
  (void)arg;
  vTaskDelay(pdMS_TO_TICKS(1500));
  bool ok = true;
  uint8_t *p = malloc(4096), *q = malloc(4096);
  int fd = -1;
  uint32_t n;
  if (!p || !q)
    ok = false;
  if (ok) {
    fd = connect_local();
    ok = fd >= 0 && authenticate(fd, q);
  }
  uint32_t tx = 1, rx = 1;
  const unsigned sizes[] = {64, 512, 4096, 65536, 1048576};
  for (unsigned i = 0; ok && i < sizeof(sizes) / sizeof(sizes[0]); i++) {
    mbedtls_sha256_context a, b;
    mbedtls_sha256_init(&a);
    mbedtls_sha256_init(&b);
    mbedtls_sha256_starts(&a, 0);
    mbedtls_sha256_starts(&b, 0);
    for (unsigned off = 0; ok && off < sizes[i];) {
      unsigned count = sizes[i] - off;
      if (count > 4095)
        count = 4095;
      p[0] = 0;
      for (unsigned k = 0; k < count; k++)
        p[k + 1] = (off + k) * 31u + i;
      mbedtls_sha256_update(&a, p + 1, count);
      ok = send_frame(fd, tx++, p, count + 1) && receive(fd, rx++, q, &n) &&
           n == count + 1 && !memcmp(p, q, n);
      if (ok)
        mbedtls_sha256_update(&b, q + 1, count);
      off += count;
    }
    uint8_t x[32], y[32];
    mbedtls_sha256_finish(&a, x);
    mbedtls_sha256_finish(&b, y);
    ok = ok && !memcmp(x, y, 32);
    mbedtls_sha256_free(&a);
    mbedtls_sha256_free(&b);
    printf("SELFTEST loopback %u SHA256 %s ", sizes[i], ok ? "PASS" : "FAIL");
    for (int k = 0; k < 32; k++) {
      printf("%02x", x[k]);
    }
    printf("\n");
  }
  if (fd >= 0)
    close(fd);
  if (ok) {
    fd = connect_local();
    ok = fd >= 0 && authenticate(fd, q) &&
         send_frame(fd, 1, (uint8_t *)"ping\n", 5) && receive(fd, 1, q, &n) &&
         n == 5 && !memcmp(q, "PONG\n", 5);
    if (fd >= 0) {
      close(fd);
    }
    printf("SELFTEST reconnect + ping %s\n", ok ? "PASS" : "FAIL");
  }
  if (ok) {
    fd = connect_local();
    uint8_t bad[] = "incorrect secret";
    ok = fd >= 0 && send_frame(fd, 0, bad, sizeof(bad) - 1) &&
         recv(fd, q, 1, 0) == 0;
    if (fd >= 0) {
      close(fd);
    }
    printf("SELFTEST authentication rejection %s\n", ok ? "PASS" : "FAIL");
  }
  if (ok) {
    fd = connect_local();
    ok = fd >= 0 && authenticate(fd, q);
    uint8_t h[16];
    p[0] = 0;
    fm1_frame_header(h, 1, p, 1);
    h[15] ^= 1;
    ok = ok && io(fd, h, 16, true) && io(fd, p, 1, true) &&
         recv(fd, q, 1, 0) == 0;
    if (fd >= 0) {
      close(fd);
    }
    printf("SELFTEST CRC rejection %s\n", ok ? "PASS" : "FAIL");
  }
  free(p);
  free(q);
  printf("SELFTEST firmware TCP loopback %s (over-air Wi-Fi and FM-1 USB "
         "untested)\n",
         ok ? "PASS" : "FAIL");
  fflush(stdout);
  vTaskDelete(NULL);
}
void net_selftest_start(void) {
#ifdef CONFIG_FM1_TRANSPORT_SELFTEST
  xTaskCreatePinnedToCore(selftest, "net_selftest", 8192, NULL, 3, NULL, 0);
#else
  (void)selftest;
#endif
}
