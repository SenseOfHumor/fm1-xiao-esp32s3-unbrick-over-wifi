#pragma once
#include <stddef.h>
#include <stdint.h>
void net_start(void);
void net_write(const void *data, size_t len);
void proto_receive(const uint8_t *data, unsigned len);
void proto_disconnect(void);
