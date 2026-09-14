/** Returns a new report only for a strictly matching, nonterminal current attempt. Never mutates primary. */
export function mergeActiveCheckpoint(primary, active) {
  const reject = reason => ({ report: primary, applied: false, reason });
  if (primary?.schemaVersion !== 1 || active?.schemaVersion !== 1) return reject('unsupported-schema');
  const hash = primary.manifest?.configurationSHA256;
  if (typeof hash !== 'string' || active.configurationSHA256 !== hash) return reject('configuration-mismatch');
  const run = active.run;
  if (!run || typeof run.runID !== 'string' || !Array.isArray(primary.runs)) return reject('invalid-run');
  const matches = primary.runs.filter(row => row.runID === run.runID);
  if (matches.length !== 1) return reject('unknown-or-duplicate-run');
  const current = matches[0];
  if (current.status !== 'running' || run.status !== 'running') return reject('terminal-run');
  if (typeof current.attemptID !== 'string' || current.attemptID !== run.attemptID) return reject('stale-attempt');
  for (const key of ['libraryID', 'mode', 'order', 'repeat', 'split', 'slice', 'mediaMode']) {
    if (current[key] !== run[key]) return reject('run-metadata-mismatch');
  }
  if (!Array.isArray(current.inputIDs) || JSON.stringify(current.inputIDs) !== JSON.stringify(run.inputIDs)) return reject('input-order-mismatch');
  if (!Number.isInteger(run.completedInputCount) || run.completedInputCount < (current.completedInputCount ?? 0)
      || run.completedInputCount < 0 || run.completedInputCount > current.inputIDs.length) return reject('stale-progress');
  const completedIDs = new Set(current.inputIDs.slice(0, run.completedInputCount));
  if (!run.memberships || Object.keys(run.memberships).some(id => !completedIDs.has(id))) return reject('unexpected-membership');
  return { report: { ...primary, runs: primary.runs.map(row => row.runID === run.runID ? structuredClone(run) : row) },
    applied: true, reason: 'matching-active-checkpoint' };
}
