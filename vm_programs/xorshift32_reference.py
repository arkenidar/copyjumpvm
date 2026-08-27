#!/usr/bin/env python3
"""Reference xorshift32 PRNG — for validating the copyjumpvm microcode version."""

MASK32 = 0xFFFFFFFF


def xorshift32(state):
    """Advance one xorshift32 step and return the new 32-bit state."""
    state = (state ^ ((state << 13) & MASK32)) & MASK32
    state = (state ^ (state >> 17)) & MASK32
    state = (state ^ ((state << 5) & MASK32)) & MASK32
    return state


def bits_lsb_first(value):
    """32 bits as a string, least-significant bit first (matches VM output order)."""
    return ''.join(str((value >> i) & 1) for i in range(32))


def main():
    import sys
    seed = 0x12345678
    n = 10
    if len(sys.argv) > 1:
        seed = int(sys.argv[1], 0)
    if len(sys.argv) > 2:
        n = int(sys.argv[2])

    state = seed & MASK32
    print(f"seed=0x{state:08X}  n={n}")
    for _ in range(n):
        state = xorshift32(state)
        print(f"0x{state:08X}  {state:10d}  bits: {bits_lsb_first(state)}")


if __name__ == "__main__":
    main()
