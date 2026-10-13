"""Read Git history without executing repository code or shell commands."""
import subprocess
from collections import Counter
from datetime import date, timedelta
from pathlib import Path


class AnalysisError(ValueError):
    pass


def git(path, *args):
    try:
        return subprocess.run(['git', '-C', str(path), *args], check=True,
                              capture_output=True, timeout=120).stdout
    except FileNotFoundError as exc:
        raise AnalysisError('Git is not installed.') from exc
    except subprocess.TimeoutExpired as exc:
        raise AnalysisError('Git exceeded the 120-second command timeout.') from exc
    except subprocess.CalledProcessError as exc:
        raise AnalysisError(exc.stderr.decode('utf-8', 'replace').strip()) from exc


def analyze(path='.', days=90, today=None):
    if not 1 <= days <= 3660:
        raise AnalysisError('days must be between 1 and 3660.')
    today = today or date.today()
    start = today - timedelta(days=days - 1)
    root = Path(git(path, 'rev-parse', '--show-toplevel').decode().strip())
    shallow = git(root, 'rev-parse', '--is-shallow-repository').strip() == b'true'
    raw = git(root, 'log', '--all', '--use-mailmap',
              '--format=%H%x00%aN%x00%aE%x00%aI%x00%s%x00')
    people, activity, weekdays = Counter(), Counter(), Counter()
    recent = []
    for line in raw.splitlines():
        parts = line.split(b'\0')
        if len(parts) < 5:
            continue
        sha, name, email, stamp, subject = [x.decode('utf-8', 'replace') for x in parts[:5]]
        day = date.fromisoformat(stamp[:10])
        if not start <= day <= today:
            continue
        people[(name, email)] += 1
        activity[day.isoformat()] += 1
        weekdays[day.weekday()] += 1
        recent.append({'sha': sha, 'author': name, 'date': stamp, 'subject': subject})
    recent.sort(key=lambda c: (c['date'], c['sha']), reverse=True)
    files = set(git(root, 'ls-files', '-z').split(b'\0')) - {b''}
    def present(names):
        return any(n.encode() in files for n in names)
    signals = {
        'readme': present(['README.md', 'README.rst', 'README', 'readme.md']),
        'license': present(['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING']),
        'contributing': present(['CONTRIBUTING.md', 'CONTRIBUTING.rst']),
        'ci': any(f.startswith(b'.github/workflows/') or f == b'.gitlab-ci.yml' for f in files),
        'tests': any(f.startswith((b'tests/', b'test/')) or b'.test.' in f for f in files),
    }
    contributors = [{'name': n, 'email': e, 'commits': c}
                    for (n, e), c in sorted(people.items(), key=lambda p: (-p[1], p[0]))]
    return {'schema_version': 1, 'repository': root.name, 'start': start.isoformat(),
            'end': today.isoformat(), 'days': days, 'commits': sum(activity.values()),
            'active_days': len(activity), 'contributors': contributors,
            'activity': {(start + timedelta(days=i)).isoformat(): activity[(start + timedelta(days=i)).isoformat()]
                         for i in range(days)},
            'weekdays': [weekdays[i] for i in range(7)], 'recent': recent[:20],
            'signals': signals, 'shallow': shallow}
