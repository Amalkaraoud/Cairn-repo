# Threat model
**Assets:** integrity and ordering of security events. **Adversary:** can read/write the device file system after the fact (burglar, malicious tenant, compromised cloud sync) but does **not** hold K0 and cannot change what the owner stored off-device.

| Attack | Outcome | Mechanism |
|---|---|---|
| Edit / delete / insert / reorder | detected, localised to first bad record | hash chain + sequence numbers |
| Edit + recompute hashes | detected | HMAC under key unknown to attacker |
| Truncate tail | detected **only** with anchor (or in-RAM head while powered) | external anchor |
| Spoofed sensor jump / flood | event flagged and sealed | plausibility gate |
| Steal current ratcheted key | **not detected** for future/forged appended records; earlier records stay protected | forward integrity only |
| Full device compromise before logging | out of scope | needs secure element / attestation |
| Time spoofing (unauthenticated NTP) | out of scope; timestamps are advisory, `seq` is authoritative | — |
