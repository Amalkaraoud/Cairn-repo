"""Sensor plausibility gate: flags physically implausible or abnormal readings.

Three lightweight rules (no ML, a few floats of state, O(1) per sample):

* TEMP_JUMP  - temperature step between two samples larger than a physical bound
* GAS_ALARM  - fixed threshold (same 2000 threshold as TP2) with hysteresis
* GAS_SPIKE  - adaptive EWMA mean / mean-absolute-deviation z-score
* PIR_FLOOD  - too many rising edges in a sliding window (replay / jamming)
* MOTION     - simple rising-edge event
"""


class Plausibility:
    def __init__(self, max_temp_step=4.0, gas_alarm=2000, gas_hyst=150,
                 alpha=0.1, z_thresh=5.0, min_dev=15.0, warmup=10,
                 pir_window_s=10, pir_flood_n=6):
        self.max_temp_step = max_temp_step
        self.gas_alarm = gas_alarm
        self.gas_hyst = gas_hyst
        self.alpha = alpha
        self.z_thresh = z_thresh
        self.min_dev = min_dev
        self.warmup = warmup
        self.pir_window_s = pir_window_s
        self.pir_flood_n = pir_flood_n
        self.prev_temp = None
        self.gas_mean = None
        self.gas_dev = min_dev
        self.gas_n = 0
        self.gas_alarm_on = False
        self.pir_prev = 0
        self.pir_edges = []
        self.flood_on = False

    def check_temp(self, t):
        ev = []
        if self.prev_temp is not None and abs(t - self.prev_temp) > self.max_temp_step:
            ev.append(("TEMP_JUMP", "%.1f" % t))
        self.prev_temp = t
        return ev

    def check_gas(self, g):
        ev = []
        if g >= self.gas_alarm and not self.gas_alarm_on:
            self.gas_alarm_on = True
            ev.append(("GAS_ALARM", str(g)))
        elif g < self.gas_alarm - self.gas_hyst and self.gas_alarm_on:
            self.gas_alarm_on = False
            ev.append(("GAS_CLEAR", str(g)))
        if self.gas_mean is None:
            self.gas_mean = float(g)
            self.gas_n = 1
            return ev
        dev = self.gas_dev if self.gas_dev > self.min_dev else self.min_dev
        z = (g - self.gas_mean) / dev
        anomalous = self.gas_n >= self.warmup and z > self.z_thresh
        if anomalous and not self.gas_alarm_on:
            ev.append(("GAS_SPIKE", str(g)))
        if not anomalous:                       # do not let anomalies poison the baseline
            diff = g - self.gas_mean
            self.gas_mean += self.alpha * diff
            self.gas_dev += self.alpha * (abs(diff) - self.gas_dev)
        self.gas_n += 1
        return ev

    def check_pir(self, value, now_s):
        ev = []
        rising = value and not self.pir_prev
        self.pir_prev = value
        if rising:
            self.pir_edges.append(now_s)
            ev.append(("MOTION", "1"))
        cutoff = now_s - self.pir_window_s
        self.pir_edges = [x for x in self.pir_edges if x >= cutoff]
        if len(self.pir_edges) >= self.pir_flood_n:
            if not self.flood_on:
                self.flood_on = True
                ev.append(("PIR_FLOOD", str(len(self.pir_edges))))
        elif len(self.pir_edges) < self.pir_flood_n // 2:
            self.flood_on = False
        return ev
