#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from lxml import etree


FIG_RE = re.compile(r"^(?:Figure|Fig\.|图)\s*(\d+)[\s\.:：]", re.IGNORECASE)
TAB_RE = re.compile(r"^(?:Table|表)\s*(\d+)[\s\.:：]", re.IGNORECASE)
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
TOGGLE_TEX_RE = re.compile(r"(?<!\\)\$(?!\$)(.+?)(?<!\\)\$", re.DOTALL)
TEX_COMMAND_RE = re.compile(r"\\(?:frac|sqrt|sum|prod|int|mathrm|mathbf|mathcal|hat|bar|dot|vec|left|right)\b")
UNSAFE_TOGGLE_COMMAND_RE = re.compile(r"\\(?:begin|end|tag|label|ref|includegraphics|input|write18)\b")

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}
INLINE_MATH_ACRONYM_WHITELIST = {
    "OFDM", "UWOC", "BER", "EVM", "SNR", "CFNN", "LMS", "ZF", "AVG-ZF",
    "RES-TCN", "FFT", "FEC", "MATLAB", "CPU", "GPU", "DB", "BIT",
}
MATH_CUE_RE = re.compile(
    r"(?:式中|其中|定义(?:为)?|记为|表示为|写为|可写为|(?:^|[。；，,])\s*(?:设|令)|denote|define|let|where)\s*[，,:：]?",
    re.IGNORECASE,
)
FORMULA_OPERATOR_RE = re.compile(
    r"(?P<formula>(?:[A-Za-zΑ-Ωα-ω][A-Za-z0-9Α-Ωα-ω_^*]*(?:\[[^\]\n]{1,20}\])?)\s*"
    r"(?:=|≠|≈|∈|∉|≤|≥|<|>)\s*"
    r"(?:[-+−]?(?:\d+(?:\.\d+)?|[A-Za-zΑ-Ωα-ω][A-Za-z0-9Α-Ωα-ω_^*]*(?:\[[^\]\n]{1,20}\])?)"
    r"(?:\s*[×·*/+−-]\s*(?:10(?:[−-]?\d+)?|\d+(?:\.\d+)?|[A-Za-zΑ-Ωα-ω][A-Za-z0-9Α-Ωα-ω_^*]*))?))"
)
INDEXED_SYMBOL_RE = re.compile(r"\b[A-Za-zΑ-Ωα-ω][A-Za-z0-9Α-Ωα-ω_^*]*\s*\[[A-Za-z0-9, ]+\]")


def strip_xml(xml: str) -> str:
    text = re.sub(r"<[^>]+>", " ", xml)
    return re.sub(r"\s+", " ", text).strip()


def sequence_warnings(kind: str, nums: list[int]) -> list[str]:
    warnings: list[str] = []
    if not nums:
        warnings.append(f"No {kind.lower()} captions detected in visible text.")
        return warnings
    if len(set(nums)) != len(nums):
        dupes = sorted(n for n in set(nums) if nums.count(n) > 1)
        warnings.append(f"Duplicate {kind.lower()} numbers: {dupes}")
    expected = list(range(min(nums), max(nums) + 1))
    missing = sorted(set(expected) - set(nums))
    if missing:
        warnings.append(f"Missing {kind.lower()} numbers: {missing}")
    if nums != sorted(nums):
        warnings.append(f"{kind} numbers appear out of order: {nums}")
    return warnings


def balanced_braces(text: str) -> bool:
    depth = 0
    escaped = False
    for char in text:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def plain_text_outside_math(paragraph) -> str:
    return "".join(paragraph.xpath(".//w:t[not(ancestor::m:oMath)]/text()", namespaces=NS))


def nearest_ancestor(element, local_name: str):
    parent = element.getparent()
    while parent is not None:
        if etree.QName(parent).localname == local_name:
            return parent
        parent = parent.getparent()
    return None


