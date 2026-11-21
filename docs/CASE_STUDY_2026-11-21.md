# Completed recovery: XIAO ESP32-S3 Sense → M-VAVE FM-1

## Outcome and evidence categories

On 2026-11-21, an actual M-VAVE FM-1 was restored to verified stock V15 using
a battery-powered Seeed XIAO ESP32-S3 Sense, an external USB-C female breakout
wired to native USB test pads, and a Mac running the Wi-Fi TCP client.

The saved live evidence was independently inspected after the operator reported
success: 143 sector acknowledgments, expected complete final image, unchanged
protected bytes. The operator then reported that the FM-1 worked. That final
normal-boot outcome is an operator observation; the documentation process did
not independently inspect its screen, audio output, every feature or long-term
reliability. No further target operation was performed to produce this paper.

Evidence categories used below:

- **Actual local artifacts:** original independent reads, manifests, programming
  logs, write journal, fresh/final readbacks, final verification marker.
- **Operator-provided actual transcript:** first ROM handshake interval when
  a later log command had consumed/overwritten the earlier saved output.
- **Offline analysis:** comparisons and plans computed from the actual snapshot.
- **Software regression:** localhost/unit checks, not new hardware measurements.
- **Hypothesis:** likely cause where the saved evidence cannot prove causation.

Sanitized summary: [evidence/restore-verification.json](evidence/restore-verification.json).
Raw dumps, full logs and credential-bearing binaries are private and excluded
from Git. Hashes are published to make the claims auditable without redistributing
per-unit data or firmware. See PRESERVATION_AND_PUBLICATION.md.

## Initial failure

The unit originally ran factory firmware. The operator attempted a browser-based
SLOOP install; immediately after Upload Firmware, it appeared to reset/power off.
Thereafter the backlight cycled, no screen content appeared, and neither Mac nor
Windows recognized an ordinary USB device. This suggested application/boot-state
failure, not proof of destroyed hardware or ROM.

An RP2040 fallback was not needed. There was no separate USB-to-UART adapter or
second ESP32 USB controller. The single native interface was first used for
programming, then exclusively for the target. Wi-Fi replaced the computer-facing
UART connection expected by the original ESP32 port.

## Hardware actually used

| Item | Recorded configuration / limits |
|---|---|
| Bridge | Seeed XIAO ESP32-S3 Sense; S3 rev v0.2 |
| Memory | Detected 8 MiB external quad flash, 8 MiB embedded octal PSRAM |
| USB data | TP8 → external D+, TP7 → external D−, GND → external GND |
| External connector | Generic red female USB-C breakout, six labels, two unidentified CC-area SMD parts |
| VBUS | No XIAO/battery/3V3/5V supply connection to breakout VBUS |
| CC | No external XIAO wires to CC1/CC2; existing component circuit unknown |
| Target cable | USB-C data cable between external breakout and FM-1 |
| XIAO power | Single-cell lithium battery through existing TP4056 charge/protection arrangement |
| Target power | FM-1's own charged battery |
| Programming | Built-in XIAO USB-C to Mac, target detached |
| Recovery | Built-in XIAO USB-C EMPTY, Mac control over Wi-Fi |

The official schematic confirms pad mappings and that pads bypass the receptacle's
22 Ω series resistors. The successful operation shows this particular path could
carry the required signaling. It does NOT identify CC resistor values, prove
absence of all faults, validate battery protection polarity/topology, or certify
USB signal integrity. No multimeter verification was recorded. Reproductions
must perform their own electrical checks; do not copy this evidence gap.

An earlier direct built-in-C-to-FM-1 concept was superseded. In the actual
external-breakout topology, leaving its VBUS unpowered isolates the source if
verified; it does not inherently require cutting the cable's power conductor.

## Development and verification before the actual target

1. Cloned the primary ESP32 port once into a no-spaces workspace and created
   feature/xiao-s3-wifi-recovery. Existing related checkout was not overwritten.
2. Recorded upstream commits and preserved loader SHA-256 checks in fetch script
   and CMake. Updated the pinned recovery client for its newer supported-ID checks.
3. Inspected official Seeed schematic and upstream no-VBUS instructions.
4. Implemented WPA2 AP, independent authentication secret, bounded framed TCP,
   CRC/sequence validation, partial I/O and single-controller/disconnect behavior.
5. Wrapped the upstream high-level recovery logic instead of replacing it.
6. Added diagnostic, read-only recovery and explicitly write-enabled build modes.
7. Detected the actual XIAO memory and saved its original complete **8 MiB** flash;
   separately verified the backup against the board with esptool.
