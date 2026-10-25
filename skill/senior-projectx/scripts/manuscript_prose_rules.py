"""Shared Journal/Conference/Project editorial candidates and source-bound review.

This is a read-only prose screen, not authorship detection. A candidate is a
request to inspect the scientific context; no rule deletes or rewrites facts.
Draft commands remain advisory; each branch's final gate uses these candidates.
"""
from __future__ import annotations

from difflib import SequenceMatcher
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re


RULES = (
    ("defensive_prose", re.compile(
        r"\b(?:we do not claim|should not be interpreted as|this does not undermine|"
        r"does not affect the validity|despite this limitation|remains valid despite|"
        r"the (?:method|model|framework|approach) is not intended to|"
        r"does not imply|cannot establish|cannot be used as evidence|"
        r"merely|just a simple|only an incremental|proof[- ]of[- ]concept)\b|"
        r"\b(?:although|while|despite)\b.{0,140}\b(?:cannot|unable|imperfect|limitation)\b"
        r".{0,140}\b(?:still|nevertheless|remains?|useful|valuable)\b|"
        r"(?:虽然|尽管).{0,90}(?:不能|无法|不足|局限).{0,90}(?:但|仍|价值)|"
        r"这并不(?:意味着|影响)|不能(?:据此|作为).{0,45}(?:依据|证明|声称)|"
        r"(?:所提|提出的|本研究的|该)(?:方法|模型|框架|算法).{0,50}(?:但是|但|却).{0,35}(?:不能|无法)|"
        r"\b(?:proposed|developed) (?:method|model|framework|approach|algorithm)\b"
        r".{0,90}\b(?:cannot|unable to|does not|not intended to)\b|"
        r"\b(?:the|this|our) (?:method|model|framework|approach|algorithm)\b"
        r".{0,55}\b(?:cannot|can't|unable to|not able to)\b|"
        r"(?:该|所提|本研究的|本)(?:方法|模型|框架|算法).{0,30}(?:无法|不能)(?:实现|支持|作为|用于|提供|刻画|描述|证明)?|"
        r"(?:本文|本研究)(?:不把|不提供|不声称)|不能据此声称|尚不能(?:作为|外推)|"
        r"本(?:报告|文档)(?:仅|只)(?:供|作)(?:参考|参考使用)|"
        r"\b(?:we do not interpret this as|the conclusion should be restricted to|"
        r"a more cautious conclusion is|the current evidence is limited by)\b", re.I),
     "State the modeled condition or observed result directly. Remove self-denial and reassurance; preserve actual constraints and adverse evidence."),
    ("ai_formulaic_prose", re.compile(
        r"\b(?:it is worth noting(?: that)?|it (?:should|must) be (?:noted|emphasized)(?: that)?|"
        r"plays? a crucial role|provides? valuable insights|this clearly demonstrates|"
        r"these findings highlight|this distinction is important because|"
        r"in today['’]s rapidly evolving|holistic framework|seamlessly|"
        r"the following conclusions can be drawn|rather than|instead of)\b|"
        r"\bnot only\b.{0,120}\bbut also\b|"
        r"(?:证据链|证据角色|结论边界|研究边界|赋能|核心(?:价值|优势|作用|支撑|意义)|"
        r"取得(?:了)?(?:良好|显著|优异)(?:效果|成效)|具有(?:十分|非常)?重要(?:的)?(?:意义|价值)|"
        r"全面(?:系统)?地?(?:分析|研究|揭示)|为.{0,24}提供(?:了)?(?:有力|坚实|重要)(?:支撑|保障)|"
        r"值得注意的是|需要强调的是)", re.I),
     "Replace stock evaluation or internal labels with the scientific object, action, condition and consequence; remove text carrying no technical information."),
    ("ai_formulaic_prose", re.compile(
        r"(?:^|(?<=[.!?。！？])\s*)(?:First(?:ly)?|Second(?:ly)?|Third(?:ly)?|Finally|"
        r"Moreover|Furthermore|Additionally)\b|"
        r"(?:^|(?<=[。！？]))\s*(?:首先|其次|再次|最后|第一|第二|第三)[，、：:]?", re.I),
     "Connect the next statement through the preceding variable, output, result or open question. Genuine numbered algorithm steps and distinct contribution items may be retained after contextual review."),
    ("ai_formulaic_prose", re.compile(
        r"\b(?:good (?:performance|effectiveness|robustness|results)|performs? well|"
        r"(?:Figure|Fig\.|Table)\s*\d+(?:\([a-z]\))?\s+(?:shows?|presents?|illustrates?)\s+"
        r"(?:the\s+)?(?:experimental\s+)?(?:results|performance|effectiveness|comparison)\s*[.!])|"
        r"为验证.{0,35}(?:有效性|性能).{0,70}实验结果表明.{0,60}(?:良好|较好|有效性|鲁棒性)|"
        r"实验结果表明.{0,45}(?:具有较好|具有良好|效果良好|取得良好)|"
        r"(?:图|表)\s*\d+\s*(?:展示|显示|给出)(?:了)?(?:实验|测试|对比)?结果[。.]", re.I),
     "Replace an empty experiment/figure recital with the concrete observation and its scientific relationship. Keep substantive paired errors, distributions and necessary comparison design."),
    ("experimental_process_leakage", re.compile(
        r"\b(?:according to your (?:request|prompt)|as requested by (?:you|the user)|"
        r"according to the reviewer|reviewer requested|we revised|after revision|"
        r"this paper has been modified|changes in the manuscript|as an AI (?:assistant|language model)|"
        r"claim (?:ID |[A-Z]\d)|evidence (?:chain|role|map)|pass/fail gate|audit gate|"
        r"completion status|freeze state|author-confirmed|confirmed by the author|"
        r"has not yet been synchronized|has not yet been completed|"
        r"the diagnostic is intentionally evaluated|this comparison asks whether|"
        r"this figure does not replace|the purpose of this diagnostic is)\b|"
        r"(?:按(?:照)?(?:用户|审稿人|提示词)(?:的)?要求|本次生成|在修改过程中|作者确认|"
        r"尚未(?:同步|回传|完成)|后续归档|冻结状态|审查门禁|阻断项|证据链|证据角色|"
        r"回归测试通过|校验通过|完成状态|调参记录|运行日志|实验验收)|"
        r"(?:hash|checksum|digest)[ -]*(?:verified|verification passed|check passed)|"
        r"(?:SHA[- ]?256|MD5)\s*[:=]\s*[0-9a-f]{32,64}\b|"
        r"[A-Za-z]:[\\/](?:Users|科研)[^\s}]*", re.I),
     "Move execution, revision, audit, pending-work and packaging records to a separate JSON/MD sidecar. Keep the scientific formulation, reproducibility protocol and actual result in their manuscript sections."),
    ("experimental_process_leakage", re.compile(
        r"\b(?:tuned?|adjusted?|searched?|reran|run again)\b.{0,90}\b(?:until|to reach|target|must)\b"
        r".{0,90}\b(?:wins?|win rate|victor|[345]\s*/\s*[45])\b|"
        r"(?:必须|调参至|继续调参|调到|直到|验收|目标胜率).{0,50}(?:胜率|胜|win|[345]\s*/\s*[45])|"
        r"(?:win|胜率).{0,40}(?:验收|必须|目标)|"
        r"(?:日志|文件|脚本|运行).{0,30}(?:已通过|已保存|校验成功|回传|同步)", re.I),
     "Keep tuning targets, acceptance counts and run receipts in the experiment sidecar. Report current verified metrics under the stated selection protocol, without rewriting them to match a desired outcome."),
    ("experimental_process_leakage", re.compile(
        r"\b(?:we|the authors?)\s+(?:first\s+)?(?:ran|executed|reran|launched)\b"
        r".{0,100}\b(?:then|again|completed|saved|uploaded|trial|job)\b|"
        r"(?:先|随后|然后).{0,25}(?:运行|重跑|执行|导出|上传).{0,60}(?:日志|脚本|文件|完成|保存|调参)|"
        r"(?:实验|测试|调参)(?:进度|过程记录|运行状态|完成记录)", re.I),
     "Replace run chronology with the methodological protocol or scientific finding; keep execution history in a sidecar."),
    ("experimental_report_prose", re.compile(
        r"\b(?:this (?:experiment|test|comparison) is (?:intended|designed) to|"
        r"this (?:experiment|test|comparison) aims? to (?:verify|demonstrate|validate)|"
        r"to (?:verify|demonstrate|validate) (?:the )?(?:effectiveness|superiority|"
        r"good performance)|(?:experimental|experiment|test) results (?:show|demonstrate) that)\b|"
        r"(?:该|本|此)(?:实验|测试|对比|比较)(?:旨在|的目的(?:在于|是))|"
        r"为(?:了)?验证.{0,35}(?:有效性|优越性|性能)|(?:实验|测试)结果表明|"
        r"(?:本次|本节)(?:实验|测试).{0,25}(?:验证|证明|展示|表明)", re.I),
     "State the measured finding or engineering relationship directly. Put the necessary comparison design in Methods; remove effectiveness-verification and experimental-report narration."),
    ("experimental_process_leakage", re.compile(
        r"\b(?:the|this) (?:figure|plot|manuscript|document)\b.{0,50}\b(?:regenerated|"
        r"reformatted|saved as|exported to|converted to|verification passed)\b|"
        r"(?:图片|图像|文档|稿件).{0,30}(?:重新生成|重新排版|另存为|已导出|已转换)", re.I),
     "Keep figure generation, document formatting and saved-file receipts in the production sidecar; the caption and body describe scientific content."),
)

