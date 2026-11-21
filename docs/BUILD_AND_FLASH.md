# Build and deploy the XIAO firmware

This document covers the microcontroller image, not writing the FM-1. A build
is not proof of an electrical link, a successful flash is not proof of ROM
entry, and an AP/ping is not proof the correct recovery mode is running.

## Tested environment and reproducibility boundary

The completed case used:

- macOS 26.6.2 on an Apple-silicon Mac.
- Project Python 3.12.12; pyserial 3.5; programming esptool 5.6.0.
- ESP-IDF **v5.4.1**, commit `4c2820d377d1375e787bcef612f0c32c1427d183`.
- IDF's own Python environment used esptool 4.14.0 during the build.
- Actual chip: ESP32-S3 QFN56 rev v0.2, embedded 8 MiB PSRAM AP_3v3,
  external 8 MiB flash (manufacturer c8, device 4017), quad flash at 3.3 V.
- Application build target esp32s3, DIO flash, 80 MHz flash, octal PSRAM 80 MHz,
  FreeRTOS tick 1000 Hz; partitions below.

The default machine Python was newer than the selected toolchain environment.
Using an explicit Python 3.12 environment avoided relying on that default.
The instructions reproduce configuration/behavior; they do not promise byte-
identical firmware across timestamps, compilers, credentials or host machines.
Every board's images contain its own credentials.

No package here promises compatibility with an arbitrary ESP32 variant or a
XIAO Plus with a different memory configuration. Detect the actual hardware.
The sense camera, microphone and SD-card features are unused by this project.

## Install once, while online

Clone a fork containing this adaptation into a path without spaces. Install
Git, Python 3.12, a C compiler for tests, CMake/Ninja and ESP-IDF prerequisites
from Espressif for your host. Do not blindly run a package-manager recipe meant
for another OS. On macOS, Xcode command-line tools provide `cc`.

One supported source layout is:

```
workspace/
  fm1-esp32-unbrick/
  esp-idf-v5.4.1/
```

Example toolchain setup (commands are for a new workstation, not a requirement
to clone over the working recovery project):

```bash
# From workspace/, outside your existing project:
git clone --branch v5.4.1 --recursive https://github.com/espressif/esp-idf.git esp-idf-v5.4.1
python3.12 esp-idf-v5.4.1/tools/idf_tools.py install --targets esp32s3
python3.12 esp-idf-v5.4.1/tools/idf_tools.py install-python-env --features core
```

Then inside the adaptation checkout:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
sh tools/fetch_deps.sh
.venv/bin/python tools/configure_wifi.py
```

`fetch_deps.sh` reviews/pins both external source trees and checks the loader's
exact SHA-256 before copying it into main/. CMake checks that hash again. Do not
remove either check. See UPSTREAM.md for all revisions.

The build helper defaults to the sibling IDF path, accepts an existing IDF_PATH,
and uses the tested idf5.4_py3.12_env when present. Override
IDF_PYTHON_ENV_PATH explicitly for a different valid installation; do not assign
a project path to HOME. The script checks IDF 5.4.1 and the final memory/mode flags.

## Credentials and reset/rotation

`configure_wifi.py` generates a random WPA2 password and a separate random TCP
secret. It creates `wifi_credentials.json` and `sdkconfig.wifi` with mode 0600.
It refuses to replace either file by default. No actual case credential is
published. SSID defaults to FM1-Recovery, AP IP 192.168.4.1, TCP port 3333.

`--rotate` deliberately archives the previous two files and generates new
values. The firmware already on a board does NOT learn a changed JSON file.
ESP-IDF also does NOT overwrite an existing sdkconfig from new defaults.

For a deliberate rotation: preserve the existing generated sdkconfig files and
binaries in a private archive, move the generated per-mode sdkconfig files out
of their active names, rotate once, rebuild the required modes, and flash the
new matching image. Do not regenerate a secret to fix a network timeout.

The relevant generated configs are sdkconfig, sdkconfig.recovery.generated and
sdkconfig.approved-v15. They and credential backups stay ignored. Never publish
build logs/configs/ELFs/images that may contain passwords or the TCP secret.

## Build modes and separation

```bash
bash tools/build_firmware.sh diagnostic
bash tools/build_firmware.sh recovery
# Only after a separately reviewed/approved application-only plan:
bash tools/build_firmware.sh approved-v15 --enable-app-writes
```

| Mode | Native pins | USB console | FM-1 flash gate | Config / output |
|---|---|---|---|---|
| diagnostic | Recovery never initializes GPIO19/20 | retained | off | sdkconfig / build/ |
| recovery | USB_KEY then native host | off | off | sdkconfig.recovery.generated / build-recovery/ |
| approved-v15 | Same as recovery | off | on, same range/identity limits | sdkconfig.approved-v15 / build-approved-v15/ |

No mode automatically flashes anything or changes computer networks. The
approved-v15 flag permits a build, not a device operation. The Python client
still requires a verified reference, reviewed per-unit approval and explicit
write options. All three variants preserve the same underlying native timings.

If cached sdkconfig disagrees with the selected mode, the helper fails its
post-build guard. Stop before flashing and resolve the configuration; do not
trust a directory's name as proof its image is read-only.

The historical read-only and write-enabled images from the successful case
are retained privately. Updating these helpers after recovery does not make
those binaries disappear or retroactively change which code was hardware-tested.

## Partition table and flash addresses

| Name | Offset | Size / purpose |
|---|---|---|
| bootloader | 0x0000 | Built ESP32-S3 bootloader |
| partition table | 0x8000 | Generated from partitions.csv |
| nvs | 0x9000 | 0x6000 bytes |
| phy_init | 0xF000 | 0x1000 bytes |
| factory application | 0x10000 | 0x200000 bytes |

The original XIAO backup is a full image, not just this application partition.
Do not mix a partition table or bootloader from a different build/project.

## Preserve the XIAO before replacement

Keep the FM-1 detached from the external breakout. Enter downloader mode,
identify the actual port, and detect chip/flash size:

```bash
ls /dev/cu.usbmodem*
FM1_XIAO_PORT=/dev/cu.usbmodem_REPLACE_WITH_ACTUAL_PORT
.venv/bin/python -m esptool --chip esp32s3 --port "$FM1_XIAO_PORT" --after no-reset flash-id
```

For a detected 8 MiB XIAO, choose a NEW backup path; do not overwrite the case's
or your own original file:

```bash
mkdir -p backup
FM1_BOARD_BACKUP=$(mktemp -d "$PWD/backup/xiao-original-XXXXXXXX")
.venv/bin/python -m esptool --chip esp32s3 --port "$FM1_XIAO_PORT" --after no-reset \
  read-flash 0 0x800000 "$FM1_BOARD_BACKUP/full-flash.bin"
