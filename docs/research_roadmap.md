# Research roadmap — optimizing copy-jump systems, in general

This is the program-optimization view of RESM/BBJJ, decoupled from any single
benchmark (the Hutter Prize is one instance; this is the *science* behind it).

## Framing

"Optimize a copy-jump system" means studying, for a fixed minimal machine:

1. the **space** of programs (what does one equivalence class look like?),
2. the **transformations** (which rewrites preserve I/O behavior?),
3. the **complexity** (how hard is "smallest program"?),
4. the **synthesis** (can you *find* the small program?),
5. the **design space** (which "derivative" ISA trades off richness vs. size?),
6. the **decidability** (which programs provably terminate, and does
   optimization preserve that?).

Copy-jump is a good substrate precisely because it is minimal: every
optimization becomes a visible bit-level / graph transformation, and
"equivalent programs" is a clean, well-defined relation.

## The six directions (and the literature)

| Direction | Established CS area |
|---|---|
| rewrite taxonomy & completeness | **Superoptimization** — Massalin 1987; STOKE / Souper (SMT + search) |
| smallest program for a function | **Smallest-grammar / SLP** — NP-hard (Charikar et al. 2005), O(log n)-approx; RePair, SEQUITUR |
| optimize-in-general engine | **Equality saturation / e-graphs** — Tate et al. 2009; the `egg` library |
| find a program from I/O examples | **Program synthesis** — SyGuS, CEGIS |
| program = DAG, time/space tradeoff | **Pebble games** — Pippenger 1981 (→ register allocation) |
| how rich should the ISA be? | **OISC / minimal-ISA** — SUBLEQ, MOV, BitBitJump; the Kolmogorov *invariance constant* |
| which programs terminate | **Decidable-halting classes** — the repo's own "well-defined subset" |

### 1. Rewrite taxonomy & completeness

Enumerate the local, semantics-preserving rewrites and ask which are *complete*:

- dead-copy elimination, jump threading, label coalescing, constant folding,
  self-copy removal (`m x x`), redundant-jump removal;
- block extraction / outlining (what `outliner.js` does);
- loop synthesis (the inverse of unrolling), inverse rotation;
- **open question**: is there a confluent (Church–Rosser) rewrite set?

### 2. Complexity

Prove "smallest copy-jump program for a given I/O relation" is NP-hard (it
should reduce to smallest-grammar), and find the best approximation ratio
achievable specifically on this machine.

### 3. Equality saturation / e-graph optimizer

The modern "optimize in general" engine: keep *all* equivalent programs in an
e-graph and extract the cheapest. Prototyping this over the copy-jump rewrite
rules would generalize the outliner from "greedy outlining" to "cost-driven
extraction over a whole equivalence class."

### 4. Program synthesis

Upgrade `arkenidar/simple`'s brute force into a smarter search (constraint/SMT,
or e-graph + cost): "smallest copy-jump program with this I/O table."

### 5. The derivative-ISA tradeoff

Measure the (ISA richness) ↔ (program size / steps) curve — i.e. *quantify the
Kolmogorov invariance constant* as you add an ALU, a word-copy, a counter, etc.
Copy-jump is the "zero point" of that curve; this is ISA-design research.

### 6. Halting-preserving optimization

Show that the optimizations *preserve* the decidable-termination class — tying
program optimization to the repo's halting-detection claim.

## Where the repo already sits

- `vm_programs/outliner.js` — greedy outlining (a special case of directions 1 & 3).
- `vm_programs/peephole.js` — the start of the rewrite taxonomy (direction 1).
- `vm_programs/md5_gen.py` — a compiler that lowers an algorithm to the substrate.
- `arkenidar/simple` (external) — brute-force synthesis (direction 4, naïve form).

## Concrete next steps

1. Grow the **peephole rule set** and test confluence.
2. A **complexity note** (NP-hardness + approximation).
3. An **e-graph prototype** (`egg`-style) for cost-driven extraction.
4. A **synthesis benchmark** (copy-jump as a SyGuS/SMT target).
5. A **derivative-ISA experiment** (measure size vs. instruction richness).
