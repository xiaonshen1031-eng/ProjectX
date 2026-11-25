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
    ("experimental_process_leakage", re.compile(
        r"\b(?:this|the|their)\s+(?:cross[- ]source\s+discrepancy|checkpoint\s+correspondence|"
        r"(?:original\s+)?(?:checkpoint|log|file)\s+(?:mapping|recovery|verification))\s+"
        r"(?:is|remains?)\s+(?:unresolved|pending|unverified)\b|"
        r"\b(?:original|old|archival|cloud)\s+(?:run\s+)?(?:checkpoints?|logs?|source files?)\b"
        r".{0,65}\b(?:unavailable|missing|lost|not recovered|cannot be recovered)\b|"
        r"(?:检查点|原始日志|原运行日志|云端日志|源文件)(?:对应关系|映射|恢复|核查)?.{0,20}"
        r"(?:尚未解决|仍未解决|尚未恢复|仍待确认|待核验|无法恢复)|"
        r"(?:跨来源|跨源)(?:数值)?差异.{0,15}(?:尚未解决|仍未解决|仍待确认)", re.I),
     "Keep archival-recovery and verification status in the author record. In clean prose state the actual reported values, comparison unit and supported scope. Preserve material discrepancies and mandatory availability disclosures; do not invent their causes or remove the conflicting values."),
    ("self_evaluative_prose", re.compile(
        r"\b(?:our|this|the present)\s+(?:research|study|work|contribution)\s+(?:is|remains?)\s+"
        r"(?:weak|unconvincing|of little value|not novel|only incremental)\b|"
        r"\b(?:our|the proposed)\s+(?:method|model|approach)\s+(?:performs? poorly|is inferior)\b|"
        r"(?:本文|本研究|我们的研究|所提方法).{0,12}(?:价值不大|创新性不足|缺乏创新|表现很差|表现不好|研究薄弱)", re.I),
     "Replace a verdict about the study's worth with the exact evaluated comparison and its scientific consequence. Preserve adverse values, conditions and source attribution; do not substitute promotional praise."),
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
        r"回归测试通过|校验通过|完成状态|调参记录|实验验收)|"
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
    ("experimental_report_prose", re.compile(
        r"\b(?:the|these|our)\s+(?:experimental\s+)?(?:results|findings)\s+(?:are|can be)\s+"
        r"(?:shown|seen|found|presented)\s+in\s+(?:Figure|Fig\.|Table)\s*\d+(?:[.\-‑–]\d+)*\s*[.!]|"
        r"(?:^|[。！？]\s*)(?:相关|相应|上述)?(?:实验|测试|对比)?结果(?:如|见|展示于|呈现于)"
        r"(?:图|表)\s*\d+(?:[.\-‑–]\d+)*\s*[。.]", re.I),
     "A location-only sentence adds no scientific relationship. Explain what the cited quantity changes, or attach the reference directly to the finding; retain substantive captions and definitions."),
    ("experimental_report_prose", re.compile(
        r"\b(?:these|the (?:above|foregoing)) (?:results|findings) (?:further )?"
        r"(?:confirm|demonstrate|validate|verify) (?:the )?"
        r"(?:effectiveness|superiority|feasibility|robustness) of (?:the )?"
        r"(?:(?:proposed|presented|developed) )?(?:method|model|approach|algorithm|framework)\s*(?:[.!?]|$)|"
        r"(?:上述|以上|这些|该)(?:结果|现象|对比)(?:进一步|充分|再次)?(?:验证|证实|证明|表明)(?:了)?"
        r"(?:所提(?:出的)?|本文(?:所)?提出的|该)(?:方法|模型|算法|框架)的"
        r"(?:有效性|优越性|可行性|鲁棒性)\s*(?:[。！？]|$)", re.I),
     "Replace a generic validation conclusion with the compared quantity, evaluated condition and supported consequence. Keep a specific feasibility or uncertainty statement where it changes interpretation."),
    ("experimental_process_leakage", re.compile(
        r"\b(?:the|this) (?:figure|plot|manuscript|document)\b.{0,50}\b(?:regenerated|"
        r"reformatted|saved as|exported to|converted to|verification passed)\b|"
        r"(?:图片|图像|文档|稿件).{0,30}(?:重新生成|重新排版|另存为|已导出|已转换)", re.I),
     "Keep figure generation, document formatting and saved-file receipts in the production sidecar; the caption and body describe scientific content."),
)

