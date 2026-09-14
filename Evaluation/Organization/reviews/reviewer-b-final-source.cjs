// Blind amendment review: only amended inputs, original inputs, and this reviewer's
// original review are consulted. Individual decisions below were source-reviewed.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.join(__dirname, '..');
const revisedBytes = fs.readFileSync(path.join(root, 'inputs-reviewed.json'));
const baseBytes = fs.readFileSync(path.join(__dirname, 'reviewer-b.json'));
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const expected = '189b78c63aadf04ac31eb18e08d7536552b6354f3eb4642a831d38dc27fbef9f';
if (hash(revisedBytes) !== expected) throw new Error('Reviewed input hash changed');
const revised = JSON.parse(revisedBytes);
const original = JSON.parse(fs.readFileSync(path.join(root, 'inputs.json'), 'utf8'));
const final = JSON.parse(baseBytes);

const decisions = {
  'l01-i01': 'Elm steps permit, east-curb inlet, overflow, and Thursday identify the same permit drawing as i24; sparse wording retains specific identity.',
  'l01-i02': 'The weekday grocer delivery observation, seated sightline, loading bay, and explicit Orchard crossing report all concern the crossing audit. Extra logistical detail introduces no second project.',
  'l02-i01': 'Swatches C/D with equal shade but different dipping histories fit the indigo report and dried cotton treatment comparison in i12; no other supplied swatch assignment competes.',
  'l02-i02': 'The kettle controls budget and low-vision prototype tasks concern the same control-panel assignment. A speaker, cardboard housing, feedback, and simulated heating are components of that prototype.',
  'l03-i01': 'Island bunkhouse keys and pier kiosk match the Mere overnight bunkhouse in i17. The mainland day visit has no overnight room or ferry-key requirement.',
  'l03-i02': 'Tuesday estuary day trip uses the riverside bus, observation screen, scope, and packed lunch, matching i13/i20. Same-day return without accommodation supports the mainland visit.',
  'l04-i02': 'Lantern is explicitly named; trio fee, refreshments, and borrowed lights match the listening evening in i28.',
  'l04-i03': 'Orchard Voices edit log, market bell, stallholder recollection, and episode opening identify the audio episode. The source does not ask for film-trailer work despite a separate bridge elsewhere.',
  'l05-i01': 'Drift trial retains its name; the food-bank volunteers replace the library venue/group. The supplied shift-board records establish the continuing trial despite its changed participants.',
  'l05-i04': 'Reading extension popup, article title editing, saved queue entry, draft restoration, and cancellation concern the browser reading product. No pantry date-entry context is present.',
  'l06-i01': 'Copper bird crate and externally visible tip indicator match the automaton loan packing constraints in i09/i10/i24.',
  'l06-i02': 'Six dock ledgers with brittle blue covers, cradle handling, folded inserts, and gutter capture identify the digitization batch; extra preservation steps remain part of scanning.',
  'l07-i02': 'Half-closed valve, far drip line, and repeated catch match the stone-tank emitter audit and i16 account of this corrected fault.',
  'l07-i03': 'East barley strips, fallen sowing-depth marker, and shallow-versus-deep treatment recovery identify the east depth experiment. The western cover-crop experiment holds sowing depth constant.',
  'l08-i02': 'Horn trial, outer station boat, and first pulse identify east-channel listening logistics, supported by i01/i17.',
  'l08-i03': 'Harbor Seal passenger ramp bushings, measured diameter, and incorrect sister-vessel drawing concern the same refit. Temporary walkway coordination remains refit logistics; no spill-drill action is requested here.',
  'l09-i01': 'Novice footwork, tape, visible signals, and Tuesday hall location match the fencing course in i21/i27. Floor-tape borrowing by the relay does not make this lesson note a relay source.',
  'l09-i02': 'Slate Pool is explicit. Second-instructor budgeting supports the opening confidence-series lessons at the wall and shallow-water entry, matching i08/i16/i18.',
  'l10-i01': 'Finder pointing at a daytime distant target and dusk star matches the finder worksheet and repeated daylight checks in i11/i19. Mirror washing has different procedures and no independent pointing session.',
  'l10-i02': 'Cobalt lamp fit, wavelength exposures, reference exposures, and calibration review place the purchasing estimate in the spectrograph calibration context.',
  'l11-i01': 'Faro is explicitly named; insulated pot capacity and portions concern the soup supper serving arrangements in i05/i13.',
  'l11-i02': 'Reassigned to Piedra: the amended source explicitly names the Piedra menu meeting, lunch orders, the base shared by both dishes, kitchen preparation sequence, and printing the menu. These resolve the original Faro/Piedra uncertainty in favor of the lunch redesign, not the soup event.',
  'l12-i01': 'Moraine explicitly names the surface survey; equally spaced transects and ground cover match ridge visibility and pottery-count corrections in i22/i23.',
  'l12-i03': 'Ardoise boxes, preserved original labels, context and collection-date checks identify the archive. The French passage explains distinct collections from the same square/layer; this is one archive checklist copy, not a second project.',
};