def is_display_math(math_element) -> bool:
    if nearest_ancestor(math_element, "oMathPara") is not None:
        return True
    row = nearest_ancestor(math_element, "tr")
    if row is not None:
        row_text = "".join(row.xpath(".//w:t/text()", namespaces=NS)).strip()
        if re.search(r"\(\s*\d+[a-z]?\s*\)\s*$", row_text, re.IGNORECASE):
            return True
    paragraph = nearest_ancestor(math_element, "p")
    if paragraph is None:
        return False
    prose = plain_text_outside_math(paragraph).strip(" \t\r\n，,。.;；:")
    return not prose


def formula_like_plaintext_audit(root) -> tuple[list[dict], list[str]]:
    symbol_inventory = sorted(
        {
            token
            for text in root.xpath(".//m:oMath//m:t/text()", namespaces=NS)
            for token in re.findall(r"[A-Za-zΑ-Ωα-ω][A-Za-z0-9Α-Ωα-ω]*", text)
            if token.upper() not in INLINE_MATH_ACRONYM_WHITELIST
        },
        key=lambda item: (item.lower(), item),
    )
    symbol_set = set(symbol_inventory)
    examples: list[dict] = []
    for index, paragraph in enumerate(root.xpath(".//w:body//w:p", namespaces=NS), start=1):
        text = " ".join(plain_text_outside_math(paragraph).split())
        if not text or re.match(r"^\[\d+\]\s", text):
            continue
        matches: list[str] = []
        for match in FORMULA_OPERATOR_RE.finditer(text):
            candidate = match.group("formula").strip()
            left = re.match(r"[A-Za-zΑ-Ωα-ω][A-Za-z0-9Α-Ωα-ω_^*]*", candidate)
            left_token = left.group(0).replace("_", "").replace("^", "").replace("*", "") if left else ""
            if left_token.upper() in INLINE_MATH_ACRONYM_WHITELIST and not re.search(r"(?:=|≠|≈|∈|∉|≤|≥|<|>)", candidate):
                continue
            matches.append(candidate)
        cue_present = bool(MATH_CUE_RE.search(text))
        for match in INDEXED_SYMBOL_RE.finditer(text):
            candidate = match.group(0).strip()
            base = re.match(r"[A-Za-zΑ-Ωα-ω][A-Za-z0-9Α-Ωα-ω_^*]*", candidate).group(0)
            if cue_present or base in symbol_set:
                matches.append(candidate)
        if cue_present and symbol_set:
            cue_tail = text[MATH_CUE_RE.search(text).end():]
            for token in re.findall(r"(?<![A-Za-z0-9-])([A-Za-zΑ-Ωα-ω][A-Za-z0-9Α-Ωα-ω_^*]{0,12})(?![A-Za-z0-9-])", cue_tail):
                if token in symbol_set and token.upper() not in INLINE_MATH_ACRONYM_WHITELIST:
                    matches.append(token)
        unique_matches = list(dict.fromkeys(matches))
        if unique_matches:
            examples.append({"paragraph": index, "matches": unique_matches, "text": text[:500]})
    return examples, symbol_inventory


