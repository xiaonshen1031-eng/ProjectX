# Project research and delivery playbook

Use this reference for commissioned research, technical services, engineering studies, and task-book-driven reports. The customer contract, accepted outline, and retained template control the deliverable.

Apply the six-class language requirements in [writing-and-release.md](writing-and-release.md) to every final client report: no confirmed experimental-report, AI formulaic, stacked, redundant, defensive or mechanical prose. These requirements cover summaries, body, captions, table text/notes, conclusions, recommendations and technical appendices. Preserve Chinese engineering subjects, customer wording, accepted chapter structure and Project formatting.

## Task contract

Translate each requirement into a technical question with explicit data objects, unknowns, units, constraints, method, validation evidence, and report location. A small request may use one task and one chapter brief; do not require a complete project directory before answering a self-contained calculation or section request.

Respect the assigned subtopics and current deliverable. A partial contribution is not the whole contracted topic. A report revision is not a request to rerun the research, and a PPT adaptation is not permission to copy paragraphs verbatim, add a cover page, or create sections outside the assigned work. Read the retained customer template for structure, wording, visual hierarchy and object behavior before adapting content.

When a presentation is requested, rewrite the model and findings into the template's reporting language rather than shortening report paragraphs mechanically. Check text-box fit, arrow endpoints, connector crossings, equation placement and font compatibility in the saved/reopened deck and rendered slides. A companion explanation follows the accepted slide sequence when requested; it does not introduce another research structure.

Keep task identity separate from competition question numbers. New tasks use `task_id`. Preserve `question_id` only when an older workspace consumer requires it.

## Data content and population

Audit the contents needed to answer the question, not just file existence. Verify field meaning, declared unit, unique identifiers, sampling times, ranges, missing values, duplicates, legal zero values, object counts, aggregation, join keys, and join coverage. Distinguish measured, public, reconstructed, simulated, and synthetic data. An absent observation is not zero unless the source contract says so.

Training, parameter-estimation, validation, and delivery populations can differ. Report which population each calculation uses. Keep raw input read-only; preserve the processing code and only the input-to-output relationships needed by current consumers.

When the contract permits regional adaptation of public data, explain the source curve, scenario classification, normalization, scaling basis, time alignment, aggregation weights, and physical constraints. Separate observed regional totals from adapted profiles and model-calculated response. Put these facts together in the data/method section, without repetitive caveats below each figure. Do not describe an adapted or simulated series as a local measurement. Never invent a source for an assumed parameter; name the assumption and its engineering role.

Make the regional mapping computable: identify the source archetype, target regional/category total, weight denominator and final time-step unit. Verify conservation after scaling, avoid counting overlapping source groups twice, and apply regional weather or calendar changes only through a stated transformation. Annual energy, installed capacity, coincident power and peak power are different scaling targets. An undocumented input unit requires a reasoned unit decision and magnitude check in the working record; put the selected unit and any result-sensitive assumption once in the data section, not in repeated plot warnings.

## Model and solve

Start from the mathematical structure. State knowns, unknowns, controls, state, time and space indices, units, assumptions, constraints, and objective. Use direct calculation or an analytic relation when it answers the question. Add prediction, simulation, optimization, or machine learning only when the technical problem requires it.

The built-in solver contracts are narrow:

- `solve-allocation`: continuous multi-period charging LP. It does not accept integer requirements.
- `bounded-sum`: exact greedy solver for a continuous linear objective with one total-sum equality and independent lower/upper bounds.
- `replay-dag`: timing replay for a caller-supplied topological and resource order. It evaluates that order and never claims optimal scheduling.
- Project-specific scripts: declare inputs, outputs, units, solver assumptions, and validation functions in the task contract.

Retain an infeasible or adverse result when input and model checks show it is real. Identify conflicting capacities, windows, bounds, or required inputs. Do not switch the contracted problem automatically.

## Independent validation

Reconstruct the result from delivered objects without trusting only solver status. Substitute into original equations and hard constraints; check units, dimensions, bounds, conservation, and object coverage. Where applicable, compare a small analytic case, lower or upper bound, primal/dual relationship, baseline, perturbation, or data not used for model choice.

Repeated execution of the same function verifies reproducibility, not independence. A finite result and a `success=true` flag do not prove feasibility.

## Cross-task lineage

Pass explicit objects between topics: a parameter set, prediction series, feasible region, state, resource boundary, or chosen plan. Record meaning, unit, time scale, object identifier, applicability, and actual source. Use `record-lineage` only for files with a downstream consumer. When an upstream input changes, `check-lineage` marks the affected artifacts stale; recompute those artifacts and their dependent prose.

