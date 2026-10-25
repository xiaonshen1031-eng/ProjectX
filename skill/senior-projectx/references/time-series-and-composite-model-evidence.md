# Time-Series and Composite-Model Evidence

Use this playbook for forecasting papers, decomposition-forecasting pipelines, hybrid neural architectures, and reviewer revisions about novelty, generalization, uncertainty, reproducibility, or deployment.

## 1. Separate the Evidence Questions

A strong forecasting paper answers different questions with different evidence:

| Question | Evidence required |
|---|---|
| Does the predictor reduce forecast loss? | held-out chronological evaluation, uncertainty over evaluation units, effect size, paired comparison |
| Is the gain stable? | independent training runs, blocked/rolling windows, sites/seasons/regimes, distribution of errors |
| Does the method generalize? | an explicitly held-out site, region, climate zone, period, or regime matching the claim |
| Does the model quantify predictive uncertainty? | probabilistic outputs, coverage/calibration, interval width or proper scoring rule |
| Is the difference statistically distinguishable? | dependence-aware paired inference, such as DM or block bootstrap, with multiplicity control |
| Is the full system deployable? | end-to-end latency, throughput, memory, hardware/software, tail latency, and operational deadline |

Statistical significance is not predictive uncertainty. Multi-site in-distribution testing is not automatically cross-region transfer, and seasonal testing is not automatically out-of-distribution (OOD) testing.

## 2. Temporal Split Contract

Preserve time order. Random k-fold cross-validation is usually invalid when it lets future observations influence training or model selection for past predictions.

Before training, record:

- training, validation, development-test, and sealed-test time ranges;
- whether preprocessing, feature selection, decomposition, normalization, and imputation were fitted only on the permissible past data;
- forecast origin, horizon, stride, and input-window length;
- rolling-origin, expanding-window, blocked holdout, or other backtest design;
- overlap between forecast windows and how dependence is handled during inference;
- sites, seasons, and regimes assigned to development versus final evaluation.

A fixed chronological split can be valid, but it is weaker than repeated rolling-origin evaluation for claims about stability across time. Explain the trade-off instead of claiming that every form of cross-validation is inherently invalid.

## 3. Generalization Ladder

Label evidence at the level it actually supports:

1. **Within-site temporal holdout:** future periods from sites seen during development.
2. **Multi-site in-distribution evaluation:** several sites are tested, but all site identities or regions were represented during development.
3. **Leave-site-out transfer:** one or more sites are completely excluded from fitting and model selection.
4. **Cross-region or cross-climate transfer:** the held-out region/climate differs materially and was not used during development.
5. **OOD regime evaluation:** a prespecified shift, such as unseen extreme weather or sensor degradation, is quantified and tested.

Do not answer an OOD criticism merely by listing multiple plants or seasons. State the exact held-out factor, shift definition, and whether the test was confirmatory or added post hoc.

## 4. Composite-Model Novelty

An `A + B` architecture is not justified by component descriptions alone. Build a three-layer evidence chain:

1. **Component capability:** what A and B can each represent or optimize.
2. **Coupling mechanism:** where information passes between them and what operation becomes possible only through that coupling.
3. **Counterfactual evidence:** compare A, B, A+B, capacity-matched alternatives, order-swapped or mismatched combinations, and a simple strong baseline under the same tuning budget.

The mechanism claim should predict a measurable signature. Examples include improved performance specifically at abrupt transitions, long-horizon dependencies, high-frequency residuals, rare regimes, or noisy inputs. Test that signature directly. A prose-only statement that a “synergy is unlocked” is not evidence.

When the architecture permits a factorial design, estimate the interaction rather than inferring synergy from two favorable main effects. For a lower-is-better loss, one useful contrast is

`I = [L(A + simple head) - L(A + B)] - [L(simple backbone + simple head) - L(simple backbone + B)]`.

Report a dependence-aware confidence interval for `I`. If the interaction is not distinguishable from zero, describe the components as complementary or additive, not synergistic. Also include a coupling-placebo variant that preserves approximate capacity while removing, relocating, or randomizing the claimed information path. If B is only a terminal head, name it as such rather than implying deeper bidirectional coupling.

For multi-stage decomposition and forecasting pipelines, prevent leakage by fitting decomposition choices and clustering thresholds without access to the sealed future. Report the cost and contribution of each stage, and compare against simpler end-to-end predictors.

## 5. Forecast Statistics

Report raw loss differences and effect sizes before significance labels. Use an inference method compatible with temporal dependence and the evaluation hierarchy:

- Diebold-Mariano (DM) for paired loss sequences when its assumptions and horizon adjustment are appropriate;
- moving-block, stationary, or circular block bootstrap for serially dependent errors;
- site- or regime-level paired aggregation when those are the inferential units;
- multiplicity correction for many models, sites, seasons, metrics, or horizons.

Do not interpret `p < 0.05` as proof of practical superiority. Report the loss differential definition, sign convention, long-run variance or block construction, sample size/effective units, effect size, confidence interval, exact or adjusted p-value, and failure cases. If the study reports only three training repetitions, avoid strong stability claims unless evaluation-unit uncertainty and seed sensitivity are separately justified.

## 6. Uncertainty Is a Separate Output Contract

For deterministic forecasting, define the actual point-prediction output and its loss. Describe DM as paired inference on the mean loss differential with the specified temporal correction. Predictive interval coverage and sharpness belong to a separately defined probabilistic output when that is part of the method. Use those positive scientific definitions in the manuscript; keep unsupported-extension or missing-experiment diagnoses in internal JSON/Markdown.

When uncertainty is claimed, report:

- empirical coverage at nominal levels;
- interval width or sharpness;
- a proper score such as CRPS or NLL;
- calibration by site, season, horizon, and extreme regime;
- the calibration set and whether it was separated from the sealed test.

## 7. Deployment Evidence

Measure the operational path actually required at inference time:

`data ingestion -> preprocessing -> feature computation -> decomposition -> model inference -> post-processing -> output`

Report warm-up policy, batch size, hardware, software, mean, median, P95/P99, throughput, peak memory, and the deadline ratio. Model-only latency cannot establish deployment readiness when signal decomposition or feature generation dominates runtime. A short 100-step trace can illustrate behavior but should not replace the full test-stream distribution or stress test.

## 8. Results Writing

Organize results by scientific question:

`finding -> effect and uncertainty -> strongest comparator -> regime where the effect appears -> mechanism diagnostic -> practical implication or boundary`

Avoid ranking every number. Explain interactions across sites, seasons, horizons, and modules. When one method wins most cells, summarize the distribution and exceptions rather than repeating each table entry. When a simpler method is competitive, discuss cost-accuracy or stability-accuracy trade-offs directly.

## 9. Reviewer-Response Patterns

- **Incremental-combination criticism:** add the coupling mechanism and counterfactual experiment; do not answer only with richer architectural adjectives.
- **OOD criticism:** either run a true held-out shift test or explicitly narrow the claim and record the limitation.
- **Uncertainty criticism:** distinguish deterministic significance testing from predictive uncertainty; add probabilistic evaluation when the claim requires it.
- **Fixed split criticism:** explain temporal leakage risk, then strengthen evidence with rolling-origin or blocked backtesting when feasible.
- **Deployment criticism:** report full-pipeline and tail latency, not only model-forward time.
- **Reproducibility criticism:** provide preprocessing boundaries, seeds, exact splits, configurations, code/data access, and executable provenance. Links to third-party components alone do not reproduce the integrated method.

Every response must preserve the reviewer comment, identify the evidence artifact, calibrate the resulting claim, and quote the exact final manuscript change.
