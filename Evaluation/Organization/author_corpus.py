"""Original synthetic author corpus; contains hidden labels. Never feed to a runner.

Run directly to regenerate the two intentional fixture artifacts beside this file.
The prose below is manually authored; the script only assigns IDs and serializes it.
"""

import itertools
import json
import random
from pathlib import Path


LIBRARIES = []


def library(domain, threads, bridges, singletons, extra_related=()):
    assert [len(items) for _, items in threads] == [2, 3, 3, 4, 5, 7]
    assert len(bridges) == len(singletons) == 3
    LIBRARIES.append((domain, threads, bridges, singletons, extra_related))


library("neighborhood infrastructure", [
    ("Elm steps rain-garden permit", [
        "Elm steps garden: the permit sketch must show runoff entering from the east curb. The pretty planting diagram is insufficient; the inspector needs the overflow route before approving excavation.",
        "After the rain, water pooled beside the lowest stair instead of reaching our proposed bed. Revise that east-curb drawing with a shallow inlet channel; the permit appointment remains Thursday.",
    ]),
    ("Canal towpath rain-garden volunteer day", [
        "Canal towpath planting day needs twelve pairs of gloves and a volunteer who can explain the reed plugs. This is maintenance of an existing basin, so nobody should submit an excavation application.",
        "The towpath coordinator changed the volunteer start from nine to ten because the gatekeeper arrives late. The old signup image still says nine; mention the correction in the reminder.",
        "Receipt note: reed plugs cost 86 credits, leaving 24 for gloves. Keep this against the canal planting allowance. The council's stairway project has its own budget and no shared purchasing authority.",
    ]),
    ("North hall repair cafe", [
        "Repair cafe at North Hall: bring two soldering mats and reserve the table nearest ventilation. We can inspect unplugged lamps, but the volunteer form must not promise certified electrical repairs.",
        "The mending corner only drew three visitors last time. For Saturday's hall session, move clothing repairs beside the entrance and put the lamp inspection queue along the windows.",
        "Keep the handwritten lamp checklist from our North Hall session. Someone assumed a loose switch was a broken cable; recording the symptoms first would have saved a lot of disassembly.",
    ]),
    ("South court tool-lending locker", [
        "South Court locker proposal: lend hand tools through numbered compartments, with a paper borrowing card for residents without phones. A staffed repair event is not part of this request.",
        "The caretaker says the courtyard wall cannot support a loaded metal cabinet. Price a freestanding frame and draw its footprint before the tenants vote on the tool locker.",
        "Budget review for the lending cabinet: 140 credits for the frame, 55 for weather seals, and 30 for spare locks. Do not fund power tools until we know the borrowing pattern.",
        "Trial return cards were unreadable after drizzle. Use the sheltered noticeboard pocket for receipts, while the numbered compartments keep their simple brass labels. Test again before the courtyard vote.",
    ]),
    ("Juniper bus-stop shade campaign", [
        "Juniper stop shade petition should count people waiting between two and four, not total bus boardings. The transport office asked for evidence of exposure during the hottest part of the afternoon.",
        "Our first count accidentally included people waiting outside the bakery. Repeat the observation from the opposite pavement and mark the actual queue boundary on the paper tally.",
        "Draft for the shelter meeting: ask for a narrow canopy that leaves wheelchair turning space. A tree sounds pleasant, but the underground utility corridor makes planting unlikely here.",
        "Transport replied that a temporary fabric awning might be permitted this season. Save that email with the Juniper shade evidence; it changes the proposal but does not settle maintenance responsibility.",
        "Correct the petition handout: the shade meeting is on the eighteenth, not the eighth. Twenty copies already went to the bakery, so a replacement poster alone will miss some neighbors.",
    ]),
    ("Orchard crossing visibility audit", [
        "Orchard crossing audit starts with photographs from a seated pedestrian's height. We are checking whether parked delivery vans hide approaching cyclists, rather than campaigning for another traffic signal.",
        "At the crossing opposite the grocer, the white van blocked the view for eleven minutes. Record duration and position without photographing the driver or making assumptions about who owns it.",
        "The road engineer wants a weekday sample as well as Saturday photographs. Ask two volunteers to observe the grocer's delivery window, using the same seated sightline as before.",
        "We argued about red paint during the audit meeting, but the immediate request is moving one loading bay. Keep the sightline diagram on page one and alternatives at the back.",
        "Print shop quote for the visibility report is 18 credits for six bound copies. Digital submission is accepted, so only print the two copies needed for the walking inspection.",
        "Duplicate reminder from my pocket notebook: grocer crossing, weekday delivery window, seated-height photographs. The original note is on the kitchen board; keep this copy until the volunteer rota is confirmed.",
        "The latest van photos show an unobstructed view after the loading bay moved temporarily. Add both before and after observations to the crossing report; do not discard evidence that weakens our initial claim.",
    ]),
], [
    (0, 1, "Compare the Elm steps inlet sketch with the canal basin's existing overflow before Thursday. The volunteer crew can explain what clogged last winter, but the permit drawing and towpath planting day remain separate jobs."),
    (2, 3, "North Hall's repair volunteers offered to demonstrate safe hand-tool checks for the South Court locker launch. Add the demonstration to the cafe agenda and the lending proposal without combining their budgets."),
    (4, 5, "The Juniper shade petition and Orchard crossing report both need a seated-accessibility diagram. Reuse the drawing style, then check canopy clearance and van sightlines independently; the two transport requests have different evidence."),
], [
    "A radio interview used 'repair' to describe rebuilding trust after a disagreement. I liked that metaphor and want to remember it for personal journaling; it has nothing to do with broken appliances.",
    "The blue mug's handle feels better than the taller one's when reading at night. If I buy another, look for a wide loop and a matte glaze rather than matching the color.",
    "Finished a fictional detective story in which the missing clock was behind a pantry door. The reveal worked because the author mentioned an unexplained ticking sound early on.",
])


library("university assignments", [
    ("Topology seminar torus presentation", [
        "Topology seminar presentation: use a paper torus to explain why two familiar loops cannot both shrink to points. The assignment is a twelve-minute explanation, with no expectation of a formal homology calculation.",
        "The doughnut photo is too distracting for the opening slide. Start with opposite edges of a square identified, then bring out the paper model when the audience asks where the loops go.",
    ]),
    ("Probability seminar urn simulation", [
        "Probability seminar task is an urn simulation with replacement. Compare the empirical frequency after fifty and five thousand draws; the lecturer cares about variability between runs, not one impressive convergence plot.",
        "I coded sampling without replacement by accident. Fix the urn routine before interpreting the narrowing spread, and retain the old output in the lab notebook as a documented modelling error.",
        "For the probability handout, label each colored line as a separate run. The caption should explain why a short streak does not show that the random generator prefers blue balls.",
    ]),
    ("Material studies indigo swatch report", [
        "Indigo swatch report for material studies: photograph each cotton sample after drying, not straight from the bath. The wet samples falsely suggest that a longer dip always produces a darker final shade.",
        "The dye studio moved our report deadline to Friday because the drying rack was unavailable. Keep the original Tuesday entry visible in the process log and annotate the revised date beside it.",
        "My swatch discussion needs to separate bath duration from repeat dipping. Samples C and D have similar color but different treatment histories, which is the interesting result for this assignment.",
    ]),
    ("Acoustics stairwell impulse experiment", [
        "Acoustics lab: record a single handclap on the second landing of the west stairwell. We need decay time at three microphone distances, with the fire door closed throughout every take.",
        "The first stairwell recording contains footsteps and a door slam after the clap. Mark that take unusable rather than trimming until it looks clean; repeat at the same microphone position.",
        "Reserve the field recorder for Wednesday morning. This is for the landing decay experiment, and a phone's automatic gain adjustment would make the amplitude comparisons difficult to defend.",
        "The west stairwell plot suggests a slower decay at the far microphone. Check whether background ventilation sets the apparent floor before writing that distance changed the room's reverberation time.",
    ]),
    ("Urban history market-map essay", [
        "Urban history essay compares two fictional town market maps from 1820 and 1880. Focus on how stall access changes after the canal bridge appears; avoid claiming that every larger road means more trade.",
        "The map archive caption calls the northern lane 'Fish Row,' while the transcription says 'Firs Row.' Mention the uncertainty in a footnote instead of building the whole market argument on a possible typo.",
        "Office-hours advice: my essay has plenty of map description but no clear claim. Use the shift from water access to cart access as the organizing question, then test it against both dates.",
        "The essay bibliography needs the map sheets as primary sources and the transport chapter as background. I had reversed those categories in the outline; fix the labels before submitting the draft.",
        "A third map complicates the bridge story: carts already reached the west stalls before 1880. Keep the discovery and narrow the claim to the eastern market rather than forcing a tidy narrative.",
    ]),
    ("Interaction design kettle accessibility prototype", [
        "Interaction design assignment: prototype a kettle control panel usable with low vision. The brief concerns selecting temperature and confirming heating status, not redesigning the vessel or claiming the prototype is electrically safe.",
        "Our foam panel has three identical round buttons, so testers cannot identify the temperature control by touch. Try a raised ridge on that button and a different shape for start.",
        "For Friday's kettle critique, bring the paper task cards and audio feedback samples. The tutor asked us to explain why the completion tone differs from the warning tone.",
        "Prototype budget is capped at 35 credits. Borrow the speaker and use cardboard for the housing; buying a real heating element would consume the allowance without helping test the controls.",
        "A tester mistook the long tone for an error, contradicting our first session. Include both reactions in the findings and try spoken confirmation before concluding that tones alone are sufficient.",
        "Copy of the critique reminder: raised ridge on temperature, distinct start shape, and spoken confirmation trial. This repeats my studio note because the team only reads the shared task board.",
        "Final reflection should explain why the kettle panel kept physical buttons despite the sleek touchscreen sketch. The strongest evidence is the low-vision task session, not our preference for a retro appearance.",
    ]),
], [
    (0, 1, "Book the small tutorial room once for the torus rehearsal and urn presentation practice, with separate half-hour slots. Both seminar talks need audience questions, but their handouts and assessment rubrics are different."),
    (2, 5, "The indigo report and kettle prototype both need consistent photographs under the studio lamp. Reserve it for two sessions; dye color accuracy and readable tactile-control documentation require different camera angles."),
    (3, 5, "Borrow the acoustics recorder to compare the kettle prototype's confirmation tones after completing the stairwell takes. Save separate folders so a control-feedback sample cannot be mistaken for a room decay measurement."),
], [
    "A classmate recommended a board game about tiny railways. I only want to remember that the short version uses half the map and finishes before the evening bus, not organize a club tournament.",
    "Shopping note: replace the stretched strap on the laundry bag with cotton webbing. Measure the old loop while the bag is empty, because the knot makes its apparent length misleading.",
    "The campus duck with a white feather slept under the bicycle rack again. This is just a small observation from the walk home, without a research question or course assignment attached.",
])


