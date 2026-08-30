# The RESM / BBJJ machine model

**copyjumpvm** is an implementation of a tiny, Turing-complete machine known
as **RESM** — the *Raw Execution-Step Machine* — also called **BBJJ**,
*Bit Bit Jump Jump*.

> *"copy a bit, then conditionally jump. That's the entire instruction set."*

## The single instruction

Every instruction has the same four operands and executes in three phases:

| Operand | Meaning |
|---|---|
| `COPY_FROM` | memory address of the source bit |
| `COPY_TO`   | memory address where the bit is written |
| `IP_CASE_0` | next instruction address if the path-selector bit is `0` |
| `IP_CASE_1` | next instruction address if the path-selector bit is `1` |

| Phase | Action |
|---|---|
| 1. Fetch | read the bit at `COPY_FROM` |
| 2. Copy ("Bit Bit") | write that bit to `COPY_TO` |
| 3. Jump ("Jump Jump") | set the instruction pointer to `IP_CASE_0` or `IP_CASE_1`, chosen by the **Program Path Selector (PPS)** bit |

In this repo the same instruction appears in two notations:

- **numeric `.cj`** — `[copy_from, copy_to, jump_case_true, jump_case_false]`
- **textual `.prg.txt`** — `m <dst> <src>` (copy) and `j <cond> <label0> <label1>` (jump)

## Relationship to a Turing machine

RESM/BBJJ is derived from Turing machines and the **BitBitJump** OISC
(one-instruction-set computer). One RESM instruction is a *raw execution
step* — the smallest grain of "read a bit, write a bit, choose the next step".

| Turing machine | RESM / BBJJ |
|---|---|
| tape of cells (bits) | random-access bit memory |
| head reads a cell | `COPY_FROM` reads one bit |
| head writes a cell | `COPY_TO` writes one bit |
| transition function: read → write, move, change state | one instruction = copy + jump (the jump *is* the state transition) |
| next transition depends on the current symbol | the PPS bit selects `IP_CASE_0` vs `IP_CASE_1` |

## How general algorithms fit

Because the machine is Turing-complete, any algorithm can be compiled down to
it. The recipe is a lowering chain:

1. **high-level algorithm** (e.g. MD5)
2. → **boolean / arithmetic operations** (`AND/OR/XOR/NOT`, `+ mod 2^32`)
3. → **digital circuits** (each gate ≈ 7 copy+jump instructions; a full adder = 5 gates; a 32-bit add = 32 chained full adders)
4. → **control flow** (loops become `j` jumps, or are unrolled straight-line)
5. → **literal data** (constants and inputs embedded as bit values)

### Worked example: MD5

`vm_programs/md5_gen.py` is a compiler that lowers MD5 onto this substrate:
bitwise round functions become gate circuits, modular 32-bit addition becomes
ripple-carry full-adder chains, rotation becomes index remapping, and the
64-round loop is unrolled with the `K[i]`/`s[i]`/`g` constants embedded. The
result (`vm_programs/program_md5.prg.txt`, ~376k instructions) produces
bit-for-bit the same digest as `hashlib` — a concrete witness that the machine
runs real algorithms. See `vm_programs/md5.md` for the details.

## Why this minimalism matters

- **Turing completeness** — any computation can be expressed.
- **Micro-code as the lowest layer** — higher-level languages compile to it or
  are interpreted on top of it.
- **Genetic programming / program synthesis** — 1-bit granularity enables
  micro-mutations and evolutionary search (e.g. `arkenidar/simple`).
- **Code compression** — the uniform format makes program rewriting and
  optimization granular and tractable.
- **Self-modifying code** — programs can rewrite themselves (progressive
  decompression at runtime).
- **Halting analysis** — the VM can detect infinite loops for a well-defined
  subset of programs.

## Links

- `arkenidar/resm_aka_bbjj` — the RESM/BBJJ CPU design and docs:
  <https://github.com/arkenidar/resm_aka_bbjj>
- Full documentation: <https://arkenidar.github.io/resm_aka_bbjj/docs/full-doc.html>
- `BitBitJump` on Esolangs: <https://esolangs.org/wiki/BitBitJump>
- `arkenidar/CopyJumpMachine` — Python interpreter for the textual format:
  <https://github.com/arkenidar/CopyJumpMachine>
- `arkenidar/simple` — program synthesis / decompressor discovery:
  <https://github.com/arkenidar/simple>
