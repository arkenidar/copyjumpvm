#!/usr/bin/env node
/**
 * outliner.js — rewrite inlined copy+jump code into shared subgraphs.
 *
 * v1: extracts exact-duplicate, self-contained, single-entry/single-exit
 *     fragments (fall-through only; all internal labels are local). The shared
 *     body reads/writes the SAME fixed addresses every time (so no argument
 *     passing), and returns via a small "return register" + a dispatch tree.
 *
 * Usage: node outliner.js <in.prg.txt> [out.prg.txt]
 */
'use strict';
const fs = require('fs');

const RET_BASE = 8000; // reserved bits for the return register (must be unused)
const MIN_BODY = 2;    // minimum body size in instructions

// ---------- parsing ----------
function parse(text) {
  const items = [];
  let ignore = false;
  for (const raw of text.split('\n')) {
    const t = raw.trim();
    if (t === '#begin:') { ignore = true; continue; }
    if (t === '#end:') { ignore = false; continue; }
    if (ignore) continue;
    const line = raw.split('#')[0].trim();
    if (!line) continue;
    const p = line.split(/\s+/);
    if (p[0] === 'l') items.push({ t: 'label', name: p[1] });
    else if (p[0] === 'm') items.push({ t: 'ins', op: 'm', dst: p[1], src: p[2] });
    else if (p[0] === 'j') items.push({ t: 'ins', op: 'j', args: p.slice(1) });
    else throw new Error('unrecognized line: ' + line);
  }
  return items;
}

function build(items) {
  const ins = [], labelsAt = [];
  const labelPos = new Map();
  let pending = [];
  for (const it of items) {
    if (it.t === 'label') { pending.push(it.name); continue; }
    labelsAt[ins.length] = pending.slice();
    for (const L of pending) labelPos.set(L, ins.length);
    pending = [];
    ins.push(it);
  }
  labelsAt[ins.length] = pending.slice();
  for (const L of pending) labelPos.set(L, ins.length);

  const refMap = new Map();
  for (let k = 0; k < ins.length; k++) {
    if (ins[k].op !== 'j') continue;
    for (const a of ins[k].args) {
      if (a === 'next') continue;
      if (labelPos.has(a)) {
        if (!refMap.has(a)) refMap.set(a, []);
        refMap.get(a).push(k);
      }
    }
  }
  return { ins, labelsAt, labelPos, refMap };
}

const isNum = s => /^-?\d+$/.test(s);
// jump targets: for `j <label>` it's args[0]; for `j <cond> <l1>` and
// `j <cond> <l0> <l1>` the condition is args[0] and targets are the rest.
const jTargets = it => it.args.length === 1 ? it.args : it.args.slice(1);

// fragment [i,j] is extractable iff: no jump out (only 'next'), no numeric
// targets, and no label inside is referenced from outside (fall-through only).
function selfContained(i, j, c) {
  for (let k = i; k <= j; k++) {
    if (c.ins[k].op !== 'j') continue;
    for (const a of jTargets(c.ins[k])) {
      if (a === 'next') continue;
      if (isNum(a)) return false;
      const p = c.labelPos.get(a);
      if (p === undefined || p < i || p > j + 1) return false;
    }
  }
  for (let k = i + 1; k <= j + 1; k++)
    for (const L of (c.labelsAt[k] || []))
      for (const r of (c.refMap.get(L) || []))
        if (r < i || r > j) return false;
  return true;
}

// canonical signature: internal labels -> ordinals, exit labels -> EXIT,
// addresses kept as-is.
function canonical(i, j, c) {
  const ord = new Map(); let n = 0;
  const exit = new Set(c.labelsAt[j + 1] || []);
  for (let k = i + 1; k <= j; k++)
    for (const L of (c.labelsAt[k] || [])) if (!ord.has(L)) ord.set(L, n++);
  const parts = [];
  for (let k = i; k <= j; k++) {
    const it = c.ins[k];
    if (it.op === 'm') parts.push('M:' + it.dst + ':' + it.src);
    else {
      const cond = it.args.length >= 2 ? it.args[0] : '';
      const t = jTargets(it).map(a => a === 'next' ? 'NEXT' : (exit.has(a) ? 'EXIT' : 'L' + ord.get(a))).join(':');
      parts.push('J:' + cond + ':' + t);
    }
  }
  return parts.join('|');
}

function findGroups(c) {
  const groups = new Map();
  const n = c.ins.length;
  for (let i = 0; i < n; i++)
    for (let j = i; j < n; j++) {
      if (j - i + 1 < MIN_BODY) continue;
      if (!selfContained(i, j, c)) continue;
      const s = canonical(i, j, c);
      if (!groups.has(s)) groups.set(s, []);
      groups.get(s).push({ i, j });
    }
  return groups;
}

function nonOverlapping(occs) {
  occs = occs.slice().sort((a, b) => a.i - b.i);
  const out = [];
  for (const o of occs) if (!out.length || o.i > out[out.length - 1].j) out.push(o);
  return out;
}

function pickBest(groups) {
  let best = null;
  for (const [, occs] of groups) {
    const sel = nonOverlapping(occs);
    if (sel.length < 2) continue;
    const S = sel[0].j - sel[0].i + 1;
    const N = sel.length;
    const k = Math.ceil(Math.log2(N));
    const savings = (N - 1) * S - N * (k + 1) - (N - 1);
    if (savings > 0 && (!best || savings > best.savings)) best = { occs: sel, S, N, k, savings };
  }
  return best;
}