library("personal travel planning", [
    ("Mere island overnight birding trip", [
        "Mere Island overnight plan: take the early passenger ferry and sleep in the west bunkhouse. The bird hide is only accessible at low tide, so check the crossing window before choosing a return sailing.",
        "The bunkhouse host corrected the key pickup to the pier kiosk, not the village shop. Save that with the island ferry plan; arriving after the kiosk closes would leave us outside.",
    ]),
    ("Mere mainland estuary day visit", [
        "Mere estuary day visit stays entirely on the mainland. Pack the scope and lunch, then use the riverside bus; the island ferry timetable is irrelevant even though the reserve shares the same name.",
        "The mainland reserve's north boardwalk is closed for nesting birds. Move our estuary observation stop to the public screen by the bus terminus and avoid the tempting path across the mud.",
        "Estuary day budget: 14 credits for two bus tickets and no accommodation. The cafe is closed on our chosen Tuesday, so the packed lunch is a real requirement rather than a backup.",
    ]),
    ("Rook city architecture weekend", [
        "Rook City weekend is for the covered arcade walking tour. Reserve the small guesthouse by the tram depot, and leave Sunday morning free for sketching the station roof before checkout.",
        "The arcade guide cancelled the Saturday tour because of roof repairs. A self-guided route through the same district still fits our guesthouse booking; ask whether the courtyard remains publicly accessible.",
        "Use the tram day pass on the architecture weekend. The station and covered arcade are on different lines, and individual fares become more expensive after the third ride.",
    ]),
    ("Sable ridge hut trek", [
        "Sable Ridge trek: reserve two bunks at the saddle hut and plan the climb from the southern trailhead. The northern approach is shorter on the map but crosses an unbridged stream.",
        "Hut caretaker says blankets are supplied but sleeping liners are required. Add liners to the ridge packing list and remove the heavy spare blanket unless the weather changes substantially.",
        "The forecast made us shift the trek from the twelfth to the nineteenth. The hut transfer is confirmed; the old bus booking still needs moving, so keep both dates in the action list.",
        "Trail note from the ridge forum: the final stone steps are exposed, but the hut is below them. Our route ends at the hut, and reaching the summit is optional rather than promised.",
    ]),
    ("Linden lakeside family reunion", [
        "Linden reunion weekend needs a dining room that seats sixteen at one table. The lakeside cabins are convenient, but confirm a ramp to the meal room before paying the group deposit.",
        "The cabin manager sent photos of two entrance steps after saying access was level. Ask for the side-door measurements and keep the contradictory messages together until we can choose a workable room.",
        "Reunion meal poll favors an early supper and a separate quiet breakfast slot. Do not schedule the lake walk during supper preparation, because several people offered to help with both.",
        "The lakeside deposit is 180 credits for all four cabins. Track each household's share privately in our own notes, but the planning board only needs whether the combined payment is complete.",
        "A rainy-day alternative for Linden is the cabin common room with photo albums. Bring sticky labels for identifying places in the pictures, and leave the original photographs unmarked.",
    ]),
    ("Vela rail festival visit", [
        "Vela rail festival trip: the heritage train demonstration is Sunday afternoon, although the model exhibition opens Saturday. Book a return train after the demonstration so we do not leave before the main reason for going.",
        "Our festival lodging is above the bakery two streets from the station. The host warns that morning deliveries start at five; bring earplugs rather than assuming the quiet-stay description means silence.",
        "The model exhibition ticket includes the signal-box tour but not the heritage ride. Set aside 12 credits for the ride, and check whether advance reservations are required on the festival Sunday.",
        "Route planning for Vela: the through train is replaced by a bus on the last leg. Allow the published connection margin and avoid packing the rigid poster tube that will be awkward on the bus.",
        "Correction from the organizer: the heritage demonstration starts at two, not three. That gives us more time before the return service, but change the shared itinerary so nobody wanders off at two.",
        "I saved the signal-box ticket twice, once as a screenshot and once in the itinerary. Both refer to the same Sunday tour; there is only one booking and no extra place to offer anyone.",
        "After the festival, note that the small signal-box tour was better than the crowded model hall. Keep the bus replacement warning with the trip record so next year's planning starts from what actually happened.",
    ]),
], [
    (0, 1, "Pack the same waterproof scope cover for the Mere island overnight and the mainland estuary Tuesday. Their tide notes describe different access points, so copying an entire itinerary would create a dangerous timing mistake."),
    (2, 5, "Compare station-area lodging costs for the Rook architecture weekend and Vela rail festival when updating the travel allowance. Keep the guesthouse deposit and bakery-room deposit on separate lines, because the dates do not overlap."),
    (3, 4, "The sleeping liners from the Sable hut trek can go into the car for the Linden reunion, where bedding is optional. Add them to both packing lists without treating the cabin weekend as part of the hike."),
], [
    "The word 'platform' in a novel referred to a character's public promises, not a station. I underlined the passage because that double meaning made the final conversation much funnier.",
    "Tested a simple lentil soup with smoked paprika and lemon. The lemon belongs at the end; adding it before simmering made the flavor seem dull even with the same ingredients.",
    "Replace the desk lamp bulb with a warmer one next time it fails. The current bright white light is useful for sorting papers but unpleasant when the rest of the room is dark.",
])


