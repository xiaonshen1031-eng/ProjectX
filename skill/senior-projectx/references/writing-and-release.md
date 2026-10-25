# Technical report prose and final delivery

Use this reference for continuous Chinese technical analysis. Current customer structure, language and format remain authoritative.

## Six defects that must be resolved before final delivery

Every final manuscript and client report must contain no confirmed instance of the six defects below: experimental-report language (实验报告式语言), AI formulaic language (AI化语言), stacked language (堆叠式语言), redundancy (冗余语言), defensive prose (防御性表述) and mechanical prose (机械性表述). One occurrence is sufficient to require correction; low density does not excuse it. Apply the requirements to the abstract or executive summary, body, captions, table headings/cells/notes, conclusions, recommendations and scientific or technical appendices. A response letter and an internal research record are distinct artifacts with different purposes.

1. **Defensive prose.** Remove self-denial, apology, reassuring qualifications and sentences that introduce a capability and immediately deny the same capability. Do not append `we do not claim`, `should not be interpreted as`, `this does not undermine`, `although ... cannot ... still`, or their Chinese equivalents to protect an overstated claim. Rewrite the original claim to match the actual formulation and result. State genuine scientific conditions and observed adverse results directly where their interpretation requires them. A mathematical impossibility, feasibility restriction or factual evaluation setting is scientific content.
2. **AI formulaic prose.** Remove stock praise, empty significance claims, invented slogan-like names, decorative quotation marks and sequence words doing the work of an argument. `首先/其次/最后`, `First/Second/Finally`, `证据链`, vague `核心价值`, and `provides valuable insights` must not remain as generic manuscript scaffolding. Use an established technical term or a defined mathematical operation. A term quoted from a cited standard, a defined new operator or actual numbered algorithm steps is different content and may be retained after contextual review.
3. **Redundant prose.** Give each detailed scientific finding one principal analysis location. Do not interpret the same table values or figure pattern repeatedly under new synonyms. Methods specify the protocol; Results interpret the observations; the abstract and conclusion synthesize the supported capability. These distinct roles can refer to the same result without repeating its full analysis. Preserve a later passage when it adds a new condition, inference, discrepancy or consequence.
4. **Stacked/cumulative phrasing.** Rewrite near-synonymous properties, abstract noun strings and chains such as `X and Y and Z`, `X, Y, Z and/or W`. Explain which quantity changes which operation or outcome. Keep scientifically necessary index sets, tensor dimensions, constraints and measured properties; make conjunction and alternatives exact. A short sentence with a concrete input/output relationship is preferable to a larger inventory of capabilities.
5. **Mechanical prose and discontinuity.** Sentences and adjacent paragraphs must carry a scientific or engineering object or relation forward. Use a definition to introduce its derived quantity, an equation to explain its input/output, a discrepancy to motivate the next calculation, or a result to support a bounded inference. A connector such as `Furthermore` or `在此基础上` cannot supply a missing relation. Repeated paragraph skeletons and ordinal openings cannot replace that relation. Read the previous, current and following paragraph together; repair the relationship itself rather than changing transition words.
6. **Experimental/process report language.** Keep run chronology, tuning diaries, desired win thresholds, author confirmations, pending cloud transfers, source-file inventories, checkpoint/checksum receipts, revision comments and audit status in an external JSON or Markdown record. Final prose receives the actual scientific protocol and verified finding. A paragraph explaining why an artifact passes an internal criterion is a research record, not result analysis. Replace empty agenda/report openings such as `This experiment is intended to`, `The purpose of this diagnostic is`, `本次实验`, `为验证有效性` and an unsupported `实验结果表明` with the actual object, observation and interpretation. A substantive experiment-design description belongs in Methods; a commissioned technical report still uses its accepted engineering structure and tone.

No automatic edit may delete unfavorable observations, mathematical constraints, uncertainty, source attribution, required disclosures or reproducibility-critical scientific details. A reviewer may retain a flagged phrase only because its present use is concrete scientific content, not because a rhetorical defect is preferred or convenient. Anti-template screening is not a claim about AI authorship.

## Editing examples

Examples illustrate editing operations; their values are hypothetical and must not become paper results.

| Defect | Before | Scientifically valid revision |
| --- | --- | --- |
| Defensive self-denial | `The method supports reliable operation, but it cannot provide evidence for operational decisions.` | If only forecasts were evaluated: `The method predicts hourly station load under the evaluated demand conditions.` Remove the unsupported operational claim at its source. |
| Reassurance after adverse evidence | `Although the method loses at H24, this does not undermine its usefulness.` | `At H24, the baseline has lower MAE; the additional error is concentrated after the demand transition.` Include the concentration statement only when the residual data support it. |
| Chinese self-defense | `虽然模型不能描述所有波动，但仍具有一定参考价值。` | `模型状态由日尺度负荷构成，状态方程描述日尺度变化。` State actual modeled resolution without a reassuring evaluation. |
| Empty language and invented label | `首先构建“证据驱动核心闭环”，其次全面提升鲁棒性。` | `式（8）的残差统计量用于更新融合权重。更新后的权重用于下一预测时刻。` Use only the actual implemented dependency. |
| Noun accumulation | `The module improves accuracy, robustness, reliability, stability, and generalization.` | Report the measured error change, then explain a distinct perturbation result if one exists. Do not claim unmeasured properties. |
| Table replay | A paragraph reproduces all rows of Table 4, followed by another paragraph explaining the same ranks. | Keep Table 4's exact matrix, use one decisive magnitude or exception, and explain the corresponding mechanism once. |
| Disconnected sentences | `The predictor uses a 24-step input. Communication restoration is important.` | If no scientific dependency exists, move the second statement to its actual context. If predictor output enters a restoration decision, define that input explicitly. Do not invent a connection. |
| Tuning diary | `The configuration was tuned until routing achieved 3/4 wins and passed acceptance.` | Keep the trial history and target in the experiment record. In the paper, state the actual selection objective in Methods and verified paired errors in Results. |
| File/audit receipt | `The figure was regenerated, saved, and hash verified.` | Remove the receipt from the manuscript and keep it in the internal record only when it serves a real consumer. |

