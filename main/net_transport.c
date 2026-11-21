// Authenticated bounded frames over a single-controller WPA2 SoftAP.
#include "net_transport.h"
#include "esp_event.h"
#include "esp_netif.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "log.h"
#include "nvs_flash.h"
#include "wire_protocol.h"
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define MAX_FRAME 4096
// Header: magic FM1W, sequence, payload length, CRC32(payload); all integers
// big endian.
static int peer = -1;
static uint32_t tx_seq;
static SemaphoreHandle_t wire;
static bool failed;
static bool complete(int fd, void *buf, size_t n, bool sending) {
  uint8_t *p = buf;
  int64_t deadline = esp_timer_get_time() + 5000000;
  while (n) {
    int64_t left = deadline - esp_timer_get_time();
    if (left <= 0)
      return false;
    struct timeval tv = {.tv_sec = left / 1000000, .tv_usec = left % 1000000};
    setsockopt(fd, SOL_SOCKET, sending ? SO_SNDTIMEO : SO_RCVTIMEO, &tv,
               sizeof(tv));
    int k = sending ? send(fd, p, n, 0) : recv(fd, p, n, 0);
    if (k <= 0)
      return false;
    p += k;
    n -= k;
  }
  return true;
}
static bool frame_read(int fd, uint32_t seq, uint8_t *buf, uint32_t *n) {
  uint8_t h[16];
  uint32_t expected;
  // A quiet authenticated connection has a two-minute lease. Once a frame
  // starts, bounded reads prevent trickled bytes from keeping a partial command
  // alive.
  if (recv(fd, h, 1, 0) != 1 || !complete(fd, h + 1, 15, false))
    return false;
  return fm1_frame_parse(h, seq, n, &expected) &&
         complete(fd, buf, *n, false) && fm1_crc32(buf, *n) == expected;
}
void net_write(const void *data, size_t len) {
  xSemaphoreTake(wire, portMAX_DELAY);
  const uint8_t *p = data;
  while (peer >= 0 && !failed && len) {
    size_t n = len > MAX_FRAME ? MAX_FRAME : len;
    uint8_t h[16];
    fm1_frame_header(h, tx_seq++, p, n);
    if (!complete(peer, h, 16, true) || !complete(peer, (void *)p, n, true)) {
      failed = true;
      shutdown(peer, SHUT_RDWR);
      break;
    }
    p += n;
    len -= n;
  }
  xSemaphoreGive(wire);
}
static void server(void *arg) {
  (void)arg;
  int listener = socket(AF_INET, SOCK_STREAM, IPPROTO_IP);
  int reuse = 1;
  setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
  struct sockaddr_in addr = {.sin_family = AF_INET,
                             .sin_port = htons(CONFIG_FM1_TCP_PORT),
                             .sin_addr.s_addr = htonl(INADDR_ANY)};
  configASSERT(listener >= 0 &&
               bind(listener, (struct sockaddr *)&addr, sizeof(addr)) == 0 &&
               listen(listener, 1) == 0);
  uint8_t buf[MAX_FRAME];
  for (;;) {
    int fd = accept(listener, NULL, NULL);
    if (fd < 0)
      continue;
    struct timeval timeout = {.tv_sec = 5};
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
    setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
    uint32_t n;
    const char *secret = CONFIG_FM1_SESSION_SECRET;
    if (!frame_read(fd, 0, buf, &n) || n != strlen(secret) ||
        memcmp(buf, secret, n)) {
      close(fd);
      continue;
    }
    xSemaphoreTake(wire, portMAX_DELAY);
    peer = fd;
    failed = false;
    tx_seq = 0;
    xSemaphoreGive(wire);
    net_write("AUTH OK\n", 8);
    dlog("STATE CLIENT_CONNECTED");
    uint32_t seq = 1;
    for (;;) {
      timeout.tv_sec = 120;
      timeout.tv_usec = 0;
      setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
      if (!frame_read(fd, seq++, buf, &n))
        break;
      // Echo is a transport diagnostic, separate from the line protocol.
      if (buf[0] == 0)
        net_write(buf, n);
      else
        proto_receive(buf, n);
    }
    // Finish any in-flight local operation before clearing its parser state.
    // Do not admit a new session until all old replies have been discarded.
    shutdown(fd, SHUT_RDWR);
    proto_disconnect();
    xSemaphoreTake(wire, portMAX_DELAY);
    peer = -1;
    close(fd);
    xSemaphoreGive(wire);
    dlog("CLIENT_DISCONNECTED: in-flight writes are never replayed");
  }
}
void net_start(void) {
  configASSERT(strlen(CONFIG_FM1_AP_PASSWORD) >= 8 &&
               strlen(CONFIG_FM1_AP_PASSWORD) <= 63);
  configASSERT(strlen(CONFIG_FM1_SESSION_SECRET) >= 24 &&
               strlen(CONFIG_FM1_SESSION_SECRET) <= MAX_FRAME);
  wire = xSemaphoreCreateMutex();
  configASSERT(wire);
  esp_err_t e = nvs_flash_init();
  // Never erase NVS implicitly: preserve the board's data and report failures.
  ESP_ERROR_CHECK(e);
  ESP_ERROR_CHECK(esp_netif_init());
  ESP_ERROR_CHECK(esp_event_loop_create_default());
  esp_netif_create_default_wifi_ap();
  wifi_init_config_t init = WIFI_INIT_CONFIG_DEFAULT();
  ESP_ERROR_CHECK(esp_wifi_init(&init));
  wifi_config_t cfg = {.ap = {.ssid = CONFIG_FM1_AP_SSID,
                              .password = CONFIG_FM1_AP_PASSWORD,
                              .channel = 6,
                              .max_connection = 1,
                              .authmode = WIFI_AUTH_WPA2_PSK,
                              .pmf_cfg = {.required = true}}};
  ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
  ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &cfg));
  ESP_ERROR_CHECK(esp_wifi_start());
  dlog("STATE WIFI_READY: %s 192.168.4.1:%d", CONFIG_FM1_AP_SSID,
       CONFIG_FM1_TCP_PORT);
  printf("FM1 Wi-Fi: %s / %s at 192.168.4.1:%d\nTCP secret: %s\n",
         CONFIG_FM1_AP_SSID, CONFIG_FM1_AP_PASSWORD, CONFIG_FM1_TCP_PORT,
         CONFIG_FM1_SESSION_SECRET);
  xTaskCreatePinnedToCore(server, "wifi_tcp", 8192, NULL, 4, NULL, 0);
  extern void net_selftest_start(void);
  net_selftest_start();
}
