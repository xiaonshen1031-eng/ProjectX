# Native Figure Export and Word Integration

Use for exporting an accepted figure, inserting/replacing manuscript figures, and synchronizing captions or cross-references. Preserve the current source, scientific content and equation backend. A conversion-only request does not authorize redesign, new experiments or a manuscript rewrite.

## Establish authoritative inputs

Read the current task, figure source and manuscript before writing. A user-edited VSDX can differ from the last generated spec even when its filename is unchanged. Export that saved file directly; do not regenerate it from an older generator. Prefer the latest accepted manuscript lineage, and ask only if materially different candidates cannot be resolved from context.

Source authority comes from the user's designated file and accepted editing history. An old manifest, thumbnail, ZIP or export is not a newer source merely because its timestamp is later. Recheck the saved source after user edits, and update only the source-to-export mapping actually consumed by insertion. Reuse an export only when it is still bound to that source revision.

Preserve originals and use a new manuscript copy unless overwriting was explicitly requested. Snapshot only the inputs and files actually at risk; use the existing figure/source mapping rather than starting a whole-tree audit. Record the old-to-new figure map when adding a figure. Replacing Figure 1 and inserting a new Figure 1 have different numbering consequences.

## Export a real vector artifact

For native Visio diagrams, export through Visio. An EMF file extension alone does not prove vector text and paths. Inspect the artifact or its Office rendering; independent raster icons may remain raster without flattening the complete figure.

- Export from the saved user revision, preferably read-only or from an exact working copy. Do not change the original canvas merely to crop an export.
- When an A4 page contains a smaller drawing, use tight drawing/selection bounds where supported. A native selection export can avoid a large empty page; verify that no relevant object, label, arrowhead or picture edge was omitted.
- Measure the EMF frame or SVG/PDF bounds, not the source page size or filename. Preserve post-crop aspect ratio. Set final width from the current manuscript text area and compute height from the measured ratio.
- Keep the requested font and inspect transparency, icon orientation, clipping and native text in the actual export. Do not rasterize all content or convert editable text to paths solely to make a vector claim.
- Deliver only formats with a requested editing, insertion, submission or QA use. A 600 dpi PNG is appropriate when requested; a vector PDF/EMF has no intrinsic raster dpi requirement. Do not upscale a small bitmap and label it a high-resolution vector result.

If native MathType overlays accompany a plotting/background layer, preserve their object payloads, relative positions and physical scale. A standalone flattened preview is not the editable source. State clearly what the exported EMF preserves and where later structural or formula editing occurs.

Compute the scale from the painted drawing bounds, including labels, line caps and arrowheads. Verify the full exported frame after cropping; a drawing-selection rectangle can omit the outside of a thick head. Aspect-preserving resizing changes the apparent fonts and strokes together, so do not infer final 3 pt lines or readable formulas from source-editor settings alone.

## Insert without altering unrelated content

Use the document's established caption style and declared equation backend. For a bounded insertion, preserve existing images, OLE relationships, native equations, bookmarks and formatting. Minimal OOXML changes or supported native Word operations are preferable to reconstructing the entire paper through a converter. Check the particular payloads and relationships at risk; do not reconvert all MathType objects for a figure edit.

1. Place the figure near its scientific discussion. Add a brief natural callout when needed; use the approved caption or a scope-matched scientific caption.
2. Set both width and aspect-derived height in the source document. A centered paragraph flag alone does not prove centering.
3. Clear inherited picture-paragraph indentation. In Word, `firstLine="0"` can leave inherited character-based indentation active: clear `firstLineChars`, and relevant left/right character indents, as well as point-based indents. Preserve body paragraph indentation.
4. Keep the figure with its caption. Ensure the next heading remains with its first paragraph and that floating formula overlays stay anchored to their figure. Avoid fixed paragraph heights that clip the illustration.
5. Preserve surrounding text, tables, equation numbers, reference numbering and experimental values except for specifically authorized edits.

Existing native media should remain intact. For a narrowly patched DOCX, compare only affected package parts and the existing OLE/media payloads needed to demonstrate preservation. A relationship/media inventory is useful when there is a concrete risk of lost formulas or unintended image substitution; it is not a universal checksum requirement.

## Renumber captions and references together

Determine whether captions and references are static text, `SEQ`/`REF` fields, bookmarks or a mixture. Keep native field relationships when present and update their displayed results through Word when needed.

For static text, form one old-to-new mapping and apply it once across complete paragraph text, preserving run formatting and embedded objects. Numbers can be split across runs. Handle `Figure`, `Fig.`, plural lists, ranges and subfigure suffixes such as `(b)`. Use simultaneous replacement or another collision-safe approach; repeated ascending string substitutions can increment a reference more than once.

Do not replace bare numbers or alter equation, table, section, citation, bus or scenario identifiers. Inspect relevant headers, footnotes, text boxes and tables for figure references instead of assuming all references are ordinary body paragraphs. Check caption order and each affected body reference against its intended figure after insertion. Update the figure/source mapping and use it for later edits.

## Render the actual final Word file

Export the final DOCX through Word or the verified document-rendering route and inspect the manuscript pages. For native OLE/EMF documents, use native Word when another renderer loses objects. If a packaged renderer fails, diagnose its log and use a truthful supported fallback; do not substitute a standalone figure preview for document QA.

Review the full final document once for a delivered manuscript, including pages affected by reflow. Check the inserted figure at final size and locally inspect fine labels, branch/arrow joins, Alpha edges, borders and every side of the crop. Confirm caption pairing, heading placement and all changed numbers. A valid DOCX ZIP or native-object count does not prove visible layout.

Keep the QA input as an exact disposable copy so a background Word process cannot lock the deliverable during a correction. Confirm the tested copy corresponds to the current delivery. Wait for export and close to finish before replacing files. After an authoring failure, stop dependent stages rather than validating a stale successful output.

For Windows automation, use a compatible Office COM runtime; Windows PowerShell 5.1 with STA is useful where PowerShell 7 lacks the required interop API. An interop failure is not evidence that no application is running. Run background helpers hidden. Close only owned documents and applications; identify a stalled automation process before terminating it, and never kill every Word/Visio process. Record safe-mode-only or incomplete native checks accurately.

Bound native export retries to changed failure causes. If a responsive Office instance stalls on late-bound argument marshalling, use a typed bridge supported by the installed Office interop assembly rather than launching more application instances or repeating the identical call. Keep failures separate from the successful export receipt. Renderer-specific black Alpha backgrounds or malformed EMF formula glyphs require checking the same media in native Office before changing accepted icons or formulas.

Retain one current DOCX and the requested figure exports in the delivery folder. Keep previews, logs, native test copies and prior versions in the work/backup area unless requested. Report the concrete insertion and numbering outcome, the final files and any material verification limitation.

Keep only consumed QA records and useful checkpoints; repeated full-document renders, duplicate upload ZIPs and unbounded diagnostic logs are not reusable figure sources. Identify regenerable previews separately from native editables, result arrays and provenance before any authorized cleanup. A previous project's storage limit is not a default for later work.
