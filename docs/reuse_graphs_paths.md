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

1. **parse** the program into instructions + labels;
2. **detect** exact-duplicate, self-contained, single-entry/single-exit
   fragments (canonicalized so label-renamed clones match, and "exit labels"
   sitting just past the body are recognized);
3. **score** each fragment by net size savings and **greedily extract** the best;
4. **rewrite**: keep one copy of the body; replace each occurrence with
   (a) set the return register (`⌈log₂N⌉` bits) + jump in, and (b) a dispatch
   tree at the body's exit that jumps back to the right continuation.

`vm_programs/verify_outliner.py` runs the original vs the rewritten program
under `CopyJumpMachine.py` and asserts identical output bits.

Results on the repo's own programs:

- `program_integer_sum.prg.txt`: the 29-instruction full adder (inlined 7×) is
  extracted once → **233 → 94 instructions (−139)**, verified bit-identical on
  several inputs.
- `program_inline_demo.prg.txt` (synthetic): an 8-instruction body inlined 4× →
  **44 → 36 instructions (−8)**, verified bit-identical.

## Related

- `resm_bbjj.md` — the machine model (single instruction, no ALU, Turing map).
- `vm_programs/md5.md` — a concrete compiled algorithm (inlined reuse).