Keep proxy and original operators separately named. When a proxy proposes a candidate, evaluate it with the original engineering relation when feasible. Shared parameters do not imply shared dynamic state.

## Chapter context and prose

A chapter brief points to exact current paths, JSON pointers, and bounded table slices. Read those sources at writing time. Separate:

1. calculation or measurement;
2. interpretation supported by that evidence;
3. engineering recommendation and its conditions.

Use the customer outline. Without one, start from project overview and tasks; objects, materials, and data; one or more technical topics organized as problem/model/solve/validate/analyze; integrated technical evaluation and recommendations; conclusions; and only the necessary references or appendices. Merge and remove sections freely. Do not force novelty claims, a literature-gap funnel, fixed chapter counts, figure quotas, or reference quotas.

### Connected client-report prose

Write around the contracted topic. Reference papers support a model or parameter choice; identify them by title/author or a resolvable citation, not headings such as “论文1–4复现”. Do not import a project's region, load categories, case count, chapter count, or numerical conclusions into another project.

Make the technical dependency readable: input data define the research objects; those objects enter state relations, physical constraints, estimation or optimization; the solution produces quantities used in the subsequent analysis. Explain the intermediate model, not just input and output labels. Define new symbols where they enter the argument and carry the same objects into later sections. An aggregation stage followed by forecasting is appropriate only when the task actually requires both.

Explain why each central relation is used, what it receives, how its parameters are obtained, and which calculated quantity is passed onward. Equations are part of this derivation, not detached formula cards. Define newly introduced or recontextualized symbols together; do not repeat a full symbol dictionary after every equation. Describe an actual methodological improvement through the changed relation and enabled capability when the contract calls for innovation, without inventing a novelty section or claiming innovation from a renamed workflow.

Read each revised paragraph together with its neighbors. Connect them through a shared quantity, condition, equation, result, or engineering question. Combine short factual sentences with longer relational sentences; do not put every sentence into its own paragraph or replace fragmented prose with one long enumeration. Removing transition words alone does not repair a missing relationship.

Results explain a finding with a few decisive values, its supported mechanism or active constraint, and the implication for the contracted question. Tables retain exact values; figures expose patterns; prose interprets them. Do not replay every table cell, force the same paragraph template, or append “证明模型有效” after each figure. Comparisons name the actual baseline, what changes between cases, what remains fixed, and which metric answers the question. Add only comparisons required to substantiate the contracted conclusions.

Keep “证据链”“证据角色”“口径”“闭环”“审计通过”, solver success flags, chapter briefs, file paths, JSON pointers, and revision status in internal JSON/Markdown records when they are authoring/checking concepts. In report prose, state the actual quantity, calculation, or result. These are contextual rules, not a ban on legitimate domain terminology or on a source's official wording. Final Project reports always write the engineering result directly; remove empty agenda/report narration such as “本次实验”“为验证有效性” and an unsupported “实验结果表明”. Preserve substantive scientific protocol, data-source descriptions and the actual observed result in their proper sections.

Remove every confirmed instance of defensive framing without removing material facts. State the modeled time scale, source type, assumption, zero result, unfavorable comparison, or infeasible case directly where it matters. A single rhetorical “仅供参考”“虽然……仍有价值”“不能视为……” requires revision; do not replace it with unsupported certainty. Source disclosure belongs in the data section; a genuine feasibility restriction or case-specific applicability condition belongs with the affected relation or result. Do not require a boilerplate limitations or future-work paragraph in the conclusion.

For example, replace “图3承担证据链闭环职责，虽然存在不足但仍有参考价值” with the supported relationship, such as “图3中的可调功率随持续时间延长而下降，主要受累计能量约束限制。” The example is a writing pattern, not a finding to copy without data.

### Results that continue the model

Organize analysis by engineering questions, not by plotting order. Introduce the output being analyzed and the relevant case conditions; interpret its variation using the relations and constraints already established. Carry the resulting quantity into the next question rather than finishing each figure with a disconnected summary. Long and short sentences should follow the reasoning, not a length quota.

Before writing a finding, check its region/object, time window, unit, statistic and denominator against the current arrays or tables. Distinguish a maximum from an average or quantile, capacity from energy, response from recovery, and a pointwise limit from accumulated feasibility. A flat maximum below a limit is not a progressively rising maximum. Compute coincident regional totals from aligned series rather than adding each region's separate peak; recompute a reversed improvement percentage with its new denominator. A plotted shape alone does not establish a causal mechanism: use the state relation, binding constraint or controlled comparison to explain it.

