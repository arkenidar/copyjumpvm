#!/usr/bin/env python3
"""cc.py — a tiny C-like compiler targeting copyjump (+ peek/poke + j @reg).

Compiles `int f(int a, int b) { ... }` function definitions to copyjump
microcode, using a software call stack (return addresses pushed/popped with
poke/peek + a stack pointer, returned via `j @reg`), and synthesizing
arithmetic (+,-,comparisons) from gate primitives + full adders (no ALU).

Usage: python3 cc.py <source.c> [output.prg.txt]
"""

import os
import re
import sys

W = 8                 # int width (bits)
RET_BITS = 13         # return-address (instruction index) width
SP_BITS = 13          # stack pointer width

# --- memory layout ---
ARG = [100, 108, 116]  # argument registers A0, A1, A2 (8 bits each)
RET = 124              # return-value register R0 (8 bits)
TEMP_BASE = 200        # temp registers (8-bit words, allocated on demand)
STACK_BASE = 4000      # call-stack region (cells)
SP = 6000              # stack pointer register (13 bits: 6000..6012)
RETADDR = 6200         # popped return address (13 bits: 6200..6212)
T0, T1, T2, T3 = 7000, 7001, 7002, 7003  # scratch bits
CARRY = 7004           # carry scratch bit
BIT_TEMP_BASE = 7100   # comparison-result bits (allocated on demand)

# --- code-size constants (for computing forward return addresses) ---
INCR_SIZE = 4 * SP_BITS             # ripple increment: 4 instr/bit
DECR_SIZE = 5 * (SP_BITS - 1) + 4   # ripple decrement
PUSH_SIZE = RET_BITS * (1 + INCR_SIZE)   # push a return address
POP_SIZE = RET_BITS * (DECR_SIZE + 1)    # pop a return address


