# Figure Design Rubric

Use this reference before generating or revising manuscript figures. It converts "make the figure better" into a decision process.

## Figure Purpose Classes

Assign each figure one primary purpose:

- **Mechanism overview**: connects a concrete scenario to system propagation, operating difficulty and research motivation.
- **Framework/workflow**: explains actual scientific objects, transformations, decisions and method logic.
- **Decision validation**: shows a verified condition or preparation, its boundary/domain and the resulting admissible or excluded actions.
- **Data appearance**: shows input data, labels, or domain-specific visual texture.
- **Representation**: explains transformed inputs, priors, features, or channels.
- **Diagnostic**: tests a bottleneck or upper bound.
- **Main comparison**: supports the central performance claim.
- **Ablation**: isolates the contribution of components.
- **Stability**: shows variation over folds, seeds, scenarios, or thresholds.
- **Failure/limitation**: used only when the paper explicitly discusses failure modes.
- **Auxiliary transfer**: supports supplementary generalization or objectness evidence.

Resolve the figure's scientific purpose before drawing. For an existing accepted-source export, preserve its purpose and content; conversion does not require a new performance claim or table. Use `editable-diagram-playbook.md` for native mechanisms/workflows and the decision-validation section of `advanced-figure-workflow.md` for result-driven action/boundary figures.

## Plot-Type Selection

First retrieve `figure-pattern-pool.md`: scientific question → evidence schema → nearest recipe → backend → layout draft → standalone QA → targeted revision → manuscript QA. Correct structure before colors. Use these selection guards:

- Pearson plus nonlinear dependence: shared-order dual triangles and meaningful clustering, rather than two duplicate square heatmaps.
- Sparse variable groups: avoid forced Mantel; use a compact dependency summary or table.
- Main benchmark with exact table values: show breadth, distributions, consistency or interaction across relevant tasks/horizons.
- Prediction-fidelity claims: retain all fair baselines with common sampling, identity lines and scales.
- Ablation after matrix-heavy figures: prefer Full-inclusive forest/paired effects or conditional sensitivity diagnostics with honest uncertainty.
- Computational cost: independent evidence or a compact table, not an ambiguous ablation panel.
- Preparation-to-action coupling: a real condition/status matrix, boundary and outcome/support view; no invented measurements or generic workflow substitute.

Choose the plot type from the evidence structure:

- few methods and few metrics: a table, or paired effect/range estimates when actual units or uncertainty add scientific information
- many methods and many metrics: table first; metric matrix only if visual pattern matters
- stochastic runs: dot plot with mean and uncertainty; avoid boxplots with too few points
- threshold sweep: calibrated response with actual conditional/error/coverage structure and a justified decision reference; otherwise a table
- spatial or image evidence: image panels with equal display boxes and preserved aspect ratio
- signed change: paired effect forest, distribution or signed task-condition matrix with a meaningful zero pivot
- class confusion: confusion matrix with normalized values, readable labels, and explicit denominator
- ablation with module removal: Full-inclusive paired effects with valid uncertainty and matched unit identity
- computational cost: repeat-timing distributions, condition-resource atlas, paired resource effects or a table; select trade-off views only when the underlying conditions and resource measurements answer the engineering question
- true temporal or trajectory relation: combine observations with relevant residual/uncertainty/condition/constraint information, all from real arrays
- coordinated trajectory mechanism: matched control effects plus aligned observed/reference/output and state/weight changes when available; use `COORDINATED_CURVE_DIAGNOSTIC` and preserve case selection and band semantics

Avoid using heatmaps for every result section. A heatmap is appropriate only when the two-dimensional structure helps interpretation.

## Layout Rules

- Use fewer, larger panels rather than many unreadable subfigures.
- Keep each panel's visual role clear.
- Give each panel an additional comparison or relation; merge low-information repeats rather than filling a fixed panel quota.
- Use white background unless the journal or data type requires otherwise.
- Use compact panel labels only when caption/body references require them; do not add letters automatically.
- Remove in-axis titles when captions already describe panels.
- Use padding, not cropping, for image panels with different aspect ratios.
- Keep legends inside only when they do not cover data.
- Place colorbars close to the relevant panel and verify tick-label clipping.
- Make axis labels and tick labels readable at the final inserted width.

## Typography Targets

For Word figures inserted around 8.5-16.5 cm wide:

- axis labels: typically 9-11 pt after insertion
- tick labels: typically 8-10 pt after insertion
- legends: typically 8-10 pt after insertion
- panel labels: visible but not dominant

If the user explicitly requests larger labels, honor that request and verify the final Word/PDF page for overlap.

## Color Rules

- Use perceptually ordered colormaps for scalar metrics.
- Use diverging colormaps only for signed or relative-difference data.
- Use categorical palettes only for discrete methods/classes.
- Avoid rainbow colormaps unless the field specifically expects them.
- Avoid a manuscript figure family dominated by one hue.
- Use direct labels or distinct markers when color alone cannot distinguish methods.
- Check grayscale distinguishability when figures may be printed.

## Backend-Aware Implementation Pattern

For native diagrams, plan system geometry and connector lanes with `editable-diagram-playbook.md`. The axes-oriented pattern below applies to publication plots; do not force it onto a requested Visio source. For accepted-source conversion and Word insertion use `word-figure-integration.md`.

Use this pattern for publication plots:

1. define figure size and final target width
2. create axes with explicit normalized positions
3. set global font and renderer defaults
4. plot data with stable line widths and marker sizes
5. apply scientific colormap or palette
6. add essential labels, keys and annotations; panel tags only when used in the narrative
7. choose MATLAB or Python from project/user/editing requirements and export only per-figure required formats
8. inspect the actual manuscript-rendered page (DOCX or compiled LaTeX) after insertion

## Review Questions

Before accepting a figure, answer:

- What claim does this figure support?
- Is the same information already clearer in a table?
- Is the strongest fair comparator visible?
- Are uncertainty and sample size visible when relevant?
- Does the figure avoid visual overclaiming?
- Are all labels readable in the final manuscript?
- Are any targets, masks, axes, colorbars, or legends clipped?
- Do legend entries and numbered callouts identify actual encodings and unambiguous targets?
- Do repeated native modules align in visible centers/baselines, and do complete arrowheads and joins survive the final scale?
- Is the figure analyzed in the body text?

If any answer is unclear, revise the figure or remove it.
