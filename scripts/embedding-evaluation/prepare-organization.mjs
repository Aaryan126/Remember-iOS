import { createHash } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, realpathSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, extname, isAbsolute, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const args = process.argv.slice(2);
const options = {};
for (let i = 0; i < args.length; i += 2) {
  if (!args[i].startsWith('--') || !args[i + 1]) throw Error('Expected --name value pairs');
  const key = args[i].slice(2);
  if (!['inputs', 'grdb', 'split', 'mode', 'orders', 'freeze', 'libraries', 'max-runs', 'timeout', 'media', 'derived-data'].includes(key)) throw Error(`Unknown option: ${key}`);
  if (key in options) throw Error(`Duplicate option: ${key}`);
  options[key] = args[i + 1];
}
if (!options.inputs || !options.grdb) throw Error('Usage: node prepare-organization.mjs --inputs inputs.json --grdb /existing/GRDB.swift [--split development] [--mode both] [--freeze manifest.json]');
const hash = data => createHash('sha256').update(data).digest('hex');
const scriptRoot = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptRoot, '../..');
const bytes = readFileSync(options.inputs);
const inputsSHA256 = hash(bytes);
const input = JSON.parse(bytes);
if (input.schemaVersion !== 1 || !Array.isArray(input.libraries)) throw Error('Unsupported inputs schema');
const split = options.split ?? 'development';
const mode = options.mode ?? 'both';
const mediaMode = options.media ?? 'extracted';
if (!['extracted', 'reference'].includes(mediaMode)) throw Error('Invalid media mode');
if (!['development', 'heldout', 'public', 'all'].includes(split) || !['embedding', 'local', 'both'].includes(mode)) throw Error('Invalid split/mode');
let freezeSHA256 = null;
if (split !== 'development') {
  if (!options.freeze) throw Error('Held-out execution requires --freeze with a matching frozen input hash');
  const frozenBytes = readFileSync(options.freeze);
  const frozen = JSON.parse(frozenBytes);
  if (frozen.inputsSHA256 !== inputsSHA256) throw Error('Frozen input hash does not match');
  freezeSHA256 = hash(frozenBytes);
}
const orders = (options.orders ?? 'chronological,reverse,interleaved,seed17,seed29').split(',');
if (new Set(orders).size !== orders.length || orders.some(v => !['chronological', 'reverse', 'interleaved', 'seed17', 'seed29'].includes(v))) throw Error('Invalid orders');
const wanted = options.libraries?.split(',');
const seen = new Set();
const assets = new Map();
const libraries = input.libraries.filter(l => (split === 'all' || l.split === split) && (!wanted || wanted.includes(l.id))).map(l => {
  if (typeof l.id !== 'string' || !/^[a-zA-Z0-9_-]+$/.test(l.id) || seen.has(l.id)) throw Error('Invalid/duplicate library ID');
  seen.add(l.id);
  if (!['development', 'heldout', 'public'].includes(l.split) || !['english', 'multilingual', 'public', 'scale', 'media'].includes(l.slice)) throw Error('Invalid library split/slice');
  const ids = new Set();
  const items = l.items.map(item => {
    if (typeof item.id !== 'string' || !/^[a-zA-Z0-9_-]+$/.test(item.id) || ids.has(item.id)) throw Error('Invalid/duplicate item ID');
    ids.add(item.id);
    if (!['text', 'image', 'pdf', 'audio', 'video'].includes(item.kind) || !Number.isFinite(item.timestamp)) throw Error('Invalid input kind/timestamp');
    if (item.kind !== 'text') {
      if (typeof item.referenceText !== 'string' || typeof item.assetPath !== 'string' || isAbsolute(item.assetPath)) throw Error('Media requires referenceText and relative assetPath');
      const base = realpathSync(dirname(resolve(options.inputs)));
      const source = realpathSync(resolve(base, item.assetPath));
      if (relative(base, source).startsWith('..')) throw Error('Asset must be within the input directory');
      const assetBytes = readFileSync(source);
      if (typeof item.assetSHA256 !== 'string' || item.assetSHA256 !== hash(assetBytes)) throw Error('Media requires matching assetSHA256 frozen in inputs');
      const assetName = hash(assetBytes) + extname(source).toLowerCase();
      if (!['.png', '.jpg', '.jpeg', '.pdf', '.wav', '.aiff', '.m4a', '.mp4', '.mov'].includes(extname(assetName))) throw Error('Unsupported asset extension');
      assets.set(assetName, { source, sha256: hash(assetBytes) });
      return { id: item.id, kind: item.kind, text: item.referenceText, timestamp: item.timestamp,
        assetName, caption: typeof item.caption === 'string' ? item.caption : null };
    }
    if (typeof item.text !== 'string') throw Error('Text input requires text');
    // Explicit projection prevents labels/reviewer notes from reaching the model.
    return { id: item.id, kind: 'text', text: item.text, timestamp: item.timestamp };
  });
  if (!items.length) throw Error('Empty library');
  const projected = { id: l.id, split: l.split, slice: l.slice, items };
  if (l.orders?.interleaved) {
    const order = l.orders.interleaved;
    if (!Array.isArray(order) || order.length !== ids.size || new Set(order).size !== ids.size || order.some(id => !ids.has(id))) throw Error('Invalid predeclared interleaving');
    projected.orders = { interleaved: order };
  }
  return projected;
});
if (!libraries.length || wanted?.some(id => !seen.has(id))) throw Error('No matching libraries or unknown requested library');
const timeoutSeconds = Number(options.timeout ?? 600);
const maximumRuns = Number(options['max-runs'] ?? 0);
if (!Number.isInteger(timeoutSeconds) || timeoutSeconds < 1 || timeoutSeconds > 600 || !Number.isInteger(maximumRuns) || maximumRuns < 0) throw Error('Invalid timeout/max-runs');
const grdbRoot = realpathSync(options.grdb);
if (!existsSync(join(grdbRoot, 'Package.swift'))) throw Error('Expected existing GRDB checkout');
const appProject = readFileSync(join(repoRoot, 'Remember/Remember.xcodeproj/project.pbxproj'), 'utf8');
const team = appProject.match(/DEVELOPMENT_TEAM = ([A-Z0-9]+);/)?.[1];
if (!team) throw Error('Development team not found');
const sourceHashes = {};
function sources(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    if (entry.name === '.git') continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) sources(path);
    else if (entry.name.endsWith('.swift')) sourceHashes[path.slice(repoRoot.length + 1)] = hash(readFileSync(path));
  }
}
sources(join(repoRoot, 'Remember/Remember'));
sources(join(repoRoot, 'Remember/Shared'));
sourceHashes['scripts/embedding-evaluation/OrganizationProbe.swift'] = hash(readFileSync(join(scriptRoot, 'OrganizationProbe.swift')));
const configuration = { schemaVersion: 1, libraries, modes: mode === 'both' ? ['embedding', 'local'] : [mode], orders, timeoutSeconds, maximumRuns, mediaMode,
  manifest: { inputsSHA256, freezeSHA256, sourceHashes, assets: Object.fromEntries([...assets].map(([name, a]) => [name, a.sha256])), cloudEnabled: false, split, mediaMode,
    interleaving: 'predeclared input order, otherwise six chronological chunks round-robin', grdbPackageSHA256: hash(readFileSync(join(grdbRoot, 'Package.swift'))) } };
