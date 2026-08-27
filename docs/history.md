# History

## 2026-08-27 — xorshift32: 5-stage build (XOR gate → PRNG)

All five stages are complete and verified.

### What was built (all textual, run via `CopyJumpMachine.py` — no export)

| Stage | File | Result |
|---|---|---|
| 1. XOR gate | `vm_programs/program_xor_gate.prg.txt` | ✅ 4/4 truth-table cases pass |
| 2. Reference xorshift32 | `vm_programs/xorshift32_reference.py` | ✅ outputs match expected |
| 3. Countdown loop-count | `vm_programs/program_countdown.prg.txt` | ✅ counts `10 → 1`, terminates |
| 4. One number from seed | `vm_programs/program_xorshift32_step.prg.txt` | ✅ `0x87985AA5` |
| 5. N numbers in loop | `vm_programs/program_xorshift32_loop.prg.txt` | ✅ all 10 match reference |

Plus the generator: **`vm_programs/xorshift32_gen.py`** (emits stages 4 & 5).

### Verification highlights

- **Stage 1**: `00→byte:0`, `01→byte:1`, `10→byte:1`, `11→byte:0`.
- **Stage 3**: `byte: 10, 9, 8, …, 1`.
- **Stage 4**: 32 bits reconstruct to `0x87985AA5` (matches reference step 1).
- **Stage 5**: automated diff against `xorshift32_reference.py` → **all 10 values OK** (`0x87985AA5` … `0x3AB14B11`).

### How to use / play with it

```bash
# XOR gate (type/pass two bits)
printf '1\n0\n' | python3 vm_programs/CopyJumpMachine.py vm_programs/program_xor_gate.prg.txt

# Reference PRNG (play with seed/n)
python3 vm_programs/xorshift32_reference.py 0x12345678 10
python3 vm_programs/xorshift32_reference.py 1 5

# Countdown
python3 vm_programs/CopyJumpMachine.py vm_programs/program_countdown.prg.txt

# One number / N numbers
python3 vm_programs/CopyJumpMachine.py vm_programs/program_xorshift32_step.prg.txt
python3 vm_programs/CopyJumpMachine.py vm_programs/program_xorshift32_loop.prg.txt
```

### Changing the embedded constants (as requested, documented in comments)

- **Generator** (`xorshift32_gen.py`): edit `SEED` and `N` at the top, then re-run `python3 vm_programs/xorshift32_gen.py` to regenerate stages 4 & 5. The emitted `.prg.txt` headers echo the chosen values (e.g. `# SEED = 0x12345678`, `# N = 10`).
- **Countdown** (`program_countdown.prg.txt`): `# === EMBEDDED CONSTANT: N = 10 ===` with a commented bit-map for editing.
- **Seed init** in the generated programs is annotated per bit (`# x[0] = seed bit 0 = 0`).

### Design notes

- The **shifts are free**: the generator realizes `<<13`, `>>17`, `<<5` as index arithmetic over the bit arrays (out-of-range source = constant 0), so no actual shift instructions.
- Each bit-XOR compiles to a compact 7-instruction branch pattern (`a=0 → dst=b`; `a=1,b=0 → 1`; `a=1,b=1 → 0`), reused 61× per xorshift step (the other 35 bits are plain copies where the shift moved a bit out).
- The **countdown** from stage 3 is reused verbatim in stage 5 (ripple-borrow decrement + zero-check), wired to loop the xorshift step + output.

Everything is non-interactive (no `in` reads) so it's deterministic and directly diffable against the Python reference.

### Files created

- `vm_programs/program_xor_gate.prg.txt`
- `vm_programs/xorshift32_reference.py`
- `vm_programs/program_countdown.prg.txt`
- `vm_programs/program_xorshift32_step.prg.txt`
- `vm_programs/program_xorshift32_loop.prg.txt`
- `vm_programs/xorshift32_gen.py`

### Possible next steps

- Larger bit-width countdown (16/32-bit N).
- A different xorshift variant.
- Emit the `.cj` numeric export (via `exporter.py`) later.
