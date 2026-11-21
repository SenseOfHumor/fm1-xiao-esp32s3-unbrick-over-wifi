# XIAO ESP32-S3 Sense Wi-Fi recovery guide

This stable entry point replaces the earlier accumulated session-specific guide.
All earlier local versions, builds, credentials and evidence were retained in
a private preservation archive before public documentation was reorganized.

Read in this order:

1. [README](../README.md): scope, hardware map, quickstart and restrictions.
2. [WIRING](WIRING.md): actual external breakout, test-pad/resistor relationships,
   CC/VBUS and measurements that cannot be inferred from successful operation.
3. [BUILD_AND_FLASH](BUILD_AND_FLASH.md): ESP-IDF/Python, original XIAO backup,
   three build modes, cold downloader entry and no-reset deployment.
4. [REPRODUCING](REPRODUCING.md): complete offline operational sequence, exact
   commands and human approval points using the reader's own unit and backups.
5. [RECOVERY_SAFETY](RECOVERY_SAFETY.md): protected regions, failure/shutdown policy.
6. [CASE_STUDY](CASE_STUDY_2026-11-21.md): actual completed unit, chronological
   errors, real hashes, minimal repair and limitations of the evidence.

Do not use another owner's hash/143-sector approval as your own. The historical
fixed policy reproduces only the completed case; the public per-unit plan route
is software-tested and requires a newly reviewed approval. It has not been
hardware-tested on a second unit.

The original upstream dual-port UART guide is retained separately in
../README.upstream.md. The actual XIAO route uses TP8/TP7/GND to an external
female connector, built-in USB-C empty during recovery and computer TCP over
manually selected Wi-Fi. No new controller, UART adapter or speculative GPIO
substitution is needed for this documented route.
