#!/usr/bin/env node
/**
 * peephole.js — the start of the copy-jump rewrite taxonomy (local, semantics-
 * preserving peephole optimizations). Rules:
 *
 *   R1  self-copy elimination : `m x x` (numeric dst == src) is a no-op.
 *   R2  jump-to-next          : `j L` immediately followed by `l L` is a no-op.
 *
 * Usage: node peephole.js <in.prg.txt> [out.prg.txt]
 */
'use strict';
const fs = require('fs');

const isNum = s => /^-?\d+$/.test(s);

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
    else throw new Error('unrecognized: ' + line);
  }
  return items;
}

function render(it) {
  return it.t === 'label' ? `l ${it.name}`
    : it.op === 'm' ? `m ${it.dst} ${it.src}`
    : `j ${it.args.join(' ')}`;
}

function pass(items) {
  const out = [];
  let changed = false;
  let i = 0;
  while (i < items.length) {
    const it = items[i];
    if (it.t === 'ins' && it.op === 'm' && isNum(it.dst) && it.dst === it.src) {
      changed = true; i++; continue;               // R1
    }
    if (it.t === 'ins' && it.op === 'j' && it.args.length === 1 &&
        i + 1 < items.length && items[i + 1].t === 'label' && items[i + 1].name === it.args[0]) {
      changed = true; i++; continue;               // R2 (drop jump, keep label)
    }
    out.push(it);
    i++;
  }
  return { items: out, changed };
}

function countInstr(items) { return items.filter(x => x.t === 'ins').length; }

function main() {
  const [inPath, outPath] = process.argv.slice(2);
  if (!inPath) { console.error('usage: node peephole.js <in.prg.txt> [out.prg.txt]'); process.exit(2); }
  let items = parse(fs.readFileSync(inPath, 'utf8'));
  const before = countInstr(items);
  let iters = 0;
  while (iters++ < 1000) {
    const r = pass(items);
    if (!r.changed) break;
    items = r.items;
  }
  const after = countInstr(items);
  const target = outPath || inPath.replace(/\.prg\.txt$/, '.peephole.prg.txt');
  fs.writeFileSync(target, items.map(render).join('\n') + '\n');
  console.log(`peephole: ${before} -> ${after} instructions (saved ${before - after}, ${iters - 1} pass(es))`);
  console.log(`wrote: ${target}`);
}

if (require.main === module) main();
module.exports = { parse, pass, countInstr };