library("independent arts projects", [
    ("Paper Moon shadow-play commission", [
        "Paper Moon shadow play needs a crescent puppet that rotates without flashing its support rod. This commission is a seven-minute school performance, so the mechanism must survive quick setup in an ordinary classroom.",
        "The crescent turns cleanly when the hinge sits behind the lower point. Photograph that arrangement before packing the puppet; our classroom operator will have only a short rehearsal before the school performance.",
    ]),
    ("Moon Paper poetry chapbook", [
        "Moon Paper chapbook proof: move the short poem about windows to the inside cover. The title resembles the shadow play, but this is a separate print edition with no puppets or performance rights.",
        "The chapbook printer says the pale gray text disappears on uncoated stock. Request a darker proof of the window poem before signing off the run of eighty copies.",
        "Printing allowance for the poetry edition is 96 credits. A stitched binding looks lovely but exceeds that limit, so test two staples placed far enough from the inner text.",
    ]),
    ("Orchard voices oral-history audio episode", [
        "Orchard Voices audio episode should open with the market bell, then the fictional stallholder's recollection. Leave a pause before narration so listeners can recognize that the scene has changed.",
        "The bell clip includes a gust across the microphone. Keep a short clean strike from the second take and record the edit in the episode log rather than pretending it is one continuous scene.",
        "Audio review moved the stallholder episode release to Monday. The poster still promises Friday, so update the public-facing draft before it goes to the volunteer who schedules the announcements.",
    ]),
    ("Window Seat silent short film", [
        "Window Seat short film: the passenger sees the same yellow umbrella at three stops. Shoot the interior reactions together, but keep the outside light consistent enough that the journey feels continuous.",
        "The borrowed bus is available for two hours on Sunday. Our silent short needs window reflections and empty seats, so prepare the camera angles in advance and skip unnecessary driving shots.",
        "Costume note for the repeated umbrella scene: the passenger's scarf changes position after the second stop. Pin a small continuity photograph to the shot list; nobody will remember the fold accurately.",
        "The film edit currently suggests that two days passed because the final shot is too dark. Try the alternate window take before adding a title card that would change the intended single-journey story.",
    ]),
    ("Dusk courtyard mural", [
        "Dusk mural proposal uses broad silhouettes on the courtyard's rough brick wall. Fine linework will vanish at the viewing distance, so make the sample panel at actual scale before choosing brushes.",
        "Residents prefer the orange sample in shade but the purple sample in afternoon sun. Photograph both at the intended evening viewing time before calling the palette vote final.",
        "The courtyard wall survey found a damp patch behind the planned central figure. Move that part of the composition or wait for the surface repair; extra paint is not a convincing solution.",
        "Mural materials meeting: the scaffolding hire consumes half the allowance. A lower composition would be reachable from the approved platform, but confirm that the altered skyline still reads from the entrance.",
        "Update the painting calendar: surface repairs finish on the twenty-second, so the weekend session cannot start on the twentieth. Keep the original booking note because the platform hire needs a date change.",
    ]),
    ("Lantern chamber-music listening event", [
        "Lantern listening evening pairs a string trio with low paper lights in the east studio. Keep an aisle clear through the cushions and offer chairs at the back for people who cannot sit on the floor.",
        "The trio wants the audience close enough to hear quiet bow sounds. Move the back row forward, then check that the chair users still have an unobstructed view between the paper lanterns.",
        "Event budget: 110 credits for musicians and 25 for refreshments. Borrow the battery lights; purchasing decorative fixtures would mean cutting the fee we already agreed with the trio.",
        "At the rehearsal, the paper lights rattled when the ventilation started. Suspend fewer lanterns and test the room with the fan running before deciding that the soft passages need amplification.",
        "The listening notes should explain when to enter if arriving late. A short pause between pieces is suitable; asking people to wait outside for the entire first half would be unnecessarily unwelcoming.",
        "Copied from the rehearsal card: fan on, fewer hanging lanterns, chairs behind cushions. This is the same room arrangement note, saved again because the printed card may stay with the lighting kit.",
        "After the Lantern evening, record that the close chair row worked and the refreshments queue blocked the exit briefly. Future room plans should move drinks to the side table before the musicians begin.",
    ]),
], [
    (0, 1, "The school asked whether the Paper Moon puppet visit includes copies of Moon Paper. Reply that the shadow performance and poetry edition are separate projects; offer a combined quote only if they explicitly want both."),
    (2, 3, "The market bell from Orchard Voices could mark the bus departure in Window Seat's trailer, although the film itself remains silent. Check the audio episode edit and trailer cue sheet as separate deliverables."),
    (4, 5, "Move the courtyard mural's sample viewing away from the Lantern trio rehearsal. Both need the east studio entrance kept clear that evening, but the paint vote and listening event have independent attendance lists."),
], [
    "My bicycle bell has a pleasant low ring but the clamp slips on wet handlebars. Put a thin rubber strip beneath it before tightening; this is a small home maintenance reminder.",
    "I finally understood the card game's scoring: unused tokens count against you only after the third round. Remember that detail next time rather than inventing a new house rule halfway through.",
    "A jar of loose buttons looks surprisingly like a tiny mosaic when sunlight comes through it. Keep the observation for a personal sketch someday; there is no commission or current artwork attached.",
])


library("small software prototypes", [
    ("Pebble pantry expiry prototype", [
        "Pebble pantry prototype should let someone record an opened jar without knowing the purchase date. Distinguish an unknown date from today's date, otherwise the shelf view will confidently show misleading freshness information.",
        "The kitchen test found that people search for 'opened' before looking for expiry. Put the opened-date control above the optional best-before field in the jar entry form, then repeat that task.",
    ]),
    ("Pebble reading queue browser extension", [
        "Pebble reading queue extension saves article titles locally and needs a keyboard shortcut for the next unread item. This is the browser experiment, unrelated to the pantry prototype that happens to share its working name.",
        "The reading popup closes while someone renames an article. Keep the edit in a draft until saved, and restore it when the popup reopens so a stray click does not destroy the work.",
        "Extension review: importing a saved reading list twice creates duplicate entries. Compare normalized URLs before adding items, but preserve the user's edited title on the existing entry.",
    ]),
    ("Tern rehearsal-room booking demo", [
        "Tern booking demo is for a single rehearsal room with a fixed cleanup gap. Show occupied time and cleanup time differently so a musician understands why the apparently empty fifteen minutes cannot be booked.",
        "The booking workshop found that a canceled rehearsal still blocks its cleanup gap. Remove the associated gap when canceling, and show a clear confirmation containing the date and room name.",
        "A second organizer wants recurring reservations in Tern. Log that as a later request; the current demo must first handle one-off cancellations correctly before expanding the booking rules.",
    ]),
    ("Moss balcony watering reminder", [
        "Moss reminder trial groups plants by balcony exposure, not by species name. A shaded basil pot dries differently from the sunny one, and the notification should say which side to inspect.",
        "The watering prototype sent its morning reminder after I had already marked the pots checked. Cancel pending reminders when the check is recorded, including from a second open tab.",
        "Notification wording review: say 'check the soil' rather than 'water now.' Our trial has no moisture sensor, so the app should not act as if it knows whether every pot needs water.",
        "Moss test schedule changes from daily to alternate mornings next week. Retain the earlier daily setting in the experiment notes, since comparing interruption rates depends on knowing when the schedule changed.",
    ]),
    ("Kite invoice export utility", [
        "Kite invoice export needs a plain CSV for the cooperative's treasurer. Preserve leading zeros in reference numbers through an explicit text column, and make the preview show exactly which fields will leave the app.",
        "The export sample treated an empty amount as zero. Keep missing amounts visibly blank and warn before creating the file; a zero-value invoice and an incomplete invoice mean different things.",
        "Treasurer feedback: sort the invoice preview by issue date, with undated drafts at the bottom. Alphabetical customer order makes it harder to compare the file against the monthly ledger.",
        "Cost note for Kite: the paid export widget adds nothing we need. The existing table formatter supports quoted commas already, so spend the prototype budget on a proper usability session instead.",
        "Regression example from the invoice demo: a customer label beginning with an equals sign must export as literal text. Keep that sample in the checklist even though most demonstration names are ordinary words.",
    ]),
    ("Drift volunteer shift swap board", [
        "Drift shift board allows volunteers to offer a shift and another person to accept it. The original owner remains responsible until acceptance completes; posting an offer must not immediately erase their assignment.",
        "Two testers accepted the same shift simultaneously. The board showed both as successful, so the acceptance operation needs one authoritative winner and a useful explanation for the other person.",
        "The swap-board walkthrough should include a volunteer who cannot take evening shifts. Show the time before the accept button and keep their availability note visible while they compare offers.",
        "Our organizer meeting rejected a public leaderboard for accepted swaps. Helping cover a shift is enough; the board should focus on uncovered work and avoid turning schedule flexibility into a competition.",
        "Drift trial moved from the library volunteers to the food-bank volunteers after room access fell through. The product experiment is still the same shift-swap trial, with a different participating group.",
        "I pasted the simultaneous-acceptance bug into my phone notes as well as the board: two success messages, one available shift. These describe the same test failure, not a second incident.",
        "The closing trial report should distinguish completed swaps from offers that expired. Counting every posted offer as a success exaggerated usefulness, especially for the unpopular late-evening shifts.",
    ]),
], [
    (0, 3, "Compare the pantry's unknown dates with Moss's unsensed soil state before writing confidence copy. Both prototypes need honest uncertainty, but jar storage and balcony checks require separate fields and user tests."),
    (1, 4, "Reuse the reading extension's import preview layout for Kite's invoice export preview. The first resolves duplicate URLs and the second exposes financial fields, so their validation messages cannot simply be copied."),
    (2, 5, "Bring the Tern cancellation problem and Drift simultaneous-acceptance failure to the concurrency review. One releases a room slot and the other transfers a shift; document separate acceptance rules for each demo."),
], [
    "The old wooden kite in the cupboard has a split spar near the tail. This is a childhood toy, and I only need to measure the broken piece before deciding whether to mend it.",
    "A documentary showed how salt crystals grow around a dangling string. I want to remember the slow close-up shots and the simple lighting, without starting another science project this month.",
    "The new corner bakery sells a dark rye loaf that stays good for several days. Slice and freeze half next time; buying two whole loaves at once was excessive for my kitchen.",
])


