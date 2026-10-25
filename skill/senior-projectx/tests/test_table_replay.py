from __future__ import annotations
from pathlib import Path
import subprocess, sys, tempfile, unittest
from docx import Document
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_writing_quality as word_screen
from manuscript_prose_rules import editorial_screen, numeric_values


VALUES = ["1.11", "2.22", "3.33", "4.44", "5.55", "6.66"]

def replay_text(values=VALUES):
    return "Table 1 reports residual losses of " + ", ".join(values) + ", respectively."

def shared_blocks(values=VALUES, text=None):
    return [{"location": "table:1/row:1/cell:" + str(i), "text": value,
             "kind": "table", "section": "results", "table": 1, "row": 1, "cell": i}
            for i, value in enumerate(values, 1)] + [
        {"location": "paragraph:2", "text": "Residual losses quantify point forecast error.", "section": "results"},
        {"location": "paragraph:3", "text": "Each residual is the absolute difference between forecast and observation.", "section": "results"},
        {"location": "paragraph:4", "text": text or replay_text(), "section": "results"}]

class ReplayFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def word(self, tables=None, text=None, caption=False):
        doc = Document()
        doc.add_heading("3 Results", level=1)
        for values in tables or []:
            table = doc.add_table(rows=1, cols=len(values))
            for cell, value in zip(table.rows[0].cells, values):
                cell.text = value
        if caption:
            doc.add_paragraph("Figure 1. " + replay_text())
        else:
            doc.add_paragraph(text or replay_text())
        path = self.directory / "manuscript.docx"
        doc.save(path)
        return path

    def replay(self, result):
        return [c for c in result["editorial_candidates"] if c["type"] == "table_replay"]

class ActualTableReplayTests(ReplayFixture):
    def test_actual_table_replay_reaches_all_three_word_branches(self):
        path = self.word([VALUES])
        for branch in ("project",):
            with self.subTest(branch=branch):
                result = word_screen.inspect_writing(path, manuscript_mode=branch)
                candidate = self.replay(result)[0]
                self.assertEqual(candidate["related_location"], "table:1")
                self.assertEqual(candidate["table_evidence"]["matched_value_count"], 6)
                self.assertIn("table:1/row:1/cell:6: 6.66", candidate["related_text"])
                self.assertEqual(candidate["table_evidence"]["match_fraction"], 1)

    def test_actual_table_replay_blocks_each_word_final_gate_but_draft_is_compatible(self):
        path = self.word([VALUES])
        for branch in ("project",):
            with self.subTest(branch=branch):
                cmd = [sys.executable, "-B", str(ROOT / "scripts/check_writing_quality.py"),
                       str(path), "--manuscript-mode", branch]
                self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
                self.assertEqual(subprocess.run(cmd + ["--require-clean"], capture_output=True).returncode, 2)

    def test_six_values_without_an_actual_table_are_not_replay(self):
        self.assertFalse(self.replay(word_screen.inspect_writing(self.word())))

    def test_different_table_values_are_not_replay(self):
        self.assertFalse(self.replay(word_screen.inspect_writing(self.word([["7.77", "8.88", "9.99", "10.10", "11.11", "12.12"]]))))

    def test_two_decisive_anchors_are_not_replay(self):
        result = word_screen.inspect_writing(self.word([VALUES], "Residual MAE decreases from 6.66 to 1.11 after the demand transition."))
        self.assertFalse(self.replay(result))

    def test_values_from_two_tables_are_not_combined(self):
        self.assertFalse(self.replay(word_screen.inspect_writing(self.word([VALUES[:3], VALUES[3:]]))))

    def test_threshold_requires_six_distinct_matches(self):
        self.assertFalse(self.replay(editorial_screen(shared_blocks(VALUES[:5], replay_text(VALUES[:5])), "project")))
        self.assertEqual(len(self.replay(editorial_screen(shared_blocks(), "project"))), 1)

    def test_overlap_must_cover_at_least_three_quarters_of_current_values(self):
        self.assertEqual(len(self.replay(editorial_screen(shared_blocks(text=replay_text(VALUES + ["7.77", "8.88"])), "project"))), 1)
        self.assertFalse(self.replay(editorial_screen(shared_blocks(text=replay_text(VALUES + ["7.77", "8.88", "9.99"])), "project")))

    def test_repeated_occurrences_of_one_value_do_not_meet_distinct_threshold(self):
        self.assertFalse(self.replay(editorial_screen(shared_blocks(["1.11"] * 6, replay_text(["1.11"] * 6)), "project")))

    def test_table_evidence_changes_invalidate_old_decision_away_from_neighbors(self):
        blocks = shared_blocks(VALUES + ["7.77"])
        old = self.replay(editorial_screen(blocks, "project"))[0]
        decision = {"reviews": [{"candidate_id": old["candidate_id"], "decision": "scientific_content",
            "reason": "The residual losses specify the measured operands of the required numerical derivation."}]}
        self.assertEqual(editorial_screen(blocks, "project", decision)["unresolved_editorial_count"], 0)
        blocks[6]["text"] = "8.88"
        changed = editorial_screen(blocks, "project", decision)
        new = self.replay(changed)[0]
        self.assertNotEqual(old["candidate_id"], new["candidate_id"])
        self.assertEqual(new["review_status"], "unresolved")
        self.assertEqual(changed["stale_review_count"], 1)

    def test_literal_decimal_normalization_preserves_exact_value(self):
        values = [str(float(v)) + "0" for v in VALUES]
        self.assertEqual(len(self.replay(editorial_screen(shared_blocks(values), "project"))), 1)
        self.assertEqual(numeric_values("H24, IEEE14, Table 19, [1, 2, 3], 1.110, −2.20, 3.3e1, 4.4\\%"),
                         {"1.11", "-2.2", "33", "4.4%"})

    def test_rounding_and_percentage_rescaling_are_never_guessed(self):
        self.assertFalse(self.replay(editorial_screen(shared_blocks([v + "1" for v in VALUES]), "project")))
        self.assertFalse(self.replay(editorial_screen(shared_blocks([v + "%" for v in VALUES]), "project")))

    def test_caption_numeric_list_is_not_body_table_replay(self):
        self.assertFalse(self.replay(word_screen.inspect_writing(self.word([VALUES], caption=True))))

    def test_specific_numerical_derivation_can_be_retained_after_context_review(self):
        blocks = shared_blocks()
        result = editorial_screen(blocks, "project")
        candidate = self.replay(result)[0]
        review = {"reviews": [{"candidate_id": candidate["candidate_id"], "decision": "scientific_content",
            "reason": "The residual losses define the measured operands required to reproduce the numerical derivation."}]}
        checked = editorial_screen(blocks, "project", review)
        self.assertEqual(self.replay(checked)[0]["review_status"], "retained_scientific_content")
        self.assertEqual(checked["unresolved_editorial_count"], 0)

    def test_related_prose_evidence_also_binds_candidate_identity(self):
        original = "Residual-weighted fusion has lower prediction error than the strongest baseline across the evaluated commuter demand transitions."
        blocks = [{"location": "p1", "text": original, "section": "results"},
                  {"location": "p2", "text": "The demand transition separates steady observations from the changing-load condition.", "section": "results"},
                  {"location": "p3", "text": original, "section": "results"}]
        old = next(c for c in editorial_screen(blocks, "project")["editorial_candidates"] if c["type"] == "redundant_prose")
        blocks[0]["text"] = original + " The residual adjustment is evaluated at matched origins."
        new = next(c for c in editorial_screen(blocks, "project")["editorial_candidates"] if c["type"] == "redundant_prose")
        self.assertNotEqual(old["candidate_id"], new["candidate_id"])

