import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const options = {};
for (let i = 2; i < process.argv.length; i += 2) {
  const key = process.argv[i]?.slice(2);
  if (!['inputs', 'labels', 'freeze', 'output'].includes(key) || !process.argv[i + 1]) throw Error('Use --inputs --labels --freeze --output');
  options[key] = process.argv[i + 1];
}
if (Object.keys(options).length !== 4) throw Error('Use --inputs --labels --freeze --output');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const inputBytes = readFileSync(options.inputs), labelBytes = readFileSync(options.labels);
const freeze = JSON.parse(readFileSync(options.freeze));
if (freeze.inputsSHA256 !== hash(inputBytes) || freeze.labelsSHA256 !== hash(labelBytes)) throw Error('Core reviewed input and label hashes must match their freeze');
const inputs = JSON.parse(inputBytes), labels = JSON.parse(labelBytes);
if (inputs.schemaVersion !== 1 || labels.schemaVersion !== 1) throw Error('Unsupported schema');
const decisions = { schemaVersion: 1, cases: [] }, gold = { schemaVersion: 1, cases: [] };
for (const library of inputs.libraries) {
  const label = labels.libraries.find(row => row.id === library.id);
  if (!label) throw Error(`Missing reviewed labels for ${library.id}`);
  const ambiguous = new Set(label.ambiguous ?? []);
  const source = new Map(library.items.map(item => [item.id, item]));
  const groups = new Map();
  for (const [id, memberships] of Object.entries(label.memberships)) {
    if (memberships.length !== 1 || ambiguous.has(id)) continue;
    if (!source.has(id)) throw Error('Unknown source');
    const group = groups.get(memberships[0]) ?? [];
    group.push(id); groups.set(memberships[0], group);
  }
  const eligible = [...groups.values()].map(ids => ids.sort((a, b) => source.get(a).timestamp - source.get(b).timestamp || a.localeCompare(b)))
    .filter(ids => ids.length >= 2).sort((a, b) => a[0].localeCompare(b[0]));
  const mergeGroup = eligible.find(ids => ids.length >= 4);
  if (!mergeGroup || eligible.length < 2) throw Error(`Insufficient unambiguous evidence in ${library.id}`);
  for (const kind of ['merge', 'split']) {
    const ids = kind === 'merge' ? mergeGroup.slice(0, 4) : [...eligible[0].slice(0, 2), ...eligible[1].slice(0, 2)];
    const caseID = `case${String(decisions.cases.length + 1).padStart(2, '0')}`;
    const initialMemberships = Object.fromEntries(ids.map((id, index) => [id, [kind === 'merge' && index >= 2 ? 'seed02' : 'seed01']]));
    const expectedGroups = kind === 'merge' ? [ids] : [ids.slice(0, 2), ids.slice(2)];
    decisions.cases.push({ id: caseID, libraryID: library.id, split: library.split,
      items: ids.map(id => { const item = source.get(id); return { id, kind: 'text', text: item.text, timestamp: item.timestamp }; }), initialMemberships });
    gold.cases.push({ id: caseID, kind, expectedGroups, acceptableProposals: kind === 'split' ? expectedGroups : [],
      mustPreserveMemberships: kind === 'split', evidenceIDs: ids });
  }
}
if (decisions.cases.length !== 24) throw Error('Expected exactly 12 libraries / 24 controlled opportunities');
const output = resolve(options.output);
if (existsSync(output)) throw Error('Refusing to overwrite derived benchmark directory');
mkdirSync(output, { recursive: true });
const serializedInputs = JSON.stringify(decisions, null, 2) + '\n';
const serializedLabels = JSON.stringify(gold, null, 2) + '\n';
writeFileSync(join(output, 'inputs.json'), serializedInputs);
writeFileSync(join(output, 'labels.json'), serializedLabels);
writeFileSync(join(output, 'freeze.json'), JSON.stringify({ schemaVersion: 1, inputsSHA256: hash(serializedInputs), labelsSHA256: hash(serializedLabels),
  derivedFrom: { inputsSHA256: hash(inputBytes), labelsSHA256: hash(labelBytes), freezeSHA256: hash(readFileSync(options.freeze)) },
  derivationSHA256: hash(readFileSync(new URL(import.meta.url))),
  scorerSHA256: hash(readFileSync(new URL('./score-decisions.mjs', import.meta.url))),
  contractSHA256: hash(readFileSync(new URL('./DECISIONS.md', import.meta.url))),
  probeSHA256: hash(readFileSync(new URL('./OrganizationDecisionProbe.swift', import.meta.url))),
  interpretation: 'Controlled seeded-state operational diagnostic, not natural capture-history accuracy. No model predictions used to select cases.' }, null, 2) + '\n');
console.log(JSON.stringify({ output, cases: decisions.cases.length, merges: 12, splits: 12 }, null, 2));