library("museum conservation", [
    ("Aster gallery lacquer screen treatment", [
        "Aster gallery's lacquer screen has lifting edges around the lower gold cloud. Test the proposed consolidant on the detached study fragment before treating the screen; a shiny repair would be visible under exhibition lights.",
        "The study fragment darkened after the second consolidant application. Record that result beside the gold-cloud treatment proposal and pause the lower-edge work until a less visible method is approved.",
    ]),
    ("Aster study room paper screen mount", [
        "Aster study room's paper screen needs a new mount for teaching sessions. Despite the similar inventory description, it is a modern folding study object, not the lacquer screen in the gallery.",
        "The teaching screen's replacement hinges should allow it to lie partly open without tension. Ask the mount maker for a mockup with scrap board before cutting the final support.",
        "Study room budget review: reuse the existing storage box if the new paper-screen mount fits. A larger box would consume the allowance reserved for hinges and corner supports.",
    ]),
    ("Blue vessel salt-monitoring campaign", [
        "Blue vessel monitoring begins with weekly photographs of the white deposits near its foot. Mark the camera position on the bench so lighting changes cannot be mistaken for new salt growth.",
        "The newest vessel image looks cleaner because someone rotated the pot. Repeat the photograph at the bench mark and note the rotation in the monitoring log before judging the deposit trend.",
        "Conservation meeting moved the blue vessel checks from weekly to twice weekly during the humidity change. Keep the earlier schedule in the record; the different intervals matter when comparing deposit growth.",
    ]),
    ("Dock ledger digitization batch", [
        "Dock ledger digitization covers the six volumes with brittle blue covers. Use the cradle at a shallow opening angle, and capture folded inserts separately before they obscure the writing near the gutter.",
        "The second ledger has a page numbered 47 twice. Preserve both images and add a distinguishing suffix in the image index; renumbering the historical pages would conceal a feature of the source.",
        "Scanning estimate for the dock books must include the foldout handling time. The supplier's per-page quote assumed flat sheets, so the first budget understates the labor substantially.",
        "Quality check found a thumb covering the last word on two ledger images. Request replacement captures for those pages while retaining the rejected files in the batch's audit record.",
    ]),
    ("Amber textile light-exposure rotation", [
        "Amber textile rotation will alternate two embroidered panels in the small display case. Calculate exposure separately for each panel; changing which one is visible does not reset either object's accumulated light history.",
        "The case meter was facing the ceiling during Monday's reading. Repeat it at textile height and annotate the invalid reading rather than using it to justify a longer display period.",
        "Curatorial review favors showing the repaired hem on the first panel. Adjust the mount drawing so the support leaves that detail visible, while the rotation schedule still protects the more sensitive thread.",
        "Our textile rotation handover was listed for the ninth, but gallery closure now starts on the eleventh. Correct the case-access booking and retain the old date in the movement log.",
        "Visitors asked why the second embroidered panel disappeared after a month. Add a plain explanation of light exposure beside the case, without implying the hidden panel is damaged beyond display.",
    ]),
    ("Copper automaton loan preparation", [
        "Copper automaton loan requires a transport support that restrains the base without touching the moving bird. Document its resting position before anyone designs foam cutouts around the mechanism.",
        "The receiving museum wants a daily demonstration, but our loan proposal currently permits static display only. Keep that request with the condition notes and seek a decision before finalizing the agreement.",
        "Packing meeting: the automaton's case needs an indicator showing if it tipped during transit. Ask for an external window so staff can inspect the indicator without opening the sealed inner support.",
        "The loan freight quote excludes the courier's overnight stay. Add that cost to the copper bird budget before comparing carriers; the cheapest listed transport price is not the complete trip cost.",
        "Condition photography found a scratch beside the base screw that appears in an older image too. Mark it as pre-existing in the automaton report rather than attributing it to the packing rehearsal.",
        "Copy from the loan checklist: base restrained, moving bird untouched, tip indicator visible. I saved the same packing constraints in my travel notebook because the courier will not carry the full design folder.",
        "The lender approved one supervised automaton demonstration at installation, replacing the static-only plan. Preserve both versions of the instruction and make the single demonstration limit prominent on the courier sheet.",
    ]),
], [
    (0, 1, "Ask the mount maker to inspect the lacquer screen's edge clearance and the teaching paper screen's hinge mockup on the same visit. They are distinct objects in different rooms and need separate treatment records."),
    (2, 4, "The blue vessel's deposit checks and Amber textile readings can share a humidity logger during the case trial. Keep photographs of salt growth separate from exposure totals; the measurements answer different conservation questions."),
    (3, 5, "The dock ledger cradle supplier also quoted for the copper automaton's transport support. Compare material specifications in one procurement meeting, but issue separate orders tied to the scanning batch and outgoing loan."),
], [
    "The word 'conservation' on the cereal box refers to energy savings in manufacturing. I clipped the wording because the claim is vague, not because it belongs to any museum treatment file.",
    "Home reminder: the curtain ring nearest the window catches on a small burr in the rail. Smooth that spot before replacing the rings; the rest of the curtain moves freely.",
    "A friend described a dream about a staircase made of folded newspapers. I liked the image and wrote it down after lunch, with no plan to turn it into an exhibition concept.",
])


