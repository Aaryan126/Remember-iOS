// Independent source review. Assignments were made after reading all 360 inputs.
// This file reads no author labels, predictions, application code, or other review.
const fs = require('node:fs');
const path = require('node:path');

const specifications = [
  {
    id: 'l01',
    groups: {
      'elm-permit': [1, 23, 24],
      'orchard-crossing': [2, 3, 5, 8, 9, 19, 27, 28],
      'north-hall-cafe': [4, 13, 16, 21],
      'south-court-locker': [4, 7, 12, 14, 30],
      'juniper-shade': [6, 9, 11, 15, 17, 26],
      'canal-planting': [22, 23, 25, 29],
      'personal-mug': [10], 'detective-reading': [18], 'repair-metaphor': [20],
    },
    bridges: [4, 9, 23],
    ambiguous: [],
    audit: 'The explicit budget separation in i04, transport distinction in i09, and separate jobs in i23 make bridges unusually easy. Personal items i10/i18/i20 have no supported shared context. i26 is assigned through the exposure count and bakery queue evidence, not its lack of a project name.',
  },
  {
    id: 'l02',
    groups: {
      'indigo-report': [1, 12, 16, 26],
      'kettle-controls': [2, 4, 16, 17, 19, 21, 27, 28, 29],
      'stairwell-decay': [5, 7, 18, 22, 27],
      'market-history-essay': [6, 14, 20, 24, 30],
      'urn-simulation': [8, 10, 15, 23],
      'torus-talk': [9, 11, 15],
      'laundry-strap': [3], 'campus-duck': [13], 'railway-game': [25],
    },
    bridges: [15, 16, 27],
    ambiguous: [],
    audit: 'Seminar/course vocabulary is insufficient to merge the urn and torus assignments. Equipment sharing is spelled out in i15/i16/i27. Explicit duplicate i21 and unusually clear non-assignment language in i13/i25 reduce realism and make some decisions shortcut-friendly.',
  },
  {
    id: 'l03',
    groups: {
      'mere-island-overnight': [1, 17, 19],
      'mainland-estuary-day': [2, 13, 19, 20],
      'vela-festival': [4, 6, 7, 12, 14, 18, 27, 30],
      'linden-reunion': [5, 8, 9, 26, 28, 29],
      'sable-trek': [8, 11, 15, 16, 22],
      'rook-architecture': [10, 18, 24, 25],
      'lentil-soup': [3], 'desk-lamp': [21], 'platform-wordplay': [23],
    },
    bridges: [8, 18, 19],
    ambiguous: [],
    audit: 'Mere island and mainland reserve are explicitly different trips despite sharing a place name; cabin access contradictions remain in the reunion. Three bridges describe separate packing or spending records. i06 explicitly announces its duplicate status, while i23 directly disclaims the station meaning.',
  },
  {
    id: 'l04',
    groups: {
      'lantern-evening': [2, 12, 16, 18, 23, 27, 28, 29],
      'orchard-audio': [3, 5, 10, 19],
      'moon-paper-book': [4, 6, 21, 30],
      'window-seat-film': [5, 8, 9, 11, 17],
      'dusk-mural': [7, 18, 20, 24, 25, 26],
      'paper-moon-puppets': [13, 21, 22],
      'button-sketch': [1], 'card-game': [14], 'bicycle-bell': [15],
    },
    bridges: [5, 18, 21],
    ambiguous: [],
    audit: 'The film trailer audio is part of the continuing film work, even though the film is silent. The reversed Moon/Paper names are directly disambiguated in i06/i21. i01/i15 overtly mark themselves as personal; i23 overtly announces duplication. These are synthetic shortcut cues.',
  },
  {
    id: 'l05',
    groups: {
      'drift-shift-board': [1, 2, 6, 7, 8, 20, 27, 28],
      'pebble-reading': [4, 15, 21, 26],
      'pebble-pantry': [5, 16, 24],
      'tern-booking': [7, 13, 14, 23],
      'moss-reminders': [9, 12, 17, 18, 24],
      'kite-invoice': [10, 11, 22, 26, 29, 30],
      'toy-kite': [3], 'salt-documentary': [19], 'rye-loaf': [25],
    },
    bridges: [7, 24, 26],
    ambiguous: [],
    audit: 'The changed Drift participant group in i01 does not start a new trial. The two Pebble projects are explicitly disambiguated in i21. i07/i24/i26 explicitly distinguish shared review topics from product identity. The toy kite and science-project disclaimer are easy negative cues.',
  },
  {
    id: 'l06',
    groups: {
      'automaton-loan': [1, 9, 10, 11, 14, 18, 24, 29],
      'dock-ledgers': [2, 17, 21, 25, 29],
      'blue-vessel-monitoring': [3, 7, 19, 27],
      'lacquer-screen-treatment': [5, 13, 15],
      'amber-textile-display': [6, 16, 19, 23, 28, 30],
      'teaching-screen-mount': [8, 12, 13, 22],
      'cereal-claim': [4], 'curtain-rail': [20], 'newspaper-dream': [26],
    },
    bridges: [13, 19, 29],
    ambiguous: [],
    audit: 'Static-only versus one demonstration instructions concern the same automaton loan. The two screens have distinct object identities made explicit in i13/i22. Conservation vocabulary alone does not join other objects. The cereal/dream negatives explicitly deny museum-project membership.',
  },
  {
    id: 'l07',
    groups: {
      'stone-tank-audit': [2, 10, 11, 16, 21, 25, 27, 30],
      'east-barley-depth': [3, 8, 19],
      'tomato-shade': [4, 5, 13, 17],
      'west-barley-cover': [6, 9, 19, 23],
      'blue-shed-mushrooms': [4, 7, 12, 18, 24],
      'pear-pollinators': [14, 20, 22, 25, 28, 29],
      'sheet-folding': [1], 'seed-poem': [15], 'radio-knob': [26],
    },
    bridges: [4, 19, 25],
    ambiguous: [],
    audit: 'The barley experiments remain distinct by plots and treatment variables. i16 explicitly keeps different irrigation faults within one audit. Shared scale/counters/timing generate three conspicuous bridges. i15 announces metaphor status; i21 announces duplication, offering easy negative and positive signals.',
  },
  {
    id: 'l08',
    groups: {
      'east-channel-fog-trial': [1, 2, 4, 8, 11, 13, 14, 17],
      'basin-c-sediment': [1, 10, 23, 26],
      'harbor-seal-ramp': [3, 9, 21, 24, 30],
      'quay-four-drill': [5, 15, 19, 24, 25, 27],
      'north-beacon-electrical': [6, 12, 16],
      'south-beacon-cleaning': [16, 18, 20, 22],
      'harbor-puzzle': [7], 'hallway-clock': [28], 'bread-pot': [29],
    },
    bridges: [1, 16, 24],
    ambiguous: [],
    audit: 'The added station i13 and night-pattern request i04 remain fog-trial context. Beacon stations are different maintenance tasks despite a common boat circuit. i07 explicitly labels a metaphor and i11 explicitly labels a copy. Most cross-context distinction is supplied directly by the source.',
  },
  {
    id: 'l09',
    groups: {
      'harbor-fencing': [1, 6, 10, 21, 27],
      'slate-pool-series': [2, 3, 8, 12, 16, 18, 22, 26],
      'junior-rowing-starts': [4, 9, 11],
      'cedar-relay': [5, 10, 17, 24, 28, 30],
      'hill-court-tennis': [7, 14, 19, 22],
      'masters-endurance': [11, 13, 15, 20],
      'umbrella-strap': [23], 'tomato-sauce': [25], 'bath-joke': [29],
    },
    bridges: [10, 11, 22],
    ambiguous: [],
    audit: 'The masters indoor session remains part of the endurance block. The continuation-group request i26 is evidence about the completed pool series, without a separately established new project. Equipment/access bridges explicitly name both contexts. The joke and duplicate are overtly labeled.',
  },
  {
    id: 'l10',
    groups: {
      'lumen-finder': [1, 5, 11, 19],
      'cobalt-calibration': [2, 8, 14, 15, 16, 17, 25, 30],
      'rill-occultation': [3, 17, 20, 21, 23],
      'aurora-camera': [4, 6, 9, 12, 24, 26],
      'lumen-mirror-wash': [5, 7, 29],
      'cinder-cadence-study': [13, 18, 22, 26],
      'bookshelf-shim': [10], 'radio-drama': [27], 'star-keepsake': [28],
    },
    bridges: [5, 17, 26],
    ambiguous: [],
    audit: 'Lumen pointing and mirror maintenance are distinct tasks with an explicit dependency. Cobalt lamp procurement is assigned to calibration through its named maintenance estimate and lamp-line context. i15 explicitly identifies a copy, while i28 directly disclaims instrument membership. Failed fixes and negative observations retain original contexts.',
  },
  {
    id: 'l11',
    groups: {
      'faro-soup-supper': [1, 2, 3, 5, 13, 20, 27],
      'nube-aroma-lesson': [6, 11, 15, 25],
      'oliva-recipe-book': [6, 7, 8, 10, 16, 18, 26, 28],
      'brisa-starter-clinic': [9, 12, 23, 29],
      'brisa-shaping-workshop': [17, 21, 23],
      'piedra-lunch-redesign': [19, 20, 22, 30],
      'bedroom-drawer': [4], 'reading-preference': [14], 'cloud-sighting': [24],
    },
    bridges: [6, 20, 23],
    ambiguous: [2],
    rationaleOverrides: {
      2: 'Provisional Faro membership: shared kitchen and readable ingredient information fit i01/i05. However, this unnamed "Menu meeting" and its diners could also belong to Piedra lunch redesign (i19/i22/i30). The source lacks an event name, serving-station detail, or other decisive identity evidence; exclude from unambiguous scoring.',
    },
    audit: 'i02 has a real Faro/Piedra ambiguity despite stronger Faro evidence. Spanish and English items are interleaved, but each is mostly monolingual and repeats the English libraries\' task structure. Saturday shaping and Sunday starter workshops are explicitly distinguished; i18 announces duplication and i24 disclaims cooking-class membership.',
  },
  {
    id: 'l12',
    groups: {
      'moraine-surface-survey': [1, 10, 22, 23],
      'serein-well-recording': [2, 13, 24, 26, 30],
      'ardoise-archive': [2, 3, 4, 5, 9, 12, 15, 27],
      'valon-a-hearth': [6, 8, 14],
      'tilleul-geophysics': [7, 10, 11, 20, 25, 28],
      'valon-b-walls': [14, 17, 21, 29],
      'well-metaphor': [16], 'suitcase-wheel': [18], 'houseplant': [19],
    },
    bridges: [2, 10, 14],
    ambiguous: [],
    audit: 'Trench A sampling and trench B wall phasing have distinct questions despite the same site. Successive sample bags remain within one archive-management context rather than becoming new projects. French/English texts repeat the same bridge/duplicate/revision/disclaimed-singleton construction found in English libraries.',
  },
];