QUOTE_RE = re.compile(
    r"(?:提出|构建|形成|称为|打造|引入)(?:了)?[“\"]([^”\"]{2,35})[”\"]|"
    r"\b(?:introduce|propose|call|term|construct)\w*\s+(?:a\s+|an\s+|the\s+)?[“\"]([^”\"]{3,70})[”\"]|"
    r"[“\"][^”\"]{2,35}(?:闭环|机制|范式|体系|核心|能力|决策链)[”\"]|"
    r"[“\"][^”\"]{0,45}\b(?:evidence|intelligence|synergy|core|multi-domain)\b[^”\"]{0,45}[”\"]", re.I)
ABSTRACT_WORDS = re.compile(
    r"\b(?:accuracy|robustness|stability|reliability|generalization|effectiveness|"
    r"adaptability|efficiency|flexibility|synergy|resilience)\b|"
    r"准确性|鲁棒性|稳定性|可靠性|泛化性|有效性|适应性|协同性|多维度|多层级|多尺度", re.I)
CHINESE_ABSTRACT_STACK_RE = re.compile(
    r"(?:[\u3400-\u9fff]{2,10}(?:性|化|能力|机制|体系|水平)[、，,]){2,}"
    r"[\u3400-\u9fff]{2,10}(?:性|化|能力|机制|体系|水平)"
)
CONNECTOR_RE = re.compile(r"^(?:Moreover|Furthermore|Additionally|Therefore|Consequently|Finally|"
                          r"此外|因此|在此基础上|进一步|随后|最后)[,，]?", re.I)
