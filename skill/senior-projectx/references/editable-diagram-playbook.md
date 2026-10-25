# Editable Scientific Diagrams

Use for introduction mechanisms, method principles, workflows, infrastructure scenes and local diagram repair. Read the relevant introduction and method before drawing. Apply the user's current choices of software, references, icons, text, colors and frozen geometry. Result figures remain governed by `figure-and-delivery.md` and `advanced-figure-workflow.md`.

## Establish the visual explanation

Identify the scientific relation and the reader's question before choosing a layout:

| Purpose | What the figure should make visible |
|---|---|
| Introduction mechanism | A concrete disturbance or behavior, its propagation through the actual system, the resulting operating difficulty and the research motivation |
| Method principle | The scientific objects and relations on which the method operates, including a meaningful local mechanism when needed |
| Workflow | Actual inputs, transformations, decision branches and outputs; iteration or feedback only when it exists in the method |
| Local repair | The diagnosed geometry or readability defect, with accepted content and objects preserved |

An introduction mechanism motivates the research; it is not empirical proof of novelty or performance. A workflow should explain operations rather than present a row of module names. Do not force prediction stages into a non-prediction paper or transfer another paper's acronym, topology, equations or conclusions.

When references are supplied, open or parse the actual files and inspect their rendered appearance. A filename or thumbnail is insufficient for a VSDX/PPTX reference. Learn layout, symbol grammar and visual hierarchy; extract suitable independent icons only when authorized. Do not insert the complete reference as the finished figure or copy its network structure without a scientific reason.

Use the current user-edited source as the authority. An export or insertion request does not authorize rebuilding it from an older script. Identify the manuscript and figure versions from the current task and files; resolve a materially ambiguous source before writing.

## Compose the system before decorating it

Use a dominant system, physical scene or computational object to organize the figure. Arrange devices, states and events around its meaningful connections. Decide major positions, shared ports and connector lanes before placing small labels and icons.

- Build complexity from verified dependencies, control levels, state changes, repeated events and alternative feasible paths. Do not add components, fake curves, repeated icons or text to make a simple mechanism look complicated.
- Keep related mechanisms adjacent. Attach an inset or temporal history to its corresponding device, conductor, state or event; avoid several detached miniatures and long empty arrows.
- For a repeated disturbance during recovery, show the relevant sequence on the same local scene when scientifically supported. A temporal leader must originate at the actual represented object, not float below a colored band. Avoid making the time axis look like an additional physical circuit.
- Remove duplicated buses, unnecessary return routes, repeated headings and unused margins only when connectivity and interpretation remain unchanged.
- Choose panel divisions and orientation from information structure. Do not force a/b panels for a compact mechanism that reads better as one horizontal figure. Conversely, preserve separate panels when settings or evidence roles require them.
- When the layout is fundamentally sparse or tangled, rebuild the affected arrangement. Replacing icons or changing colors alone does not repair the architecture.

Freeze accepted parts before a local revision using existing task notes or object IDs. Typical frozen items are label strings, icon files and transforms, approved line geometry/weights, data, formulas and accepted branches. Carry these constraints across turns. Do not regenerate frozen icons or change approved red strokes during a blue-line cleanup.

## Align repeated modules and explain every key

Use explicit column centers, row baselines, shared header/footer positions and routing lanes for repeated modules. Equal-role stages should have balanced widths, internal margins and spacing; a scientifically longer stage need not contain the same number of objects. Preserve its actual content instead of adding filler to force symmetry. Extend the canvas in the reading direction when a compact layout needs more routing room, rather than squeezing arrows and labels.

For an icon grid, align the visible icon centers and label baselines, not just the picture frames. Transparent margins and long method names can make equal frame coordinates look uneven. Center a shorter row within the same grid, wrap or space long labels consistently, and inspect the complete group at final size. A four-plus-three family grid is one local example, not a required arrangement for another method.

