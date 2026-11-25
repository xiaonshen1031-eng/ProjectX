"""Project prose, technical exceptions and actual DOCX final-gate tests."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_writing_quality as word_screen
from manuscript_prose_rules import editorial_screen, numeric_values, read_reviews


def screen(text, reviews=None, section="结果分析"):
    blocks = [{"location": "paragraph:1", "kind": "prose", "section": section, "text": text}]
    return editorial_screen(blocks, "project", reviews)


class ProjectWritingTests(unittest.TestCase):
    def test_chinese_coordination_needs_context(self):
        result = screen("报告分析负荷形态和调节能力与运行风险以及恢复特征。")
        self.assertIn("coordination_stacking", {c["type"] for c in result["editorial_candidates"]})
        result = screen("方案比较储能与空调的参与小时。")
        self.assertNotIn("coordination_stacking", {c["type"] for c in result["editorial_candidates"]})

    def test_location_only_reference_uses_the_complete_chapter_number(self):
        self.assertIn("experimental_report_prose", {
            c["type"] for c in screen("对比结果见图3.4-2。")["editorial_candidates"]
        })
        text = "图3.4-2记录了空调首次恢复的时刻，峰值出现在第二个刻钟。"
        self.assertEqual(screen(text)["editorial_candidate_count"], 0)
        self.assertEqual(numeric_values("表3.4-2中由12.417降至9.609，按0.25小时累计。"),
                         {"12.417", "9.609", "0.25"})

    def test_chapter_number_does_not_turn_analysis_into_a_caption(self):
        document = Document()
        document.add_paragraph("图3.4-2 供电缺额时间序列", style="Caption")
        document.add_paragraph("图3.4-2 中的峰值与蒙西输送受限的时段一致。")
        document.add_paragraph("表3.5-1 的恢复电量由逐刻钟回补功率积分得到。")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.docx"
            document.save(path)
            blocks = word_screen.load_editorial_blocks(path, word_screen.load_paragraphs(path))
        self.assertEqual([block["kind"] for block in blocks], ["caption", "prose", "prose"])

    def test_calendar_labels_do_not_supply_table_replay_matches(self):
        text = "用2025年出力比较2035年12月23日18时的缺额。2024-12-23 18:00对应2至6天的候选差异。"
        self.assertEqual(numeric_values(text), {"2", "6"})
        self.assertEqual(numeric_values("5年回收期，设备在18小时内完成恢复。"), {"5", "18"})

    def test_reviewable_technical_constraint_and_actual_adverse_result(self):
        for text in [
            "可行解的存在不能推出唯一性。",
            "在低负荷时段，基准方案把平均误差从0.26降至0.21。",
            "控制器根据站内运行日志计算过去15 min的负荷均值。",
            "Training logs are unavailable to the controller during inference.",
        ]:
            result = screen(text)
            self.assertFalse(any(c.get("review_policy") == "rewrite_required"
                                 for c in result["editorial_candidates"]), text)

    def test_reassurance_and_recovery_cannot_be_waived_by_scientific_words(self):
        for text in [
            "虽然模型无法解释午峰，但仍具有参考价值。",
            "原始训练日志尚未恢复。",
            "The original checkpoints were lost.",
        ]:
            result = screen(text, section="资料披露")
            self.assertTrue(result["unresolved_editorial_count"], text)
            reviews = {"reviews": [
                {"candidate_id": c["candidate_id"], "decision": "scientific_content",
                 "reason": "这些资料定义了午峰模型、训练日志的使用条件以及 original checkpoints 的比较来源。"}
                for c in result["editorial_candidates"]
            ]}
            checked = screen(text, reviews, section="资料披露")
            self.assertGreater(checked["unresolved_editorial_count"], 0)
            self.assertTrue(checked["editorial_review_errors"])

    def test_required_disclosure_resolves_relative_source_and_checks_object_and_polarity(self):
        text = "原始训练日志未保留。"
        candidate, = screen(text)["editorial_candidates"]
        quote = "报告应说明原始训练日志是否保留。"
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            source = directory / "requirements.txt"
            submission = directory / "reviews.json"
            item = {
                "candidate_id": candidate["candidate_id"], "decision": "required_disclosure",
                "reason": "原始训练日志的留存情况是任务书要求的披露内容。",
                "requirement_source": source.name, "requirement_quote": quote,
            }
            submission.write_text(json.dumps({"reviews": [item]}, ensure_ascii=False), encoding="utf-8")
            source.write_text(quote, encoding="utf-8")
            checked = screen(text, read_reviews(submission))
            self.assertFalse(checked["unresolved_editorial_count"], checked)
            self.assertEqual(checked["editorial_candidates"][0]["review_status"],
                             "retained_required_disclosure")
            item["requirement_quote"] = "说明原始训练日志是否保留。"
            submission.write_text(json.dumps({"reviews": [item]}, ensure_ascii=False), encoding="utf-8")
            source.write_text("请不要" + item["requirement_quote"], encoding="utf-8")
            self.assertGreater(screen(text, read_reviews(submission))["unresolved_editorial_count"], 0)
            other = "请说明原始检查点是否保留。"
            source.write_text(other, encoding="utf-8")
            item["requirement_quote"] = other
            submission.write_text(json.dumps({"reviews": [item]}, ensure_ascii=False), encoding="utf-8")
            self.assertGreater(screen(text, read_reviews(submission))["unresolved_editorial_count"], 0)

    def test_malformed_candidate_ids_report_a_review_error(self):
        result = screen("原始训练日志未保留。", {"reviews": [{"candidate_id": {"id": 1}}]})
        self.assertTrue(result["editorial_review_errors"])

    def test_docx_cli_remains_read_only_and_draft_exit_is_advisory(self):
        document = Document()
        document.add_heading("资料披露", 1)
        document.add_paragraph("原始训练日志尚未恢复。")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "report.docx"
            document.save(path)
            original = path.read_bytes()
            command = [sys.executable, "-B", str(ROOT / "scripts" / "check_writing_quality.py"), str(path)]
            draft = subprocess.run(command, capture_output=True, check=True)
            strict = subprocess.run([*command, "--require-clean"], capture_output=True)
            self.assertEqual(strict.returncode, 2, strict.stderr)
            result = json.loads(draft.stdout)
            self.assertEqual(result["manuscript_mode"], "project")
            self.assertGreater(result["unresolved_editorial_count"], 0)
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
