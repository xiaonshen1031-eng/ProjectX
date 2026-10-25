#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

try:
    import requests
except ImportError:  # Offline formatting checks do not require requests.
    requests = None
from docx import Document


REF_RE = re.compile(r"^\[(\d+)\]\s+(.+)$")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})(?:v\d+)?", re.IGNORECASE)
ARXIV_ID_RE = re.compile(r"\barxiv:([0-9]{4}\.[0-9]{4,5})(?:v\d+)?", re.IGNORECASE)
ARXIV_DOI_RE = re.compile(r"10\.48550/arxiv\.([0-9]{4}\.[0-9]{4,5})(?:v\d+)?", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
JOURNAL_HINT_RE = re.compile(
    r"\b(IEEE|Energy|Applied|Renewable|Transactions|Journal|Letters|"
    r"Robot|Robotics|Remote\s+Sens|Drones|Marine|Mar\.|Technol|Geol|Ocean|Oceans|"
    r"Proceedings|Conference|arXiv|Neural|Systems|Auton|Sensors|Wiley|SAGE|"
    r"Nature|Nat\.\s+Methods|Science|Springer|Elsevier|MDPI|ACM|CVPR|ICCV|ECCV|Graphics\s+Gems)\b",
    re.IGNORECASE,
)
UA = "senior-projectx-reference-check/2.0 (metadata audit)"


def norm(text: str) -> str:
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def load_reference_lines(path: Path) -> list[str]:
    if path.suffix.lower() == ".docx":
        doc = Document(path)
        lines = []
        in_refs = False
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            if text.lower() == "references":
                in_refs = True
                continue
            if in_refs:
                lowered = text.lower()
                if lowered.startswith("disclaimer/") or lowered.startswith("publisher's note"):
                    break
                lines.append(text)
        return lines
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def likely_title(ref_body: str) -> str:
    text = re.sub(r"https?://\S+", "", ref_body).strip()
    candidates = [x.strip() for x in re.split(r"\.\s+", text) if len(x.strip()) > 12]
    if len(candidates) >= 2:
        return candidates[1]
    return candidates[0] if candidates else ""


def title_match_score(resolved_title: str, ref_body: str, title_guess: str) -> tuple[float, str]:
    if not resolved_title:
        return 0.0, "mismatch"
    resolved_n = norm(resolved_title)
    ref_n = norm(ref_body)
    guess_n = norm(title_guess)
    if resolved_n and resolved_n in ref_n:
        return 1.0, "match"
    score = max(similarity(resolved_title, title_guess), similarity(resolved_title, ref_body))
    if score >= 0.78:
        return score, "match"
    if resolved_n and guess_n and (resolved_n in guess_n or guess_n in resolved_n):
        return max(score, 0.90), "match"
    return score, "partial" if score >= 0.58 else "mismatch"


def author_match(ref_body: str, resolved_authors: str) -> str:
    if not resolved_authors:
        return "unknown"
    ref_n = norm(ref_body)
    families = []
    for name in resolved_authors.split(";"):
        parts = name.strip().split()
        if parts:
            families.append(parts[-1].lower())
    if not families:
        return "unknown"
    hits = sum(1 for fam in families[:3] if fam and fam in ref_n)
    if families[0] in ref_n and hits >= min(2, len(families[:3])):
        return "match"
    if families[0] in ref_n:
        return "first_author_match"
    return "mismatch"


def doi_resolves(doi: str) -> bool:
    if requests is None:
        return False
    try:
        response = requests.head(f"https://doi.org/{doi}", allow_redirects=True, timeout=15, headers={"User-Agent": UA})
        return response.status_code < 400
    except Exception:
        return False


def crossref_metadata(doi: str) -> dict:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    if requests is None:
        return {"source": "Crossref", "resolved": False, "status": "requests package unavailable", "source_url": f"https://doi.org/{doi}"}
    try:
        response = requests.get(url, timeout=30, headers={"User-Agent": UA})
    except Exception as exc:
        return {"source": "Crossref", "resolved": False, "status": f"error: {exc}", "source_url": f"https://doi.org/{doi}"}
    if response.status_code != 200:
        return {"source": "Crossref", "resolved": False, "status": response.status_code, "source_url": f"https://doi.org/{doi}"}
    msg = response.json().get("message", {})
    authors = []
    for a in msg.get("author") or []:
        name = " ".join(x for x in [a.get("given", ""), a.get("family", "")] if x).strip()
        if name:
            authors.append(name)
    date_parts = (
        msg.get("published-print", {}).get("date-parts")
        or msg.get("published-online", {}).get("date-parts")
        or msg.get("issued", {}).get("date-parts")
        or [[""]]
    )
    return {
        "source": "Crossref",
        "resolved": True,
        "status": 200,
        "source_url": f"https://doi.org/{doi}",
        "resolved_title": (msg.get("title") or [""])[0],
        "resolved_authors": "; ".join(authors),
        "resolved_venue": (msg.get("container-title") or [""])[0],
        "resolved_year": str(date_parts[0][0]) if date_parts and date_parts[0] else "",
    }


def arxiv_metadata(arxiv_id: str) -> dict:
    url = "https://export.arxiv.org/api/query?id_list=" + urllib.parse.quote(arxiv_id)
    if requests is None:
        return {"source": "arXiv", "resolved": False, "status": "requests package unavailable", "source_url": f"https://arxiv.org/abs/{arxiv_id}"}
    try:
        response = requests.get(url, timeout=30, headers={"User-Agent": UA})
    except Exception as exc:
        return {"source": "arXiv", "resolved": False, "status": f"error: {exc}", "source_url": f"https://arxiv.org/abs/{arxiv_id}"}
    if response.status_code != 200:
        return {"source": "arXiv", "resolved": False, "status": response.status_code, "source_url": f"https://arxiv.org/abs/{arxiv_id}"}
    root = ET.fromstring(response.content)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = root.find("a:entry", ns)
    if entry is None:
        return {"source": "arXiv", "resolved": False, "status": 404, "source_url": f"https://arxiv.org/abs/{arxiv_id}"}
    authors = [a.findtext("a:name", default="", namespaces=ns) for a in entry.findall("a:author", ns)]
    return {
        "source": "arXiv",
        "resolved": True,
        "status": 200,
        "source_url": f"https://arxiv.org/abs/{arxiv_id}",
        "resolved_title": " ".join((entry.findtext("a:title", default="", namespaces=ns) or "").split()),
        "resolved_authors": "; ".join(a for a in authors if a),
        "resolved_venue": "arXiv",
        "resolved_year": (entry.findtext("a:published", default="", namespaces=ns) or "")[:4],
    }


def classify_entry(entry: dict, metadata: bool) -> str:
    if entry.get("source") == "arXiv":
        if metadata:
            if entry.get("metadata_resolved") and entry.get("title_match") == "match":
                return "verified_arxiv_metadata"
            return "ARXIV_MISMATCH_CHECK"
        return "arxiv_present"
    if entry["doi"]:
        if metadata:
            if not entry.get("metadata_resolved"):
                return "DOI_NOT_RESOLVED"
            if entry.get("title_match") == "match" and entry.get("author_match") in {"match", "first_author_match"}:
                return "verified"
            return "METADATA_MISMATCH_CHECK"
        return "doi_present" if entry.get("doi_resolves") is not False else "DOI_NOT_RESOLVED"
    if entry["arxiv_id"]:
        return "arxiv_present"
    return "non_doi_source"


def validate_references(lines: Iterable[str], online: bool = False, metadata: bool = False) -> dict:
    entries = []
    warnings: list[str] = []
    numbers = []
    for idx, line in enumerate(lines, start=1):
        m = REF_RE.match(line)
        if m:
            num = int(m.group(1))
            body = m.group(2)
            numbers.append(num)
        else:
            num = idx
            body = line
        doi_match = DOI_RE.search(body)
        arxiv_match = ARXIV_RE.search(body) or ARXIV_ID_RE.search(body)
        doi = doi_match.group(0).rstrip(".") if doi_match else ""
        arxiv_doi_match = ARXIV_DOI_RE.search(doi)
        arxiv_id = arxiv_match.group(1) if arxiv_match else (arxiv_doi_match.group(1) if arxiv_doi_match else "")
        title_guess = likely_title(body)
        entry = {
            "number": num,
            "numbered_style": bool(m),
            "has_year": bool(YEAR_RE.search(body)),
            "has_journal_hint": bool(JOURNAL_HINT_RE.search(body)),
            "doi": doi,
            "arxiv_id": arxiv_id,
            "doi_resolves": None,
            "metadata_resolved": None,
            "source": "",
            "source_url": "",
            "title_guess": title_guess,
            "resolved_title": "",
            "title_similarity": None,
            "title_match": "",
            "resolved_authors": "",
            "author_match": "",
            "resolved_venue": "",
            "resolved_year": "",
            "audit_status": "",
            "text": body,
        }
        if not entry["has_year"]:
            warnings.append(f"Reference [{num}] may be missing a year.")
        if not entry["has_journal_hint"]:
            warnings.append(f"Reference [{num}] may be missing a journal or venue marker.")
        if not doi and not arxiv_id:
            warnings.append(f"Reference [{num}] is missing a DOI/arXiv identifier or is a non-DOI source.")
        if doi and online and not metadata:
            entry["doi_resolves"] = doi_resolves(doi)
            if not entry["doi_resolves"]:
                warnings.append(f"Reference [{num}] DOI did not resolve: {doi}")
        if metadata and (doi or arxiv_id):
            result = arxiv_metadata(arxiv_id) if arxiv_id and (not doi or ARXIV_DOI_RE.search(doi)) else crossref_metadata(doi)
            entry["metadata_resolved"] = bool(result.get("resolved"))
            entry["source"] = result.get("source", "")
            entry["source_url"] = result.get("source_url", "")
            entry["resolved_title"] = result.get("resolved_title", "")
            entry["resolved_authors"] = result.get("resolved_authors", "")
            entry["resolved_venue"] = result.get("resolved_venue", "")
            entry["resolved_year"] = result.get("resolved_year", "")
            score, tmatch = title_match_score(entry["resolved_title"], body, title_guess)
            entry["title_similarity"] = round(score, 3)
            entry["title_match"] = tmatch
            entry["author_match"] = author_match(body, entry["resolved_authors"])
            if not entry["metadata_resolved"]:
                warnings.append(f"Reference [{num}] metadata did not resolve: {doi or arxiv_id}")
            elif tmatch != "match":
                warnings.append(f"Reference [{num}] title may not match resolved metadata.")
            elif doi and entry["author_match"] not in {"match", "first_author_match"}:
                warnings.append(f"Reference [{num}] authors may not match resolved metadata.")
            time.sleep(0.15)
        entry["audit_status"] = classify_entry(entry, metadata)
        entries.append(entry)

    if numbers:
        expected = list(range(min(numbers), max(numbers) + 1))
        missing = sorted(set(expected) - set(numbers))
        if missing:
            warnings.append(f"Missing reference numbers: {missing}")
        if len(set(numbers)) != len(numbers):
            warnings.append("Duplicate reference numbers detected.")

    counts = {}
    for entry in entries:
        counts[entry["audit_status"]] = counts.get(entry["audit_status"], 0) + 1
    return {"entries": entries, "status_counts": counts, "warnings": warnings}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check reference formatting, DOI/arXiv resolution, and optional metadata consistency.")
    parser.add_argument("input_path")
    parser.add_argument("--online", action="store_true", help="Check DOI resolution with doi.org HEAD requests.")
    parser.add_argument("--metadata", action="store_true", help="Resolve DOI/arXiv metadata and compare title/author fields.")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    path = Path(args.input_path).resolve()
    result = validate_references(load_reference_lines(path), online=args.online or args.metadata, metadata=args.metadata)
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    sys.stdout.buffer.write((payload + "\n").encode("utf-8", errors="replace"))
    if args.json_out:
        Path(args.json_out).write_text(payload, encoding="utf-8")


if __name__ == "__main__":
    main()
