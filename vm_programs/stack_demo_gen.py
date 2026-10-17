#!/usr/bin/env python3
"""Generate a stack (push/pop) demo using peek/poke (@) addressing.

A software stack is the first rung of the data-structure tower that peek/poke
unlocks. Stack cells live at STACK_BASE..STACK_BASE+999; the stack pointer SP
is a 13-bit address register at SP..SP+12.

  push(x) = poke x at @SP, then SP++   (ripple increment)
  pop()   = SP--, then output @SP      (ripple decrement + peek)

Demo: push 0,1,1 then pop three times -> output [1, 1, 0] (visible LIFO reversal).
"""

import os

SP = 2000          # stack pointer register (13 bits: 2000..2012)
SP_BITS = 13
STACK_BASE = 5000

HERE = os.path.dirname(os.path.abspath(__file__))


class Emit:
    def __init__(self):
        self.lines = []
        self.tag = 0

    def emit(self, s):
        self.lines.append(s)

    def _t(self):
        self.tag += 1
        return self.tag


def emit_load_const(e, base, value, nbits):
    for i in range(nbits):
        e.emit(f"m {base + i} {(value >> i) & 1}")


def emit_increment(e, base, nbits):
    t = e._t()
    for i in range(nbits):
        e.emit(f"j {base + i} i{i}_is1__{t}")
        e.emit(f"m {base + i} 1")          # bit 0 -> set 1, done
        e.emit(f"j inc_done__{t}")
        e.emit(f"l i{i}_is1__{t}")
        e.emit(f"m {base + i} 0")          # bit 1 -> set 0, ripple to next
    e.emit(f"l inc_done__{t}")


def emit_decrement(e, base, nbits):
    t = e._t()
    for i in range(nbits):
        e.emit(f"j {base + i} d{i}_is1__{t}")
        e.emit(f"m {base + i} 1")          # bit 0 -> set 1, borrow
        if i < nbits - 1:
            e.emit(f"j d{i + 1}__{t}")
        else:
            e.emit(f"j dec_done__{t}")     # underflow on last bit -> done
        e.emit(f"l d{i}_is1__{t}")
        e.emit(f"m {base + i} 0")          # bit 1 -> set 0, done
        if i < nbits - 1:
            e.emit(f"j dec_done__{t}")
            e.emit(f"l d{i + 1}__{t}")
    e.emit(f"l dec_done__{t}")


def emit_push(e, x):
    e.emit(f"m @{SP} {x}")                 # poke x at mem[SP]
    emit_increment(e, SP, SP_BITS)


def emit_pop(e):
    emit_decrement(e, SP, SP_BITS)
    e.emit(f"m out @{SP}")                 # peek and output


def generate():
    e = Emit()
    e.emit("# stack demo (peek/poke): push 0,1,1 then pop -> expect [1,1,0] (LIFO reversal)")
    emit_load_const(e, SP, STACK_BASE, SP_BITS)
    emit_push(e, 0)
    emit_push(e, 1)
    emit_push(e, 1)
    emit_pop(e)
    emit_pop(e)
    emit_pop(e)
    e.emit("j end")

    path = os.path.join(HERE, "program_stack_demo.prg.txt")
    with open(path, "w") as f:
        for ln in e.lines:
            f.write(ln + "\n")
    print(f"wrote {path} ({len(e.lines)} lines)")


if __name__ == "__main__":
    generate()
