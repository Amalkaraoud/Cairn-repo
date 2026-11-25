# Related work (limited search, 2026-11-16 — not a systematic review)
* Schneier & Kelsey, *Secure Audit Logs to Support Computer Forensics*, ACM TISSEC 1999 forward-secure MACs + one-way hash chain (the ratchet idea we reuse).
* Ma & Tsudik, forward-secure sequential aggregate authentication (and truncation attacks), 2007–2009.
* Shepherd et al., *EmLog: Tamper-Resistant System Logging for Constrained Devices with TEEs*, arXiv:1712.03943 — needs a TEE.
* *Lightweight Tamper-Evident Log Integrity Verification for IoT Edge Environments: A Merkle-Tree Pipeline…*, arXiv:2605.00065 (2026).
* Saito, *Proof of Authenticity of General IoT Information with Tamper-Evident Sensors and Blockchain*, arXiv:2512.18560 (2025).
* Open-source libraries for hash-chained audit logs exist (e.g. `auditchain` on PyPI, `loghash`); IoT+blockchain sensor demos exist on GitHub.

**Positioning.** The mechanisms are known. What CAIRN contributes is an *adaptation*: a MicroPython implementation (HMAC built on `hashlib`), a plausibility gate placed *before* sealing, a heartbeat design, and a reproducible Wokwi demo with an attacker simulator. No MicroPython-specific tamper-evident logger was found in the queries made; this is not proof that none exists.