library("experimental agriculture", [
    ("East plot barley sowing-depth trial", [
        "East plot barley trial compares shallow and deep sowing in alternating strips. Count emergence before the first fertilizer application so the treatment comparison is not muddled by different nutrient timing.",
        "A marker fell over between the two eastern strips. Recover the sowing-depth assignment from the field sketch before counting seedlings; guessing from emergence density would bake the expected result into the data.",
    ]),
    ("West plot barley cover-crop trial", [
        "West plot barley follows two different winter covers, with the same sowing depth throughout. The question is carryover from the cover crop, not the depth comparison happening across the lane.",
        "The west trial's clover strips stayed wetter after rain than the rye strips. Record soil moisture alongside emergence, because a simple cover-label comparison will miss a plausible reason for the difference.",
        "Seed order for the cover-crop follow-up needs equal barley quantities for both previous covers. Do not reuse the east plot's shallow-versus-deep bag labels, even though the cultivar is identical.",
    ]),
    ("Glasshouse tomato shade-cloth test", [
        "Tomato shade test uses two cloth densities over the glasshouse benches. Rotate the temperature sensors between benches after calibration, while keeping the plants under their assigned cloth throughout the trial.",
        "The sensor beneath the heavier cloth read high even in the calibration tray. Replace that unit and flag its earlier tomato readings; the apparent cooling failure may be an instrument problem.",
        "Shade-cloth review moved harvest weighing to Thursdays. Keep the previous Wednesday dates in the tomato log so the extra growth day is visible when comparing the first and second harvest totals.",
    ]),
    ("Blue shed oyster mushroom substrate test", [
        "Blue shed mushroom test compares straw and wood-chip substrate in identical hanging bags. Label inoculation dates clearly and keep the ventilation setting fixed while the first flush develops.",
        "One straw bag was tied much tighter than the others and stayed visibly wet. Mark it as a handling deviation before weighing, rather than quietly treating the yield as a clean substrate comparison.",
        "The oyster mushroom allowance covers twenty bags and a replacement shelf. Borrow the weighing scale from the packing room, since buying another would reduce the number of replicate bags.",
        "Harvest notes from the blue shed: the wood-chip bags started later but produced a second flush sooner. Compare cumulative yield as well as first-pick weight before selecting a substrate.",
    ]),
    ("North orchard pear pollination survey", [
        "North orchard pear survey counts visits to tagged blossom clusters during three fixed observation windows. Record insects landing on flowers separately from insects merely flying past, using the same rule for every tree.",
        "Wind cancelled the noon pollinator count, while the morning count went ahead. Leave noon as missing in the pear sheet; zero would wrongly imply that an observer saw no visits.",
        "Field meeting decided to add a sheltered row to the blossom survey. Mark it as an added stratum rather than pooling it invisibly with the exposed trees from the original plan.",
        "The pear observation cards need larger spaces for time and cloud cover. Volunteers filled the margins with weather notes, which shows those fields matter more than our decorative orchard header.",
        "Flower tags faded after the shower. Replace them using the branch photographs from the first survey day, keeping the original cluster identifiers so repeat visits still refer to the same blossoms.",
    ]),
    ("Stone tank irrigation emitter audit", [
        "Stone tank emitter audit measures catch volume at the start, middle, and end of each drip line. Run the system for the same interval every time, and note pressure before collecting the cups.",
        "The far line gave a small catch because its valve was half closed. Record that setup error and repeat the run before diagnosing blocked emitters across the whole irrigation zone.",
        "Audit purchase list: sixty identical cups and a measuring jug with readable marks. Mismatched kitchen containers make spills and volume comparisons harder, so this small expense is justified.",
        "The irrigation contractor wants our line diagram before visiting. Include the stone tank, slope direction, and valve positions; the crop labels are less useful for tracing pressure loss.",
        "Yesterday's note blamed clogged emitters, but cleaning them did not improve the end cups. Keep that failed intervention in the audit record and test pressure loss along the uphill section next.",
        "Duplicate field reminder: same run interval, pressure first, three positions per drip line. This copies the laminated audit card because the card is currently drying after falling into a collection bucket.",
        "Closing irrigation report should distinguish the corrected half-open valve from the unresolved uphill pressure drop. They happened in one audit but require different actions, and averaging the catches hides both.",
    ]),
], [
    (0, 1, "The east depth trial and west cover-crop trial need barley emergence counts on the same morning. Share the click counters, but use separate field sheets so identical cultivar names do not mix the treatments."),
    (2, 3, "Book the packing-room scale for Thursday's tomato harvest and Friday's mushroom flush. Shade density and substrate type are separate experiments, even if the shared equipment calendar lists both as harvest weighing."),
    (4, 5, "Avoid running the stone-tank drip audit during the pear blossom observation windows. The contractor's movement through the north orchard could disturb insects; coordinate timing while preserving separate survey and maintenance records."),
], [
    "The old radio's tuning knob slips unless I turn it slowly clockwise. Remember that quirk before assuming the station has gone off air; the set still sounds clear once tuned.",
    "I tried folding a fitted sheet by following the elastic corners inward. The result is not tidy, but it stacks better and no longer pushes the cupboard door open.",
    "A poem compared patience to a seed beneath snow. Save the line's idea for a reading journal; it is a metaphor I enjoyed, not an observation from any of the field trials.",
])


library("harbor operations", [
    ("North beacon battery replacement", [
        "North beacon service replaces the corroded battery tray during the low-water access window. Photograph the cable routing before disconnecting anything, because the drawing in the cabinet shows an older terminal layout.",
        "The new tray fits, but the lid presses against the positive cable when closed. Pause the beacon reassembly and revise the routing sketch before the next low-water visit.",
    ]),
    ("South beacon lens-cleaning visit", [
        "South beacon visit is for salt film on the lens, with no battery work planned. Bring the approved cleaning cloths and check the landing ladder; the north station's electrical parts list does not apply.",
        "The south landing ladder inspection moved the cleaning boat departure to noon. The earlier tide note remains useful, but replace the nine-o'clock meeting instruction so the crew does not wait at the quay.",
        "Lens inspection after cleaning still shows a faint cloudy band inside the glass. Record it for the south beacon specialist rather than repeatedly polishing the outside and claiming the visit solved everything.",
    ]),
    ("Basin C sediment survey", [
        "Basin C sediment survey uses five repeated sounding transects near the grain berth. Save the tide correction with every run so a change in water level does not masquerade as movement of the bed.",
        "The third transect zigzagged while the survey boat avoided a tug. Repeat that line on the planned bearing and keep the interrupted run marked as unsuitable for the regular cross-section comparison.",
        "The sediment report needs a note that the western mound appears in last season's survey too. Our current measurements refine its extent; they do not establish that the mound formed this month.",
    ]),
    ("Harbor seal ferry boarding-ramp refit", [
        "Harbor Seal ferry refit replaces the passenger ramp's worn hinge bushings. Measure lateral play before removal and after installation, with the ramp at the same angle for both readings.",
        "The ramp supplier quoted the wrong bushing diameter from a sister vessel's drawing. Send the measured dimensions and hold the order until the replacement quote identifies Harbor Seal explicitly.",
        "Refit meeting approved a temporary shore walkway while the ferry ramp is out. Check the handrails and turning space before posting the passenger diversion signs at the terminal entrance.",
        "The final ramp test showed less lateral movement but a new squeak at full extension. Keep the squeak in the refit punch list; meeting the clearance target does not close every defect.",
    ]),
    ("Quay 4 spill-response drill", [
        "Quay 4 drill simulates a small fuel spill using floating markers, never actual fuel. Assign observers to record boom deployment and communication delays without interrupting the response team's decisions.",
        "The drill radio call used the wrong berth number, sending the support cart to Quay 2. Include the confusion in the debrief and test whether repeating the location prevents a recurrence.",
        "Equipment allowance for the spill exercise includes replacement gloves and marker floats. The reusable boom is borrowed from stores; list its return inspection so the drill does not leave response gear unavailable.",
        "The exercise date changed from the sixth to the thirteenth because a cargo call now occupies the quay. Update the observer invitations and preserve the superseded schedule for the equipment booking adjustment.",
        "Debrief wording should separate time to recognize the marker spill from time to close the boom. A single total made it impossible to see that communication improved while deployment remained slow.",
    ]),
    ("East channel fog-signal trial", [
        "East channel fog-signal trial compares two pulse patterns from the temporary horn. Listening stations need synchronized watches and a clear way to record an unheard signal, not just whichever pattern they think they heard.",
        "The bluff station reported pattern B during a silent interval. Keep that false detection in the trial sheet; excluding it would make the horn seem easier to identify than it was.",
        "The harbor meeting wants a quieter night pattern, but our current trial runs only in daylight. Record the request as untested rather than claiming the daytime listening results settle nighttime disturbance.",
        "Transport costs for the horn trial include a boat trip to the outer listening station. Share that trip among observers, while allowing enough time to establish positions before the first scheduled pulse.",
        "Wind shifted midway through the east-channel test. Split the analysis by the observed wind period and retain the full sequence, because comparing only the best interval would favor one pulse pattern unfairly.",
        "Copied horn-trial instruction: synchronized watches, record silence, mark false detections. The same wording is on the station cards; this phone copy is for the observer whose card blew into the boat well.",
        "The revised listening plan adds a landward station after residents described echoes between warehouses. This extends the same fog-signal trial, and the earlier offshore observations should remain in its evidence set.",
    ]),
], [
    (0, 1, "The workboat can carry the north beacon battery tray and south beacon lens kit on one circuit. Keep separate station checklists; a successful cleaning visit cannot certify the electrical work at the other beacon."),
    (2, 5, "The Basin C survey crew can place the outer fog-trial observer after finishing the sounding transects. Coordinate boat time, but do not mix tide-corrected depth records with the east-channel listening sheets."),
    (3, 4, "The temporary walkway for Harbor Seal's ramp refit narrows the approach used by Quay 4's spill cart. Check both plans together before the drill, then record any walkway change in the refit file."),
], [
    "The phrase 'safe harbor' in a puzzle clue meant a sheltered feeling rather than a dock. I missed the wordplay because I kept searching for a coastal place name.",
    "A neighbor's sourdough recipe uses a small covered pot for the first half of baking. Try the method with an ordinary loaf someday, after checking whether my pot handle tolerates oven heat.",
    "The hallway clock gains about two minutes each week. Set it back when watering the houseplants on Sunday; replacing it seems unnecessary while the habit is easy to remember.",
])


