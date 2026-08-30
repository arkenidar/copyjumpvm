#!/usr/bin/env python3
"""Generator for a textual copyjumpvm MD5 program.

Computes MD5 of a single-block message (< 56 bytes) and emits
`program_md5.prg.txt`, which runs under vm_programs/CopyJumpMachine.py.

Every MD5 operation is lowered to copy-jump primitives at the bit level:
  - NOT / AND / OR / XOR       -> small jump+copy branch patterns
  - 32-bit addition mod 2^32   -> ripple-carry chain of full adders
  - left-rotate                -> index remapping at generation time
  - K[i], s[i], g, round kind  -> embedded constants (no runtime tables)

Bits are stored LSB-first (bit i = (word >> i) & 1), matching the rest of
this repository, and the 16 output bytes are emitted LSB-first per byte.
"""

import hashlib
import math
import os
import struct

MASK32 = 0xFFFFFFFF

# === EMBEDDED MESSAGE (change to hash a different short string) ===
MESSAGE = b""  # MD5("") = d41d8cd98f00b204e9800998ecf8427e
# MESSAGE = b"abc"  # MD5("abc") = 900150983cd24fb0d6963f7d28e17f72

HERE = os.path.dirname(os.path.abspath(__file__))

# --- memory layout (addr 0=const0, 1=const1, user bits start at 2) ---
A = 10            # state word A  -> 10..41
B = 42            # state word B  -> 42..73
C = 74            # state word C  -> 74..105
D = 106           # state word D  -> 106..137
M = 200           # message M[0..15] -> 200..711 (512 bits)
F = 800           # round function result + running sum accumulator
R = 832           # left-rotated accumulator
KSCRATCH = 864    # 32-bit K constant scratch word
BNEW = 896        # next B value (B + rot(F))
INIT_A = 928      # initial-state constants (never mutated), added back at the end
INIT_B = 960
INIT_C = 992
INIT_D = 1024
T0, T1, T2 = 8000, 8001, 8002  # scratch bits
CARRY = 8003      # ripple-carry bit

# --- MD5 constants ---
K = [int(abs(math.sin(i + 1)) * 2 ** 32) & MASK32 for i in range(64)]
S = ([7, 12, 17, 22] * 4 + [5, 9, 14, 20] * 4 +
     [4, 11, 16, 23] * 4 + [6, 10, 15, 21] * 4)

A0 = 0x67452301
B0 = 0xefcdab89
C0 = 0x98badcfe
D0 = 0x10325476


class Emitter:
    """Accumulates textual copyjump instructions with unique labels."""

    def __init__(self):
        self.lines = []
        self.tag = 0

    def _t(self):
        self.tag += 1
        return self.tag

    def emit(self, s):
        self.lines.append(s)

    def comment(self, s):
        self.lines.append("# " + s)

    def blank(self):
        self.lines.append("")

    # --- single-bit logic gates (each ~7 instructions) ---
    def bit_not(self, dst, a):
        t = self._t()
        self.emit(f"j {a} a1__{t}")
        self.emit(f"m {dst} 1")
        self.emit(f"j done__{t}")
        self.emit(f"l a1__{t}")
        self.emit(f"m {dst} 0")
        self.emit(f"l done__{t}")

    def bit_and(self, dst, a, b):
        t = self._t()
        self.emit(f"j {a} a1__{t}")
        self.emit(f"m {dst} 0")
        self.emit(f"j done__{t}")
        self.emit(f"l a1__{t}")
        self.emit(f"m {dst} {b}")
        self.emit(f"l done__{t}")

    def bit_or(self, dst, a, b):
        t = self._t()
        self.emit(f"j {a} a1__{t}")
        self.emit(f"m {dst} {b}")
        self.emit(f"j done__{t}")
        self.emit(f"l a1__{t}")
        self.emit(f"m {dst} 1")
        self.emit(f"l done__{t}")

    def bit_xor(self, dst, a, b):
        t = self._t()
        self.emit(f"j {a} a1__{t}")
        self.emit(f"m {dst} {b}")
        self.emit(f"j done__{t}")
        self.emit(f"l a1__{t}")
        self.emit(f"j {b} a1b1__{t}")
        self.emit(f"m {dst} 1")
        self.emit(f"j done__{t}")
        self.emit(f"l a1b1__{t}")
        self.emit(f"m {dst} 0")
        self.emit(f"l done__{t}")

    # --- 32-bit word helpers ---
    def copy_word(self, dst, src):
        for i in range(32):
            self.emit(f"m {dst + i} {src + i}")

    def load_const(self, dst, value):
        value &= MASK32
        for i in range(32):
            self.emit(f"m {dst + i} {(value >> i) & 1}")

    def rotate_left_copy(self, dst, src, s):
        for j in range(32):
            self.emit(f"m {dst + j} {src + ((j - s) % 32)}")

    def full_adder(self, sum_dst, a, b, cin, carry_dst):
        # sum = a ^ b ^ cin ; carry = (a & b) | ((a ^ b) & cin)
        # Reads of a/b/cin all happen before sum_dst/carry_dst are written,
        # so in-place accumulation (dst == a) is safe.
        self.bit_xor(T0, a, b)
        self.bit_and(T2, a, b)
        self.bit_xor(sum_dst, T0, cin)
        self.bit_and(T1, T0, cin)
        self.bit_or(carry_dst, T1, T2)

    def add32(self, dst, a, b):
        self.emit(f"m {CARRY} 0")
        for i in range(32):
            self.full_adder(dst + i, a + i, b + i, CARRY, CARRY)

    # --- MD5 round function F/G/H/I, one bit -> F[bit] ---
    def round_func_bit(self, bit, kind):
        b, c, d = B + bit, C + bit, D + bit
        if kind == "F":  # (B & C) | (~B & D)
            self.bit_and(T0, b, c)
            self.bit_not(T1, b)
            self.bit_and(T2, T1, d)
            self.bit_or(F + bit, T0, T2)
        elif kind == "G":  # (D & B) | (~D & C)
            self.bit_and(T0, d, b)
            self.bit_not(T1, d)
            self.bit_and(T2, T1, c)
            self.bit_or(F + bit, T0, T2)
        elif kind == "H":  # B ^ C ^ D
            self.bit_xor(T0, b, c)
            self.bit_xor(F + bit, T0, d)
        elif kind == "I":  # C ^ (B | ~D)
            self.bit_not(T1, d)
            self.bit_or(T0, b, T1)
            self.bit_xor(F + bit, c, T0)


