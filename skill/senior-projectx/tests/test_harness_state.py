from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / 'scripts/update_harness_state.py'


class HarnessStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.harness = Path(self.temp.name) / 'harness'

    def call(self, *args, ok=True):
        ran = subprocess.run([sys.executable, '-B', str(SCRIPT), '--harness-root', str(self.harness), *args], capture_output=True, text=True, encoding='utf-8')
        if ok:
            self.assertEqual(ran.returncode, 0, ran.stderr)
            return json.loads(ran.stdout)
        self.assertNotEqual(ran.returncode, 0)

    def state(self):
        return json.loads((self.harness / 'state/skill_state.json').read_text(encoding='utf-8'))

    def test_feedback_and_decisions_append_without_erasing_prior_events(self):
        for number in (1, 2):
            self.call('feedback', '--classification', 'project', '--feedback', f'Feedback {number}', '--interpretation', 'Preserve accepted figures.', '--root-cause', 'An overbroad edit changed the figure.')
            self.call('decision', '--decision', f'Bounded repair {number}', '--scope', 'project', '--rationale', 'Only the affected objects need a change.')
        for name in ('feedback/user_feedback.jsonl', 'decisions/decision_log.jsonl'):
            self.assertEqual(len((self.harness / name).read_text(encoding='utf-8').splitlines()), 2)

    def test_preferences_preserve_scope_and_accumulate_evidence(self):
        self.call('preference', '--preference-id', 'units', '--statement', 'State the actual unit.', '--scope', 'project', '--confidence', '0.8', '--evidence-increment', '2')
        self.call('preference', '--preference-id', 'units', '--evidence-increment', '1')
        value = self.state()['preferences']['units']
        self.assertEqual(value['scope'], 'project')
        self.assertEqual(value['evidence_count'], 3)
        self.assertEqual(value['statement'], 'State the actual unit.')

    def test_case_replace_is_explicit_and_preserves_unrelated_cases(self):
        def case(identifier, expected):
            return ('regression', '--case-id', identifier, '--task-type', 'project', '--input-summary', 'A local revision.', '--expected-behavior', expected, '--forbidden-behavior', 'Change other results.', '--relevant-rule', 'SKILL.md')
        self.call(*case('A', 'Preserve values.'))
        self.call(*case('B', 'Preserve geometry.'))
        self.call(*case('A', 'New behavior.'), ok=False)
        self.call(*case('A', 'New behavior.'), '--replace')
        values = json.loads((self.harness / 'regression/regression_cases.json').read_text(encoding='utf-8'))['cases']
        self.assertEqual([v['case_id'] for v in values], ['A', 'B'])
        self.assertEqual(values[1]['expected_behavior'], 'Preserve geometry.')

    def test_version_history_and_duplicate_protection(self):
        self.call('version', '--version', '1.0', '--summary', 'Initial maintained state.')
        self.call('version', '--version', '1.1', '--summary', 'Compatible formulas.')
        self.call('version', '--version', '1.1', '--summary', 'Duplicate.', ok=False)
        self.assertEqual(self.state()['version_history'][-1]['previous_version'], '1.0')
        self.assertEqual(len(self.state()['version_history']), 2)

    def test_failed_evaluation_is_retained_as_failed(self):
        self.call('eval', '--eval-id', 'run-1', '--status', 'fail', '--check', 'An expected assertion failed.')
        self.assertEqual(self.state()['last_regression']['status'], 'fail')
        records = json.loads((self.harness / 'evals/eval_registry.json').read_text(encoding='utf-8'))['runs']
        self.assertEqual(records[0]['status'], 'fail')

    def test_selected_harness_never_writes_to_the_distributed_state(self):
        path = ROOT / 'harness/state/skill_state.json'
        before = path.read_bytes()
        self.call('preference', '--preference-id', 'temporary', '--scope', 'project')
        self.assertEqual(path.read_bytes(), before)

    def test_chinese_feedback_is_utf8_even_under_a_legacy_windows_codepage(self):
        env = dict(os.environ, PYTHONIOENCODING='cp936')
        command = [sys.executable, '-B', str(SCRIPT), '--harness-root', str(self.harness),
                   'feedback', '--classification', 'preference', '--feedback', '取消简单图，保留真实约束关系。',
                   '--interpretation', '使用信息充分的工程诊断图。', '--root-cause', '默认模板信息量不足。']
        ran = subprocess.run(command, capture_output=True, env=env)
        self.assertEqual(ran.returncode, 0, ran.stderr.decode('utf-8'))
        returned = json.loads(ran.stdout.decode('utf-8'))
        self.assertEqual(returned['feedback'], '取消简单图，保留真实约束关系。')
        record = json.loads((self.harness / 'feedback/user_feedback.jsonl').read_text(encoding='utf-8').strip())
        self.assertEqual(record['feedback'], returned['feedback'])
