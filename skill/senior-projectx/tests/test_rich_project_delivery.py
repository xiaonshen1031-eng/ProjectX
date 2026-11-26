import json
import copy
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import project_demo as demo
import project_report as report
import project_research as research
import project_plot_policy as policy
from validate_figure_manifest import validate_publication_encoding, publication_policy
from selftest_skill import inspect_docx_properties


class RichProjectDeliveryTests(unittest.TestCase):
    def test_small_positive_margin_remains_distinct_from_binding_zero(self):
        self.assertEqual(report._margin_label(.02), '0.02')
        self.assertEqual(report._margin_label(.0004, 1), '0.0004')
        self.assertEqual(report._margin_label(-3.5e-15, 1), '0.0')

    def test_qname_corruption_rejected_even_when_zip_and_xml_parse(self):
        self.assertEqual(inspect_docx_properties(ROOT / 'templates/project_report.docx'), [])
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / 'broken.docx'
            with ZipFile(broken, 'w') as package:
                package.writestr('docProps/core.xml', '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:created xsi:type="dcterms:W3CDTF">2026-10-25T00:00:00Z</dc:created></cp:coreProperties>')
            self.assertIn('Unbound metadata QName', inspect_docx_properties(broken)[0])

    def test_simple_plot_and_decorative_wrapper_rejected_for_project(self):
        self.assertTrue(publication_policy({'branch': 'project'}, []))
        for plot in ('bar', 'line', 'sparse_scatter', 'pareto_2d'):
            errors = []
            validate_publication_encoding({'plot_type': plot}, 'fig', errors)
            self.assertTrue(errors, plot)
        errors = []
        validate_publication_encoding({'plot_type': 'composite_diagnostic', 'plot_layers': [
            {'role': 'title', 'encoding': 'text'}, {'role': 'legend', 'encoding': 'text'}]}, 'fig', errors)
        self.assertTrue(errors)

    def test_report_generator_uses_saved_scenario_traces_and_binds_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            demo.prepare(root)
            allocation = root / 'data/results/allocation.csv'
            research.solve_allocation(root / 'data/periods.csv', root / 'data/vehicles.csv', root / 'model/allocation.json', allocation)
            demo.sensitivity(root)
            args = (root / 'data/periods.csv', allocation, root / 'data/vehicles.csv', root / 'data/results/sensitivity.csv', root / 'figure/final')
            manifest = report.build_figures(*args)
            checked = policy.audit(manifest)
            self.assertEqual(checked['status'], 'pass', checked)
            self.assertEqual([v['plot_type'] for v in manifest['artifacts']], ['temporal_diagnostic', 'response_diagnostic', 'composite_diagnostic'])
            atlas = manifest['artifacts'][-1]
            self.assertEqual(sum('allocation_' in path for path in atlas['source']), 6)
            self.assertEqual(atlas['render_contract']['scales'][0]['vmin'], 0)
            self.assertEqual(atlas['render_contract']['roles']['allocation']['color'], '#00A878')
            self.assertEqual(atlas['numerical_evidence']['scenario_summary'][2]['binding_period_count'], 1)
            self.assertEqual(atlas['numerical_evidence']['scenario_summary'][2]['binding_periods'], [2])
            onset = atlas['numerical_evidence']['scenario_summary'][3]['newly_full_example']
            self.assertEqual(onset['period'], 3)
            self.assertAlmostEqual(onset['baseline_margin_kw'], 2)
            self.assertAlmostEqual(onset['increases_kw']['EV-02'], 1.1)
            self.assertAlmostEqual(onset['increases_kw']['EV-05'], .9)
            self.assertAlmostEqual(manifest['artifacts'][0]['numerical_evidence']['uniform_minimum_margin_kw'], 4.2666666667)
            shift = manifest['artifacts'][1]['numerical_evidence']['single_vehicle_shift']
            self.assertEqual((shift['vehicle'], shift['origin'], shift['destination']), ('EV-02', 2, 4))
            self.assertEqual((shift['energy_kwh'], shift['released_kw'], shift['departure_energy_kwh']), (11, 11, 22))
            clipped = copy.deepcopy(manifest)
            clipped['artifacts'][-1]['render_contract']['scales'][0]['vmin'] = 1
            self.assertTrue(any('clips' in e for e in policy.audit(clipped)['errors']))
            recolored = copy.deepcopy(manifest)
            recolored['artifacts'][0]['render_contract']['roles']['allocation']['color'] = '#306BE8'
            self.assertTrue(any('catalog' in e for e in policy.audit(recolored)['errors']))
            pdf = Path(atlas['exports']['pdf']['path'])
            pdf.write_bytes(pdf.read_bytes() + b'\n')
            self.assertTrue(any('export missing or stale: pdf' in e for e in policy.audit(manifest)['errors']))
            missing = root / 'data/results/scenarios/allocation_0.80.csv'
            complete = missing.read_bytes()
            trace = pd.read_csv(missing)
            nonzero = trace.charge_kw.idxmax()
            incomplete_output = root / 'figure/incomplete'
            trace.drop(index=nonzero).to_csv(missing, index=False)
            with self.assertRaisesRegex(ValueError, 'every vehicle and period'):
                report.build_figures(*args[:-1], incomplete_output)
            self.assertFalse(incomplete_output.exists())
            trace.loc[nonzero, 'charge_kw'] += 1
            trace.to_csv(missing, index=False)
            with self.assertRaisesRegex(ValueError, 'reported mean capacity margin'):
                report.build_figures(*args[:-1], incomplete_output)
            self.assertFalse(incomplete_output.exists())
            missing.write_bytes(complete + b'\n')
            self.assertEqual(policy.audit(manifest)['status'], 'fail')
            missing.unlink()
            with self.assertRaises(FileNotFoundError): report.build_figures(*args[:-1], incomplete_output)
            self.assertFalse(incomplete_output.exists())

    def test_additive_primitive_requires_real_component_definition(self):
        layer = {'role': 'additive_composition', 'encoding': 'stacked_bar', 'evidence_source': 'allocation.csv',
                 'evidence_definition': 'Vehicle powers sum to the total per time period.'}
        fig = {'plot_type': 'composite_diagnostic', 'plot_layers': [layer,
            {'role': 'constraint_margin', 'encoding': 'line', 'evidence_source': 'periods.csv',
             'evidence_definition': 'Capacity minus synchronized total load.'}]}
        errors = []; validate_publication_encoding(fig, 'fig', errors)
        self.assertTrue(errors)
        layer.update(additive_definition_documented=True, component_totals_checked=True)
        errors = []; validate_publication_encoding(fig, 'fig', errors)
        self.assertEqual(errors, [])

    def test_report_tracks_migrating_capacity_bottleneck_at_equal_binding_counts(self):
        low = SimpleNamespace(demand_scale=1.0, mean_margin_kw=8.5)
        high = SimpleNamespace(demand_scale=1.2, mean_margin_kw=5.0)
        summaries = [
            {'demand_scale': 1.0, 'status': 'optimal', 'binding_periods': [2]},
            {'demand_scale': 1.2, 'status': 'optimal', 'binding_periods': [4]},
        ]
        paragraphs = report._compare_scenario_capacity(low, high, summaries)
        self.assertRegex(paragraphs, r'时段 2[^。]*余量，时段 4[^。]*容量上限')
        self.assertRegex(paragraphs, r'时段 4[^。]*加充[^。]*挪到')

    def test_one_vehicle_shift_preserves_energy_at_unequal_interval_lengths(self):
        allocation = np.array([[6.0, 0.0, 0.0]])
        window = np.array([[True, False, True]])
        limits, margin, duration = np.array([9.0]), np.array([0.0, 20.0, 2.0]), np.array([0.5, 1.0, 1.0])
        evidence = report._single_vehicle_shift(allocation, window, limits, margin, duration, [10, 11, 12], ['A'], 0)
        self.assertEqual(evidence['destination'], 12)
        self.assertEqual(evidence['departure_energy_kwh'], 3)
        moved = allocation.copy()
        moved[0, 0] -= evidence['released_kw']
        moved[0, 2] += evidence['destination_charge_increase_kw']
        np.testing.assert_allclose(moved @ duration, allocation @ duration)
        np.testing.assert_allclose(moved, [[2.0, 0.0, 2.0]])
        self.assertIsNone(report._single_vehicle_shift(allocation, window, limits, np.array([0, 20, 0]), duration,
                                                       [10, 11, 12], ['A'], 0))

    def test_observed_points_remain_available_inside_sourced_conditional_diagnostics(self):
        fig = {'plot_type': 'composite_diagnostic', 'plot_layers': [
            {'role': 'conditional_distribution', 'encoding': 'scatter', 'evidence_source': 'observations.csv',
             'evidence_definition': 'All paired observations grouped by measured operating condition.'},
            {'role': 'paired_effect', 'encoding': 'interval', 'evidence_source': 'effects.csv',
             'evidence_definition': 'Per-unit paired changes and their empirical distribution.'}]}
        errors = []; validate_publication_encoding(fig, 'fig', errors)
        self.assertEqual(errors, [])


if __name__ == '__main__': unittest.main()
