from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/pdf'
SHOTS=OUT/'screenshots'
OUT.mkdir(parents=True,exist_ok=True)
FONTS=Path('/System/Library/Fonts/Supplemental')
for n,f in [('Body','Arial.ttf'),('Bold','Arial Bold.ttf'),('Italic','Arial Italic.ttf'),('Display','Georgia.ttf')]:
    pdfmetrics.registerFont(TTFont(n,str(FONTS/f)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Italic',boldItalic='Bold')
W,H=595.276,841.89
INK='#182B35'; MUTED='#536671'; TEAL='#146D70'; PALE='#EAF1F1'; BG='#F7F8F7'; LINE='#DCE3E3'; AMBER='#845A2A'
c=canvas.Canvas(str(OUT/'Remember_Product_Review.pdf'),pagesize=(W,H),pageCompression=1)
c.setTitle('Remember | Product review and feedback guide | September 2026')
c.setAuthor('Remember')
c.setSubject('Current implementation, phone UI, user needs, evidence, and product feedback')
page=0

def text(x,top,w,t,size=10.5,leading=None,color=INK,font='Body'):
    s=ParagraphStyle('p',fontName=font,fontSize=size,leading=leading or size*1.44,textColor=HexColor(color),spaceAfter=0)
    p=Paragraph(t,s); _,h=p.wrap(w,H)
    if top < H-43 and top+h>H-43: raise ValueError(f'Page {page}: overflow {top+h}: {t[:100]}')
    p.drawOn(c,x,H-top-h)
    return top+h

def rect(x,top,w,h,fill=PALE,r=10,stroke=None):
    c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(stroke or fill)); c.setLineWidth(.7)
    c.roundRect(x,H-top-h,w,h,r,fill=1,stroke=bool(stroke))

def line(x,top,w,color=LINE):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(.6); c.line(x,H-top,x+w,H-top)

def page_start(section,title=None,sub=None):
    global page
    if page: c.showPage()
    page+=1
    c.setFillColor(HexColor(BG)); c.rect(0,0,W,H,fill=1,stroke=0)
    text(42,24,160,'REMEMBER',9,12,TEAL,'Bold')
    text(330,24,225,section.upper(),8,12,MUTED)
    line(42,48,W-84)
    text(42,H-31,400,'PRODUCT REVIEW  /  14 SEPTEMBER 2026',7,9,MUTED)
    text(W-63,H-32,25,f'{page:02}',8,10,MUTED,'Bold')
    if title: text(42,72,W-84,title,27,33,INK,'Display')
    if sub: text(42,117,W-84,sub,10.5,15,MUTED)

def label(x,top,w,t): return text(x,top,w,t.upper(),8.2,12,TEAL,'Bold')
def block(x,top,w,heading,body):
    y=text(x,top,w,heading,12.3,17,INK,'Bold')
    return text(x,y+6,w,body,10.3,15,MUTED)+21

def callout(top,title,body,fill=PALE):
    rect(42,top,W-84,79,fill)
    text(57,top+12,W-114,title,11.5,16,TEAL,'Bold')
    text(57,top+34,W-114,body,9.6,14,INK)

def phone(name,x,top,w):
    path=SHOTS/(name+'.png')
    with Image.open(path) as im: iw,ih=im.size
    h=w*ih/iw
    rect(x-4,top-4,w+8,h+8,'#24343B',24)
    c.saveState()
    clip=c.beginPath(); clip.roundRect(x,H-top-h,w,h,21)
    c.clipPath(clip,stroke=0,fill=0)
    c.drawImage(str(path),x,H-top-h,width=w,height=h,mask='auto')
    c.restoreState()
    return top+h

def caption(x,top,w,t): text(x,top,w,t,8.1,11.5,MUTED)

def bullet_list(x,top,w,items):
    for heading,body in items:
        top=block(x,top,w,heading,body)
    return top

# 1
page_start('A product in progress')
label(42,74,450,'An iPhone memory vault')
text(42,100,510,'Keep the source.<br/>Find the thread.',37,44,INK,'Display')
text(42,204,490,'Save what matters. Find it later. Follow how an idea or project evolved, with the original material always within reach.',13,19,MUTED)
phone('memories',49,291,151)
phone('bubbles',220,263,156)
phone('river',396,291,151)
label(42,656,510,'Working prototype / User and investor feedback edition')
text(42,680,511,'The core iPhone experience is implemented. Automatic organization remains experimental, and the service needs more work before a production launch.',11,16)
text(42,731,511,'Real simulator captures with fictional notes and deliberately arranged threads. Screens show the current UI; they do not demonstrate automatic grouping accuracy.',8.5,12,MUTED)

# 2
page_start('The problem and the promise','Saving is easy. Returning is hard.','Remember is built around deliberate capture, useful retrieval, and a history you can inspect.')
rows=[
('“Where did I save that?”','Notes, links, documents and media become one searchable library.','Less time searching across separate places.'),
('“I remember the idea, not the filename.”','Local text search, filters, plus explicit AI search and source-based questions.','Find relevant material even when recall is incomplete.'),
('“How did this project get here?”','Project threads and a chronological River retain captures, revisions and organization events.','Reconstruct the context behind a decision.'),
('“Why did the app connect these?”','Inspect placement evidence and correct membership; corrections are preserved.','Keep control when automation is wrong.'),
('“Can I trust what was generated?”','Original sources, checked evidence quotes, local storage and visible AI controls.','Review the source before relying on an answer.')]
y=175
for pain,response,value in rows:
    label(42,y,510,pain)
    text(42,y+21,275,response,10.2,15)
    text(341,y+21,208,value,10.2,15,MUTED)
    line(42,y+85,511); y+=104
text(42,711,511,'These are product hypotheses, not validated user outcomes. Likely early users include students, researchers, creators and people managing ongoing personal projects. Interviews should identify which group feels this pain most often.',9.7,14,MUTED)

# 3
page_start('Implementation snapshot','What exists today','Assessment: a functional iPhone prototype with a developed UI and an experimental organization layer.')
headers=['AREA','CURRENT IMPLEMENTATION','EVIDENCE / LIMIT']
xs=[42,163,383]; ws=[111,211,170]
for x,w,t in zip(xs,ws,headers): label(x,169,w,t)
rows=[
('Capture & vault','Notes, photos, videos, links, PDFs and voice; in-app and Share Extension entry paths.','Implemented. Original files remain local. Not every intake path was exercised for this PDF.'),
('Memories & retrieval','Card library, search, filters, details, editing, tags, collections and recovery.','UI toured; local behavior covered by unit tests.'),
('Project & River','Timeline, bubble map, thread history, past-state comparison and corrections.','Navigable and test-covered. Grouping quality is a separate, unresolved issue.'),
('AI Help','Question composer, retrieval, quoted sources and generated-answer validation.','Implemented and unit-tested with fixtures. No live cloud answer verified in this review.'),
('Organization','On-device extraction and similarity; optional reasoning; merges and reviewable splits.','Historical device benchmark failed semantic-quality targets. Research replacements are not integrated.'),
('Settings & control','Light/dark/system appearance, archive, collections, tags and privacy activity.','UI toured. Archive retains content; permanent erasure is not implemented.')]
y=198
for i,row in enumerate(rows):
    if i%2==0: rect(35,y-8,525,81,'#EDF2F2',5)
    for j,(x,w,t) in enumerate(zip(xs,ws,row)): text(x,y,w,t,9.3,13.1,INK if j<2 else MUTED,'Bold' if j==0 else 'Body')
    y+=94
text(42,771,510,'Built does not mean launched, commercially validated, or reliable across every device and workload.',8.2,11,MUTED)

# 4
page_start('Phone tour / 01','Memories and capture','The starting point: save a thought quickly, then return to a readable library.')
phone('memories',50,177,220)
phone('capture-dial',324,177,220)
caption(50,666,220,'MEMORIES · Search and cards for saved material.')
caption(324,666,220,'CAPTURE DIAL · Rotate to reveal more actions.')
text(42,703,511,'Built: note creation, camera capture, Photos import, file import and voice recording. The dial de-emphasizes the library while open. Detail screens support reading, editing and metadata inspection.',10,14.5)
text(42,754,511,'Feedback prompt: can you tell how to save something, and does the rotating menu make that task easier?',9.5,14,TEAL,'Bold')

# 5
page_start('Phone tour / 02','Project: the complete thread list','Timeline gives the project experience a straightforward, scannable entry point.')
phone('project-timeline',50,178,225)
block(307,180,242,'One place to find a thread','All threads are listed with their full titles and memory counts. Tap a row to open its River.')
block(307,297,242,'A separate activity history','Source, date and topic controls filter the history below the thread list. Earlier activity can be loaded on demand.')
block(307,427,242,'Two views of the same work','Timeline and Graph lead to the same River. The list remains useful when titles are long or the map is crowded.')
block(307,555,242,'Naming to validate','“Project” contains many threads. Ask whether Project, Threads, or another label best describes what people expect here.')
callout(714,'Try it without a guided explanation','Find the garden studio thread. What do you expect to see when you open it?')

# 6
page_start('Phone tour / 03','Bubbles: a map you can explore','A spatial view of threads, with a light and dark appearance.')
phone('bubbles',50,177,220)
phone('bubbles-dark',324,177,220)
caption(50,665,220,'LIGHT · Neutral surfaces and a centered title.')
caption(324,665,220,'DARK · Graphite circles and restrained highlights.')
text(42,698,511,'Drag the grid; it settles on a thread. Larger circles contain more memories. Tap to enter the River; hold for a preview. Connections reflect shared sources or tags, not proven causal or conceptual relationships.',10.2,14.7)
text(42,753,511,'Current limit: the map displays up to 40 threads. Timeline lists all threads. No pinch-to-zoom controls are provided.',9.2,13.5,MUTED)

# 7
page_start('Phone tour / 04','The River: context over time','Open a thread and follow its history back to the saved sources.')
phone('river',50,178,225)
block(307,180,242,'A continuous history','A left-hand branch connects entries. Notes and supported media appear in chronological capture and revision events.')
block(307,306,242,'The source stays accessible','Open a memory from the River and return directly. Photos, voice players and user-initiated video playback can appear inline.')
block(307,444,242,'Revisit an earlier state','Travel through time reveals past membership and revisions, with a comparison to the current thread.')
block(307,574,242,'Correct without erasing','Inspect why an item was placed, choose its threads, rename a thread, or restore a note revision. Undo applies where still valid.')
callout(714,'The important distinction','A River should tell the story of a continuing context. Two notes can share a subject and still belong in different Rivers.')

# 8
page_start('Phone tour / 05','Ask, with the source beside it','AI Help is implemented; live cloud answer quality was not tested for this PDF.')
phone('ask',50,178,225)
block(307,180,242,'Ask a saved-material question','Type a question or dictate it, then explicitly submit it. The system retrieves a bounded set of source excerpts.')
block(307,300,242,'Check the quoted evidence','Generated claims must carry quotes found literally in retrieved text. When validation or the service fails, source-only results can remain useful.')
block(307,446,242,'Know what leaves the phone','Ask and AI search send relevant content to the configured OpenAI service even when automatic cloud assistance is off.')
block(307,584,242,'A limit worth understanding','A matching quote does not prove that a claim follows from it, that retrieval is complete, or that the original source is correct.')
callout(714,'Example question to test later','“What measurements did I save for the studio workbench?” Judge the answer, its source, and the time it saves.')

# 9
page_start('Phone tour / 06','Settings, recovery and trust','Controls for appearance, organization and the boundary between local and cloud processing.')
phone('settings',50,178,225)
block(307,180,242,'Appearance','System, Light and Dark options. The UI uses native controls, readable cards and a restrained action color.')
block(307,289,242,'Archive and organization','Restore memories and threads from Archive. Manage collections and tags without making a collection the owner of its source files.')
block(307,419,242,'Privacy & AI','Automatic cloud assistance is off by default. The activity screen records operation metadata instead of prompts, source text or generated answers.')
block(307,557,242,'Accessibility foundations','Dynamic Type, VoiceOver actions, Reduce Motion, Reduce Transparency and Increased Contrast have implementation support. Broader user testing is still needed.')
callout(714,'A material gap before launch','Archive is reversible hiding, not permanent deletion. Complete erasure, backup/export and a clear recovery story need product decisions.')

# 10
page_start('How it works','From a saved item to a traceable thread','The app keeps original material and a history of what changed.')
steps=[('01','CAPTURE','Save an original file or note in the local vault.'),('02','EXTRACT','Read text from notes, images and PDFs; transcribe supported voice recordings on-device.'),('03','ORGANIZE','Start a thread immediately. Use available source evidence and models to consider placement.'),('04','RETRIEVE','Browse, filter or search locally. Explicit AI actions can use selected content through the proxy.'),('05','REVISIT','Open the River, inspect evidence, compare history and make a correction.')]
y=178
for number,title,body in steps:
    rect(42,y,40,40,PALE,12); text(52,y+10,25,number,13,18,TEAL,'Bold')
    label(101,y,440,title); text(101,y+20,440,body,10.4,15)
    if number!='05': line(61,y+46,1)
    y+=91
rect(42,649,511,128,'#EAF0F5')
text(58,663,475,'What is kept local',12,17,INK,'Bold')
text(58,688,475,'Originals, the current library database and an append-only event history. Capture and revisions are recorded together. User corrections constrain future organization; they do not silently upload memories for training.',10.2,15)
text(58,745,475,'Cloud operations are explicit exceptions to this local foundation, not cloud backup or sync.',9.4,13.5,TEAL)

# 11
page_start('What works / What remains','The honest readiness picture','The product flow works. Reliable automatic organization and production operations remain open work.')
block(42,178,245,'Verified in this review','The simulator app built and the unit suite ran. Screen tours exercised library navigation, note creation, Project, map previews, River navigation, Settings and the assistant entry screen.')
block(319,178,234,'Implemented, with limits','OCR, transcription, Share Extension intake, media playback, semantic search and grounded Ask exist in code. A screenshot tour does not certify every real-device or network path.')
line(42,343,511)
label(42,363,510,'The strongest current caution: organization quality')
text(42,389,511,'The completed 10-11 September device baseline missed its heldout English grouping targets in both modes. Incorrect joins and fragmented threads remain a real product risk. Successful execution is not the same as useful organization.',11,16)
rect(42,468,511,111,'#F2EDE5')
text(58,482,476,'Research is separate from the app',12,17,AMBER,'Bold')
text(58,508,476,'Later specialist-matcher experiments improved some match recovery, but the 13 September validation failed its all-seeds qualification rule. No replacement matcher is integrated or qualified for production. Further context-focused diagnostics are in preparation.',10.2,15)
block(42,604,245,'Capability gaps','Video scenes and video speech are not indexed; only captions are. Saved links do not guarantee full-page content. Model availability and language support vary.')
block(319,604,234,'Launch gaps','No account system, cloud sync, collaboration or complete backup/export. The development AI proxy still needs authenticated access and production controls. Larger-library performance is not validated.')

# 12
page_start('Direction and priorities','What we want to achieve','A useful personal memory system that gets easier to trust as the library grows.')
priorities=[
('1. Make the core loop valuable','Help people save an item and successfully find it again in a real situation. Validate the first target audience and the most frequent capture types.','Measure: capture completion, time to find an item, repeat retrieval and voluntary return use.'),
('2. Make organization trustworthy','Agree on what a continuing project means. Reduce incorrect joins before expanding automation. Keep uncertain material separate and corrections easy.','Measure: accepted-join precision, missed connections, correction effort and stability across arrival order.'),
('3. Make the interface self-explanatory','Test the rotating dial, Project naming, map gestures and River with people who have not seen a demo. Preserve the direct list route.','Measure: unassisted task success, hesitation points, mis-taps and accessibility task completion.'),
('4. Make personal data recoverable','Resolve erasure, export, backup and device-loss recovery. Harden cloud access and make the data boundary understandable.','Measure: restore success, privacy comprehension and reliability under interruption.')]
y=176
for title,body,measure in priorities:
    text(42,y,511,title,13,18,INK,'Bold')
    text(42,y+27,511,body,10.5,15)
    text(42,y+78,511,measure,9.2,13.5,TEAL)
    line(42,y+119,511); y+=147
text(42,771,511,'Proposed sequence for discussion. These are priorities and desired outcomes, not delivery dates or commitments.',8.2,11,MUTED)

# 13
page_start('Feedback guide','Show it. Listen. Let people try.','Use a short walkthrough, then give the participant room to interpret the product in their own words.')
label(42,175,511,'First impressions / before explaining the metaphors')
y=201
for n,q in enumerate([
'What do you think this app helps you do? When did you last need that?',
'Where do you currently save this kind of material? What makes returning to it difficult?',
'Which screen makes immediate sense? Which needs an explanation?'],1):
 y=text(42,y,511,f'<b>{n}.</b> {q}',11,16)+15
label(42,335,511,'Try three tasks / observe before helping')
y=361
for q in [
'Save a note. Find it again. Tell us what you expected the add control to do.',
'Open a thread from the list, then from the bubbles. Which route would you use again?',
'Open the River and inspect a source. Explain what “Travel through time” would be useful for.']:
 y=text(42,y,511,'• '+q,10.6,15.5)+13
label(42,500,511,'Discuss the product boundary')
y=526
for q in [
'Which items belong in the same River? Which are merely related? Give an example from your own work.',
'What would you keep, change or remove? What would you most want to add?',
'What would make you trust the app with your material? What recovery or privacy controls would you expect?']:
 y=text(42,y,511,'• '+q,10.6,15.5)+13
callout(711,'Close with one concrete priority','“If we improved only one thing before you tried it again, what should it be?” Record the answer in their words.')

# 14
page_start('User and investor discussion','What evidence should come next?','The current artifact demonstrates implementation and design progress. Commercial demand remains to be established.')
block(42,179,245,'For prospective users','Would this replace something, complement it, or add another place to maintain? Which recurring task would make you return next week? What should happen when the app groups something incorrectly?')
block(319,179,234,'For investors and advisers','Which initial audience has the clearest unmet need? Is the River valuable enough to drive adoption? What proof of retention, trust and distribution would you need before treating this as a business opportunity?')
line(42,374,511)
label(42,395,511,'What this review does not establish')
text(42,422,511,'Market size, competitive superiority, willingness to pay, pricing, user growth, retention, revenue and unit economics have not been established by the inspected implementation evidence. No commercial metrics are claimed here.',11,16)
label(42,512,511,'A lightweight way to capture responses')
rows=[('Participant context','Role / current tools / most recent recall problem'),('Keep','Most useful feature and why'),('Change or remove','Most confusing or unnecessary part'),('Add','Missing capability and the task it enables'),('Return trigger','What would bring them back next week?')]
y=540
for a,b in rows:
    text(42,y,137,a,9.6,14,INK,'Bold'); text(190,y,363,b,9.6,14,MUTED)
    line(42,y+29,511); y+=41
text(42,761,511,'Capture observed behavior separately from opinions. Do not turn a positive demo reaction into a retention claim.',8.8,12,TEAL)

# 15
page_start('Evidence appendix / 01','What the organization results say','Historical benchmark evidence, kept separate from the current screen demonstration.')
label(42,177,511,'10-11 September / current production-policy baseline')
text(42,202,511,'144 of 144 core device scenarios completed on fictional, agent-reviewed libraries. On five heldout English libraries, both modes missed the preregistered 99% pair-precision and 85% pair-recall goals. [E1]',10.5,15)
rect(42,277,511,143,PALE)
for x,w,t in [(56,218,'MODE'),(285,118,'PAIR PRECISION'),(416,121,'PAIR RECALL')]: label(x,291,w,t)
for y,vals in [(326,('Embedding only','77.12%','31.65%')),(369,('Local reasoning','18.01%','59.50%'))]:
    for x,w,t in zip([56,285,416],[218,118,121],vals): text(x,y,w,t,12,17,INK,'Bold')
text(42,440,511,'Precision asks: of the pairs grouped together, how many belong together? Recall asks: of the pairs that belong together, how many were recovered? These are macro library averages, with runs averaged within a library; local mode includes more chronological repeats.',9.7,14,MUTED)
label(42,523,511,'13 September / separate specialist-matcher validation')
text(42,550,511,'The D3 hybrid recovered more matches than the refitted simple baseline, but two of three seeds missed its 95% precision gate. The all-seeds qualification therefore failed. Across seeds, precision was 94.59-95.79% and macro recall 58.39-65.15%. [E2]',10.5,15)
text(42,633,511,'This later study used 960 fictional sources across 48 libraries; its evaluation split contained 240 sources. It is an English pair-classification experiment, not a production thread replay. Its numbers are not directly comparable to the full-system baseline above.',9.7,14,MUTED)
text(42,706,511,'Both studies use synthetic, agent-reviewed material. Neither establishes real-user effectiveness. Device performance, media coverage and broader language support remain separate validation needs.',9.7,14,MUTED)

# 16
page_start('Evidence appendix / 02','Scope, sources and verification','Prepared from the repository and simulator on 14 September 2026. No application feature changes were made.')
label(42,175,511,'How to read the claims')
text(42,201,511,'“Implemented” means the behavior exists in current code. “Verified” refers to a check actually run for this review. Earlier device results are explicitly dated historical evidence. Goals and proposed next steps are not shipped capabilities.',9.8,14)
label(42,273,511,'Screen provenance')
text(42,299,511,'The main phone images are direct captures of the current app on an iPhone 17 simulator (iOS 26.5). Nine fictional notes were seeded using the app’s persistence APIs, and seven threads were deliberately arranged using user-assignment APIs. Connections shown come from fixture tags. No personal phone content or live cloud responses are included.',9.8,14)
label(42,396,511,'Verification performed for this review')
verification=(OUT/'verification_summary.txt').read_text() if (OUT/'verification_summary.txt').exists() else 'Verification result pending.'
text(42,422,511,escape(verification).replace('\n','<br/>'),9.5,13.8)
label(42,548,511,'Repository sources / evidence register')
sources=[
('[E1]','docs/evaluations/2026-09-10-organization-benchmark.md','Completed baseline, quality limits and performance attempts.'),
('[E2]','Evaluation/MatcherValidation/P2_REPORT.md','13 September qualification result; research is not integrated.'),
('[E3]','readme.md; docs/provenance.md; docs/appearance.md','Current feature surface, data/history rules and UI behavior.'),
('[E4]','Remember/Remember/ and Remember/RememberTests/','Current views, pipeline, storage, AI boundary and regression tests.'),
('[E5]','docs/organization-improvement-plan.md; Evaluation/OrganizationDiagnostics/RESUME.md','Proposed direction and incomplete diagnostic preparation.')]
y=574
for code,path,desc in sources:
    y=text(42,y,511,f'<b>{code}</b> {escape(path)}',8.3,11.5)+2
    y=text(65,y,488,desc,8.2,11,MUTED)+9
c.save()
print(OUT/'Remember_Product_Review.pdf')
print(f'{page} pages')
