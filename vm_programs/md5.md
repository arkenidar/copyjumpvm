# MD5 in copyjump (single-block)

MD5 computed entirely from copy+jump primitives, executed by the "pythonic
runner" `CopyJumpMachine.py`.

For the general machine model (RESM / BBJJ) behind this, see
`../docs/resm_bbjj.md`.

## Files

| File | Role |
|---|---|
| `md5_gen.py` | generator: emits `program_md5.prg.txt` |
| `program_md5.prg.txt` | generated MD5 program (~376k lines) |
| `md5_reference.py` | expected digests via `hashlib` |
| `md5_check.py` | runs the program in the VM and diffs vs `hashlib` |

## Run

(run from the `vm_programs/` directory)

```shell
python3 md5_reference.py    # expected digests
python3 md5_gen.py          # (re)generate program_md5.prg.txt
python3 md5_check.py        # run in VM + diff vs hashlib
python3 CopyJumpMachine.py program_md5.prg.txt   # emits 16 digest bytes
```

Change the embedded message by editing `MESSAGE` at the top of `md5_gen.py`,
then re-running the generator.

## Memory layout

`addr 0` = constant 0, `addr 1` = constant 1 (defined by the runner); user
bits start at `2`. Each MD5 word is 32 consecutive bit-addresses, LSB-first
(`bit i = (word >> i) & 1`).

| Symbol | Base | Notes |
|---|---|---|
| A, B, C, D | 10, 42, 74, 106 | working state registers |
| M | 200 | message `M[0..15]` (512 bits) |
| F | 800 | round-function result + running sum |
| R | 832 | left-rotated accumulator |
| KSCRATCH | 864 | 32-bit K constant |
| BNEW | 896 | next `B` value |
| INIT_A..INIT_D | 928, 960, 992, 1024 | initial constants (added back at the end) |
| T0, T1, T2 | 8000..8002 | scratch bits |
| CARRY | 8003 | ripple-carry bit |

## Bit-level primitives

Only `m <dst> <src>` (copy one bit) and `j <cond> <label>` / `j <label>`
(jump) exist, so everything else is synthesized:

- **NOT / AND / OR / XOR** — ~7-instruction branch patterns:
  `j a a1 … m dst …` selects the output for each input case.
- **full adder** (1 bit): `sum = a⊕b⊕cin`, `carry = (a&b) | ((a⊕b)&cin)`.
- **add32** (mod 2^32): 32 full adders chained through a single carry bit
  (`m CARRY 0` then ripple). Operand reads happen before the sum/carry writes,
  so in-place accumulation (`dst == a`) is safe.
- **left-rotate**: free — the generator remaps indices
  (`R[j] = F[(j - s) mod 32]`).

## Round structure (unrolled ×64)

```
F = f(B, C, D)          # F/G/H/I chosen by round number
F = F + A + K[i] + M[g] # mod 2^32
B = B + leftrotate(F, s[i])
A = D; D = C; C = B     # register rotation
```

then, after all 64 rounds, add the initial constants back:

```
A += a0; B += b0; C += c0; D += d0
```

`K[i] = int(abs(sin(i+1)) * 2^32) & 0xFFFFFFFF`, and `s[i]`, `g`, and the
function kind are hard-coded per round (no runtime tables).

## Padding

Standard MD5 padding (`0x80`, zero fill, 64-bit little-endian bit length).
**Single 512-bit block only**, so `len(message) < 56` bytes.

## Verification

`md5_check.py` passes against `hashlib` for the RFC 1321 vectors:

| message | digest |
|---|---|
| `""` | `d41d8cd98f00b204e9800998ecf8427e` |
| `"a"` | `0cc175b9c0f1b6a831c399e269772661` |
| `"abc"` | `900150983cd24fb0d6963f7d28e17f72` |
| `"message digest"` | `f96b697d7cb7938d525a2f31aaf161d0` |
| `"hello"` | `5d41402abc4b2a76b9719d911017c592` |
| `"The quick brown fox jumps over the lazy dog"` | `9e107d9d372bb6826bd81d3542a419d6` |
