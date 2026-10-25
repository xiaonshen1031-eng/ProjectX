# MATLAB Figure Playbook

Use this reference when a manuscript needs MATLAB-generated engineering figures, especially when the final deliverable is a Word manuscript with EMF/vector insertion.

## Advanced recipe routing and backend choice

Retrieve the nearest scientific question/evidence schema from `figure-pattern-pool.md` before drawing. Prefer MATLAB when explicitly requested, already used by the analysis/generator family, required for editable FIG or reliable Word EMF, or supported by approved local figure utilities. Prefer the parallel Python playbook for an existing Python statistical pipeline and PDF/SVG delivery without FIG. Do not change language merely for style. Mixed backends share fonts, method colors/markers, line weights, panel proportions, keys and physical widths.

Quality priority: scientific correctness → evidence completeness → plot-type fitness → information density → comparator visibility → statistical readability → layout balance → typography → color/aesthetics → decorative polish. A clear table can beat a complex graphic; a genuine temporal, trajectory or continuous relation can use curves with scientifically relevant measured diagnostics.

| Recipe | MATLAB implementation decisions |
|---|---|
| CORR_DUAL_TRI_STREE | Shared data-derived order for the two metrics; explicit triangle masks, aligned dendrogram and labeled metric-specific keys. Reuse approved SHeatmap/SMatrix/STree or native patches/linkage; no decorative/manual clustering. |
| DEPENDENCY_MANTEL_DENSE | Select only with real sufficient relational structure. Keep full multivariate block distances and precomputed effect/p-value semantics; explain permutation design and weaken secondary links. |
| PAIRPLOT_PROMINENT_R | Explicit cell axes, diagonal distributions, lower scatter/regression and upper statistics; center bold r using normalized coordinates, common fonts and outer-only ticks. No automatic letters or clipped labels. |
| MAIN_PERFORMANCE_BREADTH | Task/horizon/metric comparison space with strongest-baseline-relative changes and optional pairwise outcomes; exact values remain in tables when possible. |
| REGRESSION_ALL_BASELINES | All fair benchmark methods, shared axis limits and y=x, identical sample regime and R² calculation; tiledlayout or explicit axes; proposed emphasis never erases baselines. |
| ABLATION_EFFECT_FOREST | Full-inclusive paired effects, horizontal uncertainty whiskers, signed effects and honest neutral/contrary outcomes; use a sensitivity profile for continuous parameters. |
| COMPUTATIONAL_COST_TRADEOFF | Cost table, repeat-timing distributions/paired effects, condition-resource atlas, or real latency with regime/tail/diagnostic structure. Use a trade-off view only when its points contain enough information. Log scales retain units. |

Built-in `heatmap`, `plotmatrix` and `subplot` are not banned, but are insufficient defaults when the scientific structure requires triangles/tree alignment, prominent cell statistics, or controlled complex geometry. Prefer explicit axes or tiledlayout for those cases.

### Dependency lessons

Use utilities only when already approved in the project; no vendoring or skill dependency. Read its existing dependency record for version/license/API changes. In an accepted analysis workflow, precomputed Mantel matrices preserve full multivariate tests instead of scalar proxies, pairplot label formatting addresses cell collisions, and the exact MIC estimator is declared without silent substitution. Those local versions and patches are not global requirements. Without a utility, reproduce the scientific encoding in native MATLAB or the project's Python stack, not a lower-quality default.

The current D1 source clusters each metric separately; its triangular layout is an observed design example, not proof of shared ordering. For the shared-order recipe, obtain one order from a declared scientific distance and reuse it for both metrics and the tree. Use only source-appropriate statistical inference; no fixed group counts, cluster counts or permutation counts.

## Lessons From Final Manuscript Revisions

Late-stage manuscript figure work should not be treated as decoration. Before regenerating a figure family:

- decide what claim each figure supports
- remove low-value standalone plots that repeat tables without adding interpretation
- limit image-panel figures to the smallest number of representative validation or test cases needed for the claim
- avoid excessive subfigures, narrow panels, and large blank margins
- choose plot types deliberately: paired effects, conditional distributions, metric matrices, calibrated coverage/residual views and image panels should each serve a different evidence role
- verify the final rendered Word/PDF page, because a figure that is readable in MATLAB or PNG preview may still be clipped, flattened, or crowded after EMF insertion

For image-panel papers, build panels with padding or `contain` logic rather than cropping. Preserve target aspect ratios and avoid forcing all examples into one row when this makes panels unreadable.

## Slandarer-Inspired MATLAB Practices

The slandarer MATLAB repositories are useful examples of publication-aware plotting habits:

- `MATLAB-PLOT-CHEAT-SHEET` uses an explicit figure canvas, nested axes, normalized panel positions, and `Painters` rendering for vector output.
- `slanColor` emphasizes scientific colormaps, large palette libraries, perceptually safer alternatives to default colormaps, and pivot control for diverging data.
- `MATLAB-special-heatmap` wraps heatmaps as an object with explicit support for cell formats, NaN handling, text annotations, labels, colorbar placement, and triangular/correlation styles.

Adopt the principles, not copied code:

- set the figure size explicitly in pixels or centimeters before drawing
- create axes objects intentionally instead of relying on default subplot spacing
- use a vector export route supported by the installed MATLAB release; legacy `Painters` does not guarantee vector output and R2025a ignores the `Renderer` property for `print`/`saveas`
- export `.fig` for requested editable MATLAB source, `.emf` when Word requires it, and `.pdf`/`.png` according to the figure contract; do not export every format automatically
- use professional colormaps for sequential, diverging, cyclic, and categorical data instead of default rainbow or one-note palettes
- for diverging metrics, set a meaningful pivot such as zero, baseline score, or clinical/engineering threshold
- for heatmaps, handle NaN values visibly and choose annotation text color according to cell luminance
- place legends only after checking data occlusion; use direct labels or compact legends for dense plots
- avoid decorative titles inside axes when the caption already names the figure
- tune font sizes for the final physical figure width, not for the MATLAB screen

