---
name: academic-paper-craft
description: Use when writing or auditing ML papers to prevent AI tells.
version: 1.0.0
author: Ruihan Su (MichaelSou1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [academic-writing, anti-vibe-paper, peer-review, narrative-framing, latex, ml-conferences]
    related_skills: [academic-method-writing, academic-related-work, academic-paper-naming, anti-defensive-writing, natural-english-writing]
---

# Academic Paper Craft & Anti-Vibe Guardrails

Draft, revise, and audit academic manuscripts (CVPR, ICCV, ECCV, NeurIPS, ICML, ICLR, ACL, EMNLP, COLM) so they carry an unmistakable central thesis, airtight claim-to-evidence alignment, self-contained figures, clean LaTeX typography, and zero LLM "vibe paper" fingerprints.

## When to Use

- Drafting or restructuring full manuscripts, Abstracts, Introductions, Experiments, Conclusions, Captions, or Appendices
- Auditing an existing draft from a peer-reviewer perspective to eliminate LLM ghostwriting traces ("vibe paper" tells)
- Revising manuscripts or proposing targeted modification plans without breaking global consistency
- Reframing experimental narratives or trade-offs when initial hypotheses shift or individual metrics lag
- **Don't use for:** standalone BibTeX search (`arxiv`), naming acronyms in isolation (`academic-paper-naming`), or early pre-code brainstorming (`ml-research-spec-design`). Load `academic-method-writing` alongside this skill for deep codebase-to-equation verification, and `academic-related-work` for Related Work architecture.

---

## 1. Macro Narrative: The Launch Event Principle (发布会原则)

Treat a paper as a focused academic launch built around its strongest proven value, never as a chronological lab log, work report, or self-audit.

1. **Organize strictly around defensible strengths.** Identify what is genuinely novel, leading, or irreplaceable (new capability, mechanism, perspective, applicability, efficiency, scalability, or meaningful trade-off). Content that does not support this core advantage does not belong on the main narrative spine.
2. **Never write a chronological trial-and-error log.** Do not narrate "first we tried X, then Y failed, so we added Z." Retain only the final standing logic: why the problem matters -> why prior methods fall short -> what mechanism we introduce -> how evidence proves it.
3. **Open Abstracts and Introductions like a launch keynote (never 1–2 stiff paragraphs).** A 1–2 paragraph Introduction with an abrupt motivation is an immediate desk/borderline-reject signal. Build a complete 4–5 paragraph funnel:
   - Concrete, important unsolved problem and real-world/scientific stakes;
   - Specific structural gap in existing paradigms (with verified citations);
   - Core insight and clean high-level mechanism (without premature implementation trivia);
   - Strongest empirical findings and concrete takeaways.
4. **Never shift high-level focus onto prompt-induced minutiae.** When an author asks to add a small constraint, edge-case fix, or auxiliary detail, integrate it proportionally at its local technical level. Never elevate a minor engineering patch into a headline motivation or sudden narrative detour (which exposes iterative user-prompting traces).
5. **Reconstruct the story around the strongest evidence.** When empirical results do not support the original hypothesis, do not defend the old framing. Redefine the problem scope, re-rank contributions, and rebuild Title/Abstract/Intro around what the evidence actually proves.
6. **Keep Conclusions strictly to memory reinforcement.** Summarize what was solved, proposed, and proven, and why it matters. Never introduce surprise self-doubt, new caveats, or expanded failure modes in the final paragraph.

---

## 2. Claim-Evidence Alignment & Experimental Framing

1. **Map every core claim to explicit evidence.** Every motivation raised in the Introduction must be answered in Experiments. Maintain an explicit mental (or side-column) ledger: `Core Claim -> Figure/Table ID -> Quantitative/Analytical Result`. If evidence is missing, narrow the claim's scope immediately rather than leaving a broken promise.
2. **Treat experiments as argumentative tools, not result warehouses.** Every experiment and ablation must serve at least one explicit job:
   - Prove the core method works on the target problem;
   - Attribute gains to the claimed mechanism;
   - Demonstrate value in the target operating regime;
   - Rule out the primary competing explanation.
   Delete, compress, or move to the Appendix any experiment that distracts from the main thesis or opens tangential debates.
   - **Data-leakage & split-role discipline:** Audit every evaluation split across four contamination axes before presenting it as a blind test set: (1) *development leakage* (any subset used for stopping criteria, reward shaping, or failure-driven iteration), (2) *in-domain environment/template overlap* with training tasks, (3) *perturbation/generator isomorphism* between training and test injectors, and (4) *public trajectory pretraining exposure*. Position any split with development or generator overlap transparently as a **Controlled Diagnostic & Ablation Testbed** (for dose-response curves, step-level timing, or credit-assignment diagnostics), and anchor headline external validity on untouched, independently authored benchmarks.
   - **Cross-run benchmark ledger hygiene:** When aggregating historical benchmark runs from a project repository, never merge or subtract scores across mismatched observation/action harnesses (e.g., DOM + multi-action vs. screenshot-only coordinate single-action, or different context/step caps); place incompatible protocols in separate tables, exclude aborted/invalid-protocol or pre-navigation-corrupted runs, and match denominators on shared valid instances with `UNKNOWN` / `INFRA` isolated.
3. **Explicitly articulate advantages in prose.** Never expect reviewers to infer contributions from bold numbers in a table. State *where* the method wins best, *why* the mechanism causes that gain, and *what* practical bottleneck it resolves.
4. **Reframe unfavorable metrics without language of defeat or reviewer bait.**
   - Do not set uncompetitive dimensions as the paper's primary arena; define evaluation around the task constraints, regimes, or cost-performance trade-offs where the method genuinely wins.
   - Never volunteer self-weakening verdicts (`Unfortunately`, `merely`, `lags significantly behind`, `limited effectiveness`, `遗憾的是`, `仅仅`, `效果有限`).
   - State exact conditions and trade-offs neutrally (`reduces latency by 40% while retaining 89.0% accuracy vs. 90.0%`), narrow claims to avoid unnecessary head-on collisions, and never generalize a local phenomenon into a global flaw of the method.
   - **Priority order for sub-optimal material:** (1) Delete if irrelevant to core claim -> (2) Narrow claim scope -> (3) Shift to a more faithful evaluation dimension -> (4) Frame as an objective target/cost trade-off -> (5) Reorganize tables/figures to center the core strength -> (6) Reconstruct the narrative -> (7) State a calm, bounded limitation *only* when unavoidable and directly affecting core validity.
5. **Zero defensive disclaimers.** Following `anti-defensive-writing`, state what the paper *does* and *shows*; stop explaining what it "does not claim" or preemptively answering unasked hypothetical objections. Place genuine methodological boundaries once, calmly, in Method or Limitations.

---

## 3. Section Hygiene & High-Risk Reviewer Spot-Check Zones

1. **Method (Notation, Pacing, Pseudocode, Baselines):**
   - **Define every symbol at first use (`denote`).** Never drop undefined scalars, sets, or operators into equations.
   - **Ban fragmented equation pacing.** Never write staccato `"one short clause -> display formula -> one short clause -> display formula"` chains. Weave simple definitions inline and reserve display equations for coherent, non-trivial derivations and core objectives.
   - **No zero-information pseudocode.** Do not include `algorithmic` blocks that merely transcribe a standard forward pass or 3-line loss sum already clear from equations. Reserve pseudocode for non-trivial multi-stage control flow, asynchronous loops, or custom data-filtering algorithms.
   - **No premature baseline comparisons or motivational citation clutter in Method.** Keep Method focused on *your* formulation and mechanistic rationale: cite only the exact foundational environment, backbone, or optimization algorithm your method directly instantiates, and keep problem-gap or peer-method citations (`\cf~\cite{...}`) in Introduction and Related Work. When a table defines symbol or binary-indicator semantics, reference the table instead of duplicating those definitions in body prose.
2. **Figures & Table Captions (Blind-Cover Self-Containment Test):**
   - Cover the main text and inspect each Figure/Table + Caption alone. Never merely repeat the figure title.
   - Explicitly specify: **experimental subject/model, groupings/conditions, X/Y axis quantities & units, color/marker/line encodings, sample size $n$ (distinguishing independent subjects/runs/seeds from repeated measurements on the same instance), bar/point aggregator (mean vs. median), and error-bar/band definition (SD, SEM, min-max, or 95% CI)**. Never guess statistical semantics from visual appearance—check code/logs or ask the author.
   - Ensure every figure directly backs a specific judgment in the Results prose.
3. **Related Work & Citations:**
   - **Zero hallucinated or semantically mismatched citations.** Never cite from parametric memory. Verify exact authors, title, venue, and whether the cited paper actually makes the specific technical claim attributed to it.
4. **Appendix (Highest AI-Trace Disaster Zone):**
   - Reviewers spot-check Appendices specifically to catch lazy LLM dumps. Apply the *exact same* prose, notation, and formatting standards to the Appendix as to the main text: no unedited Markdown lists, no boldface spam, no verbatim repetition of main-text paragraphs.
   - **Bidirectional linkage:** Every Appendix section, proof, or table must be explicitly referenced (`Appendix A`, `Table S2`) at the exact point in the main text where that question arises.

---

## 4. Paragraph Architecture, Naming & Formatting Guardrails

1. **Cohesive argument paragraphs over fragmented micro-paragraphs.** Never start a new paragraph every 1–2 sentences. Build 4–7 sentence paragraphs around one unified claim: clear topic sentence -> mechanism/evidence development -> link back to the section argument.
2. **Ban bullet-point and numbered-list abuse.**
   - Write continuous academic prose by default. Never copy Markdown lists (`1. ... 2. ...` or `- **Header:** ...`) into LaTeX paragraphs.
   - Never flatten **sequential, causal, or progressive** logic into parallel bullet points. Reserve bullets strictly for genuinely parallel enumerations (typically only the 3-item Contributions summary at the end of the Introduction, if venue-appropriate).
3. **Restrained, consistent terminology and zero boldface spam.**
   - Do not coin pretentious neologisms for standard concepts. Keep module names concise (2–3 words max).
   - **Global terminology lock:** Use one canonical full name (defined with its acronym at first appearance in Abstract and again in Main Text) and *identical* casing/hyphenation/abbreviation across every section, figure, and appendix. Never synonym-cycle technical terms.
   - **Visual hierarchy discipline:** Ban inline `**boldface**` / `\textbf{}` inside body sentences to emphasize keywords or module names. Limit boldface to `\paragraph{}` lead-ins and best-result cells in tables.

---

## 5. Micro-Style, Lexicon & LaTeX Punctuation Blacklist

1. **Eliminate GPT punctuation fingerprints:**
   - **Zero full-width Unicode punctuation in English LaTeX** (full-width hyphens `－`, Chinese parentheses `（）`, colons `：`, commas `，`, curly quotes `“ ”`). More than three full-width hyphens/dashes on a page is an instant reviewer tell of uninspected copy-paste.
   - **Strictly ration em-dashes (`---` / `—`) and semicolons (`;`).** Default to zero em-dashes per page; rewrite parenthetical insertions with commas, parentheses, or separate sentences. Do not chain clauses with semicolons.
   - Use proper LaTeX dashes: `-` (compound words), `--` (numeric ranges `1--5`), and straight TeX quotes `` `...' `` / `` ``...'' ``.
2. **Ban characteristic LLM sentence templates:**
   - Ban mid-sentence `, therefore,` (`X is bounded, therefore, Y converges` -> comma splice / GPT tell; use crisp causal verbs or sentence-initial `Consequently,` / `Thus,` sparingly).
   - Ban hollow throat-clearing and boilerplate transitions: `It is worth noting that`, `It should be noted that`, `Notably,`, `Importantly,`, `Crucially,`, `This ensures that`, `This allows the model to`, `Not only ... but also ...`, `It is not merely X, it is Y`.
   - Ban superficial trailing participle (`-ing`) clauses tacked onto sentence ends (`..., highlighting its effectiveness`, `..., ensuring seamless integration`, `..., underscoring the importance of`). State the concrete causal effect or stop at the period.
3. **Ban flashy puffery adverbs and baseless assertions:**
   - Strip zero-information adverbs: `elegantly`, `seamlessly`, `naturally`, `theoretically` (when no theorem follows), `remarkably`, `dramatically`, `meticulously`, `intrinsically`, `fundamentally`.
   - Never echo user prompt adjectives (`propose a lightweight plug-and-play X` -> repeating `lightweight plug-and-play` in every paragraph). Show the property once via flop/parameter counts or equations.
   - Never make sweeping, unbacked assertions in an authoritative tone; ground every factual statement in a citation, equation, or table number.
4. **Write plain, high-clarity English (`natural-english-writing`).** Prefer concrete subjects and direct verbs over roundabout nominalizations and stacked 5-noun strings. Clarity and precision beat artificial complexity.

---

## 6. Workflow: Context Scoping, Burden-of-Proof Edits & Global Consistency

1. **Strict grounding in current manuscript and verified artifacts.** Base edits strictly on the provided draft, experimental logs, codebase, and verified primary literature. Never invent missing ablation rationales, hypothetical failure modes, or unrequested defensive caveats that conflict with existing sections.
2. **Modification Request Report (Burden of Proof) for major revisions.** Before directly mutating a mature or multi-section draft, present a structured **Modification Request Report** so the author retains full editorial control. For each proposed non-trivial change, justify:
   1. **Current flaw:** Exact quote/location and what concrete problem it causes;
   2. **Necessity check:** Does the argument genuinely fail or mislead a reviewer if left unchanged? (If it is mere stylistic preference with high churn, drop it);
   3. **Proposed fix:** Concrete replacement phrasing or structural move;
   4. **Global ripple effect:** Which other sections, symbols, equations, captions, or forward/backward references must update in tandem;
   5. **Cognitive load check:** Does this edit simplify the reader's path, or patch one local hole at the cost of confusing the main thread ("fixing the head while breaking the tail")?
   *Completion criterion:* Wait for author approval on structural/scope changes before applying `patch` / `write_file` to `.tex` manuscripts (unless explicitly told to rewrite directly).
3. **Mandatory Full-Text Consistency Pass after drafting or editing a section.** LLMs naturally drift across long contexts and equalize major vs. minor points ("treating watermelons and sesame seeds as equal"). After finishing any chapter or revision batch, audit across the entire manuscript (`search_files` / `read_file`):
   - Information hierarchy: core contributions get space and prime placement; minor implementation details stay subordinate;
   - Terminology, acronym, and mathematical symbol consistency from Abstract -> Intro -> Method -> Experiments -> Appendix;
   - Claim scope parity (Abstract/Intro claims == Experiment evidence == Conclusion summary);
   - Cross-reference integrity (`\ref`, `\eqref`, `\cite`, and main-text pointers to every Appendix section);
   - Automated deterministic scan on drafted files (regex check for `—` / `---`, `;` outside math, full-width CJK punctuation, inline `**bold**` outside `\paragraph{}`/table headers, raw Markdown bullets in prose, double-escaped LaTeX macros like `\\mathrm`, and blacklisted filler words like `Crucially`/`Notably`/`iff`).

---

## Pitfalls

- **Fixing weak evidence by adding defensive hedges instead of narrowing the claim:** Pasting "although our evaluation is preliminary..." leaves the overclaim intact while adding reviewer bait. Narrow the claim sentence itself to match what the table proves.
- **Treating every user prompt tweak as a paper contribution:** If the user says "mention we clip values to $[-1, 1]$ for stability," add half a clause in the implementation paragraph—never rewrite the Method motivation around value clipping.
- **Prematurely merging downstream definitions into early conceptual tables:** Adding a forward-referenced column (e.g., downstream RL reward tiers inside an early problem-formulation or evaluation taxonomy table) forces readers to parse undefined symbols before reaching the subsection that motivates them. Keep each table scoped to concepts already defined at its point of appearance.
- **Placing `table*` / `figure*` at the end of a LaTeX subsection:** In two-column conference styles, full-width `*`-floats appear at the earliest on the page *after* their declaration; declaring them at the bottom of a subsection pushes them onto a later section's page. Declare `table*[t]` / `figure*[t]` near the start of the subsection and verify float pages in `main.aux` alongside a zero-`Overfull \hbox` log check.
- **Using plain justified `p{...}` columns or parenthetical clutter in narrow single-column LaTeX tables:** Narrow `p{...}` cells (~2–3cm) in two-column templates stretch inter-word gaps and hyphenate short words across lines. Define a ragged-right hyphen-free column type (`\newcolumntype{L}[1]{>{\raggedright\hyphenpenalty=10000\exhyphenpenalty=10000\let\newline\\\arraybackslash}p{#1}}`), strip parenthetical sub-explanations from compact indicator cells, and check both `Overfull` and `Underfull` box warnings on build.
- **Copy-pasting Markdown artifacts into `.tex`:** Leaving `**bold**`, Unicode `—`, curly quotes, or inline `1) ... 2) ...` lists inside LaTeX prose immediately flags unedited LLM output.
- **Guessing error-bar or sample-size semantics in captions:** Writing "mean $\pm$ std over 5 seeds" from visual inspection when the plot actually shows 95% CI or repeated trials on one scene introduces factual falsification. Verify plotting scripts first.

## Verification Checklist

- [ ] **Launch narrative:** Abstract/Intro establish problem -> gap -> mechanism -> headline evidence (4–5 paragraphs, zero chronological lab-log narration)
- [ ] **Claim-evidence ledger:** Every main claim maps to a specific Figure/Table/Equation; unsupported claims narrowed, tangential experiments pruned
- [ ] **Zero defensive self-sabotage:** No preemptive "we do not claim..." or self-deprecating verdicts; unfavorable metrics framed neutrally as explicit scope/trade-offs
- [ ] **Method hygiene:** Every symbol denoted at first use, zero fragmented clause-formula-clause chains, zero redundant pseudocode, zero premature baseline comparisons
- [ ] **Blind-cover caption test:** Every Figure/Table caption states subject, axes/units, encodings, $n$ (independent vs. repeated), and exact error-bar definition
- [ ] **Appendix & bibliography audit:** Every citation verified against primary sources; every Appendix item cited in main text and held to main-paper prose standards
- [ ] **Anti-AI style & LaTeX scan:** Zero full-width punctuation, zero em-dash/semicolon spam, zero mid-sentence `, therefore,`, zero `elegantly/seamlessly/notably/this ensures that`, zero body boldface spam, zero unjustified bullet lists, and full-text terminology/symbol consistency verified
