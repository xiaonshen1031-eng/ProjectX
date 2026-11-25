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

## 中文工程算例

以下为教学数据。某制冷设备可降低用电功率 30 kW，降载期间温度按 0.2 °C/min 上升，运行上限为 30 °C。研究要判断它能否提供 20 min 服务。

**任务和方法。** 用温度上限减去起始温度得到可用热裕度。热裕度除以升温速率得到达限时刻。实际服务时长取达限时间与 20 min 窗口的较小值，按 30 kW 对服务时间积分。

**结果分析。** 起始温度为 24 °C 时，设备在窗口内可连续降载 20 min，减少用电 10 kWh。起始温度为 28 °C 时，第 10 min 即达到温度限值，减少用电 5 kWh。维持 20 min 至少需要 4 °C 热裕度，因此在上述升温率和限值下，可把起始温度不高于 26 °C 的设备计入该项服务。28 °C 工况可按 10 min 能力安排。温度、减载功率按时间对齐绘图，限值和窗口一并标出。

如果数据只给出两组降载时长，而未提供温升观测或模型，正文只比较该条件下的服务时长及电量。热裕度可作为待验证因素，不能直接给出 26 °C 门槛。与设备实测数据的关系取决于可用证据。

## Automated screen

`check_writing_quality.py` reports paragraph location, original text, reason, and contextual advice. Select an explicit language for mixed reports. Use `--manuscript-mode project --require-clean` for final DOCX and follow [the current-text review rules](writing-and-release.md#只读检查与复核). Review the actual report for relations, evidence and textual continuity after resolving the candidates.
