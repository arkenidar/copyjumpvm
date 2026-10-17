#!/usr/bin/env python3
"""Verify that an outlined (rewritten) copyjump program is semantically
equivalent to its inlined original: run both under CopyJumpMachine and compare
the full output bit stream. Optional 3rd arg = input bits ('0'/'1') for
programs that read from 'in'."""
import builtins
import sys

from CopyJumpMachine import run_code


class BitCollector:
    def __init__(self):
        self.bits = []

    def print_bit(self, bit):
        self.bits.append(bit)


def run(path, inputs):
    it = iter(inputs)
    orig_input = builtins.input
    builtins.input = lambda prompt='': next(it, '0')
    try:
        collector = BitCollector()
        run_code(open(path).read(), collector, [0] * (1024 * 8))
        return collector.bits
    finally:
        builtins.input = orig_input


def main():
    if len(sys.argv) not in (3, 4):
        print("usage: python3 verify_outliner.py <original.prg.txt> <rewritten.prg.txt> [input_bits]")
        sys.exit(2)
    original, rewritten = sys.argv[1], sys.argv[2]
    inputs = sys.argv[3] if len(sys.argv) == 4 else ''
    a = run(original, inputs)
    b = run(rewritten, inputs)
    print(f"{original}: {len(a)} bits")
    print(f"{rewritten}: {len(b)} bits")
    if a == b:
        print("PASS: identical output")
        sys.exit(0)
    print("FAIL: outputs differ")
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            print(f"  first difference at bit {i}: {x} vs {y}")
            break
    if len(a) != len(b):
        print(f"  length differs: {len(a)} vs {len(b)}")
    sys.exit(1)


if __name__ == "__main__":
    main()