Use named, informative cases: the actual operating/reference case, a specific modeling or adaptation alternative, or a required parameter/condition change. State what changes and what stays fixed. A shape comparison after normalization and an absolute-scale comparison answer different questions; do not call annual energy equal unless it was actually held equal. Report the primary metric and any decision-relevant trade-off rather than ranking the method as universally best. Do not add cases, prediction stages or robustness studies merely to make a finished project look larger.

If the user asks to omit zero-valued display items, omit the specified rows/series only from that view and its layout. Keep valid zeros in source data and calculations; preserve the original aggregation denominator and adverse results. Missing, unavailable and infeasible values are not zero. A scenario envelope is not a statistical confidence interval, and uncertainty bands require their actual estimator and population.

## Chinese figures

Each figure records its technical question, source results, variables and units, comparison, type, final width, caption, and prose location. Tables carry exact values. Figures carry distribution, process, geometry, constraints, trade-offs, allocation, or diagnostics. Text explains why the observed relationship answers the question.

At final physical size, use 9–11 pt axis labels and 8–10 pt ticks/legend. Prefer Times New Roman for Latin text/numbers and an installed Microsoft YaHei bold or SimHei regular for Chinese text. Record a fallback truthfully. Avoid a default total title, preserve aspect ratio, and check both the standalone export and the inserted page for clipping, overlap, occluded data, and missing glyphs.

Choose complementary figure types from the relationships being analyzed. Do not turn a request for richer information into an all-heatmap, all-bar, or all-line report. Use sourced conditional, constraint, allocation or multi-metric diagnostics. Do not emit standalone simple bars, simple lines or sparse scatter views. Avoid explanatory paragraphs or defensive notes burned into the plot footer; put essential units, case definitions, and concise captions in their proper locations. Preserve accepted figure assets during a prose-only revision.

Useful mappings include response/recovery trajectories with constraint boundaries for dynamics; stacked allocation or shared-scale small multiples for regional composition; duration–capacity envelopes for sustained capability; distributions or empirical cumulative curves for heterogeneity; heatmaps for genuinely dense time–region matrices; and paired profiles or multi-metric comparisons for case changes. Use only mappings supported by the outputs. Do not enforce a plot-type quota, add decorative 3D, or fill space with repeated encodings. One complementary multi-panel view may replace several sparse plots, provided its panels share meaningful scales and retain readable labels.

Inspect all text objects, including Chinese category ticks, legends, colorbars and annotations. Do not set every tick to Times New Roman when some ticks contain Chinese. For mixed Chinese/Latin labels, use verified glyph fallback or separate aligned text runs; if Latin weight must remain regular while Chinese is bold, use separate runs rather than claiming one global font weight satisfies both. In MATLAB, an axes-level TNR setting is suitable for numeric ticks, not automatically for Chinese categories. Caption units and plotted units must agree. Check complete axes frames, legend placement and actual inserted dimensions; source font sizes and a high dpi alone do not establish readability.

## Word formulas and delivery

### Default Project formatting profile

Current explicit requirements take precedence over customer templates, which take precedence over this reusable Chinese engineering-report profile. The bundled allocation-example builder applies this profile; for a different customer template, adapt the renderer rather than silently resetting its styles.

| Element | Default and checks |
| --- | --- |
| Page and body | A4; Chinese SimSun/宋体, Latin and digits Times New Roman; black, regular 12 pt/小四. First-line indent two Chinese characters; 1.5-line spacing, with no extra blank paragraph between ordinary paragraphs. |
| Headings and title | Black, regular SimSun Chinese with Times New Roman Latin/digits; size and spacing establish hierarchy. No inherited blue theme, bold SimHei, underline, or decorative rule. Explicit customer heading rules override. |
| Data tables | Three black horizontal rules: top, below header, bottom. No vertical lines, internal row grid, or gray/colored shading. SimSun/TNR regular 10.5 pt/五号, single spacing, zero first-line indent; repeating header and readable cell padding. Default rule weights may be 1.5/0.75/1.5 pt. |
| Display equations | Center the actual native object in the usable text area; continuous numeric `(1)`, `(2)`, … at the right margin unless the retained template specifies chapter numbering. Zero character/point indents; replace inherited MathType tab stops with intentional center/right stops. Keep equation numbering distinct from the object. Borderless equation-layout tables are not data tables and must not acquire three-line borders. |
| Inline mathematics | Same editable backend as display equations, including symbol definitions, prose references, captions, and table headings/cells. Body context 12 pt, table context 10.5 pt at final size; check baseline and line height after conversion. |
| Captions and references | Explicit paragraph roles, not loose prefix matching. Caption indent zero; references left-aligned with a readable hanging indent, not full justification that stretches English. References use black regular SimSun/TNR 12 pt and 1.5-line spacing unless the customer specifies otherwise. Keep captions with the corresponding table/figure. |
| Figure labels | Separate from document text: the approved plotting font profile may use bold Microsoft YaHei. Never apply that bold font to the body or tables. |