ARTIFACT_RE = re.compile(r"\b(?:Figure|Fig\.|Table)\s*\d+[a-z]?\b|(?:图|表)\s*\d+", re.I)
STOPWORDS = set("a an the and or of to in on for from with by at as is are was were be been being "
                "it its this that these those which who their they them such also can may could would "
                "have has had do does did than more most each all both one two three first second "
                "finally therefore however furthermore additionally moreover study paper method methods "
                "model models proposed result results figure table shows show indicates indicate "
                "data analysis experiment experiments used using use compared comparison "
                "after before during when where while between through into under over without "
                "above below following previous current next stated evaluated observed".split())


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[。！？!?])\s*|(?<=[.;])\s+(?=[A-Z])", text) if s.strip()]


def substantive_tokens(text: str) -> set[str]:
    text = ARTIFACT_RE.sub("", text)
    latin = {t for t in re.findall(r"[A-Za-z][A-Za-z_-]{2,}", text.lower()) if t not in STOPWORDS}
    chinese = set()
    for word in re.findall(r"[\u3400-\u9fff]+", text):
        chinese.update(word[i:i+2] for i in range(len(word)-1))
    return latin | chinese


def carries_object_forward(left: str, right: str) -> bool:
    """A shared word or carried subject, not an accidental Chinese character pair.

    Chinese bigrams are useful for locating text, but an embedded pair in two
    unrelated longer nouns cannot establish a relationship by itself. Longer
    repeated phrases or a repeated short subject provide context-review cues.
    """
    shared = substantive_tokens(left) & substantive_tokens(right)
    if any(re.search(r"[A-Za-z]", token) for token in shared):
        return True
    left_phrases = {word[i:i+3] for word in re.findall(r"[\u3400-\u9fff]+", left)
                    for i in range(len(word)-2)}
    right_phrases = {word[i:i+3] for word in re.findall(r"[\u3400-\u9fff]+", right)
                     for i in range(len(word)-2)}
    if left_phrases & right_phrases:
        return True
    opening = CONNECTOR_RE.sub("", right.strip()).lstrip(" ,，:：;；")
    subject = re.match(r"[\u3400-\u9fff]{2}", opening)
    return bool(subject and subject.group() in shared)


