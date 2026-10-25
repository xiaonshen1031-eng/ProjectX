# Advanced Scientific Figure Workflow

Use this reference for result figures intended for engineering reports. The goal is evidence density and legibility, not visual complexity for its own sake.

## Start From the Scientific Question

Retrieve the closest entry in `figure-pattern-pool.md` before choosing an API. Use the ordered process: scientific question → evidence schema → accepted recipe → backend → layout draft → standalone visual QA → targeted revision → manuscript-rendered QA. For accepted examples, inspect layout and source scripts when available; transfer semantic encodings without old data, fixed counts, palettes or project dependencies. Follow the pool's scientific-correctness-first quality hierarchy.

Before plotting, write one sentence each for:

- the conclusion the figure should support;
- the data and evaluation units behind it;
- the comparator or reference required for interpretation;
- the uncertainty or failure information that must remain visible;
- the final physical insertion width and export formats.

Remove a figure if a compact table communicates the result more faithfully.

## Panel contribution and mechanism evidence

For a composite figure, assign each panel one distinct evidence role in the existing figure note: what additional comparison, condition or relation becomes visible, and which saved objects support it. Merge or remove a panel that only repeats a table, outcome count or neighboring panel without advancing the parent question. Panel count follows that reasoning; a request for three horizontal panels is a local layout constraint, not a reusable quota. Increase useful evidence density before adding panels or shrinking fonts.

An operational mechanism illustration motivates a method. A matched component/risk-term result can support its scoped marginal effect and explain how its output changes under those controls. Claims of scientific novelty require the paper's methodological and prior-work comparison; a more elaborate figure does not strengthen novelty by itself. Preserve neutral, adverse and unchanged outcomes alongside improvements.

For curve coordination, adaptive control or related trajectory mechanisms, retrieve `COORDINATED_CURVE_DIAGNOSTIC` in `figure-pattern-pool.md`. It combines a matched effect summary with one or more aligned case views when actual prediction/state arrays are available. Keep fold-wise percentages, pooled effects and task-mean effects separate; they can use different denominators. Representative cases illustrate the mechanism and do not replace population evidence.

Enrich an existing trajectory only with relevant saved layers: observations/reference/output, actual expert or scenario dispersion, per-lead changes, constraint margins, or state/weight changes. Align issue origin, horizon, timestamps, units and member identity across tracks. Distinguish predictive coverage, confidence intervals and finite-expert ranges/IQRs. A within-window maximum is not automatically a threshold event. Keep case selection fixed during a visual revision; do not choose a more favorable case or invent larger deviations to make curves look more informative.

## Preferred Evidence-Rich Forms

- paired estimation or Gardner-Altman plots for matched comparisons;
- raincloud/half-violin plus raw points and interval summaries for distributions;
- ridgeline or conditional distributions for many ordered scenarios;
- spatial error, uncertainty, coverage, or residual maps for geospatial claims;
- terrain-current or condition-performance atlases for two conditioning variables;
- takeover/decision landscapes with observed events over a learned or analytic field;
- feasibility manifolds with raw-to-projected displacement vectors;
- calibration curves, coverage-width plots, and rank-reliability diagrams;
- effect-size forest plots for many comparators or ablations;
- trajectory envelopes or phase-space plots for dynamic feasibility;
- bubble heatmaps only when size, color, and text encode distinct, interpretable quantities.

When evidence contains only a short one-dimensional list of means, use a table. A true continuous/time/trajectory relationship may retain curves in a composite view with measured residuals, relevant uncertainty, condition/event structure, calibration or constraint diagnostics. These layers must answer the same scientific question; cite their actual arrays or analytic definition. Identity lines and interval segments are primitives, not simple-line result charts. Additive compositions require a genuine decomposition and checked totals. Do not invent extra dimensions or bands to produce a more elaborate figure.

## Decision-validation results

Use this form when the scientific question connects a preparation or condition to a verified boundary and then to an admissible action. It is a result figure, not an algorithm flowchart or another overall performance comparison. Extract the actual plan/settings, scanned domain, boundary definition, reachable state, candidate actions and successor outcomes from the current paper and saved result objects before drawing.

Choose a compact encoding that makes the decision test visible:

- A preparation-by-budget or condition-by-threshold matrix can show winning/safe, losing/failure-reachable or other study-defined statuses. Keep the distinction between guaranteed survival and one successful realization. Show costs and selected plans beside the relevant rows without a long side table.
- An action-by-outcome grid, aligned successor supports or local boundary/feasibility view can show why commands are retained or excluded. Encode the actual failures and legal continuations, rather than placing a sentence in each command card.
- When timing or physical availability matters, align the measured or enumerated states with the decision outcomes. Keep true state, public observation, branch count and grouped support count distinct when the study distinguishes them.
- Compose a single horizontal result when that makes a short coupled mechanism easier to read. Use subfigures only when evidence roles or conditions justify them; do not force empty a/b panels or a chain of arrow-linked text boxes.

