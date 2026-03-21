# Converting `book_v2.md` into an Audio‑Ready en‑US Transcript from Preface Through Epilogue

## Executive summary

This report specifies a reproducible, automation-friendly method to convert the GitHub Markdown source `book_v2.md` into an audiobook-style transcript covering **Preface → Epilogue**, including strategies for (a) reliably fetching/parsing GitHub Flavored Markdown (GFM), (b) extracting the exact content range using heading-aware boundary detection, (c) converting Markdown constructs (headings, lists, tables, equations, code, references) into natural narration, and (d) building a **pronunciation layer** that outputs **IPA + readable respellings** and can optionally emit SSML/PLS pronunciations for TTS engines.

Key constraints from the source document matter for design. The file is explicitly structured with top-level headings for **“Preface: How to Read This Book”** and **“Epilogue: The Navigator”**. citeturn5view1turn5view0 It contains (at least) a glossary with symbols like **Φ** (explicitly annotated as “fye”), inline equations for entropy families (Tsallis/Rényi), multiple Markdown tables (notably in appendices), and an extensive references section. citeturn7view0turn7view1turn19view2turn18view0

Assumptions (called out because the request leaves them unspecified):
- **Language**: en‑US narration, consistent with the request and SSML locale conventions (`xml:lang="en-US"`). citeturn11search0turn11search9  
- **Audio output**: “audio-ready transcript” is treated as a *narration script* that can drive either **human narration** or **TTS**. If mastering targets are needed, the common industry constraints differ by distributor; for example, entity["organization","ACX","audiobook marketplace, us"] publishes explicit technical specs (e.g., file length cap, sample rate). citeturn22search1turn22search5 LibriVox’s public specs are another commonly referenced baseline for spoken-word MP3 settings. citeturn21search2  
- **Page count**: not assumed. Instead, treat “30–60 pages” as roughly **7,500–18,000 words** at ~250–300 words/page (typical prose), then estimate runtime at your chosen narration WPM (e.g., 150–165 WPM).

## Source document characteristics and the extraction target

The primary source is the Markdown book authored by entity["people","Kenneth Malloy","author of navigational faculty"] and versioned “v2.75 — March 2026.” citeturn4view0 The start and end anchors required by this task are present as top-level headings:

- Start boundary: `# Preface: How to Read This Book` citeturn5view1  
- End boundary: `# Epilogue: The Navigator` citeturn5view0  

Within the Preface, the author directs readers toward a glossary and describes tagging claims as `[A]`, `[B]`, `[C]`. citeturn4view0 Those tags are “non-prose elements” you must normalize for narration (“Level A”, “Level B”, “Level C”, or “tag A/B/C”) rather than reading raw brackets.

The file includes:
- A **Glossary of Key Terms** with explicit pronunciation guidance for at least one symbol: `Φ (fye, rhymes 'eye')`. citeturn7view0  
- Inline math-like expressions (not necessarily LaTeX delimited), including Tsallis/Rényi entropy definitions and Greek letters (e.g., `S_q`, `H_α`, `Σ`, `α → 1`). citeturn7view1turn19view1  
- Markdown tables used to present structured results (e.g., Appendix D results table; Appendix L “Diagnostic Panel” table). citeturn19view2turn19view1  
- A large **References** section that is not appropriate to read verbatim in most audiobook treatments; it should usually be omitted or summarized as “References available in the accompanying text.” citeturn18view0  

Implication: treat the transformation as **structure-aware** (AST-based) rather than regex-only, because tables, inline code spans, and hierarchical headings drive narration decisions.

## Fetching and parsing the Markdown reliably

### Fetch step with integrity and reproducibility

Use one of three approaches; pick based on deployment constraints (CI/CD, rate limits, offline builds).

**Option A: Fetch from `raw.githubusercontent.com` (simplest)**  
This produces the exact Markdown bytes used by renderers.

```bash
curl -L \
  -o book_v2.md \
  https://raw.githubusercontent.com/KenMalloy/NavigationalFacultyTheory/main/book_v2.md

# Quick sanity checks
wc -c book_v2.md
wc -w book_v2.md
```

The “Raw” artifact is the canonical basis for parsing; the published file content confirms Preface and Epilogue headings in the raw text. citeturn4view0turn5view0turn5view1