These sentences preserve normal science and do not require defensive framing:

- `The input contains batch, horizon, and channel dimensions.`
- `The allocation satisfies energy balance and capacity constraints.`
- `The formulation uses a DC feasibility model.`
- `The horizon is 24 h and the calibration window precedes the test interval.`
- `The paired test uses a heteroskedasticity and autocorrelation consistent variance estimate.`
- `At H24, baseline MAE is lower than the ensemble MAE.`
- `The controller receives matured forecast errors at the next update.`

Keep the condition, direction, units, denominator, uncertainty and citation referent unchanged when revising. When evidence establishes an association, avoid turning the interpretation into a causal proof.

## Single analysis location and paragraph continuity

Before drafting, identify the scientific question answered by a subsection. Choose the full analysis location for each result. A table holds exact numerical comparisons; a figure represents distributions, temporal structure, geometry or mechanisms; prose explains the relation and its consequence. Do not use all three to narrate the same values.

Read each paragraph with both neighbors. Identify the shared quantity and what happens to it: definition, transformation, estimation, comparison or inference. If the next paragraph changes topic, state the actual relationship or place the material in the correct subsection. If the data cannot support a proposed mechanism, retain the observed pattern and the supported interpretation rather than inventing attribution or appending an unsupported-evidence defense.

A short cross-reference can reconnect a previously established relationship. It should add the relationship needed here, not reproduce the earlier analysis. Detailed symbol explanations belong after a coherent equation group; unchanged definitions need not be repeated after every formula.

## Scientific protocol versus experiment sidecar

Keep in the manuscript when needed for interpretation or reproduction: data source and population, temporal partitions, sampling resolution, preprocessing, candidate set, objective, calibration/selection rule, hyperparameters that define the algorithm, seed design, hardware for reported runtime, loss direction, statistical test, dependence correction, sample size, uncertainty and exact measurement scope. Put those details in the appropriate data/setup, Methodology or metrics section once.

Put in an external JSON/MD record: individual job launches, console output, trial-by-trial tuning history, desired win counts, run progress, pending files, author confirmation history, formatting/conversion logs, audit decisions, checksum receipts, prompt instructions and reviewer issue status. A scientific assertion must be justified by actual current evidence; moving its execution history outside the paper does not change that assertion.

Do not move a necessary unfavorable result outside the paper merely because it is inconvenient. Report the observed comparison directly. Do not add a boilerplate limitations or future-work paragraph to every result, and do not require the conclusion to list missing experiments. A required venue disclosure or a material scientific applicability condition remains in its proper location.

Create a sidecar only when real records or review decisions need to be retained; do not generate empty ledgers or merge them into the submission manuscript.

## Read-only screen and final gate

Use the Project screen on the current report:

```powershell
python scripts/check_writing_quality.py report.docx --manuscript-mode project --language chinese --require-clean --json-out review/writing.json
```

The first call locates candidates, including single-sentence defects and neighboring paragraphs. Read their text and context. Rewrite confirmed defects in the source and rerun the screen. Do not waive a defect by marking it `rewritten` while it is still detected. A genuine scientific use can be retained with a source-bound decision:

```json
{
  "reviews": [
    {
      "candidate_id": "copy the current candidate_id from writing.json",
      "decision": "scientific_content",
      "reason": "The conjunction lists three independently enforced capacity constraints; removing it would change the feasible set."
    }
  ]
}
```

Candidate identifiers bind the exact current text, location and neighboring context. Changed text or context requires fresh review. Old decisions cannot approve a new candidate. The final gate returns nonzero for unresolved candidates, malformed decisions, definite contamination or source-read failures in technical reports. Calls without `--require-clean` remain advisory draft screens for CLI compatibility; that behavior is not permission to deliver unresolved prose.

The DOCX reader excludes bibliography entries and resumes language screening in an English or Chinese technical appendix. An inline `Abstract:` or `摘要：` label remains summary prose, even when a heading style was applied to the whole paragraph. Numeric table replay is a context-review candidate when at least six distinct literal values match one actual table and cover at least 75% of the paragraph's distinct numeric values. A few decisive quantitative anchors, new derived quantities and ordinary numerical protocol details are not automatically table replay. The candidate binds the actual table text; a changed table requires a fresh decision. Ordinary literal TeX tables are screened from their actual cells, separately from captions and code. Read rendered macro-generated tables and nonliteral equivalences manually.

Complete allocation-example delivery additionally screens its current DOCX through `audit_project_delivery.py`; a past clean writing report cannot approve a changed document. Use the current customer structure throughout.

The screen cannot prove semantic continuity or find every paraphrased repetition. Final delivery also requires a full manual semantic reading of the current text, covering all six defects, all distinct figure panels and the actual scientific or engineering dependencies. Read captions and table text as well as body paragraphs, and compare abstract/summary, Results and conclusion for repeated analysis. A high legacy screen score or zero regex matches cannot replace that pass or override unresolved candidates.
