import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mergeActiveCheckpoint } from './merge-organization-checkpoint.mjs';

const args = process.argv.slice(2);
const options = {};
for (let i = 0; i < args.length; i += 2) {
  const key = args[i]?.replace(/^--/, '');
  if (!args[i]?.startsWith('--') || !args[i + 1] || !['config', 'device', 'action', 'output', 'host-timeout', 'active-checkpoint'].includes(key)) throw Error('Invalid option/value');
  options[key] = args[i + 1];
}
if (!options.config || !options.device) throw Error('Usage: node run-organization.mjs --config generated/configuration.json --device deviceID --action build|run|collect|all --output /tmp/results.json');
const action = options.action ?? 'all';
if (!['build', 'run', 'collect', 'all'].includes(action)) throw Error('Invalid action');
if (action !== 'build' && !options.output) throw Error('--output required');
const useActiveCheckpoint = options['active-checkpoint'] ?? 'yes';
if (!['yes', 'no'].includes(useActiveCheckpoint)) throw Error('--active-checkpoint must be yes or no');
if (options.output && [options.output, `${options.output}.primary.json`, `${options.output}.active.json`].some(existsSync)) throw Error('Refusing to overwrite an existing result or raw sidecar; choose a new output path');
const configPath = resolve(options.config);
const config = JSON.parse(readFileSync(configPath));
const root = dirname(configPath);
const derivedData = config.derivedDataPath ?? join(root, 'build');
if (!root.includes('RememberOrganizationProbe-')) throw Error('Expected temporary project from prepare-organization.mjs');
const bundle = 'SimpleStudio.Remember.OrganizationProbe';
const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
for (const [path, expected] of Object.entries(action === 'collect' ? {} : config.manifest.sourceHashes)) {
  if (path.startsWith('/') || path.split('/').includes('..')) throw Error('Invalid source hash path');
  const observed = createHash('sha256').update(readFileSync(join(repoRoot, path))).digest('hex');
  if (observed !== expected) throw Error(`Source changed since preparation: ${path}. Prepare a fresh configuration.`);
}
const hostTimeout = Number(options['host-timeout'] ?? 3600);
if (!Number.isInteger(hostTimeout) || hostTimeout < 1 || hostTimeout > 43200) throw Error('Invalid host timeout');
function command(binary, arguments_, allowFailure = false) {
  const result = spawnSync(binary, arguments_, { stdio: 'inherit', timeout: (hostTimeout + 60) * 1000 });
  if (result.error) throw result.error;
  if (result.status !== 0 && !allowFailure) throw Error(`${binary} exited ${result.status}`);
  return result.status;
}
if (action === 'build' || action === 'all') {
  command('xcodebuild', ['-project', join(root, 'OrganizationProbe.xcodeproj'), '-scheme', 'OrganizationProbe',
    '-destination', `platform=iOS,id=${options.device}`, '-derivedDataPath', derivedData,
    '-disableAutomaticPackageResolution', '-allowProvisioningUpdates', 'build']);
}
let launchStatus = 0;
if (action === 'run' || action === 'all') {
  command('xcrun', ['devicectl', 'device', 'install', 'app', '--device', options.device,
    join(derivedData, 'Build/Products/Debug-iphoneos/OrganizationProbe.app')]);
  // Only this isolated benchmark bundle is terminated/relaunched; the personal app is never touched.
  launchStatus = command('xcrun', ['devicectl', 'device', 'process', 'launch', '--device', options.device,
    '--terminate-existing', '--console', '--timeout', String(hostTimeout), bundle], true);
}
if (action !== 'build') {
  const primaryPath = resolve(`${options.output}.primary.json`);
  const activePath = resolve(`${options.output}.active.json`);
  command('xcrun', ['devicectl', 'device', 'copy', 'from', '--device', options.device,
    '--source', `Documents/organization-${config.manifest.configurationSHA256}.json`, '--destination', primaryPath,
    '--domain-type', 'appDataContainer', '--domain-identifier', bundle]);
  let results = JSON.parse(readFileSync(primaryPath));
  if (results.manifest?.configurationSHA256 !== config.manifest.configurationSHA256) throw Error('Collected result configuration mismatch');
  let activeCheckpoint = 'not-needed';
  if (useActiveCheckpoint === 'yes' && results.runs?.some(run => run.status === 'running')) {
    try {
      const status = command('xcrun', ['devicectl', 'device', 'copy', 'from', '--device', options.device,
        '--source', `Documents/organization-${config.manifest.configurationSHA256}-active.json`, '--destination', activePath,
        '--domain-type', 'appDataContainer', '--domain-identifier', bundle], true);
      if (status === 0) {
        const merged = mergeActiveCheckpoint(results, JSON.parse(readFileSync(activePath)));
        results = merged.report; activeCheckpoint = merged.reason;
      } else activeCheckpoint = 'unavailable-primary-preserved';
    } catch (error) {
      activeCheckpoint = `unreadable-primary-preserved: ${error.message}`;
    }
  }
  // Raw primary and active sidecars remain untouched; the merged collection is a new exclusive artifact.
  writeFileSync(resolve(options.output), JSON.stringify(results), { flag: 'wx' });
  const statuses = {};
  for (const run of results.runs ?? []) statuses[run.status] = (statuses[run.status] ?? 0) + 1;
  const observed = new Set((results.runs ?? []).map(run => run.runID));
  const pendingRunIDs = (results.manifest.expectedRunIDs ?? []).filter(id => !observed.has(id));
  console.log(JSON.stringify({ output: resolve(options.output), primaryPath, activeCheckpoint, launchStatus, statuses, pendingRunIDs,
    note: 'Inspect completion coverage and score quality separately. Relaunch resumes terminal scenarios without replacing results.' }, null, 2));
  if (launchStatus !== 0 || pendingRunIDs.length || results.runs?.some(run => run.status !== 'completed')) process.exitCode = 2;
}