def enough_text(text: str, english: int = 14, chinese: int = 25) -> bool:
    if len(re.findall(r"[\u3400-\u9fff]", text)) >= chinese:
        return True
    return len(re.findall(r"\b[A-Za-z]+\b", text)) >= english


def normalized(text: str) -> str:
    # Keep values: distinct horizons or findings are not duplicates merely
    # because they use the same sentence skeleton.
    return " ".join(re.findall(r"[A-Za-z0-9]+|[\u3400-\u9fff]", text.lower()))


TABLE_NUMBER_RE = re.compile(
    r"(?<![\w.])[-+−]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?"
    r"\s*(?:\\?%)?(?!\w|\.\d)"
)


def numeric_values(text: str) -> set[str]:
    """Comparable literal values, excluding citations, artifact IDs and H24-like labels.

    Decimal normalization equates 1.110 with 1.11, but never guesses rounding,
    units, percentage scaling, scientific symbols or calculated equivalence.
    """
    text = re.sub(r"\[\s*\d+(?:\s*[,;–-]\s*\d+)*\s*\]", "", text)
    text = ARTIFACT_RE.sub("", text)
    values = set()
    for match in TABLE_NUMBER_RE.finditer(text):
        token = match.group().strip().replace("−", "-")
        percentage = token.endswith("%")
        token = token.rstrip("%").rstrip("\\").strip()
        try:
            value = Decimal(token)
        except InvalidOperation:
            continue
        if value.is_finite():
            canonical = format(value.normalize(), "f") if value else "0"
            values.add(canonical + ("%" if percentage else ""))
    return values


def actual_table_evidence(blocks: list[dict]) -> list[dict]:
    """Group current visible cells by one actual table, never across tables."""
    grouped = {}
    for block in blocks:
        if block.get("kind") != "table" or "table" not in block:
            continue
        key = (block.get("file", ""), block["table"])
        grouped.setdefault(key, []).append(block)
    tables = []
    for (file, table), cells in grouped.items():
        values = set().union(*(numeric_values(cell["text"]) for cell in cells))
        if len(values) < 6:
            continue
        location = (file + ":" if file else "") + f"table:{table}"
        tables.append({"location": location, "file": file, "table": table,
                       "text": "\n".join(cell["location"] + ": " + cell["text"] for cell in cells),
                       "values": values})
    return tables


def specific_scientific_reason(reason: object, candidate: dict) -> bool:
    """Reject generic pass/approval prose; semantic validity still needs reading."""
    if not isinstance(reason, str) or len(reason.strip()) < 12:
        return False
    if re.fullmatch(r"(?:pass|ok|approved|reviewed|scientific content|technical content|looks fine|"
                    r"已审读|通过|科学内容|保留)(?:[\s.!。]*)", reason.strip(), re.I):
        return False
    anchors = substantive_tokens(candidate["original_text"] + " " + candidate.get("related_text", ""))
    relation = re.search(r"\b(?:defines?|definition|denotes?|specifies?|states?|because|constraint|"
                         r"condition|conjunction|alternatives?|dimensions?|variables?|measured|"
                         r"observed|compared|compares?|cited|source|operator|equation|feasible|"
                         r"information|inputs?|outputs?|assumption|disclosure|requires?|estimates?)\b|"
                         r"定义|条件|约束|变量|维度|输入|输出|比较|观测|测量|公式|引用|文献|来源|算子|假设|披露", reason, re.I)
    return bool(relation and anchors & substantive_tokens(reason))


