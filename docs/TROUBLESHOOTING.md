# Errors faced, evidence, causes and workarounds

This list distinguishes confirmed code/measurement facts from hypotheses.
Never turn a historical workaround into an automatic reset after a failed write.
Preserve the last confirmed sector and full evidence before changing a live session.

## 1. Mac Internet disappears when joining the XIAO AP

**Observed:** the Mac had only its ordinary Wi-Fi for Internet. An automated
network-join command once returned success but the interface stayed on its old
subnet; direct TCP was unreachable. Joining an isolated AP would also interrupt
the online assistant session.

**Resolution:** stop automatic network switching. Prepare local commands/docs,
then let the operator manually join the AP and work offline. A separate Windows
controller was an optional alternative, not a hardware requirement; the actual
case later used a real manual Mac AP connection and PONG.

**Do not infer:** command exit zero proves association, on-board loopback proves
over-air communication, or Internet is required during local recovery.

## 2. No /dev/cu.usbmodem* despite connecting a cable

**Observed:** only Bluetooth/debug-console ports appeared, including after warm
BOOT/RESET attempts. No XIAO serial device could be selected safely.

**Resolution in this case:** detach the FM-1; remove USB AND battery power using
existing safe connectors; hold BOOT while reconnecting built-in XIAO USB-C to
the Mac with a known data cable; release BOOT after about two seconds. The
Espressif USB JTAG/serial unit then appeared. Detect the actual port and chip.

**Why caution matters:** recovery owns native pins and disables the setup
peripheral. A battery keeps the chip powered after USB removal. Do not guess
an unrelated serial port, install CH340 drivers for native USB, short random
pads, or desolder a live battery. Use --after no-reset and remove computer data
before starting recovery firmware.

## 3. PONG, but USB_RECOVERY_DISABLED

**Observed:** real Wi-Fi communication worked, but the diagnostic image's worker
never initialized the recovery GPIOs. A separate built recovery image had not
yet been installed. A readback later matched the diagnostic binary exactly.

**Resolution:** verify generated mode flags AND actual deployed image. Flash
all three read-only recovery artifacts, verify hashes, leave downloader running,
unplug Mac data, then start on battery. Do not modify GPIO mappings or attach
the target to make a diagnostic-mode message disappear.

The legacy startup phrase data on UART0 is stale text, not evidence a UART
adapter is required. Actual transport in the adaptation is TCP.

## 4. --wait 180 fails after a quiet .5-second read

**Confirmed defect:** upstream's serial-style polling expects no data during
short waits; the first TCP adapter treated that socket timeout as a fatal frame
failure and closed the connection.

**Fix:** retain partial wire-frame bytes and return an empty quiet poll. Bound
the incomplete-frame lifetime separately (five seconds). EOF, wrong CRC,
sequence or malformed frames remain fatal; no silent reconnect/replay.
Regression tests include delay through several polls and split header/body data.

## 5. --wait 180 exits on uboot=0 v15=0

**Confirmed defect:** pinned upstream wait_status returned the first OK status
snapshot, not the first READY state. ensure_uboot immediately rejected zero/zero.
The saved real client log showed a reply in ~13 ms followed by that exact failure.

**Fix:** the Wi-Fi wrapper waits on a monotonic readiness deadline, requests
another status only after a response, and maintains a held TCP session with
harmless ping every 15 seconds. It returns immediately on uboot=1 and stops on
real errors, disconnect, timeout or application mode without sending a soft key.
No USB_KEY waveform change or firmware reflash was needed for this fix.

The C server's status hold lasts only until ready or 20 seconds after host
start. A zero after detach is legitimate. Old KEY and later zero logs are not
proof those events happened at the same instant.

## 6. Real UBOOT enumerated, then detached about five seconds after mount

**Actual timestamps:** mount 132.415 s, WL82 UBOOT1.00 INQUIRY and ready flag at
133.917 s, detach 137.418 s. That is 5.003 s after mount and 3.501 s after INQUIRY.
No loader command was recorded between INQUIRY and detach.

**Investigation:** host tasks have no five-second lifetime; the local 2-second
transfer timeout only applies to commands. The helper was not running yet,
so helper keepalive did nothing. An idle ROM watchdog/reset is plausible, but
power/physical link issues cannot be excluded by that transcript alone.

**Effective workflow:** corrected readiness handling followed promptly by info,
or one dump command that performs identity and both reads in the same session.
A later actual session succeeded; the earlier detach's exact physical cause
was not proven. Do not label the hypothesis as a measured watchdog constant.

After detach the firmware remains in the host loop; client waiting cannot
restart KEY. Prepare new physical attempts deliberately, never automatic rekey
as an uncertain-write recovery strategy.

## 7. Earlier handshake lines disappear from logs

**Confirmed behavior:** the ESP32 log ring is 16 KiB, overwrites oldest entries
and is consumed by log_take. The log command is a drain, not a file read.
`tee same-file.log` also truncates its previous on-disk capture.