library("community sports coaching", [
    ("River junior rowing starts clinic", [
        "River juniors' starts clinic practices the first five strokes in stable training boats. Keep the focus on coordinated timing, and stop each attempt before speed makes the beginners rush their hand movements.",
        "The rowing coach wants a side-view video of one clean start and one rushed start. Use those during the clinic recap, with the same five-stroke limit so the comparison stays understandable.",
    ]),
    ("River masters rowing endurance block", [
        "River masters' endurance block uses steady twenty-minute pieces at conversational effort. This is a six-week adult training block, separate from the juniors' short starts clinic despite sharing the boathouse.",
        "The masters moved Wednesday's steady row indoors after high water closed the river. Keep the session in the endurance log, but label the machine workout so distance is not compared directly with boat distance.",
        "Review of the adult block: attendance stayed high when the steady pieces had a short break between them. Preserve the moderate effort target rather than turning the break into permission for sprinting.",
    ]),
    ("Hill court beginner wheelchair-tennis taster", [
        "Hill Court tennis taster needs wide turning space behind the baseline and a rack of lighter practice balls. Confirm that the equipment route from reception is step-free before sending the participant information.",
        "The chair storage room door is narrower than the accessible entrance shown on the map. Move the loan equipment to the court-side room for the tennis taster, and update the volunteer setup sheet.",
        "Taster budget covers two assistant coaches and loan chair transport. Borrow the ball basket from the club so the small remaining allowance can fund large-print direction signs.",
    ]),
    ("Harbor novice fencing footwork course", [
        "Harbor fencing beginners will practice advance and retreat along floor tape before using weapons. The four-session course needs clear stopping signals and enough spacing that adjacent pairs do not drift together.",
        "The first footwork class confused 'retreat twice' with a single long step. Demonstrate two balanced movements slowly, then have partners describe what they see before increasing the pace.",
        "Venue change for the novice fencing course: the mirrored studio is unavailable next Tuesday. Use the upper hall, checking that its floor tape lifts cleanly and the longer room still allows visible signals.",
        "Course reflection should mention that beginners improved balance but still crossed their feet when distracted. Keep that limitation in the final note rather than claiming four sessions produced reliable match-ready footwork.",
    ]),
    ("Cedar recreational running relay", [
        "Cedar relay planning uses short loops so slower recreational runners spend less time isolated. Each team chooses its own order, but the exchange area needs one clear entrance and one exit.",
        "The loop marshal found a loose paving slab beside the second turn. Shift the marked route onto the adjacent smooth path and remeasure it before publishing an exact distance.",
        "Relay meeting favored reusable number belts over pins. Price enough belts for the active runners rather than every team member, since they can pass the belt during the exchange.",
        "Correct the Cedar event date to the twenty-fifth; the park permit names that Saturday, while our draft invitation says the eighteenth. Contact the team organizers with the correction before they arrange travel.",
        "Rain plan for the relay is a shorter paved loop, not cancellation at the first shower. Write the route-change decision time into the marshal sheet so everyone gives teams the same information.",
    ]),
    ("Slate pool adult swimming confidence series", [
        "Slate Pool confidence series begins in the shallow lane with comfortable face immersion. Participants can decline any exercise, and instructors should describe the next step before asking someone to move away from the wall.",
        "The second pool session went better when the instructor demonstrated breathing at water level. Add that to the lesson card, keeping the option to watch without joining until the swimmer feels ready.",
        "Series budget needs a second instructor for the first two weeks. Smaller groups at the wall matter more than buying extra floats, especially while everyone learns the room and entry steps.",
        "The pool manager offered the deep lane after a booking change. Decline it for this stage of the confidence series; our current exercises rely on participants being able to stand comfortably.",
        "My earlier note says every participant floated independently, but the assistant reports two still used hand support. Correct the progress summary and retain the initial note so the source of the overstatement is clear.",
        "Duplicate lesson reminder from the waterproof card: demonstrate breathing at water level, explain first, allow watching. I saved it again here because the shared pool clipboard is often returned to reception.",
        "At the final confidence session, several swimmers asked for a gentle continuation group. Record that request separately from completion of the current series; attendance alone should not be described as competence in deep water.",
    ]),
], [
    (0, 1, "The juniors' starts clinic and masters' endurance block need the same two training boats on Wednesday. Resolve the timetable at the boathouse, while retaining separate session plans for coordinated starts and sustained effort."),
    (2, 5, "Compare the Hill Court taster's arrival directions with Slate Pool's first-session guide. Both need clear access information, but the tennis equipment route and shallow-pool entry are different checks at different venues."),
    (3, 4, "The fencing course can lend its floor-tape dispenser for Cedar's relay briefing room. Put return time in both equipment lists, since the footwork lesson and running event occur on consecutive evenings."),
], [
    "The phrase 'running a bath' confused the language learner in the comedy scene. I saved the joke because the character arrived in sports clothes carrying a stopwatch, which made the misunderstanding wonderfully literal.",
    "The tomato sauce tasted sweeter after the onions cooked slowly, even without sugar. Leave enough time for that step next time instead of trying to repair the flavor at the end.",
    "My umbrella opens correctly but will not stay closed unless the strap is pulled tight. Replace the worn hook-and-loop patch when I mend the coat pocket this weekend.",
])


library("observatory research operations", [
    ("Lumen telescope mirror wash", [
        "Lumen mirror wash requires a clean drying rack before the primary mirror comes out. Photograph the support clips and mark their positions on the worksheet so reassembly preserves the existing orientation.",
        "The drying rack test left fibers on a spare glass plate. Replace the cloth supports before the Lumen wash; a scheduled maintenance morning is not a reason to proceed with a contaminated setup.",
    ]),
    ("Lumen finder alignment session", [
        "Lumen finder alignment session uses a distant daytime target before checking a bright star at dusk. This is a pointing adjustment only; the separate primary-mirror wash has its own maintenance procedure.",
        "The finder crosshair drifts when its bracket screw is tightened. Record the offset before and after tightening, then repeat the daylight target check rather than compensating by eye at night.",
        "Alignment session moved to the western terrace because a new banner blocks the usual tower target. Save the alternate sightline with the finder worksheet so the next daytime check can repeat it.",
    ]),
    ("Cinder variable-star cadence study", [
        "Cinder star study tests whether alternating short and long gaps recover the suspected brightness cycle. Keep exposure length constant during this cadence comparison, and log cloud interruptions instead of silently filling missing points.",
        "The apparent dimming coincides with a passing thin cloud in the guide image. Flag those Cinder measurements for review and compare the reference stars before describing a new minimum.",
        "Study meeting chose another two nights of the alternating-gap schedule. The first night's curve is suggestive but not enough to distinguish a true cycle from the sampling pattern we imposed.",
    ]),
    ("Rill asteroid occultation attempt", [
        "Rill occultation attempt needs a continuous timestamped video around the predicted event. Confirm the camera clock before setting up, because a beautiful disappearance recording is not useful if its timing cannot be trusted.",
        "The camera displays local time while the event sheet uses UTC. Put both clearly on the occultation checklist and verify the conversion before deciding when to start the continuous recording.",
        "Travel allowance for the occultation covers the eastern roadside site and a backup location farther south. Check the horizon photographs before choosing; the cheaper site is useless if a ridge hides the target.",
        "No disappearance appears in the Rill video, but the timing check passed and the target stayed visible. Save the negative observation with the weather notes; an unsuccessful prediction is still a valid observation.",
    ]),
    ("Aurora all-sky camera condensation trial", [
        "Aurora camera trial compares two low-power heater settings beneath the clear dome. Record condensation and sky background together, because a dry dome is not enough if the heater causes visible image artifacts.",
        "The higher setting cleared droplets but produced a bright reflection near the frame edge. Keep both effects in the camera trial log, then test whether repositioning the cable changes the reflection.",
        "Purchase review for the dome experiment: a second temperature probe costs less than another heater. Add the probe near the rim so we can tell whether the persistent droplets follow a colder region.",
        "The trial calendar originally ended on the tenth, but dry weather gave us no useful condensation nights. Extend to the seventeenth and retain the original end date in the experiment history.",
        "After the cable moved, the edge reflection remained. Do not label the change a fix; compare the dome's interior surfaces during the next daylight inspection before choosing another intervention.",
    ]),
    ("Cobalt spectrograph wavelength calibration", [
        "Cobalt calibration maps lamp lines onto the spectrograph's detector columns. Start with isolated lines across the full sensor, and keep the crowded central blend out of the initial fit.",
        "One reference line was identified from a neighboring peak rather than its true center. Correct that label and compare residuals before increasing the polynomial order to conceal the mismatch.",
        "Calibration review asks for separate residual plots before and after the overnight temperature change. A single combined scatter plot hides whether the instrument drifted consistently in one direction.",
        "The lamp supplier's quote includes a mounting bracket we already have. Remove that duplicate cost from the Cobalt maintenance estimate and confirm the replacement lamp still fits the existing socket.",
        "Our first note says the calibration is stable across the detector, but the far-red residuals disagree. Keep the earlier conclusion in the log and narrow the valid range until more isolated lines are measured.",
        "Copied calibration warning: avoid the central blend and inspect the far-red residuals. This repeats the bench note in the night operator's checklist, since the bench notebook stays in the instrument room.",
        "The extra lamp exposure found two usable lines beyond the old valid range. Update the wavelength solution with a versioned result and retain the earlier fit so processed observations can be traced to their calibration.",
    ]),
], [
    (0, 1, "Schedule the Lumen finder alignment after the mirror has been washed and reinstalled. The maintenance and pointing tasks need separate completion checks, even though removing the mirror makes their order important."),
    (2, 4, "Aurora's sky camera images may help flag cloudy intervals in the Cinder brightness study. Link the relevant frames to the star observations while keeping heater-setting evaluation in the camera trial record."),
    (3, 5, "Reserve the timing checker for the Rill occultation and the temperature logger for Cobalt calibration on the same equipment form. These instruments support different measurements, so retain separate verification instructions and return times."),
], [
    "The ceramic star on my key ring broke at one point. I kept the pieces because the glaze is an unusual green, but this is a personal keepsake rather than an observatory instrument part.",
    "A radio drama used silence after a door shut to imply that the visitor had vanished. Remember how effective that pause was; the script never needed to explain the disappearance aloud.",
    "The narrow bookshelf leans slightly because one floorboard is lower. A thin wooden shim stopped the wobble during cleaning, so measure it before trying a permanent replacement foot.",
])