class SharedLanguageMissesTests(unittest.TestCase):
    def test_single_agenda_and_reference_only_defense_reach_every_branch(self):
        for text, kind in (("This experiment aims to verify the proposed model.", "experimental_report_prose"),
                           ("本实验的目的在于验证所提模型的有效性。", "experimental_report_prose"),
                           ("本报告仅供参考。", "defensive_prose")):
            for branch in ("project",):
                with self.subTest(text=text, branch=branch):
                    result = editorial_screen([{"location": "p1", "text": text}], branch)
                    self.assertIn(kind, {c["type"] for c in result["editorial_candidates"]})

    def test_real_protocol_and_source_fact_are_not_agenda_or_defense(self):
        for text in ("The calibration interval precedes the test interval, and the horizon is 24 h.",
                     "负荷数据来自已处理的站点逐小时测量序列。", "容量约束排除超过可用充电功率的分配。"):
            for branch in ("project",):
                with self.subTest(text=text, branch=branch):
                    result = editorial_screen([{"location": "p1", "text": text}], branch)
                    self.assertEqual(result["editorial_candidate_count"], 0)

    def test_chinese_embedded_pair_does_not_connect_unrelated_objects(self):
        blocks = [{"location": "p1", "section": "results", "text": "通勤车辆在晚间抵达充电站，站点小时负荷随接入车辆数量增加而提高，日内需求呈现集中峰值。"},
                  {"location": "p2", "section": "results", "text": "在此基础上，密码签名验证变电站通信指令的来源，传输信道遭受网络攻击时采用独立密钥完成认证。"}]
        for branch in ("project",):
            with self.subTest(branch=branch):
                self.assertIn("disconnected_prose", {c["type"] for c in editorial_screen(blocks, branch)["editorial_candidates"]})

    def test_short_chinese_technical_subject_can_carry_its_actual_object_forward(self):
        blocks = [{"location": "p1", "section": "methods", "text": "观测负荷与站点预测值之间的差异形成逐小时残差，更新时刻取决于测量数据的到达时间。"},
                  {"location": "p2", "section": "methods", "text": "因此，残差决定下一时刻各候选模型的融合权重，权重变化随成熟误差的大小调整预测贡献。"}]
        self.assertNotIn("disconnected_prose", {c["type"] for c in editorial_screen(blocks, "project")["editorial_candidates"]})
