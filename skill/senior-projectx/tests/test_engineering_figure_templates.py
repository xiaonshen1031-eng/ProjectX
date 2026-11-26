"""Validate the physical calculations used by the six reusable templates."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest


TEMPLATES = Path(__file__).resolve().parents[1] / 'templates'
sys.path.insert(0, str(TEMPLATES))
from project_engineering_figures import BUILDERS, build_plan, serialize


def case(**fields):
    return {'scope': 'Synthetic regression under one matched operating scope', **fields}


class EngineeringFigureTests(unittest.TestCase):
    def test_duration_weights_each_sorted_interval(self):
        plan = build_plan('duration', case(capacity_kw=8, intervals=[
            {'id': 'short', 'hours': .5, 'baseline_kw': 10, 'candidate_kw': 7},
            {'id': 'long', 'hours': 1.5, 'baseline_kw': 6, 'candidate_kw': 9},
        ]))
        evidence = plan['evidence']
        self.assertEqual(evidence['observed_hours'], 2.)
        self.assertEqual(evidence['above_cap_hours'], [.5, 1.5])
        self.assertEqual(evidence['above_cap_kwh'], [1., 1.5])

    def test_calendar_distinguishes_missing_zero_and_binding(self):
        plan = build_plan('saturation', case(capacity_kw=10, near_kw=2, days=[
            {'date': '2026-01-10', 'load_kw': [11, 10, 9, 8, None] + [0] * 19},
        ]))
        self.assertEqual(plan['evidence']['daily_hours'][0].tolist(), [1, 2, 20, 1])

    def test_budget_requires_independently_reconciled_total(self):
        data = case(baseline_kwh=100, candidate_kwh=96, components=[
            {'label': 'Shift out', 'delta_kwh': -8}, {'label': 'Shift in', 'delta_kwh': 8},
            {'label': 'Avoided', 'delta_kwh': -4},
        ])
        self.assertEqual(build_plan('energy-bridge', data)['evidence']['net_kwh'], -4)
        data['candidate_kwh'] = 104
        with self.assertRaisesRegex(ValueError, 'does not reconcile'):
            build_plan('energy-bridge', data)

    def test_adjacent_windows_integrate_nonuniform_bins_without_dropping_negative_return(self):
        data = case(bin_edges_h=[0, .5, 1.5, 2.5], event_end_h=.5, recovery_end_h=2.5,
                    pairs=[{'id': 'A', 'reference_kw': [10, 10, 10], 'controlled_kw': [8, 13, 6]}])
        result = build_plan('rebound', data)['evidence']
        self.assertEqual(result['net_reduced_kwh'].tolist(), [1.])
        self.assertEqual(result['net_returned_kwh'].tolist(), [-1.])
        data['event_end_h'] = 1.25
        with self.assertRaisesRegex(ValueError, 'exact input bin edges'):
            build_plan('rebound', data)

    def test_hysteresis_uses_sample_state_rather_than_assigning_configured_threshold(self):
        result = build_plan('hysteresis', case(on_threshold_c=25, off_threshold_c=23, samples=[
            {'time_h': 0, 'temperature_c': 24., 'power_kw': 0, 'cooling': False},
            {'time_h': 1, 'temperature_c': 25.6, 'power_kw': 4, 'cooling': True},
            {'time_h': 2, 'temperature_c': 22.9, 'power_kw': 0, 'cooling': False},
        ]))['evidence']
        self.assertEqual(result['observed_on'], [{'time_h': 1., 'temperature_c': 25.6}])
        self.assertEqual(result['observed_off'], [{'time_h': 2., 'temperature_c': 22.9}])

    def test_pareto_keeps_ties_and_reports_no_feasible_candidate(self):
        data = case(currency='USD', cost_cap=16, unserved_cap_kwh_per_day=3, candidates=[
            {'id': 'A', 'family': 'F', 'daily_cost': 10, 'unserved_kwh_per_day': 5},
            {'id': 'B', 'family': 'F', 'daily_cost': 12, 'unserved_kwh_per_day': 4},
            {'id': 'C', 'family': 'G', 'daily_cost': 12, 'unserved_kwh_per_day': 4},
            {'id': 'D', 'family': 'G', 'daily_cost': 15, 'unserved_kwh_per_day': 4},
        ])
        result = build_plan('pareto', data)['evidence']
        self.assertEqual(result['nondominated_ids'], ['A', 'B', 'C'])
        self.assertIsNone(result['least_cost_feasible'])
        data['unserved_cap_kwh_per_day'] = 4
        self.assertEqual(build_plan('pareto', data)['evidence']['least_cost_feasible'], 'B')

    def test_all_bilingual_fixtures_make_finite_export_plans(self):
        fixture = json.loads((TEMPLATES / 'project-engineering-examples.json').read_text(encoding='utf-8'))
        self.assertEqual(set(fixture), set(BUILDERS))
        for chart, versions in fixture.items():
            for locale, data in versions.items():
                with self.subTest(chart=chart, locale=locale):
                    source = deepcopy(data)
                    output = build_plan(chart, data, locale)
                    self.assertEqual(source, data)
                    self.assertEqual(output['canvas_mm'][0], 166)
                    self.assertGreaterEqual(len(output['panels']), 2)
                    json.dumps(output, default=serialize, allow_nan=False)


if __name__ == '__main__':
    unittest.main()
