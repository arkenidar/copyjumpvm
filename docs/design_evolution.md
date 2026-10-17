# Design evolution — how this project reasons its way forward

> **This is a living log.** Each new step of *reasoning* is appended here
> incrementally (not rewritten), so the document mirrors the evolution and
> stays open for others to read and participate. The code lives in
> `vm_programs/`; this file records *why* it looks the way it does.

---

## 1. Origin — the Hutter Prize thesis

We did not start from "a copy+jump virtual machine." We started, ~20 years ago,
from the **Hutter Prize**: *compression is a measurable proxy for intelligence*
— a self-contained program that regenerates a file *is a model* of that file.

**Key insight:** *compressed data = a program; decompression = execution;
better compression = a better model.* This makes "find the smallest program
that outputs D" the central question. → `compression_intelligence.md`

## 2. The minimal machine — RESM / BBJJ

To study that question on a tractable substrate, we minimized the machine
itself: one instruction, *copy a bit, then jump to one of two places*.

**Key insight:** the machine has **no ALU** and **no call stack** — nothing
but copy + branch. Both the *data plane* (arithmetic/logic) and the *control
plane* (subroutine reuse) are **software-defined**. → `resm_bbjj.md`

## 3. Code reuse as graphs — outliner, then generator-aware

Reuse without a stack: shared subgraphs + a return register + dispatch. We
built `outliner.js` (post-hoc outlining of inlined code), measured it, and
then realized something better.

**Key insight:** a **generator knows its patterns by name**, so it should emit
shared subroutines *from the start* instead of inlining and re-discovering
them. `md5_gen.py` became **reuse-aware** — shared `add32` subroutines, then the
`F/G/H/I` round functions — `program_md5.prg.txt` dropped
**260,996 → 36,865 instructions (~7×)**, each step with no post-hoc pass and
verified against `hashlib`. → `reuse_graphs_paths.md`

## 4. Research framing — optimize copyjump *in general*

Decoupled from any single benchmark, the question becomes a *science*:
the space of programs, the rewrite rules, the complexity of "smallest
program", synthesis, and the **ISA-richness ↔ program-size** tradeoff
(the Kolmogorov invariance constant). → `research_roadmap.md`

## 5. The next primitive — peek / poke (indirect addressing)

The 64 MD5 rounds are *unrolled* because `K[i]`, `M[g]`, `s[i]` depend on the
round index `i` at runtime — and **without indirection you can't compute an
address**. Adding **peek** (read via an address held in a register) / **poke**
(write via a register) would let us write *one* round body + a counter + data
tables, and loop 64 times.

**Key insight (cost model):** indirection makes parameterized subroutines
*possible* but only *profitable* for large bodies or loops — it doesn't make a
7-instruction `bit_xor` worth sharing (passing 3 addresses ≈ 39 bits already
exceeds the body). The win is the **loop**, not the gates.

## 6. Address-as-value = pointers — the whole tower

"Address as value" **is a pointer** (peek/poke = pointer dereference). That
one primitive unlocks the entire tower of data structures, each rung built in
*software* on the previous one:

```
peek/poke  (address-as-value)     = pointer dereference
  + pointer arithmetic (base + i) = arrays       (static AND dynamic indexing)
  + an allocator (a program)      = heap         → dynamic arrays, objects
  + a stack pointer (a register)  = stack        → push/pop
  + stack of return addresses     = CALL STACK   → recursion  ← the "enabling"
  + node = (data, *next)          = linked list  → trees → hash maps → …
```

**Key insight — the flip:** *without* peek/poke, copyjump is a **fixed-address
machine** (FSM over a fixed bit-array — the "well-defined subset" with
decidable halting). *With* peek/poke it becomes a **pointer machine**, where
recursion and dynamic data structures become possible (and halting analysis
gets harder). So the earlier "no call stack → no recursion" and this "pointers
→ call stack → recursion" are two halves of one story: **a single primitive
flips the machine from *fixed* to *dynamic*.**

You don't add `malloc`, a stack, or a call-stack *to the ISA* — you add
indirection and build the rest in software. A hash map is not an instruction;
it's peek/poke + an allocator + a linked list.

---

## 7. Peek/poke implemented — still OISC, now with pointers

We added indirect addressing **as an addressing mode, not a new opcode**: an
operand prefixed with `@` is dereferenced — the 13-bit value stored at that
address is used as the actual address.

**Key insight — OISC vs URISC:** *OISC* counts instructions; *URISC* is the
minimality philosophy (Mavaddat & Parhami 1988). Adding indirection as a *mode*
keeps the single instruction (`[copy_from|ind, copy_to|ind, j0, j1]`) — so the
machine is **still OISC and still URISC**, just with a richer addressing model.

The extended ISA (same `m`/`j`; `@` is a mode):

```
m  dst  src    # direct
m  dst  @src   # peek (indirect read)
m  @dst src    # poke (indirect write)
m  @dst @src   # both
j  @reg        # computed goto (indirect jump / return)
```

Implemented in `CopyJumpMachine.py` (`ADDR_BITS=13`, `addr_of`), verified by
`program_indirect_demo.prg.txt` (peek + poke) and a computed-goto check.

This is "one primitive unlocks the tower" made real: pointers are now
expressible, so arrays / heap / stacks / call-stacks / recursion become
*software* built on the substrate.

*(next: the round loop — use peek to read `K[i]`/`M[g]`/`s[i]` and collapse the
64× unrolled rounds into one loop; then demonstrate the data-structure tower.)*

## 8. Deeper reuse + why the round *loop* is not worth it

We shared the remaining fixed-address bodies — the **register rotation**
(`A=D, D=C, C=B, B=BNEW`, 128 instr ×64 → one body) and the **rotate** (16
shift amounts → 16 bodies). `program_md5.prg.txt`: 36,865 → **28,272
instructions** (~9× smaller than the original 260,996).

Then we tested the loop idea and found a **negative result worth recording**:

**In a no-ALU machine, immediate constants beat data tables.** The 64 unrolled
rounds are already near-optimal: the per-round cost that remains is `K[i]`
loaded as *immediates* (32 `m` per round) — the cheapest possible encoding. A
loop would read `K[i]` from a table via peek, which needs (a) initializing the
table (2048 `m`), (b) address arithmetic or base+offset addressing to index it,
and (c) a counter. That costs *more* than the immediates it replaces — because
data here is also loaded via instructions, and reading it back costs extra
peeks.

So "collapse 64× into a loop" is a **non-optimization** for this substrate:
code (immediates) and data (tables) cost the same to load, but immediates are
consumed for free while tables are read back through peek.

*(next: demonstrate the data-structure tower — a software stack / call-stack /
linked list — now that peek/poke exist.)*