const changed = [];
for (const library of revised.libraries) {
  const oldLibrary = original.libraries.find(value => value.id === library.id);
  for (const item of library.items) {
    const oldItem = oldLibrary.items.find(value => value.id === item.id);
    if (item.text !== oldItem.text) changed.push(item.id);
  }
}
if (changed.length !== 24 || changed.some(id => !decisions[id]) || Object.keys(decisions).length !== 24) {
  throw new Error('Unexpected amendment coverage');
}

final.inputsSHA256 = hash(revisedBytes);
final.baseReviewSHA256 = hash(baseBytes);
final.amendmentReview = {};
for (const id of changed) {
  const library = final.libraries.find(value => value.id === id.split('-i')[0]);
  const previousMemberships = [...library.memberships[id]];
  const previouslyAmbiguous = library.ambiguous.includes(id);
  if (id === 'l11-i02') {
    library.memberships[id] = ['piedra-lunch-redesign'];
    library.ambiguous = library.ambiguous.filter(value => value !== id);
    library.issues[0] = 'Original i02 was ambiguous between Faro and Piedra. Its amended source explicitly names Piedra and the shared base of its lunch dishes, resolving that ambiguity and changing membership to Piedra. Spanish/English code switching is now present in i02. Saturday shaping and Sunday starter workshops remain separate; i18 and i24 retain explicit duplicate and non-project cues.';
  }
  library.rationale[id] = decisions[id];
  final.amendmentReview[id] = {
    previousMemberships,
    finalMemberships: [...library.memberships[id]],
    previouslyAmbiguous,
    ambiguous: library.ambiguous.includes(id),
    decision: id === 'l11-i02' ? 'Reassign and resolve ambiguity using explicit new evidence' : 'Retain membership after reviewing replacement source',
    evidence: decisions[id],
  };
}

for (const library of final.libraries) {
  library.issues.push('Amendment audit: one sparse and one long source were independently rereviewed in this library. Added length variation reduces the original uniform-length limitation, but fixed counts, explicit bridges, and repeated source roles remain. No new ambiguity was forced solely because a source became short.');
}

const base = JSON.parse(baseBytes);
let retained = 0;
let annotated = 0;
for (const library of final.libraries) {
  const before = base.libraries.find(value => value.id === library.id);
  const sourceLibrary = revised.libraries.find(value => value.id === library.id);
  const ids = new Set(sourceLibrary.items.map(value => value.id));
  if (Object.keys(library.memberships).length !== ids.size) throw new Error('Coverage');
  for (const [id, memberships] of Object.entries(library.memberships)) {
    if (!ids.has(id) || !memberships.length || memberships.length !== new Set(memberships).size || !library.rationale[id]) throw new Error(`Invalid annotation ${id}`);
    annotated += 1;
    if (!decisions[id]) {
      if (JSON.stringify(memberships) !== JSON.stringify(before.memberships[id]) ||
          library.rationale[id] !== before.rationale[id] ||
          library.ambiguous.includes(id) !== before.ambiguous.includes(id)) throw new Error(`Untouched annotation changed ${id}`);
      retained += 1;
    }
  }
  if (JSON.stringify(library.relationships) !== JSON.stringify(before.relationships)) throw new Error('Unexpected edge change');
  if (library.relationships.length !== 36) throw new Error('Relationship coverage');
}
if (retained !== 336 || annotated !== 360) throw new Error('Unexpected final counts');
fs.writeFileSync(path.join(__dirname, 'reviewer-b-final.json'), `${JSON.stringify(final, null, 2)}\n`, { flag: 'wx' });
console.log(JSON.stringify({ inputsSHA256: final.inputsSHA256, baseReviewSHA256: final.baseReviewSHA256,
  retained, rereviewed: changed.length, annotated,
  ambiguous: final.libraries.flatMap(value => value.ambiguous),
  membershipChanges: ['l11-i02: faro-soup-supper -> piedra-lunch-redesign'] }));