**Option B: Fetch via GitHub REST “contents” API with raw media type (best for authenticated/rate-limited environments)**  
GitHub’s “Get repository content” endpoint supports a raw media type specifically “Returns the raw file contents.” citeturn15view0

```bash
curl -L \
  -H "Accept: application/vnd.github.raw+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/repos/KenMalloy/NavigationalFacultyTheory/contents/book_v2.md \
  -o book_v2.md
```

Rationale: you can add auth headers, capture ETags, and align on a pinned API version for deterministic builds. citeturn15view0turn14search4

**Option C: `git clone` and pin a commit hash (best for long-lived builds)**  
Use when you want the transcript tied to a specific revision and reproducible by others.

### Parse step: treat input as GitHub Flavored Markdown (GFM)

GitHub uses **GitHub Flavored Markdown**, defined as a superset of CommonMark with formal specification. citeturn9search35turn9search1turn8search0

Even if the current file doesn’t contain every GFM extension, your conversion pipeline should support:
- Tables, task lists, strikethrough, autolinks (GFM spec + common tool support). citeturn9search1turn9search12  
- Fenced code blocks (GitHub Docs). citeturn9search27  
- LaTeX math blocks/inline math (GitHub supports LaTeX math in Markdown). citeturn9search4  

Recommended parsing principle: **parse to an AST**, not directly to HTML/plaintext, so you can narrate each node type with deliberate rules.

Common robust parser choices:
- **Node/unified/remark**: `remark-parse` produces Markdown AST (mdast), and `remark-gfm` adds GFM constructs including footnotes/tables/task lists. citeturn13search4turn13search0turn9search12  
- **Python**: `markdown-it-py` (CommonMark-compliant core + plugins including footnotes and tables). citeturn13search1turn13search9  
- **Pandoc**: converts Markdown to a structured intermediate AST and supports filters for custom transformations. citeturn8search1turn13search11  

## Identifying Preface→Epilogue boundaries and extracting the target text

### Boundary detection method (heading-aware, not line-based)

Because Preface and Epilogue are top-level headings, the most robust boundary approach is:

1. Parse Markdown into an AST where headings are explicit nodes.
2. Walk nodes in document order.
3. Flip an `in_scope` flag when you hit the Preface heading.
4. Stop after you’ve emitted Epilogue content (or include Epilogue and stop at the next top-level boundary if present).

This is resilient to changes in whitespace, line wrapping, and table formatting.

A practical rule set:
- Treat **heading depth 1** (`# ...`) as “major section boundaries.”
- Define start when heading text matches `^Preface:` (or exact string match).
- Define stop when heading text matches `^Epilogue:` and you have emitted its subtree.

This is aligned with CommonMark/GFM semantics of headings. citeturn8search0turn9search1

### Special-case recommendation: include “title page” as opening credits

Your scope request begins at Preface, but audiobook conventions often include a short opening identifying title/author/version. The file contains these immediately before Preface. citeturn4view0 A common compromise is:
- Add a synthetic “Opening Credits” section generated from the metadata lines.
- Then begin the strict Preface content.

That keeps you faithful to the requested content while producing a usable audio artifact.

## Converting Markdown into natural narration

### Core narration normalization strategy

Use a **two-pass transform**:

**Pass A: Structural narration pass (AST → “narration blocks”)**  
Turn the AST into a sequence of “utterance blocks” with metadata:

- `block_type`: heading | paragraph | list | table | equation | code | quote | footnote | reference
- `section_path`: e.g., `["Preface", "Glossary", "Chapter 1"]`
- `text`: plain narration text (not raw Markdown)
- `speech_hints`: pauses, emphasis intent, pronunciation tags, “don’t read” flags
- `source_span`: pointer to source nodes/spans for traceability

**Pass B: Linguistic smoothing pass (“read-aloud editing”)**  
Apply language rules across blocks:
- Expand abbreviations and symbols contextually.
- Normalize punctuation that TTS reads literally.
- Insert pauses around heading transitions and list/table boundaries.
- Enforce consistent rendering of the `[A]/[B]/[C]` tags described in Preface. citeturn4view0

### Handling headings

Recommended audiobook phrasing:
- `# Heading` → “Section: …” (or “Chapter …: …” if the heading already includes “Chapter”).
- Add 400–800 ms pause after major headings (SSML `<break>` if using SSML). SSML is designed for author control over speech output. citeturn11search0  

