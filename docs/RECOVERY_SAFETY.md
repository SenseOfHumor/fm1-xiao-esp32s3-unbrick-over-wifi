# Restoration invariants and failure policy

## Device and region gates

The path is for key 980F/type 3 and pinned-upstream-supported 1 MiB flash IDs.
This hardware case restored 856014; B36014 has software support but no hardware
result here. Never normalize a strange identity or add --i-know to continue.

Application writes must be aligned whole 4 KiB sectors in **[0x4000,0x93000)**.
Preserve byte-for-byte:

- **0x00000..0x03FFF:** SPL/head and boot configuration.
- **0x93000..0xE8FFF:** VM/settings including case-specific staged loader/record.
- **0xE9000..0xE9FFF:** per-unit Bluetooth data.
- **0xEA000..0xFBFFF:** factory voices/resources.
- **0xFC000..0xFEFFF:** globals.
- **0xFF000..0xFFFFF:** key_mac.

These names follow upstream's map; not every calibration/configuration schema
was decoded. Preserving ALL bytes outside the application avoids guessing
which unknown fields are per-unit. No full/block/chip erase is offered.

## Approval is a lifecycle, not a checkbox

1. Electrical/power/CC checks on your own assembly; no target attachment before
   those are established. The prototype's undocumented measurements are a limit.
2. Verified XIAO backup, source revisions and matching build/controller credentials.
3. Read-only recovery, actual identity and two independent matching full reads.
4. Independent protected original copy and offline package/sector plan.
5. Human review/approval of that exact package, reference and address list.
6. Deliberate write-capable firmware deployment with target detached.
7. Fresh live identity and fresh ENTIRE original match before first erase.
8. Per-sector CRC/range/identity/readback checks, persistent acknowledgments.
9. Final whole-flash comparison, protected-data equality, success marker.
10. Safe shutdown and separately observed normal boot.

A generated approval JSON is not a signed authorization service; --approved-v15
is the operator's explicit declaration that review/approval occurred. The client
recomputes the plan and validates the exact known V15 file rather than trusting
arbitrary addresses from that JSON. Do not run someone else's manifest.

Historical no-manifest defaults preserve the successful case only. The optional
per-unit manifest path is the public software-tested generalization. It does
not automatically authorize a second unit and has not been hardware-tested on
one. On macOS the independent copy must retain uchg; non-macOS read-only mode is
a weaker guard and should be backed by separate offline copies.

## Firmware package

Initial stock recovery uses the exact public V15 hash in UPSTREAM.md. A matching
head in this case supported an app-only repair. The guarded manifest workflow
conservatively refuses a different head. Do not rewrite it to force a package.

V16 extends past the Transporter application boundary and is rejected. SLOOP
and arbitrary images are not alternate defaults. An image being available on a
mirror does not make its entire contents safe for another unit.

## Loader/OTA cleanup is a separate risk

In the case the analyzer's fixed span falsely implied damage merely because
it included its own record and other data after a relocated loader. A body
CRC/authenticity was not established. Neither fact authorizes erasure.

The separate upstream repair-settings command changes settings windows and can
delete configuration. It is NOT a loader-only fix, is not part of this Wi-Fi
route, and was not needed for the completed recovery. Full-restore/head writes
are likewise outside this procedure. Preserve existing restrictions.

## Interrupted operations

An explicit ERR crc reply means a payload was refused BEFORE erase and is the
only failure class eligible for the retained upstream safe retry policy.
A disconnect, missing reply, erase/program error, unknown identity or failed
readback does not establish that flash was untouched.

On failure: keep power/wiring stable, preserve all evidence, inspect the last
STARTED/VERIFIED journal entries, and obtain a separately reviewed read-only
state assessment. Do not blindly replay, reset the target or reflash the bridge
mid-operation. No transparent TCP reconnect or command replay is implemented.

## Finished operation

A success marker alone must agree with process exit zero, exact verified sector
sequence, final read hash and protected-region equality. Keep fresh/final
readback files, not just a terminal screenshot. Only then follow the documented
shutdown order. If screen boot fails, do not reinterpret the same approval as
permission for VM/OTA/head repair.

## Credentials and publication

The AP uses WPA2 plus a separate controller secret. CRC is not authentication;
there is no TLS, anti-brute-force service or Internet gateway. Keep it isolated,
use unique random credentials, and never publish credential-bearing images or
logs. Source control is not a backup system for private per-device flash.
