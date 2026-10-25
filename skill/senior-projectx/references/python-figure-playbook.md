# Python Figure Playbook

Use when project analysis/results already live in Python, the user requests it, statistical diagnostics fit the existing stack, or PDF/SVG are the target vectors without a MATLAB FIG requirement. Do not migrate a stable MATLAB pipeline just for aesthetics. Retrieve the nearest recipe from `figure-pattern-pool.md` before selecting plotting APIs.

## Design before implementation

Scientific question → evidence schema → accepted recipe → backend → physical layout → standalone visual QA → targeted revision → manuscript-rendered QA. Follow the pool's quality hierarchy: scientific correctness, evidence completeness, plot-type fitness, information density, comparator visibility, statistical readability, layout balance, typography, color, decoration.

For “draw all chapter figures,” internally map manuscript questions and saved tables/results to claims and evidence roles, retrieve recipes, choose backends and final sizes, then draw. For “match my previous figure,” inspect the accessible accepted design and transfer encoding/layout, never old values. For “ugly,” diagnose plot fitness, sparse information, missing comparators, panel architecture and weak annotations before recoloring. Do not redesign an accepted figure without changed requirements or a concrete defect.

## Existing stack and setup

Prefer the project's NumPy, pandas, Matplotlib and SciPy. Use statsmodels/sklearn only when already available and scientifically needed. Do not add seaborn/Plotly/Altair merely to plot. Existing seaborn is fine, but final geometry belongs to explicit Matplotlib object-level controls.

- Start from `templates/python_publication_figure_template.py`. It accepts saved effect CSVs and exports only requested formats. `--demo` is an explicitly labeled layout demonstration, never paper evidence.
- Set centimeters/inches and insertion width before drawing. Use `fig, ax = plt.subplots(...)` or GridSpec with real margins; notebook display and automatic tight_layout are not layout QA.
- Use a configurable font. For required Times New Roman, verify availability with font_manager; report and record any compatible fallback rather than claiming a font that was absent. English/numeral and Chinese text must use fonts with the needed glyphs.
- Configure PDF/PS font embedding and SVG text semantics (`pdf.fonttype=42`, `ps.fonttype=42`, `svg.fonttype='none'` when appropriate). Confirm in exported files rather than assuming settings guarantee every backend result.
- Persist/reuse one method-style map per paper. Share markers, line weights, typography, panel proportions, legend conventions and output widths with MATLAB figures. Do not inherit a source paper's specific colors.

## Recipe implementation

| Recipe | Object-level route |
|---|---|
| CORR_DUAL_TRI_STREE | Compute a declared distance/linkage on real observations or saved structure, obtain leaves once, reorder both matrices identically, use explicit masks/cells and an aligned tree. Separate signed/nonnegative keys. |
| DEPENDENCY_MANTEL_DENSE | Use real multivariate block distances and valid saved/permutation statistics; draw link widths/styles with a explained key. Sparse relations should trigger another encoding. |
| PAIRPLOT_PROMINENT_R | Explicit grid cells, diagonal distributions, lower scatter/regression, bold centered upper r. Suppress redundant inner ticks and check outer labels. Existing PairGrid is a starting point, not completion. |
| MAIN_PERFORMANCE_BREADTH | Shared task/horizon space and normalized metric reductions plus optional outcome breadth; strongest comparator and denominators come from saved results. |
| REGRESSION_ALL_BASELINES | Shared-axis scatter panels for the complete fair roster, common y=x/sample definition and full-array R²; selective standalone export reuses those same results. |
| ABLATION_EFFECT_FOREST | Horizontal asymmetric intervals, Full reference, signed effects, row-specific N and optional full/tie/variant counts. No repetitive heatmap default. |
| COMPUTATIONAL_COST_TRADEOFF | Cost table, repeated-timing distribution/paired effects, measured condition-resource atlas, or temporal latency with real regime/tail/diagnostic structure. Use a trade-off view only when its points contain enough information. State hardware/batch/protocol and log units. |

## Statistical and visual semantics

Bootstrap intervals, effect sizes, regression and confidence bands derive from saved raw results under the prespecified unit/dependence structure. Record estimator, random seed, interval rule and sample IDs in ordinary provenance. Never move observations, pick favorable seeds, enter desired numeric values, hide failed methods, replace NaN/unavailable metrics with zero, or apply undeclared smoothing. A display subsample does not redefine the metric population.

For heatmaps, use sequential/nonnegative and diverging/signed semantics with a meaningful pivot; explicit missing masks, luminance-aware text and limited precision. Avoid rainbow palettes and annotation overload. For pairplots, verify statistical text is centered and larger than ticks, diagonal distributions carry meaning, variable labels fit and no needless letters remain.

Keep text, lines, markers and cells vector when practical. Large image/dense data layers can be rasterized selectively with a stated reason, while axes, text, legends and annotations remain vector. No automatic title or decorative panel letters; labels are for caption/body reference needs. Keep units, strongest comparator, all required baselines, stochastic uncertainty and shared comparison scales visible. Exact numbers can stay in tables.

## Export contract and QA

Python source is the `.py` generator. Export PDF/SVG/PNG as declared in per-figure `required_formats`; do not require `.fig`. PNG at 600 dpi is a useful high-resolution QA/raster option when requested, not a universal venue rule. Vector formats do not have a submission dpi requirement. Retain physical canvas dimensions; indiscriminate tight bounding-box cropping can change insertion scale.

For a hard EMF requirement, use a reliable conversion chain already present in the project and inspect its fonts/clipping. Do not install a complex conversion toolchain by default or claim Python produces MATLAB FIG. If the existing project is MATLAB and FIG/EMF controls the workflow, route there. Mixed backends share the paper's style contract.

For each first draft, inspect the exported vector at final size: readable font/statistics, clipping, overlap, comparator roster, shared scales, units, color accessibility, legends and caption consistency. Then inspect the actual manuscript-rendered page (Word export for DOCX, the compiled venue PDF for LaTeX). Use `manuscript_rendered_qa`; legacy `word_rendered_qa` remains accepted. Set `annotation_readability_checked` only after reviewing final-width fonts and statistics. Recipe-specific questions live in the pool; the validator only checks declarations. Fix the identified geometry/encoding problem, and stop when relevant evidence is sufficient.

## Shared panel controls

Comparison panels share axis limits, scale, full metric population, display-sample protocol, normalization, panel dimensions and labeling logic where scientifically appropriate. Avoid dashboard decoration and an unmodified library theme when explicit scientific geometry is needed. Keep only formats with an editing, submission or QA consumer; approximately 600 dpi is the default for a requested raster unless the venue overrides it. Follow `figure-and-delivery.md` for aspect-preserving crops, protected plot frames, separate EMF export and Office-size typography checks.

Project图件采用 [信息量与图型规则](project-figure-policy.md)，取消简单柱线和稀疏散点默认输出。曲线和可加色块可以作为真实工程诊断中的信息层，装饰和重复子图不构成信息增量。
