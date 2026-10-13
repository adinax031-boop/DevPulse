# DevPulse

**Your repository, at a glance. Your data, on your machine.**

A zero-runtime-dependency Python CLI that turns local Git history into a polished, self-contained HTML dashboard. No accounts, tokens, telemetry, JavaScript, or external assets.

## Start in 30 seconds

Requires Python 3.10+ and Git. Install from this checkout (not yet published to PyPI):

```sh
git clone https://github.com/adinax031-boop/DevPulse.git
cd DevPulse
python -m pip install .
devpulse analyze /path/to/repository --days 90
devpulse report /path/to/repository --days 90 -o activity.html
```

Open `activity.html` in any browser. Or run without installation: `python -m devpulse report /path/to/repository` from this checkout.

## What you get

- Daily activity timeline, weekday rhythm, contributor counts, and recent commits.
- Machine-readable JSON through `analyze` (schema version 1).
- README, license, contribution guide, CI, and test presence signals.
- `.mailmap` identity normalization and shallow-clone warnings.
- Responsive offline HTML, escaped repository content, restrictive content security policy.
- Safe output: existing reports require explicit `--force` to overwrite.

[Open the sample report](examples/sample-report.html) by downloading it locally.

## Semantics and limits

Counts use **author dates in their recorded timezone**, inclusive of the start and end date; the end is today's local date. All commits reachable from all refs are counted once, including merges. Recent commits are sorted by author timestamp. Unreachable history is excluded; shallow clones may omit history. Repository signals inspect tracked paths in the working tree and check presence only. Contributor identities appear with email in JSON but only names in HTML. Review reports before sharing.

Git activity is not a measure of productivity, engineering quality, or individual performance. There is deliberately no synthetic “health score.”

The CLI reads Git metadata, does not execute project code, and does not modify the analyzed repository. Each Git command has a 120-second timeout. It loads history into memory; huge monorepos may need more memory. HTML timeline tooltips provide dates; JSON offers complete accessible daily counts. Supports normal working-tree repositories, not bare repositories.

## Development

```sh
python -m unittest discover -s tests -v
python -m compileall -q devpulse tests
python -m pip install ruff
ruff check .
```

CI checks Python 3.10, 3.12, and 3.13. Integration tests create actual temporary Git repositories and cover date windows, branch history, mailmap, empty repositories, shallow clones, HTML injection, and CLI overwrite handling.

## Release

Version 0.1.0; MIT licensed. To build distributable artifacts: `python -m pip install build && python -m build`. Publishing is a separate maintainer action; no registry release is implied by this repository.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
