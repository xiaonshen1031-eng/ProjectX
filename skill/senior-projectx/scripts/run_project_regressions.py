#!/usr/bin/env python3
"""Run the packaged Project regressions without writing into source datasets."""
from __future__ import annotations

import argparse
import io
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pattern', default='test_*.py')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--log', type=Path)
    parser.add_argument('--record', action='store_true', help='Register this actual run in the selected harness.')
    parser.add_argument('--harness-root', type=Path, default=ROOT / 'harness')
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=args.pattern)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = stream.getvalue()
    status = 'fail' if result.failures or result.errors else 'partial' if result.skipped else 'pass'
    payload = {'status': status, 'tests_run': result.testsRun,
               'passed': result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
               'failed': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
               'skip_reasons': [{'test': str(t), 'reason': reason} for t, reason in result.skipped],
               'failures': [{'test': str(t), 'detail': detail} for t, detail in [*result.failures, *result.errors]]}
    for path, content in [(args.out, json.dumps(payload, ensure_ascii=False, indent=2)), (args.log, log)]:
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content + '\n', encoding='utf-8')
    if args.record:
        from update_harness_state import record_eval
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        record_eval(argparse.Namespace(eval_id='project-regression-' + stamp, status=status,
                    check=[f"passed={payload['passed']}", f"failed={payload['failed']}", f"errors={payload['errors']}", f"skipped={payload['skipped']}"],
                    artifact=[], notes='Executed the packaged Project unit regressions.'), args.harness_root.resolve())
    if status == 'fail':
        sys.stderr.write(log)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == 'pass' else 2


if __name__ == '__main__':
    raise SystemExit(main())