For OOXML, encode two-character indentation as `w:firstLineChars="200"` with a compatible 24 pt fallback for 12 pt text; encode 1.5-line spacing as `w:line="360" w:lineRule="auto"`. It is a line multiple, not `exact` point spacing. Table single spacing is `240/auto`. Set both character-based and point-based indents to zero for non-body roles so inherited values cannot survive.

Do not classify a paragraph beginning “图1与表3……” as a caption. Use its semantic role/style; if legacy text detection is unavoidable, require a real caption delimiter and inspect context. Do not add an empty spacer paragraph after every table. Use modest paragraph spacing and remove only identified generated spacers, never page breaks, fields, or user content wholesale.

### Native equation coverage and conversion

The default final backend is `mathtype_native`; `office_math` is an explicitly selected alternative. Plain italic letters, Unicode subscripts, equation pictures, and raw Toggle TeX are not native MathType. A display-equation count alone cannot establish completeness: inventory genuine mathematical references throughout prose and tables, without converting units, acronyms, case names, or ordinary numbers unnecessarily.

Maintain ordered formula IDs, exact case-sensitive TeX, inline/display placement, context, and intended font size. Uppercase and lowercase symbols are distinct: PowerShell's ordinary hashtable is case-insensitive, so token inventories must use an ordinal case-sensitive dictionary. Include repeated occurrences and table-header formulas; preserve source order, not merely a set of unique expressions.

Protect the original. Build an immutable source-only Toggle TeX copy, then call conversion once per output copy. Never re-toggle an already converted document. Verify real Equation Native/MTEF content, correspondence to each intended expression, previews, actual Word page rendering, and save-close-reopen persistence. ProgID, object counts, or converter success alone do not establish authenticity. Where the native-content comparison uses independent conversion, create it from a separate copy of the same unchanged source, not by toggling the primary result again.

After conversion, check table equations at table text size and body equations at body size; font metadata in a source manifest does not resize a native object by itself. If display scaling is needed, derive it from the original dimensions and target context so rerunning the layout pass does not shrink it again. Preserve native equation payloads during style-only repairs, bind final verification to the actual final file, and repeat the affected render/reopen checks. Do not claim manual editability or visual review that has not been performed.

### Centered native equations with right-hand numbers

Number display equations only; repeated inline symbol references are not numbered equations. Use Word `SEQ Equation` fields or the customer's existing MathType numbering system, with a cached numeric result visible after save. Keep the number in an ordinary black TNR run outside the native formula. Update equation cross-references after insertion, deletion or renumbering, preserving existing bookmarks and field targets. Do not replace a native object with typed text or an image to add a number.

For an ordinary one-column body paragraph, obtain usable width from the paragraph's current section: page width less left/right margins and any gutter. Clear inherited local/style tab stops and both character/point indents, use a left-aligned paragraph with an intentional center tab at half the usable width, place the unchanged object after that tab, and place the number after a right tab at the usable width. Centering the whole equation-plus-number paragraph shifts the formula away from the text-area center. Never copy fixed tab positions from a previous report. Multi-column sections, layout tables, floating objects, very wide or multiline formulas require template-specific layout and render review rather than this helper.

`scripts/project_equation_layout.py --docx report_native.docx --manifest equation_source.json --output report_numbered.docx` applies that limited layout after conversion. It uses the ordered inline/display inventory, preserves all ZIP parts except the main-document layout XML, refuses ambiguous paragraphs and special section layouts, and does not run Toggle TeX, resize formulas, or certify their mathematical content. Existing native evidence must be rebound/rechecked against the numbered final file; its old file binding must not be reused as final approval. Rerunning the helper on its own output must not add duplicate numbers or tabs.