shasum -a 256 "$FM1_BOARD_BACKUP/full-flash.bin"
.venv/bin/python -m esptool --chip esp32s3 --port "$FM1_XIAO_PORT" --after no-reset \
  verify-flash 0 "$FM1_BOARD_BACKUP/full-flash.bin"
```

Require verification success. Full original backup and hash belong in private
storage separate from build outputs. Do not assume 4 MiB from upstream's generic
board-backup script. The completed case saved and separately verified 8 MiB.

## Downloader procedure and no-port workaround

Recovery firmware deliberately disables USB-Serial-JTAG pads and drives the
native pins, so normal native USB enumeration may disappear. Do not interpret
that alone as a bricked XIAO or try to install a CH340 driver.

With the target detached and built-in port empty, hold BOOT, tap/release RESET,
release BOOT, then connect a known USB data cable directly to the computer.
Find the actual new port. Avoid guessing when multiple boards are attached.

In the completed case, warm BOOT/RESET attempts still produced no port. The
successful workaround was: remove **both** USB and external battery power
using an existing safe connector/switch; hold BOOT while plugging the built-in
USB-C port directly into the Mac; release BOOT after about two seconds. Keep
external battery disconnected while programming. Do not desolder a live cell
or invent jumper shorts to emulate a button.

## Flash and leave downloader running

Select paths from ONE mode. Example for read-only recovery:

```bash
.venv/bin/python -m esptool --chip esp32s3 --port "$FM1_XIAO_PORT" \
  --after no-reset write-flash --flash-mode dio --flash-size 8MB --flash-freq 80m \
  0x0 build-recovery/bootloader/bootloader.bin \
  0x8000 build-recovery/partition_table/partition-table.bin \
  0x10000 build-recovery/fm1_esp32_unbrick.bin
```

For approved writes, use all three paths from build-approved-v15/ instead.
For diagnostics, use build/. No combination of folders is valid.

Require three successful esptool hash verifications and **Staying in bootloader**.
`--after no-reset` is intentional. Do not use a command that hard-resets recovery
firmware while its data pair is connected to the computer. The case's final
write-capable deployment was checked against the detected Espressif USB device
and known board serial identity, not a blind hardcoded port.

After verified deployment: unplug computer USB FIRST, restore checked battery
power, leave built-in USB-C empty, and only then reset/start the XIAO. The FM-1
stays OFF/detached until the electrical gate and Wi-Fi recovery-mode checks pass.
A programming port disappearing in recovery mode is expected. An AP alone is
not proof the correct mode or USB wiring works.

## Never flash the FM-1 package into the XIAO

V15-FM-1.fwsc stays on the computer. The XIAO embeds only the verified volatile
JieLi helper plus its own ESP32 application; it is not a storage device for a
whole FM-1 firmware package. `.uf2` instructions are for a different RP2040 route.
