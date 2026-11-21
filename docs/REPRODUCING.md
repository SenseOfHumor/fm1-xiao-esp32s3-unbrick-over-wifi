# Reproduce the recovery action

This is an operational sequence with gates, not an instruction to write every
FM-1 that happens to answer USB. The actual successful case is documented
separately. Do not use its original dump, approvals or fixed hashes as your own
unit's reference. A forum report or simulated run is not a hardware check.

## Stage 0 — prepare the workstation and offline material

Read WIRING.md, RECOVERY_SAFETY.md and BUILD_AND_FLASH.md before soldering or
flashing. Obtain an adaptation checkout, pinned dependencies, Python environment,
ESP-IDF 5.4.1, the correctly identified hardware and a trusted V15 package while
online. Do not clone over an existing recovery workspace.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
sh tools/fetch_deps.sh
.venv/bin/python tools/configure_wifi.py
bash tools/build_firmware.sh diagnostic
bash tools/build_firmware.sh recovery
```

The credential generator is a first-time action; never rerun it casually on a
working board. Keep its two files together with matching firmware builds.
Record tool versions and source commits. Capture each programming/operation log
into a new private directory. Do not publish those files without review.

Save this guide locally. When the computer joins the board's AP, Internet and
an online assistant session can disappear. Nothing here automatically switches
Wi-Fi or requires an online assistant during a physical attempt.

## Stage 1 — identify power and USB wiring

The completed route uses a XIAO ESP32-S3 Sense with TP8/D+/GPIO20, TP7/D−/GPIO19
and GND to an external female USB-C breakout. VBUS has NO supply connection;
CC1/CC2 have no external XIAO wires, but existing breakout circuitry must be
traced/measured. The FM-1 has its own battery. The XIAO's built-in USB-C stays
empty in recovery. Full pin/net/resistor evidence and required measurements
are in WIRING.md. Do not infer a breakout model from a red PCB.

Record a photo/diagram and instrument results for your actual assembly, including
pad/cable orientation, absence of shorts, isolation from every power source,
CC component values/endpoints and stable independent supply. Stop if this cannot
be established. The original case did not record meter readings; do not invent
those readings or treat its success as an exemption for another assembly.

## Stage 2 — preserve the original XIAO

With FM-1 physically detached, enter the downloader, identify chip/port/flash
size, read the complete original flash, hash it and separately verify it with
esptool. The observed Sense had 8 MiB; upstream's generic 4 MiB backup script
is not a substitute for detecting size. See BUILD_AND_FLASH.md for exact commands.
Keep the backup separate from firmware outputs and never overwrite it later.

## Stage 3 — diagnostic image and network

Flash all three diagnostic images from build/ using the matching addresses and
--after no-reset. No FM-1 is attached. This image does not initialize recovery
pins. Only diagnostic mode retains the native USB setup console.

The case verified actual firmware boot and AP initialization, then used on-board
TCP loopback tests to validate framing/authentication/CRC without moving the
Mac's Internet network. Those tests are NOT an over-air computer-to-XIAO result.
A later manual AP join returned real PONG and diagnostic mode logs.

Manually join your generated AP/password and run:

```bash
.venv/bin/python tools/wifi_recover.py ping
.venv/bin/python tools/wifi_recover.py log
# Run the diagnostic echo test before target recovery, in diagnostic mode:
.venv/bin/python tools/wifi_recover.py selftest
```

Require actual PONG; the helper's successful process exit alone is insufficient
if returned text differs. Read the TCP secret from the existing JSON through the
client, not by putting it on a command line. Wrong secret/CRC/sequence closes
the session. If the Mac needs Internet simultaneously, use Ethernet/USB tether
or a separate controller; otherwise deliberately work offline. Do not let
an automation switch networks out from under a remote session.

## Stage 4 — deploy read-only recovery and verify mode

Program build-recovery/ with the target detached and --after no-reset. Require
all three verification hashes and Staying in bootloader. Unplug computer USB
FIRST, then restore checked battery power and start/reset XIAO with its built-in
port EMPTY. Do not leave USB programming connected to the same native data nets.

Manually join the AP. With target still detached, ping and capture a NEW board
log. Require recovery stage messages such as USB_KEY_SENDING/current KEY progress.
USB_RECOVERY_DISABLED means the diagnostic image is running or you opened a
stale saved file. Verify the actual image; do not fix that message by attaching
the FM-1 or changing GPIOs. A legacy UART banner is only a stale description.

The firmware keys continuously. After a successful handoff then detach, it
stays in the host loop and does not automatically re-arm KEY. Prepare fresh
physical sessions deliberately, with target detached during any programming;
never make a reset an automatic recovery action after a failed write.

## Stage 5 — actual identity and two matching original reads

Start with a checked electrical assembly, fresh USB_KEY session, independent
battery power, XIAO built-in USB-C empty and FM-1 OFF. Attach the established
external-breakout data/ground connection. Make a unique directory and run one
dump command; promptly switch FM-1 ON after the readiness wait begins:

```bash
mkdir -p backups
FM1_DUMP=$(mktemp -d "$PWD/backups/unit-original-XXXXXXXX")
set -o pipefail
.venv/bin/python tools/wifi_recover.py dump "$FM1_DUMP" --wait 180 \
  2>&1 | tee "$FM1_DUMP/session.log"
