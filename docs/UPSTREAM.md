# Provenance, hashes and third-party material

## Source lineage

| Project | Revision used | Role |
|---|---|---|
| [dagnazty/fm1-esp32-unbrick](https://github.com/dagnazty/fm1-esp32-unbrick) | b87e11c2159c7b46de2f21e72ffdec289e9d7b60 | Primary ESP32-S3 native recovery port |
| [kurogedelic/FM-1-transporter](https://github.com/kurogedelic/FM-1-transporter) | 14fd4dfe08b5afb403693142b07fcb21a95092ba | Original USB_KEY/ROM protocol and hardware guidance |
| [Quixotic7/MvaveFM1Unbricker](https://github.com/Quixotic7/MvaveFM1Unbricker) | 331f848c96842bd7e3d4ab4bcdc05604fe64f9a2 | Pinned high-level client, identity/package/restore safeguards |
| [kagaimiq/jl-uboot-tool](https://github.com/kagaimiq/jl-uboot-tool) | adb3f18889e88ac512ce0a3c4d8cc3d3cb30696a | JieLi helper source location/protocol definitions |
| [Quixotic7/FM1Backups](https://github.com/Quixotic7/FM1Backups) | 8cbc3b066ed15ec6a0d5a990efb78b56f6c17183 | V15 mirror and separately identified factory reference |
| [Espressif ESP-IDF](https://github.com/espressif/esp-idf) | v5.4.1 / 4c2820d377d1375e787bcef612f0c32c1427d183 | Tested build SDK |

The primary fetch script originally pinned the high-level client to
517b9387e62e908115e5eec66c32d0ac3289f039. It was inspected/tested, then deliberately
updated to 331f848... for current supported flash-ID checks and package safeguards.
The existing related user checkout was not overwritten. Pinned third-party trees
are fetched separately and excluded from this source repository.

The adaptation's original upstream README is preserved as
../README.upstream.md. Its earlier dual-USB/UART instructions and its
November 1 hardware result belong to that project, not this November 21 case.

## Loader integrity — both checks retained

`data/loaderblobs/usb/wl82loader.bin` from the pinned jl-uboot-tool tree:

`d41da6126760c9d66660bcc0cac8d27d221806c5e369a8036921efe68dca5376`

The dependency fetch script verifies that SHA-256 before copying the 24,064-byte
blob; main/CMakeLists.txt independently refuses an incorrect/missing blob. No
placeholder, guessed loader or unchecked download is accepted.

The helper is proprietary third-party material, not relicensed by this MIT
repository. Fetching a known file is not permission to publish it or embedded
binaries. Neither the blob nor built credential-bearing images are committed.

## Public stock V15 identity

The already validated V15-FM-1.fwsc came from the pinned recovery-project mirror.
Its authenticity is established to that pinned project's known hashes, not a
manufacturer digital signature newly checked by this adaptation.

| Artifact/region | SHA-256 |
|---|---|
| V15 .fwsc file | db1642b2b6fa5c2cccb11ffd13878068bb28601678d3644049f99dc40e7edb8a |
| V15 application 0x4000..0x92FFF | 6edf3c37fb5bbbc33607c89375ee024d5477c17914d72221c8c68e58a8255686 |
| Stock V15 head | d9f43191777656de01c7bed4f9e9ba2e34e94832c5d2ed02c3fc7ab7a6d9bd67 |

No V15 file is committed. Obtain it while online, verify it, keep it on the
computer; the entire FM-1 image need not reside on the XIAO. Do not replace it
with V16 merely because a manufacturer's current download changed. V16 reaches
past this Transporter route's protected application boundary and is rejected.

The factory-reference app differs from downloadable V15. Its full reference
hash is bf6371a494c3f7313672a4b393ded14b101ad8be8a93f06768076c2e27aa6ebd.
That file is explicitly a separate unit/reference, not this owner's original.
Do not treat reference device-specific data as portable calibration/settings.

## Hardware sources

- [Seeed V1.3 schematic, 2026-01-15](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_V1.3_SCH_260115.pdf), page 4 / sheet 03 ESP32S3.
- [Seeed V1.1 schematic](https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/XIAO_ESP32S3_SCH_v1.1.pdf), previously inspected as well.
- [Seeed specifications](https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/).
- [ESP-IDF 5.4.1 USB host documentation](https://docs.espressif.com/projects/esp-idf/en/v5.4.1/esp32s3/api-reference/peripherals/usb_host.html).

Schematic PDFs were cached privately for inspection. Source files link to their
owners instead of claiming their diagrams are MIT-licensed material here.
The external red breakout has no identified manufacturer/specification. No model
number, CC component value or safety certification is inferred from its color.

## Attribution

Preserve LICENSE: dag's ESP32 port, Leo Kuroshita's FM-1 Transporter,
Michael P Jones's recovery tooling and Andrey Grigoryev's JieLi work underpin
this adaptation. SWAPNIL's XIAO/Wi-Fi integration is additive. No manufacturer
endorsement, warranty or trademark ownership is claimed.