const source = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'inputs.json'), 'utf8'));
const result = {
  schemaVersion: 1,
  reviewer: 'reviewer-b',
  role: 'independent-review',
  model: 'inherited model identity not exposed',
  blindToPredictions: true,
  libraries: [],
};

for (const spec of specifications) {
  const library = source.libraries.find(value => value.id === spec.id);
  if (!library || library.items.length !== 30) throw new Error(`Unexpected library ${spec.id}`);
  const itemId = number => `${spec.id}-i${String(number).padStart(2, '0')}`;
  const memberships = {};
  const rationale = {};
  for (const item of library.items) {
    const number = Number(item.id.split('-i')[1]);
    memberships[item.id] = Object.entries(spec.groups)
      .filter(([, numbers]) => numbers.includes(number))
      .map(([name]) => name);
    if (!memberships[item.id].length) throw new Error(`Unreviewed item ${item.id}`);
    const excerpt = item.text.length > 230 ? `${item.text.slice(0, 227)}...` : item.text;
    rationale[item.id] = spec.rationaleOverrides?.[number] ||
      `Context: ${memberships[item.id].join(' and ')}. Source evidence: ${JSON.stringify(excerpt)}`;
  }
  const threads = Object.keys(spec.groups);
  const relationships = [];
  for (let a = 0; a < threads.length; a += 1) {
    for (let b = a + 1; b < threads.length; b += 1) {
      const first = threads[a];
      const second = threads[b];
      const bridgeEvidence = spec.bridges.filter(number =>
        spec.groups[first].includes(number) && spec.groups[second].includes(number));
      relationships.push({
        first,
        second,
        related: bridgeEvidence.length > 0,
        evidence: bridgeEvidence.length ? bridgeEvidence.map(itemId) :
          [itemId(spec.groups[first][0]), itemId(spec.groups[second][0])],
      });
    }
  }
  const singletonCount = Object.values(spec.groups).filter(numbers => numbers.length === 1).length;
  const overlapCount = Object.values(memberships).filter(assigned => assigned.length > 1).length;
  result.libraries.push({
    id: spec.id,
    memberships,
    ambiguous: spec.ambiguous.map(itemId),
    rationale,
    relationships,
    issues: [
      spec.audit,
      `Distribution audit: ${library.items.length} text-only items, ${threads.length - singletonCount} continuing contexts, ${singletonCount} singletons, ${overlapCount} dual-context sources. This identical high-level structure across all 12 libraries is a benchmark shortcut risk; no grouping was inferred from counts.`,
      'Template audit: repeated budget/meeting/revision/explicit-copy/personal-aside phrasing and tidy explicit bridges reduce natural ambiguity. Cross-library construction similarities may inflate apparent heldout generalization even when subject matter changes.',
      'Relationship annotation: true requires a source-supported cross-context connection. False means no specific connection is supported in this supplied library; common discipline, location type, vocabulary, or writing style alone was insufficient. Evidence on a false edge identifies the distinct contexts, not proof that no real-world relationship could exist.',
    ],
  });
}

const assignedItems = result.libraries.reduce((count, library) => count + Object.keys(library.memberships).length, 0);
if (result.libraries.length !== 12 || assignedItems !== 360) throw new Error('Incomplete review');
const destination = path.join(__dirname, 'reviewer-b.json');
fs.writeFileSync(destination, `${JSON.stringify(result, null, 2)}\n`, { flag: 'wx' });
console.log(JSON.stringify({ libraries: result.libraries.length, items: assignedItems,
  relationshipAnnotations: result.libraries.reduce((count, library) => count + library.relationships.length, 0),
  ambiguous: result.libraries.flatMap(library => library.ambiguous) }));
