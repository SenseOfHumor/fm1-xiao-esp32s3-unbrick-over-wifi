# Real ROM readiness and first detach investigation

## Evidence

The operator's actual Terminal transcript showed KEY ACK at 130.313 s,
calibration at 130.315, host handoff at 131.816, mount at 132.415, WL82 UBOOT1.00
INQUIRY/UBOOT_IDENTIFIED at 133.917, and detach at 137.418. That is 5.003 s after
mount and **3.501 s after INQUIRY**. No loader or identity query was logged
between them. This was actual hardware, not a simulator.

At inspection, the reused saved log contained only later no-device entries.
The firmware ring holds 16 KiB, overwrites oldest data and consumes entries on
read. Reusing tee filename also replaced the earlier capture. The operator
provided the original interval explicitly; the case study labels that provenance.
The client failure log itself was present and showed zero status then immediate
error despite --wait 180.

## Why status prematurely ended the wait

Pinned upstream wait_status sends one request and returns its first OK reply.
Zero/zero therefore triggered ensure_uboot's failure rather than continuing to
wait. The server holds status until ready or 20 s after USB host start; a zero
snapshot can legitimately arrive after a device detached. Its worker cannot
normally dispatch status while blocking in the KEY loop, so older KEY logs and
later zero flags are not proof of simultaneous states.

The Wi-Fi wrapper now waits until ready/deadline/real terminal error, maintains
one pending request, retries status only after a completed zero reply, and
sends harmless ping every 15 s through the RX task to keep the TCP idle lease
alive. It returns immediately on uboot=1 so checked info follows promptly. It
never sends soft-key/reset automatically. An earlier separate adapter fix made
quiet .5-second polls nonfatal while retaining partial framed data.

## Do readiness flags match INQUIRY?

host.c sets uboot_ready=true immediately before UBOOT_IDENTIFIED on the same
worker that dispatches protocol commands. Status reads dev && uboot_ready.
DEV_GONE closes the device and clears the flag. The observed transcript and
later zero reply fit that lifecycle. No state-flag or USB timing firmware change
was required to fix the confirmed client semantic bug.

## What is known about the detach

The host daemon/client tasks continue indefinitely; no intentional five-second
host shutdown follows INQUIRY. The 2-second command timeout is not a general
host lifetime. There was no subsequent timeout/loader command in the interval.

jl_ensure_loader starts only when info/read needs it. jl_keepalive returns while
loader_running is false. Consequently a successful INQUIRY followed by no client
info leaves ROM idle without helper keepalive. A ROM idle reset/watchdog is
plausible, not proven. Another ROM-stage comment mentions an approximate idle
reset in a different RAM-command context; it is not a measured specification
for this event. Power or connection instability cannot be excluded from one log.

The first remedy was prompt client readiness→info and one-session dump, not
proactive firmware helper startup. Actual identity, two matching full reads and
later a verified restoration succeeded without altering USB_KEY/calibration.
That success does not retroactively identify the exact detach cause.

## Operational consequence

After detach the existing host loop does not re-enter KEY automatically. A
client wait cannot resurrect the old session. Prepare new physical attempts
deliberately, never automatic rekey/reset after uncertain writes. Capture fresh
before/after logs under unique filenames and preserve the client's own output.
Do not insert manual log commands or delays between ready and loader startup.

Regression tests exercise quiet fragmented TCP, zero→ready, deadline, held
requests/keepalive, terminal errors, no soft-key/reset, disconnect without replay
and immediate checked identity. These are software checks, not additional
hardware observations. See VALIDATION.md and CASE_STUDY_2026-11-21.md.
