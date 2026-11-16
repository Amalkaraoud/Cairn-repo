#!/usr/bin/env python3
"""Generate wokwi/diagram.json, the wiring schematic and result figures from one source of truth."""
import json, os, shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
INK, AMBER, TEAL, GREY, PAPER, RED = "#14213D", "#E0A030", "#2A9D8F", "#8D99AE", "#F6F3EC", "#C8553D"

PARTS = [
    {"type": "board-esp32-devkit-c-v4", "id": "esp", "top": 0, "left": 0,
     "attrs": {"env": "micropython-20231005-v1.21.0"}},
    {"type": "board-ssd1306", "id": "oled1", "top": 150, "left": 230, "attrs": {"i2cAddress": "0x3c"}},
    {"type": "wokwi-dht22", "id": "dht1", "top": -150, "left": 120, "attrs": {"temperature": "24", "humidity": "45"}},
    {"type": "wokwi-pir-motion-sensor", "id": "pir1", "top": -150, "left": -110, "attrs": {}},
    {"type": "wokwi-gas-sensor", "id": "gas1", "top": 120, "left": -260, "attrs": {}},
    {"type": "wokwi-led", "id": "led1", "top": 300, "left": 20, "attrs": {"color": "green"}},
    {"type": "wokwi-led", "id": "led2", "top": 300, "left": 90, "attrs": {"color": "red"}},
    {"type": "wokwi-resistor", "id": "r1", "top": 250, "left": 10, "rotate": 90, "attrs": {"value": "220"}},
    {"type": "wokwi-resistor", "id": "r2", "top": 250, "left": 80, "rotate": 90, "attrs": {"value": "220"}},
    {"type": "wokwi-pushbutton", "id": "btn1", "top": 330, "left": 170, "attrs": {"color": "red", "label": "ATTACK"}},
    {"type": "wokwi-pushbutton", "id": "btn2", "top": 330, "left": 250, "attrs": {"color": "blue", "label": "AUDIT"}},
]
# (from, to, colour, label, group)
CONN = [
    ("oled1:VCC", "esp:3V3", "red", "3V3", "OLED"), ("oled1:GND", "esp:GND.1", "black", "GND", "OLED"),
    ("oled1:SCL", "esp:22", "green", "GPIO22 (SCL)", "OLED"), ("oled1:SDA", "esp:21", "blue", "GPIO21 (SDA)", "OLED"),
    ("dht1:VCC", "esp:3V3", "red", "3V3", "DHT22"), ("dht1:GND", "esp:GND.2", "black", "GND", "DHT22"),
    ("dht1:SDA", "esp:23", "orange", "GPIO23", "DHT22"),
    ("pir1:VCC", "esp:5V", "red", "5V", "PIR"), ("pir1:GND", "esp:GND.2", "black", "GND", "PIR"),
    ("pir1:OUT", "esp:14", "yellow", "GPIO14", "PIR"),
    ("gas1:VCC", "esp:3V3", "red", "3V3", "MQ-2"), ("gas1:GND", "esp:GND.1", "black", "GND", "MQ-2"),
    ("gas1:AOUT", "esp:34", "purple", "GPIO34 (ADC)", "MQ-2"),
    ("esp:2", "r1:1", "green", "GPIO2", "LED vert"), ("r1:2", "led1:A", "green", "220 ohm", "LED vert"),
    ("led1:C", "esp:GND.3", "black", "GND", "LED vert"),
    ("esp:4", "r2:1", "red", "GPIO4", "LED rouge"), ("r2:2", "led2:A", "red", "220 ohm", "LED rouge"),
    ("led2:C", "esp:GND.3", "black", "GND", "LED rouge"),
    ("esp:13", "btn1:1.l", "red", "GPIO13", "BTN ATTACK"), ("btn1:2.l", "esp:GND.3", "black", "GND", "BTN ATTACK"),
    ("esp:27", "btn2:1.l", "blue", "GPIO27", "BTN AUDIT"), ("btn2:2.l", "esp:GND.3", "black", "GND", "BTN AUDIT"),
]

def write_diagram():
    d = {"version": 1, "author": "CAIRN", "editor": "wokwi", "parts": PARTS,
         "connections": [[a, b, c, []] for a, b, c, _, _ in CONN], "dependencies": {}}
    with open(os.path.join(ROOT, "wokwi", "diagram.json"), "w") as f:
        json.dump(d, f, indent=2)

