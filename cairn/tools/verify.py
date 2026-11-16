#!/usr/bin/env python3
"""CAIRN offline verifier.

Usage:
    python3 tools/verify.py --log serial_dump.txt --key-hex <K0_HEX> [--anchor SEQ:HASH]

* The log may be a raw copy of the Wokwi serial terminal: only lines containing
  a JSON record (optionally prefixed with ``LOG ``) are used.
* Without --key-hex only the hash chain is checked (weaker).
Exit code: 0 = log verified, 1 = tampering detected, 2 = usage error.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "firmware"))
from chainlog import verify_records  # noqa: E402


def extract(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("LOG "):
            line = line[4:]
        if line.startswith("{") and line.endswith("}"):
            out.append(line)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--log", required=True)
    ap.add_argument("--key-hex", help="initial key K0 (hex); enables MAC verification")
    ap.add_argument("--anchor", help="SEQ:HASH recorded off-device; enables truncation detection")
    a = ap.parse_args(argv)
    try:
        with open(a.log) as f:
            lines = extract(f.read())
        k0 = bytes.fromhex(a.key_hex) if a.key_hex else None
        anchor = None
        if a.anchor:
            s, h = a.anchor.split(":")
            anchor = (int(s), h)
    except (OSError, ValueError) as exc:
        print("error:", exc)
        return 2
    res = verify_records(lines, k0, anchor)
    mode = "chain+MAC" if k0 else "chain-only"
    if res["ok"]:
        print("VERIFIED (%s): %d records intact" % (mode, res["checked"]))
        return 0
    print("TAMPERING DETECTED (%s): first inconsistency at record #%s - %s"
          % (mode, res["bad_seq"], res["reason"]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
