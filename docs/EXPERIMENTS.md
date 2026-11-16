# Experiments
Run `python3 experiments/run_experiments.py` (seeded, ~40 s). Output: `experiments/results/results.json`.

**Data status:** all data are **synthetic** and all runs are on a **host computer** (CPython) using the firmware modules unchanged. Nothing here was measured on an ESP32 or in Wokwi.

* **E1 — tampering.** 300 random logs (20–150 records) per attack; verifiers: chain-only, chain+MAC, chain+MAC+anchor. Results are deterministic consequences of the construction; the key-compromise row shows the documented limit.
* **E2 — plausibility.** 100 traces per fault, 1500 ticks (0.5 s) each; gas/temperature sampled every 2 s. Baseline = fixed gas threshold of 2000 (TP2). The adaptive rule alone misses a slow ramp, the fixed threshold alone misses a 1200 spike: the rules are complementary. False alarms on clean traces: 13 gas alarms in 37 500 gas samples (≈0.035 %).
* **E3 — overhead.** ≈274 bytes per record (JSON). Host timings are indicative only.