class Emitter:
    def __init__(self):
        self.lines = []
        self.tag = 0
        self.n = 0               # instruction count
        self.temp_next = TEMP_BASE
        self.bit_next = BIT_TEMP_BASE

    def emit(self, s):
        self.lines.append(s)
        if s[:2] in ('m ', 'j '):
            self.n += 1

    def _t(self):
        self.tag += 1
        return self.tag

    def alloc(self):
        t = self.temp_next
        self.temp_next += W
        return t

    def alloc_bit(self):
        b = self.bit_next
        self.bit_next += 1
        return b

    # ---- single-bit gates ----
    def bit_not(self, dst, a):
        t = self._t()
        self.emit(f"j {a} a1__{t}")
        self.emit(f"m {dst} 1")
        self.emit(f"j done__{t}")
        self.emit(f"l a1__{t}")
        self.emit(f"m {dst} 0")
        self.emit(f"l done__{t}")

    def bit_and(self, dst, a, b):
        t = self._t()
        self.emit(f"j {a} a1__{t}")
        self.emit(f"m {dst} 0")
        self.emit(f"j done__{t}")
        self.emit(f"l a1__{t}")
        self.emit(f"m {dst} {b}")
        self.emit(f"l done__{t}")

    def bit_or(self, dst, a, b):
        t = self._t()
        self.emit(f"j {a} a1__{t}")
        self.emit(f"m {dst} {b}")
        self.emit(f"j done__{t}")
        self.emit(f"l a1__{t}")
        self.emit(f"m {dst} 1")
        self.emit(f"l done__{t}")

    def bit_xor(self, dst, a, b):
        t = self._t()
        self.emit(f"j {a} a1__{t}")
        self.emit(f"m {dst} {b}")
        self.emit(f"j done__{t}")
        self.emit(f"l a1__{t}")
        self.emit(f"j {b} a1b1__{t}")
        self.emit(f"m {dst} 1")
        self.emit(f"j done__{t}")
        self.emit(f"l a1b1__{t}")
        self.emit(f"m {dst} 0")
        self.emit(f"l done__{t}")

    # ---- word helpers ----
    def copy_word(self, dst, src):
        for i in range(W):
            self.emit(f"m {dst + i} {src + i}")

    def load_const(self, dst, value):
        for i in range(W):
            self.emit(f"m {dst + i} {(value >> i) & 1}")

    # ---- arithmetic (W-bit, no ALU -> synthesized) ----
    def full_adder(self, sum_dst, a, b, cin, carry_dst):
        self.bit_xor(T0, a, b)
        self.bit_and(T2, a, b)
        self.bit_xor(sum_dst, T0, cin)
        self.bit_and(T1, T0, cin)
        self.bit_or(carry_dst, T1, T2)

    def add_word(self, dst, a, b, cin=0):
        self.emit(f"m {CARRY} {cin}")
        for i in range(W):
            self.full_adder(dst + i, a + i, b + i, CARRY, CARRY)

    def sub_word(self, dst, a, b):
        # dst = a - b = a + ~b + 1  (two's complement)
        nb = self.alloc()
        for i in range(W):
            self.bit_not(nb + i, b + i)
        self.add_word(dst, a, nb, cin=1)

    def eq_word(self, dst_bit, a, b):
        self.emit(f"m {T2} 1")   # running AND
        for i in range(W):
            self.bit_xor(T0, a + i, b + i)
            self.bit_not(T1, T0)
            self.bit_and(T2, T2, T1)
        self.emit(f"m {dst_bit} {T2}")

    def lt_word(self, dst_bit, a, b):
        self.emit(f"m {T2} 0")   # lt
        self.emit(f"m {T3} 1")   # higher bits equal so far
        for i in range(W - 1, -1, -1):
            self.bit_not(T0, a + i)
            self.bit_and(T1, T0, b + i)     # ~a & b
            self.bit_and(T1, T1, T3)        # and higher-equal
            self.bit_or(T2, T2, T1)         # lt |= ...
            self.bit_xor(T0, a + i, b + i)
            self.bit_not(T0, T0)            # equal bit
            self.bit_and(T3, T3, T0)        # update higher-equal
        self.emit(f"m {dst_bit} {T2}")

    # ---- the software call stack ----
    def emit_increment(self, base, nbits):
        t = self._t()
        for i in range(nbits):
            self.emit(f"j {base + i} i{i}_is1__{t}")
            self.emit(f"m {base + i} 1")
            self.emit(f"j inc_done__{t}")
            self.emit(f"l i{i}_is1__{t}")
            self.emit(f"m {base + i} 0")
        self.emit(f"l inc_done__{t}")

    def emit_decrement(self, base, nbits):
        t = self._t()
        for i in range(nbits):
            self.emit(f"j {base + i} d{i}_is1__{t}")
            self.emit(f"m {base + i} 1")
            if i < nbits - 1:
                self.emit(f"j d{i + 1}__{t}")
            else:
                self.emit(f"j dec_done__{t}")
            self.emit(f"l d{i}_is1__{t}")
            self.emit(f"m {base + i} 0")
            if i < nbits - 1:
                self.emit(f"j dec_done__{t}")
                self.emit(f"l d{i + 1}__{t}")
        self.emit(f"l dec_done__{t}")

    def call(self, func_label):
        # push the return address (MSB first so pop reconstructs LSB-first)
        ret_addr = self.n + PUSH_SIZE + 1
        for bit in reversed(range(RET_BITS)):
            self.emit(f"m @{SP} {(ret_addr >> bit) & 1}")
            self.emit_increment(SP, SP_BITS)
        self.emit(f"j {func_label}")

    def ret(self):
        for bit in range(RET_BITS):
            self.emit_decrement(SP, SP_BITS)
            self.emit(f"m {RETADDR + bit} @{SP}")
        self.emit(f"j @{RETADDR}")

    def define_func(self, name):
        self.emit(f"l {name}")


# ---- lexer ----
def tokenize(src):
    tokens = []
    i = 0
    while i < len(src):
        c = src[i]
        if c.isspace():
            i += 1
            continue
        if c == '/' and i + 1 < len(src) and src[i + 1] == '/':
            while i < len(src) and src[i] != '\n':
                i += 1
            continue
        if c.isdigit():
            j = i
            while j < len(src) and src[j].isdigit():
                j += 1
            tokens.append(('num', int(src[i:j])))
            i = j
            continue
        if c.isalpha() or c == '_':
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == '_'):
                j += 1
            tokens.append(('id', src[i:j]))
            i = j
            continue
        for op in ('==', '!=', '<=', '>=', '&&', '||', '<<', '>>'):
            if src.startswith(op, i):
                tokens.append(('op', op))
                i += len(op)
                break
        else:
            if c in '+-*/%<>&|^!~(){};,=':
                tokens.append(('op', c))
                i += 1
            else:
                raise Exception(f"unexpected char: {c}")
    tokens.append(('eof', None))
    return tokens


