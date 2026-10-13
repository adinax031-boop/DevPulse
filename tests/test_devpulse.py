import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from devpulse.core import AnalysisError, analyze
from devpulse.report import render


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init')
        self.git('config', 'user.name', '<script>alert(1)</script>')
        self.git('config', 'user.email', 'test@example.invalid')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], check=True, capture_output=True)

    def commit(self, name, day, subject='feat: example'):
        (self.root / name).write_text('example', encoding='utf-8')
        self.git('add', name)
        env = dict(os.environ, GIT_AUTHOR_DATE=f'{day}T12:00:00+00:00', GIT_COMMITTER_DATE=f'{day}T12:00:00+00:00')
        subprocess.run(['git', '-C', str(self.root), 'commit', '-m', subject], env=env, check=True, capture_output=True)

    def test_empty_repository(self):
        self.assertEqual(analyze(self.root)['commits'], 0)

    def test_window_counts_and_signals(self):
        self.commit('README.md', '2026-01-01')
        self.commit('LICENSE', '2026-01-10')
        d = analyze(self.root, 3, date(2026, 1, 10))
        self.assertEqual(d['commits'], 1)
        self.assertEqual(len(d['activity']), 3)
        self.assertTrue(d['signals']['readme'])
        self.assertTrue(d['signals']['license'])
        self.assertEqual(d['weekdays'][5], 1)

    def test_all_refs_and_mailmap(self):
        self.commit('README.md', '2026-01-10')
        self.git('checkout', '-b', 'other')
        self.commit('LICENSE', '2026-01-11')
        (self.root / '.mailmap').write_text('Canonical <canonical@example.invalid> <test@example.invalid>\n')
        d = analyze(self.root, 2, date(2026, 1, 11))
        self.assertEqual(d['commits'], 2)
        self.assertEqual(d['contributors'][0]['name'], 'Canonical')

    def test_html_escaping(self):
        self.commit('README.md', '2026-01-10', '<img src=x onerror=alert(1)>')
        html = render(analyze(self.root, 1, date(2026, 1, 10)))
        self.assertNotIn('<script>', html)
        self.assertNotIn('<img src=x', html)
        self.assertIn('&lt;img', html)
        self.assertIn('Content-Security-Policy', html)

    def test_invalid_repo_and_days(self):
        with self.assertRaises(AnalysisError):
            analyze(self.root / 'missing')
        with self.assertRaises(AnalysisError):
            analyze(self.root, 0)

    def test_cli_json_report_and_overwrite_guard(self):
        self.commit('README.md', date.today().isoformat())
        def cli(*args):
            return subprocess.run([sys.executable, '-m', 'devpulse', *args], capture_output=True, text=True)
        result = cli('analyze', str(self.root))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['commits'], 1)
        output = str(self.root / 'report.html')
        self.assertEqual(cli('report', str(self.root), '-o', output).returncode, 0)
        self.assertEqual(cli('report', str(self.root), '-o', output).returncode, 1)
        self.assertEqual(cli('report', str(self.root), '-o', output, '--force').returncode, 0)

    def test_shallow_clone_warning(self):
        self.commit('README.md', date.today().isoformat())
        clone = self.root / 'clone'
        subprocess.run(['git', 'clone', '--depth', '1', self.root.as_uri(), str(clone)], check=True, capture_output=True)
        self.assertTrue(analyze(clone)['shallow'])


if __name__ == '__main__':
    unittest.main()
