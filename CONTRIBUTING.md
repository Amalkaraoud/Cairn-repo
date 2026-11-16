# Contributing
Issues and pull requests are welcome. Please:
1. Run `python3 -m unittest discover -s tests` before opening a PR.
2. Keep firmware modules MicroPython-compatible (no `typing`, no f-string-heavy code, no stdlib-only modules such as `hmac`).
3. Label any new experiment as synthetic / simulated / measured, and make it seedable.
4. Never commit real keys: `firmware/keys.py` is git-ignored.
Ideas welcome: log rotation with chained segments, Merkle checkpoints, e-mail/MQTT anchoring, real-hardware measurements.