Example rule:
- `## Chapter 1: The Hard Problem` becomes:  
  “Chapter one. The Hard Problem.” then a pause, then content. (The source uses this pattern heavily.) citeturn4view0turn5view2  

### Handling lists

The source includes list-like structures (including dashed bullets) that should become spoken enumeration. citeturn5view2turn19view2

Rules:
- For short lists (≤5 items): read each item with ordinal cues (“First… Second…”) or with a consistent bullet intro (“Item one…”).
- For long lists: summarize, then optionally read only the most important items; preserve full detail in companion text output.

If a list item is a definitional clause (common in the book), prefer “Here are the conditions. One: … Two: …”.

### Handling equations and math-like expressions

GitHub supports LaTeX math in Markdown; your pipeline should handle both:
- **LaTeX-delimited math** (if present later): detect and convert through a math speech engine.
- **Unicode/plaintext math** (present in this file): parse tokens and render as speech.

The book includes, for example, Tsallis entropy and Rényi entropy inline equations and Greek letters. citeturn7view1turn19view1

Practical narration patterns:
- `S_q = (1/(q−1))(1 − Σ p(x)^q)` →
  “S sub q equals: open parenthesis, one over q minus one, close parenthesis, times: open parenthesis, one minus the sum over x of p of x to the q power, close parenthesis.”
- `α → 1` →
  “alpha approaches one.”

### Handling tables

The file uses Markdown tables for results and diagnostic panels. citeturn19view2turn19view1

Audiobook rule: **do not read tables cell-by-cell unless the table is tiny and it truly matters**.

Preferred table narration template:
1. “The following table summarizes X.”
2. “It compares A vs B along dimensions C.”
3. “The key takeaway is …”
4. Optionally: read 1–3 standout rows only.

Example target tables include:
- Appendix D results table (“Comparator … Median lag … p-value …”). citeturn19view2  
- Appendix L diagnostic panel table with 5 markers. citeturn19view1  

### Handling footnotes, citations, and references

Even if footnotes are rare in this specific file, your system should support them because GFM ecosystems commonly use them (and remark-gfm explicitly parses footnotes). citeturn9search12turn9search1

Suggested narration rules:
- Inline citations like “(Author, Year)” in running text: usually read minimally (“…author name, year…”) only when essential.
- Footnotes: convert to “Note:” at the end of the paragraph or collect at the end of a section as “Notes for this section.”
- Full references section: in most audiobook contexts, replace with: “References are included in the accompanying text edition.” The file has a substantial `# References` section. citeturn18view0  

### Handling code blocks and inline code

GitHub supports fenced code blocks; treat them as “non-prose.” citeturn9search27

Rules:
- Inline code spans: speak as “code” and normalize underscores/dots:  
  `enaqt_simulation/core.py` → “E N A Q T underscore simulation slash core dot P Y.” (The source includes code paths like these.) citeturn23view0  
- Code blocks:
  - Prefer: “A code example follows in the text edition,” unless the code is short and conceptually critical.
  - If read: read only high-level pseudocode, not syntax punctuation.

## Pronunciation system for scientific terms, symbols, and specialized vocabulary

### Design goal: deterministic, reviewable pronunciations with fallbacks

Build a pronunciation layer that outputs **three parallel representations** per term:

1. **IPA** (canonical, human review; use the official IPA chart references for symbol conventions). citeturn9search2turn9search5  
2. **Readable respelling** (en‑US narrator-friendly: “fye”, “RAY‑nee”, “SIG‑muh”).  
3. **Engine-targeted phonemes** (optional): SSML `<phoneme>` tags or a W3C PLS lexicon file.

W3C maintains the key standards for pronunciation control:
- SSML 1.1 for speech synthesis markup. citeturn11search0  
- PLS 1.0 for pronunciation lexicons, with alphabet control such as `alphabet="ipa"`. citeturn11search9turn16search2  

### Term detection: combine source-derived lexicon + statistical detection

A rigorous approach uses three feeds:

**Feed A: Source glossary mining (highest precision)**  
The file has a Glossary with bolded term entries; extract each bolded headword plus any parenthetical pronunciation note. This is where you get **Φ → “fye”** explicitly. citeturn7view0

