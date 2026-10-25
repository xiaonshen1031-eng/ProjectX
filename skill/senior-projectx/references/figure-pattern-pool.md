# Scientific Figure Pattern Pool

First retrieval layer for result figures. Choose by scientific question and evidence schema, then backend and physical size. A recipe is an encoding contract, not a gallery, mandatory figure, dataset source, or license to invent evidence. Prefer a simpler justified CUSTOM design or table when it answers the question better.

## Retrieval and visual profile

Scientific question → evidence schema → nearest accepted recipe → backend selection → layout draft → standalone visual QA → targeted revision → manuscript-rendered QA. Separate conceptual figures. Retrieve only the nearest recipe and the selected backend playbook.

Quality priority: scientific correctness → evidence completeness → plot-type fitness → information density → comparator visibility → statistical readability → layout balance → typography → color/aesthetics → decorative polish.

- Fix physical dimensions before polishing. English/numeral font follows user/venue (Times New Roman when required); report unavailable fonts. Judge every label at insertion width. Statistical annotations should outrank ticks, not data. Panel letters only when caption/body references require them; no decorative axes titles.
- Within a paper, reuse method colors, markers, line weights and ordering conventions across MATLAB/Python. Colors here are not prescribed. Use redundant marks for critical categories; a proposed method must not make fair baselines invisible.
- Visual hierarchy: data/statistical structure, comparator relationship, essential annotation, axes/units, legend, decoration. Reserve a real legend/header band. Avoid both crowding and dead zones; sparse evidence is a reason to change encoding, not fabricate groups.
- Composite panels must answer one parent question. Match standalone limits, typography and evidence without recomputing results; export standalone panels only for requested editing/supplement/presentation. Panel exports are not new figure families.
- Show stochastic uncertainty, paired units and strongest fair comparators. Exact values belong in tables when the figure conveys patterns. Missing/NaN values remain missing, never zero. No synthetic replacement, manual numeric entry, regression-point movement, undeclared smoothing, attractive manual cluster order, favorable seed selection, concealed failed baselines, or OCR reconstruction when saved results exist.
- Declare metric direction, normalization, sample regime and statistical estimator. Do not silently substitute MIC implementations or call another dependence metric MIC. Preserve provenance; design references in `reference_pool_ids` do not replace `data_source` or `generator_script`.
- The manifest validates declarations, paths and contracts; it cannot see a missing baseline in an image or certify visual quality. Inspect vectors and final manuscript pages. Stop after accepted QA unless changed evidence/layout or user feedback requires targeted revision.

## CORR_DUAL_TRI_STREE

### Scientific question
Which variables share linear and nonlinear dependence, and does clustering expose interpretable structure?
### Best used when
Pearson and a declared nonlinear metric cover the same variables and sample regime; paired comparison benefits from common ordering.
### Avoid when
Only one metric is needed, clustering has no interpretable role, or too few variables justify a matrix. Never choose two plain square heatmaps merely because the API is convenient.
### Evidence schema
Variable names, aligned observations or saved metric matrices, missing-value policy, exact nonlinear estimator/settings, distance definition, linkage and leaf order. Preserve source experiment IDs.
### Core encoding
Use upper/lower triangles for complementary metrics with one data-derived variable order; attach a dendrogram or clearly explained cluster rails in the same coordinate system. Pearson uses a signed scale; MIC uses a nonnegative scale. Label both meanings and keys separately.
### Accepted visual structure
Observed final D1 uses paired rotated triangular SMatrix views, strong aligned variable-label baselines, cluster outlines/rails and separate horizontal metric keys. **It is not a shared-order upper/lower matrix**: the inspected helper computes linkage separately for each metric. Transfer its legibility and cluster organization; for the requested direct cross-metric recipe compute one justified ordering and apply it to both matrices. Do not claim the source already satisfies that rule or copy its fixed cluster count.
### MATLAB route
Use project-approved SHeatmap/SMatrix and STree when present, or explicit patches/axes with native linkage output. Obtain the order once, apply it to both row/column indices and align the tree. Do not use built-in heatmap as a substitute for the required structure.
### Python route
Use Matplotlib masks/vector cells and the project's scipy.cluster.hierarchy implementation. Compute a declared distance/linkage, derive leaves once and index both matrices consistently; preserve metric-specific color semantics.
### Required comparators
The same variable/sample set for both metrics, with explicit metric labels. A model comparator is unnecessary for descriptive dependence.
### Annotation rules
Use limited numeric precision only where readable; choose text contrast from rendered cells. Statistics need not fill every cell. No invented significance or cluster labels.
### Layout rules
Reserve label and colorbar margins; align tree leaves and matrix centers; use one variable order across triangles. Metric headings have a scientific function, unlike repeated dataset captions.
### Failure modes
Independent plain heatmaps, inconsistent ordering in direct comparison, decorative trees, manual reordering, duplicate variable text, annotation overload.
### QA questions
Are metric meanings distinguishable? Is ordering shared and reproducible? Does the tree come from data? Are labels and keys readable? Does clustering help interpretation? Do annotations obscure cells?
## DEPENDENCY_MANTEL_DENSE