8. Built/flashed diagnostics, verified programming hashes and booted. On-board
   TCP tests passed 64 B, 512 B, 4 KiB, 64 KiB and 1 MiB with matching SHA-256.
9. Deferred automatic Mac AP switching to preserve Internet. The operator later
   manually joined the AP and obtained real PONG/diagnostic logs.
10. Prior sample-image exercises verified software logic and planned 143 sectors;
    those were NOT measurements of this unit and never authorized a write.

The initial XIAO backup SHA-256 was
`179da4a5b0893ca776ee83276736dad25cce6f7f70a0eaa7e25d0619062f8590`.
Its bytes remained unchanged through the final restoration.

## First actual ROM handshake

The operator preserved this actual interval from Terminal; the current on-disk
capture had later no-device lines because logs are consumptive and tee was reused:

```text
130.313 ACK (data line held low) after 259091 packets
130.315 STATE ROM_ACK_RECEIVED
130.315 STATE OSCILLATOR_CALIBRATION
131.815 PULSE: D+ released after 1499.8 ms - calibration done, host takes over
131.816 STATE USB_HOST_HANDOFF
131.847 HANDOFF: pulses stopped, OTG host started in 30820 us
132.415 HOST: device mounted, addr=1 (568.9 ms after host start)
132.416 VID=4C4A PID=8057 bcdDevice=0300 bcdUSB=0110
133.917 INQUIRY OK: vendor="WL82    " product="UBOOT1.00       " rev="1.00"
133.917 STATE UBOOT_IDENTIFIED
137.418 HOST: device detached (5003.0 ms after mount)
```

This was genuine target ROM entry. It was not yet a processor-key/flash-ID query.
The code sets uboot_ready beside UBOOT_IDENTIFIED and clears it on DEV_GONE.
A later zero status does not invalidate that brief successful interval.

## Why --wait did not wait

Two separate client defects were found:

1. Serial-style .5-second quiet polls initially became fatal TCP timeouts. The
   adapter now retains partial frames and returns an empty quiet poll, with a
   separate incomplete-frame deadline.
2. Upstream wait_status returned the first OK status, including zero/zero, then
   ensure_uboot failed immediately. The Wi-Fi wrapper now keeps polling until
   ready/deadline/real error, sends a harmless ping during a held wait to preserve
   the TCP lease, and requests info immediately after readiness.

No USB waveform change was made. The server's 20-second hold is relative to host
start; an initial zero reply captured later is not evidence it replied while
KEY's blocking loop was still active.

The first detach was 3.501 seconds after INQUIRY, with no helper startup recorded.
Host tasks do not terminate after five seconds; helper keepalive only starts
after that helper runs. Idle ROM reset is plausible but was not measured as a
causal watchdog specification. Power/connection causes were not ruled out.
The corrected client and prompt same-session identity/read path subsequently
succeeded. No proactive automatic loader startup or USB timing alteration was
needed to obtain the successful session.

## Actual identity and verified double backup

Recorded actual identity:

```text
OK key=980F type=3 id=856014
```

Flash capacity was 1 MiB. Two independent complete reads were equal. The
timestamped dump, both named independent reads and saved manifest all matched:

`68c5c500ed28aa73b6d9ece9ba8e12795a4985625fa76c77e66d28cfdf3ddea2`.

An additional full copy was preserved outside logs with read-only permissions
and macOS UF_IMMUTABLE/uchg verified. This is a filesystem guard that an owner
can deliberately clear, not hardware WORM. Original readings were retained.

## Actual flash analysis

| Region | Finding |
|---|---|
| 0x00000..0x03FFF | Exact public stock V15 head; no rewrite needed |
| 0x04000..0x32FFF | 47 sectors differ from separate factory reference |
| 0x33000..0x92FFF | 96 sectors equal that factory reference byte-for-byte |
| Entire app vs public V15 | All 143 sectors differ |
| Torn-sector heuristic | No torn sectors detected; does not exclude interruption |
| 0xE6000..0xE601F | Staged-loader outer header CRC valid |
| 0xE6020..0xE7B27 | Declared 6920-byte body; expected RAM address and marker present |
| 0xE7F00..0xE7F6F | Valid OTA record pointing to E6000 |
| 0xE8000 | Existing data/settings/leftovers |
| 0xE9000 onward | Bluetooth and factory resource data; preserve |

