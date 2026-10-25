# Figure Portfolio Blueprint

Use this reference to design a coherent, varied engineering figure family. Build the portfolio from claims and evidence types; do not target a fixed number of attractive plots.

## Portfolio Roles

A technical report may need a justified subset of these roles:

- **Environment or data evidence**: reference bathymetry, topology, image/domain examples, input distribution, sensor geometry.
- **Main performance**: all-method distribution, paired effect, confidence interval, or task-level ranking.
- **Spatial mechanism**: error, uncertainty, residual, coverage, or attention maps with common limits.
- **Conditioned behavior**: terrain-current atlas, stress matrix, scenario ridgeline, conditional response surface.
- **Decision mechanism**: takeover landscape, policy regions, candidate utility field, preference matrix.
- **Safety or feasibility**: phase-space manifold, raw-to-projected displacement, constraint margins, fallback transitions.
- **Ablation and attribution**: full-inclusive raincloud, paired effect forest, component sensitivity, interaction plot.
- **Calibration and reliability**: reliability curve, coverage-width trade-off, rank calibration, residual diagnostics.
- **Generalization and scaling**: unseen-domain transfer, team-size scaling, compute-memory profile, domain embedding.
- **Failure and limitation**: difficult-subset distributions, representative failures, risk envelopes, boundary cases.

Do not create every role when the corresponding claim is absent. Conversely, do not claim calibration, safety, generalization, or scalability without a dedicated proof object.

### Forecasting / prediction portfolio example

Dependency structure → main performance breadth → regression/calibration behavior → robustness or cross-domain transfer → ablation → computational cost.

This is an example, not a mandatory sequence. Each figure needs a distinct evidence function and a real claim; no claim means no compulsory Mantel, regression or cost plot. A compact table may satisfy cost evidence. Retrieve recipes from `figure-pattern-pool.md`, select a backend, fix physical size and review the first draft before targeted revision. Do not count standalone exports as new families.

## Encoding Selection

- Use paired estimation plots for matched experiments.
- Use raincloud/half-violin plots when distributions and raw units matter; place all directly compared methods in one coordinate system.
- Use effect-size forests when many comparators or ablations need intervals.
- Use spatial maps only with preserved geometry, explicit units, shared color limits, and traceable arrays.
- Use heatmaps when both axes encode meaningful conditioning variables; annotate cells with luminance-aware text.
- Use feasibility manifolds only when axes are physical constraints and transitions are real candidate projections.
- Use decision landscapes only when the background field and overlaid events come from the same frozen policy/evaluator.
- Use a 3-D scientific view only when three real independent dimensions are needed to answer the question, with recoverable depth and scale. Never extrude a banned chart into 3-D to pass the rule. Use condition/resource matrices, paired effects or a cost table instead of a two-dimensional Pareto scatter.

If the available evidence is only a list of means, use a table. True temporal, trajectory, calibration and continuous-response curves remain usable inside a composite scientific view with relevant measured residuals, uncertainty, conditions, coverage or constraints. Record each layer's source and purpose; cosmetic overlays and repeated ordinary panels do not add scientific information. A valid additive decomposition may use composition segments after checking component totals.

## Completeness and Diversity Gate

For a manuscript with at least six result figures, aim for:

- at least three distinct scientific purpose classes;
- at least three distinct plot families;
- at least one uncertainty-aware comparison;
- at least one mechanism or diagnostic figure;
- at least one limitation, transfer, robustness, or failure view when such a claim is made.

Do not count six separately exported method panels as six plot families.

## Per-Figure Evidence Contract

Complete `templates/figure_evidence_manifest.json` and run `scripts/validate_figure_manifest.py`. For each figure, record:

- manuscript number and caption;
- the scientific question answered by the figure;
- purpose and claim IDs;
- plot type and why it fits the data;
- raw data source and generator script;
- evaluation unit and sample size;
- strongest comparator and uncertainty representation;
- backend, recipe (or justified CUSTOM), design-reference IDs, per-figure required formats and physical insertion width;
- comparator_set (proposed plus all fair baselines for regression), shared_scale_group, common limits or normalization rules;
- final-width font/annotation readability, clipping, overlap, color accessibility, standalone and manuscript-rendered checks;
- body-text paragraph that interprets the result.

## Visual Hierarchy

- Make the data region dominant; avoid excessive whitespace and oversized legends.
- Keep typography stable across the figure family at final physical width.
- Use consistent colors for the same methods across figures.
- Use different colormap families only when the encoded quantity changes.
- Keep sequential, diverging, cyclic, and categorical color semantics distinct.
- Preserve raw points where sample size permits and disclose aggregation.
- Show confidence intervals or distributional uncertainty rather than only means.
- Place annotations in low-density regions; never cover critical data.
- Separate panels when a combined layout makes labels unreadable.

## Dual QA

Every final figure must pass two different reviews:

1. **Standalone vector review**: open the EMF/PDF/SVG and inspect bounds, fonts, line weights, colorbars, and legend geometry.
2. **Manuscript page review**: insert the final required format, export through Microsoft Word for DOCX or compile the venue LaTeX source, inspect the page at high zoom, and verify no flattening, raster fallback, clipping, compression, or text substitution.

Fix geometry by enlarging the canvas, axes, or safe margins. Do not reduce an already approved font merely to hide layout defects.