### Scientific question
How do meaningful multivariate feature blocks relate to response-distance structure?
### Best used when
Enough scientifically real groups and heterogeneous relations justify a link-based view. There is no universal minimum group count.
### Avoid when
Sparse variables produce a largely empty canvas. Use a compact dependency summary, correlation profile, distance-correlation view, small network or table. Do not choose Mantel solely because the library supports it.
### Evidence schema
Named feature/response blocks, aligned sampling units, full multivariate distance matrices, distance definitions, Mantel effect estimates and permutation p-values with count/seed and exchangeability restrictions.
### Core encoding
Matrix structure plus selected links; width encodes effect magnitude and a separate documented style encodes significance. De-emphasize secondary links without hiding contrary findings.
### Accepted visual structure
Prompt-confirmed historical lesson: enough genuine relational structure, restrained link density and readable groups. No Mantel figure is present in the inspected current final set; do not describe this as an observed final layout.
### MATLAB route
If approved locally, use SMantelLink with precomputed effect/p-value matrices. The project's dependency notes document why collapsing a multivariate block to a scalar proxy changes the test. Native patches/lines are an acceptable alternative; preserve the full-block statistic.
### Python route
Use existing distance/permutation routines with explicit Matplotlib cells and links. Respect the study's dependence/exchangeability design; do not add a library or substitute a correlation coefficient silently.
### Required comparators
All declared scientifically relevant block relationships, including weak or neutral results; label excluded/unavailable tests distinctly.
### Annotation rules
Explain effect, significance and permutation semantics. Link visibility is not a claim of causality.
### Layout rules
Separate node labels and matrix labels; use hierarchical link weights and a compact key. Switch encoding when density is intrinsically insufficient.
### Failure modes
Fake groups to fill space, splitting one variable into pseudo-groups, all links equally heavy, unexplained p-value colors, scalar proxies for multivariate tests.
### QA questions
Are groups real? Is the view sparse or overloaded? Are weak links subordinate but recoverable? Are permutation counts/design and effect meanings explicit?
## PAIRPLOT_PROMINENT_R

### Scientific question
What marginal distributions and pairwise relationships explain the input structure?
### Best used when
A manageable set of meaningful variables needs marginal, scatter/regression and statistical views together.
### Avoid when
Too many cells force illegible typography, temporal dependence makes reported inference invalid, or the result repeats the dependence figure without a new question.
### Evidence schema
Aligned named variables, units, sample/subsample IDs, missingness policy and saved correlation/statistical results. Compute statistics on the declared population; disclose any display-only sampling.
### Core encoding
Diagonal distributions; lower-triangle scatter/regression; upper-triangle statistics. The correlation label is a main information layer.
### Accepted visual structure
Prompt-confirmed prominent, bold, horizontally centered `r` in a stable low-conflict position. Inspected D3 generator uses explicit cell controls and outer-only numeric ticks; the status record says pairplots were removed from the active package. No final preview was available to verify the requested centered-r appearance.
### MATLAB route
Use explicit cell axes or the approved SPairplot object; set each axis/label deliberately. Place `r` at normalized horizontal center with stable vertical alignment. Avoid default plotmatrix.
### Python route
Use Matplotlib GridSpec and the existing statistics stack. An existing PairGrid may initialize cells, but inspect and control axes, annotations and fonts individually; seaborn is optional.
### Required comparators
Same sample definition and missing-value treatment across variable pairs where comparison requires it. No arbitrary model baseline.
### Annotation rules
Bold `r` larger than ticks, centered, precision controlled; define significance only if valid. No automatic panel letters or redundant dataset titles.
### Layout rules
Reserve outer-label margins, suppress redundant interior ticks, maintain one font and balance diagonal/scatter/statistic prominence. Split variable groups scientifically when cells become too small.
### Failure modes
Small/default fonts, off-center statistics, automatic `(a)-(d)`, clipped outer labels, every cell repeating all ticks.
### QA questions
Is `r` centered and easier to find than ticks? Is the diagonal meaningful? Are outer labels visible? Are panel letters necessary? Is the sampling/statistic definition consistent?
## MAIN_PERFORMANCE_BREADTH