**Feed B: Symbol and pattern scanner (math + Greek + operators)**  
Detect:
- Greek letters: `α, β, γ, Φ, Σ` etc (Unicode ranges).
- Math operators: `≈, ≤, ≥, →, ×, −, ∑/Σ` etc.
- Subscripts/superscripts: `S_q`, `ps⁻¹`, `10⁻¹⁵`. citeturn23view0turn7view1  
Normalize Unicode minus (`−`) vs hyphen (`-`) to avoid TTS literal “dash” artifacts.

**Feed C: Scientific named entities & acronyms (recall-oriented)**  
Heuristics:
- ALLCAPS tokens of length 2–8: “IIT”, “GNWT”, “ENAQT”, “PCI”. citeturn7view0turn23view0  
- Capitalized surnames used adjectivally: “Rényi”, “Tsallis”, “Kolmogorov”. citeturn7view1turn19view1  
- Chemical shorthand: “5‑MeO‑DMT”.

### Pronunciation generation stack

**Step 1: Look up in a standard lexicon (CMUdict) for ordinary English**  
The CMU Pronouncing Dictionary is the most common open pronunciation lexicon for American English and is intended for speech systems. citeturn16search1  
Use it for words like “entropy”, “probability”, “consciousness” (and many others).

**Step 2: Grapheme‑to‑phoneme fallback for out‑of‑vocabulary tokens**  
For names/technical tokens not in CMUdict:
- **Sequitur G2P** (trainable G2P; academic origin at entity["organization","RWTH Aachen University","aachen, germany"]). citeturn10search0  
- **Phonetisaurus** (WFST-based G2P training/usage). citeturn10search13  
These tools can be trained/bootstrapped from CMUdict pronunciations.

**Step 3: Phonemization/IPA emission for quick approximations and debugging**  
Use `espeak-ng` as a practical “phoneme oracle” for many tokens; it can output IPA directly (`--ipa`). citeturn8search24turn12search10  
For batch phonemization in Python, `phonemizer` supports backends including eSpeak and can emit phoneme strings. citeturn10search3turn10search7

**Step 4: Human-in-the-loop review for high-risk terms**  
High-risk categories:
- Ambiguous acronyms (should it be letters or a word?)
- Non-English surname pronunciations (Rényi has a Hungarian pronunciation; many en‑US narrations anglicize). citeturn17search1  
- Symbols whose pronunciation varies by field (“phi” /fiː/ vs /faɪ/): here, the text explicitly directs “Φ (fye)”. citeturn7view0  

### Math-to-speech for LaTeX/MathML pipelines

If LaTeX blocks appear (GitHub supports them), convert as:
1. LaTeX → MathML (via MathJax or equivalent)
2. MathML → speech strings (MathCAT or Speech Rule Engine)

Open tools commonly used for math speech:
- MathCAT (open-source math-to-speech). citeturn0search2  
- Speech Rule Engine (SRE) for rule-based math speech generation. citeturn0search3  

### Output pronunciation artifacts

Produce three deliverables:
- `pronunciations.csv` (term, ipa, respelling, say-as, notes, examples)
- `lexicon.pls` (optional; W3C PLS 1.0) citeturn11search9  
- Inline SSML `<phoneme>` tags for terms that must be forced (engine-specific; some TTS vendors document IPA/X‑SAMPA acceptance). citeturn11search13turn11search5  

## Audio-ready transcript format, sample excerpt, and processing pipeline

### Time-stamped transcript format

Two practical formats cover most “audio-ready” needs:

**Format A: Timed blocks for editors (WebVTT)**  
WebVTT is a W3C standard for time-aligned text tracks. citeturn20search0  
Use it for editing, QA, and navigation markers even if your synthesis format is SSML.

**Format B: “Timed SSML blocks” (TSB) for synthesis workflows**  
Not a formal standard, but extremely practical: each cue embeds a syntactically valid SSML fragment, with cue timestamps used by your pipeline tooling (not by SSML itself). SSML is explicitly designed for controlling speech rendering. citeturn11search0  

### Sample excerpt with inline pronunciation annotations (paraphrased demonstration)

Below is an example “Timed SSML blocks” excerpt (≈275–330 words) that demonstrates how headings, tags, symbols, and an equation can be represented. It paraphrases the source themes rather than reproducing long verbatim passages.

