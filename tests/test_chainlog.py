import hashlib
import hmac as std_hmac
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "firmware"))
from mpcrypto import hmac_sha256, sha256  # noqa: E402
from chainlog import ChainLog, verify_records, verify_file  # noqa: E402

K0 = b"K" * 32


def make_log(n=20):
    d = tempfile.mkdtemp()
    log = ChainLog(os.path.join(d, "l"), os.path.join(d, "s"), K0)
    for i in range(n):
        log.append(1000 + i, "HB" if i % 3 else "MOTION", i)
    with open(log.path) as f:
        return log, f.read().splitlines()


class TestCrypto(unittest.TestCase):
    def test_hmac_matches_stdlib(self):
        for klen in (1, 20, 32, 64, 100):
            key = bytes(range(klen))
            msg = b"hello world" * 7
            self.assertEqual(hmac_sha256(key, msg), std_hmac.new(key, msg, hashlib.sha256).digest())

    def test_rfc4231_case2(self):
        out = hmac_sha256(b"Jefe", b"what do ya want for nothing?").hex()
        self.assertEqual(out, "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843")


class TestChain(unittest.TestCase):
    def test_clean_log_verifies(self):
        _, lines = make_log()
        self.assertTrue(verify_records(lines)["ok"])
        self.assertTrue(verify_records(lines, K0)["ok"])

    def test_edit_detected_and_localised(self):
        _, lines = make_log()
        r = json.loads(lines[9]); r["v"] = "999"; lines[9] = json.dumps(r)
        res = verify_records(lines)
        self.assertFalse(res["ok"]); self.assertEqual(res["bad_seq"], 10)

    def test_delete_detected(self):
        _, lines = make_log()
        del lines[5]
        res = verify_records(lines)
        self.assertFalse(res["ok"]); self.assertEqual(res["bad_seq"], 6)

    def test_reorder_detected(self):
        _, lines = make_log()
        lines[4], lines[5] = lines[5], lines[4]
        self.assertFalse(verify_records(lines)["ok"])

    def test_rehash_needs_key(self):
        _, lines = make_log()
        from chainlog import canonical, to_hex
        recs = [json.loads(x) for x in lines]
        assert recs[6]["e"] == "MOTION"
        recs[6]["e"] = "HB"
        prev = recs[6]["p"]
        for r in recs[6:]:
            r["p"] = prev
            r["h"] = to_hex(sha256(canonical(r["s"], r["t"], r["e"], r["v"], prev).encode()))
            prev = r["h"]
        forged = [json.dumps(r) for r in recs]
        self.assertTrue(verify_records(forged)["ok"])            # chain-only is fooled
        res = verify_records(forged, K0)                          # MAC is not
        self.assertFalse(res["ok"]); self.assertEqual(res["reason"], "MAC_MISMATCH")

    def test_truncation_needs_anchor(self):
        log, lines = make_log()
        anchor = (log.seq, log.head)
        cut = lines[:-3]
        self.assertTrue(verify_records(cut, K0)["ok"])            # undetectable alone
        res = verify_records(cut, K0, anchor)
        self.assertFalse(res["ok"]); self.assertEqual(res["reason"], "TRUNCATED")

    def test_audit_detects_truncation_via_ram_head(self):
        log, lines = make_log()
        with open(log.path, "w") as f:
            f.write("\n".join(lines[:-2]) + "\n")
        self.assertFalse(log.audit()["ok"])

    def test_state_persists_across_reboot(self):
        log, _ = make_log(5)
        log2 = ChainLog(log.path, log.state_path, None)
        log2.append(2000, "HB", 1)
        self.assertTrue(verify_file(log.path, K0)["ok"])

    def test_key_compromise_limit(self):
        """Documented limit: an attacker holding the *current* key can forge future records."""
        log, lines = make_log(5)
        log.append(3000, "FORGED", "x")      # uses the legitimately ratcheted key
        self.assertTrue(verify_file(log.path, K0)["ok"])


if __name__ == "__main__":
    unittest.main()
