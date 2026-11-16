# Running CAIRN in Wokwi

**Quickest:** open the ready-made project (circuit + 8 firmware files already loaded): https://wokwi.com/projects/480885243109700609 — press ▶. The steps below rebuild it from scratch (`New project` links open a blank project by design).
1. wokwi.com → *New project* → **MicroPython on ESP32**.
2. Replace `diagram.json` with `wokwi/diagram.json`. If a part type or pin name is rejected, fix it in the editor (the provided file was validated in Wokwi).
3. Add the files of `firmware/` (flat): `main.py, config.py, chainlog.py, plausibility.py, mpcrypto.py, ssd1306.py, attacker.py, keys_demo.py`. A ready folder is produced by `python3 scripts/make_assets.py` → `dist/wokwi_bundle/`.
4. If Wi-Fi/NTP fails with the chosen MicroPython build, switch `env` in `diagram.json` to `micropython-20230426-v1.20.0` (reported to work with Wokwi Wi-Fi); CAIRN still runs without NTP (timestamps then count from boot).
5. Press ▶. Use the gas slider, PIR click and DHT22 temperature to generate events. Press **ATTACK** (cycles EDIT → DELETE → TRUNCATE → REHASH) then **AUDIT**.
6. Copy the serial terminal into `dump.txt` and run `tools/verify.py` (see README).
Expected: EDIT/DELETE/TRUNCATE are flagged on the OLED; REHASH passes the on-device audit but fails the offline MAC check.
