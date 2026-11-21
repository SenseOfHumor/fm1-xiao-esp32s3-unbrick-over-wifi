# Contributing

Start with README.md, docs/ARCHITECTURE.md and docs/RECOVERY_SAFETY.md. Changes
must preserve the explicit distinction between software checks, real hardware
observations, operator reports and unproven hypotheses.

## Development checks

Use Python 3.12, requirements-dev.txt and pinned dependencies from
`sh tools/fetch_deps.sh`. Run `python -m pytest tests -q`, Python/shell syntax
checks and `git diff --check`. Ordinary tests do not contact a target. A clean
source checkout must pass without anyone's private dumps or credentials;
case-fixture tests may skip, but portable safety/protocol tests must remain.

For firmware changes, use ESP-IDF 5.4.1 and record build mode/configuration.
Changing timing, PHY ownership, range gates or USB command ordering needs
specific evidence and separate hardware validation. Do not broadly replace
working timings to mask a stale status reply or an unknown electrical circuit.

## Safety-sensitive reviews

Never widen application writes beyond aligned [0x4000,0x93000), remove loader
hash checks, infer compatibility from enumeration alone, or add automatic
retry/reset after uncertain writes. Keep writes disabled in default/read-only
builds and in the client without explicit reviewed approval. Preserve original
and final readbacks, per-sector journal and full-image verification.

Public per-unit approval support is deliberately distinct from historical
fixed-hash reproduction. Do not edit case constants to make another unit pass.
Do not describe a new software refactor as hardware-proven until it actually is.

## Reports

Include board/revision, OS/Python/IDF versions, source commits, sanitized mode
flags, exact error/state transitions and relevant timestamps. Explain what was
actually measured. A generic breakout needs a real circuit/pin assessment;
color/LED/silkscreen alone is not that evidence.

Do NOT attach Wi-Fi secrets, complete generated images/configs, raw full-flash
files, Bluetooth addresses/keys or device-specific data to public issues. Share
sanitized text, hashes, region addresses and reproducible software fixtures.
Keep raw evidence privately until a safe sharing path is agreed.

## Attribution and distribution

Preserve MIT notices and links to the upstream sources. Do not add proprietary
loader/firmware binaries or cached manufacturer schematics as MIT source.
A Git branch/commit is not permission to push to the original author's remote.
