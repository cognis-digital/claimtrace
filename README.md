# CLAIMTRACE — Misinformation provenance tracer — earliest-known appearance graph

> Part of the **[Cognis Neural Suite](https://github.com/cognis-digital)** by [Cognis Digital](https://cognis.digital)
> MIT License · domain: `info-integrity`

[![PyPI](https://img.shields.io/pypi/v/cognis-claimtrace.svg)](https://pypi.org/project/cognis-claimtrace/)
[![CI](https://github.com/cognis-digital/claimtrace/actions/workflows/ci.yml/badge.svg)](https://github.com/cognis-digital/claimtrace/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Misinformation provenance tracer — earliest-known appearance graph.

## Install

```bash
pip install cognis-claimtrace
```

For local development from this repo:

```bash
pip install -e .
```

## Quick start

```bash
claimtrace --version
claimtrace scan demos/                          # run against bundled demo
claimtrace scan demos/ --format sarif --out r.sarif --fail-on high
claimtrace mcp                                   # start as MCP server (Cognis.Studio / Claude Desktop / Cursor)
```

## Built-in demo scenarios

Every scenario folder includes a `SCENARIO.md` describing what it represents and what findings to expect.

- `demos/01-political-rumor-origin/` — see [`SCENARIO.md`](demos/01-political-rumor-origin/SCENARIO.md)
- `demos/02-clean-news-spread/` — see [`SCENARIO.md`](demos/02-clean-news-spread/SCENARIO.md)
- `demos/03-deepfake-amplification/` — see [`SCENARIO.md`](demos/03-deepfake-amplification/SCENARIO.md)

## How it fits the Cognis Neural Suite

This tool is one of 52 in the [Cognis Neural Suite](https://github.com/cognis-digital). The full suite + launcher lives at:

- Suite landing: https://cognis.digital
- All 52 repos: https://github.com/cognis-digital
- Cognis.Studio (Enterprise AI Workforce, MCP host): https://cognis.studio

Every Suite tool ships an MCP server, so Cognis.Studio agents can call them as scoped capabilities.

## License

MIT. See [LICENSE](LICENSE).

## About

**[Cognis Digital](https://cognis.digital)** — Wyoming, USA · *Making Tomorrow Better Today: Advanced Cybersecurity, AI Innovation, and Blockchain Expertise.*
