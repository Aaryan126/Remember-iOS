import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const canonicalSet = ids => [...ids].sort().join('\u0000');
function partition(memberships, ids) {
  if (!memberships || canonicalSet(Object.keys(memberships)) !== canonicalSet(ids)) throw Error('Missing/extra prediction IDs');
  const groups = new Map();
  for (const [id, memberships_] of Object.entries(memberships)) {
    if (!Array.isArray(memberships_) || !memberships_.length || memberships_.some(g => typeof g !== 'string')) throw Error('Invalid prediction memberships');
    for (const group of memberships_) { const members = groups.get(group) ?? []; members.push(id); groups.set(group, members); }
  }
  return [...groups.values()].map(canonicalSet).sort().join('\u0001');
}
function sameAssignments(a, b, ids) {
  return ids.every(id => a?.[id] && b?.[id] && canonicalSet(a[id]) === canonicalSet(b[id]));
}
export function scoreDecisionCases(inputs, labels, results) {
  if (inputs.schemaVersion !== 1 || labels.schemaVersion !== 1 || results.schemaVersion !== 1) throw Error('Unsupported schema');
  const expectedRunIDs = results.manifest?.expectedRunIDs;
  if (!Array.isArray(expectedRunIDs) || !expectedRunIDs.length || new Set(expectedRunIDs).size !== expectedRunIDs.length) throw Error('Expected run coverage required');
  const modes = [...new Set(expectedRunIDs.map(id => id.endsWith('-embedding') ? 'embedding' : id.endsWith('-local') ? 'local' : 'invalid'))];
  if (modes.includes('invalid')) throw Error('Invalid mode');
  const runs = new Map();
  for (const run of results.runs) {
    if (!expectedRunIDs.includes(run.runID) || runs.has(run.runID)) throw Error('Duplicate/unexpected run');
    runs.set(run.runID, run);
  }
  const output = { schemaVersion: 1, interpretation: 'Controlled seeded-state operational diagnostic; not natural arrival-history accuracy', modes: {}, cases: [] };
  for (const mode of modes) {
    const stats = { merge: { opportunities: 0, completed: 0, modelAvailable: 0, successful: 0, observedEvents: 0, correctEvents: 0, citationFailures: 0 },
      split: { opportunities: 0, completed: 0, modelAvailable: 0, successful: 0, observedEvents: 0, correctEvents: 0, citationFailures: 0, unexpectedMembershipChanges: 0 } };
    for (const input of inputs.cases) {
      const runID = `${input.id}-${mode}`;
      if (!expectedRunIDs.includes(runID)) continue;
      const label = labels.cases.find(row => row.id === input.id);
      if (!label || !['merge', 'split'].includes(label.kind)) throw Error('Missing/invalid labels');
      const stat = stats[label.kind]; stat.opportunities += 1;
      const run = runs.get(runID), ids = input.items.map(item => item.id);
      let success = false, correctEvents = 0, observedEvents = 0, preserved = null;
      if (run?.status === 'completed') {
        if (partition(run.initialMemberships, ids) !== partition(input.initialMemberships, ids)) throw Error('Observed seed state differs from frozen input');
        if (run.initialPinnedCount !== 0 || typeof run.citationsValid !== 'boolean') throw Error('Missing/invalid seed or citation integrity record');
        if (!run.citationsValid) stat.citationFailures += 1;
        stat.completed += 1;
        if (Array.isArray(run.availability?.unavailableEmbeddingIDs) && run.availability.unavailableEmbeddingIDs.length === 0) stat.modelAvailable += 1;
        const finalPartition = partition(run.memberships, ids);
        const actual = (run.events ?? []).filter(event => event.kind === (label.kind === 'merge' ? 'merge' : 'splitProposal'));
        observedEvents = actual.length;
        for (const event of actual) {
          const assigned = Object.keys(event.assignments ?? {});
          if (assigned.some(id => !ids.includes(id))) throw Error('Event references unexpected source');
          if (label.kind === 'merge') {
            if (assigned.length >= 2 && label.expectedGroups.some(group => assigned.every(id => group.includes(id)))) correctEvents += 1;
          } else if (label.acceptableProposals.some(group => canonicalSet(group) === canonicalSet(assigned))) correctEvents += 1;
        }
        if (label.kind === 'merge') {
          const expectedPartition = label.expectedGroups.map(canonicalSet).sort().join('\u0001');
          success = finalPartition === expectedPartition && actual.length > 0 && correctEvents === actual.length;
        } else {
          partition(run.initialMemberships, ids);
          preserved = sameAssignments(run.initialMemberships, run.memberships, ids);
          if (!preserved) stat.unexpectedMembershipChanges += 1;
          success = preserved && actual.length > 0 && correctEvents === actual.length;
        }
        success = success && run.citationsValid;
      }
      stat.observedEvents += observedEvents; stat.correctEvents += correctEvents;
      if (success) stat.successful += 1;
      output.cases.push({ runID, kind: label.kind, status: run?.status ?? 'missing', success, observedEvents, correctEvents, preserved });
    }
    for (const stat of Object.values(stats)) {
      stat.opportunityRecall = stat.opportunities ? stat.successful / stat.opportunities : null;
      stat.eventPrecision = stat.observedEvents ? stat.correctEvents / stat.observedEvents : null;
    }
    output.modes[mode] = stats;
  }
  return output;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const options = {};
  for (let i = 2; i < process.argv.length; i += 2) {
    const key = process.argv[i]?.slice(2);
    if (!['inputs', 'labels', 'freeze', 'results'].includes(key) || !process.argv[i + 1]) throw Error('Use --inputs --labels --freeze --results');
    options[key] = process.argv[i + 1];
  }
  if (Object.keys(options).length !== 4) throw Error('Use --inputs --labels --freeze --results');
  const bytes = readFileSync(options.inputs), labelBytes = readFileSync(options.labels), frozenBytes = readFileSync(options.freeze);
  const hash = data => createHash('sha256').update(data).digest('hex');
  const frozen = JSON.parse(frozenBytes), results = JSON.parse(readFileSync(options.results));
  if (frozen.scorerSHA256 !== hash(readFileSync(new URL(import.meta.url)))
      || frozen.contractSHA256 !== hash(readFileSync(new URL('./DECISIONS.md', import.meta.url)))
      || frozen.probeSHA256 !== results.manifest?.sourceHashes?.['scripts/embedding-evaluation/OrganizationDecisionProbe.swift']) throw Error('Frozen scorer/contract/probe hashes mismatch');
  if (frozen.inputsSHA256 !== hash(bytes) || frozen.labelsSHA256 !== hash(labelBytes) || results.manifest?.inputsSHA256 !== hash(bytes)
      || results.manifest?.freezeSHA256 !== hash(frozenBytes)) throw Error('Frozen input/label/result hashes mismatch');
  console.log(JSON.stringify(scoreDecisionCases(JSON.parse(bytes), JSON.parse(labelBytes), results), null, 2));
}
