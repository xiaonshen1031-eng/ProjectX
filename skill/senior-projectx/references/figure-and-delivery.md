# Figure and Delivery

## Route the figure by its scientific job

Distinguish a conceptual mechanism, a method workflow, a verified result and an export/insertion task before selecting tools. Introduction mechanisms explain the research problem through the actual system; workflows expose method operations; result figures show outcomes supported by saved evidence. A local decision or safety-boundary verification belongs to the result class, even if it contains actions and successor states.

Use `editable-diagram-playbook.md` for native overview/workflow/principle figures and connector repairs. Use `advanced-figure-workflow.md` plus one relevant plotting backend for results. Use `word-figure-integration.md` for an accepted user-edited source, EMF conversion, manuscript insertion and synchronized figure numbering. Do not demand Python/MATLAB for a requested VSDX diagram or redesign an accepted source just to export it.

Use the task's current source, scientific question, final physical size and frozen revision constraints as the compact working contract. Existing notes or the per-figure mapping are sufficient; create no unused forms. Rendering, source inspection and editability tests must refer to that same saved revision.

## Figure Pipeline

Before plotting results, retrieve `figure-pattern-pool.md` from the scientific question and saved evidence schema, select MATLAB/Python from project and delivery requirements, and fix physical size. For native diagrams use the routed editor instead. Inspect actual supplied reference files and their renders; transfer design grammar, never another paper's topology, terms or result values. First-draft visual QA checks the appropriate scientific role, density, required comparisons, scales and readability; revise the diagnosed failure, then inspect the manuscript page. Stop after accepted QA unless something relevant changes.

When the user asks for a full paper package:

1. identify which figures are scientific result figures
2. separate them from conceptual flowcharts
3. preserve the exact mapping from manuscript figure number to source file
4. store final figures in submission-ready formats
5. write the evidence role of each figure before drawing it
6. confirm each final figure is analyzed in the manuscript body, not only captioned

For editable scientific delivery, select formats from the user/venue and per-figure manifest:

- the requested native diagram source, such as `vsdx`, with separately movable picture assets where used
- `emf` for Word insertion
- `fig` only for requested MATLAB re-editing; a Python generator remains `.py`
- `svg` or `pdf` as Python/native publication vectors or intermediates in an existing verified EMF conversion chain
- `png` only as a preview or QA artifact unless the user or journal accepts raster insertion

The current `validate_figure_manifest.py` validates computational result-plot contracts; it does not certify native diagram editability. Record a conceptual diagram's native source, meaning and actual checks in the existing figure/source mapping. Do not invent data files or a Python/MATLAB generator merely to fill result-plot fields.

After inserting EMF into Word, always render the DOCX to PDF and inspect the final page. Standalone figure previews are not enough because Word/LibreOffice conversion can crop method labels, rotated tick labels, legends, and colorbar tick labels.

For MATLAB figures, follow the dedicated workflow in `matlab-figure-playbook.md`. Use explicit physical sizes and axes positions, a vector export route supported by the installed release, the retained template's typography, professional colormaps, and only requested exports. A renderer setting alone does not establish vector output. For Python, use `python-figure-playbook.md`; never force `.fig` or install a conversion stack merely for completeness.

## Flowcharts and Principle Diagrams

Follow `editable-diagram-playbook.md`. Derive a mechanism from the introduction and method; derive a workflow from actual inputs, transformations, decisions and outputs. Organize one dominant system or object with compact local relations, planned connector lanes and short labels. Meaningful complexity comes from real dependencies and state changes, with no duplicated modules, fake data curves or detached explanatory cards added for appearance.

For requested Visio/PowerPoint editing, retain native text, connectors, symbols, curves and sensible groups. Separate transparent scene icons may improve recognition, but should not dominate the mechanism. A generated full-image diagram converted to a vector wrapper or imported as one native-editor object is not genuinely editable. Preserve approved icons, words and strokes during local cleanup; verify shared ports, crossovers, arrowheads, switch gaps and temporal leaders in the saved native source and final-size render.

For a decision result, use the preparation/condition, boundary and action/outcome guidance in `advanced-figure-workflow.md`; do not replace verified outcomes with a workflow. Conceptual mechanisms and actual trajectories use arrows or lines according to their actual relationships.

If the figure is intentionally left blank for later manual drawing, keep its caption and provide a detailed drawing prompt. Do not invent a placeholder image unless the user asks for it.

## Heatmap and Matrix Figures

For heatmaps and metric matrices:

- do not reuse the same heatmap style for every matrix if different evidence types would be clearer as paired effects, distributions, or conditional diagnostics
- choose sequential colormaps for non-negative scores and diverging colormaps for signed differences
- set the diverging pivot to a meaningful value, such as zero, baseline score, or decision threshold
- choose cell annotation color from actual rendered cell luminance
- use white text on dark cells and black text on light cells
- verify the result after EMF insertion, because color conversion can differ from the PNG preview
- keep colorbar tick coordinates and labels numerically consistent; repair a clipped endpoint through canvas/colorbar padding or label alignment, without moving the tick to a different value and retaining the old label
- use explicit vector rectangles and independent text when `imshow` or rasterized heatmaps convert poorly
- keep long method names readable by increasing left margin or wrapping labels

## Legends and Dense Result Views

For line plots, trajectory plots, and composite profiles:

- keep legends inside only when they do not cover data
- inspect overlap after final EMF insertion, not only in the MATLAB/Python preview
- distinguish overlapping zero-valued methods with marker/line styles or a disclosed offset along a categorical axis; retain their measured coordinates and never shift a zero along the quantitative axis for visibility
- avoid isolated-dot plots with excessive whitespace unless the plot has a clear diagnostic purpose
- choose views from the engineering relationship; a sparse series of ordinary charts is not a substitute for analysis

For seed/fold stability with only a few runs, prefer dot/range plots with mean and variability overlays over boxplots that imply a distribution the data cannot support.

For effect forests and uncertainty views, compute limits from all interval endpoints as well as the reference, with visible padding for caps and markers. MATLAB/Matplotlib automatic limits and text-bounds checks do not prove that whiskers, arrows or data marks are inside the final axes. Inspect the left/right endpoint of every interval in the standalone vector and inserted page; a truncated interval changes the scientific interpretation even when every label is visible.

## Delivery Folder Pattern

When preparing a delivery package, prefer this split:

- `code`
- `figure`
- `data`

Inside `data`, separate:

- benchmark or topology source data
- renewable or exogenous input data
- original code outputs
- final manuscript tables or corrected figure data

## Provenance File

Update the existing provenance/source mapping for corrected figures or tables. Create a separate file only when a downstream redraw, manuscript assembly or handoff consumes it.

Record:

- manuscript figure number
- final delivered filename
- whether it is original output or revised redraw
- source script or source data path
- insertion format used in the final manuscript
- QA artifact used to verify final rendering, such as a PDF page screenshot

Per-figure `required_formats` overrides the legacy top-level list. `recipe_id` must be registered or `CUSTOM` with a scientific justification. `reference_pool_ids` records design sources, not experimental evidence. `annotation_readability_checked` records final-width font/statistic inspection for recipe submissions; `manuscript_rendered_qa` accepts the relevant Word/LaTeX page QA, with `word_rendered_qa` retained as the legacy fallback. Declare the complete benchmark `comparator_set` at top level and each regression figure roster for omission checks; the validator does not inspect pixels.

## Multi-panel physical geometry

Preserve common axis limits, scale, sampling protocol, normalization, panel size and labeling logic when panels are intended for comparison. A display subsample changes marks only; reported metrics come from the frozen full evaluation population. Maintain one data-to-mark mapping and disclose any smoothing or logarithmic transform.

When the requested output is individual subfigure EMFs, export each panel independently and reinsert it into its original slot only if document modification is requested. A combined large image does not satisfy separate editable/vector-panel delivery. Enlarge labels, legend and annotations in the source generator for the intended physical width, then inspect them after Office insertion. Do not enlarge the entire bitmap or stretch width and height independently. Preserve the post-crop aspect ratio; uniform resizing only when allowed and required by the slot.

Crop empty margins after all labels and legends are laid out. Protect the full top/bottom/side frame, ticks, axis labels, numerical annotations and legends. Crop distances from one revision are local instructions, never default global values. Cropping changes physical scale if the result is automatically fitted to the old slot; inspect actual width/height and comparable panel scales. A legend requested at top-center inside the axes should sit near the frame with enough safe padding for text ascenders, and must not cover the plotted data or numbers. Reposition the legend or allocate headroom without changing evidence or silently changing comparative axes.

There is no universal 18/24/30 pt figure rule: authoring point size and final displayed point size differ after insertion. Check readability, consistent hierarchy, full frame and non-occlusion at the actual insertion dimensions. Use the accepted panel family as a visual reference; fix the four requested figures without rebuilding the paper or rerunning experiments. For standalone EMF delivery without a manuscript insertion request, a temporary Office rendering at the intended or declared size is sufficient QA; do not modify the manuscript just to create that check.

The current customer template and accepted panels govern report typography; inspect final physical size.

Measure the exported vector's intrinsic dimensions rather than inferring them from a filename or canvas option. Windows EMF device-DPI metadata can change its native frame size while preserving proportions. Insert it at the declared final dimensions with aspect ratio locked, then measure the actual Word/PDF text; the MATLAB authoring point size and intrinsic EMF point size can differ. Never apply a second arbitrary enlargement based only on a screen preview. For a cropped panel, compute the scale from the post-crop vector bounds and inspect the full frame and legend again.

## Verified production references

[Nature's figure specifications](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/) support labeled units, accessible colors, legible editable text and avoiding decorative objects or text over busy data. [Its panel export guide](https://research-figure-guide.nature.com/figures/building-and-exporting-figure-panels/) ties arrangement and font checks to final physical size. These are production principles; the current customer template governs the report's fonts and dimensions.

[MathWorks exportgraphics documentation](https://www.mathworks.com/help/matlab/ref/exportgraphics.html) documents vector content, version-specific export features and aspect-ratio behavior. [MATLAB R2025a release notes](https://www.mathworks.com/help/pdf_doc/matlab/rn.pdf) state that `Renderer` no longer controls `print`/`saveas` output. Check the installed release; use an available vector export route and inspect the produced artifact rather than treating `Painters` or an `.emf` suffix as proof. Request only needed formats, preserve physical geometry, and verify Office insertion for Word delivery.

Project图件采用 [信息量与图型规则](project-figure-policy.md)，取消简单柱线和稀疏散点默认输出。曲线和可加色块可以作为真实工程诊断中的信息层，装饰和重复子图不构成信息增量。
