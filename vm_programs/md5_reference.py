#!/usr/bin/env python3
"""Reference MD5 digests for validating the copyjumpvm microcode version."""

import hashlib

# Keep in sync with MESSAGE in md5_gen.py.
VECTORS = [
    b"",
    b"abc",
]


def main():
    for m in VECTORS:
        print(f"{m!r:20} -> {hashlib.md5(m).hexdigest()}")


if __name__ == "__main__":
    main()