.venv/bin/python tools/wifi_recover.py log 2>&1 | tee "$FM1_DUMP/board-after.log"
```

Use real hardware mode: NO --dry-run or --mock-flash. The command checks exact
key/type/supported flash identity before reading. Native USB 4C4A:8057 and
INQUIRY WL82 UBOOT1.00 establish ROM entry; they alone do not identify the flash.
Expected supported key is 980F, type 3, and ID 856014 or B36014. The second ID is
accepted by upstream, but this completed case tested only 856014.

The modified readiness wait treats zero status as nonterminal, keeps a pending
TCP wait alive with ping and returns immediately when ready. Dump then queries
the verified RAM helper and reads twice without an operator gap. No implicit
soft-key or application reset is sent by this wait.

Require two exact 1 MiB reads, byte equality, matching SHA-256, and analysis.json
with mock=false and actual identity. The wrapper preserves:

- full-flash-before-1.bin — first independent read.
- full-flash-before-2.bin — second independent read.
- analysis.json — identity, hash, ranges and upstream analysis.
- Upstream timestamped dump and human-readable analysis.
- Your own session/board logs.

Stop if equality or identity fails. Preserve mismatched reads/logs for diagnosis;
do not write, normalize identities or count a simulated dump as a real backup.
The current wrapper only preserves its named verified pair after equality; do
not claim a failed partial read is a verified backup.

## Stage 6 — acquire and validate V15 offline

The public V15 mirror used in this case is Quixotic7/FM1Backups at
8cbc3b066ed15ec6a0d5a990efb78b56f6c17183, file V15-FM-1.fwsc. The project
links the upstream package rather than redistributing it. If using Git to obtain
that mirror, do so while online, then check out the exact recorded commit.

Required package SHA-256:
`db1642b2b6fa5c2cccb11ffd13878068bb28601678d3644049f99dc40e7edb8a`.
Required V15 application SHA-256:
`6edf3c37fb5bbbc33607c89375ee024d5477c17914d72221c8c68e58a8255686`.

```bash
# If obtaining a NEW local mirror, while online (skip if already obtained):
# git clone https://github.com/Quixotic7/FM1Backups.git third_party/FM1Backups
# git -C third_party/FM1Backups checkout --detach 8cbc3b066ed15ec6a0d5a990efb78b56f6c17183
FM1_V15=/absolute/path/to/V15-FM-1.fwsc
shasum -a 256 "$FM1_V15"
.venv/bin/python tools/prepare_v15_plan.py \
  --backup-dir "$FM1_DUMP" --package "$FM1_V15" \
  --immutable-backup "$PWD/backups/independent-original.bin" \
  --out "$FM1_DUMP/v15-approval.json" \
  2>&1 | tee "$FM1_DUMP/offline-plan.log"