```xml
@00:00:00.000-00:00:18.000
<p>
  <s>Preface. How to read this book.</s>
  <break time="600ms"/>
  <s>
    The author proposes a three-layer account of consciousness: what it does, how it does it,
    and what it navigates through.
  </s>
</p>

@00:00:18.000-00:00:45.000
<p>
  <s>
    When you hear bracket tags like “A”, “B”, and “C”, treat them as commitment levels:
    Level A is the most conservative layer, Level C the most speculative.
  </s>
  <break time="500ms"/>
  <s>
    The glossary introduces technical terms, including symbols. For example,
    <phoneme alphabet="ipa" ph="faɪ">Φ</phoneme>
    is read as “fye” in this text.
  </s>
</p>

@00:00:45.000-00:01:22.000
<p>
  <s>
    Some passages use compact mathematical notation. Read these aloud instead of spelling punctuation.
    For instance, when defining Tsallis entropy, you may see:
    “S sub q equals (1 over q minus 1) times (1 minus sigma over x of p of x to the q power).”
  </s>
  <s>
    If the text introduces Rényi entropy, you can pronounce the name as “RAY-nee”
    <break time="200ms"/>
    and optionally note the Hungarian vowel length in the IPA guide: <phoneme alphabet="ipa" ph="ˈreːɲi">Rényi</phoneme>.
  </s>
  <break time="400ms"/>
  <s>
    When a table appears, summarize what it compares and state the key takeaway,
    then direct the listener to the companion text for exact cell values.
  </s>
</p>
```

Notes tying this demo to the real source:
- The source explicitly annotates **Φ** as “fye”. citeturn7view0  
- The source includes explicit Tsallis/Rényi equations and Greek-letter notation. citeturn7view1turn19view1  
- The document includes multiple Markdown tables where summarization is preferable in audio (e.g., Appendix D, Appendix L). citeturn19view2turn19view1  

### Tooling recommendations with pros/cons and practical commands

#### Markdown parsing and transformation

| Component | Recommended tools | Strengths | Risks / cons | Best use case |
|---|---|---|---|---|
| AST-first Markdown processing (GFM) | `remark-parse` + `remark-gfm` | Full markdown→AST pipeline; explicit handling of GFM features like tables/footnotes/task lists. citeturn13search4turn9search12 | Node toolchain; you must implement narration rules yourself | Maximum control over narration + annotations |
| Python AST parsing | `markdown-it-py` (+ plugins) or Mistune AST renderer | Python-native; plugin ecosystem; Mistune can emit AST tokens. citeturn13search1turn13search6 | GFM parity depends on plugins; edge-case differences vs GitHub renderer | Python-first production systems |
| Format conversion as baseline | Pandoc + filters (Panflute) | Many input/output formats; AST filters are a first-class concept. citeturn8search1turn13search11 | Pandoc “plain text” output is not narration-aware by default | Rapid prototyping; multi-format outputs |

#### Pronunciation and phoneme tooling

| Need | Tools | Strengths | Risks / cons |
|---|---|---|---|
| Standard en‑US pronunciations | CMU Pronouncing Dictionary (CMUdict) | Widely used open pronunciation lexicon for American English. citeturn16search1 | Limited coverage for names/new technical tokens |
| OOV (out-of-vocabulary) G2P | Sequitur G2P; Phonetisaurus | Trainable G2P; good for custom vocabularies. citeturn10search0turn10search13 | Requires training data, evaluation, and manual review |
| Quick IPA generation | `espeak-ng --ipa` / phonemizer (eSpeak backend) | Fast, local IPA/phoneme output; helpful debugging. citeturn8search24turn10search3 | Not a “gold” lexicon; can be anglicizing/unreliable for niche names |
| Standards for forcing pronunciations | SSML + PLS | Cross-platform conceptual standard; supports IPA lexicons. citeturn11search0turn11search9 | Actual TTS engine support varies |

#### Open-source TTS engines (for optional audio and automated “pronunciation samples”)

