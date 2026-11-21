#include "wire_protocol.h"
#include <string.h>
static uint32_t get32(const uint8_t *p) {
  return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 |
         p[3];
}
static void put32(uint8_t *p, uint32_t v) {
  p[0] = v >> 24;
  p[1] = v >> 16;
  p[2] = v >> 8;
  p[3] = v;
}
uint32_t fm1_crc32(const uint8_t *data, uint32_t len) {
  uint32_t crc = ~0u;
  while (len--) {
    crc ^= *data++;
    for (int i = 0; i < 8; i++)
      crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1)));
  }
  return ~crc;
}
void fm1_frame_header(uint8_t *h, uint32_t sequence, const uint8_t *payload,
                      uint32_t len) {
  memcpy(h, "FM1W", 4);
  put32(h + 4, sequence);
  put32(h + 8, len);
  put32(h + 12, fm1_crc32(payload, len));
}
bool fm1_frame_parse(const uint8_t *h, uint32_t sequence, uint32_t *len,
                     uint32_t *crc) {
  if (memcmp(h, "FM1W", 4) || get32(h + 4) != sequence)
    return false;
  *len = get32(h + 8);
  *crc = get32(h + 12);
  return *len > 0 && *len <= FM1_FRAME_MAX;
}
