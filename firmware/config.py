"""CAIRN configuration: pins follow the course/TP conventions."""

# --- pins (same as TP2 / TP3 / chapter 3 where possible) ---
PIN_PIR = 14        # PIR sensor output (TP2)
PIN_GAS_ADC = 34    # MQ-2 analog output (TP2)
PIN_DHT = 23        # DHT22 data (chapter 3)
PIN_SCL = 22        # OLED I2C clock (TP3)
PIN_SDA = 21        # OLED I2C data  (TP3)
PIN_LED_OK = 2      # green LED: chain OK (TP2 LED pin)
PIN_LED_ALERT = 4   # red LED: alert / tamper (TP2 second LED pin)
PIN_BTN_ATTACK = 13  # button: simulate an attacker editing the log file
PIN_BTN_AUDIT = 27   # button: run integrity audit + dump log (GPIO27: not a strapping pin)

# --- timing ---
LOOP_MS = 100            # main tick (buttons are polled at this rate)
SENSOR_PERIOD_MS = 2000  # DHT22 cannot be read faster than ~0.5 Hz
HEARTBEAT_EVERY = 5      # one HB record every N sensor samples
ANCHOR_EVERY = 10        # print an anchor every N records
MAX_RECORDS = 150        # demo cap (no rotation in v0.1)

# --- files ---
LOG_PATH = "cairn.log"
STATE_PATH = "cairn.state"

# --- network (Wokwi virtual access point) ---
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""
NTP_TIMEOUT_S = 8
