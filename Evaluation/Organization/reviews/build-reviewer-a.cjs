// Independent review A: assignments below were made after reading every source
// in inputs.json and the contract, without author labels or app predictions.
// This generator only formats those manual assignments and source excerpts.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const assignments = {
  l01: {
    'elm-permit': [1, 24, 23],
    'towpath-maintenance': [25, 22, 29, 23],
    'north-hall-repairs': [21, 16, 13, 4],
    'south-court-lending': [30, 14, 7, 12, 4],
    'juniper-shade': [15, 26, 6, 17, 11, 9],
    'orchard-crossing': [28, 8, 2, 5, 27, 19, 3, 9],
    'mug-preference': [10], 'detective-story': [18], 'trust-metaphor': [20]
  },
  l02: {
    'indigo-report': [12, 26, 1, 16],
    'kettle-controls': [19, 29, 2, 4, 17, 21, 28, 16, 27],
    'stairwell-acoustics': [7, 18, 5, 22, 27],
    'market-maps-essay': [20, 14, 24, 6, 30],
    'urn-simulation': [10, 8, 23, 15],
    'torus-presentation': [11, 9, 15],
    'laundry-strap': [3], 'duck-observation': [13], 'railway-board-game': [25]
  },
  l03: {
    'mere-island-overnight': [17, 1, 19],
    'mainland-estuary-day': [20, 13, 2, 19],
    'rook-architecture-weekend': [25, 24, 10, 18],
    'vela-rail-festival': [27, 12, 4, 7, 30, 6, 14, 18],
    'sable-ridge-trek': [22, 15, 11, 16, 8],
    'linden-reunion': [26, 9, 5, 28, 29, 8],
    'lentil-soup': [3], 'lamp-bulb': [21], 'novel-platform-metaphor': [23]
  },
  l04: {
    'dusk-mural': [25, 24, 7, 26, 20, 18],
    'lantern-listening': [28, 12, 27, 2, 29, 23, 16, 18],
    'orchard-audio': [19, 3, 10, 5],
    'window-seat-film': [9, 8, 11, 17, 5],
    'paper-moon-puppets': [22, 13, 21],
    'moon-paper-chapbook': [6, 4, 30, 21],
    'button-jar-observation': [1], 'card-game-scoring': [14], 'bicycle-bell': [15]
  },
  l05: {
    'drift-shift-swaps': [28, 2, 8, 6, 20, 1, 27, 7],
    'tern-room-booking': [13, 23, 14, 7],
    'moss-plant-checks': [9, 18, 12, 17, 24],
    'pebble-pantry': [16, 5, 24],
    'pebble-reading-extension': [21, 15, 4, 26],
    'kite-invoice-export': [22, 29, 10, 30, 11, 26],
    'wooden-kite': [3], 'crystal-documentary': [19], 'rye-loaf': [25]
  },
  l06: {
    'copper-automaton-loan': [10, 1, 18, 24, 11, 9, 14, 29],
    'dock-ledger-digitization': [2, 17, 21, 25, 29],
    'blue-vessel-monitoring': [27, 3, 7, 19],
    'amber-textile-rotation': [23, 6, 16, 28, 30, 19],
    'aster-lacquer-treatment': [15, 5, 13],
    'aster-teaching-screen': [22, 12, 8, 13],
    'cereal-claim': [4], 'curtain-rail': [20], 'newspaper-dream': [26]
  },
  l07: {
    'east-barley-depth': [8, 3, 19],
    'west-barley-cover': [23, 9, 6, 19],
    'tomato-shade': [5, 17, 13, 4],
    'mushroom-substrate': [18, 12, 24, 7, 4],
    'pear-pollinator-survey': [22, 20, 28, 29, 14, 25],
    'stone-tank-irrigation': [27, 2, 10, 11, 30, 21, 16, 25],
    'fitted-sheet': [1], 'seed-poem': [15], 'radio-knob': [26]
  },
  l08: {
    'north-beacon-electrical': [6, 12, 16],
    'south-beacon-lens': [22, 20, 18, 16],
    'harbor-seal-ramp': [9, 3, 21, 30, 24],
    'quay-four-spill-drill': [5, 15, 25, 19, 27, 24],
    'basin-c-sediment': [23, 26, 10, 1],
    'east-channel-fog-signal': [17, 8, 2, 14, 4, 11, 13, 1],
    'safe-harbor-wordplay': [7], 'hallway-clock': [28], 'bread-pot': [29]
  },
  l09: {
    'harbor-fencing-course': [21, 27, 1, 6, 10],
    'cedar-relay': [28, 5, 30, 24, 17, 10],
    'slate-pool-confidence': [8, 16, 2, 18, 3, 12, 26, 22],
    'hill-court-tennis': [14, 19, 7, 22],
    'river-junior-starts': [9, 4, 11],
    'river-masters-endurance': [13, 20, 15, 11],
    'umbrella-strap': [23], 'tomato-sauce': [25], 'bath-wordplay': [29]
  },
  l10: {
    'lumen-finder-alignment': [1, 19, 11, 5],
    'lumen-mirror-wash': [7, 29, 5],
    'aurora-camera-heating': [9, 12, 4, 6, 24, 26],
    'cinder-star-cadence': [13, 22, 18, 26],
    'cobalt-calibration': [14, 16, 2, 25, 8, 15, 30, 17],
    'rill-occultation': [21, 20, 3, 23, 17],
    'bookshelf-shim': [10], 'radio-drama': [27], 'ceramic-star-keepsake': [28]
  },
  l11: {
    'faro-soup-supper': [5, 1, 13, 2, 27, 3, 20],
    'oliva-bilingual-recipes': [8, 10, 7, 16, 26, 18, 28, 6],
    'nube-aroma-lesson': [11, 25, 15, 6],
    'brisa-sunday-starter': [9, 29, 12, 23],
    'brisa-saturday-shaping': [21, 17, 23],
    'piedra-lunch-redesign': [19, 30, 22, 20],
    'drawer-squeak': [4], 'reading-preference': [14], 'cloud-observation': [24]
  },
  l12: {
    'moraine-pottery-survey': [1, 22, 23, 10],
    'tilleul-boundary-geophysics': [7, 11, 20, 28, 25, 10],
    'valon-a-hearth-sampling': [8, 6, 14],
    'valon-b-wall-phasing': [21, 29, 17, 14],
    'serein-well-recording': [13, 24, 26, 30, 2],
    'ardoise-sediment-archive': [27, 5, 15, 4, 12, 3, 9, 2],
    'novel-well-metaphor': [16], 'suitcase-wheel': [18], 'home-plant': [19]
  }
};

