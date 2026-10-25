import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import project_demo as demo
import project_report as report
import project_research as research
import project_plot_policy as policy
from validate_figure_manifest import validate_publication_encoding, publication_policy
from selftest_skill import inspect_docx_properties


class RichProjectDeliveryTests(unittest.TestCase):
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
            missing = root / 'data/results/scenarios/allocation_0.80.csv'
            missing.write_bytes(missing.read_bytes() + b'\n')
            self.assertEqual(policy.audit(manifest)['status'], 'fail')
            missing.unlink()
            with self.assertRaises(FileNotFoundError): report.build_figures(*args)

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

    def test_observed_points_remain_available_inside_sourced_conditional_diagnostics(self):
        fig = {'plot_type': 'composite_diagnostic', 'plot_layers': [
            {'role': 'conditional_distribution', 'encoding': 'scatter', 'evidence_source': 'observations.csv',
             'evidence_definition': 'All paired observations grouped by measured operating condition.'},
            {'role': 'paired_effect', 'encoding': 'interval', 'evidence_source': 'effects.csv',
             'evidence_definition': 'Per-unit paired changes and their empirical distribution.'}]}
        errors = []; validate_publication_encoding(fig, 'fig', errors)
        self.assertEqual(errors, [])


if __name__ == '__main__': unittest.main()
