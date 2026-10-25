#!/usr/bin/env python3
"""Chinese figure and editable Word-report builder for the Senior-ProjectX."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from PIL import Image
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_font(candidates: Iterable[str]) -> tuple[str, str]:
    from matplotlib import font_manager
    available = {f.name.lower(): f.name for f in font_manager.fontManager.ttflist}
    for candidate in candidates:
        if candidate.lower() in available:
            return available[candidate.lower()], "requested"
    fallback = font_manager.FontProperties().get_name()
    return fallback, "fallback"


def font_contract() -> dict:
    chinese, status = resolve_font(["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"])
    latin, latin_status = resolve_font(["Times New Roman", "Liberation Serif", "DejaVu Serif"])
    return {"chinese": chinese, "chinese_status": status, "latin": latin, "latin_status": latin_status,
            "chinese_weight": "bold" if chinese != "SimHei" else "normal"}


def _style_figure_text(label, fonts: dict, size: float) -> None:
    has_chinese = bool(re.search(r"[\u3400-\u9fff]", label.get_text()))
    # Latin-first glyph fallback preserves TNR digits in mixed CJK/unit labels.
    label.set_fontfamily([fonts["latin"], fonts["chinese"]] if has_chinese else [fonts["latin"]])
    label.set_fontweight(fonts.get("chinese_weight", "bold") if has_chinese else "normal")
    label.set_fontsize(size)


def _mixed_axis(ax, fonts: dict, *, label_size: float = 10, tick_size: float = 9) -> None:
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        _style_figure_text(label, fonts, tick_size)
    for label in [ax.xaxis.label, ax.yaxis.label, ax.xaxis.get_offset_text(), ax.yaxis.get_offset_text()]:
        _style_figure_text(label, fonts, label_size if label in [ax.xaxis.label, ax.yaxis.label] else tick_size)
    ax.grid(True, axis="y", color="#D9D9D9", linewidth=0.6, alpha=0.75)
    ax.spines[["top", "right"]].set_visible(False)


def build_figures(periods_path: Path, allocation_path: Path, vehicles_path: Path,
                  sensitivity_path: Path, output_dir: Path) -> dict:
    """Render sourced constraint, response-window and scenario diagnostics."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    periods = pd.read_csv(periods_path)
    allocation = pd.read_csv(allocation_path)
    vehicles = pd.read_csv(vehicles_path)
    sensitivity = pd.read_csv(sensitivity_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    fonts = font_contract()
    plt.rcParams.update({"font.size": 9, "axes.unicode_minus": False, "pdf.fonttype": 42, "ps.fonttype": 42})
    artifacts = []
    ids = periods.period.to_numpy()
    x = np.arange(len(ids))
    base = periods.base_load_kw.to_numpy()
    capacity = periods.capacity_kw.to_numpy()
    total = allocation.groupby("period").charge_kw.sum().reindex(ids, fill_value=0).to_numpy()
    duration = periods.duration_h.to_numpy()
    uniform = np.zeros(len(ids))
    for v in vehicles.itertuples():
        mask = (ids >= v.arrival_period) & (ids < v.departure_period)
        uniform[mask] += v.energy_kwh / duration[mask].sum()
    margin = capacity-base-total

    def layer(role, encoding, source, definition):
        return {"role": role, "encoding": encoding, "evidence_source": str(source), "evidence_definition": definition}

    def save(fig, name, identity, role, question, caption, sources, layers, kind):
        for ax in fig.axes:
            _mixed_axis(ax, fonts)
            if ax.images or ax.patches: ax.grid(False)
            for label in ax.texts: _style_figure_text(label, fonts, label.get_fontsize())
            if ax.get_legend():
                for label in ax.get_legend().get_texts(): _style_figure_text(label, fonts, 8)
        path = output_dir / name
        fig.savefig(path, dpi=320, bbox_inches="tight", pad_inches=0.04)
        plt.close(fig)
        sources = list(dict.fromkeys(map(str, sources)))
        artifacts.append({"id": identity, "path": str(path), "role": role, "question": question,
                          "width_cm": 15.6, "caption": caption, "plot_type": kind, "source": sources,
                          "source_sha256": {s: file_hash(Path(s)) for s in sources}, "plot_layers": layers})

    fig, (ax, residual) = plt.subplots(2, 1, figsize=(6.55, 4.05), sharex=True,
                                    gridspec_kw={"height_ratios": [2.2, 1]}, constrained_layout=True)
    ax.step(x, base, where="mid", color="#2477A6", label="基础负荷")
    ax.step(x, base+total, where="mid", color="#D9802F", linewidth=1.6, label="分配后负荷")
    ax.step(x, base+uniform, where="mid", color="#9772A8", linestyle=":", label="均分参考")
    ax.step(x, capacity, where="mid", color="#333333", linestyle="--", label="容量边界")
    ax.fill_between(x, base+total, capacity, step="mid", color="#76B7B2", alpha=.19)
    ax.set_ylabel("功率（kW）")
    ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.01), ncol=4, frameon=False)
    residual.fill_between(x, 0, margin, step="mid", color="#1D8C82", alpha=.4)
    residual.step(x, margin, where="mid", color="#1D8C82")
    residual.step(x, capacity-base-uniform, where="mid", color="#9772A8", linestyle=":")
    residual.axhline(0, color="#333333", linewidth=.7)
    residual.set_ylabel("余量（kW）"); residual.set_xlabel("时段")
    residual.set_xticks(x, ids)
    save(fig, "figure_constraint_diagnostic.png", "figure_process", "过程与约束",
         "时间分配如何改变各时段容量占用和剩余容量？", "图1 充电时序、容量边界与逐时段余量",
         [periods_path, allocation_path, vehicles_path],
         [layer("observed_time_series", "line", periods_path, "基础负荷、容量和逐车辆均分参考使用原始时段与窗口"),
          layer("constraint_margin", "step_area", allocation_path, "余量等于容量减基础负荷再减实际分配功率，保留全部时段")],
         "temporal_diagnostic")

    fig, ax = plt.subplots(figsize=(6.55, 3.45), constrained_layout=True)
    cmap = plt.get_cmap("YlOrBr")
    upper = float(vehicles.max_charge_kw.max())
    for row, v in enumerate(vehicles.itertuples()):
        mask = (ids >= v.arrival_period) & (ids < v.departure_period)
        for j in np.flatnonzero(mask):
            ax.add_patch(Rectangle((j-.46, row-.33), .92, .66, facecolor="#EEEEEE", edgecolor="white"))
        values = allocation[allocation.vehicle_id == v.vehicle_id].set_index("period").charge_kw.reindex(ids, fill_value=0).to_numpy()
        for j in np.flatnonzero(values > 1e-9):
            value = values[j]
            ax.add_patch(Rectangle((j-.46, row-.33), .92, .66, facecolor=cmap(.22+.7*value/upper), edgecolor="white"))
            ax.text(j, row, f"{value:.1f}", ha="center", va="center", fontsize=8,
                    color="white" if value/upper > .75 else "#111111")
        delivered = float(np.dot(values, duration))
        ax.text(len(ids)-.15, row, f"{delivered:.1f}/{v.energy_kwh:.1f}", va="center", fontsize=8)
    ax.text(len(ids)-.15, -.75, "交付/需求（kWh）", fontsize=8, va="center")
    ax.set_xlim(-.65, len(ids)+1.65); ax.set_ylim(len(vehicles)-.4, -1.03)
    ax.set_xticks(x, ids); ax.set_yticks(np.arange(len(vehicles)), vehicles.vehicle_id)
    ax.set_xlabel("时段"); ax.set_ylabel("车辆")
    ax.plot([], [], color="#DDDDDD", linewidth=7, label="可用窗口")
    ax.plot([], [], color=cmap(.65), linewidth=7, label="实际功率（格内 kW）")
    ax.legend(loc="upper center", bbox_to_anchor=(.43, 1.13), ncol=2, frameon=False)
    save(fig, "figure_window_allocation.png", "figure_balance", "对象守恒与时间窗",
         "各对象如何在自身窗口和功率边界内满足需求电量？", "图2 车辆接入窗口、功率分配与电量满足关系",
         [periods_path, allocation_path, vehicles_path],
         [layer("coverage", "gantt", vehicles_path, "灰色格表示车辆可用接入窗口；窗口外不安排充电"),
          layer("conditional_response", "annotated_tiles", allocation_path, "着色格及数值给出真实功率，右列比较累计交付与需求电量")],
         "response_diagnostic")

    # Full scenario traces are required; summary means cannot recover time structure.
    feasible = sensitivity[sensitivity.status == "optimal"]
    if feasible.empty: raise ValueError("No feasible scenario traces available for a scenario atlas")
    margins, scenario_sources = [], []
    for row in feasible.itertuples():
        path = sensitivity_path.parent / "scenarios" / f"allocation_{row.demand_scale:.2f}.csv"
        if not path.is_file(): raise FileNotFoundError("Scenario atlas requires saved allocation: " + str(path))
        table = pd.read_csv(path)
        charge = table.groupby("period").charge_kw.sum().reindex(ids, fill_value=0).to_numpy()
        margins.append(capacity-base-charge); scenario_sources.append(path)
    margins = np.asarray(margins)
    fig, (ax, summary) = plt.subplots(1, 2, figsize=(6.55, 3.8), gridspec_kw={"width_ratios": [3.9, 1.55]}, constrained_layout=True)
    mesh = ax.imshow(margins, cmap="YlGnBu", aspect="auto", vmin=0)
    for i in range(len(feasible)):
        for j in range(len(ids)):
            value = 0.0 if abs(margins[i,j]) < 1e-9 else margins[i,j]
            ax.text(j, i, f"{value:.0f}", ha="center", va="center", fontsize=8,
                    color="white" if margins[i,j] > margins.max()*.62 else "#111111")
    ax.set_xticks(x, ids); ax.set_yticks(np.arange(len(feasible)), [f"{v:.2f}" for v in feasible.demand_scale])
    ax.set_xlabel("时段"); ax.set_ylabel("需求倍率")
    cb = fig.colorbar(mesh, ax=ax, orientation="horizontal", pad=.18, fraction=.08, aspect=25)
    cb.set_label("容量余量（kW）")
    summary.set_xlim(0, 1); summary.set_ylim(len(feasible)-.5, -1)
    summary.text(.05, -.85, "目标值", fontsize=9)
    summary.text(.61, -.85, "平均余量", fontsize=9)
    for i, row in enumerate(feasible.itertuples()):
        summary.text(.05, i, f"{row.objective:.2f}", fontsize=8.5, va="center")
        summary.text(.70, i, f"{row.mean_margin_kw:.2f}", fontsize=8.5, va="center")
    summary.text(.70, len(feasible)-.3, "kW", fontsize=8)
    summary.set_axis_off()
    save(fig, "figure_scenario_constraint_atlas.png", "figure_sensitivity", "情景与容量压力",
         "需求增长将容量压力转移到哪些时段，成本与平均余量如何同步改变？", "图3 需求增长下的逐时段容量余量与调度指标",
         [periods_path, sensitivity_path, *scenario_sources],
         [layer("constraint_margin", "conditional_matrix", scenario_sources[0], "逐情景读取实际分配序列，逐时段计算容量余量；每一情景源文件均列于source"),
          layer("conditional_response", "aligned_numeric_profile", sensitivity_path, "按同一情景行对齐目标值与平均余量，不插值、不作概率区间")],
         "composite_diagnostic")

    for item in artifacts:
        item["sha256"] = file_hash(Path(item["path"]))
        with Image.open(item["path"]) as rendered:
            item["pixel_size"] = [rendered.width, rendered.height]
            item["aspect_ratio"] = round(rendered.width / rendered.height, 6)
        item["font_contract"] = fonts
        item["final_size_typography"] = {"axis_label_pt": 10, "tick_pt": 9, "legend_pt": 8.5}
    return {"schema": "senior_projectx.project.figure_manifest.v1", "language": "chinese",
            "no_default_suptitle": True, "artifacts": artifacts, "font_contract": fonts}