# These phrases are rhetorical framing, unlike a mathematical negation such
# as "does not imply" or a timed information constraint. A review reason may
# explain a genuine scientific use, but cannot approve this live framing.
REWRITE_ONLY_RE = re.compile(
    r"\b(?:we do not claim|this does not undermine|"
    r"despite this limitation|remains valid despite|just a simple|only an incremental)\b|"
    r"\bdoes not affect the validity of\s+(?:our|this|the present|the proposed|the)\s+"
    r"(?:research|study|work|method|model|approach|contribution|framework)\b|"
    r"(?:虽然|尽管).{0,90}(?:不能|无法|不足|局限).{0,90}(?:但|仍).{0,20}(?:价值|有用|有效)|"
    r"(?:本文|本研究)(?:不声称)|这并不影响.{0,20}(?:有效性|研究价值)|"
    r"(?:我们的研究|本研究|本文).{0,12}(?:价值不大|创新性不足|缺乏创新|研究薄弱)", re.I)

# Match operational artifacts together with an operational state, not the
# words "log", "checkpoint" or a mathematical negation on their own. These
# cases cannot be approved by an impressive-sounding scientific review reason.
INTERNAL_ARTIFACT_EN = (
    r"(?:\b(?:run|training|experiment(?:al)?|job)\s+(?:logs?|artifacts?|records?|traces?)\b|"
    r"\b(?:original|old|archival|cloud|internal)\s+(?:run\s+)?(?:checkpoints?|source\s+files?)\b|"
    r"\bcheckpoint\s+(?:correspondence|mapping|matching|recovery|verification)\b|"
    r"\b(?:cross[- ]source\s+discrepancy)\b)"
)
GENERIC_RECORD_EN = r"\b(?:original|old|archival|internal|historical)\s+(?:records?|artifacts?)\b"
INTERNAL_CONTEXT_EN = re.compile(r"\b(?:training|checkpoints?|jobs?|cloud|run logs?)\b", re.I)
INTERNAL_STATE_EN = (
    r"(?:\s+(?:is|are|was|were|remains?|remained|have been|has been)\s+"
    r"(?:(?:still|currently|temporarily|now|already)\s+)*"
    r"(?:unavailable|inaccessible|lost|deleted|unverified|unresolved|pending|"
    r"not\s+(?:yet\s+)?(?:retained|kept|recovered|accessible|available|verified|reconciled|backed up)|"
    r"no longer\s+(?:accessible|available|retained)|"
    r"missing(?=\s*(?:[.;,]|$|from\b|after\b|since\b|because\b|so\b)))\b|"
    r"\s+(?:have|has|had)\s+not\s+(?:yet\s+)?been\s+(?:recovered|retained|verified|backed up)\b|"
    r"\s+(?:cannot|can\s+not|could\s+not)\s+be\s+"
    r"(?:accessed|retrieved|recovered|located|verified|reconciled|matched)\b|"
    r"\s+(?:disappeared|went\s+missing)\b)"
)


def _internal_status_pattern(artifact: str) -> re.Pattern:
    return re.compile(
        artifact + INTERNAL_STATE_EN + r"|"
        r"\b(?:cannot|could not|unable to|failed to)\s+"
        r"(?:retrieve|recover|obtain|access|verify|reconcile|locate|match)\b.{0,65}" + artifact + r"|"
        r"\b(?:we|the authors?)\s+(?:lack|lacked|have\s+no)\s+access\s+to\s+"
        r"(?:(?:the|our|original)\s+){0,3}" + artifact + r"|"
        r"\b(?:we|the authors?)\s+(?:are|were)\s+(?:(?:still|currently|now)\s+)?"
        r"(?:recovering|retrieving|reconstructing|reconciling|searching for)\b.{0,55}" + artifact,
        re.I)


