#pragma once
#include <stdbool.h>
#include <stdint.h>
#define FM1_FRAME_MAX 4096u
uint32_t fm1_crc32(const uint8_t *data, uint32_t len);
void fm1_frame_header(uint8_t *header, uint32_t sequence,
                      const uint8_t *payload, uint32_t len);
bool fm1_frame_parse(const uint8_t *header, uint32_t sequence, uint32_t *len,
                     uint32_t *crc);
