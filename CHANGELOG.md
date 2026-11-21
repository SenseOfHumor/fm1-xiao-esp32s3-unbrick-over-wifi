# Changelog

## Unreleased — XIAO ESP32-S3 Sense Wi-Fi adaptation

### Hardware case completed 2026-11-21

- Battery-powered XIAO native TP8/TP7/GND → external female USB-C breakout;
  built-in USB-C reserved for programming and empty during target recovery.
- Authenticated framed Wi-Fi TCP replaces the computer UART channel.
- Real ROM entry, 980F/type3/856014 identification and two matching full backups.
- Corrected quiet TCP polling and zero-status readiness semantics without
  changing the successful native USB_KEY/calibration timings.
- Approved public V15 application-only restore: 143 sectors, full verification,
  unchanged head/protected data, owner-reported normal boot.
- Retained separate diagnostic, read-only and explicitly write-capable images;
  original XIAO/target evidence preserved privately.

### Publication preparation after recovery

- Detailed source/reproduction/build/hardware/safety/protocol/case documentation;
  original upstream README and attribution preserved.
- Optional per-unit offline approval plans replace the need to edit historical
  case hashes. Software-tested; not claimed as a second hardware recovery.
- Credential generator refuses accidental rotation and preserves deliberate
  rotation copies. Build helper exposes an explicit write-capable preset and
  checks SDK/memory/mode/credential consistency.
- Private controller packager includes current adapters and refuses overwrites.
- Public synthetic tests, optional private-fixture skips, source-only test check
  and CI configuration. No raw device images, secrets or proprietary packages
  committed. No firmware/target action was taken during publication work.