INTERNAL_STATUS_EN = _internal_status_pattern(INTERNAL_ARTIFACT_EN)
GENERIC_RECORD_STATUS_EN = _internal_status_pattern(GENERIC_RECORD_EN)
INTERNAL_ARTIFACT_ZH = (
    r"(?:原始运行日志|原(?:始)?训练(?:日志|记录|产物)|历史训练记录|旧运行记录|"
    r"云端(?:实验|运行)?(?:日志|记录|检查点)|训练产物|内部(?:实验|运行)?(?:日志|记录)|"
    r"实验运行日志|检查点(?:的)?(?:对应关系|映射|核对|匹配|恢复))"
)
INTERNAL_STATE_ZH = (
    r"(?:尚未解决|仍未解决|尚未恢复|仍待确认|待核验|待核对|无法核验|无法核对|"
    r"无法恢复|不可访问|不可用|无法获取|无法调取|暂不可查|丢失|未保留|未恢复|"
    r"尚未找回|正在恢复|正在找回|尚未回传|待同步|待找回)"
)
INTERNAL_STATUS_ZH = re.compile(
    INTERNAL_ARTIFACT_ZH + r".{0,22}" + INTERNAL_STATE_ZH + r"|"
    r"(?:无法获取|无法调取|无法恢复|正在恢复|正在找回).{0,15}" + INTERNAL_ARTIFACT_ZH + r"|"
    r"(?:运行日志|原始日志).{0,12}(?:尚未恢复|正在恢复|待回传|待核对|待归档|仍在找回|待找回)")
RESTRICTED_RELEASE_EN = re.compile(
    r"(?:" + INTERNAL_ARTIFACT_EN + r"|" + GENERIC_RECORD_EN + r")"
    r"\s+(?:is|are|was|were)\s+"
    r"(?:(?:unavailable|inaccessible|not available)\s+(?:for public (?:release|sharing|access)|to the public|to external users)|"
    r"not publicly available)\s+"
    r"(?:under|due to|because of|pursuant to)\s+(?:(?:the|a|an)\s+)?"
    r"(?:data[- ]use agreement|licen[cs]e|privacy policy|privacy agreement|ethics policy|consent agreement|institutional policy|contract)\b",
    re.I)

# A model's information set is scientific content, even when it excludes
# training logs. Keep this exception local to the complete input-condition
# clause; an archive-loss explanation or an author-access problem is different.
SCIENTIFIC_INPUT_ACCESS_EN = re.compile(
    INTERNAL_ARTIFACT_EN + r"\s+(?:is|are)\s+"
    r"(?:unavailable|inaccessible|not\s+(?:available|accessible))\s+to\s+"
    r"(?:(?:the|a|an|our)\s+)?(?:classifier|predictor|controller|estimator|router|agent|model|algorithm)"
    r"\s+(?:at|during)\s+(?:deployment|inference|prediction|forecast\s+issuance|decision\s+time)"
    r"(?=\s*[,;.!?]|\s*$)", re.I)
INPUT_ARCHIVE_FAILURE_EN = re.compile(
    r"\b(?:they|these|those|the\s+(?:logs?|records?|artifacts?|traces?))\s+"
    r"(?:(?:are|were|have\s+been|had\s+been)\s+)?"
    r"(?:lost|deleted|destroyed|missing|not\s+retained|not\s+recovered|unrecovered)\b|"
    r"\b(?:we|the\s+authors?)\s+(?:cannot|could\s+not|failed\s+to)\s+"
    r"(?:recover|retrieve|locate|access)\s+(?:them|these|those)\b", re.I)


