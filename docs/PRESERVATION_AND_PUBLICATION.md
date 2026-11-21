# Preserve evidence; publish source safely

## Two different products

A public source checkout is a reproducible workflow, not a person's recovery
archive. Preserve both separately:

| Public Git content | Private evidence |
|---|---|
| Source, tests, config defaults, build helpers | Actual Wi-Fi password/session secret |
| Pin/region definitions and safeguards | Generated sdkconfigs, ELF/maps and compiled images |
| Pinned source revisions and firmware hashes | XIAO original full flash |
| Sanitized case outcome and sector addresses | FM-1 original independent reads and per-unit data |
| Known errors, workarounds and explicit limits | Fresh/final full readbacks, raw logs and journals |
| License/attribution and external source links | Controller ZIPs, firmware packages and forensic archives |

A compiled image includes the board credentials; a USB boot log prints them.
Ignoring only the JSON is not sufficient. A device dump can contain Bluetooth
addresses/keys, settings, sounds and other personal data. Do not upload raw
full-flash files just to prove a checksum. A hash does not reconstruct those bytes.

The original case password was local-only and is not published. Generate unique
random credentials. CRC is integrity, not authentication; do not expose the
plain TCP service to untrusted or Internet networks.

## What was preserved for this completed case

Before reorganizing public files, a private compressed archive captured the
entire working repository, INCLUDING .git, ignored source/configuration, venv,
all diagnostic/read-only/write-enabled builds, raw logs, original/final dumps,
private approval plans, controller ZIP and local offline Markdown guides. The
independent immutable backup directory was also included. The source working
files were not replaced by an empty clone.

A second archive after the publication commit preserves the final public
checkout plus private working evidence and commit. Archive paths/hashes and a
file/flag inventory are recorded privately, not committed as a list of personal
filesystem paths. Archive files are private (mode 0600, parent mode 0700).
An archive's presence is verified by listing members, reading its contents and
checking its SHA-256; do not claim a successful backup solely because tar opened.

The raw artifacts remain at their existing local paths. macOS uchg protects
the independent original against accidental modification/deletion, but an owner
can deliberately clear it; this is not hardware WORM. A tar extraction may
not restore every filesystem flag automatically. Preserve originals as-is,
verify extraction hashes, and re-establish appropriate locks deliberately.
External SDK/toolchain installations are left unchanged and their revisions
are recorded, but the project archive is not a full-machine operating-system
image. Do not remove original files after making an archive or rely on a single disk.

## Suggested archive manifest for another recovery

Record source/SDK/tool versions, original and final full hashes, original-size
checks, independent-read equality, immutable/read-only status, identities,
approved address list, firmware hashes, last STARTED/VERIFIED sector, final
protected-data equality and actual normal-boot observation. Distinguish direct
measurements, operator reports, hypotheses and simulations explicitly.

Keep each attempt in a fresh directory. Never repeatedly tee to a single file;
ESP32 logs are both rolling and consumptive. A terminal screenshot is not a
substitute for original binary data or a complete write journal.

## Review before a source commit

1. Run git status --short and inspect every staged path.
2. Check that originals, packages, credentials, generated configs, images and
   archives are ignored. Do not use git add -f for them.
3. Search staged text/blob bytes for the actual active password and TCP secret
   WITHOUT printing the secret as a shell argument or into tool logs.
4. Check private absolute paths/serial MACs, old session passwords and references
   to non-distributed files. Replace active examples with placeholders.
5. Include sanitized outcome JSON, exact region addresses and source hashes
   instead of raw device artifacts. Preserve upstream MIT notices.
6. Validate Markdown links, shell/Python syntax, software tests and a clean
   source-only checkout without private fixtures. Do not claim CI validates
   a physical board or that a software refactor was hardware-retested.

.gitignore is a guardrail, not proof: previously tracked files bypass ignore
rules. Review staged diffs and binary content before committing.

## Public source destination

The owner subsequently authorized publication of the reviewed source to
https://github.com/SenseOfHumor/fm1-esp32-unbrick, a fork of the original
project. Private archives, credentials, generated builds and full device dumps
remain local. Publishing source does not require publishing those files.

The local `origin` remote points to the owner's fork; `upstream` preserves the
original author's repository. Review `git remote -v` before subsequent pushes.
GitHub authentication is supplied by the authenticated GitHub CLI/keychain,
not by a credential committed to this repository. Public cloning requires no
GitHub credentials. Each operator generates their own Wi-Fi and TCP secrets.

No credential-bearing binary, private controller ZIP or archive is a public
release asset. Reproduce firmware from reviewed source with new credentials.
Do not redistribute M-VAVE packages/JieLi loader or Seeed PDFs under this
project's MIT license; link their owners and respect their terms.
