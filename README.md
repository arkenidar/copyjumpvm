# copyjumpvm
"copy+jump only" virtual machine

The "vm_programs" directory contains EXAMPLE programs in source format, a compiler, compiled programs, translator to copyjump.js format, translated programs

you can enjoy exploring this work of mine. PS: maybe I have "accidentally" found a way to redefine the Alan Turing's "halting problem". wouldn't it be cool?

## Machine model — RESM / BBJJ ("copy + jump")

copyjumpvm is an implementation of a minimal, Turing-complete machine called
**RESM** (*Raw Execution-Step Machine*) aka **BBJJ** (*Bit Bit Jump Jump*):
every instruction just copies one bit and jumps to one of two next
instructions, chosen by a path-selector bit. Any algorithm can be compiled
down to it — see `docs/resm_bbjj.md` for the full explanation (including how
the MD5 program in `vm_programs/` is such a compilation).

```shell
./run.sh iloop.cj # this outputs: "status: infinite loop (iloop) detected."
```

```shell
./run.sh tloop.cj # this outputs: "status: terminated"
```

so the status (terminates or infinitely loops) can be determined, thus solving partly the halting problem (works for a well-defined subset of programs, see source code or notes in ouput)

## Python runner example programs

The `vm_programs/` directory also holds textual micro-programs executed by
`vm_programs/CopyJumpMachine.py` (the "pythonic runner"), plus their generators
and reference validators:

```shell
# MD5 of an embedded message (single 512-bit block), diffed against hashlib
python3 vm_programs/md5_gen.py        # regenerate program_md5.prg.txt
python3 vm_programs/md5_check.py      # run in the VM and compare to hashlib

# xorshift32 PRNG
python3 vm_programs/xorshift32_reference.py 0x12345678 10
python3 vm_programs/CopyJumpMachine.py vm_programs/program_xorshift32_loop.prg.txt
```

See `docs/history.md` for the build logs and `vm_programs/md5.md` for the MD5
design notes.

---

Dario Cangialosi (Coder) says: https://github.com/arkenidar/copyjumpvm I had been working on these kind of project for a "microcode-based virtual machine" for a testing benchmark for applying "code compression" code optimization techniques, since the microcode format allows for fine-grained mutations and then fine-grained optimizations by rewriting. The smallest grain is a 1 bit copy operation followed by a Instruction Pointer assignment (jump) by choice of 2 given option values selected by a fixedly positioned path-selector bit. At the following (arkenidar/copyjumpvm [https://github.com/arkenidar/copyjumpvm]) link you can see 2 program formats examples (textual format and numeric/tabular format) and the VM here linked can execute numeric tabular formatted microcode (*.cj). Other my GitHub projects are similar, but at times different, explorations (e.g. arkenidar / CopyJumpMachine [https://github.com/arkenidar/CopyJumpMachine] can execute textual format micro-programs, and then can be a easier starting point for building. [https://github.com/arkenidar/simple] arkenidar / simple has a brute force discovery of programs that produce a given output, feature useful for a code compression challenge where the code should work as a data decompressor when executed, so a decompressor program should be found or synthesized)