def wiring_fig():
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=200)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER); ax.axis("off")
    ax.set_xlim(0, 110); ax.set_ylim(-1, 62)
    ax.add_patch(FancyBboxPatch((44, 8), 22, 46, boxstyle="round,pad=0.5,rounding_size=2", fc=INK, ec=INK))
    ax.text(55, 51, "ESP32 DevKit", color="white", ha="center", fontsize=12, fontweight="bold")
    ax.text(55, 48.3, "MicroPython", color=AMBER, ha="center", fontsize=9)
    left = [("PIR", "OUT  GPIO14", "VCC 5V · GND", 46), ("MQ-2", "AOUT GPIO34 (ADC)", "VCC 3V3 · GND", 34),
            ("LED vert", "GPIO2 + 220 Ω", "chaîne OK", 22), ("LED rouge", "GPIO4 + 220 Ω", "alerte / altération", 10)]
    right = [("DHT22", "DATA GPIO23", "VCC 3V3 · GND", 46), ("OLED SSD1306", "SDA GPIO21 · SCL GPIO22", "VCC 3V3 · GND (I²C 0x3C)", 34),
             ("Bouton ATTACK", "GPIO13 (pull-up)", "→ GND", 22), ("Bouton AUDIT", "GPIO27 (pull-up)", "→ GND", 10)]
    for items, x0, x1, side in ((left, 3, 44, "L"), (right, 77, 66, "R")):
        for name, l1, l2, y in items:
            ax.add_patch(FancyBboxPatch((x0, y - 3.4), 30, 8, boxstyle="round,pad=0.3,rounding_size=1.2", fc="white", ec=TEAL, lw=1.6))
            ax.text(x0 + 1.5, y + 2.2, name, fontsize=10, fontweight="bold", color=INK, va="center")
            ax.text(x0 + 1.5, y - 0.2, l1, fontsize=8, color=INK, va="center")
            ax.text(x0 + 1.5, y - 2.1, l2, fontsize=7.4, color=GREY, va="center")
            xe = x0 + 30 if side == "L" else x0
            ax.plot([xe, x1], [y + 0.5, y + 0.5], color=AMBER, lw=2)
            ax.plot([x1], [y + 0.5], "o", color=AMBER, ms=5)
    ax.text(55, 0.5, "Schéma de câblage généré à partir de wokwi/diagram.json — GND commun, broches alignées sur les TP", ha="center", fontsize=8.5, color=GREY)
    fig.savefig(os.path.join(ROOT, "assets", "wiring.png"), facecolor=PAPER, bbox_inches="tight"); plt.close(fig)

def charts():
    r = json.load(open(os.path.join(ROOT, "experiments", "results", "results.json")))
    t = r["tamper"]
    labels = {"EDIT": "Modification", "DELETE": "Suppression", "REORDER": "Réordonnancement", "INSERT_FAKE": "Insertion",
              "EDIT_REHASH": "Modif. + re-hachage", "TRUNCATE_TAIL": "Troncature de fin", "KEY_COMPROMISE_APPEND": "Clé volée (ajout)"}
    order = list(labels)
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=200); fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    w = 0.26; xs = range(len(order))
    for k, (key, col, name) in enumerate((("chain_only", GREY, "Chaîne seule"), ("chain_mac", TEAL, "Chaîne + HMAC"), ("chain_mac_anchor", AMBER, "Chaîne + HMAC + ancre"))):
        vals = [t[o][key] for o in order]
        ax.bar([x + (k - 1) * w for x in xs], vals, w, color=col, label=name)
        for x, v in zip(xs, vals):
            if v == 0:
                ax.text(x + (k - 1) * w, 2, "0", ha="center", fontsize=8, color=INK)
    ax.set_xticks(list(xs)); ax.set_xticklabels([labels[o] for o in order], rotation=18, ha="right", fontsize=8.5)
    ax.set_ylabel("Taux de détection (%)"); ax.set_ylim(0, 112)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=8.5, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.12))
    ax.set_title("300 essais par attaque · données synthétiques · exécution hôte", fontsize=8.5, color=GREY, y=-0.42)
    fig.savefig(os.path.join(ROOT, "assets", "fig_tamper.png"), facecolor=PAPER, bbox_inches="tight"); plt.close(fig)
    f = r["plausibility"]["faults"]
    names = {"TEMP_SPOOF": "Saut de température", "GAS_SPIKE_1200": "Pic de gaz (1200)", "GAS_ALARM_2400": "Gaz > seuil (2400)",
             "GAS_SLOW_RAMP": "Montée lente du gaz", "PIR_FLOOD": "Inondation PIR"}
    order = list(names)
    fig, ax = plt.subplots(figsize=(9, 4.4), dpi=200); fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    gas = {"GAS_SPIKE_1200", "GAS_ALARM_2400", "GAS_SLOW_RAMP"}
    ax.bar([i - 0.2 for i in range(len(order))], [f[o]["recall_fixed_threshold_pct"] if o in gas else 0 for o in order], 0.38, color=GREY, label="Seuil fixe seul (TP2), gaz uniquement")
    ax.bar([i + 0.2 for i in range(len(order))], [f[o]["recall_full_pct"] for o in order], 0.38, color=TEAL, label="CAIRN (règles combinées)")
    ax.set_xticks(range(len(order))); ax.set_xticklabels([names[o] for o in order], rotation=15, ha="right", fontsize=8.5)
    ax.set_ylabel("Rappel (%)"); ax.set_ylim(0, 112)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=8.5, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.12))
    fa = r["plausibility"]["false_alarms"]
    ax.set_title("100 traces/défaut · synthétique · fausses alarmes sur traces saines : %d gaz, %d temp., %d PIR (150 000 ticks)" % (fa["gas"], fa["temp"], fa["pir"]), fontsize=8, color=GREY, y=-0.42)
    fig.savefig(os.path.join(ROOT, "assets", "fig_plausibility.png"), facecolor=PAPER, bbox_inches="tight"); plt.close(fig)

def bundle():
    dst = os.path.join(ROOT, "dist", "wokwi_bundle")
    shutil.rmtree(dst, ignore_errors=True); os.makedirs(dst)
    for fn in os.listdir(os.path.join(ROOT, "firmware")):
        if fn.endswith(".py"): shutil.copy(os.path.join(ROOT, "firmware", fn), dst)
    shutil.copy(os.path.join(ROOT, "wokwi", "diagram.json"), dst)

if __name__ == "__main__":
    write_diagram(); wiring_fig(); charts(); bundle(); print("assets ok")