Inspect every small motif as a complete drawing: axes, sample points, search trees, density curves, switches and terminal marks. Include stroke widths and arrowheads in the visible bounds. A missing lower-left branch or half symbol must be repaired in its source geometry or clipping region; shrinking the whole figure or covering the defect does not restore the missing object.

Every legend item must correspond to a visible encoding with the same meaning. Apply the declared styles to the relevant objects, or remove an unused legend entry when authorized; do not add an unsupported mechanism to make the key appear used. Every numbered callout must identify one unambiguous object, region or effect. Use a nearby anchor, bracket or short leader when position alone is ambiguous, and keep its number consistent with the caption/body reference. Check legend-to-object and number-to-region correspondence in both directions.

## Preserve native editability

Use the requested native editor. For VSDX, use native text, connectors, lines, buses, switch symbols, curves, marks and meaningful subsystem groups. Connect intended junctions through shared ports or endpoint glue where supported. A continuous editable curve is preferable to many overlapping short strokes when they encode one path.

Scene assets may be separate transparent pictures. Use native engineering symbols for simple electrical objects and small coordinated image assets for buildings, vehicles or attack/damage objects when those improve recognition. Keep icons subordinate to the mechanism; do not spend the figure's visual budget on oversized illustrations. Match viewpoint and visual detail rather than mixing unrelated illustration styles.

Picture transparency must be genuine Alpha. White rectangles, checkerboards, colored backplates and cutout fringes are defects. Set image carriers to no fill and no border. Connect a line to the intended visible port or opaque edge, accounting for transparent margins; do not connect to the outer image frame and leave a visible gap. Preserve frozen asset pixels and transforms.

A flat image wrapped in SVG/PDF, imported as one VSDX object, or split into arbitrary raster tiles is not a native editable diagram. State accurately which elements are native and which are independently movable pictures. When native MathType is requested, provide genuine editable MathType objects in a supported source or companion Word/figure source and verify placement after export. Vector glyphs and equation screenshots do not establish MathType editability. Follow the declared equation backend rather than imposing MathType on every diagram.

When the requested source supports embedded MathType, keep the actual native objects there; a separate formula-source document does not establish formula editability inside that diagram. An EMF insertion remains an exported picture, so identify the native source used for later formula editing. If verified native objects are reused, preserve their mathematical meaning, native payload and matching preview, and record reuse accurately rather than claiming an independent conversion. A backend limitation or blocked conversion must remain visible in the delivery record.

## Route connections deliberately

Give physical connectivity, information/control, recovery and hostile/failure effects distinct semantics and a matching legend. For power-system scenes, black conductors with restrained blue information/control, green recovery/availability and red damage/blocked effects are a useful starting grammar. This is a domain example, not a mandatory palette for all papers or statistical plots. Current user choices and the retained figure family govern.

At approximately 17 cm final width, useful starting stroke weights are:

| Role | Final-size starting range |
|---|---|
| Main power flow or dominant causal direction | 1.1–1.3 pt |
| Secondary physical branch | 0.7–0.9 pt |
| Short workflow connection | 0.8–1.0 pt |
| Axis or auxiliary leader | 0.35–0.5 pt |

Adapt these to the figure and actual insertion scale. Use a compact arrowhead with enough visible shaft; a large triangle with a tiny tail is a layout defect. Start and end at the intended ports, with any deliberate separation scientifically meaningful and visually consistent.

Distinguish source-editor points from final printed points. Under uniform scaling, `final stroke = source stroke × inserted width / exported drawing width`, with widths in the same units; fonts and arrowheads need the same final-size check. A user request such as approximately 3 pt governs that task and its stated editor/scale, not every later diagram. Keep one connection's shaft and head stem visually consistent while preserving intentional hierarchy between major and auxiliary routes. Fix an over-wide head independently of its shaft when the shaft is already correct.

