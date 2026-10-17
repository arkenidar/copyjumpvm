# Call stack & the C-like function language (the "control" track)

This is the *control* side of the tower (not data): a **software call stack**
for invoking subroutines, and a **C-borrowed higher-level language** for
defining functions, compiled down to copyjump.

## The calling convention (ABI)

- **Arguments** → fixed argument registers `A0, A1, …` (each an `W`-bit word).
- **Return value** → fixed return register `R0` (`W` bits).
- **Return address** → pushed on a **software call stack** (a `RET_BITS`-bit
  stack pointer + `poke`), popped with `peek` + `j @reg` (computed goto).

```
call f:    write args -> A0..An ; push return_addr ; j f_entry
return:    write result -> R0 ;  pop return_addr ;  j @return_addr
```

The **return address is an instruction index**, known by the *compiler* (it
tracks the instruction count), which is why the higher level must be compiled.

Recursion works because each call pushes its own return address; the compiler
saves live arguments on the stack around a call and restores them after
(callee-saved), so a recursive call doesn't clobber the caller's `n`.

## The language (a C subset)

```c
int sum(int a, int b) {
    return a + b;
}

int countdown(int n) {
    if (n == 0) {
        return 0;
    }
    output_int(n);
    return countdown(n - 1);
}

int main() {
    return countdown(3);
}
```

| Aspect | Choice |
|---|---|
| types | `int` = `W`-bit unsigned word (W = 8 for now) |
| operators | `+ - == != < <= > >= && \|\| !` (arithmetic/comparison synthesized from gates + full adders — the machine has no ALU) |
| statements | `return expr;`, `if (cond) {…} else {…}`, `expr;` (calls), `while (cond) {…}` |
| built-ins | `output_bit(x)`, `output_int(x)` |
| entry point | `int main() { … }` |
| excluded (data track) | pointers, arrays, structs, heap |

## The tower

```
Level 0: copyjump + peek/poke + j @reg        (bits, copy + branch)
Level 1: ABI — call/return, software call stack  (this)
Level 2: the C-like language                    (this)
   └── cc.py compiles Level 2 -> Level 1 -> Level 0
```

## Cost note

The software stack is the honest price of "no call-stack hardware": each call
pushes a `RET_BITS`-bit return address (per-bit `poke` + ripple-increment of
the SP), each return pops it (ripple-decrement + `peek`). That's ~1.5k
instructions per call/return pair — expensive, but it's *real* (built entirely
from copy + jump + peek/poke), and it's what makes recursion *possible* on the
substrate.
