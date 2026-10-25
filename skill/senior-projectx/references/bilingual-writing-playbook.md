# Bilingual scientific and technical writing

Use restrained Chinese engineering language by default. Current instructions, verified facts and the retained customer template govern the work.

## Evidence and scope

Freeze the current task, evidence, and deliverable before rewriting. Do not create a new contribution, experiment, result, limitation, citation, or engineering condition to improve style. Preserve values, signs, units, denominators, comparison scope, uncertainty, negative evidence, and the difference between observation and inference.

Revise point to point. A changed claim may require changes to its abstract, method definition, result interpretation, figure caption, conclusion, and response letter. Check those actual consumers and stop when they are consistent.

## Natural restrained prose

Prefer concrete subjects and verbs. State what object changed, under which condition, by how much or in what direction, and what evidence supports the interpretation. Vary sentence form according to the relation among facts. Use enumeration only when the items are truly parallel.

Read [writing-and-release.md](writing-and-release.md) before drafting or final revision. Its six-class language requirements apply to body, captions, tables and conclusions. Preserve substantive engineering conditions and adverse findings.

Inspect these patterns:

- decorative quotation marks around newly invented concepts;
- repeated long-dash chains used in place of logic;
- stacked synonyms, abstract nouns, and promotional attributes;
- repeated sentence or paragraph skeletons;
- generic transition scaffolding;
- fragments that separate one scientific relation into several short paragraphs;
- defensive claims that praise the work after admitting contrary evidence;
- hollow report phrases without objects, conditions, or evidence;
- prompt, reviewer, generation, audit, and revision-process language in formal prose.

Preserve legitimate terminology quotes, mathematical minus signs, numeric ranges, compound hyphens, concrete risk statements, factual scope conditions, necessary operating instructions and observed unfavorable results. Remove the rhetorical pattern itself, rather than substituting a synonym. Anti-pattern heuristics cannot determine whether text was written by AI.

## English

Use neutral technical English when requested. Keep citations attached to the author, named object, or exact supported claim. Avoid large citation stacks when sources have different responsibilities. Define report-specific acronyms where needed; customer and user style govern voice.

Write Methodology as a continuous mathematical dependency: inputs and assumptions, representations, transformations, objective and constraints, solution, and outputs. Explain each distinct symbol once near its first equation group. Numbered equations remain editable under the declared backend.

Organize Results by scientific questions. Use tables for exact values, figures for structure, and prose for interpretation. A result paragraph normally contains the finding, one or two decisive anchors, the responsible mechanism or constraint when supported, and the consequence for the research question. Do not replay every table cell.

## Chinese

Use complete Chinese sentences with clear engineering subjects. A technical paragraph should develop one relation across conditions, computation, evidence, and implication. Chinese paragraph length is assessed with characters and sentences, not English whitespace word counts.

Replace hollow language such as “取得良好效果” with the actual object and evidence. Replace defensive language such as “虽然存在偏差但仍能证明方法有效” with the observed location, cause supported by data, and the narrower conclusion. Keep genuine constraints and safety risks because they affect decisions.

Avoid packaging ordinary mechanisms in decorative quotation marks. If a new term is necessary, define its observable meaning and use it consistently. Avoid parallel strings such as “稳定性、可靠性、鲁棒性和泛化性” unless each item has a distinct measured quantity or analysis.

## Figures, equations, and conclusions

Captions identify the object, condition, and visual encoding without repeating the full analysis. Distinct panels or figures receive distinct interpretation or an explicit joint synthesis. Equation prose explains variables and semantics after a coherent equation group when that structure improves reading.

Conclusions answer the commissioned question and connect the established technical findings without replaying the full analysis or adding an automatic limitations checklist.

## Automated screen

`check_writing_quality.py` reports paragraph location, original text, reason, and contextual advice. `--language auto` selects Chinese when the body contains substantial Chinese text; use an explicit language for mixed reports. Select `--manuscript-mode project` and use `--require-clean` for final DOCX: unresolved candidates require rewriting and rescanning, or a source-bound scientific-content review with a specific reason. Confirmed rhetorical defects cannot be waived. Explicit placeholders and confirmed source contamination also block delivery. Complete a full manual semantic reading of current body, captions, table text and conclusions; the advisory draft command, a high screen score or zero regex matches cannot substitute for that reading or permit unresolved final prose.
