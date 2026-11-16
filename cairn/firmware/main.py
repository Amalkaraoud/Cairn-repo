"""CAIRN - tamper-evident home-security black box (MicroPython, ESP32 / Wokwi).

Sensors  : PIR (motion), MQ-2 (gas), DHT22 (temperature/humidity)
Evidence : every notable event is appended to a hash-chained, HMAC-sealed log
Display  : SSD1306 OLED shows live readings, chain status and the last anchor
Buttons  : ATTACK (GPIO13) simulates a log-tampering attacker,
           AUDIT  (GPIO27) runs the integrity self-check and dumps the log
"""
import time
from machine import Pin, I2C, ADC
import dht

import config as C
import attacker
from mpcrypto import from_hex
from chainlog import ChainLog
from plausibility import Plausibility
import ssd1306

try:
    import keys as K          # your private key file (git-ignored)
except ImportError:
    import keys_demo as K     # public demo key (NOT secret)


def sync_time():
    """Wi-Fi + NTP (chapter 5 / TP3). Returns True on success, never blocks forever."""
    try:
        import network
        import ntptime
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(C.WIFI_SSID, C.WIFI_PASSWORD)
        t0 = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), t0) > C.NTP_TIMEOUT_S * 1000:
                return False
            time.sleep_ms(250)
        ntptime.settime()
        return True
    except Exception as exc:   # network stack absent or NTP unreachable
        print("NTP unavailable:", exc)
        return False


def pressed(pin):
    """Debounced active-low button read."""
    if pin.value() == 0:
        time.sleep_ms(30)
        return pin.value() == 0
    return False


def draw(oled, seq, head, t, h, g, pir, status, anchor, last_ev, synced):
    oled.fill(0)
    oled.text("CAIRN #%d %s" % (seq, "NTP" if synced else "RTC?"), 0, 0)
    oled.text("T%s H%s G%d P%d" % (("%.1f" % t) if t is not None else "--",
                                   ("%d" % h) if h is not None else "--", g, pir), 0, 11)
    oled.text(status, 0, 22)
    oled.text("HEAD " + head[:8], 0, 33)
    oled.text(anchor, 0, 44)
    oled.text(last_ev[:16], 0, 55)
    oled.show()


def main():
    i2c = I2C(0, scl=Pin(C.PIN_SCL), sda=Pin(C.PIN_SDA))
    oled = ssd1306.SSD1306_I2C(128, 64, i2c)
    pir_pin = Pin(C.PIN_PIR, Pin.IN)
    gas = ADC(Pin(C.PIN_GAS_ADC))
    gas.atten(ADC.ATTN_11DB)
    sensor = dht.DHT22(Pin(C.PIN_DHT))
    led_ok = Pin(C.PIN_LED_OK, Pin.OUT)
    led_alert = Pin(C.PIN_LED_ALERT, Pin.OUT)
    btn_attack = Pin(C.PIN_BTN_ATTACK, Pin.IN, Pin.PULL_UP)
    btn_audit = Pin(C.PIN_BTN_AUDIT, Pin.IN, Pin.PULL_UP)

    oled.fill(0)
    oled.text("CAIRN booting", 0, 0)
    oled.text("syncing time...", 0, 11)
    oled.show()
    synced = sync_time()

    log = ChainLog(C.LOG_PATH, C.STATE_PATH, from_hex(K.K0_HEX))
    det = Plausibility()
    log.append(time.time(), "BOOT", "ntp=%d" % (1 if synced else 0))
    print("CAIRN ready; synced=%s; seq=%d" % (synced, log.seq))

    status, anchor, last_ev = "CHAIN:OK", "ANCHOR: none", "BOOT"
    t = h = None
    g = 0
    attack_i = 0
    next_sample = time.ticks_ms()
    samples = 0
    alert_until = 0
    last_anchor_seq = 0
    led_ok.value(1)

    while True:
        now_ms = time.ticks_ms()
        events = []
        pir = pir_pin.value()
        events += det.check_pir(pir, now_ms // 1000)

        if time.ticks_diff(now_ms, next_sample) >= 0:
            next_sample = time.ticks_add(now_ms, C.SENSOR_PERIOD_MS)
            samples += 1
            try:
                sensor.measure()
                t, h = sensor.temperature(), sensor.humidity()
                events += det.check_temp(t)
            except OSError:
                t = h = None                      # DHT22 read failed (chapter 3 pattern)
            g = gas.read()
            events += det.check_gas(g)
            if samples % C.HEARTBEAT_EVERY == 0:
                events.append(("HB", "T=%s;G=%d" % (("%.1f" % t) if t is not None else "NA", g)))

        for name, val in events:
            if log.seq >= C.MAX_RECORDS:
                break
            rec = log.append(time.time(), name, val)
            last_ev = "%s %s" % (name, val)
            print("EVT", rec["s"], name, val, rec["h"][:12])
            if name not in ("HB", "MOTION", "GAS_CLEAR"):
                led_alert.value(1)
                alert_until = time.ticks_add(now_ms, 5000)
            if log.seq - last_anchor_seq >= C.ANCHOR_EVERY:
                last_anchor_seq = log.seq
                anchor = "ANC#%d %s" % (log.seq, log.head[:6])
                print("ANCHOR %d %s" % (log.seq, log.head))   # owner copies it OFF the device

        if alert_until and time.ticks_diff(now_ms, alert_until) >= 0:
            alert_until = 0
            led_alert.value(0)

        if pressed(btn_attack):
            kind = attacker.KINDS[attack_i % len(attacker.KINDS)]
            attack_i += 1
            desc = attacker.run(kind, C.LOG_PATH)
            last_ev = "ATK " + kind
            print("ATTACK", kind, desc)
            while btn_attack.value() == 0:
                time.sleep_ms(20)

        if pressed(btn_audit):
            res = log.audit()
            if res["ok"]:
                status = "CHAIN:OK"
                led_ok.value(1)
                led_alert.value(0)
            else:
                status = "BROKEN @%s %s" % (res["bad_seq"], res["reason"][:5])
                led_ok.value(0)
                led_alert.value(1)
            print("AUDIT", res)
            try:                                  # export for the offline verifier
                with open(C.LOG_PATH) as f:
                    for line in f:
                        print("LOG", line.strip())
            except OSError:
                pass
            while btn_audit.value() == 0:
                time.sleep_ms(20)

        draw(oled, log.seq, log.head, t, h, g, pir, status, anchor, last_ev, synced)
        time.sleep_ms(C.LOOP_MS)


main()
