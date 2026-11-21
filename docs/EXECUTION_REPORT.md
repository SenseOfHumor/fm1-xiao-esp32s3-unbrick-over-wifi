# Completed execution report

## Final result

A genuine FM-1 was restored to stock V15 on 2026-11-21 using the XIAO native
USB test pads/external breakout and Wi-Fi control. Saved actual evidence proves
143 verified application-sector operations, full expected final-image equality
and unchanged head/protected data. The owner reported normal operation afterward.
No head, OTA loader/record, settings, Bluetooth or resource repair was performed.

The complete chronological [case study](CASE_STUDY_2026-11-21.md) distinguishes
physical observations, saved bytes, software tests and hypotheses. A sanitized
[evidence summary](evidence/restore-verification.json) and the
[143-address acknowledgment list](evidence/verified-sectors.csv) are public.
Raw dumps, credentials, binaries and logs remain private.

## Verified facts

| Item | Result |
|---|---|
| Initial bridge | Actual ESP32-S3, 8 MiB flash and 8 MiB embedded PSRAM |
| Original XIAO preservation | Full 8 MiB saved; separate esptool verification; original hash unchanged |
| Diagnostic/read-only/approved build | All built and programmed in separate stages; programming hashes verified |
| Native connection | TP8/GPIO20/D+, TP7/GPIO19/D− and GND to external female USB-C breakout |
| Computer connection | Wi-Fi TCP; native built-in USB-C empty during target recovery |
| ROM entry | Actual KEY ACK, calibration, host handoff, 4C4A:8057 and WL82 UBOOT1.00 |
| Actual device identity | 980F / type 3 / flash 856014 / 1 MiB |
| Original FM-1 | Two independent equal reads, hash 68c5c500ed28aa73b6d9ece9ba8e12795a4985625fa76c77e66d28cfdf3ddea2 |
| Independent original | Separate read-only macOS uchg copy verified |
| Head | Byte-identical public V15 head; not rewritten |
| Plan | 143 whole sectors, 0x04000..0x92FFF; 585,728 bytes |
| Live pre-write check | Entire fresh image matched original including all protected data |
| Actual write journal | 143 STARTED + 143 VERIFIED entries in exact approved order |
| Final full image | 872d9c4c7ccce4520ba94bbc60c3d4dbc43abfee77ce686f79aa510c66f02b79 |
| Protected bytes | 00000..03FFF and 93000..FFFFF unchanged byte-for-byte |
| Normal boot | Owner reported success; no independent long-term/audio qualification claimed |

## Important retained limitations

- Unknown generic red breakout CC parts; no recorded multimeter measurements.
- The first 5-second detach's exact cause was not proven; idle ROM reset is a
  hypothesis supported by absence of subsequent commands, not a measured timer.
- Loader DAMAGED warning was solely a fixed-span trailing-erasure heuristic;
  no whole-body authentic reference was established, and no cleanup was needed.
- The initial sample simulation is not a real unit backup or approval.
- B36014 support is inherited in software; hardware recovery here used 856014.
- Public per-unit approval support/build conveniences were added after success
  and software-tested. The historical fixed-hash policy is what ran on hardware.
- An archive/commit does not publish to a GitHub fork automatically.

## Reproduction and preservation

Use [REPRODUCING.md](REPRODUCING.md), not local session paths. All older local
notes and artifacts were preserved in a private pre-publication archive; public
documents were then rewritten into consistent procedure/reference/case material.
The immutable original and raw files remain on disk. A final private archive
captures the source commit plus private evidence. See
[PRESERVATION_AND_PUBLICATION.md](PRESERVATION_AND_PUBLICATION.md).

Current tests/coverage are recorded in [VALIDATION.md](VALIDATION.md). A software
test result is never described as a new hardware attempt, and this documentation
work did not flash or operate the recovered device.