Keep operating regimes explicit. If default costs select one preparation but a local witness is drawn from a different cost-sensitive setting, identify both settings and connect them naturally in the adjacent prose. Do not let a default-selection label imply that a node belongs to that default plan. Preserve the actual attack/resource budget, time/stage, tolerance, state and legality definitions used for the displayed result.

Show scanned thresholds faithfully. A result censored above the tested maximum is `> maximum`, not the next exact value. Keep missing, infeasible, untested and losing states distinct; they are not interchangeable zeros. Counts of physical branches and public/aggregated supports must retain their separate meanings. A statement that all legal successors are safe requires the corresponding universal test, not an average outcome.

Visual redesign alone does not authorize new experiments, shifted thresholds, changed commands, rescaled timing claims or new numerical conclusions. If source text and saved results disagree, record the discrepancy and resolve the scientific source within the authorized scope; do not silently choose whichever makes a cleaner picture. Deterministic exhaustive checks do not need invented error bars, significance or a sample population of independent repeated trials.

Use short status labels and a compact meaningful key. Add visual redundancy to color where needed. Keep the data/state/action marks dominant; long explanatory boxes, repeated headings, empty arrows and decorative mini-plots weaken the result. Check that this figure contributes a distinct decision finding rather than repeating a benchmark figure or table.

Write a short caption stating the scientific relation, actual setting and panel roles. Put necessary state conditions and the explanation of the selected action in connected nearby prose. Avoid run-log narration or captioning every internal construction step. If a native editor is requested, use `editable-diagram-playbook.md` for the graphical objects and `word-figure-integration.md` for editable equations and Office insertion; preserve the result evidence contract.

## Anti-Patterns

- one violin per file when the scientific comparison requires all methods together;
- 3-D plots used only to appear advanced;
- two-dimensional Pareto scatter/frontier plots, including accuracy-cost diagrams repackaged as CUSTOM or multi-panel figures;
- a plain bar or line figure made to look advanced by decorative layers, cosmetic whiskers or unrelated insets;
- heatmaps with unreadable annotations or arbitrary rainbow colors;
- panels so compressed that the source font appears oversized after insertion;
- outside legends that are clipped by EMF export;
- large in-axis titles duplicating the caption;
- jitter or decorative offsets that can be mistaken for changed data;
- a result map generated from synthetic values when real saved arrays exist.
- a decision-validation result replaced by a generic workflow or prose cards;
- a caption or selected-plan label that combines different operating regimes as if they were one case;
- additional panels or curves that create apparent complexity without additional verified information.

## MATLAB Layout Contract

1. Set the physical canvas before drawing.
2. Set `PaperSize` and `PaperPosition` to the same physical canvas; do not rely on tight cropping.
3. Place axes, colorbars, and legends with explicit normalized positions.
4. Reserve safe margins for long y labels, rotated ticks, colorbar labels, and bottom legends.
5. Select an export route supported by the installed MATLAB release; `Painters` is a legacy rendering choice, not proof of vector output (R2025a ignores `Renderer` for print/saveas).
6. Preserve aspect ratio for spatial maps and image evidence.
7. Use rendered-cell luminance to choose black or white heatmap annotations.
8. Keep fonts unchanged when fixing clipping; enlarge canvas or move the plot region first.
9. Export editable source and final vectors (`.fig`, `.emf`, `.pdf` or `.svg` as required); use PNG only for QA unless requested.
10. For Word EMF delivery, insert the final EMF, export through Microsoft Word and inspect the actual page; for LaTeX, inspect the compiled venue PDF.

For independent Word panels, export each panel separately with identical physical dimensions and common limits. Do not rasterize or manually crop panels to make them appear aligned.

## Python Layout Contract

Use `python-figure-playbook.md` and the Python publication template. Set physical size, GridSpec/axes and margins explicitly; verify fonts, preserve vector text, share method style, and request only PDF/SVG/PNG unless an existing verified conversion chain is needed. Python does not require FIG. In mixed projects, both backends follow one physical/style contract.

## Visual Review Gate

The first draft receives recipe-specific QA: plot fitness and information density, complete comparator roster, shared scales where needed, prominent readable statistics, no clipped or overlapping labels/keys, accurate caption and body interpretation. For all-baseline regression, compare the declared roster against the benchmark; a boolean or file-existence pass cannot inspect the image. Fix only diagnosed issues. Once accepted, avoid redundant redesign/export/verification without changed inputs or feedback.

Reject the figure if any of these fail:

- no text, tick, colorbar, marker, or legend is clipped;
- labels remain readable at final inserted width;
- data are not hidden by annotations or legend;
- color remains interpretable in grayscale or with marker redundancy;
- uncertainty and sample size are visible when relevant;
- axes and units are scientifically correct;
- post-crop aspect ratio and comparative panel scales are preserved; source and inserted width/height imply one uniform scale factor;
- all values trace to saved result files;
- the caption and body interpretation agree with the visual;
- the figure does not overstate causal or statistical evidence.

Review the standalone vector and the actual manuscript-rendered page separately. Passing one does not imply the other passes.