def _set_cell_margin(cell, top=80, start=90, bottom=80, end=90):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar"); tc_pr.append(tc_mar)
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}"); tc_mar.append(node)
        node.set(qn("w:w"), str(value)); node.set(qn("w:type"), "dxa")


def _set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    element = OxmlElement("w:tblHeader"); element.set(qn("w:val"), "true"); tr_pr.append(element)


def _set_run_font(run, chinese="SimSun", latin="Times New Roman", size=12, bold=False):
    run.font.name = latin; run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = RGBColor(0, 0, 0)
    fonts = run._element.get_or_add_rPr().rFonts
    for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        fonts.attrib.pop(qn(f"w:{attr}"), None)
    fonts.set(qn("w:eastAsia"), chinese)


def _paragraph_role(paragraph, role: str) -> None:
    """Apply the explicit default-profile role; prose prefixes never infer captions."""
    if role not in {"body", "heading", "caption", "table", "display", "figure", "reference"}:
        raise ValueError(f"Unknown Project paragraph role: {role}")
    pf = paragraph.paragraph_format
    pf.widow_control = True
    pf.left_indent = Pt(0); pf.right_indent = Pt(0)
    pf.first_line_indent = Pt(24 if role == "body" else 0)
    ind = paragraph._element.get_or_add_pPr().get_or_add_ind()
    for attr in ("hanging", "hangingChars", "leftChars", "rightChars"):
        ind.attrib.pop(qn(f"w:{attr}"), None)
    ind.set(qn("w:firstLineChars"), "200" if role == "body" else "0")
    pf.line_spacing = 1.0 if role in {"table", "caption", "display", "figure"} else 1.5
    pf.space_before = Pt(0); pf.space_after = Pt(0)
    pf.alignment = (WD_ALIGN_PARAGRAPH.JUSTIFY if role == "body" else
                    WD_ALIGN_PARAGRAPH.CENTER if role in {"caption", "display", "figure", "table"} else
                    WD_ALIGN_PARAGRAPH.LEFT)
    if role in {"display", "caption", "figure", "table"}:
        pf.tab_stops.clear_all()


