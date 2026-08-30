#!/usr/bin/env python3
"""Validate the copyjumpvm MD5 program against hashlib.

Runs `program_md5.prg.txt` through CopyJumpMachine.run_code with a silent
byte-collecting printer, reconstructs the digest bytes, and compares them to
hashlib.md5(MESSAGE).
"""

import hashlib
import os

import md5_gen
from CopyJumpMachine import run_code

HERE = os.path.dirname(os.path.abspath(__file__))


class ByteCollector:
    """Collects output bits and groups them into bytes (LSB-first)."""

    def __init__(self):
        self._bits = []
        self.bytes = []

    def print_bit(self, output_bit):
        assert output_bit in (0, 1)
        self._bits.append(output_bit)
        if len(self._bits) == 8:
            byte = 0
            pos = 1
            for bit in self._bits:
                byte += pos * bit
                pos *= 2
            self.bytes.append(byte)
            self._bits = []


def main():
    program = open(os.path.join(HERE, "program_md5.prg.txt")).read()

    collector = ByteCollector()
    memory = [0] * (1024 * 8)
    run_code(program, collector, memory)

    got = bytes(collector.bytes)
    expected = hashlib.md5(md5_gen.MESSAGE).digest()

    print(f"MESSAGE = {md5_gen.MESSAGE!r}")
    print(f"got      = {got.hex()}")
    print(f"expected = {expected.hex()}")

    if got == expected:
        print("PASS: MD5 matches hashlib")
    else:
        print("FAIL: digest mismatch")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
