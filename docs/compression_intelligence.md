# Compression as intelligence — the origin of copyjump

This project did not start as "a copy+jump virtual machine." It started, about
twenty years ago, from the **Hutter Prize** thesis:

> *"Being able to compress well is closely related to acting intelligently …
> as a path to AGI."*

## The origin: the Hutter Prize (2006)

- **Task** — losslessly compress `enwik9` (the first 1 GB of Wikipedia) so that
  the **decompressor program + the compressed data together** are below
  ~100 MB (the running record).
- **The submission is a self-contained program** — a compressor `comp.exe`
  (size `S1`) produces an archive `archive.exe` (size `S2`); running
  `archive.exe` with no outside input regenerates the 1 GB file. The score is
  `S = S1 + S2 < L`.
- **Prize** — `500'000 € × (1 − S/L)`, minimum €5,000 (1% improvement), within
  ≲50 h on a single core, <10 GB RAM, <100 GB HDD.
- **The point** — the compressed file *is* a program, and decompression *is*
  execution. A program that reproduces the data **is a model of the data**;
  so the smaller the program, the better the understanding. Compression, in
  this view, is a measurable proxy for intelligence.

## The chain this spawned (the arrow, in the right order)

Everything here grows *out of* that thesis, not toward it:

1. **The thesis** — compression = intelligence; a decompressor is a model.

2. **RESM / BBJJ ("Raw Execution-Step Machine" / "Bit Bit Jump Jump")** — a
   deliberately minimal substrate for expressing those decompressor programs:
   nothing but *copy one bit + jump to one of two places*. The least structure
   a "generator program" can have. (See `resm_bbjj.md`.)

3. **`arkenidar/simple`** — brute-force *synthesis* of a program that emits a
   given output: the "find the decompressor" problem, taken literally.

4. **`outliner.js`** — the deterministic version of the same search: instead of
   synthesizing a decompressor from scratch, it *factors an existing one*
   (inlining → subgraph reuse). (See `reuse_graphs_paths.md`.)

5. **The seed-program pipeline** — encode a data file as a trivial program
   (`m out 0`, `m out 1`, …), then size-optimize that program. The optimized
   program **is** the compressed data; running it **is** decompression — the
   prize's `archive.exe` in miniature.

## The key equivalence

```
compressed data  =  a program
decompression    =  execution
better compression =  a better model of the data
```

The seed-program idea makes this literal in copyjump: the "compressed file" is
a copyjump program, and the runner is the decompressor.

## Where copyjump sits on the compression axis

Compression has (at least) two independent axes:

- **repetition** — grammar / dictionary / loops (what the outliner exploits);
- **statistics** — context modelling + entropy coding (Huffman/arithmetic),
  which the Hutter winners (`cmix` and friends) exploit to reach ~10:1 on
  `enwik9`.

copyjump's toolchain is entirely on the *repetition* axis. A "general"
decompressor-generator would need **both** — loops (cycles) *and* entropy
coding — and its optimum is Kolmogorov complexity, which is uncomputable
(hence the prize pays for *any* measured improvement, not the optimum).

## Related

- `resm_bbjj.md` — the machine model.
- `reuse_graphs_paths.md` — code reuse and the outliner (the factoring step).
- `history.md` — build log.
