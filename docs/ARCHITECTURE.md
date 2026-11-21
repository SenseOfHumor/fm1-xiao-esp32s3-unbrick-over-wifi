# Architecture and transport contract

## Separation of responsibilities

main/recovery.c generates the native USB_KEY/ACK/calibration sequence locally.
main/host.c initializes ESP-IDF's native USB PHY/host and Bulk-Only transport.
main/jieli_uboot.c implements JieLi commands, volatile loader upload, flash
queries/reads and bounded sector erase/program/readback. main/proto.c adapts
Transporter's line protocol, while main/net_transport.c provides Wi-Fi/TCP.
Python retains the pinned upstream package parser, identity checks and restore
engine; adapters add framing, readiness waiting, backup preservation and exact
approval gates.

No Wi-Fi round trip times the USB waveform. The recovery worker is pinned to
core 1 at priority 3; Wi-Fi/network tasks and USB helper tasks run on core 0.
The existing packet/pulse critical sections and watchdog configuration remain.
This architecture and the observed target response do not replace an oscilloscope
measurement of jitter or prove every other cable/board has equivalent timing.

## Native USB lifecycle

1. POWERED, Wi-Fi/AP initialized and protocol receiver available.
2. In diagnostic mode, recovery worker stays out of GPIO19/20 and reports
   USB_RECOVERY_DISABLED; on-board transport tests can run without a target.
3. In recovery mode, release USB-Serial-JTAG pull-up/pad ownership and set
   GPIO19=D−, GPIO20=D+ with weak drive/pull-downs.
4. USB_BUS_IDLE is logged only if both lines read zero; then USB_KEY_SENDING.
5. Local key 0x16EF, ACK sensing and calibration pulses continue without network
   control. Existing already-attached/rekey branches are upstream behaviors.
6. Release GPIO control and initialize the native OTG host immediately.
7. Enumerate, claim MSC endpoints, GET MAX LUN and INQUIRY.
8. Mark UBOOT ready; the next info/read command starts the verified RAM helper.
9. Helper idle keepalive is a read-only GET_ONLINE_DEVICE after one second.
10. On USB DEV_GONE, close/release the device, clear readiness and reset loader
    state. The host daemon continues; USB_KEY does not restart automatically.

Observed case timing: 1499.8 ms calibration, 30,820 microsecond host handoff,
mount ~568.9 ms after host start. These are observed log intervals, not a new
set of timing constants or a guarantee.

`UBOOT_IDENTIFIED` is emitted beside uboot_ready=true on the worker. A later
zero status after detach is valid; it does not mean the earlier event was fake.
The host marks ready on a successful INQUIRY; the Python exact identity check
is still mandatory before reads/restoration. A ROM USB descriptor alone does
not identify the flash manufacturer/capacity or validate a package.

## TCP frame

Every frame is a 16-byte header followed by 1..4096 payload bytes:

| Bytes | Meaning |
|---|---|
| 0..3 | ASCII FM1W |
| 4..7 | uint32 sequence, big endian |
| 8..11 | uint32 payload length, big endian |
| 12..15 | uint32 zlib-compatible CRC-32 of payload, big endian |

Each direction has an independent counter starting at zero. First client
payload is the random session secret; first server payload is AUTH OK plus
newline. Later frames carry original line-protocol bytes. Complete reads/writes
handle partial socket delivery. Length/magic/sequence/CRC failures close the
connection. TCP is never transparently reconnected or a command silently replayed.

Initial authentication and complete I/O operations have bounded five-second
timeouts. Authenticated inactivity has a 120-second lease. Python quiet polling
is different from an incomplete-frame deadline: a .5-second status poll can
return no data while retaining partial framed bytes. A partial frame that never
finishes still times out rather than being resynchronized by discarding bytes.

One active controller is admitted. New TCP connections can queue in the socket
backlog but do not operate concurrently. One protocol command may be pending.
A parser mutex serializes incoming bytes, worker dispatch and disconnect cleanup.
On disconnect: finish any already-running local operation; drop incomplete binary
payloads/queued requests; discard old replies before a new session is admitted.
A disconnected write has uncertain outcome until actual flash is read again.

## Status waiting and lease maintenance

Upstream's original wait_status returns its first status reply, including zero
flags. Its ensure_uboot then fails immediately. The Wi-Fi adapter instead treats
zero/zero as a nonterminal snapshot, observes one monotonic readiness deadline,
and requests another status only when the previous request completed.

The server may hold a request while USB_KEY is active. During that quiet wait,
client ping every 15 seconds keeps the authenticated socket lease alive; the
RX task answers ping independently. PONG is not confused with a status reply.
Readiness returns without a further sleep, allowing info/helper startup promptly.
An application-mode response stops; no implicit soft-key/reset is sent.

The server's 20-second status hold is relative to host startup, not the entire
key wait. Old pending status and later zero flags must not be interpreted as a
synchronized observation that keying and zero status happened simultaneously.
See ROM_STATUS_FIX.md and the actual case transcript.

## Logging

The ring is 16,384 bytes. Oldest bytes drop on overflow; `log_take` consumes
bytes by advancing its tail. A log request returns LOG <length>, exact bytes,
then END. It is not a persistent flight recorder. Use unique before/after
files, not repeated tee to the same filename. A long successful flash read can
roll earlier handshake events out of the ring, so preserve client identity and
verification output separately.

A legacy startup banner still says data on UART0. In this adaptation, actual
protocol TX/RX is TCP. Do not diagnose a physical UART problem from that old string.

## Write barriers

The C firmware refuses sector addresses outside aligned [0x4000,0x93000), has
no bulk/chip erase command, validates payload CRC before erase, and verifies
readback. Its compile-time write gate is off in diagnostic/read-only modes.
When enabled, it queries the chip identity before the sector algorithm.

The Python guarded route additionally requires the exact known public V15 file,
own independent original reads, a separate protected copy, a reviewed per-unit
manifest, exact live identity, a fresh complete flash match including protected
data, exact sector sequence/payloads, an fsynced journal and final full-image
comparison. Typed confirmation remains unless deliberately using --yes.

The old fixed-hash approval remains for forensic reproduction of the successful
unit. New manifests remove the original user's path/hash assumptions without
removing the independent checks. This generalization is software-tested; the
historical fixed policy is the one exercised in the completed hardware restore.

CRC errors explicitly rejected before an erase can be retried under upstream's
existing policy. Missing reply, socket failure, erase/write failure or uncertain
readback must NOT lead to a blind retry. STARTED with no VERIFIED journal entry
means uncertain outcome, not that nothing happened.

## Diagnostic echo limitation

A frame whose first payload byte is NUL is routed to diagnostic echo before
line parsing. This is useful for binary transport tests but is not a universal
binary-stream multiplexer. The successful approved V15 payload/frame boundaries
were checked not to collide with that marker. Do not repurpose raw RAM-write or
arbitrary firmware commands through this adapter without separately validating
that framing path. Generic arbitrary-image writing is not a supported feature.