# ---- parser (recursive descent) ----
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def next(self):
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, kind, val=None):
        t = self.next()
        if t[0] != kind or (val is not None and t[1] != val):
            raise Exception(f"expected {(kind, val)}, got {t}")
        return t

    def parse_program(self):
        funcs = []
        while self.peek()[0] == 'id' and self.peek()[1] == 'int':
            funcs.append(self.parse_function())
        return funcs

    def parse_function(self):
        self.expect('id', 'int')
        name = self.expect('id')[1]
        self.expect('op', '(')
        params = []
        if self.peek()[1] != ')':
            while True:
                self.expect('id', 'int')
                params.append(self.expect('id')[1])
                if self.peek()[1] == ',':
                    self.next()
                else:
                    break
        self.expect('op', ')')
        return ('func', name, params, self.parse_block())

    def parse_block(self):
        self.expect('op', '{')
        stmts = []
        while self.peek()[1] != '}':
            stmts.append(self.parse_stmt())
        self.expect('op', '}')
        return stmts

    def parse_stmt(self):
        t = self.peek()
        if t[0] == 'id' and t[1] == 'return':
            self.next()
            e = self.parse_expr()
            self.expect('op', ';')
            return ('return', e)
        if t[0] == 'id' and t[1] == 'if':
            self.next()
            self.expect('op', '(')
            cond = self.parse_expr()
            self.expect('op', ')')
            then = self.parse_block()
            else_ = None
            if self.peek()[1] == 'else':
                self.next()
                else_ = self.parse_block()
            return ('if', cond, then, else_)
        if t[0] == 'id' and t[1] == 'while':
            self.next()
            self.expect('op', '(')
            cond = self.parse_expr()
            self.expect('op', ')')
            return ('while', cond, self.parse_block())
        e = self.parse_expr()
        self.expect('op', ';')
        return ('expr', e)

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.peek()[1] == '||':
            self.next()
            left = ('binop', '||', left, self.parse_and())
        return left

    def parse_and(self):
        left = self.parse_cmp()
        while self.peek()[1] == '&&':
            self.next()
            left = ('binop', '&&', left, self.parse_cmp())
        return left

    def parse_cmp(self):
        left = self.parse_add()
        if self.peek()[1] in ('==', '!=', '<', '<=', '>', '>='):
            op = self.next()[1]
            left = ('binop', op, left, self.parse_add())
        return left

    def parse_add(self):
        left = self.parse_unary()
        while self.peek()[1] in ('+', '-'):
            op = self.next()[1]
            left = ('binop', op, left, self.parse_unary())
        return left

    def parse_unary(self):
        if self.peek()[1] in ('!', '~', '-'):
            op = self.next()[1]
            return ('unop', op, self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        e = self.parse_primary()
        while self.peek()[1] == '(':
            self.next()
            args = []
            if self.peek()[1] != ')':
                while True:
                    args.append(self.parse_expr())
                    if self.peek()[1] == ',':
                        self.next()
                    else:
                        break
            self.expect('op', ')')
            e = ('call', e[1], args)
        return e

    def parse_primary(self):
        t = self.next()
        if t[0] == 'num':
            return ('const', t[1])
        if t[0] == 'id':
            return ('var', t[1])
        if t[1] == '(':
            e = self.parse_expr()
            self.expect('op', ')')
            return e
        raise Exception(f"unexpected token: {t}")


# ---- codegen ----
class Compiler(Emitter):
    def compile_program(self, funcs):
        # init the stack pointer
        for i in range(SP_BITS):
            self.emit(f"m {SP + i} {(STACK_BASE >> i) & 1}")
        # call main, then terminate
        self.call('main')
        self.emit('j end')
        for fn in funcs:
            self.compile_func(fn)

    def compile_func(self, fn):
        name, params, stmts = fn[1], fn[2], fn[3]
        self.define_func(name)
        for s in stmts:
            self.compile_stmt(s, params)

    def compile_stmt(self, s, params):
        kind = s[0]
        if kind == 'return':
            k, a = self.compile_expr(s[1], params)
            if k == 'word':
                self.copy_word(RET, a)
            else:
                self.emit(f"m {RET} {a}")
                for i in range(1, W):
                    self.emit(f"m {RET + i} 0")
            self.ret()
        elif kind == 'if':
            cond = s[1]
            k, a = self.compile_expr(cond, params)
            else_lbl = f"else_{self._t()}"
            then_lbl = f"then_{self._t()}"
            end_lbl = f"endif_{self._t()}"
            self.emit(f"j {a} {else_lbl} {then_lbl}")
            self.emit(f"l {else_lbl}")
            if s[3] is not None:
                for st in s[3]:
                    self.compile_stmt(st, params)
            self.emit(f"j {end_lbl}")
            self.emit(f"l {then_lbl}")
            for st in s[2]:
                self.compile_stmt(st, params)
            self.emit(f"l {end_lbl}")
        elif kind == 'while':
            loop_lbl = f"loop_{self._t()}"
            body_lbl = f"body_{self._t()}"
            end_lbl = f"end_{self._t()}"
            self.emit(f"l {loop_lbl}")
            k, a = self.compile_expr(s[1], params)
            self.emit(f"j {a} {end_lbl} {body_lbl}")
            self.emit(f"l {body_lbl}")
            for st in s[2]:
                self.compile_stmt(st, params)
            self.emit(f"j {loop_lbl}")
            self.emit(f"l {end_lbl}")
        elif kind == 'expr':
            e = s[1]
            if e[0] == 'call' and e[1] == 'output_bit':
                k, a = self.compile_expr(e[2][0], params)
                self.emit(f"m out {a}")
            elif e[0] == 'call' and e[1] == 'output_int':
                k, a = self.compile_expr(e[2][0], params)
                for i in range(W):
                    self.emit(f"m out {a + i}")
            else:
                self.compile_expr(e, params)  # discard result

    def compile_expr(self, e, params):
        tag = e[0]
        if tag == 'const':
            t = self.alloc()
            self.load_const(t, e[1])
            return ('word', t)
        if tag == 'var':
            return ('word', ARG[params.index(e[1])])
        if tag == 'binop':
            op = e[1]
            if op in ('+', '-'):
                lk, la = self.compile_expr(e[2], params)
                rk, ra = self.compile_expr(e[3], params)
                t = self.alloc()
                if op == '+':
                    self.add_word(t, la, ra)
                else:
                    self.sub_word(t, la, ra)
                return ('word', t)
            if op in ('==', '!=', '<', '<=', '>', '>='):
                lk, la = self.compile_expr(e[2], params)
                rk, ra = self.compile_expr(e[3], params)
                b = self.alloc_bit()
                if op == '==':
                    self.eq_word(b, la, ra)
                elif op == '!=':
                    self.eq_word(b, la, ra)
                    self.bit_not(b, b)
                elif op == '<':
                    self.lt_word(b, la, ra)
                elif op == '<=':
                    self.lt_word(b, ra, la)
                    self.bit_not(b, b)
                elif op == '>':
                    self.lt_word(b, ra, la)
                else:  # '>='
                    self.lt_word(b, la, ra)
                    self.bit_not(b, b)
                return ('bit', b)
            if op in ('&&', '||'):
                lk, la = self.compile_expr(e[2], params)
                rk, ra = self.compile_expr(e[3], params)
                b = self.alloc_bit()
                if op == '&&':
                    self.bit_and(b, la, ra)
                else:
                    self.bit_or(b, la, ra)
                return ('bit', b)
            raise Exception(f"unknown binop {op}")
        if tag == 'unop':
            op = e[1]
            k, a = self.compile_expr(e[2], params)
            if op == '!':
                b = self.alloc_bit()
                self.bit_not(b, a)
                return ('bit', b)
            if op == '~':
                t = self.alloc()
                for i in range(W):
                    self.bit_not(t + i, a + i)
                return ('word', t)
            if op == '-':  # unary negation (0 - x)
                t = self.alloc()
                z = self.alloc()
                self.load_const(z, 0)
                self.sub_word(t, z, a)
                return ('word', t)
            raise Exception(f"unknown unop {op}")
        if tag == 'call':
            name = e[1]
            args = e[2]
            for i, arg in enumerate(args):
                k, a = self.compile_expr(arg, params)
                self.copy_word(ARG[i], a)
            self.call(name)
            return ('word', RET)
        raise Exception(f"unknown expr {e}")


def main():
    if len(sys.argv) < 2:
        print("usage: python3 cc.py <source.c> [output.prg.txt]")
        sys.exit(2)
    src_file = sys.argv[1]
    src = open(src_file).read()
    funcs = Parser(tokenize(src)).parse_program()
    c = Compiler()
    c.compile_program(funcs)
    out = sys.argv[2] if len(sys.argv) > 2 else src_file.replace('.c', '.prg.txt')
    with open(out, 'w') as f:
        for ln in c.lines:
            f.write(ln + '\n')
    print(f"wrote {out} ({len(c.lines)} lines, {c.n} instructions)")


if __name__ == '__main__':
    main()



