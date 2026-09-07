"""Opt-in live benchmark. Calls paid APIs; does not use Supabase or store user history."""
import argparse
import json
from pathlib import Path
import time
from services.ai_provider import call_humanizer
from services.rewrite import source_overlap


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['ghost_1', 'ghost_2', 'both'], default='ghost_1')
    parser.add_argument('--paid', action='store_true', help='Use configured paid-tier models')
    parser.add_argument('--level', choices=['light', 'medium', 'aggressive'])
    parser.add_argument('--fixture', type=Path, default=Path(__file__).parent / 'tests/fixtures/academic_cybersecurity.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding='utf-8'))
    if args.level:
        fixture['level'] = args.level
    results = []
    for mode in ['ghost_1', 'ghost_2'] if args.mode == 'both' else [args.mode]:
        start = time.monotonic()
        try:
            result = call_humanizer(fixture['source'], fixture['level'], fixture['tone'], args.paid, mode)
            results.append({'mode': mode, 'seconds': round(time.monotonic() - start, 2),
                            'source_overlap': source_overlap(fixture['source'], result['humanized_text']), **result})
        except Exception as exc:
            cause = exc.__cause__
            results.append({'mode': mode, 'error_type': type(exc).__name__,
                            'cause_type': type(cause).__name__ if cause else None,
                            'status_code': getattr(cause, 'status_code', None),
                            'diagnostics': getattr(exc, 'diagnostics', []),
                            'programming_error': str(exc) if isinstance(exc, TypeError) else None})
    report = {'fixture': fixture, 'results': results,
              'review_note': 'Mechanically valid output is not proof of preserved meaning or detector performance. Review every requirement manually.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Report saved to {args.output}')
    if any('error_type' in result for result in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
