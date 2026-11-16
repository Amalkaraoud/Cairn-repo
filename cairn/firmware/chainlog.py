"""CAIRN tamper-evident log: hash chain + HMAC with a forward-secure key ratchet.

Record i (one JSON line)::

    {"s": seq, "t": ts, "e": event, "v": value, "p": prev_hash, "h": hash, "m": mac}

    h_i = SHA256( seq | ts | event | value | h_{i-1} )      # integrity / ordering
    m_i = HMAC( K_i, h_i )                                  # authenticity
    K_{i+1} = SHA256( K_i )                                 # key ratchet (old keys erased)

* The hash chain alone detects naive edits, deletions, insertions, reordering.
* The MAC detects an attacker who recomputes the hashes but does not hold the key.
* The ratchet means that stealing the device later does not allow forging
  *earlier* records (forward integrity, in the spirit of Schneier & Kelsey, 1999).
* Truncating the tail of the log is only detectable against an external *anchor*
  (seq, head hash) kept off the device, or against the in-RAM head.
"""
try:
    import ujson as json
except ImportError:
    import json

from mpcrypto import sha256, hmac_sha256, to_hex, from_hex, ct_equal

GENESIS = "0" * 64


def canonical(seq, ts, event, value, prev):
    return "%d|%d|%s|%s|%s" % (seq, ts, event, value, prev)


def _hash_record(seq, ts, event, value, prev):
    return to_hex(sha256(canonical(seq, ts, event, value, prev).encode()))


def _fail(seq, reason, checked):
    return {"ok": False, "checked": checked, "bad_seq": seq, "reason": reason}


def verify_records(lines, k0=None, anchor=None):
    """Verify an iterable of JSON lines.

    k0     -- initial key (bytes). ``None`` = chain-only verification (no MAC check).
    anchor -- optional ``(seq, head_hash)`` pair saved outside the device.
    Returns a dict: ok, checked, bad_seq, reason.
    """
    prev = GENESIS
    key = k0
    expected = 1
    checked = 0
    hashes = [] if anchor else None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            seq, ts, ev, val = rec["s"], rec["t"], rec["e"], rec["v"]
            rprev, rh, rm = rec["p"], rec["h"], rec["m"]
        except (ValueError, KeyError, TypeError):
            return _fail(expected, "BAD_RECORD", checked)
        if seq != expected:
            return _fail(expected, "SEQ_GAP", checked)
        if rprev != prev:
            return _fail(seq, "PREV_MISMATCH", checked)
        if _hash_record(seq, ts, ev, val, rprev) != rh:
            return _fail(seq, "HASH_MISMATCH", checked)
        if key is not None:
            mac = to_hex(hmac_sha256(key, rh.encode()))
            if not ct_equal(mac, rm):
                return _fail(seq, "MAC_MISMATCH", checked)
            key = sha256(key)
        prev = rh
        expected += 1
        checked += 1
        if hashes is not None:
            hashes.append(rh)
    if anchor:
        a_seq, a_hash = anchor
        if checked < a_seq:
            return _fail(checked + 1, "TRUNCATED", checked)
        if hashes[a_seq - 1] != a_hash:
            return _fail(a_seq, "ANCHOR_MISMATCH", checked)
    return {"ok": True, "checked": checked, "bad_seq": None, "reason": "OK"}


def verify_file(path, k0=None, anchor=None):
    """Stream-verify a log file (low RAM; usable on the device)."""
    try:
        with open(path) as f:
            return verify_records(f, k0, anchor)
    except OSError:
        return _fail(1, "NO_LOG", 0)


class ChainLog:
    """Append-only, tamper-evident log stored in a text file."""

    def __init__(self, path, state_path, k0=None):
        self.path = path
        self.state_path = state_path
        self.seq = 0
        self.head = GENESIS
        self.key = None
        self._load_or_init(k0)

    def _load_or_init(self, k0):
        try:
            with open(self.state_path) as f:
                st = json.loads(f.read())
            self.seq = st["seq"]
            self.head = st["head"]
            self.key = from_hex(st["key"])
        except (OSError, ValueError, KeyError):
            if k0 is None:
                raise ValueError("no state and no initial key")
            self.seq, self.head, self.key = 0, GENESIS, k0
            open(self.path, "w").close()
            self._save_state()

    def _save_state(self):
        with open(self.state_path, "w") as f:
            f.write(json.dumps({"seq": self.seq, "head": self.head,
                                "key": to_hex(self.key)}))

    def append(self, ts, event, value=""):
        """Append one record; returns it. ``value`` is stored as a string."""
        value = str(value)
        seq = self.seq + 1
        h = _hash_record(seq, ts, event, value, self.head)
        m = to_hex(hmac_sha256(self.key, h.encode()))
        rec = {"s": seq, "t": ts, "e": event, "v": value,
               "p": self.head, "h": h, "m": m}
        with open(self.path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        self.seq, self.head = seq, h
        self.key = sha256(self.key)          # ratchet: previous key is gone
        self._save_state()
        return rec

    def audit(self):
        """Chain-only self-check + comparison with the in-RAM head.

        NOTE: this cannot detect an attacker who recomputes the hashes; that
        needs the offline verifier holding K0 (tools/verify.py).
        """
        res = verify_file(self.path)
        if res["ok"] and (res["checked"] != self.seq):
            return _fail(res["checked"] + 1, "TRUNCATED", res["checked"])
        return res