const source = JSON.parse(fs.readFileSync(path.join(__dirname, '../inputs.json'), 'utf8'));
assert.equal(source.libraries.length, 12);
const libraries = source.libraries.map(library => {
  const groups = assignments[library.id];
  assert.ok(groups, `Missing library ${library.id}`);
  assert.equal(library.items.length, 30);
  assert.equal(Object.keys(groups).length, 9);
  const memberships = {};
  const rationale = {};
  for (const item of library.items) {
    const ordinal = Number(item.id.split('-i')[1]);
    memberships[item.id] = Object.entries(groups)
      .filter(([, members]) => members.includes(ordinal)).map(([group]) => group);
    assert.ok(memberships[item.id].length > 0, `Unreviewed ${item.id}`);
    assert.ok(memberships[item.id].length <= 2, `Unexpected overlap ${item.id}`);
    const sentence = item.text.match(/^.*?[.!?](?:\s|$)/u)?.[0].trim() ?? item.text;
    rationale[item.id] = `Context: ${memberships[item.id].join(' and ')}. Source: “${sentence}”`;
  }
  const itemId = ordinal => `${library.id}-i${String(ordinal).padStart(2, '0')}`;
  for (const [group, members] of Object.entries(groups)) {
    assert.equal(new Set(members).size, members.length, `Duplicate assignment ${group}`);
    for (const ordinal of members) assert.ok(memberships[itemId(ordinal)], `Unknown item ${ordinal}`);
  }
  const relationships = [];
  const names = Object.keys(groups);
  for (let i = 0; i < names.length; i++) {
    for (let j = i + 1; j < names.length; j++) {
      const first = names[i];
      const second = names[j];
      // Positive relations have explicit shared-resource or cross-project source
      // evidence. Other pairs have separate source anchors and no evidenced link.
      const bridge = groups[first].filter(ordinal => groups[second].includes(ordinal));
      relationships.push({ first, second, related: bridge.length > 0,
        evidence: bridge.length ? bridge.map(itemId) : [itemId(groups[first][0]), itemId(groups[second][0])] });
    }
  }
  assert.equal(relationships.length, 36);
  assert.equal(relationships.filter(x => x.related).length, 3);
  return { id: library.id, memberships, ambiguous: [], rationale, relationships, issues: [] };
});
const review = {
  schemaVersion: 1,
  reviewer: 'reviewer-a',
  role: 'independent-review',
  model: 'inherited model identity not exposed',
  blindToPredictions: true,
  libraries
};
const output = path.join(__dirname, 'reviewer-a.json');
fs.writeFileSync(output, `${JSON.stringify(review, null, 2)}\n`, { flag: 'wx' });
console.log(JSON.stringify({ libraries: libraries.length,
  reviewedItems: libraries.reduce((count, library) => count + Object.keys(library.memberships).length, 0),
  relationships: libraries.reduce((count, library) => count + library.relationships.length, 0),
  ambiguous: libraries.reduce((count, library) => count + library.ambiguous.length, 0) }));