## MATLAB Export Checklist

For each submission figure:

1. Fix size and renderer before plotting.
2. Draw with explicit axes and stable margins.
3. Use `Times New Roman` for English labels and numerals; use `Microsoft YaHei` bold for Chinese labels.
4. Use line widths, marker sizes, and font sizes that remain readable at the final Word width.
5. Save `.fig` when editable MATLAB source is requested.
6. Export `.emf` for a Word requirement, `.pdf` for vector publication/QA, and `.png` for requested preview/raster delivery (600 dpi is a useful option, not a rule for vectors).
7. Export only per-figure required formats; PDF + PNG does not imply FIG + EMF.
8. Insert the required vector into the intended manuscript.
9. Render DOCX through Word or compile the venue LaTeX source to PDF.
10. Inspect the rendered page for clipping, raster fallback, hidden legends, unreadable labels, and incomplete colorbars.

When starting a new MATLAB result figure, copy or adapt `templates/matlab_publication_figure_template.m`. Replace its demo data and axes with the manuscript's source data, but preserve the explicit canvas sizing, axes positioning, typography, renderer, and multi-format export pattern unless the customer template requires something different.

The publication, spatial and feasibility templates accept an optional format list while preserving their original one-argument calls; their default is PDF/PNG. Every illustrative output is labeled DEMO. Replace demo arrays with saved results and complete ordinary provenance before manuscript use. Inspect final vectors rather than inferring native editability from the extension.

Check the first draft with the recipe's questions: font/statistical readability at final width, complete comparators, shared scales, no clipping/overlap, visible keys, faithful uncertainty, and consistent caption/body. Revise identified issues, inspect the actual manuscript page, and stop once accepted. Do not move regression points, invent values, hide failed methods, convert missing metrics to zero, or smooth evidence without disclosure. If approved fonts clip, enlarge margins/canvas first.

## Recommended Plot Choices

Match plot type to evidence:

- method ranking across few metrics: table or effect/range estimates with real uncertainty and matched units
- seed/fold stability: dot plot with mean/standard deviation overlay, not a flat boxplot with too few points
- ablation: Full-inclusive paired effect forest, observed-unit changes or conditional component effects
- localization or prompt quality: metric matrix with readable annotations, or threshold-calibration view with actual uncertainty, coverage or conditional errors
- image segmentation examples: compact validation panels with raw image, ground truth, strongest comparator, and proposed result
- uncertainty or spatial response: heatmap only when spatial structure matters; otherwise use distributions, coverage/residual diagnostics or true continuous-response curves with relevant evidence layers
- external/auxiliary evidence: separate visual examples from supervised metrics, and state label limitations clearly

## Heatmap Rules

For heatmaps and confusion matrices:

- do not use a single heatmap style for every matrix in the manuscript
- choose sequential colormaps for non-negative scores and diverging colormaps for signed differences
- pivot diverging colormaps at the scientifically meaningful neutral value
- display only the necessary numeric precision
- switch annotation text color based on rendered luminance
- wrap or shorten long method names; do not let labels collide with the colorbar
- if EMF conversion rasterizes the image poorly, redraw cells as vector rectangles with independent text labels

## Caption and Text Integration

Every figure must be analyzed in the manuscript text:

- state the main observation before listing numeric details
- connect the visual pattern to a table or metric when possible
- explain limitations without turning a result into a failure gallery unless the paper explicitly studies failure modes
- avoid repeating the caption verbatim in the body text

Every table must also be interpreted:

- identify the strongest fair comparator
- describe absolute values and relative improvements only when supported by the CSV/JSON source
- distinguish validation, group-CV, held-out, and auxiliary experiments
- avoid claiming superiority when the table only supports competitiveness or diagnostic value

## Source Links For Further Study

- slandarer GitHub profile: `https://github.com/slandarer`
- MATLAB plot cheat sheet: `https://github.com/slandarer/MATLAB-PLOT-CHEAT-SHEET`
- slanColor colormap tools: `https://github.com/slandarer/slanColor`
- MATLAB special heatmap: `https://github.com/slandarer/MATLAB-special-heatmap`
- STree: `https://gitee.com/slandarer/matlab-stree-dendrogram` and `https://www.mathworks.com/matlabcentral/fileexchange/160048-stree-special-dendrogram-plot`
- MATLAB pairplot: `https://github.com/slandarer/MATLAB-pairplot`

## Advanced heatmap/pairplot reference consolidation

When the question needs these encodings, consult the primary implementations [MATLAB-special-heatmap](https://github.com/slandarer/MATLAB-special-heatmap) and [MATLAB-pairplot](https://github.com/slandarer/MATLAB-pairplot). Use explicit axes, triangle masks, custom cell annotations, intentional diagonal/lower/upper roles and deliberate colorbar/legend geometry. Different upper/lower metrics require independent declared encodings and scales; they are not interchangeable statistics. A pairplot's diagonal distribution, scatter and association coefficient describe different aspects of the same observations.

These repositories are visual/implementation references, not mandatory installations, vendored packages or hard dependencies. Retain the current generator and consolidate its useful controls. Follow `figure-and-delivery.md` for individual EMFs, aspect-preserving crop, protected plot frames, legend occlusion and typography at insertion size.

Project图件采用 [信息量与图型规则](project-figure-policy.md)，取消简单柱线和稀疏散点默认输出。曲线和可加色块可以作为真实工程诊断中的信息层，装饰和重复子图不构成信息增量。
