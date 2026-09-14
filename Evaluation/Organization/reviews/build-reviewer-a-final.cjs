// Formats reviewer A's independent source-based amendment decisions.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const revisedBytes = fs.readFileSync(path.join(__dirname, '../inputs-reviewed.json'));
const baseBytes = fs.readFileSync(path.join(__dirname, 'reviewer-a.json'));
const revised = JSON.parse(revisedBytes);
const base = JSON.parse(baseBytes);
const final = structuredClone(base);
final.inputsSHA256 = digest(revisedBytes);
assert.equal(final.inputsSHA256, '189b78c63aadf04ac31eb18e08d7536552b6354f3eb4642a831d38dc27fbef9f');
final.baseReviewSHA256 = digest(baseBytes);
final.amendmentReview = {};

const decisions = {
  'l01-i01': ['elm-permit', 'Elm steps permit and east-curb inlet/overflow identify the permit task; the Thursday inlet revision in l01-i24 confirms continuity.'],
  'l01-i02': ['orchard-crossing', 'Explicitly names the Orchard crossing report and requests weekday grocer-delivery observations from the agreed seated sightline.'],
  'l02-i01': ['indigo-report', 'Swatches with different dipping histories and the same shade match the drying-versus-dip comparison in l02-i12.'],
  'l02-i02': ['kettle-controls', 'Names kettle controls, a 35-credit prototype budget, temperature selection and feedback; the speaker and cardboard serve that control test.'],
  'l03-i01': ['mere-island-overnight', 'Island bunkhouse keys at the pier kiosk match the west bunkhouse and passenger ferry overnight plan in l03-i17.'],
  'l03-i02': ['mainland-estuary-day', 'Estuary Tuesday, same-day return, riverside bus, scope and packed lunch match the mainland visit in l03-i20.'],
  'l04-i02': ['lantern-listening', 'Explicit Lantern name, trio fee, refreshments and battery lights identify the listening evening described in l04-i28.'],
  'l04-i03': ['orchard-audio', 'Names the Orchard Voices edit log and the market-bell transition to the stallholder recollection; this is the episode opening edit.'],
  'l05-i01': ['drift-shift-swaps', 'Explicitly names Drift and changes the volunteer venue/group after the library room failed; the continuing trial remains identifiable.'],
  'l05-i04': ['pebble-reading-extension', 'Reading extension title editing, popup draft loss and the saved article queue identify the browser experiment in l05-i21.'],
  'l06-i01': ['copper-automaton-loan', 'Copper bird crate and a visible tip indicator match the automaton transport support and packing checklist in l06-i09 and l06-i10.'],
  'l06-i02': ['dock-ledger-digitization', 'Names the dock ledger batch, six brittle blue-covered volumes, cradle support and capture of folded inserts.'],
  'l07-i02': ['stone-tank-irrigation', 'Half-closed valve, far drip line and repeated catch match the irrigation setup error retained in l07-i16.'],
  'l07-i03': ['east-barley-depth', 'Explicit east barley strips and shallow-versus-deep treatment assignment identify the depth trial; uncertain strip labeling does not obscure project identity.'],
  'l08-i02': ['east-channel-fog-signal', 'Horn trial, outer listening station and first pulse match the east-channel listening trial in l08-i17.'],
  'l08-i03': ['harbor-seal-ramp', 'Names Harbor Seal passenger-ramp bushings and a quote based on the wrong vessel drawing; dimensions and refit sequence keep this in the ramp task.'],
  'l09-i01': ['harbor-fencing-course', 'Novice footwork, floor tape and visible signals match the fencing course in l09-i21; a hall change preserves the course identity.'],
  'l09-i02': ['slate-pool-confidence', 'Explicit Slate Pool opening weeks, instructors at the wall and entry steps identify the confidence series.'],
  'l10-i01': ['lumen-finder-alignment', 'Finder daytime distant-target and dusk-star checks match the finder worksheet and repeated daylight check in l10-i11 and l10-i19.'],
  'l10-i02': ['cobalt-calibration', 'Names Cobalt, lamp/socket compatibility, wavelength exposures and calibration review; the quotation supports that calibration preparation.'],
  'l11-i01': ['faro-soup-supper', 'Faro and insulated-pot capacity for portions explicitly identify the soup supper described in l11-i05.'],
  'l11-i02': ['piedra-lunch-redesign', 'Now explicitly names Piedra menu review, lunch orders and a base shared by two dishes, matching l11-i19. Assign Piedra only; this amended source does not mention the Faro supper.'],
  'l12-i01': ['moraine-pottery-survey', 'Moraine, equally spaced transects and ground cover match the ridge pottery visibility comparison in l12-i22 and l12-i23.'],
  'l12-i03': ['ardoise-sediment-archive', 'Explicit Ardoise boxes, original bag labels, collection dates and a repeated shelf-side checklist identify the sediment archive review.']
};
assert.equal(Object.keys(decisions).length, 24);
let changed = 0;
let retained = 0;
for (const library of final.libraries) {
  const originalLibrary = base.libraries.find(x => x.id === library.id);
  const sourceLibrary = revised.libraries.find(x => x.id === library.id);
  assert.equal(Object.keys(library.memberships).length, sourceLibrary.items.length);
  for (const item of sourceLibrary.items) {
    const judgment = decisions[item.id];
    if (!judgment) {
      assert.deepEqual(library.memberships[item.id], originalLibrary.memberships[item.id]);
      assert.equal(library.rationale[item.id], originalLibrary.rationale[item.id]);
      retained++;
      continue;
    }
    const [group, evidence] = judgment;
    const before = originalLibrary.memberships[item.id];
    const after = [group];
    const membershipChanged = JSON.stringify(before) !== JSON.stringify(after);
    if (membershipChanged) changed++;
    library.memberships[item.id] = after;
    library.rationale[item.id] = evidence;
    library.ambiguous = library.ambiguous.filter(id => id !== item.id);
    final.amendmentReview[item.id] = {
      decision: membershipChanged ? 'membership-revised' : 'membership-retained',
      previousMemberships: before, memberships: after, ambiguous: false,
      evidence,
      relationshipDecision: 'unchanged; existing explicit cross-context bridge evidence remains valid'
    };
  }
}
assert.equal(retained, 336);
assert.equal(changed, 1);
assert.equal(Object.keys(final.amendmentReview).length, 24);
fs.writeFileSync(path.join(__dirname, 'reviewer-a-final.json'), `${JSON.stringify(final, null, 2)}\n`, { flag: 'wx' });
console.log(JSON.stringify({ reviewedItems: 360, amendmentsReviewed: 24, unchangedItemsRetained: retained,
  membershipChanges: changed, ambiguous: 0, inputsSHA256: final.inputsSHA256,
  baseReviewSHA256: final.baseReviewSHA256 }));