```

The generator checks both originals/manifest, verifies public V15, rejects a
head mismatch and creates a separate original copy. On macOS it sets/verifies
UF_IMMUTABLE/uchg; elsewhere it requires a read-only copy, which is weaker than
filesystem/hardware immutability. Preserve another offline copy independently.
The original successful case's immutable copy and hash remain private.

The manifest records your actual identity, original/final full hashes, exact
sector list, package hash and independent-copy path. It is local review data,
not a signed or remote authorization service. It stores a local absolute copy
path; regenerate the plan from preserved originals when moving machines, rather
than removing checks to make a stale path work.

Review every proposed sector. Only differences inside 0x04000..0x92FFF may be
approved. Preserve 0x00000..0x03FFF and ALL bytes 0x93000..0xFFFFF. If application
already matches V15, the generator stops: no firmware write is needed. Unknown
or mismatched head/identity/layout means further diagnosis, not a forced plan.

Do not infer a need for OTA erasure from a DAMAGED analyzer label: the original
case's relocated loader tripped a fixed-span trailing-erasure heuristic that
overlapped a valid record and protected data. See the case study.

Creating the JSON is NOT approval. Get explicit approval of that exact package,
backup and sector plan before enabling either write gate.

## Stage 7 — separately approved write-capable deployment

The read-only firmware will reject wsec even if a client supplies --write.
After explicit review/approval, build a separate image:

```bash
bash tools/build_firmware.sh approved-v15 --enable-app-writes
```

Follow BUILD_AND_FLASH.md with all three paths from build-approved-v15/.
This is the only necessary XIAO reflash when moving from the read-only mode.
Keep all older builds. Target must be OFF and detached while programming.
Use --after no-reset; verify hashes; unplug computer USB before battery startup.
Manually rejoin the AP and prepare a new physical KEY/target switch-on attempt.
Do not reflash a bridge while relying on it to keep a target ROM session alive.

## Stage 8 — approved live restore and persistent evidence

Use your own absolute FM1_DUMP and FM1_V15 paths if a new Terminal was opened;
shell variables from earlier sessions do not persist. Keep a unique new
restore directory. The command below uses the explicitly reviewed manifest.
It does not use the historical case's hardcoded approval defaults.

```bash
set -o pipefail
mkdir -p logs
FM1_LIVE=$(mktemp -d "$PWD/logs/approved-restore-XXXXXXXX")
FM1_RESTORE_RC=0
.venv/bin/python tools/wifi_recover.py --approved-v15 \
  --approval-plan "$FM1_DUMP/v15-approval.json" --evidence-dir "$FM1_LIVE" \
  restore "$FM1_V15" --ref "$FM1_DUMP/full-flash-before-1.bin" \
  --verify-v15 --write --wait 180 \
  2>&1 | tee "$FM1_LIVE/restore.log" || FM1_RESTORE_RC=$?
# Only after the restore command finishes:
.venv/bin/python tools/wifi_recover.py log 2>&1 | tee "$FM1_LIVE/board-after.log" || true
printf 'Restore exit status: %s; evidence: %s\n' "$FM1_RESTORE_RC" "$FM1_LIVE"
if [ "$FM1_RESTORE_RC" -ne 0 ]; then
  printf 'STOP: keep both devices powered/connected; do not reset or retry.\n'
fi
```

This retains upstream's typed WRITE confirmation; type it only after reviewing
the displayed plan. A deliberately approved noninteractive script may use
--yes, but that is not a reason to omit any preceding check. Never automate
insertion of --i-know, full-restore, repair-settings or a broader flash range.

Before an erase, the guarded session requires:

1. Both saved originals and manifest still agree.
2. Independent protected copy remains readable/locked and hashes correctly.
3. Package is exactly verified public V15 and plan recomputes identically.
4. Fresh LIVE key/type/flash identity exactly equals the approval identity.
5. A fresh entire 1 MiB read equals the original, INCLUDING all protected data.
6. Sector sequence, addresses and payload bytes equal the approved plan.

The C gate also checks its allowed range/CRC/identity. Each successful sector
reply follows its native readback verification. The client fsyncs STARTED and
VERIFIED events. A missing reply leaves outcome uncertain; do not blindly replay.
Finally the entire flash is read again and compared byte-for-byte with original
head + V15 application + original protected data.

Success requires all of:

- Process exit status zero (use pipefail; tee's status alone proves nothing).
- `Final full read EQUALS the expected image` in the client output.
- fresh-read.bin and final-read.bin saved under the unique evidence directory.
- A journal with the exact approved VERIFIED addresses in order.
- RESTORE_VERIFIED.json with the expected final hash, count, identity and
  protected_regions_unchanged=true.

## Stage 9 — shutdown, boot and preserve

Only after all verification criteria pass: switch FM-1 OFF first, leave its
cable until it is off, disconnect it from the external breakout, power down
XIAO, then boot FM-1 normally with USB disconnected. Record whether the screen
and normal behavior actually return. A checksum is not itself a boot observation.

If ANY write/verification fails: keep both independently powered and recovery
wiring attached, save the journal and logs, and stop. Do not reset, unplug,
blindly retry or apply settings cleanup. Re-entering ROM after a partially
confirmed operation requires a separately reviewed read-only diagnosis.

Manually reconnect to normal Internet Wi-Fi when commands finish. Keep raw
originals and final readbacks private. Preserve source/tool versions and a
private archive before publishing sanitized source/results. The successful
case did not need head, OTA loader, settings or Bluetooth erasure.
