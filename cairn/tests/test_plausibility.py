import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "firmware"))
from plausibility import Plausibility  # noqa: E402


class TestPlausibility(unittest.TestCase):
    def test_temp_jump(self):
        p = Plausibility()
        self.assertEqual(p.check_temp(24.0), [])
        self.assertEqual(p.check_temp(24.5), [])
        self.assertEqual(p.check_temp(40.0)[0][0], "TEMP_JUMP")

    def test_gas_alarm_hysteresis(self):
        p = Plausibility()
        names = [e[0] for g in (400, 400, 2100, 2100, 1900, 1800, 400) for e in p.check_gas(g)]
        self.assertEqual(names.count("GAS_ALARM"), 1)
        self.assertEqual(names.count("GAS_CLEAR"), 1)

    def test_gas_spike_after_warmup(self):
        rnd = random.Random(1)
        p = Plausibility()
        for _ in range(60):
            p.check_gas(int(rnd.gauss(400, 30)))
        self.assertIn("GAS_SPIKE", [e[0] for e in p.check_gas(1100)])

    def test_no_false_alarm_on_noise(self):
        rnd = random.Random(2)
        p = Plausibility()
        flagged = [e for _ in range(2000) for e in p.check_gas(int(rnd.gauss(400, 30)))]
        self.assertEqual(flagged, [])

    def test_pir_flood(self):
        p = Plausibility()
        names = []
        for i in range(20):
            names += [e[0] for e in p.check_pir(i % 2, i)]
        self.assertIn("PIR_FLOOD", names)


if __name__ == "__main__":
    unittest.main()