- Prefer one native polyline/connector per continuous route. Put an arrowhead only at its actual directed endpoint, with a sufficient straight terminal segment; an elbow is not a second termination. Reserve clearance for the full head before the target and inside export/group bounds.
- For joined pieces, match centerlines, endpoint coordinates and effective stroke widths. Join at one shared point and remove duplicated arrow segments or overshoots; a tiny remaining tail is still a defect. Inspect both orthogonal turns and diagonal joins after scaling.
- Align branch stems, switch contacts, arrow tips and shared buses on explicit coordinates. Remove redundant collinear segments, duplicate corner dots, small returns and overshooting tails.
- A junction dot means a connection. A nonjoining crossing needs a consistent bridge or break. Preserve a genuine open switch or failed-link gap; never leave an underlying conductor that silently closes it.
- Use a consistent shallow bridge with tangent joins. If a narrow background underlay separates crossing layers, keep it behind every visible signal stroke; do not use white patches to conceal bad geometry.
- Prefer continuous native crossover-to-port paths when separate collars, tiny dashed pieces and arrow segments create fragile joints. Keep intended signal/physical separation and terminal identity.
- Use tight, readable dashes for information flow at print size. Dash codes differ across software; Visio LinePattern 9 is one verified short-dash option, not a cross-application standard. Compare the rendered spacing. Very short arrow tips usually need a clear solid segment.
- Reduce crossings by reserving lanes and aligning ports before increasing line widths. Extra colors and heavier strokes cannot resolve an ambiguous connection.

## Labels, density and caption

Use short labels and consistent gaps for the same object role. Position labels outside connector lanes and image ink. For a dense English mechanism near 17 cm, 7.5–9 pt Times New Roman labels are a useful starting point when consistent with the manuscript. Result-plot labels and Chinese Project typography retain their own profiles. Scale from the actual exported bounds and verify final-size readability.

Keep formulas to those needed for the explanation. Avoid sentences inside every device, repeated headings and a bottom explanatory table that merely restates the main scene. Put a concise scientific caption below the figure and explain the mechanism naturally in the adjacent body text. Conceptual topology or event histories must be identified accurately; do not add fictitious precise times, equipment parameters or measured benefits.

## Targeted repair and acceptance

Translate feedback into object-level corrections:

| Feedback | Correct the underlying cause |
|---|---|
| Empty or scattered | Close unused margins and long route gaps; bring dependent objects and their events together |
| Too simple | Recover missing verified mechanisms or state relations; do not manufacture complexity |
| Busy or tangled | Reassign lanes, align ports and remove redundant routes while preserving real dependencies |
| Icons dominate | Reduce or reposition assets only if allowed; strengthen the native connection hierarchy |
| Tails or misaligned joins | Check endpoint coordinates, arrow termination, curve tangents, shared junctions and stroke order |
| Arrowhead clipped at a bend or frame | Restore a straight terminal segment and full painted bounds; adjust the head separately before changing all line weights |
| Repeated blocks look uneven | Align visible centers, label baselines, margins and shared routing anchors; check transparent picture padding |
| A legend item or number has no clear target | Repair the actual encoding or callout anchor and its caption mapping |
| Bottom sequence feels detached | Attach its leaders directly to the represented objects and align event/label axes |

Save the native source and export from that saved revision. Inspect the full figure, the final physical size and dense local regions: switch/actuator contacts, vehicle-adjacent ports, crossovers, arrow tips, temporal leaders and service branches when present. Check text collisions, Alpha edges and label gaps as well as endpoint coordinates; structural checks cannot replace visual review.

When editability matters, reopen the saved source and test representative native text, a connector/curve endpoint and an independent icon in a disposable copy. Do not save probe changes over the deliverable. If verification used safe mode or native reopening was unavailable, record that actual scope. Keep one current delivery version and put backups/intermediates outside it. Stop when the requested defects and affected regressions are resolved.

For EMF export, Word insertion and renumbering, use `word-figure-integration.md`.