library("Spanish/English culinary teaching and service", [
    ("Brisa Saturday bread-shaping workshop", [
        "Taller Brisa del sábado: practicar el formado de barras con masa ya fermentada. Necesitamos una mesa baja para quienes trabajan sentados; el objetivo es aprender los movimientos, no terminar una receta completa desde cero.",
        "The bread-shaping table can be lowered by removing its risers. Save a photograph of that setup for Saturday, and divide the fermented dough before participants arrive so the demonstration starts on time.",
    ]),
    ("Brisa Sunday sourdough starter clinic", [
        "La clínica Brisa del domingo trata del cuidado de la masa madre, no del formado de barras. Pedir tarros transparentes y enseñar cómo marcar el nivel después de alimentar cada cultivo.",
        "Sunday's starter clinic needs a simple handout showing rise and fall in the jar. Explain that a photograph at one moment cannot tell whether the starter is still rising or has already collapsed.",
        "Cambio para la clínica del domingo: empezar a las once, no a las diez. La cocina estará ocupada hasta las diez y media; corregir el mensaje enviado junto con la lista de tarros.",
    ]),
    ("Nube sensory tasting lesson", [
        "Nube tasting lesson compares aroma descriptions using covered cups of familiar ingredients. Ask learners to describe what they notice before revealing the contents, and avoid presenting one poetic description as the only correct answer.",
        "En la clase de aromas, dos personas confundieron canela con clavo. Guardar ambas respuestas y preguntar qué detalle percibieron; corregirlas inmediatamente habría borrado una conversación útil sobre las diferencias.",
        "Presupuesto de Nube: reutilizar las tazas opacas y gastar el resto en tapas que cierren bien. Las muestras perdieron olor durante la espera, lo que dificulta comparar las respuestas de los grupos.",
    ]),
    ("Piedra lunch-service menu redesign", [
        "Piedra lunch menu redesign needs two dishes that share preparation without tasting identical. The small kitchen has one oven, so the service sequence matters as much as the printed descriptions.",
        "La prueba del menú dejó el horno ocupado cuando llegaban los pedidos de verduras. Adelantar el asado de la base y comprobar cómo queda al recalentar antes de cambiar los tiempos de servicio.",
        "Menu meeting rejected the phrase 'allergy safe' because the shared kitchen cannot support that promise. List ingredients clearly and explain how diners can ask about preparation before choosing a dish.",
        "El folleto de Piedra todavía muestra el precio anterior del almuerzo. La revisión subió dos créditos por el nuevo acompañamiento; conservar el cálculo viejo, pero sustituir el borrador antes de imprimir.",
    ]),
    ("Faro winter soup supper", [
        "Cena de sopas Faro: servir tres ollas en estaciones separadas para que la cola no bloquee la puerta. Las tarjetas deben indicar ingredientes y permitir leerlos antes de tomar un cuenco.",
        "For the winter soup supper, borrow insulated serving pots from the community kitchen. Check their capacity against the expected portions instead of assuming three pots automatically cover three recipes for everyone.",
        "La reunión de Faro cambió la cena del viernes al sábado por un corte de agua. Actualizar la reserva de ollas y mantener la fecha anterior en la nota del préstamo para explicar el cambio.",
        "The supper's decoration allowance is only 15 credits after bowl rental. Use the existing paper stars and spend the remainder on clear ingredient signs, which guests actually need at the serving stations.",
        "Después de la cena, anotar que la sopa de lentejas se acabó primero y que la estación central creó atasco. Son observaciones para el informe del mismo evento, no propuestas para otra cena.",
    ]),
    ("Oliva recipe translation booklet", [
        "Oliva booklet translates six family-style recipes between Spanish and English for a fictional cooking exchange. Keep the instructions usable in either language and explain ambiguous vessel names rather than replacing them with literal dictionary matches.",
        "En el cuadernillo, 'una taza' aparece sin tamaño en la receta de arroz. Pedir una medida concreta al autor ficticio; no convertir automáticamente a mililitros con una suposición que cambie la proporción.",
        "The translation review found that 'simmer' became a phrase meaning vigorous boiling. Correct the bean recipe and check the surrounding timing instructions, since the wording error changes the actual cooking method.",
        "Reunión editorial de Oliva: poner las dos lenguas en páginas enfrentadas y alinear los pasos numerados. Así las parejas pueden cocinar juntas sin buscar una instrucción equivalente en otra sección del libro.",
        "Printing quote for the bilingual recipe booklet covers twenty-four pages, but the facing-page layout needs twenty-eight. Update the cost before approving the design; shrinking the ingredient text would make the kitchen copy harder to use.",
        "Copia de mi nota de revisión: aclarar el tamaño de taza y corregir el hervor suave de las alubias. Son los mismos dos problemas del cuadernillo que dejé apuntados en la mesa editorial.",
        "The final Oliva proof should retain the earlier translation correction in the editorial record. The printed page needs only the usable instruction, while the record explains why the cooking time changed during review.",
    ]),
], [
    (0, 1, "Reservar la cocina para el formado de pan del sábado y la clínica de masa madre del domingo en líneas separadas. Comparten Brisa y algunos utensilios, pero cada taller tiene participantes, horario y objetivo propios."),
    (2, 5, "The Nube aroma class can review descriptive words in Oliva's translated recipes. Save suggestions in both the lesson notes and booklet edits, while keeping sensory observations distinct from corrections to cooking instructions."),
    (3, 4, "Piedra puede prestar sus soportes de menú para las tarjetas de ingredientes de Faro. Apuntar la devolución después de la cena; el rediseño del almuerzo del local continúa como trabajo independiente del evento."),
], [
    "Vi una nube con forma de barco al volver a casa. La apunté por el contraste entre el cielo gris y un borde dorado, sin relación con ninguna clase ni actividad de cocina.",
    "The drawer beside my bed squeaks only when nearly closed. A folded scarf was rubbing against the back panel; moving it solved the noise without any tools or replacement hardware.",
    "Para mi lista de lectura: buscar otra novela con capítulos cortos y cartas entre personajes. Me resulta fácil retomar ese formato en el autobús, incluso después de varios días sin leer.",
])