def internal_status_spans(text: str) -> list[tuple[int, int]]:
    """Locate clear recovery/status prose, including paraphrases and heading tricks.

    A real data-access restriction is context-reviewable. It must name the
    access action and its actual policy in the same sentence; adding a generic
    disclosure heading or a privacy sentence cannot approve an unrelated log
    recovery status. Scientific uses of logs/checkpoints are not matched alone.
    """
    spans = []
    cursor = 0
    for sentence in sentences(text):
        offset = text.find(sentence, cursor)
        cursor = offset + len(sentence)
        matches = list(INTERNAL_STATUS_EN.finditer(sentence)) + list(INTERNAL_STATUS_ZH.finditer(sentence))
        if INTERNAL_CONTEXT_EN.search(sentence):
            matches += list(GENERIC_RECORD_STATUS_EN.finditer(sentence))
        restricted = list(RESTRICTED_RELEASE_EN.finditer(sentence))
        restricted += [condition for condition in SCIENTIFIC_INPUT_ACCESS_EN.finditer(sentence)
                       if not INPUT_ARCHIVE_FAILURE_EN.search(sentence[condition.end():])]
        for match in matches:
            # A policy concerning unrelated data cannot excuse lost artifacts.
            # Only an access restriction or complete model-input condition
            # containing this exact span is scientific availability content.
            # Lost/deleted/recovery states never match either exception.
            if any(r.start() <= match.start() and r.end() >= match.end() for r in restricted):
                continue
            spans.append((offset + match.start(), offset + match.end()))
    return sorted(set(spans))


def definite_internal_status(text: str) -> bool:
    return bool(internal_status_spans(text))


RECORD_SUBJECT_EN = (r"(?:(?:the|these|those|our|your|original|raw|training|run|job|experimental|all)\s+){0,6}"
                     r"(?:logs?|records?|checkpoints?|artifacts?|traces?|source\s+files?)")
RECORD_STATE_EN = r"(?:retained|kept|stored|saved|preserved|archived|deleted|lost|destroyed|available|accessible|publicly available)\b"
RECORD_LOCATION_EN = r"(?:stored|kept|archived|saved|located)\b"
RECORD_REQUEST_PATTERNS = (
    re.compile(r"\b(?:have|has|had|were|are|was|is)\s+" + RECORD_SUBJECT_EN + r"\s+(?:been\s+)?(?:not\s+)?" + RECORD_STATE_EN, re.I),
    re.compile(r"\b(?:state|disclose|report|confirm|indicate|specify|clarify)\s+(?:whether|if)\s+"
               + RECORD_SUBJECT_EN + r"\s+(?:have|has|had|were|are|was|is)\s+(?:been\s+)?(?:not\s+)?" + RECORD_STATE_EN, re.I),
    re.compile(r"\b(?:state|disclose|report|confirm|indicate|specify|clarify)\s+where\s+"
               + RECORD_SUBJECT_EN + r"\s+(?:were|are|was|is)\s+" + RECORD_LOCATION_EN, re.I),
    re.compile(r"\bwhere\s+(?:were|are|was|is)\s+" + RECORD_SUBJECT_EN
               + r"(?:\s+" + RECORD_LOCATION_EN + r")?\s*[?.]", re.I),
    re.compile(r"\b(?:state|provide|disclose|report|describe)\s+(?:the\s+)?"
               r"(?:retention status|availability|storage location|access conditions|location|whereabouts)\s+of\s+"
               + RECORD_SUBJECT_EN, re.I),
    re.compile(r"\b(?:how|where)\s+(?:can|may)\s+(?:we|readers|reviewers|one)\s+"
               r"(?:access|obtain|retrieve|download)\s+" + RECORD_SUBJECT_EN, re.I),
    re.compile(r"\b(?:please\s+)?(?:provide|share|release)\s+" + RECORD_SUBJECT_EN
               + r"\s*(?:[.!?]|for inspection\b|to the reviewers\b)", re.I),
    re.compile(r"(?<![无不未])(?:请|须|必须|要求|应当?|需).{0,8}(?:说明|披露|报告|确认).{0,18}"
               r"(?:日志|记录|检查点|实验产物|源文件)(?:是否|有无)(?:被)?"
               r"(?:保留|留存|保存|归档|销毁|丢失|可用|可访问|公开|可提供)"),
    re.compile(r"(?<![无不未])(?:请|须|必须|要求|应当?|需).{0,8}(?:说明|披露|报告|提供|确认).{0,18}"
               r"(?:日志|记录|检查点|实验产物|源文件)(?:的)?"
               r"(?:保存位置|存放地点|存放位置|留存状态|访问方式|可用性|可访问性)"),
)
RECORD_REQUEST_CONTINUATION = re.compile(
    r"\b(?:and|or)\s+(?:whether|if)\s+" + RECORD_SUBJECT_EN
    + r"\s+(?:have|has|had|were|are|was|is)\s+(?:been\s+)?(?:not\s+)?" + RECORD_STATE_EN, re.I)


