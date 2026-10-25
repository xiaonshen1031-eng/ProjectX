# Experimental Playbook

## Benchmark Design

Start from a citable benchmark or open dataset.

For electrical papers, lock down:

- system topology or dataset version
- operating horizon and resolution
- device placement and ratings
- uncertainty source
- solver stack

For robotic, remote-sensing, or coverage-planning papers, lock down:

- coverable region definition and excluded obstacles/shadow cells
- sensor footprint and quality model
- mission time, energy budget, communication radius, and collision margin
- dynamic command constraints and replay model
- training/evaluation map split and seed protocol

## Baseline Policy

Compare against relevant, competent baselines.

Do not compare a modern proposed method only against obviously weak or outdated methods unless the paper is historical or diagnostic.

Use at least one of these baseline roles when applicable:

- strong classical optimization baseline
- direct deep-learning or DRL baseline
- structurally related ablation baseline
- oracle or upper-bound reference when meaningful

For coverage-planning papers, A* or RRT* baselines should be embedded in a decomposition or coverage framework when the proposed method solves a full coverage task. Do not compare a cooperative coverage planner against a point-to-point local navigator and call the comparison fair.

## Result Sanity

For most proposed-method papers, the proposed method is expected to outperform baselines on the primary target metric. Treat this as a hypothesis to verify, not a license to fabricate.

Before accepting a result:

- confirm the metric direction is correct
- confirm the gain is visible in the raw exported data
- confirm the table, figure, and discussion tell the same story
- inspect whether any claimed superiority creates a contradiction elsewhere
- check whether nominal planned metrics still hold after smoothing, projection, or dynamic replay
- check whether a success threshold was chosen post hoc by adding sensitivity results
- check whether the strongest classical baseline is close enough that the correct conclusion is `competitive` rather than `superior`

Typical contradictions to catch:

- lower loss but worse target metric with no explanation
- figure trace inconsistent with table summary
- nominal result excellent but robustness catastrophic with no discussion
- an ablation result better than Full contradicting an unconditional superiority claim; retain the result and qualify the claim
- dynamic replay coverage far lower than nominal planning coverage with no explanation
- all stochastic standard deviations equal to zero despite claimed independent seeds

## Case Study Checklist

Select applicable evidence from the following according to the claim; this is not an experiment quota:

- benchmark description
- hardware and software environment
- training settings or solver settings
- hyperparameter table
- evaluation metrics
- overall comparison
- multi-scenario analysis
- seasonal or temporal analysis when time series are involved
- penetration or stress sweep when network loading or renewable ratio matters
- ablation study
- robustness or generalization test
- significance test when seed-based stochastic variation exists
- independent training runs for learning methods when stability is claimed
- unseen test cases for generalization claims
- closed-loop recomputation after dynamic-feasibility correction when feasibility is a contribution

## Figure Expectations

Use the figure family that best matches the claim:

- convergence curves for learning behavior
- box or violin plots for seed stability
- line plots for penetration or seasonal sweeps
- node-profile curves for feeder snapshots
- time-series traces for critical buses or outputs
- heatmaps for bus-time fields
- grouped bars or panel plots for ablation and robustness

When a figure is revised:

- update the underlying table and prose only if evidence, numerical content or interpretation changed; a typography-only repair does not require rewriting them
- keep a record of whether the final figure came from original output or a controlled redraw based on validated final values
- never change plotted values without updating the source table, provenance note, and manuscript interpretation
- if a visual offset is used to reveal overlapping zero-valued curves, annotate the offset and keep the data value unchanged

## Interpretation Standard

Explain results in terms of mechanism:

- topology awareness
- safety enforcement
- risk regularization
- device coordination
- decomposition benefit
- feature-engineering benefit

Do not stop at `Method A is higher/lower than Method B`.

If the proposed method is not best on a secondary metric, explain the trade-off instead of hiding it. Strong papers often show that the proposed method is best on the primary metric while spending more energy, time, or computation.

## Task universe, eligibility and frozen-state reporting

The formal experimental universe and a mechanism's eligible ablation subset are different. Execute a removal only where that mechanism is actually enabled in the frozen implementation. Mark other formal tasks `not applicable by design`, not zero effect or a tie. Derive win/tie/loss denominators from the applicable tasks, keep direction and tie tolerance explicit, and reconcile plot counts with the underlying results. Neither a particular task count nor a requested target win rate is a reusable rule.

Tune on the authorized training/calibration partition with a stated search and stopping criterion. Do not rerun/select evaluation seeds or TEST configurations until a desired ranking appears. A remembered cloud win rate without configurations, predictions or logs is an unverified historical report, not a reproduced numerical result. Reproduction requires actual runs and measured evidence; preserve contrary observations and distinguish old claims from new measurements. A parameter table must match the configuration that produced the reported predictions, even when an earlier prose prompt specified different settings.

Generalization after task-specific refitting establishes portability of the framework across tasks. Zero-shot transfer requires no target-task refit; domain adaptation and robustness are separate protocols. Do not relabel one as another. Preserve independence, time order, forecast availability and leakage controls in forecasting studies.

## Complete significance evidence, selective interpretation

Maintain the planned task-by-baseline comparison matrix, not only the strongest comparator. Where one table is requested, group rows with dataset/system and horizon/scenario columns under a common Task header; merge repeated group names when it improves scanning. Use all scientifically planned baselines, not a global fixed count inherited from a previous paper. Keep the complete matrix in the main table or a venue-permitted appendix, then interpret the overall pattern, nearest competitor, meaningful regime differences and mixed evidence selectively.

For Diebold–Mariano analysis, document the paired loss definition and sign, forecast origin and lead indices, evaluation sample size, mean loss differential, autocovariance estimate, bandwidth/lag rule, long-run variance estimator, test statistic and tail convention. Define finite-sample/horizon corrections if used and the multiple-comparison family/correction if applied. Dependence from overlapping forecast horizons or serial loss observations requires an appropriate estimator; sample count is not the count of plotted/subsampled points. Explain every newly introduced variable, but group the related formulas first and follow with a connected notation/method paragraph when appropriate. Statistical significance is evidence about predictive loss, not calibrated predictive uncertainty or proof of mechanism causation.

Interpret offline-heavy/online-light computation using measured full-path latency, tail cost and sampling/decision intervals for learning systems; use runtime, processed states, search-space size, bound gap, exact/bounded/truncated status and scale for solvers. Include only relevant measures and avoid repeating identical cost values in tables, figures and prose.

Project图件采用 [信息量与图型规则](project-figure-policy.md)，取消简单柱线和稀疏散点默认输出。曲线和可加色块可以作为真实工程诊断中的信息层，装饰和重复子图不构成信息增量。
