"""Command-line interface for CLAIMTRACE."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import TOOL_NAME, TOOL_VERSION
from .core import parse_observations, trace, TraceResult


def _load(path: Optional[str]) -> object:
    if path is None or path == "-":
        data = sys.stdin.read()
    else:
        with open(path, "r", encoding="utf-8") as fh:
            data = fh.read()
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON input: {exc}") from None


def _render_table(result: TraceResult) -> str:
    g = result.graph
    lines: List[str] = []
    lines.append(f"CLAIMTRACE {TOOL_VERSION} - provenance trace")
    lines.append("")
    lines.append(f"origin(s)     : {', '.join(result.origins) or '(none)'}")
    lines.append(f"earliest seen : {result.earliest_time or '(none)'}")
    lines.append(f"spread span   : {result.spread_seconds:.0f}s "
                 f"({result.spread_seconds / 3600.0:.2f}h)")
    lines.append("")

    lines.append("APPEARANCES (earliest first)")
    lines.append(f"  {'source':<22} {'first seen (UTC)':<26} variant")
    lines.append("  " + "-" * 66)
    for s in g.sources():
        ts = g.first_seen[s].astimezone().isoformat()
        var = (g.first_variant.get(s, "") or "")[:30]
        lines.append(f"  {s:<22} {ts:<26} {var}")
    lines.append("")

    lines.append("PROPAGATION EDGES")
    if not g.edges:
        lines.append("  (none)")
    for e in sorted(g.edges, key=lambda x: (x.dst, -x.confidence)):
        kind = "inferred" if e.inferred else "explicit"
        lines.append(
            f"  {e.src:<20} -> {e.dst:<20} "
            f"[{kind} conf={e.confidence:.2f} lag={e.lag_seconds:.0f}s]"
        )
    lines.append("")

    lines.append("PATHS TO ORIGIN")
    for s, path in result.paths.items():
        if len(path) > 1:
            lines.append(f"  {s}: " + " <- ".join(reversed(path)))
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="CLAIMTRACE - trace the earliest-known appearance of a "
                    "claim across sources and reconstruct its spread.",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"{TOOL_NAME} {TOOL_VERSION}",
    )
    parser.add_argument(
        "--format", choices=("table", "json"), default="table",
        help="output format (default: table)",
    )
    sub = parser.add_subparsers(dest="command")

    p_trace = sub.add_parser(
        "trace", help="trace provenance from a JSON observations file",
    )
    p_trace.add_argument(
        "input", nargs="?", default="-",
        help="path to JSON observations (default: stdin)",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help(sys.stderr)
        return 2

    if args.command == "trace":
        try:
            raw = _load(args.input)
            observations = parse_observations(raw)
            result = trace(observations)
        except FileNotFoundError:
            print(f"error: file not found: {args.input}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        if args.format == "json":
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(_render_table(result))
        return 0

    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
