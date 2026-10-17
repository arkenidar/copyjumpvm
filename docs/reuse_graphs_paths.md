# Code reuse as graphs with paths (no call stack)

A copyjump (RESM/BBJJ) program is a *control-flow graph*: instructions are
nodes, jump targets are edges, and running the program is walking a path
through that graph. In that view, **code reuse** is just *sharing a subgraph*.

## The model

- **node** — one instruction ("copy a bit, then jump").
- **edge** — a possible jump (`IP_CASE_0` / `IP_CASE_1`).
- **path** — one execution trace through the graph.
- **subroutine** — an induced subgraph `S` with entry nodes `I` and exit nodes `O`.
- **call** — a path that enters `S` at some entry and leaves at some exit.
- **reuse** — several callers route their edges into the *same* `S`.

The only thing a "call" has to answer is: **which exit edge do I take?** The
three classic answers are below — and only the last one needs a stack.

## The three return strategies

1. **Structural (bake the return per call site).** Give `S` one exit label per
   call site; the return address is implicit in *which path you took*. Reuses
   the body, duplicates only the tiny return bookkeeping. Works for any static
   (DAG-shaped) call graph. No register, no stack.

2. **Return register (link bits).** The caller writes a small `return-index`
   into a few data bits before jumping in; `S` exits through a *dispatch tree*
   that reads those bits and routes back. In RESM this is native: the jump
   already picks between two targets via the **path-selector bit**, so `k`
   selector bits give `2^k` return targets. Still no stack — just a bounded
   bit-vector.

3. **Call stack.** Only *required* when reuse is dynamically nested or
   recursive — the return address isn't known statically and several pending
   returns must be remembered at once.

## When the stack is actually needed

The **dynamic call tree** of a run is a path in the static graph whose "shape"
(the chain of pending returns) *is* the stack. Therefore:

- **static / DAG call graphs** → no stack needed (strategies 1 or 2);
- **recursion / arbitrary nesting** → a stack is needed (or some equivalent
  unbounded memory, which you would build yourself out of bits).

This is exactly the classical hierarchy: a copyjump program with no stack is a
finite-state machine over its bits, and adding a stack (as data) upgrades it to
a pushdown machine — finite-state ⊂ pushdown ⊂ Turing.

## In this repo

- The machine has **no call stack**, so "reuse" today is done by **inlining at
  generation time**: `md5_gen.py` emits the same XOR/full-adder *pattern* many
  times with fresh labels (`program_integer_sum.prg.txt` duplicates the full
  adder 7× as `…__0 … __6`). That reuses the *form*, not the *graph nodes*.
- **Graph-level reuse** (sharing the actual nodes) would instead write the body
  once and jump into it from several places, returning via strategy 2 — which
  the `j <cond> <label0> <label1>` instruction already supports natively.

## Implementation: `outliner.js`

`vm_programs/outliner.js` is a Node script that actually performs this graph
rewrite (inlining → subgraph reuse) on a `.prg.txt` program:

**Naming.** "Outlining" is the compiler term for the *inverse of inlining*: an
*inliner* copies a function body into each call site, an *outliner* finds
repeated code and pulls it out into one shared function. Synonyms in the
literature: **procedure extraction**, **function outlining** (LLVM/GCC
`-moutline`), **identical code folding / ICF** (linkers), and **procedural
abstraction** (binary rewriters).

1. **parse** the program into instructions + labels;
2. **detect** exact-duplicate, self-contained, single-entry/single-exit
   fragments (canonicalized so label-renamed clones match, and "exit labels"
   sitting just past the body are recognized);
3. **score** each fragment by net size savings and **greedily extract** the best;
4. **rewrite**: keep one copy of the body; replace each occurrence with
   (a) set the return register (`⌈log₂N⌉` bits) + jump in, and (b) a dispatch
   tree at the body's exit that jumps back to the right continuation.

Extraction is **iterative**: after each rewrite it re-detects and extracts
again until no profitable fragment remains (so a program with several distinct
repeated bodies gets them all), and the return register is placed at the first
free address (auto-detected from the program's data, so it never collides).

`vm_programs/verify_outliner.py` runs the original vs the rewritten program
under `CopyJumpMachine.py` and asserts identical output bits.

### Measured results (v1, exact-duplicate fragments)

| Program | Before | After | Saved | % | Found |
|---|---|---|---|---|---|
| `program_integer_sum` | 233 | **94** | −139 | ~60% | 29-instr full adder ×7 (verified bit-identical) |
| `program_integer_sum_5` | 264 | 248 | −16 | ~6% | three fragments (8×6, 7×6, 7×2) — iterative |
| `program_inline_demo` (synthetic) | 44 | 36 | −8 | ~18% | 8-instr body ×4 (verified) |
| `program_inline_demo2` (synthetic) | 70 | 62 | −8 | ~11% | two distinct 8-instr bodies ×3 (verified) |
| `program_xorshift32_step` | 526 | 526 | 0 | 0% | — (parameterized, not exact dupes) |
| `program_xorshift32_loop` | 584 | 584 | 0 | 0% | — |
| `program_countdown` / `integer_counter` / gates | ≤65 | same | 0 | 0% | — (little/no duplication) |
| `program_md5` | ~261k | ~261k | ~0 | 0% | parameterized; too large for O(n²) anyway |

### When it actually shrinks the program

Two gates decide whether reuse pays off.

**1. Exactness (the v1 limit).** `outliner.js` only matches *byte-identical*
fragments — same operand addresses, labels renamed. The most-repeated patterns
in `xorshift32`/`md5` (the 7-instruction `xor`/`and`/`or` gates, the full
adder) are the *same shape* but with *different operand addresses*, so v1 finds
nothing. The `integer_sum` full adder wins because all 7 copies use the *same*
addresses (2, 3, 4, `in`, `out`). Parameterized clones need v2 (argument
passing).

**2. The cost model.** Net saving is

`(N−1)·S − [ N·(operands·13 + ⌈log₂N⌉ + 1) + (N−1) ]`

where `S` = body size, `N` = call sites, and each address operand costs ~13
bits (`⌈log₂ 8192⌉`) to pass through argument registers:

- **full adder** (`S`=29, 0 args) → wins big (−60%);
- **`bit_xor`** (`S`=7, 3 address args) → *never* worth it — passing 3 addresses
  (~39 bits) already exceeds the 7-instruction body;
- **`add32`** (`S`≈1100, 3 args) → always worth it (~49 instr/call vs 1100).

**3. Scalability caveat.** A *flat* return register costs `⌈log₂N⌉` bits per
call, so it does **not** scale to huge `N`: md5's ~57k gate instances would
*blow up* rather than shrink if shared naively. Big wins there need (a)
parameterized bodies (v2) *and* (b) **nested / hierarchical returns**
(subroutines calling subroutines) — which is exactly why real CPUs grew a call
stack.

## Related

- `resm_bbjj.md` — the machine model (single instruction, no ALU, Turing map).
- `vm_programs/md5.md` — a concrete compiled algorithm (inlined reuse).
- `compression_intelligence.md` — the Hutter-Prize origin (decompressor-generator).
