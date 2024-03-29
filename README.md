# copyjumpvm
"copy+jump only" virtual machine

The "vm_programs" directory contains EXAMPLE programs in source format, a compiler, compiled programs, translator to copyjump.js format, translated programs

you can enjoy exploring this work of mine. PS: maybe I have "accidentally" found a way to redefine the Alan Turing's "halting problem". wouldn't it be cool?

```shell
./run.sh iloop.cj # this outputs: "status: infinite loop (iloop) detected."
```

```shell
./run.sh tloop.cj # this outputs: "status: terminated"
```

so the status (terminates or infinitely loops) can be determined, thus solving partly the halting problem (works for a well-defined subset of programs, see source code or notes in ouput)

Dario Cangialosi (Coder) says: https://github.com/arkenidar/copyjumpvm I had been working on these kind of project for a "microcode-based virtual machine" for a testing benchmark for applying "code compression" code optimization techniques, since the microcode format allows for fine-grained mutations and then fine-grained optimizations by rewriting. The smallest grain is a 1 bit copy operation followed by a Instruction Pointer assignment (jump) by choice of 2 given option values selected by a fixedly positioned path-selector bit. At the following (arkenidar/copyjumpvm [https://github.com/arkenidar/copyjumpvm]) link you can see 2 program formats examples (textual format and numeric/tabular format) and the VM here linked can execute numeric tabular formatted microcode (*.cj). Other my GitHub projects are similar, but at times different, explorations (e.g. arkenidar / CopyJumpMachine [https://github.com/arkenidar/CopyJumpMachine] can execute textual format micro-programs, and then can be a easier starting point for building. [https://github.com/arkenidar/simple] arkenidar / simple has a brute force discovery of programs that produce a given output, feature useful for a code compression challenge where the code should work as a data decompressor when executed, so a decompressor program should be found or synthesized)