def audit(
    docx_path: Path,
    require_emf_only: bool,
    forbidden_terms: list[str],
    equation_backend: str = "auto",
    equations_required: bool = False,
    allow_mixed_equation_backends: bool = False,
    require_inline_office_math: bool = False,
    require_mathtype_authenticity: bool = False,
    mathtype_evidence: Path | None = None,
) -> dict:
    warnings: list[str] = []
    authenticity = None
    if require_mathtype_authenticity or mathtype_evidence:
        from mathtype_authenticity import audit_mathtype
        authenticity = audit_mathtype(docx_path, mathtype_evidence)
        if authenticity['status'] != 'pass':
            warnings.append('MathType authenticity is unverified or failed; inspect native payload, intended content, preview, Word rendering and reopened document.')
    with ZipFile(docx_path) as z:
        names = z.namelist()
        document_xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        media = [n for n in names if n.startswith("word/media/")]
        visible_text = strip_xml(document_xml)

    root = etree.fromstring(document_xml.encode("utf-8"))
    math_objects = root.xpath(".//m:oMath", namespaces=NS)
    inline_omml_count = sum(1 for item in math_objects if not is_display_math(item))
    display_omml_count = len(math_objects) - inline_omml_count
    formula_like_examples, omml_symbol_inventory = formula_like_plaintext_audit(root)

    doc = Document(docx_path)
    paragraph_text = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    visible_text_docx = " ".join(paragraph_text)
    media_ext_counts = Counter(Path(name).suffix.lower() for name in media)
    figure_nums = [int(m.group(1)) for t in paragraph_text for m in [FIG_RE.match(t)] if m]
    table_nums = [int(m.group(1)) for t in paragraph_text for m in [TAB_RE.match(t)] if m]
    dois = DOI_RE.findall(visible_text_docx or visible_text)
    omml_count = len(math_objects)
    ole_object_count = len(re.findall(r"<o:OLEObject\b", document_xml))
    equation_text = visible_text
    toggle_matches = TOGGLE_TEX_RE.findall(equation_text)
    toggle_tex_count = len(toggle_matches)
    tex_command_count = len(TEX_COMMAND_RE.findall(equation_text))
    unmatched_dollar_count = max(0, equation_text.count("$") - 2 * toggle_tex_count)
    malformed_toggle_tex = [
        formula for formula in toggle_matches
        if not formula.strip() or not balanced_braces(formula) or UNSAFE_TOGGLE_COMMAND_RE.search(formula)
    ]

    if omml_count and (toggle_tex_count or (authenticity and authenticity['object_count'])):
        detected_backend = "mixed"
    elif omml_count:
        detected_backend = "office_math"
    elif toggle_tex_count:
        detected_backend = "mathtype_toggle_tex"
    elif authenticity and authenticity['status'] == 'pass':
        detected_backend = "mathtype_toggle_tex"
    elif ole_object_count:
        detected_backend = "legacy_embedded_object"
    else:
        detected_backend = "none"
    validation_backend = detected_backend if equation_backend == "auto" else equation_backend

    warnings.extend(sequence_warnings("Figure", figure_nums))
    warnings.extend(sequence_warnings("Table", table_nums))

    if require_emf_only:
        non_emf = [name for name in media if Path(name).suffix.lower() != ".emf"]
        if non_emf:
            warnings.append(f"Non-EMF media detected under EMF-only requirement: {non_emf}")

    for term in forbidden_terms:
        count = (visible_text_docx or visible_text).lower().count(term.lower())
        if count:
            warnings.append(f"Forbidden visible term appears {count} time(s): {term}")

    if validation_backend == "office_math":
        if equations_required and omml_count == 0:
            warnings.append("Declared office_math backend contains no Office Math (OMML) objects.")
        if toggle_tex_count and not allow_mixed_equation_backends:
            warnings.append("Toggle-TeX formulas detected in an office_math document; mixed equation backends require explicit authorization.")
        if require_inline_office_math and inline_omml_count == 0:
            warnings.append("Declared office_math backend contains no inline Office Math objects under the inline-math requirement.")
        if require_inline_office_math and formula_like_examples:
            warnings.append(
                f"Formula-like plain text remains under the inline Office Math requirement: {len(formula_like_examples)} paragraph(s)."
            )
    elif validation_backend == "mathtype_toggle_tex":
        if equations_required and toggle_tex_count == 0 and not (authenticity and authenticity['status'] == 'pass'):
            warnings.append("Declared mathtype_toggle_tex backend contains no $...$ Toggle-TeX formulas.")
        if omml_count and not allow_mixed_equation_backends:
            warnings.append("Office Math objects detected in a mathtype_toggle_tex document; accidental OMML or an unauthorized mixed backend is present.")
        if unmatched_dollar_count:
            warnings.append(f"Unmatched Toggle-TeX dollar delimiters detected: {unmatched_dollar_count}.")
        if malformed_toggle_tex:
            warnings.append(f"Conservatively malformed or unsupported Toggle-TeX formulas detected: {len(malformed_toggle_tex)}.")
    elif validation_backend == "mixed" and not allow_mixed_equation_backends:
        warnings.append("Both Office Math and Toggle-TeX formulas are present; mixed equation backends require explicit authorization.")
    elif equations_required:
        warnings.append("No recognized office_math or mathtype_toggle_tex equations detected although equations are required.")

    if ole_object_count and authenticity is None:
        warnings.append(
            f"Legacy embedded OLE equation/object nodes detected: {ole_object_count}. "
            "They are reported for provenance and are not silently treated as either declared authoring backend."
        )
    if not dois:
        warnings.append("No DOI-like strings detected in visible text.")

    return {
        "docx": str(docx_path),
        "media_count": len(media),
        "media_extensions": dict(sorted(media_ext_counts.items())),
        "figure_numbers": figure_nums,
        "table_numbers": table_nums,
        "doi_count": len(dois),
        "unique_doi_count": len(set(dois)),
        "office_math_object_count": omml_count,
        "display_office_math_object_count": display_omml_count,
        "inline_office_math_object_count": inline_omml_count,
        "require_inline_office_math": require_inline_office_math,
        "formula_like_plaintext_hits": len(formula_like_examples),
        "formula_like_plaintext_examples": formula_like_examples[:20],
        "omml_symbol_inventory": omml_symbol_inventory,
        "toggle_tex_formula_count": toggle_tex_count,
        "tex_command_count": tex_command_count,
        "legacy_ole_object_count": ole_object_count,
        "mathtype_authenticity": authenticity,
        "equation_backend_requested": equation_backend,
        "equation_backend_detected": detected_backend,
        "mixed_equation_backends_allowed": allow_mixed_equation_backends,
        "malformed_toggle_tex_count": len(malformed_toggle_tex),
        "forbidden_terms_checked": forbidden_terms,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit final DOCX media, captions, DOI strings, declared equation backend, and forbidden terms.")
    parser.add_argument("docx_path")
    parser.add_argument("--require-emf-only", action="store_true", help="Warn if any embedded media are not EMF.")
    parser.add_argument("--forbid-visible-term", action="append", default=[], help="Visible term that should not appear in the manuscript. Can be repeated.")
    parser.add_argument("--equation-backend", choices=["auto", "office_math", "mathtype_toggle_tex"], default="auto")
    parser.add_argument("--equations-required", action="store_true", help="Require at least one equation in the selected backend.")
    parser.add_argument("--allow-mixed-equation-backends", action="store_true", help="Allow deliberate OMML and Toggle-TeX mixing.")
    parser.add_argument("--require-inline-office-math", action="store_true", help="Require inline mathematical variables and expressions to be real OMML, not styled plain text.")
    parser.add_argument("--require-mathtype-authenticity", action="store_true", help="Require native MathType content, preview, Word render and reopen verification; never accept ProgID/count alone.")
    parser.add_argument("--mathtype-evidence", type=Path, help="Existing conversion/inspection evidence JSON with independent expected native exports.")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    result = audit(
        Path(args.docx_path).resolve(),
        args.require_emf_only,
        args.forbid_visible_term,
        equation_backend=args.equation_backend,
        equations_required=args.equations_required,
        allow_mixed_equation_backends=args.allow_mixed_equation_backends,
        require_inline_office_math=args.require_inline_office_math,
        require_mathtype_authenticity=args.require_mathtype_authenticity,
        mathtype_evidence=args.mathtype_evidence,
    )
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    sys.stdout.buffer.write((payload + "\n").encode("utf-8", errors="replace"))
    if args.json_out:
        Path(args.json_out).write_text(payload, encoding="utf-8")
    if args.require_mathtype_authenticity and result['mathtype_authenticity']['status'] != 'pass':
        raise SystemExit(2)


if __name__ == "__main__":
    main()