**Resolution:** a unique directory per attempt, distinct before/after names,
persistent client session logs, and copying important transcripts immediately.
The initial handshake interval was supplied by the operator's Terminal output
when the current saved file contained only later no-device messages. The public
case explicitly labels that provenance. Do not fabricate a missing raw log.

## 8. Analyzer says staged loader DAMAGED

**Actual case:** header at E6000, body E6020..E7B27, valid record E7F00..E7F6F,
erased padding between body/record and after record. The only reported damage
was non-erased bytes after the body.

**Confirmed analyzer limitation:** it assumes LOADER_SPAN=0x4F00, checking from
this loader through EAEFF. That span includes its valid OTA record, E8000 data,
E9000 Bluetooth data and EA000 resources. A fixed-span trailing-erasure heuristic
is not proof of body corruption at a relocated allocation.

**Resolution:** preserve all data >=93000. Do not erase a presumed five-sector
loader span or invalidate the record by guesswork. Application-only V15 restore
succeeded with loader/record/settings unchanged. Header checks alone also do
not prove an authentic loader body; retain that uncertainty.

## 9. No torn sectors, but the application is still broken

**Actual comparison:** first 47 app sectors differed from a separate factory
reference; the remaining 96 matched exactly. The head was stock V15. A write
can stop between completed sectors and leave a mixed application without a
page-tail pattern that the heuristic calls torn.

The public V15 app differs from the factory-reference app. Therefore all 143
sectors differed from public V15 in this case. Do not replace that measurement
with the unrelated earlier simulation's same sector count or assume another
unit needs 143 writes.

## 10. Correct JSON password, but authentication/SSID still fails

**Cause class:** config files and flashed firmware can disagree. Changing JSON
does not change the board. ESP-IDF defaults do not override an existing sdkconfig.
WPA2 password and independent TCP secret are different values.

**Resolution:** preserve matching config/build/controller files. Credential
creation refuses accidental overwrite; deliberate --rotate archives old files,
then requires controlled rebuild/reflash. Never publish boot logs or binaries
that print/embed actual credentials. Do not rotate to work around an idle timeout.

## 11. IDF export looks for a missing Python environment

**Observed:** the host default Python differed from the environment installed
for IDF, and export attempted a nonexistent versioned venv path.

**Resolution:** use Python 3.12 and the correctly installed IDF Python environment,
set IDF_PYTHON_ENV_PATH deliberately, use IDF 5.4.1, and inspect export/build logs.
No source compatibility change justified selecting a random newer IDF.

## 12. Upstream test reports FileNotFoundError in os.getcwd()

**Observed:** missing jl-uboot-tool test dependencies caused setUp to skip after
changing into a temporary directory. Cleanup left later tests in a deleted cwd.

**Resolution:** install the pinned tool's actual requirements (crcmod, PyYAML,
pycryptodomex, tqdm), set an absolute FM1_JLUB_DIR, and run from a valid directory.
The full suite then passed without modifying upstream tests. Optional real-
package/private-fixture tests can still skip legitimately. CI/project tests
never require publishing a person's dumps.

## 13. --write rejected / ERR writes-disabled

Two independent gates are intentional. Read-only C firmware rejects wsec even
if a client asks. The client rejects unapproved writes. After an exact approved
plan, build/deploy approved-v15 --enable-app-writes with target detached; then
use --approved-v15 plus your reviewed --approval-plan and a new evidence directory.
Do not widen the C write range or use direct RAM commands as a workaround.

The no-manifest historical write option is locked to the documented original
case's hashes. Another person's valid dump must use its own generated/reviewed
manifest, not disable the hash check.

## 14. Fresh flash differs from the approved original

**Required response:** stop before writing. Upstream's baseline restore checks
head/app equality but only reports changed data sectors. This adaptation's
approved guard requires the entire fresh 1 MiB to match, including protected
settings/OTA/Bluetooth/resources. Do not silently update the expected hash or
approve only the data difference to make a command proceed.

## 15. Write starts but reply/readback is missing

Keep devices powered and connected. Save journal, client log and available board
log. STARTED without VERIFIED does not mean the sector was untouched. Existing
retries are limited to an explicit pre-erase ERR crc rejection; socket errors
are never converted to that safe rejection. Do not blindly repeat a write or
follow generic upstream reset/retry text without a newly reviewed diagnosis.

## 16. Transport echo and arbitrary binary commands

NUL-leading frames are diagnostic echo. The verified V15 frame boundaries were
checked not to collide. Do not generalize the current adapter into an arbitrary
binary flash/RAM uploader. Use the specific public V15 guard and documented
paths; new payload families need independent framing/identity/range validation.

## 17. Successful checksums but no normal boot

A verified flash image is not itself a screen/boot test. Follow the shutdown
order (FM-1 off, disconnect target cable, XIAO off, normal FM-1 power-on with
USB detached). Record the result. The completed case's owner reported success.
If another unit still fails, do not automatically erase VM/OTA, install V16 or
write a different head. Preserve original/final images and diagnose separately.