def record_objects(text: str) -> set[str]:
    groups = {
        "log": r"\blogs?\b|日志", "record": r"\brecords?\b|记录",
        "checkpoint": r"\bcheckpoints?\b|检查点", "artifact": r"\bartifacts?\b|实验产物|训练产物",
        "source_file": r"\bsource\s+files?\b|源文件",
        "trace": r"\btraces?\b|作业轨迹|运行轨迹",
    }
    return {kind for kind, pattern in groups.items() if re.search(pattern, text, re.I)}


def requested_record_objects(quote: str) -> set[str]:
    """Require a record-subject retention/access/location predicate, not keywords."""
    request = re.search(r"\b(?:please|must|required|shall|whether|state|disclose|report|provide)\b|[?？]|请|必须|要求|应|需|说明|披露", quote, re.I)
    if not request:
        return set()
    asked = set()
    matches = [(match, False) for pattern in RECORD_REQUEST_PATTERNS for match in pattern.finditer(quote)]
    matches += [(match, True) for match in RECORD_REQUEST_CONTINUATION.finditer(quote)]
    affirmative = []
    for match, continuation in sorted(matches, key=lambda item: item[0].start()):
        prefix = re.split(r"[.!?。！？;；\n]|\b(?:but|however|whereas)\b|但是|然而", quote[:match.start()], flags=re.I)[-1]
        clause_start = match.start() - len(prefix)
        if continuation and not any(start >= clause_start for start in affirmative):
            continue
        # Negation of the request differs from asking whether a record was
        # not retained. Inspect only the governing request, not its payload.
        if re.search(r"(?:\b(?:do\s+not|don't|must\s+not|shall\s+not|should\s+not|need\s+not|"
                     r"not\s+required\s+to|no\s+(?:need|requirement)\s+to|avoid|omit|exclude)\b)"
                     r"(?:\W+\w+){0,6}\W*$", prefix, re.I):
            continue
        chinese_request = re.match(r".*?(?:说明|披露|报告|提供|确认)", match.group())
        if chinese_request and re.search(r"请(?:勿|不要|别)|不必|无需|不得|禁止|不要求", chinese_request.group()):
            continue
        asked.update(record_objects(match.group()))
        affirmative.append(match.start())
    return asked


