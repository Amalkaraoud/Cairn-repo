"""Minimal crypto helpers for CAIRN (MicroPython and CPython compatible).

MicroPython ships hashlib.sha256 on ESP32 but no ``hmac`` module, so HMAC-SHA256
(RFC 2104) is implemented here in a few lines on top of SHA-256.
"""
try:
    import hashlib
except ImportError:  # very old ports
    import uhashlib as hashlib
try:
    from ubinascii import hexlify, unhexlify
except ImportError:
    from binascii import hexlify, unhexlify

_BLOCK = 64


def sha256(data):
    """Return the raw SHA-256 digest of ``data`` (bytes)."""
    h = hashlib.sha256()
    h.update(data)
    return h.digest()


def hmac_sha256(key, msg):
    """HMAC-SHA256 (RFC 2104). ``key`` and ``msg`` are bytes."""
    if len(key) > _BLOCK:
        key = sha256(key)
    key = key + b"\x00" * (_BLOCK - len(key))
    ipad = bytes([b ^ 0x36 for b in key])
    opad = bytes([b ^ 0x5C for b in key])
    return sha256(opad + sha256(ipad + msg))


def to_hex(raw):
    return hexlify(raw).decode()


def from_hex(text):
    return unhexlify(text)


def ct_equal(a, b):
    """Constant-time string comparison (avoids early-exit timing leaks)."""
    if len(a) != len(b):
        return False
    diff = 0
    for x, y in zip(a, b):
        diff |= ord(x) ^ ord(y)
    return diff == 0
