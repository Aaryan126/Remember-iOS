import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const script = join(dirname(fileURLToPath(import.meta.url)), 'prepare-organization.mjs');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
function fixture(t, split = 'development') {
  const root = mkdtempSync(join(tmpdir(), 'OrganizationPrepareTest-'));
  t.after(() => rmSync(root, { recursive: true }));
  writeFileSync(join(root, 'Package.swift'), '// Fake existing package for preparation tests; never built.');
  const inputs = { schemaVersion: 1, labels: { hidden: 'DO_NOT_SHIP' }, libraries: [{ id: 'l1', split, slice: 'english',
    reviewerNotes: 'DO_NOT_SHIP', items: [{ id: 'i1', kind: 'text', text: 'A fictional appointment.', timestamp: 1800000000, goldThread: 'DO_NOT_SHIP' }] }] };
  const path = join(root, 'inputs.json');
  return { root, inputs, path, run(extra = []) {
    writeFileSync(path, JSON.stringify(inputs));
    const result = spawnSync(process.execPath, [script, '--inputs', path, '--grdb', root, ...extra], { encoding: 'utf8' });
    if (result.status === 0) {
      const generated = JSON.parse(result.stdout);
      t.after(() => rmSync(dirname(generated.project), { recursive: true }));
      result.config = JSON.parse(readFileSync(generated.configuration));
      result.generated = generated;
    }
    return result;
  } };
}
test('projects only input content and records expected run coverage', t => {
  const f = fixture(t); const result = f.run();
  assert.equal(result.status, 0, result.stderr);
  assert.equal(JSON.stringify(result.config).includes('DO_NOT_SHIP'), false);
  assert.equal(result.config.manifest.expectedRunIDs.length, 12);
  assert.equal(result.config.manifest.cloudEnabled, false);
  assert.equal(result.config.libraries[0].items[0].text, 'A fictional appointment.');
});
test('held-out preparation requires the exact frozen input bytes', t => {
  const f = fixture(t, 'heldout');
  assert.notEqual(f.run(['--split', 'heldout']).status, 0);
  const freeze = join(f.root, 'freeze.json');
  writeFileSync(freeze, JSON.stringify({ inputsSHA256: 'wrong' }));
  assert.notEqual(f.run(['--split', 'heldout', '--freeze', freeze]).status, 0);
  writeFileSync(freeze, JSON.stringify({ inputsSHA256: sha(JSON.stringify(f.inputs)) }));
  assert.equal(f.run(['--split', 'heldout', '--freeze', freeze]).status, 0);
});
test('public diagnostics accept their independent frozen input', t => {
  const f = fixture(t, 'public'); f.inputs.libraries[0].slice = 'public';
  const freeze = join(f.root, 'freeze.json');
  writeFileSync(freeze, JSON.stringify({ inputsSHA256: sha(JSON.stringify(f.inputs)) }));
  assert.equal(f.run(['--split', 'all', '--freeze', freeze]).status, 0);
});
test('rejects duplicate item IDs and invalid interleavings', t => {
  const f = fixture(t); f.inputs.libraries[0].items.push({ ...f.inputs.libraries[0].items[0] });
  assert.notEqual(f.run().status, 0);
  f.inputs.libraries[0].items.pop(); f.inputs.libraries[0].orders = { interleaved: ['unknown'] };
  assert.notEqual(f.run().status, 0);
});
test('rejects unsupported options and unbounded timeout', t => {
  const f = fixture(t);
  assert.notEqual(f.run(['--timeout', '601']).status, 0);
  assert.notEqual(f.run(['--whatever', 'value']).status, 0);
});
test('media hashes bind actual assets and prevent path escape', t => {
  const f = fixture(t); writeFileSync(join(f.root, 'sample.png'), 'synthetic test bytes');
  f.inputs.libraries[0].items[0] = { id: 'i1', kind: 'image', timestamp: 1800000000,
    assetPath: 'sample.png', referenceText: 'Reference fixture', assetSHA256: 'wrong' };
  assert.notEqual(f.run().status, 0);
  f.inputs.libraries[0].items[0].assetSHA256 = sha('synthetic test bytes');
  assert.equal(f.run().status, 0);
  f.inputs.libraries[0].items[0].assetPath = '/etc/hosts';
  assert.notEqual(f.run().status, 0);
});