def requirement_quote_contexts(source: str, quote: str) -> list[str]:
    """Read the full source sentence containing each exact quote occurrence.

    A short excerpt cannot drop a governing 'do not'. Repeated excerpts with
    conflicting instructions need an unambiguous fuller quotation and review.
    This is a local correspondence check, not an authority or intent parser.
    """
    source = " ".join(source.split())
    quote = " ".join(quote.split())
    contexts = []
    for match in re.finditer(re.escape(quote), source):
        before = list(re.finditer(r"[.!?。！？;；]", source[:match.start()]))
        start = before[-1].end() if before else 0
        end = match.end()
        if source[end-1] not in '.!?。！？;；':
            after = re.search(r"[.!?。！？;；]", source[end:])
            end = end + after.end() if after else len(source)
        contexts.append(source[start:end].strip())
    return contexts

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
ARTIFACT_NUMBER = r"\d+(?:[.\-‑–]\d+)*[a-z]?(?!\d|[.\-‑–]\d)"
ARTIFACT_RE = re.compile(rf"(?:\b(?:Figure|Fig\.|Table)|图|表)\s*{ARTIFACT_NUMBER}", re.I)
CHINESE_COORDINATION_RE = re.compile(r"(?<=[\u3400-\u9fff])\s*(?:以及|和(?!谐|平)|(?<!参)与)\s*(?=[\u3400-\u9fff])")
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
    r"(?<![A-Za-z0-9_.])[-+−]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][-+]?\d+)?"
    r"(?![A-Za-z0-9_]|\.\d)(?:\s*\\?%)?"
)
CALENDAR_RE = re.compile(
    r"(?<!\d)(?:(?:19|20|21)\d{2}\s*年(?:\s*\d{1,2}\s*月(?:\s*\d{1,2}\s*[日号])?)?|"
    r"\d{1,2}\s*月\s*\d{1,2}\s*[日号])(?:\s*\d{1,2}\s*时(?:\s*\d{1,2}\s*分)?)?|"
    r"(?<!\d)(?:19|20|21)\d{2}[-/]\d{1,2}[-/]\d{1,2}(?!\d)|"
    r"(?<![\d:])(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?(?![\d:])"
)


def numeric_values(text: str) -> set[str]:
    """Comparable literal values, excluding citations, artifact IDs and calendar labels.

    Decimal normalization equates 1.110 with 1.11, but never guesses rounding,
    units, percentage scaling, scientific symbols or calculated equivalence.
    """
    text = re.sub(r"\[\s*\d+(?:\s*[,;–-]\s*\d+)*\s*\]", "", text)
    text = CALENDAR_RE.sub(" ", ARTIFACT_RE.sub(" ", text))
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
    relation = re.search(r"\b(?:defines?|defined|definitions?|denotes?|specifies?|specified|states?|stated|because|constraints?|"
                         r"conditions?|conjunctions?|alternatives?|dimensions?|variables?|measured|measurements?|"
                         r"observed|observations?|compared|compares?|comparisons?|contrasts?|relates?|related|relations?|relationships?|"
                         r"balances?|balanced|balancing|constrains?|constrained|cited|sources?|operators?|equations?|feasible|"
                         r"information|inputs?|outputs?|assumptions?|disclosures?|requires?|requirements?|estimates?|estimated)\b|"
                         r"定义|条件|约束|变量|维度|输入|输出|比较|观测|测量|公式|引用|文献|来源|算子|假设|披露", reason, re.I)
    return bool(relation and anchors & substantive_tokens(reason))


