import assert from 'node:assert/strict';
import test from 'node:test';
import { mergeActiveCheckpoint } from './merge-organization-checkpoint.mjs';

function fixture() {
  const run = { runID: 'l1-embedding-chronological-0', attemptID: 'attempt1', status: 'running', libraryID: 'l1',
    mode: 'embedding', order: 'chronological', repeat: 0, split: 'development', slice: 'english', mediaMode: 'extracted',
    inputIDs: ['a', 'b'], completedInputCount: 0, memberships: {} };
  const primary = { schemaVersion: 1, manifest: { configurationSHA256: 'config1' }, runs: [run] };
  const active = { schemaVersion: 1, configurationSHA256: 'config1', run: { ...structuredClone(run), completedInputCount: 1, memberships: { a: ['topic'] } } };
  return { primary, active };
}
test('matching active attempt updates only running case without mutating archived primary', () => {
  const { primary, active } = fixture(), before = JSON.stringify(primary);
  const result = mergeActiveCheckpoint(primary, active);
  assert.equal(result.applied, true); assert.equal(result.report.runs[0].completedInputCount, 1);
  assert.equal(JSON.stringify(primary), before);
  result.report.runs[0].memberships.a.push('other'); assert.deepEqual(active.run.memberships.a, ['topic']);
});
test('wrong config, stale attempt, and old progress preserve primary', () => {
  for (const modify of [f => { f.active.configurationSHA256 = 'other'; }, f => { f.active.run.attemptID = 'old'; },
    f => { f.primary.runs[0].completedInputCount = 2; }]) {
    const f = fixture(); modify(f); const result = mergeActiveCheckpoint(f.primary, f.active);
    assert.equal(result.applied, false); assert.equal(result.report, f.primary);
  }
});
test('terminal primary or forged terminal checkpoint can never be overwritten', () => {
  for (const status of ['completed', 'error', 'blocked', 'timeout']) {
    const f = fixture(); f.primary.runs[0].status = status;
    assert.equal(mergeActiveCheckpoint(f.primary, f.active).applied, false);
  }
  const f = fixture(); f.active.run.status = 'completed'; assert.equal(mergeActiveCheckpoint(f.primary, f.active).applied, false);
});
test('bad run IDs, duplicate runs, changed inputs and unexpected memberships are rejected', () => {
  for (const modify of [f => { f.active.run.runID = 'other'; }, f => { f.primary.runs.push(f.primary.runs[0]); },
    f => { f.active.run.inputIDs.reverse(); }, f => { f.active.run.memberships.unknown = ['topic']; },
    f => { f.active.run.mode = 'local'; }]) {
    const f = fixture(); modify(f); assert.equal(mergeActiveCheckpoint(f.primary, f.active).applied, false);
  }
});