The factory reference was the existing FM1Backups new-unit-factory-20261017 dump,
not another read of this FM-1. Its hash was
`bf6371a494c3f7313672a4b393ded14b101ad8be8a93f06768076c2e27aa6ebd`.
The public downloadable V15 application differs from that factory image, so
all-143-different is not a contradiction. The 47/96 boundary is consistent with
an interrupted update between complete sector writes. The exact SLOOP build
was not available for attribution; that likely cause is not a proven instruction-
level diagnosis or proof the first 47 sectors belong to a particular release.

The boot-head SHA-256 was exactly the known V15 value:
`d9f43191777656de01c7bed4f9e9ba2e34e94832c5d2ed02c3fc7ab7a6d9bd67`.
The original application's hash was
`d829220b1c8f3302545358419eeada7e1c76f5195e83952667844bf2b33dc482`.

### The misleading DAMAGED staged-loader verdict

The only warning was non-erased bytes after the body. check_loader uses a fixed
0x4F00 span. Starting at E6000, that reaches EAEFF and includes a valid record,
E8000 data, E9000 Bluetooth and EA000 resources. Padding between the declared
body and record was all FF; padding after the 112-byte record was also all FF.
The heuristic therefore did not establish a corrupt body in this allocation.
Header CRC and marker do not prove whole-body authenticity either; no reference
body was available. The loader data-CRC field was FFFF.

No loader/record deletion was proposed. Sector-rounding that presumed span
through EAFFF would have destroyed protected data. The independent direct-USB
repair-settings policy would have changed 93000, E6000, E7000 and E8000 in this
actual snapshot; that was broader than the authorized repair and was not used.

## Approved plan and write-capable deployment

The operator explicitly approved the exact public stock V15 application-only
plan at 0x04000..0x92FFF. V15 file hash:
`db1642b2b6fa5c2cccb11ffd13878068bb28601678d3644049f99dc40e7edb8a`.
Application hash:
`6edf3c37fb5bbbc33607c89375ee024d5477c17914d72221c8c68e58a8255686`.

Plan: erase/program 143 whole 4096-byte sectors = **585,728 bytes**. Actually
differing byte positions: **561,263**. Every head byte and every byte >=93000
would remain identical. This count was recomputed from the actual dump, not
copied from the earlier 143-sector simulation.

Both client and read-only C write gates initially refused writes. A separate
write-enabled build was necessary. C source, GPIO timings and range limits
were unchanged. Original read-only/diagnostic builds were retained. The
operator detached the FM-1, restored XIAO downloader enumeration via the cold-
power BOOT workaround, and the approved image was programmed to the detected
XIAO. All three image hashes verified, ending Staying in bootloader. The board
was not started on the Mac's data bus. The operator then performed battery/
Wi-Fi handoff and the live restore commands manually.

## Final live checks and result

The successful restore used the fixed historical approval guard for this exact
original, identity, package, sector sequence and expected result. Before erase,
it required a new complete live read exactly equal to the original—including
all protected data—and saved that fresh read. It did not merely accept the
older backup as proof of current state.

The actual journal has **286 events**, STARTED and VERIFIED for each of the
143 approved sector addresses, in order. Firmware verified each sector before
its OK reply. The complete final read then matched:

`872d9c4c7ccce4520ba94bbc60c3d4dbc43abfee77ce686f79aa510c66f02b79`.

Independent post-run comparison of the actual fresh/final files confirmed:

- Both were exactly 1,048,576 bytes.
- Fresh file hash equaled the original double-backup hash.
- Final file hash equaled the planned final hash and success marker.
- Bytes 00000..03FFF and 93000..FFFFF were byte-for-byte unchanged.
- Every approved sector had its verification acknowledgment.

Actual final client line:

```text
Final full read EQUALS the expected image (sha256 872d9c4c7ccce4520ba94bbc60c3d4dbc43abfee77ce686f79aa510c66f02b79)
```

The operator was instructed to switch FM-1 OFF first, disconnect its USB cable,
power down the bridge, then boot the FM-1 normally with USB detached. The operator
reported that it worked. No head, OTA, VM/settings, Bluetooth or resource repair
was required. No later SLOOP/V16 installation or long-term functional test is
claimed by this case study.

## What can and cannot be generalized

Reproducible: native pin mapping, isolated power/data architecture, pinned loader
identity, staged diagnostic/read-only/write-capable lifecycle, framed TCP,
readiness semantics, double backups and application-only verification policy.

Not universal: this breakout's unknown CC circuit, unmeasured wiring/power,
exact flash maker on another unit, original/final hashes, 143-sector count,
interpretation of another staged-loader layout, or successful normal boot on
another hardware/firmware revision. Public per-unit plan support was added
and software-tested after recovery; it is not a second hardware result.
