# CLAIMTRACE — Misinformation provenance tracer — earliest-known appearance graph

> Part of the **[Cognis Neural Suite](https://github.com/cognis-digital)** by [Cognis Digital](https://cognis.digital)
> Cognis Open Collaboration License (COCL) v1.0 · domain: `info-integrity`

[![PyPI](https://img.shields.io/pypi/v/cognis-claimtrace.svg)](https://pypi.org/project/cognis-claimtrace/)
[![CI](https://github.com/cognis-digital/claimtrace/actions/workflows/ci.yml/badge.svg)](https://github.com/cognis-digital/claimtrace/actions)
[![License: COCL 1.0](https://img.shields.io/badge/License-COCL%201.0-2b6cb0.svg)](LICENSE)
[![Suite](https://img.shields.io/badge/Cognis-Neural%20Suite-6b46c1.svg)](https://github.com/cognis-digital)

**Misinformation provenance tracer — earliest-known appearance graph.**

*Information Integrity — provenance, synthetic-media, and narrative analysis.*

## Why

Security and intelligence teams need misinformation provenance tracer — earliest-known appearance graph without standing up heavyweight infrastructure. `claimtrace` is single-purpose, scriptable, CI-friendly, and self-hostable: point it at a target, get prioritized findings in the format your workflow already speaks (table, JSON, SARIF, HTML), and wire it into agents over MCP when you want it autonomous.

## Install

```bash
pip install cognis-claimtrace
# or, from this repo:
pip install -e ".[dev]"
```

## Quick start

```bash
claimtrace --version
claimtrace scan demos/                      # run against the bundled demo
claimtrace scan demos/ --format sarif --out r.sarif --fail-on high
claimtrace scan demos/ --format html --out report.html
claimtrace mcp                              # expose as an MCP server (Cognis.Studio / Claude Desktop / Cursor)
```

## Built-in demo scenarios

Each scenario folder includes a `SCENARIO.md` describing the situation and the findings to expect.

- [`demos/01-political-rumor-origin/`](demos/01-political-rumor-origin/SCENARIO.md)
- [`demos/02-clean-news-spread/`](demos/02-clean-news-spread/SCENARIO.md)
- [`demos/03-deepfake-amplification/`](demos/03-deepfake-amplification/SCENARIO.md)

## Output formats

- **Table** (default) — human-readable terminal summary
- **JSON** — machine-readable findings for pipelines
- **SARIF** — drops into GitHub code-scanning / IDE problem panes
- **HTML** — shareable report with severity rollups

## How it fits the Cognis Neural Suite

`claimtrace` is one of **52 tools** in the [Cognis Neural Suite](https://github.com/cognis-digital). Every tool ships an MCP server, so [Cognis.Studio](https://cognis.studio) agents can call them as scoped capabilities.

**Sibling tools in `info-integrity`:** [`deepcheck`](https://github.com/cognis-digital/deepcheck), [`electionlens`](https://github.com/cognis-digital/electionlens), [`narrativediff`](https://github.com/cognis-digital/narrativediff)

## Architecture & roadmap

- Design notes: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Planned work: [`ROADMAP.md`](ROADMAP.md)

## Contributing

PRs, new detections, and demo scenarios are welcome under the collaboration-pull model. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

Source-available under the **Cognis Open Collaboration License (COCL) v1.0** — free for personal, internal-evaluation, research, and educational use; **commercial / production use requires a license** (licensing@cognis.digital). See [LICENSE](LICENSE).

## Responsible use

This is dual-use security software. Use it only against systems, data, and identities you own or are explicitly authorized in writing to test, and in compliance with applicable law.

## About

**[Cognis Digital](https://cognis.digital)** — Wyoming, USA · *Making Tomorrow Better Today: Advanced Cybersecurity, AI Innovation, and Blockchain Expertise.*