def _configure_styles(doc: Document) -> None:
    normal = doc.styles["Normal"]
    _set_run_font(normal)
    _paragraph_role(normal, "body")
    for name, size in (("Title", 22), ("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 12)):
        style = doc.styles[name]
        _set_run_font(style, size=size)
        _paragraph_role(style, "heading")
        style.paragraph_format.space_before = Pt(12 if name != "Title" else 0)
        style.paragraph_format.space_after = Pt(6)
        ppr = style._element.get_or_add_pPr()
        border = ppr.find(qn("w:pBdr"))
        if border is not None: ppr.remove(border)
    subtitle = doc.styles["Subtitle"]
    _set_run_font(subtitle, size=14); subtitle.font.italic = False
    _paragraph_role(subtitle, "heading")
    subtitle_ppr = subtitle._element.get_or_add_pPr()
    subtitle_border = subtitle_ppr.find(qn("w:pBdr"))
    if subtitle_border is not None: subtitle_ppr.remove(subtitle_border)
    _set_run_font(doc.styles["Caption"], size=10.5)
    _paragraph_role(doc.styles["Caption"], "caption")


def _configure_page(doc: Document) -> None:
    for section in doc.sections:
        section.page_width = Cm(21.0); section.page_height = Cm(29.7)
        section.top_margin = Cm(2.5); section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.8); section.right_margin = Cm(2.6)


def create_default_template(path: Path) -> None:
    doc = Document(); _configure_styles(doc); _configure_page(doc)
    p = doc.add_paragraph("项目技术研究报告", style="Title"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("按任务书、技术问题与当前证据调整章节", style="Subtitle"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()
    for heading in ["项目概述与研究任务", "研究对象、资料与数据", "研究专题", "综合技术评价与工程建议", "结论及后续工作"]:
        doc.add_heading(heading, level=1)
        doc.add_paragraph("[按当前项目材料填写]")
    doc.core_properties.author = ""; doc.core_properties.last_modified_by = ""
    path.parent.mkdir(parents=True, exist_ok=True); doc.save(path)


def _clean_template(doc: Document) -> None:
    body = doc._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def _append_text(paragraph, text: str, *, formulas: list[dict] | None = None,
                 context: str = "body", equation_backend: str = "mathtype_native", size: float = 12):
    """Explicit $TeX$ spans become inventoried inline math, never faux variables."""
    parts = re.split(r"(\$[^$\r\n]+\$)", text)
    if len(parts) > 1 and formulas is None:
        raise ValueError("Inline mathematics requires an ordered formula manifest")
    for part in parts:
        if not part:
            continue
        if part.startswith("$") and part.endswith("$") and len(part) > 2:
            tex = part[1:-1]
            if equation_backend == "office_math":
                paragraph._p.append(_tex_to_omml(tex, size=size))
            elif equation_backend in {"mathtype_native", "mathtype_toggle_tex"}:
                _set_run_font(paragraph.add_run(part), size=size)
            else:
                raise ValueError(f"Unsupported Project equation backend: {equation_backend}")
            formula_id = f"inline_{len(formulas) + 1:04d}"
            if any(f["formula_id"] == formula_id for f in formulas):
                raise ValueError(f"Duplicate formula ID: {formula_id}")
            formulas.append({"formula_id": formula_id, "tex": tex, "placement": "inline",
                             "context": context, "font_size_pt": size})
        else:
            _set_run_font(paragraph.add_run(part), size=size)


def _add_body(doc: Document, text: str, *, bold_lead: str | None = None,
              formulas: list[dict] | None = None, equation_backend: str = "mathtype_native"):
    p = doc.add_paragraph()
    _paragraph_role(p, "body")
    if bold_lead and text.startswith(bold_lead):
        r = p.add_run(bold_lead); _set_run_font(r, bold=True)
        text = text[len(bold_lead):]
    _append_text(p, text, formulas=formulas, equation_backend=equation_backend)
    return p


def _office_math_xslt() -> Path:
    configured = os.environ.get("OFFICE_MML2OMML_XSL")
    candidates = [
        Path(configured) if configured else None,
        Path(r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL"),
        Path(r"C:\Program Files (x86)\Microsoft Office\root\Office16\MML2OMML.XSL"),
        Path(r"C:\Program Files\Microsoft Office\Office16\MML2OMML.XSL"),
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise RuntimeError(
        "office_math requires Microsoft Office MML2OMML.XSL; set OFFICE_MML2OMML_XSL to its path"
    )


def _tex_to_omml(tex: str, *, size: float = 12):
    try:
        from latex2mathml.converter import convert
        from lxml import etree
    except ImportError as exc:
        raise RuntimeError("office_math requires the installed latex2mathml and lxml packages") from exc
    mathml = etree.fromstring(convert(tex).encode("utf-8"))
    transform = etree.XSLT(etree.parse(str(_office_math_xslt())))
    omml = transform(mathml).getroot()
    if omml is None or omml.tag != qn("m:oMath"):
        raise RuntimeError("Microsoft Office MathML transform did not produce one editable m:oMath object")
    for run in omml.xpath(".//m:r", namespaces={"m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}):
        word_properties = OxmlElement("w:rPr")
        fonts = OxmlElement("w:rFonts"); fonts.set(qn("w:ascii"), "Cambria Math"); fonts.set(qn("w:hAnsi"), "Cambria Math")
        font_size = OxmlElement("w:sz"); font_size.set(qn("w:val"), str(round(size * 2)))
        size_cs = OxmlElement("w:szCs"); size_cs.set(qn("w:val"), str(round(size * 2)))
        word_properties.extend([fonts, font_size, size_cs])
        first_text = next((i for i, child in enumerate(run) if child.tag == qn("m:t")), len(run))
        run.insert(first_text, word_properties)
    return omml


def _add_formula(doc: Document, tex: str, formula_id: str, formulas: list[dict], *,
                 context: str = "body", equation_backend: str = "mathtype_native"):
    if any(f["formula_id"] == formula_id for f in formulas):
        raise ValueError(f"Duplicate formula ID: {formula_id}")
    p = doc.add_paragraph(); _paragraph_role(p, "display")
    p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(6)
    if equation_backend == "office_math":
        p._p.append(_tex_to_omml(tex))
    elif equation_backend in {"mathtype_native", "mathtype_toggle_tex"}:
        literal = r"\[" + tex + r"\]"
        r = p.add_run(literal); _set_run_font(r, size=12)
    else:
        raise ValueError(f"Unsupported Project equation backend: {equation_backend}")
    formulas.append({"formula_id": formula_id, "tex": tex, "placement": "display", "context": context,
                     "font_size_pt": 12})
    return p


def _add_caption(doc: Document, text: str, *, formulas: list[dict] | None = None,
                 equation_backend: str = "mathtype_native"):
    p = doc.add_paragraph(style="Caption"); _paragraph_role(p, "caption")
    p.paragraph_format.keep_with_next = text.startswith("表")
    p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(6)
    _append_text(p, text, formulas=formulas, context="caption", equation_backend=equation_backend, size=10.5)
    return p


def _add_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[float] | None = None,
               *, formulas: list[dict] | None = None, equation_backend: str = "mathtype_native"):
    if not headers or any(len(row) != len(headers) for row in rows):
        raise ValueError("Table rows must match the nonempty header")
    if widths and (len(widths) != len(headers) or any(w <= 0 for w in widths)):
        raise ValueError("Table widths must be positive and match the header")
    table = doc.add_table(rows=1, cols=len(headers)); table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Normal Table"; table.autofit = False
    section = doc.sections[-1]
    available = (section.page_width - section.left_margin - section.right_margin) / Cm(1)
    widths = widths or [available / len(headers)] * len(headers)
    scale = min(1.0, available / sum(widths))
    widths = [w * scale for w in widths]
    for column, width in zip(table.columns, widths): column.width = Cm(width)
    properties = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom", "left", "right", "insideH", "insideV"):
        node = OxmlElement(f"w:{edge}")
        node.set(qn("w:val"), "single" if edge in {"top", "bottom"} else "nil")
        node.set(qn("w:color"), "000000"); node.set(qn("w:sz"), "12")
        borders.append(node)
    properties.append(borders)
    look = properties.find(qn("w:tblLook"))
    if look is not None: properties.remove(look)
    _set_repeat_header(table.rows[0])
    for row_index, row in enumerate([headers, *rows]):
        cells = table.rows[0].cells if row_index == 0 else table.add_row().cells
        for i, value in enumerate(row):
            cell = cells[i]; cell.text = ""; cell.width = Cm(widths[i])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER; _set_cell_margin(cell)
            p = cell.paragraphs[0]; p.clear(); _paragraph_role(p, "table")
            _append_text(p, str(value), formulas=formulas, context="table",
                         equation_backend=equation_backend, size=10.5)
            tcpr = cell._tc.get_or_add_tcPr()
            shading = OxmlElement("w:shd"); shading.set(qn("w:val"), "clear")
            shading.set(qn("w:fill"), "auto"); tcpr.append(shading)
            if row_index == 0:
                cb = OxmlElement("w:tcBorders"); bottom = OxmlElement("w:bottom")
                bottom.set(qn("w:val"), "single"); bottom.set(qn("w:color"), "000000")
                bottom.set(qn("w:sz"), "6"); cb.append(bottom); tcpr.append(cb)
    return table


def build_report(template_path: Path, manifest_path: Path, audit_paths: list[Path], result_path: Path,
                 validation_path: Path, brief_path: Path, figure_manifest_path: Path,
                 sensitivity_path: Path, output_path: Path, formula_manifest_path: Path) -> dict:
    manifest, result, validation, brief = map(read_json, [manifest_path, result_path, validation_path, brief_path])
    equation_backend = manifest.get("equation_backend", "mathtype_native")
    if equation_backend not in {"mathtype_native", "mathtype_toggle_tex", "office_math"}:
        raise ValueError(f"Unsupported Project equation backend: {equation_backend}")
    figure_manifest = read_json(figure_manifest_path)
    audits = [read_json(path) for path in audit_paths]
    if result.get("status") != "optimal" or validation.get("status") != "pass" or any(a.get("status") != "pass" for a in audits):
        raise ValueError("Allocation example requires a verified feasible result; retain adverse cases in a task-specific report")
    sensitivity = pd.read_csv(sensitivity_path)
    doc = Document(template_path); _configure_styles(doc); _configure_page(doc); _clean_template(doc)
    formulas: list[dict] = []
    title = manifest.get("paper_title", "项目技术研究报告")
    p = doc.add_paragraph(title, style="Title"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("技术研究样章", style="Subtitle"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("研究对象：多时段充电资源连续分配")
    _paragraph_role(p, "caption"); p.paragraph_format.space_before = Pt(60)
    doc.add_page_break()

    doc.add_heading("摘要", level=1)
    minimum_margin = float(validation["minimum_capacity_margin_kw"])
    _add_body(doc, f"变压器基础负荷占用的容量随时段变化，充电计划需要在剩余容量内满足车辆的离站电量需求。由设备容量与基础负荷计算可用功率，再将车辆接入窗口、需求电量和功率上限纳入连续线性规划，可形成逐车、逐时段的充电方案。所得方案的最小容量余量为 {minimum_margin:.2f} kW。需求倍率变化下的目标值和容量余量共同反映充电需求增长对调度成本及容量压力的影响。")
    _add_body(doc, "关键词：充电资源分配；连续线性规划；容量约束；敏感性分析")

    doc.add_heading("1 项目概述与研究任务", level=1)
    _add_body(doc, "该研究内容面向受变压器容量约束的充电计划制定。工程问题包含两个连续环节：首先由已知容量和基础负荷形成各时段可分配功率；随后在车辆到离时间窗内分配充电功率，使每辆车获得规定电量，并评价容量余量及需求变化带来的影响。")
    _add_body(doc, "分配方案给出各车辆的充电功率和对应时段，容量余量则描述执行该方案后仍可承接的负荷。两类结果分别用于制定充电计划和识别紧张时段；需求倍率的变化用于分析既定容量与接入窗口下的承载能力。")
    doc.add_page_break()

    doc.add_heading("2 研究对象、资料与数据", level=1)
    _add_body(doc, "本例采用合成的时段负荷与车辆需求数据。时段数据包含基础负荷、变压器容量和时长，车辆数据包含车辆标识、到离时间、需求电量和最大充电功率。两类数据通过接入窗口关联，形成各车辆在各时段的可分配范围。")
    rows = []
    for audit in audits:
        is_period = "base_load_kw" in audit["profiles"]
        rows.append(["时段数据" if is_period else "车辆数据", str(audit["rows"]),
                     "基础负荷、容量（kW），时长（h）" if is_period else "需求电量（kWh），功率上限（kW），接入窗口"])
    _add_caption(doc, "表1 输入数据及单位")
    _add_table(doc, ["数据对象", "记录数", "主要变量及单位"], rows, [3.0, 2.0, 10.6])
    _add_body(doc, "充电功率按时段分配，并乘以对应时长累计为交付电量。容量约束作用于每个时段，电量约束作用于每辆车辆的完整接入窗口，因此时段长度和车辆到离时间共同决定分配方案的可行范围。")
    doc.add_page_break()

    doc.add_heading("3 数学模型与求解", level=1)
    _add_body(doc, r"模型以时段 $t$ 和车辆 $v$ 为索引。变压器容量 $C_t$ 与基础负荷 $L_t$ 的差值为可分配功率 $H_t$，车辆在该时段的充电功率记为 $x_{v,t}$。", formulas=formulas, equation_backend=equation_backend)
    _add_formula(doc, r"H_t=C_t-L_t", "headroom", formulas, equation_backend=equation_backend)
    _add_formula(doc, r"\min_{x}\ \sum_{v\in\mathcal{V}}\sum_{t\in\mathcal{T}} c_{v,t}x_{v,t}", "objective", formulas, equation_backend=equation_backend)
    _add_formula(doc, r"\sum_{t\in\mathcal{T}_v}\Delta t_t x_{v,t}=E_v,\quad \forall v\in\mathcal{V}", "energy", formulas, equation_backend=equation_backend)
    _add_formula(doc, r"\sum_{v\in\mathcal{V}}x_{v,t}\leq H_t,\quad \forall t\in\mathcal{T}", "capacity", formulas, equation_backend=equation_backend)
    _add_formula(doc, r"0\leq x_{v,t}\leq \overline{x}_v\,\mathbf{1}\{t\in\mathcal{T}_v\}", "bounds", formulas, equation_backend=equation_backend)
    _add_body(doc, r"车辆集合与时段集合分别记为 $\mathcal{V}$ 和 $\mathcal{T}$。车辆的接入窗口 $\mathcal{T}_v$ 限定充电时段，需求电量 $E_v$ 由各时段功率与时长 $\Delta t_t$ 的乘积累计得到，功率上界 $\overline{x}_v$ 则限定单车充电速率。功率、电量和时长的单位分别为 kW、kWh 和 h。目标系数 $c_{v,t}$ 由时段成本与时间偏好组成，各约束与目标均为线性关系，采用连续线性规划求解。", formulas=formulas, equation_backend=equation_backend)
    _add_body(doc, f"所得分配方案的目标值为 {result['objective']:.3f}。其逐时段负荷和逐车交付电量分别用于分析容量占用及需求满足情况。")
    doc.add_page_break()

    doc.add_heading("4 分配结果与容量约束", level=1)
    process = next(a for a in figure_manifest["artifacts"] if a["id"] == "figure_process")
    p = doc.add_paragraph(); _paragraph_role(p, "figure"); p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(process["path"], width=Cm(process["width_cm"]))
    _add_caption(doc, process["caption"])
    tight = int(np.argmin(np.asarray(result["capacity_margin_kw"])))
    _add_body(doc, f"图1中基础负荷占用的容量与充电功率共同决定时段余量。最紧约束出现在第 {tight} 时段，容量余量为 {result['capacity_margin_kw'][tight]:.2f} kW；所有时段的负荷与充电功率之和均未超过容量边界。充电时序受到车辆接入窗口、功率上限和时段成本共同约束，不能仅由基础负荷的高低决定。")
    balance = next(a for a in figure_manifest["artifacts"] if a["id"] == "figure_balance")
    p = doc.add_paragraph(); _paragraph_role(p, "figure"); p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(balance["path"], width=Cm(balance["width_cm"]))
    _add_caption(doc, balance["caption"])
    _add_body(doc, f"图2沿车辆接入窗口展开功率分配，各车辆的累计交付电量均满足需求，最大差值为 {validation['maximum_energy_residual_kwh']:.2e} kWh。时段功率与右侧累计电量共同反映时间窗内的需求满足关系。")
    doc.add_heading("5 工况变化与敏感性分析", level=1)
    sens = next(a for a in figure_manifest["artifacts"] if a["id"] == "figure_sensitivity")
    p = doc.add_paragraph(); _paragraph_role(p, "figure"); p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(sens["path"], width=Cm(sens["width_cm"]))
    _add_caption(doc, sens["caption"])
    sens_rows = [[f"{r.demand_scale:.2f}", {"optimal": "可行", "infeasible": "不可行"}.get(r.status, r.status), f"{r.objective:.3f}" if np.isfinite(r.objective) else "—",
                  f"{r.mean_margin_kw:.2f}" if np.isfinite(r.mean_margin_kw) else "—"] for r in sensitivity.itertuples()]
    _add_caption(doc, "表2 需求倍率敏感性结果")
    _add_table(doc, ["需求倍率", "状态", "目标值", "平均容量余量（kW）"], sens_rows, [3.0, 3.0, 4.0, 6.0])
    feasible = sensitivity[sensitivity.status == "optimal"]
    if len(feasible):
        lo, hi = feasible.iloc[0], feasible.iloc[-1]
        _add_body(doc, f"图3中的容量余量随需求增长逐步收缩，表2中的目标值同时上升。两端工况之间，平均余量减少 {lo.mean_margin_kw-hi.mean_margin_kw:.2f} kW，反映新增电量对既定设备容量的占用。逐时段余量进一步给出容量压力的分布，相同平均余量下仍需根据最紧时段确定可增加的负荷。")
    doc.add_page_break()

    doc.add_heading("6 需求满足与容量占用", level=1)
    checks = [["最大电量差值", f"{validation['maximum_energy_residual_kwh']:.2e}", "kWh"],
              ["最大容量越界量", f"{validation['maximum_capacity_violation_kw']:.2e}", "kW"],
              ["最小容量余量", f"{minimum_margin:.2f}", "kW"]]
    _add_caption(doc, "表3 电量与容量指标")
    _add_table(doc, ["指标", "数值", "单位"], checks, [8.0, 4.0, 3.6])
    _add_body(doc, "表3分别从电量和功率两个维度描述分配方案。电量差值由各车辆全部接入时段的充电量累计得到，容量越界量和最小容量余量则由各时段总负荷计算。前者反映需求满足程度，后两项反映设备容量占用情况。")
    _add_body(doc, "车辆电量差值与容量越界量均为零，说明接入窗口内的功率组合同时满足需求与设备边界。该功率组合保留了逐时段余量，运行时可据此判断新增负荷应安排的时段。")
    doc.add_heading("7 结论及工程建议", level=1)
    _add_body(doc, "设备容量扣除基础负荷后得到可分配功率，连续分配模型在车辆接入窗口内利用这一功率空间满足电量需求。所得逐时段余量反映方案实施后的剩余承载能力，可据此安排新增负荷。")
    _add_body(doc, "运行中应根据基础负荷变化更新逐时段可分配功率，并据此调整车辆充电时序。容量紧张时，可在车辆接入窗口允许的范围内将充电需求转移至余量较大的时段；若接入窗口内的可供电量仍不足以满足需求，则需要调整接入安排或配置额外容量。")
    doc.core_properties.author = ""; doc.core_properties.last_modified_by = ""
    output_path.parent.mkdir(parents=True, exist_ok=True); doc.save(output_path)
    is_office_math = equation_backend == "office_math"
    receipt = {
        "schema": "senior_projectx.project.equation_source.v1",
        "equation_backend": "office_math" if is_office_math else "mathtype_toggle_tex",
        "requested_final_backend": equation_backend,
        "status": "render_review_pending" if is_office_math else "conversion_pending", "publication_eligible": False,
        "source_docx_path": os.path.relpath(output_path, formula_manifest_path.parent).replace("\\", "/"),
        "source_docx_sha256": file_hash(output_path), "formula_count": len(formulas), "formulas": formulas,
        "note": (
            "This DOCX contains editable Office Math objects and requires Word render/page review before delivery."
            if is_office_math else
            "This source must be converted once through Word MathType and audited before it is called native MathType output."
        ),
    }
    write_json(formula_manifest_path, receipt)
    return {"status": "render_review_pending" if is_office_math else "conversion_pending",
            "equation_backend": receipt["equation_backend"], "docx": str(output_path),
            "formula_manifest": str(formula_manifest_path), "formula_count": len(formulas),
            "pages_are_not_self_certified": True}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build Chinese Project figures and a Word report from current result objects.")
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("make-template", help="Create the default editable A4 Project DOCX template.")
    q.add_argument("output", type=Path)
    q = sub.add_parser("figures", help="Create role-distinct Chinese figures from current allocation and sensitivity results.")
    q.add_argument("--periods", required=True, type=Path); q.add_argument("--allocation", required=True, type=Path)
    q.add_argument("--vehicles", required=True, type=Path); q.add_argument("--sensitivity", required=True, type=Path)
    q.add_argument("--output-dir", required=True, type=Path); q.add_argument("--manifest-out", required=True, type=Path)
    q = sub.add_parser("build", help="Build the manifest-selected Project equation backend; MathType creates a conversion-pending source, Office Math creates editable OMML.")
    q.add_argument("--template", required=True, type=Path); q.add_argument("--manifest", required=True, type=Path)
    q.add_argument("--audit", action="append", required=True, type=Path); q.add_argument("--result", required=True, type=Path)
    q.add_argument("--validation", required=True, type=Path); q.add_argument("--brief", required=True, type=Path)
    q.add_argument("--figures", required=True, type=Path); q.add_argument("--sensitivity", required=True, type=Path)
    q.add_argument("--output", required=True, type=Path); q.add_argument("--formula-manifest", required=True, type=Path)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "make-template":
        if args.output.exists(): raise FileExistsError(args.output)
        create_default_template(args.output.resolve()); result = {"status": "ok", "template": str(args.output.resolve())}
    elif args.command == "figures":
        result = build_figures(args.periods.resolve(), args.allocation.resolve(), args.vehicles.resolve(), args.sensitivity.resolve(), args.output_dir.resolve())
        write_json(args.manifest_out.resolve(), result)
    elif args.command == "build":
        if args.output.exists() or args.formula_manifest.exists():
            raise FileExistsError("Refusing to overwrite report source or formula manifest")
        result = build_report(args.template.resolve(), args.manifest.resolve(), [p.resolve() for p in args.audit],
                              args.result.resolve(), args.validation.resolve(), args.brief.resolve(), args.figures.resolve(),
                              args.sensitivity.resolve(), args.output.resolve(), args.formula_manifest.resolve())
    else: raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
