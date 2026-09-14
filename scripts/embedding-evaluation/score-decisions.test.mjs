import assert from 'node:assert/strict';
import test from 'node:test';
import { scoreDecisionCases } from './score-decisions.mjs';

function fixture() {
  const ids = ['a', 'b', 'c', 'd'];
  const memberships = Object.fromEntries(ids.map(id => [id, ['all']]));
  const mergeInitial = { a: ['left'], b: ['left'], c: ['right'], d: ['right'] };
  const inputs = { schemaVersion: 1, cases: ['case01', 'case02'].map(id => ({ id, items: ids.map(id => ({ id })),
    initialMemberships: id === 'case01' ? mergeInitial : memberships })) };
  const labels = { schemaVersion: 1, cases: [{ id: 'case01', kind: 'merge', expectedGroups: [ids] },
    { id: 'case02', kind: 'split', expectedGroups: [['a', 'b'], ['c', 'd']], acceptableProposals: [['a', 'b'], ['c', 'd']] }] };
  const results = { schemaVersion: 1, manifest: { expectedRunIDs: ['case01-embedding', 'case02-embedding'] }, runs: [
    { runID: 'case01-embedding', status: 'completed', memberships, initialMemberships: mergeInitial,
      initialPinnedCount: 0, citationsValid: true,
      availability: { unavailableEmbeddingIDs: [] }, events: [{ kind: 'merge', assignments: memberships }] },
    { runID: 'case02-embedding', status: 'completed', memberships, initialMemberships: memberships, availability: { unavailableEmbeddingIDs: [] },
      initialPinnedCount: 0, citationsValid: true,
      events: [{ kind: 'splitProposal', assignments: { a: ['new'], b: ['new'] } }] }] };
  return { inputs, labels, results };
}
test('correct merge and either complementary split score exactly', () => {
  const f = fixture(); const result = scoreDecisionCases(f.inputs, f.labels, f.results);
  assert.equal(result.modes.embedding.merge.opportunityRecall, 1);
  assert.equal(result.modes.embedding.split.opportunityRecall, 1);
  f.results.runs[1].events[0].assignments = { c: ['new'], d: ['new'] };
  assert.equal(scoreDecisionCases(f.inputs, f.labels, f.results).modes.embedding.split.eventPrecision, 1);
});
test('missing and unavailable opportunities stay in denominator', () => {
  const f = fixture(); f.results.runs = [];
  const score = scoreDecisionCases(f.inputs, f.labels, f.results);
  assert.equal(score.modes.embedding.merge.opportunityRecall, 0);
  assert.equal(score.modes.embedding.merge.eventPrecision, null);
  assert.equal(score.modes.embedding.split.completed, 0);
});
test('bad split and unintended automatic rewrite both fail', () => {
  const f = fixture(); f.results.runs[1].events[0].assignments = { a: ['new'], c: ['new'] };
  assert.equal(scoreDecisionCases(f.inputs, f.labels, f.results).modes.embedding.split.eventPrecision, 0);
  f.results.runs[1].events[0].assignments = { a: ['new'], b: ['new'] };
  f.results.runs[1].memberships = { a: ['new'], b: ['new'], c: ['all'], d: ['all'] };
  const score = scoreDecisionCases(f.inputs, f.labels, f.results).modes.embedding.split;
  assert.equal(score.opportunityRecall, 0);
  assert.equal(score.unexpectedMembershipChanges, 1);
});
test('retaining correct partition without an observed merge is not merge recall', () => {
  const f = fixture(); f.results.runs[0].events = [];
  assert.equal(scoreDecisionCases(f.inputs, f.labels, f.results).modes.embedding.merge.opportunityRecall, 0);
});
test('duplicate runs and unexpected source assignments fail validation', () => {
  const f = fixture(); f.results.runs.push(f.results.runs[0]);
  assert.throws(() => scoreDecisionCases(f.inputs, f.labels, f.results));
  f.results.runs.pop(); f.results.runs[0].events[0].assignments = { unknown: ['all'] };
  assert.throws(() => scoreDecisionCases(f.inputs, f.labels, f.results));
});
test('invalid seed state cannot manufacture a successful opportunity', () => {
  const f = fixture(); f.results.runs[0].initialMemberships = f.results.runs[0].memberships;
  assert.throws(() => scoreDecisionCases(f.inputs, f.labels, f.results), /seed state/);
});
test('broken citations are a failure even when partition is correct', () => {
  const f = fixture(); f.results.runs[0].citationsValid = false;
  const scored = scoreDecisionCases(f.inputs, f.labels, f.results).modes.embedding.merge;
  assert.equal(scored.successful, 0); assert.equal(scored.citationFailures, 1);
});
