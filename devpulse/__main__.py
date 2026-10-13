import argparse
import json
import sys
from pathlib import Path
from . import __version__
from .core import AnalysisError, analyze
from .report import render


def main(argv=None):
    parser = argparse.ArgumentParser(description='Private Git analytics. Beautiful offline reports.')
    parser.add_argument('--version', action='version', version=__version__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('analyze', 'report'):
        p = sub.add_parser(command)
        p.add_argument('repository', nargs='?', default='.')
        p.add_argument('--days', type=int, default=90)
        if command == 'report':
            p.add_argument('--output', '-o', default='devpulse-report.html')
            p.add_argument('--force', action='store_true', help='Replace an existing report')
    args = parser.parse_args(argv)
    try:
        data = analyze(args.repository, args.days)
        if args.command == 'analyze':
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            output = Path(args.output)
            with output.open('w' if args.force else 'x', encoding='utf-8') as stream:
                stream.write(render(data))
            print(f'Report written to {output.resolve()}')
        return 0
    except (AnalysisError, OSError, ValueError) as exc:
        print(f'devpulse: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