### Scientific question
Is the advantage broad across tasks, horizons and metrics, or concentrated in a few cases?
### Best used when
Exact benchmark values already have a table and there are multiple scientifically comparable tasks.
### Avoid when
A single task or incompatible metric definitions make breadth meaningless. Use a paired estimate or table when more faithful.
### Evidence schema
Task/dataset/horizon, metric and direction, all fair method values, strongest-comparator identity/rule per cell, paired evaluation units, tie rule and valid task denominators.
### Core encoding
Complementary metric-reduction matrices in a shared task space plus optional win/tie/loss breadth. Define relative-change denominator and zero-baseline handling. Missing cells are unavailable, not zero; use signed formatting so losses stay visible.
### Accepted visual structure
Observed M3 combines two metric matrices with a separate pairwise breadth panel, horizon labels within cells, one common reduction key and a dedicated metric-legend header band.
### MATLAB route
Explicit matrix patches/text and an aligned task-outcome or paired-effect strip; an existing SHeatmap may assist cell layout. Select comparators from saved benchmark data, not hardcoded labels. Do not replace the matrix with method-ranking bars or add a simple bar panel as decoration.
### Python route
Matplotlib GridSpec, shared normalization and explicit masks; pandas/NumPy only if already used. Reserve the breadth key band before plotting; avoid a hardcoded positive sign or fixed task count from the source example.
### Required comparators
Strongest fair comparator per task under a declared rule, plus the full relevant baseline roster in pairwise breadth. Reveal variable denominators and ties.
### Annotation rules
Prioritize patterns, metric direction, horizon and denominator. Keep full precision in tables; contrast text with actual cells. A win count alone is not a significance test.
### Layout rules
Shared dataset/task ordering, comparable reduction scales where scientifically valid, compact separate keys, no legend over the first data row.
### Failure modes
One ordinary improvement bar chart, only a favorable task, weak-baseline reference, colorful table duplication, hidden negative reductions or missing tasks.
### QA questions
Are main tasks covered? Is comparator selection consistent? Is breadth visible beyond exact table values? Are metric directions, task counts, ties and signs honest?
## REGRESSION_ALL_BASELINES

### Scientific question
How faithfully does each benchmark method reproduce observed values under the same task definition?
### Best used when
Prediction fidelity is a claim and matched observation/prediction arrays exist for all fair baselines.
### Avoid when
Regression does not address a claim, observations are not aligned, or the composite shrinks labels below readability. Split task composites; retain baseline coverage across the declared evidence set.
### Evidence schema
Task/horizon/sample IDs, observed value, per-method predictions, units, full-sample R², display sampling policy, limits and benchmark roster. Metrics use the declared full arrays, not a favorable display sample.
### Core encoding
Observed versus predicted scatter, common y=x and axis ranges, comparable point style and prominent R². Optional fitted line is distinct from identity. Equal visual weight across baselines.
### Accepted visual structure
Observed M5 has a balanced tiled all-method composite, local model/R² text in a data-clear corner and a shared closeness key; individual model panels also exist. The example grid dimensions and number of models are not defaults.
### MATLAB route
tiledlayout or explicit axes, one computed limits vector and identical sample policy passed to every panel; approved fig_draw_r2_regression-like helper pattern without copying project code.
### Python route
GridSpec/subplots with shared axes, a shared identity line convention and generator-computed full-array R². Keep point sampling identical across methods; do not jitter evidence points.
### Required comparators
Proposed method and every fair main-benchmark baseline. Declare per-figure `comparator_set` and top-level benchmark `comparator_set` for machine-checkable omissions. For multi-figure evidence, explicitly map coverage rather than silently omitting methods.
### Annotation rules
Same metric precision and position for every method, dataset/horizon in caption or small functional header; avoid giant repeated legends.
### Layout rules
Declare `shared_scale_group` and `common_limits_documented=true`. Reuse scale/sampling in requested standalone panels. Split composites before reducing approved fonts.
### Failure modes
Only one or two chosen baselines, per-method limits that hide bias, R² on different samples, highlighted proposed model making others invisible.
### QA questions
Is baseline coverage complete against the benchmark roster? Are y=x, limits, sample regime and R² computation consistent? Are all panels readable and comparably weighted?
## ABLATION_EFFECT_FOREST

