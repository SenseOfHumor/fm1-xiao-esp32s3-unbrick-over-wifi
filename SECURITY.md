# Security and disclosure

This is a local hardware-recovery tool, not an Internet service. The SoftAP
uses WPA2 and an independent random TCP secret. TCP is not TLS; CRC only detects
corruption. Keep the AP isolated and do not forward the port or share its secrets.
The embedded controller is single-controller, not a multi-user authorization
system. A reviewed local approval file is not a cryptographic signature.

Generated sdkconfigs, binaries/ELFs, startup logs and private controller ZIPs
may expose credentials. FM-1 and XIAO full images can contain personal/device
information. Do not publish them. The source ignore rules do not protect
previously tracked files or manually uploaded release assets.

If you find a weakness, do not demonstrate it against someone else's device.
Preserve a minimal software reproduction and coordinate privately with the
maintainer of the actual fork you use; no project-specific security mailbox
or manufacturer incident-response commitment is claimed here. If a credential
has been exposed, preserve needed forensic evidence, deliberately rotate/rebuild/
reflash the affected board and never silently rotate an active recovery session.

Do not attempt speculative resets/writes in the name of security validation.
Hardware safety, original-data preservation and uncertainty-aware recovery
remain mandatory. See docs/RECOVERY_SAFETY.md.
