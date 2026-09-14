import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const scripts = dirname(fileURLToPath(import.meta.url));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
function setup(t) {
  const root = mkdtempSync(join(tmpdir(), 'DecisionDerivationTest-'));
  t.after(() => rmSync(root, { recursive: true }));
  const input = { schemaVersion: 1, libraries: [] }, labels = { schemaVersion: 1, libraries: [] };
  for (let l = 1; l <= 12; l += 1) {
    const id = `l${String(l).padStart(2, '0')}`, memberships = {};
    const items = Array.from({ length: 8 }, (_, i) => {
      const sourceID = `${id}-i${i}`;
      memberships[sourceID] = [i < 4 ? 'SECRET_ALPHA' : 'SECRET_BETA'];
      return { id: sourceID, kind: 'text', text: `Fictional source ${i} in library ${l}`, timestamp: 1800000000 + i };
    });
    input.libraries.push({ id, split: l <= 6 ? 'development' : 'heldout', slice: 'english', items });
    labels.libraries.push({ id, memberships, ambiguous: [] });
  }
  const paths = { inputs: join(root, 'core-inputs.json'), labels: join(root, 'core-labels.json'), freeze: join(root, 'core-freeze.json'), output: join(root, 'derived') };
  writeFileSync(paths.inputs, JSON.stringify(input)); writeFileSync(paths.labels, JSON.stringify(labels));
  writeFileSync(paths.freeze, JSON.stringify({ inputsSHA256: hash(readFileSync(paths.inputs)), labelsSHA256: hash(readFileSync(paths.labels)) }));
  function derive() { return spawnSync(process.execPath, [join(scripts, 'derive-decisions.mjs'), ...Object.entries(paths).flatMap(([key, path]) => [`--${key}`, path])], { encoding: 'utf8' }); }
  return { root, paths, derive };
}
test('derives exactly 12 merge and 12 split opportunities without gold labels on device', t => {
  const fixture = setup(t); const result = fixture.derive(); assert.equal(result.status, 0, result.stderr);
  const inputs = JSON.parse(readFileSync(join(fixture.paths.output, 'inputs.json')));
  const labels = JSON.parse(readFileSync(join(fixture.paths.output, 'labels.json')));
  assert.equal(inputs.cases.length, 24);
  assert.equal(labels.cases.filter(row => row.kind === 'merge').length, 12);
  assert.equal(labels.cases.filter(row => row.kind === 'split').length, 12);
  assert.equal(JSON.stringify(inputs).includes('SECRET_'), false);
  assert.equal(inputs.cases.some(row => 'kind' in row), false);
  assert.notEqual(fixture.derive().status, 0, 'must refuse overwriting frozen derived cases');
});
test('derivation fails if reviewed label bytes changed after freeze', t => {
  const fixture = setup(t); writeFileSync(fixture.paths.labels, readFileSync(fixture.paths.labels, 'utf8') + ' ');
  assert.notEqual(fixture.derive().status, 0);
});
test('preparation verifies the frozen scorer/contract/probe and excludes host-only labels', t => {
  const fixture = setup(t); assert.equal(fixture.derive().status, 0);
  writeFileSync(join(fixture.root, 'Package.swift'), '// Existing fake package for preparation-only test');
  const inputs = join(fixture.paths.output, 'inputs.json'), freeze = join(fixture.paths.output, 'freeze.json');
  const run = () => spawnSync(process.execPath, [join(scripts, 'prepare-decisions.mjs'), '--inputs', inputs, '--freeze', freeze, '--grdb', fixture.root], { encoding: 'utf8' });
  const result = run(); assert.equal(result.status, 0, result.stderr);
  const generated = JSON.parse(result.stdout); t.after(() => rmSync(dirname(generated.project), { recursive: true }));
  const config = JSON.parse(readFileSync(generated.configuration));
  assert.equal(config.manifest.expectedRunIDs.length, 48);
  assert.equal(JSON.stringify(config).includes('SECRET_'), false);
  const frozen = JSON.parse(readFileSync(freeze)); frozen.scorerSHA256 = 'tampered'; writeFileSync(freeze, JSON.stringify(frozen));
  assert.notEqual(run().status, 0);
});
