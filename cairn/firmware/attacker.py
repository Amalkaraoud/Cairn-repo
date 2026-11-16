"""RED-TEAM SIMULATION - demo only. Plays an attacker with file-system access.

Each function rewrites ``cairn.log`` the way a burglar covering their tracks
might. None of them has the HMAC key. They exist only to show, live in the
simulator, what the audit does and does not catch.
"""
from chainlog import canonical, to_hex, sha256, GENESIS

try:
    import ujson as json
except ImportError:
    import json

KINDS = ("EDIT", "DELETE", "TRUNCATE", "REHASH")


def _read(path):
    with open(path) as f:
        return [ln for ln in f.read().split("\n") if ln.strip()]


def _write(path, lines):
    with open(path, "w") as f:
        for ln in lines:
            f.write(ln + "\n")


def _hide(rec):
    """Make the record look harmless (always changes the record)."""
    if rec["e"] != "HB":
        rec["e"] = "HB"
    else:
        rec["v"] = "T=20.0;G=0"


def run(kind, path):
    """Apply one attack; returns a short human-readable description."""
    lines = _read(path)
    if len(lines) < 6:
        return "log too short"
    mid = len(lines) // 2
    if kind == "EDIT":                      # hide an event, hashes untouched
        rec = json.loads(lines[mid])
        _hide(rec)
        lines[mid] = json.dumps(rec)
        _write(path, lines)
        return "edited rec #%d" % rec["s"]
    if kind == "DELETE":                    # remove a record
        rec = json.loads(lines[mid])
        del lines[mid]
        _write(path, lines)
        return "deleted rec #%d" % rec["s"]
    if kind == "TRUNCATE":                  # drop the last 3 records
        _write(path, lines[:-3])
        return "cut last 3 recs"
    if kind == "REHASH":                    # edit + recompute hash chain (no key!)
        recs = [json.loads(ln) for ln in lines]
        _hide(recs[mid])
        prev = recs[mid]["p"]
        for r in recs[mid:]:
            r["p"] = prev
            r["h"] = to_hex(sha256(canonical(r["s"], r["t"], r["e"], r["v"], prev).encode()))
            prev = r["h"]                   # old MACs are kept: attacker lacks the key
        _write(path, [json.dumps(r) for r in recs])
        return "edit+rehash #%d.." % recs[mid]["s"]
    return "unknown"