function render(it) {
  return it.op === 'm' ? `m ${it.dst} ${it.src}` : `j ${it.args.join(' ')}`;
}

function dispatch(out, bitIdx, idxs, cont, dc) {
  if (idxs.length === 1) return; // leaf reached directly by parent's jump
  const zero = idxs.filter(x => ((x >> bitIdx) & 1) === 0);
  const one = idxs.filter(x => ((x >> bitIdx) & 1) === 1);
  const zl = `__sub0_d${dc.n++}`;
  const ol = `__sub0_d${dc.n++}`;
  const l0 = zero.length === 1 ? cont(zero[0]) : zl;
  const l1 = one.length === 1 ? cont(one[0]) : ol;
  out.push(`j ${RET_BASE + bitIdx} ${l0} ${l1}`);
  if (zero.length > 1) { out.push(`l ${zl}`); dispatch(out, bitIdx + 1, zero, cont, dc); }
  if (one.length > 1) { out.push(`l ${ol}`); dispatch(out, bitIdx + 1, one, cont, dc); }
}

function rewrite(c, best) {
  const { ins, labelsAt } = c;
  const occs = best.occs, N = occs.length, k = best.k;
  const entry = '__sub0';
  const cont = idx => `__sub0_ret${idx}`;
  const occMap = new Map();
  occs.forEach((o, idx) => { for (let kk = o.i; kk <= o.j; kk++) occMap.set(kk, idx); });
  const exitAll = new Set();
  for (const o of occs) for (const L of (labelsAt[o.j + 1] || [])) exitAll.add(L);

  const out = [];
  let pos = 0;
  while (pos < ins.length) {
    if (occMap.has(pos)) {
      const idx = occMap.get(pos);
      for (const L of (labelsAt[pos] || [])) if (!exitAll.has(L)) out.push(`l ${L}`);
      for (let b = 0; b < k; b++) out.push(`m ${RET_BASE + b} ${(idx >> b) & 1}`);
      out.push(`j ${entry}`);
      out.push(`l ${cont(idx)}`);
      pos = occs[idx].j + 1;
    } else {
      for (const L of (labelsAt[pos] || [])) if (!exitAll.has(L)) out.push(`l ${L}`);
      out.push(render(ins[pos]));
      pos++;
    }
  }

  // terminate the main flow so it does not fall through into the subroutine
  out.push('j end');

  // shared subroutine body (internal labels renamed) + return dispatch
  out.push(`l ${entry}`);
  const o0 = occs[0];
  const exit0 = new Set(labelsAt[o0.j + 1] || []);
  const ord = new Map(); let n = 0;
  for (let kk = o0.i + 1; kk <= o0.j; kk++)
    for (const L of (labelsAt[kk] || [])) if (!ord.has(L)) ord.set(L, n++);
  const rename = a => a === 'next' ? 'next' : (exit0.has(a) ? '__sub0_exit' : `__sub0_l${ord.get(a)}`);
  for (let kk = o0.i; kk <= o0.j; kk++) {
    if (kk > o0.i) for (const L of (labelsAt[kk] || [])) out.push(`l __sub0_l${ord.get(L)}`);
    const it = ins[kk];
    if (it.op === 'm') out.push(`m ${it.dst} ${it.src}`);
    else if (it.args.length === 1) out.push(`j ${rename(it.args[0])}`);
    else out.push(`j ${it.args[0]} ${it.args.slice(1).map(rename).join(' ')}`);
  }
  out.push('l __sub0_exit');
  dispatch(out, 0, Array.from({ length: N }, (_, x) => x), cont, { n: 0 });

  // trailing labels stay at the very end
  for (const L of (labelsAt[ins.length] || [])) out.push(`l ${L}`);

  return out.join('\n') + '\n';
}

function main() {
  const [inPath, outPath] = process.argv.slice(2);
  if (!inPath) { console.error('usage: node outliner.js <in.prg.txt> [out.prg.txt]'); process.exit(2); }
  const text = fs.readFileSync(inPath, 'utf8');
  const c = build(parse(text));
  const before = c.ins.length;
  const best = pickBest(findGroups(c));
  const target = outPath || inPath.replace(/\.prg\.txt$/, '.outlined.prg.txt');

  if (!best) {
    console.log(`no profitable fragment (${before} instructions) — output unchanged`);
    fs.writeFileSync(target, text);
    return;
  }

  const result = rewrite(c, best);
  const after = result.split('\n').filter(l => l.trim().startsWith('m ') || l.trim().startsWith('j ')).length;
  console.log(`extracted body      : ${best.S} instructions x ${best.N} occurrences`);
  console.log(`return register     : ${best.k} bit(s) @ addresses ${RET_BASE}..${RET_BASE + best.k - 1}`);
  console.log(`instructions        : ${before} -> ${after} (saved ${before - after})`);
  fs.writeFileSync(target, result);
  console.log(`wrote               : ${target}`);
}

if (require.main === module) main();
module.exports = { parse, build, selfContained, canonical, findGroups, pickBest };