library("French/English archaeological fieldwork", [
    ("Valon trench A hearth sampling", [
        "Valon trench A sampling targets the thin ash lenses inside the small hearth. Record each sample's depth before lifting it, and keep the surrounding soil separate so later analysis can distinguish burning from background material.",
        "Dans le foyer de la tranchée A, la lentille grise continue sous une pierre. Dessiner cette relation avant de prélever la suite; la profondeur seule ne suffit pas à expliquer la succession des dépôts.",
    ]),
    ("Valon trench B wall phasing", [
        "Tranchée B de Valon: relever les contacts entre le petit mur courbe et le mur droit. Il s'agit de comprendre leurs phases de construction, pas d'échantillonner les cendres du foyer de la tranchée A.",
        "The curved wall appears to abut the straight one, but loose packing obscures the junction. Photograph the contact under raking light before the trench B team assigns a construction sequence.",
        "Réunion du relevé des murs: remplacer la flèche trop certaine du dessin par une relation provisoire. Le contact reste partiellement caché; conserver l'ancienne interprétation dans le journal pour montrer pourquoi elle a changé.",
    ]),
    ("Moraine ridge surface pottery transect", [
        "Moraine ridge surface survey follows parallel walking transects with equal spacing. Record visible ground cover in each segment, because a low pottery count in thick grass does not necessarily mean fewer remains.",
        "Sur la crête, la bande orientale était fraîchement fauchée tandis que la bande voisine restait couverte. Ajouter cette différence à la fiche du ramassage avant de comparer les densités de tessons.",
        "The pottery survey budget allows one additional morning on the ridge. Use it to repeat the obscured segment after mowing, and retain the first count with its poor-visibility annotation.",
    ]),
    ("Serein well timber recording", [
        "Le relevé du puits Serein décrit les assemblages du cuvelage en bois. Numéroter les pièces sur le dessin et photographier les joints visibles avant toute manipulation; la simple liste des longueurs perd leur relation.",
        "The well's lowest visible timber has a notch unlike those above it. Add a close photograph and orientation arrow to the Serein record without assuming that the unusual cut proves a different construction date.",
        "Le planning du puits passe du mardi au jeudi, car l'accès sécurisé ne sera prêt qu'après l'inspection. Garder la date initiale dans le journal et déplacer la réservation de l'appareil photo.",
        "Recording review found two timber labels reversed on the plan but correct in the photographs. Correct the drawing with an explicit revision note so future measurements remain attached to the right pieces.",
    ]),
    ("Tilleul cemetery boundary geophysics", [
        "Tilleul geophysics tests the proposed cemetery boundary beyond the visible enclosure. Lay out a grid extending across both sides of the suspected ditch, and distinguish a survey anomaly from an excavated feature in the report.",
        "La clôture métallique longe une partie de la grille du cimetière. Marquer sa position précisément: les fortes réponses voisines peuvent venir de cette clôture et non d'un fossé ancien.",
        "The boundary survey meeting chose an extra strip west of the enclosure to test whether the linear response continues. Keep the original grid results as well as the extension instead of redrawing the first survey's extent.",
        "Budget Tilleul: la location de l'instrument comprend une batterie, mais pas le second jeu nécessaire pour la longue journée. Ajouter ce coût avant de comparer l'offre avec celle du fournisseur voisin.",
        "The western extension did not reproduce the suspected ditch signal. Preserve that negative result and revise the boundary discussion; the first strong line should not remain a confident claim simply because it looked persuasive.",
    ]),
    ("Ardoise rock-shelter sediment archive", [
        "Archive des sédiments d'Ardoise: associer chaque boîte au carré et à la couche notés sur le terrain. Les sachets sans contexte lisible doivent rester signalés, sans inventer une provenance à partir de leur couleur.",
        "The rock-shelter archive has two bags labeled square C, layer 4, with different collection dates. Preserve both entries and check the field log; identical context labels do not establish that one bag is a duplicate.",
        "La réunion d'archivage demande des étagères plus profondes pour les boîtes d'Ardoise. Mesurer les contenants pleins avant de commander, car les couvercles dépassent davantage que ne le suggère le catalogue.",
        "Archive cost review: use new outer boxes for damaged containers while retaining readable original bag labels inside. Replacing every label would cost more and risk losing useful handwriting and collection notes.",
        "J'avais écrit que tous les sachets de la couche quatre étaient datés. La vérification en trouve deux sans date; corriger le bilan et garder la première note pour documenter cette erreur de contrôle.",
        "Working copy of the Ardoise archive reminder: keep original labels, flag missing context, distinguish collection dates. This repeats the shelf-side checklist because the condition review is happening in another room.",
        "Le journal de terrain confirme deux prélèvements successifs dans le carré C. Conserver les deux sachets comme collectes distinctes du même contexte, et ajouter la référence du journal plutôt que supprimer un prétendu doublon.",
    ]),
], [
    (0, 1, "The Valon hearth sampling and wall-phasing teams need the site camera during the same morning. Allocate separate slots for trench A lenses and trench B contacts; sharing a site does not make their research questions identical."),
    (2, 4, "Le transect de poterie de Moraine et la grille géophysique de Tilleul peuvent partager le récepteur de position. Vérifier séparément leurs systèmes de repérage; les segments de marche ne correspondent pas aux cases du cimetière."),
    (3, 5, "Use the Serein timber-plan revision as an example in the Ardoise archive labeling meeting. It shows why corrections need an audit trail, but the well drawings and rock-shelter sample boxes remain separate recording projects."),
], [
    "Le titre du roman parle d'un 'puits de silence', mais aucun puits réel n'apparaît dans l'histoire. J'ai aimé cette image pour décrire une conversation qui s'arrête après une question difficile.",
    "The small green suitcase rolls more quietly after a thread was removed from one wheel. Remember to inspect the axle before buying replacements if the same scraping sound returns.",
    "Note pour la maison: la plante près de la fenêtre penche vers la lumière. Tourner doucement le pot chaque semaine et vérifier que ses feuilles ne touchent pas le radiateur.",
])


def main():
    root = Path(__file__).resolve().parent
    existing = [filename for filename in ("inputs.json", "author-labels.json") if (root / filename).exists()]
    if existing:
        raise SystemExit("Refusing to overwrite existing corpus artifacts: " + ", ".join(existing))
    assert len(LIBRARIES) == 12
    inputs = {"schemaVersion": 1, "libraries": []}
    labels = {"schemaVersion": 1, "libraries": []}
    lengths = []
    for number, (domain, threads, bridges, singletons, extra_related) in enumerate(LIBRARIES, 1):
        library_id = f"l{number:02d}"
        rng = random.Random(8029 + number)
        rows = []
        base = 1740787200 + number * 5184000
        for thread_number, (name, memories) in enumerate(threads):
            for sequence, memory in enumerate(memories):
                rows.append({"text": memory, "members": [name],
                             "timestamp": base + (sequence * 8 + thread_number) * 86400 + rng.randrange(3600, 72000)})
        for bridge_number, (first, second, memory) in enumerate(bridges):
            rows.append({"text": memory, "members": [threads[first][0], threads[second][0]],
                         "timestamp": base + (55 + bridge_number) * 86400 + rng.randrange(3600, 72000)})
        for singleton_number, memory in enumerate(singletons, 1):
            rows.append({"text": memory, "members": [f"isolated note {singleton_number}"],
                         "timestamp": base + rng.randrange(1, 55) * 86400 + rng.randrange(3600, 72000)})
        rng.shuffle(rows)
        public_items = []
        memberships = {}
        rationale = {}
        for item_number, row in enumerate(rows, 1):
            item_id = f"{library_id}-i{item_number:02d}"
            public_items.append({"id": item_id, "text": row["text"], "kind": "text", "timestamp": row["timestamp"]})
            memberships[item_id] = row["members"]
            # Direct source excerpts support review without inventing unstated facts.
            rationale[item_id] = "Source evidence: " + row["text"].split(". ")[0].rstrip(".") + "."
            lengths.append((item_id, len(row["text"].split())))
        related_pairs = {frozenset((threads[first][0], threads[second][0])) for first, second, _ in bridges}
        related_pairs.update(frozenset((threads[first][0], threads[second][0])) for first, second in extra_related)
        names = [name for name, _ in threads] + [f"isolated note {n}" for n in range(1, 4)]
        relationships = []
        for first, second in itertools.combinations(names, 2):
            related = frozenset((first, second)) in related_pairs
            shared_sources = [item_id for item_id, members in memberships.items() if first in members and second in members]
            first_source = next(item_id for item_id, members in memberships.items() if members == [first])
            second_source = next(item_id for item_id, members in memberships.items() if members == [second])
            relationships.append({"first": first, "second": second, "related": related,
                                  "evidence": shared_sources if related and shared_sources else [first_source, second_source]})
        inputs["libraries"].append({"id": library_id,
                                     "split": "development" if number <= 5 or number == 11 else "heldout",
                                     "slice": "multilingual" if number >= 11 else "english",
                                     "items": public_items})
        labels["libraries"].append({"id": library_id, "memberships": memberships,
                                    "relationships": relationships, "ambiguous": [], "rationale": rationale})
    too_short = [(item_id, length) for item_id, length in lengths if length < 20]
    too_long = [(item_id, length) for item_id, length in lengths if length > 65]
    assert not too_short, too_short
    assert not too_long, too_long
    for filename, payload in [("inputs.json", inputs), ("author-labels.json", labels)]:
        (root / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"libraries": len(inputs["libraries"]), "items": len(lengths),
                      "minWords": min(length for _, length in lengths),
                      "maxWords": max(length for _, length in lengths),
                      "totalWords": sum(length for _, length in lengths)}))


if __name__ == "__main__":
    main()
