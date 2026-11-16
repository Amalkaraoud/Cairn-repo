# Architecture
```
 PIR ─┐                       ┌─► OLED (live values, chain status, anchor)
 MQ-2 ├─► Plausibility gate ─►│
 DHT22┘   (events only)       └─► ChainLog.append ─► cairn.log (JSON lines) ─► tools/verify.py (offline, K0 + anchor)
                                    │  h_i = SHA256(seq|ts|event|value|h_{i-1})
                                    │  m_i = HMAC(K_i, h_i);  K_{i+1} = SHA256(K_i)
                                    └─► ANCHOR (seq, head) printed / shown → keep off-device
```
| Module | Role |
|---|---|
| `mpcrypto.py` | SHA-256 wrapper, HMAC-SHA256 (MicroPython has no `hmac`), constant-time compare |
| `chainlog.py` | record format, append, ratchet, `verify_records`, on-device `audit` |
| `plausibility.py` | O(1) rules: TEMP_JUMP, GAS_ALARM (hysteresis), GAS_SPIKE (EWMA), MOTION, PIR_FLOOD |
| `ssd1306.py` | compact I2C OLED driver on `framebuf` |
| `attacker.py` | red-team simulation used by the ATTACK button (demo only) |
| `main.py` | sensor loop, buttons, display, Wi-Fi/NTP time with timeout fallback |

Design choices: (1) the log records **events**, not every sample, plus a periodic heartbeat so silence is itself evidence; (2) hash and MAC are separate on purpose — the hash chain is self-checkable on the device, the MAC needs a key kept offline; (3) the ratchet gives forward integrity for records written before a later compromise.