### Scientific question
What direction, size and uncertainty does each component change have relative to Full?
### Best used when
Paired saved runs/tasks permit effect estimates, with repeated evidence for intervals. Prefer a forest when matrices already dominate the paper.
### Avoid when
Only a continuous parameter is varied (use sensitivity profiles), or no interval can be estimated honestly. Show descriptive paired changes without invented uncertainty.
### Evidence schema
Full and variants, matched units, metric/direction, effect definition, estimates, interval endpoints/method/seed, task counts and optional full/tie/variant outcome counts.
### Core encoding
Full at the defined reference, zero line, horizontal intervals and marker summaries; optional aligned task-outcome strip preserves neutral and contrary evidence. Distinguish CI-excludes-zero from formal significance with multiplicity handled separately.
### Accepted visual structure
Observed A1 gives the forest most width, highlights Full's reference row, uses open/filled markers and aligns a secondary outcome panel with row-specific denominators.
### MATLAB route
Horizontal errorbar or line segments with scatter markers; share y positions with the optional outcome axes. Load saved paired statistics; Full remains visible.
### Python route
Matplotlib errorbar with asymmetric xerr, common y coordinates and optional stacked counts. Start from the Python publication template and adapt to saved evidence.
### Required comparators
Full and every relevant ablation, including ties, worse Full outcomes and failed/unsupported variants retained with truthful status.
### Annotation rules
State effect direction in the x label, mark reference explicitly, preserve signed effects and each row's N; no hardcoded task totals from a previous paper.
### Layout rules
Long names get left margin. Share rows and a compact legend. Keep confidence whiskers readable; do not revert to another heatmap for visual variety alone.
### Failure modes
Full omitted, cherry-picked seeds, manual interval shifts, neutral results concealed, copied fixed N, repeated ablation heatmap, unrelated runtime metrics mixed into the panel.
### QA questions
Is Full visible? Are effect sign, interval and N clear? Are ties/contrary outcomes preserved? Are counts consistent with the evaluation set? Does the form expose uncertainty?
## COMPUTATIONAL_COST_TRADEOFF

### Scientific question
What resource cost accompanies accuracy, and does the measured pipeline meet its operational timing needs?
### Best used when
There is a compute/deployment claim and comparable saved parameter counts, timing, throughput, memory or operation counts. Choose only available measurements.
### Avoid when
A compact cost table communicates the evidence better, costs are incomparable, or a single latency trace is being presented as an all-method accuracy-cost frontier.
### Evidence schema
Method, metric/unit, hardware/software, batch size, pipeline stages, warmup/synchronization policy, repetition unit, raw timings and summary definitions. Parameter/FLOP/MAC counting convention is distinct from measured timing/memory.
### Core encoding
Repeated-timing distributions with matched-unit effects, measured condition-by-resource/performance atlases, or a true temporal latency view with operational regime, tail and diagnostic structure. A compact table carries a bare all-method cost list. Do not draw two-dimensional accuracy-cost Pareto scatter/frontier plots. Log axes retain units. Computational evidence stays separate from component ablation.
### Accepted visual structure
The current final package deliberately keeps all-model compute comparison as a table. Observed E2 is a separate deployment-latency figure: raw samples, explicitly identified trend, mean/tail references and horizon bands. It is not an observed all-model trade-off chart. This table/figure split is part of the learned design choice.
### MATLAB route
Explicit axes for distributions/paired effects or condition-resource matrices. A temporal latency view keeps raw samples and real regime/tail diagnostics; any movmean is a declared descriptive aid, not an independent evidence layer. Use only saved timings; plotting never reruns inference.
### Python route
Matplotlib distribution/interval/conditional-matrix objects or actual step/time samples with meaningful regime/tail diagnostics from saved timing tables. No Pareto scatter. Keep timing summaries and descriptive smoothing definitions in provenance/caption; do not install a profiler just to fill missing fields.
### Required comparators
For comparative cost, all relevant fair methods measured under comparable protocols. A single-method deployment claim may instead compare observed latency against a stated deadline; do not infer relative efficiency from it.
### Annotation rules
State units and reference definitions, actual batch/hardware/protocol in caption/provenance. Keep raw timings visible under any declared trend. NaN/unavailable memory or FLOPs are not zero.
### Layout rules
Separate compute evidence from ablation. Reserve key clearance and place regime labels in a data-clear band. Shared scales only when the intended comparison requires them; otherwise document differing scales.
### Failure modes
Unexplained hardware differences, unlabeled log axes, fake operation counts, cost/ablation mixtures, decorative Sankey/bubbles, simple latency curves decorated with unrelated panels, two-dimensional Pareto scatter, table data turned into a low-information cost list graphic.
### QA questions
Are units/hardware/protocols comparable? Are parameter counts and measured latency distinguished? Is the performance metric shared? Are log scales clear? Does the figure add more than a table?
## ORIGIN_ERROR_DISTRIBUTION