| Engine | Pros | Cons / cautions | Example CLI / usage |
|---|---|---|---|
| Piper | Fast, local neural TTS; designed for on-device use. citeturn8search2 | SSML feature support depends on wrappers; voice availability varies | Typically invoked via installed `piper` binary or Python package (engine-specific) |
| Coqui TTS | Flexible neural TTS toolkit; CLI supports text→WAV. citeturn11search2 | Heavier dependencies; model selection/quality varies | `tts --text "Hello" --out_path out.wav` citeturn11search2 |
| MaryTTS | Java server architecture; multi-language platform. citeturn9search3 | Voice quality often below state-of-the-art neural engines without custom voices | Run as server; synthesize via HTTP endpoints (implementation-specific) |
| eSpeak / eSpeak NG | Extremely lightweight; multilingual; IPA output modes. citeturn12search10turn8search24 | Robotic voice; best as a phoneme/IPA tool or fallback TTS | `espeak-ng --ipa -v en-us "text"` citeturn8search24turn12search10 |
| Festival | Mature research system; scriptable. citeturn11search11turn11search27 | Older voices; setup complexity | Use `festival` in tts mode (see manual) citeturn11search11 |
| Mimic3 / OpenTTS (wrappers) | Convenient packaging; OpenTTS unifies multiple engines in containers. citeturn12search1turn12search5 | Mimic3 is no longer actively maintained. citeturn12search0 | Best for prototyping and internal tooling |

### Mermaid flowchart of the processing pipeline

```mermaid
flowchart TD
  A[Fetch Markdown bytes] --> B[Parse as GFM to AST]
  B --> C[Locate Preface heading]
  C --> D[Extract nodes until Epilogue end]
  D --> E[Normalize structure]
  E --> E1[Headings -> spoken titles + pauses]
  E --> E2[Lists -> enumerations or summaries]
  E --> E3[Tables -> summary narration + optional row highlights]
  E --> E4[Equations/symbols -> math speech strings]
  E --> F[Build pronunciation lexicon]
  F --> F1[Glossary mining]
  F --> F2[Symbol & acronym detection]
  F --> F3[CMUdict lookup + G2P fallback]
  F --> G[Emit audio-ready script]
  G --> G1[Timed transcript (WebVTT)]
  G --> G2[Timed SSML blocks + optional PLS]
  G2 --> H[Optional TTS synthesis]
  H --> I[QC: diff checks + listening pass]
  I --> J[Publish outputs]
```

## Quality control checklist and effort estimate for a 30–60 page section

### Quality-control checklist (automation + human review)

Automated structural QC:
- Verify the AST walk finds exactly one start boundary (`Preface`) and one end boundary (`Epilogue`) and that extracted content includes the Epilogue heading. citeturn5view1turn5view0  
- Ensure every top-level heading in-scope becomes a spoken section marker (especially chapters). citeturn5view2turn19view1  
- Detect tables and enforce “table summarization mode” by default (table nodes must not expand into cell-by-cell reads unless explicitly allowed). citeturn19view2turn19view1  
- Detect the references section and apply the “omit/summary” rule, unless a “full bibliographic read” mode is explicitly enabled. citeturn18view0  

Pronunciation QC:
- Build a “high-risk token list” (Greek letters, math operators, acronyms, surnames, chemical abbreviations).
- Confirm that **Φ** is rendered as directed (“fye”) everywhere it appears. citeturn7view0  
- Confirm that equation reading templates are consistent for repeated constructs (Σ sums, arrows, approximations). citeturn7view1turn23view0  

Listening QC (critical even for TTS pipelines):
- Spot-check one sample per chapter and every appendix with dense math/tables.
- Verify pacing at boundaries: headings, list introductions, table summaries.

### Estimated effort and time (30–60 pages)

Treat “30–60 pages” as **~7,500–18,000 words** (typical prose density). At 155 WPM narration speed, that’s roughly **48–116 minutes** of finished audio.

A realistic engineering + editorial estimate (assuming you are building the pipeline, not manually rewriting everything):
- **Initial tooling setup and first-pass conversion**: 4–12 hours (parser integration + narration rules + first lexicon pass).
- **Pronunciation curation** (science-heavy text): 1–3 hours for the first 30–60 pages, then 15–45 minutes incremental as the lexicon stabilizes (glossary mining reduces ongoing effort). citeturn7view0turn23view1  
- **Human listening QA and fixes**: 0.5–1.5× real-time audio length (≈25–175 minutes) depending on density of math/tables and your tolerance for minor prosody errors.
- **If exporting to distributor-constrained audio specs**: add a mastering pass; requirements can be strict on length and encoding parameters. citeturn22search1turn22search5turn21search2  

The dominant cost driver is not Markdown parsing; it is the **long-tail pronunciation and non-prose narration decisions** (tables, equations, appendices, and references). This is predictable from the presence of dense appendices and tables in the source. citeturn23view0turn19view2turn18view0