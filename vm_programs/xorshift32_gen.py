#!/usr/bin/env python3
"""Generator for textual copyjumpvm xorshift32 programs (stages 4 and 5).

Emits:
  program_xorshift32_step.prg.txt  -- one xorshift32 step from the seed
  program_xorshift32_loop.prg.txt  -- N xorshift32 steps in a loop

Both run under vm_programs/CopyJumpMachine.py (no export needed).
"""

import os

MASK32 = 0xFFFFFFFF

# === EMBEDDED CONSTANTS (change these to re-seed / change count) ===
SEED = 0x12345678   # 32-bit xorshift32 seed
N = 10              # number of outputs (stage 5 only)

# --- textual memory layout (addr 0=const0, 1=const1, user memory starts at 2) ---
X_BASE = 10    # state  x[0..31]  -> addresses 10..41
Y1_BASE = 50   # temp   y1[0..31] -> addresses 50..81
Y2_BASE = 90   # temp   y2[0..31] -> addresses 90..121
CNT_BASE = 130 # counter c[0..7]  -> addresses 130..137

HERE = os.path.dirname(os.path.abspath(__file__))


def xor_bit(out, dst, a, b, tag):
    """Emit code computing dst = a ^ b (a, b are memory addresses)."""
    out.append(f"j {a} a1__{tag}")
    out.append(f"m {dst} {b}")
    out.append(f"j done__{tag}")
    out.append(f"l a1__{tag}")
    out.append(f"j {b} a1b1__{tag}")
    out.append(f"m {dst} 1")
    out.append(f"j done__{tag}")
    out.append(f"l a1b1__{tag}")
    out.append(f"m {dst} 0")
    out.append(f"l done__{tag}")


def emit_seed_init(out):
    out.append(f"# --- init: load 32-bit SEED (0x{SEED:08X}) into state x[0..31], LSB-first ---")
    for i in range(32):
        bit = (SEED >> i) & 1
        out.append(f"m {X_BASE + i} {bit}   # x[{i}] = seed bit {i} = {bit}")


def emit_xorshift_step(out):
    """xorshift32: x ^= x<<13; x ^= x>>17; x ^= x<<5 (shifted-out bits are 0)."""
    out.append("# --- xorshift32 step ---")

    # y1[i] = x[i] ^ x[i-13]  (x[i-13]=0 when i<13)
    out.append("# y1 = x ^ (x << 13)")
    for i in range(32):
        dst = Y1_BASE + i
        a = X_BASE + i
        if i >= 13:
            xor_bit(out, dst, a, X_BASE + (i - 13), f"y1_{i}")
        else:
            out.append(f"m {dst} {a}   # y1[{i}] = x[{i}] (shifted-out -> 0)")

    # y2[i] = y1[i] ^ y1[i+17]  (y1[i+17]=0 when i>14)
    out.append("# y2 = y1 ^ (y1 >> 17)")
    for i in range(32):
        dst = Y2_BASE + i
        a = Y1_BASE + i
        if i <= 14:
            xor_bit(out, dst, a, Y1_BASE + (i + 17), f"y2_{i}")
        else:
            out.append(f"m {dst} {a}   # y2[{i}] = y1[{i}] (shifted-out -> 0)")

    # x[i] = y2[i] ^ y2[i-5]  (y2[i-5]=0 when i<5)
    out.append("# x = y2 ^ (y2 << 5)   (written back into x)")
    for i in range(32):
        dst = X_BASE + i
        a = Y2_BASE + i
        if i >= 5:
            xor_bit(out, dst, a, Y2_BASE + (i - 5), f"y3_{i}")
        else:
            out.append(f"m {dst} {a}   # x[{i}] = y2[{i}] (shifted-out -> 0)")


def emit_output(out):
    out.append("# --- output the 32-bit state, LSB first ---")
    for i in range(32):
        out.append(f"m out {X_BASE + i}   # out bit {i}")


def emit_countdown_init(out):
    out.append(f"# === EMBEDDED CONSTANT: N = {N} ===")
    out.append(f"# counter is 8 bits at addresses {CNT_BASE}..{CNT_BASE + 7}, LSB-first")
    for i in range(8):
        bit = (N >> i) & 1
        out.append(f"m {CNT_BASE + i} {bit}   # counter bit {i} = {bit}")


def emit_countdown_body(out):
    """Decrement 8-bit counter, then loop back if nonzero else terminate."""
    out.append("# --- decrement counter by 1 (ripple borrow) ---")
    for i in range(8):
        addr = CNT_BASE + i
        out.append(f"j {addr} d{i}_is_1")
        out.append(f"m {addr} 1")
        if i < 7:
            out.append(f"j d{i + 1}")
        else:
            out.append("j decrement_done")
        out.append(f"l d{i}_is_1")
        out.append(f"m {addr} 0")
        out.append("j decrement_done")
        if i < 7:
            out.append(f"l d{i + 1}")
    out.append("l decrement_done")
    out.append("# --- if counter is zero, terminate; else loop again ---")
    for i in range(8):
        out.append(f"j {CNT_BASE + i} nonzero")
    out.append("j end")
    out.append("l nonzero")
    out.append("j main_loop")


def write_program(filename, header, body):
    path = os.path.join(HERE, filename)
    with open(path, "w") as f:
        for ln in header + body:
            f.write(ln + "\n")
    print(f"wrote {filename} ({len(header) + len(body)} lines)")


def generate_step():
    header = [
        "# xorshift32 - one step (generate ONE number from the seed)",
        "# runs under vm_programs/CopyJumpMachine.py",
        f"# SEED = 0x{SEED:08X}",
        "",
    ]
    body = []
    emit_seed_init(body)
    emit_xorshift_step(body)
    emit_output(body)
    write_program("program_xorshift32_step.prg.txt", header, body)


def generate_loop():
    header = [
        "# xorshift32 - N numbers in a loop",
        "# runs under vm_programs/CopyJumpMachine.py",
        f"# SEED = 0x{SEED:08X}",
        f"# N = {N}",
        "",
    ]
    body = []
    emit_seed_init(body)
    emit_countdown_init(body)
    body.append("")
    body.append("l main_loop")
    body.append("")
    emit_xorshift_step(body)
    emit_output(body)
    body.append("")
    emit_countdown_body(body)
    write_program("program_xorshift32_loop.prg.txt", header, body)


if __name__ == "__main__":
    generate_step()
    generate_loop()