### Scientific question
Does error vary across evaluation origins, and which methods have broad or heavy-tailed error?
### Best used when
Enough saved matched origin-level errors support a distribution, beyond a mean benchmark table.
### Avoid when
Only a few seeds/units exist; use dots/ranges. A KDE is not additional observations or uncertainty in the mean.
### Evidence schema
Origin/sample IDs, method, task, per-unit error, shared normalization and any displayed transformation with formula.
### Core encoding
All-method violin/raincloud or raw-point distribution on one metric scale with labeled center/interval summaries.
### Accepted visual structure
Observed M4 keeps all methods on one large axis, stable method identity and a clearly stated transformed-error axis. Standalone dataset views omit decorative panel letters.
### MATLAB route
Explicit density patches or the project's existing violin helper, summaries and a common scale; no numeric y offsets.
### Python route
Matplotlib violinplot or explicit density polygons from the existing statistics stack; preserve paired raw-unit provenance and state bandwidth/transform.
### Required comparators
All fair methods in the declared task comparison, including tails and failures.
### Annotation rules
Name the metric transformation; define the plotted center/spread. Never silently smooth away heavy tails.
### Layout rules
Wide enough for long method labels, common units, no redundant per-method legend. Split tasks rather than shrinking fonts.
### Failure modes
One violin per exported method, tiny sample distributions, unlabeled log transform or non-comparable normalizers.
### QA questions
Are origin units matched? Are all methods shown? Does the normalization match the table? Is distribution smoothing disclosed and appropriate to N?
## ERROR_REGIME_COMPOSITION

### Scientific question
Which physically meaningful regimes contribute to total prediction error?
### Best used when
A saved decomposition has a valid additive attribution and reveals mechanisms beyond total errors.
### Avoid when
The metric is not additive and no defensible attribution is declared, groups are invented, or connected shapes imply false interpolation between categorical methods.
### Evidence schema
Method, task/horizon, regime, contribution, total, normalization and exact attribution formula. Show that components close to the declared total; squared-error-share RMSE attribution is not a raw sum of regime RMSEs.
### Core encoding
Validated additive contribution compositions or contribution-by-condition matrices with common regime identity and complete methods; exact totals can remain in tables. Composition segments require a real additive meaning. A method-ranking chart without components must not be labeled an additive composition.
### Accepted visual structure
Observed G2/G3 separates each task/metric into a readable square panel with its own compact regime key. Transfer the additive decomposition and layout; connecting bands across categorical methods are optional and must not imply measured intermediate values.
### MATLAB route
Explicit stacked bars/patches from saved contribution tables, visible units and validated totals; avoid hand-entered heights.
### Python route
Matplotlib bar(bottom=...) or aligned regime profiles with saved totals; no automatic percentage normalization.
### Required comparators
All methods in the declared benchmark task and the same scientifically defined regime bins.
### Annotation rules
Clarify absolute normalized contributions versus percentages and metric-specific attribution. Do not use the same formula blindly for MAE and RMSE.
### Layout rules
Maintain method order and regime palette; shared limits when comparing panels, or document local scales. Place the key above a data-clear region.
### Failure modes
Percentage stacks mislabeled as absolute errors, nonadditive components, decorative flow bands presented as measurements, overcrowded all-task composites.
### QA questions
Do contributions close to saved totals? Are definitions identical across methods? Are units, attribution and scale choices clear? Does the view explain a mechanism?
## COORDINATED_CURVE_DIAGNOSTIC