def editorial_screen(blocks: list[dict], branch: str, reviews: dict | None = None) -> dict:
    """Blocks have location/text/section/kind/boundary plus optional file/line.

    Scientific exemptions bind to the candidate's current text and neighboring
    context. A statement that text was rewritten cannot waive a live finding.
    """
    if branch not in {"journal", "conference", "project"}:
        return {"manuscript_editorial_status": "not_applicable", "editorial_candidates": [],
                "editorial_candidate_count": 0, "unresolved_editorial_count": 0,
                "editorial_review_errors": []}
    candidates = []
    seen = set()
    prose = [b for b in blocks if b.get("kind", "prose") not in {"heading", "reference", "equation", "code"}]

    def add(block, kind, reason, other=None):
        index = blocks.index(block)
        before = blocks[index - 1]["text"] if index else ""
        after = blocks[index + 1]["text"] if index + 1 < len(blocks) else ""
        identity = {"branch": branch, "location": block["location"], "file": block.get("file", ""),
                    "type": kind, "text": block["text"], "before": before, "after": after,
                    "other_location": other.get("location") if other else None,
                    "other_text": other.get("text") if other else None}
        candidate_id = hashlib.sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:20]
        if candidate_id in seen:
            return
        seen.add(candidate_id)
        item = {"candidate_id": candidate_id, "type": kind, "location": block["location"],
                "section": block.get("section", ""), "original_text": block["text"],
                "context_before": before, "context_after": after, "reason": reason,
                "severity": "requires_context_review", "review_status": "unresolved"}
        for field in ("file", "line", "paragraph", "table", "row", "cell"):
            if field in block:
                item[field] = block[field]
        if other:
            item["related_location"] = other["location"]
            item["related_text"] = other["text"]
        candidates.append(item)
        return item

    for block in prose:
        text = block["text"]
        disclosure = bool(re.search(r"(?:disclosure|statement.*(?:AI|language models)|AI.*use)", block.get("section", ""), re.I))
        for kind, pattern, advice in RULES:
            if disclosure and kind == "experimental_process_leakage":
                continue
            if pattern.search(text):
                add(block, kind, advice)
        if QUOTE_RE.search(text):
            add(block, "ai_formulaic_prose", "A quoted label needs an established source or a precise operational definition. Remove decorative naming; retain genuine cited or defined terminology.")
        if CHINESE_ABSTRACT_STACK_RE.search(text):
            add(block, "coordination_stacking", "Abstract noun strings conceal the technical relationship. Name the object and its operation or measured change; retain independently defined dimensions, variables and constraints after contextual review.")
        for sentence in sentences(text):
            coordination = len(re.findall(r"\b(?:and|or)\b", sentence, re.I))
            properties = len(ABSTRACT_WORDS.findall(sentence))
            if re.search(r"\band\s*/\s*or\b", sentence, re.I) or coordination >= 3 or properties >= 3:
                add(block, "coordination_stacking", "Inspect each coordinated item for a distinct technical role. Express the dependency directly and specify conjunction or alternatives; keep necessary sets, constraints and measured properties.")
            if text.count("—") >= 2 and len(re.findall(r"[\u3400-\u9fff]", text)) >= 10:
                add(block, "ai_formulaic_prose", "Repeated em-dash chains replace syntax. State the input/output, condition or cause explicitly; mathematical minus signs and numeric ranges remain valid.")
        if block.get("kind", "prose") == "prose":
            current_sentences = sentences(text)
            openings = {}
            for sentence in current_sentences:
                if not enough_text(sentence, 8, 18):
                    continue
                english = re.findall(r"[A-Za-z]+", sentence.lower())
                chinese = re.match(r"[\u3400-\u9fff]{4,}", sentence)
                prefix = tuple(english[:3]) if len(english) >= 3 else (chinese.group()[:6] if chinese else "")
                if prefix:
                    openings[prefix] = openings.get(prefix, 0) + 1
            if any(count >= 3 for count in openings.values()):
                add(block, "mechanical_prose", "Repeated sentence scaffolds list operations or observations without developing their relationship. Rewrite the actual dependency; retain deliberate parallel definitions or independently specified conditions after contextual review.")
            for left, right in zip(current_sentences, current_sentences[1:]):
                if not (enough_text(left, 14, 25) and enough_text(right, 14, 25)):
                    continue
                # Pronouns can carry an explicit prior object forward; their
                # actual antecedents still require the manual prose pass.
                if re.match(r"^(?:(?:This|These|It|Its|Such)\b|该|其|上述|这一|这些)", right, re.I):
                    continue
                if not carries_object_forward(left, right):
                    add(block, "disconnected_prose", "Adjacent sentences introduce unrelated objects without a scientific dependency. Read their antecedents and state the actual input/output or inference, or move the second statement to its proper context.")

    body = [b for b in prose if b.get("kind", "prose") == "prose"]
    tables = actual_table_evidence(blocks)
    for block in body:
        values = numeric_values(block["text"])
        if len(values) < 6:
            continue
        for table in tables:
            matched = values & table["values"]
            if len(matched) < 6 or len(matched) / len(values) < .75:
                continue
            candidate = add(block, "table_replay",
                "At least six distinct prose values reproduce the same current table and cover at least 75% of this paragraph's values. Read the actual table and scientific argument together: retain decisive quantitative anchors or a necessary numerical derivation; replace row-by-row recital with the relationship, mechanism or condition it establishes.", table)
            if candidate:
                candidate["table_evidence"] = {"location": table["location"], "file": table["file"],
                    "table": table["table"], "matched_values": sorted(matched),
                    "matched_value_count": len(matched), "prose_value_count": len(values),
                    "table_value_count": len(table["values"]), "match_fraction": len(matched) / len(values)}
    previous_sentences = {}
    for block in body:
        for sentence in sentences(block["text"]):
            key = normalized(sentence)
            if enough_text(sentence, 8, 18) and key in previous_sentences:
                add(block, "redundant_prose", "The same scientific sentence appears elsewhere. Give the full finding one analysis location; other sections may synthesize its implication without repeating the sentence.", previous_sentences[key])
            previous_sentences.setdefault(key, block)
    for index, right in enumerate(body):
        for left in body[max(0, index-8):index]:
            if not (enough_text(left["text"], 25, 45) and enough_text(right["text"], 25, 45)):
                continue
            a, b = normalized(left["text"]), normalized(right["text"])
            if SequenceMatcher(None, a, b, autojunk=False).ratio() >= .88:
                add(right, "redundant_prose", "These paragraphs substantially repeat the same explanation. Retain one full analysis and replace the duplicate with the new relationship, if any.", left)
        if index == 0:
            continue
        left = body[index-1]
        # A table, equation, caption or heading is a deliberate structural
        # boundary. Do not equate section changes with missing continuity.
        adjacent = blocks.index(right) == blocks.index(left) + 1
        if not adjacent or right.get("boundary") or left.get("section") != right.get("section") or left.get("file") != right.get("file"):
            continue
        if not (enough_text(left["text"]) and enough_text(right["text"])):
            continue
        if not carries_object_forward(left["text"], right["text"]):
            add(right, "disconnected_prose", "Adjacent paragraphs carry no identifiable scientific object forward. Read them together and state the actual definition, input/output, discrepancy or inference linking them; a transition word alone supplies no relation.", left)

    review_items = (reviews or {}).get("reviews", [])
    errors = []
    review_map = {}
    if not isinstance(review_items, list):
        errors.append("reviews must be a list of source-bound decisions")
        review_items = []
    for entry in review_items:
        if not isinstance(entry, dict) or not entry.get("candidate_id"):
            errors.append("each review requires candidate_id, decision and a scientific reason")
            continue
        if entry["candidate_id"] in review_map:
            errors.append("duplicate review decision for " + str(entry["candidate_id"]))
            continue
        review_map[entry["candidate_id"]] = entry
    current_ids = {c["candidate_id"] for c in candidates}
    for candidate in candidates:
        decision = review_map.get(candidate["candidate_id"])
        if not decision:
            continue
        reason = decision.get("reason", "")
        if decision.get("decision") == "scientific_content" and specific_scientific_reason(reason, candidate):
            candidate["review_status"] = "retained_scientific_content"
            candidate["review_reason"] = reason.strip()
        else:
            errors.append("candidate " + candidate["candidate_id"] + ": a live candidate must be rewritten and rescanned, or retained with decision=scientific_content and a reason naming its actual object and scientific relation")
    stale_count = len(set(review_map) - current_ids)
    unresolved = sum(c["review_status"] == "unresolved" for c in candidates)
    return {"manuscript_editorial_status": "needs_revision" if unresolved or errors else ("clear_after_review" if candidates else "clear"),
            "editorial_candidate_count": len(candidates), "unresolved_editorial_count": unresolved,
            "editorial_candidates": candidates, "editorial_review_errors": errors,
            "stale_review_count": stale_count,
            "editorial_note": "Candidates require scientific context review; no automatic deletion or authorship inference. Rewritten text must be rescanned. Scientific exemptions bind to current text, location, neighboring context and any actual related evidence."}


def read_reviews(path: str | Path | None) -> dict | None:
    if not path:
        return None
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("editorial review decisions must be a JSON object")
    return value
