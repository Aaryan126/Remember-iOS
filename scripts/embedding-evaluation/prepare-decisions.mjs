import { createHash } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, realpathSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const options = {};
for (let i = 2; i < process.argv.length; i += 2) {
  const key = process.argv[i]?.slice(2);
  if (!['inputs', 'freeze', 'grdb', 'mode', 'split', 'derived-data'].includes(key) || !process.argv[i + 1]) throw Error('Invalid option');
  options[key] = process.argv[i + 1];
}
if (!options.inputs || !options.freeze || !options.grdb) throw Error('Use --inputs decisions/inputs.json --freeze decisions/freeze.json --grdb /existing/GRDB.swift');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const inputBytes = readFileSync(options.inputs), frozenBytes = readFileSync(options.freeze);
const freeze = JSON.parse(frozenBytes);
if (freeze.inputsSHA256 !== hash(inputBytes)) throw Error('Decision input hash differs from freeze');
for (const [key, name] of [['scorerSHA256', 'score-decisions.mjs'], ['contractSHA256', 'DECISIONS.md'], ['probeSHA256', 'OrganizationDecisionProbe.swift']]) {
  if (freeze[key] !== hash(readFileSync(new URL(`./${name}`, import.meta.url)))) throw Error(`Frozen ${key} mismatch`);
}
const data = JSON.parse(inputBytes);
if (data.schemaVersion !== 1 || !Array.isArray(data.cases)) throw Error('Invalid decision schema');
const mode = options.mode ?? 'both', split = options.split ?? 'all';
if (!['embedding', 'local', 'both'].includes(mode) || !['development', 'heldout', 'all'].includes(split)) throw Error('Invalid mode/split');
const seen = new Set();
const cases = data.cases.filter(row => split === 'all' || row.split === split).map(row => {
  if (typeof row.id !== 'string' || !/^[a-zA-Z0-9_-]+$/.test(row.id) || seen.has(row.id) || typeof row.libraryID !== 'string') throw Error('Invalid/duplicate case ID');
  seen.add(row.id);
  if (!['development', 'heldout'].includes(row.split)) throw Error('Invalid split');
  const ids = new Set();
  const items = row.items.map(item => {
    if (typeof item.id !== 'string' || !/^[a-zA-Z0-9_-]+$/.test(item.id) || ids.has(item.id) || typeof item.text !== 'string' || !Number.isFinite(item.timestamp)) throw Error('Invalid item');
    ids.add(item.id); return { id: item.id, text: item.text, timestamp: item.timestamp };
  });
  if (items.length !== 4 || Object.keys(row.initialMemberships).length !== 4) throw Error('Each case needs four seeded sources');
  const initialMemberships = Object.fromEntries(items.map(item => {
    const groups = row.initialMemberships[item.id];
    if (!Array.isArray(groups) || groups.length !== 1 || !['seed01', 'seed02'].includes(groups[0])) throw Error('Invalid initial state');
    return [item.id, groups];
  }));
  return { id: row.id, libraryID: row.libraryID, split: row.split, items, initialMemberships };
});
if (!cases.length) throw Error('No selected cases');
const scriptRoot = dirname(fileURLToPath(import.meta.url)), repoRoot = resolve(scriptRoot, '../..');
const grdb = realpathSync(options.grdb);
if (!existsSync(join(grdb, 'Package.swift'))) throw Error('GRDB package missing');
const team = readFileSync(join(repoRoot, 'Remember/Remember.xcodeproj/project.pbxproj'), 'utf8').match(/DEVELOPMENT_TEAM = ([A-Z0-9]+);/)?.[1];
if (!team) throw Error('Signing team missing');
const sourceHashes = {};
function sources(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    if (entry.name === '.git') continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) sources(path);
    else if (entry.name.endsWith('.swift')) sourceHashes[path.slice(repoRoot.length + 1)] = hash(readFileSync(path));
  }
}
sources(join(repoRoot, 'Remember/Remember')); sources(join(repoRoot, 'Remember/Shared'));
sourceHashes['scripts/embedding-evaluation/OrganizationDecisionProbe.swift'] = hash(readFileSync(join(scriptRoot, 'OrganizationDecisionProbe.swift')));
const modes = mode === 'both' ? ['embedding', 'local'] : [mode];
const config = { schemaVersion: 1, cases, modes, timeoutSeconds: 600,
  manifest: { inputsSHA256: hash(inputBytes), freezeSHA256: hash(frozenBytes), sourceHashes, cloudEnabled: false,
    expectedRunIDs: cases.flatMap(row => modes.map(mode => `${row.id}-${mode}`)),
    interpretation: 'Controlled seeded-state diagnostic; initial memberships are inputs, expected decisions remain host-only' } };
config.manifest.configurationSHA256 = hash(JSON.stringify(config));
const output = mkdtempSync(join(tmpdir(), 'RememberOrganizationDecisionProbe-'));
mkdirSync(join(output, 'Sources')); mkdirSync(join(output, 'OrganizationDecisionProbe.xcodeproj'));
copyFileSync(join(scriptRoot, 'OrganizationDecisionProbe.swift'), join(output, 'Sources/OrganizationDecisionProbe.swift'));
writeFileSync(join(output, 'Sources/DecisionConfiguration.swift'), `import Foundation\nnonisolated enum DecisionConfiguration { static let data = Data(base64Encoded: "${Buffer.from(JSON.stringify(config)).toString('base64')}")! }\n`);
const escape = path => JSON.stringify(path).slice(1, -1);
const project = readFileSync(join(scriptRoot, 'project.pbxproj.template'), 'utf8').replaceAll('__REPO_ROOT__', escape(repoRoot))
  .replaceAll('__GRDB_ROOT__', escape(grdb)).replaceAll('__DEVELOPMENT_TEAM__', team).replaceAll('EmbeddingProbe', 'OrganizationDecisionProbe')
  .replace('Embedding Probe', 'Decision Benchmark');
writeFileSync(join(output, 'OrganizationDecisionProbe.xcodeproj/project.pbxproj'), project);
writeFileSync(join(output, 'configuration.json'), JSON.stringify(config, null, 2));
const derivedData = options['derived-data'] ? resolve(options['derived-data']) : join(output, 'build');
console.log(JSON.stringify({ project: join(output, 'OrganizationDecisionProbe.xcodeproj'), configuration: join(output, 'configuration.json'), derivedData,
  app: join(derivedData, 'Build/Products/Debug-iphoneos/OrganizationDecisionProbe.app'), bundleIdentifier: 'SimpleStudio.Remember.OrganizationDecisionProbe',
  results: `Documents/decisions-${config.manifest.configurationSHA256}.json` }, null, 2));