### Scientific question
Under matched controls, where does trajectory coordination change the output, and how do state or expert-weight changes explain those changes?
### Best used when
Saved population effects and aligned observation/reference/coordinated trajectories or state arrays exist, and the mechanism requires more explanation than another aggregate performance comparison.
### Avoid when
Only a few aggregate means are available, case identities or controls differ, or a source provides no state/weight data. Use a paired-effect view or table for the evidence that actually exists; do not invent tracks.
### Evidence schema
Named task/fold/condition and control IDs; evaluation units; metric direction, normalization and denominator; fixed case-selection rule; issue origin and lead/timestamps; observations and reference/control/output arrays; stable member IDs and reference identity; initial/final states or weights when available. Any envelope includes its source population and estimator. Risk coefficients, eligibility and fallback behavior retain their actual meaning.
### Core encoding
A matched effect matrix or paired-effect summary establishes the evaluated scope. Aligned local tracks then show demand/state context, output changes from the same reference, and the corresponding state/weight changes. Connect those roles through the same case, horizon and member order. Every scientific layer must trace to its actual array and definition in the existing manifest; this is a composite diagnostic, not an exemption for decorated simple-line charts.
### Accepted visual structure
One arrangement uses a control-by-metric matrix beside case columns. Each case aligns an observed/reference/coordinated forecast, a per-lead change strip and an expert-weight change map when those quantities exist. Transfer the evidence relationships and alignment; neither three columns nor those exact tracks are mandatory. Remove redundant count-only panels when they add no distinct information.
### MATLAB route
Use saved tables/arrays with explicit aligned axes, vector paths/patches and a signed change matrix. Distinguish any finite-expert envelope from a calibrated prediction interval; reserve separate labeled keys for physical output changes and weight changes.
### Python route
Use the existing Matplotlib pipeline with a shared lead axis for each case, explicit grids and saved matrix/trajectory arrays. Derive extrema, differences and quantiles from those arrays; preserve missing data and record the quantile definition when relevant. Do not smooth or amplify small differences for appearance.
### Required comparators
The same initial/reference output and all controls needed to isolate the stated mechanism. Hold the relevant bank, population and other matched conditions fixed as required by the experimental design; label real differences. Full is not assumed to beat every control or metric.
### Annotation rules
State whether a cell is a same-fold relative percentage, a pooled effect, a task mean or a physical-unit difference. Weight differences are percentage points when computed as `100 × (new weight − initial weight)`, not relative percentages. Expert range/IQR shows dispersion, not coverage or confidence. A within-window maximum and a threshold exceedance are separate events.
### Layout rules
Use a shared lead/timestamp alignment within each case, stable expert order, legible reference-expert marks and explicit units. Comparable effect cells share a meaningful zero scale; different physical targets retain separate labeled scales. Keep headers, legends and colorbars out of data lanes. Local examples illustrate the mechanism and do not estimate population effects.
### Failure modes
Changing representative cases during visual revision, swapping effective banks across controls, silently pooling different denominators, labeling expert spread as predictive uncertainty, introducing unsupported event labels, interpreting positive weight changes as improved error, or using small curve differences as proof of novelty.
### QA questions
Do the summary and cases answer different parts of one question? Are all controls, denominators, case IDs, member orders and lead arrays matched? Are adverse and unchanged outcomes visible? Are bands and weight/output units explicit? Does the final-size view preserve every curve, key and annotation?
# Accepted / Rejected Design Lessons

| Reject in the stated context | Prefer |
|---|---|
| Two plain Pearson/MIC heatmaps, or basic heatmap replacing required tree/triangle structure | Shared-order dual triangles with data-derived clustering and explicit metric keys |
| Sparse Mantel or fabricated feature groups | Real dense relational structure, otherwise compact dependency view/table |
| Tiny pairplot text, automatic panel letters, small/off-center r | Explicit cells, prominent centered r, legible outer labels |
| Single-task improvement bar repeating the exact-value table | Task/horizon/metric breadth, distribution or interaction |
| Regression with selected baselines or per-method favorable limits | Complete baseline family, identical sampling and shared scales |
| Ablation as another repetitive heatmap or Full-forcing seed selection | Full-inclusive effects/intervals, ties and contrary outcomes |
| Compute cost mixed vaguely with ablation | Independent cost evidence or a better table; separate deployment trace |
| Many low-information panels or compressed fonts | Fewer readable panels under one scientific question |
| Curve mechanism reduced to repeated outcome counts or visually amplified examples | Matched effect summary plus genuinely aligned trajectory/state diagnostics with fixed cases |
| Expert spread labeled confidence, mixed denominators, or shifted zero/tick coordinates | Explicit source-population/band semantics, matched denominators and numerically faithful marks |
| Decorative 3D/Sankey/bubbles and unexplained color changes | Justified data dimensions and stable method identity |