if (options['derived-data']) configuration.derivedDataPath = resolve(options['derived-data']);
configuration.manifest.expectedRunIDs = libraries.flatMap(library => configuration.modes.flatMap(mode => orders.flatMap(order =>
  Array.from({ length: mode === 'local' && order === 'chronological' ? 3 : 1 }, (_, repeat) => `${library.id}-${mode}-${order}-${repeat}`))));
configuration.manifest.configurationSHA256 = hash(JSON.stringify(configuration));
function projectPath(value) {
  if (/[\r\n]/.test(value)) throw Error('Paths must not contain line breaks');
  return JSON.stringify(value).slice(1, -1);
}
const project = readFileSync(join(scriptRoot, 'project.pbxproj.template'), 'utf8')
  .replaceAll('__REPO_ROOT__', projectPath(repoRoot)).replaceAll('__GRDB_ROOT__', projectPath(grdbRoot))
  .replaceAll('__DEVELOPMENT_TEAM__', team).replaceAll('EmbeddingProbe', 'OrganizationProbe')
  .replace('Embedding Probe', 'Organization Benchmark')
  .replace('buildPhases = (000000000000000000000008, 000000000000000000000017);', 'buildPhases = (000000000000000000000008, 000000000000000000000017, 000000000000000000000019);')
  .replace('  000000000000000000000018 =', '  000000000000000000000019 = { isa = PBXResourcesBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; };\n  000000000000000000000018 =');
const output = mkdtempSync(join(tmpdir(), 'RememberOrganizationProbe-'));
mkdirSync(join(output, 'Sources'));
mkdirSync(join(output, 'OrganizationProbe.xcodeproj'));
copyFileSync(join(scriptRoot, 'OrganizationProbe.swift'), join(output, 'Sources/OrganizationProbe.swift'));
for (const [name, asset] of assets) copyFileSync(asset.source, join(output, 'Sources', name));
const encoded = Buffer.from(JSON.stringify(configuration)).toString('base64');
writeFileSync(join(output, 'Sources/OrganizationConfiguration.swift'), `import Foundation\nnonisolated enum OrganizationConfiguration { static let data = Data(base64Encoded: "${encoded}")! }\n`);
writeFileSync(join(output, 'OrganizationProbe.xcodeproj/project.pbxproj'), project);
writeFileSync(join(output, 'configuration.json'), JSON.stringify(configuration, null, 2));
const derivedData = configuration.derivedDataPath ?? join(output, 'build');
console.log(JSON.stringify({ project: join(output, 'OrganizationProbe.xcodeproj'), derivedData,
  bundleIdentifier: 'SimpleStudio.Remember.OrganizationProbe', app: join(derivedData, 'Build/Products/Debug-iphoneos/OrganizationProbe.app'),
  configuration: join(output, 'configuration.json'), configurationSHA256: configuration.manifest.configurationSHA256,
  results: `Documents/organization-${configuration.manifest.configurationSHA256}.json` }, null, 2));
