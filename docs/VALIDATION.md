# Validation matrix and reproducibility limits

## Evidence already observed on real hardware

- Actual XIAO chip/flash identification and original 8 MiB backup/readback check.
- Diagnostic firmware boot/AP startup and on-board framed TCP loopback.
- 64 B, 512 B, 4 KiB, 64 KiB and 1 MiB echo transfers with matching SHA-256.
- On-board authentication rejection, CRC rejection, reconnect and ping.
- Later real manual Mac-to-XIAO AP communication, PONG and mode logs.
- USB_KEY/ACK/calibration/native host response from the actual FM-1.
- Real 980F/type3/856014 identity, two equal original 1 MiB reads.
- Approved 143-sector application restore, fresh/final full images, unchanged
  protected data and operator-reported normal boot.

See CASE_STUDY_2026-11-21.md and evidence/. No CI or test fixture substitutes
for these observations. No physical CC/meter, second-unit B36014, arbitrary
board/OS or long-term reliability result is claimed.

## Project software tests

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
sh tools/fetch_deps.sh
.venv/bin/python -m pytest tests -q
```

| File | Meaning |
|---|---|
| test_tcp_transport.py | Header bounds, CRC/sequence, fragments, EOF/deadlines, authentication, binary transfer, reconnect, quiet delayed status |
| test_wire_c.py | Compiles actual portable C codec and compares its bytes/length checks with Python |
| test_rom_wait.py | Zero snapshots → readiness, real wait deadline, held request/lease ping, terminal errors, no soft-key/reset, upstream info over localhost frames |
| test_backup_safety.py | Independent read preservation, mismatch/size/manifest refusal, simulated-backup exclusion and default write block |
| test_approved_v15.py | Private actual-case fixture: exact plan, protected-data mismatch stop, forbidden sector/payload/identity refusal |
| test_public_workflow.py | Public synthetic approval and credential-rotation safety, independent of private dumps |

Private case-fixture tests skip in a source-only checkout without that owner's
files and optional V15 mirror. They must not be replaced with somebody else's
files or published just to make a CI counter green. The portable suite still
checks the state/transport/codec/safety behaviors with deterministic fixtures.

Synthetic fixture identity strings are test inputs, not claimed physical IDs.
Tests never connect to the board's AP or call esptool. A C compiler is required
for codec tests; the hardware-case workstation and Ubuntu CI have one.

## Additional pinned-upstream tests

The separate upstream suite was run during development: 123 passed, four optional
checks skipped after its protocol dependencies and local V15/V16 files were made
available. Earlier runs at the original dependency pin had 87 passed/10 skipped.
Those are historical recorded runs, not a claim the upstream suite was rerun
for every later documentation edit.

If reproducing that separate suite, install requirements-dev.txt and set absolute
paths from a valid current directory:

```bash
# Run from third_party/MvaveFM1Unbricker; replace paths with your own local files.
FM1_JLUB_DIR=/absolute/project/third_party/jl-uboot-tool \
FM1_V15_FWSC=/absolute/firmware/V15-FM-1.fwsc \
FM1_V16_FWSC=/absolute/firmware/V16-FM-1.fwsc \
../../.venv/bin/python -m pytest tests -q
```

Missing CRC/YAML dependencies exposed an upstream skip/temporary-cwd bug; see
TROUBLESHOOTING.md. No upstream test or identity check was disabled to obtain
passing results.

## Publication review checks

The publication pass additionally validates project tests with private fixtures
present, a staged source-only tree without private files, Python/shell syntax,
local Markdown link targets, package/build-mode handling and staged content
against actual active credentials. A known actual-case plan can be regenerated
offline through the new per-unit policy and compared to the historic result,
without opening a transport or writing hardware.

The GitHub workflow fetches pinned dependencies and runs project software tests
on Python 3.12/Ubuntu. Configuration of that workflow is not a claim that GitHub
has executed it before the branch is pushed.

Public per-unit manifest/credential tooling was added after the successful
hardware recovery. It is software-tested, not independently hardware-qualified.
Native firmware C/timing sources remain as exercised by the hardware case.

## Recorded publication-pass results

- Project suite with the private actual-case fixture available: **57 passed**.
- Staged source-only tree with no credentials/private target fixtures: **48
  passed, 9 correctly skipped** (private case-fixture tests).
- Current per-unit planner/approval preflight reproduced the historical actual
  original hash, 143-sector list and final hash OFFLINE, without a transport.
- All local Markdown links and shell/Python syntax passed.
- Staged-file scan found no active password/session secret or private images,
  logs, generated configs or firmware packages.
- Private pre-publication archive passed SHA-256, gzip integrity and selected
  archived original/final image hash verification.

These outcomes are local publication checks, not a claim that the new GitHub
workflow has already run or another physical unit has been recovered.