Check actual Word placement, not only `w:jc`: the formula should lie at the center of the usable text area, the number should be at the right margin, and both must share the intended line without collision. If measurement is available, compare object center to text-area center and inspect the page. Allow formula height to grow naturally instead of forcing an exact line height that clips fractions or matrices. Keep closely related equations together where they form one derivation, and keep their explanatory paragraph nearby; do not turn this into a rule that forces all equations onto one page.

## GB citations and bibliography

For a Chinese Project report, default to GB/T 7714 sequential citation unless the current user or customer template selects another system. Verify which edition applies at delivery time through the official standards source; publication year and effective date are separate. Do not perpetually label an older edition as current. Match the selected edition's document-type markers, punctuation, author handling and electronic-source requirements.

Verify reference metadata against the publisher, official repository or dataset record: actual authors/contributors, exact title, publication year, journal/volume/issue/pages or article number, version, DOI/URL and required access date. A year inside a DOI is not necessarily the publication year. Observation year is not article year. A dataset may have contributors and a version different from its related article; cite the dataset for the data and the article for its method where each is used. Do not replace an unknown dataset title with a locally invented description, and do not turn a local folder path, “本项目文件” or “公开作者稿” into a bibliographic record. Never invent missing metadata.

Order references by their first actual citation in report reading order, including captions and tables when they introduce a source; repeated citations keep the same number. Check absent entries, duplicate entries/numbers, unused references, stale ranges and citation referents after restructuring. Every retained reference must have a legitimate use; do not insert irrelevant citations just to consume a bibliography. A reference supports the specific data, relation or claim next to it, not an unrelated paragraph. Keep citation appearance consistent with the retained template and keep hyperlink text black under the Project profile.

### Bounded revision and final checks

Before rewriting a mature report, preserve a recoverable original and identify the requested edits. Freeze accepted data, model relations, numeric results, and figure assets unless the user reopens them or a verified error requires correction. Repair complete affected paragraphs and their transitions; do not start new analyses merely because the language needs work.

Export the final DOCX to PDF and inspect every actual page. For full research delivery, run the Project delivery audit with the data audits, result, independent validation, figure manifest, MathType evidence, PDF, and a page-review record. For a formatting/prose-only revision, compare the changed document with the accepted source and reuse unaffected research checks; do not rerun unrelated experiments or invent missing solver artifacts to satisfy the allocation-example audit. Native formulas still require current-file preservation/authenticity and render/reopen checks. The audit does not request conference anonymity, journal highlights, reviewer scores, or claims of novelty.

For native MathType on Windows, prefer the installed Word renderer so conversion does not replace or damage embedded objects. If the generic renderer lacks its required Office/LibreOffice backend, use a verified available route, record that choice internally and inspect its output; do not call an unrun renderer successful. Render review applies to the final file. Previously reviewed pages can be reused only when their rendered pixels are unchanged; inspect all changed pages and ensure the final review still covers the full document.

Check effective styles and direct overrides, not just style names: body/table sizes, line multiples, indents, black text, actual table borders and fills, formula placement, and caption roles. Compare preserved numbers/figures before and after a prose-only edit. Inspect all pages for split headings, detached captions, excessive blank space, clipped equations, and stretched references. Run `scripts/check_writing_quality.py report.docx --manuscript-mode project --language chinese --require-clean` on the actual final report. Resolve candidates by revision/rescan or current-text-bound scientific-content review, then complete a full manual semantic reading of all prose and table text for the shared six classes. Draft advisory output or a high score cannot approve final prose. Deliver the requested report, not internal receipts or intermediate versions unless requested.

Final checks are separate: technical/numerical consistency; connected paragraph-level reading; effective Word/table/figure typography; native formula content plus centered numbered rendering; and reference metadata/first-citation order. Passing one does not establish the others. Keep checking records and recoverable prior versions outside the final handoff folder. Deliver one clearly identified current report rather than a pile of iterative variants, without deleting user source files or accepted assets.

`scripts/audit_project_delivery.py` also applies the shared final language gate directly to the current DOCX. It rejects unresolved editorial candidates, invalid review decisions and definite text contamination without a separate language flag. Use its optional `--review-decisions` only for current-text-bound substantive scientific or engineering content. An older writing JSON cannot approve a changed report; complete the whole-text semantic reading as well.

Project图件采用 [信息量与图型规则](project-figure-policy.md)，取消简单柱线和稀疏散点默认输出。曲线和可加色块可以作为真实工程诊断中的信息层，装饰和重复子图不构成信息增量。