def padded_block(message):
    """MD5 padding for a single-block message (< 56 bytes)."""
    block = bytearray(message)
    block.append(0x80)
    while len(block) % 64 != 56:
        block.append(0)
    block += struct.pack("<Q", len(message) * 8)
    assert len(block) == 64, "message too long: generator supports < 56 bytes"
    return block


def generate():
    e = Emitter()

    expected = hashlib.md5(MESSAGE).hexdigest()
    e.comment("MD5 (single 512-bit block) for copyjumpvm")
    e.comment(f"MESSAGE = {MESSAGE!r}")
    e.comment(f"expected digest = {expected}")
    e.comment("runs under vm_programs/CopyJumpMachine.py")
    e.blank()

    block = padded_block(MESSAGE)
    m_words = [int.from_bytes(block[4 * g:4 * g + 4], "little") for g in range(16)]

    e.comment("--- message block M[0..15], little-endian, LSB-first ---")
    for g in range(16):
        e.load_const(M + g * 32, m_words[g])

    e.comment("--- initial state A,B,C,D (working registers) ---")
    e.load_const(A, A0)
    e.load_const(B, B0)
    e.load_const(C, C0)
    e.load_const(D, D0)

    e.comment("--- initial-state constants (kept for the final add-back) ---")
    e.load_const(INIT_A, A0)
    e.load_const(INIT_B, B0)
    e.load_const(INIT_C, C0)
    e.load_const(INIT_D, D0)

    for i in range(64):
        if i < 16:
            kind, g = "F", i
        elif i < 32:
            kind, g = "G", (5 * i + 1) % 16
        elif i < 48:
            kind, g = "H", (3 * i + 5) % 16
        else:
            kind, g = "I", (7 * i) % 16
        s = S[i]

        e.comment(f"--- round {i} ({kind}, g={g}, s={s}, K=0x{K[i]:08X}) ---")

        for bit in range(32):
            e.round_func_bit(bit, kind)

        # F = F + A + K[i] + M[g]  (mod 2^32)
        e.add32(F, F, A)
        e.load_const(KSCRATCH, K[i])
        e.add32(F, F, KSCRATCH)
        e.add32(F, F, M + g * 32)

        # B = B + leftrotate(F, s)
        e.rotate_left_copy(R, F, s)
        e.add32(BNEW, B, R)

        # A, D, C, B rotation
        e.copy_word(A, D)
        e.copy_word(D, C)
        e.copy_word(C, B)
        e.copy_word(B, BNEW)

    e.comment("--- add back initial state: A += a0, B += b0, C += c0, D += d0 ---")
    e.add32(A, A, INIT_A)
    e.add32(B, B, INIT_B)
    e.add32(C, C, INIT_C)
    e.add32(D, D, INIT_D)

    e.comment("--- output 16-byte digest (a, b, c, d little-endian) ---")
    for base in (A, B, C, D):
        for byte in range(4):
            for bit in range(8):
                e.emit(f"m out {base + byte * 8 + bit}")

    path = os.path.join(HERE, "program_md5.prg.txt")
    with open(path, "w") as f:
        for ln in e.lines:
            f.write(ln + "\n")
    print(f"wrote program_md5.prg.txt ({len(e.lines)} lines)")


if __name__ == "__main__":
    generate()

