# Physical-integration checklist

For the full action use [REPRODUCING.md](REPRODUCING.md); for schematic/electrical
reasoning use [WIRING.md](WIRING.md). This page is a quick mode/connection check.

## Programming state

- FM-1 OFF and physically detached from the external breakout.
- XIAO in ROM downloader mode, built-in USB-C connected to computer.
- Actual serial port/chip detected, not assumed from an old log.
- Original complete XIAO flash preserved and verified.
- Flash ONE mode's matching bootloader/table/application with --after no-reset.
- Require every esptool hash verification and Staying in bootloader.

## Battery/Wi-Fi state

- Unplug computer USB BEFORE starting/resetting recovery firmware.
- Restore checked battery/protection supply; built-in USB-C remains EMPTY.
- No active external charger or power jumper supplies breakout VBUS.
- Manually join the AP using this board's local credentials.
- Require actual PONG and current recovery-mode logs, not an old diagnostic file.
- Do not rotate the independent TCP secret to solve a network timeout.

## Target state

- Complete electrical checks on TP8/D+, TP7/D−, common ground, isolated VBUS,
  cable routing/orientation and actual breakout CC circuit before attachment.
- XIAO already keying; FM-1 initially OFF and on its independent battery.
- Target cable connects to EXTERNAL breakout, never XIAO built-in receptacle.
- Start one real dump/readiness command, then switch FM-1 ON promptly.
- Identify real ROM, then processor/type/flash; require two matching original reads.
- Any write needs a separate reviewed per-unit plan and write-capable deployment.

## Stop states

Diagnostic firmware, unknown power/CC wiring, unexplained bus level, unsupported
identity, mismatched backups, stale approval, changed protected data or uncertain
write outcome means stop. No automatic rekey/reset, identity override, settings
repair or head write is part of this checklist.

The completed prototype produced a genuine ROM response and verified restore
but did not record all electrical measurements. Do not infer those checks
passed merely because the final result worked.