def required_record_disclosure(entry: dict, candidate: dict) -> tuple[bool, str]:
    """Check a narrow, externally required record-status answer.

    This verifies current source/quote correspondence, not source authenticity
    or whether the venue actually requires the disclosure; those remain manual
    checks. General scientific objections are not record-retention requests.
    """
    if (candidate.get("type") != "experimental_process_leakage"
            or not definite_internal_status(candidate.get("original_text", ""))):
        return False, "required_disclosure is restricted to record/status disclosure, not rhetorical framing"
    reason = entry.get("reason", "")
    if not specific_scientific_reason(reason, candidate):
        return False, "required_disclosure needs a specific reason linking the current record fact to its disclosure requirement"
    quote = entry.get("requirement_quote", "")
    source = entry.get("requirement_source", "")
    if not isinstance(quote, str) or len(quote.strip()) < 8 or not isinstance(source, str) or not source.strip():
        return False, "required_disclosure needs requirement_source and an exact requirement_quote"
    try:
        path = Path(source)
        if not path.is_absolute() or not path.is_file() or path.stat().st_size > 2_000_000:
            return False, "requirement_source must be a readable local source file (absolute or resolved by read_reviews)"
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError, ValueError):
        return False, "requirement_source cannot be read as the stated UTF-8 source"
    compact = lambda value: " ".join(value.split())
    if compact(quote) not in compact(text):
        return False, "requirement_quote does not match the current requirement_source"
    asked = requested_record_objects(quote)
    for context in requirement_quote_contexts(text, quote):
        asked.intersection_update(requested_record_objects(context))
    if not asked:
        return False, "the quoted source must explicitly request record retention, location or availability; a general scientific objection is insufficient"
    text = candidate["original_text"]
    spans = internal_status_spans(text)
    for start, end in spans:
        objects = record_objects(text[start:end])
        if not objects or not objects.issubset(asked):
            return False, "the record requirement does not cover every status in this candidate; separate the requested answer from other operational status"
    residual = list(text)
    for start, end in spans:
        residual[start:end] = ' ' * (end - start)
    residual = ''.join(residual)
    if any(pattern.search(residual) for kind, pattern, _ in RULES if kind == "experimental_process_leakage"):
        return False, "required_disclosure covers only the requested record-status clause; separate or rewrite the additional process/production prose"
    return True, ""


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
        if (kind == "self_evaluative_prose"
                or (kind == "defensive_prose" and REWRITE_ONLY_RE.search(block["text"]))
                or (kind == "experimental_process_leakage" and definite_internal_status(block["text"]))):
            item["review_policy"] = "rewrite_required"
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
        # Pure operational status remains a live defect even under a heading
        # named "Disclosure". Genuine required access statements are handled
        # by the sentence-level policy exception above, not by heading alone.
        if definite_internal_status(text):
            add(block, "experimental_process_leakage",
                "Rewrite internal log/artifact recovery and verification status as the actual comparison, protocol and supported scope. Keep operational recovery records separately; retain material discrepancies and required access disclosures without inventing their causes.")
        for kind, pattern, advice in RULES:
            if pattern.search(text):
                add(block, kind, advice)
        if QUOTE_RE.search(text):
            add(block, "ai_formulaic_prose", "A quoted label needs an established source or a precise operational definition. Remove decorative naming; retain genuine cited or defined terminology.")
        if CHINESE_ABSTRACT_STACK_RE.search(text):
            add(block, "coordination_stacking", "Abstract noun strings conceal the technical relationship. Name the object and its operation or measured change; retain independently defined dimensions, variables and constraints after contextual review.")
        for sentence in sentences(text):
            coordination = len(re.findall(r"\b(?:and|or)\b", sentence, re.I))
            properties = len(ABSTRACT_WORDS.findall(sentence))
            chinese_coordination = len(CHINESE_COORDINATION_RE.findall(sentence))
            if re.search(r"\band\s*/\s*or\b", sentence, re.I) or max(coordination, chinese_coordination, properties) >= 3:
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
        if not isinstance(entry, dict) or not isinstance(entry.get("candidate_id"), str) or not entry["candidate_id"].strip():
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
        if decision.get("decision") == "required_disclosure":
            accepted, error = required_record_disclosure(decision, candidate)
            if accepted:
                candidate["review_status"] = "retained_required_disclosure"
                candidate["review_reason"] = reason.strip()
                candidate["requirement_source"] = decision["requirement_source"]
                candidate["requirement_quote"] = decision["requirement_quote"]
            else:
                errors.append("candidate " + candidate["candidate_id"] + ": " + error)
        elif candidate.get("review_policy") == "rewrite_required":
            errors.append("candidate " + candidate["candidate_id"] + ": explicit rhetorical framing or internal operational status must be rewritten in the source; a scientific-content reason cannot waive its live wording")
        elif decision.get("decision") == "scientific_content" and specific_scientific_reason(reason, candidate):
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
    # Requirement files travel with the review decision file, not the process
    # working directory. Inline callers can supply absolute requirement paths.
    for entry in value.get("reviews", []) if isinstance(value.get("reviews", []), list) else []:
        if isinstance(entry, dict) and isinstance(entry.get("requirement_source"), str):
            source = Path(entry["requirement_source"])
            if not source.is_absolute():
                entry["requirement_source"] = str((Path(path).resolve().parent / source).resolve())
    return value
