"""Smoke tests for CLAIMTRACE. Standard library only, no network."""
import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claimtrace import (  # noqa: E402
    TOOL_NAME,
    TOOL_VERSION,
    parse_observations,
    build_graph,
    trace,
)
from claimtrace.cli import main  # noqa: E402


SAMPLE = {
    "observations": [
        {"source": "origin", "timestamp": "2026-03-01T06:00:00Z",
         "variant": "water unsafe runoff"},
        {"source": "amplifier", "timestamp": "2026-03-01T07:00:00Z",
         "variant": "water unsafe runoff spreading", "via": "origin"},
        {"source": "reposter", "timestamp": "2026-03-01T08:00:00Z",
         "variant": "water unsafe runoff everywhere"},
    ]
}


class TestMeta(unittest.TestCase):
    def test_tool_identity(self):
        self.assertEqual(TOOL_NAME, "claimtrace")
        self.assertTrue(TOOL_VERSION)


class TestEngine(unittest.TestCase):
    def test_parse_rejects_empty(self):
        with self.assertRaises(ValueError):
            parse_observations({"observations": []})

    def test_parse_rejects_missing_field(self):
        with self.assertRaises(ValueError):
            parse_observations([{"source": "x"}])

    def test_origin_is_earliest(self):
        obs = parse_observations(SAMPLE)
        result = trace(obs)
        self.assertEqual(result.origins, ["origin"])
        self.assertEqual(result.earliest_time, "2026-03-01T06:00:00+00:00")

    def test_explicit_edge_is_confident(self):
        g = build_graph(parse_observations(SAMPLE))
        explicit = [e for e in g.edges if not e.inferred]
        self.assertTrue(explicit)
        self.assertTrue(all(e.confidence == 1.0 for e in explicit))
        self.assertTrue(any(e.src == "origin" and e.dst == "amplifier"
                            for e in explicit))

    def test_inferred_edge_for_unattributed(self):
        g = build_graph(parse_observations(SAMPLE))
        # 'reposter' has no via -> must get an inferred upstream.
        into_reposter = [e for e in g.edges if e.dst == "reposter"]
        self.assertTrue(into_reposter)
        self.assertTrue(all(e.inferred for e in into_reposter))

    def test_path_reaches_origin(self):
        result = trace(parse_observations(SAMPLE))
        for src, path in result.paths.items():
            self.assertEqual(path[0], "origin")

    def test_spread_span(self):
        result = trace(parse_observations(SAMPLE))
        self.assertAlmostEqual(result.spread_seconds, 7200.0)


class TestCLI(unittest.TestCase):
    def _capture(self, argv, stdin_text=None):
        out, err = io.StringIO(), io.StringIO()
        old_out, old_err, old_in = sys.stdout, sys.stderr, sys.stdin
        sys.stdout, sys.stderr = out, err
        if stdin_text is not None:
            sys.stdin = io.StringIO(stdin_text)
        try:
            code = main(argv)
        finally:
            sys.stdout, sys.stderr, sys.stdin = old_out, old_err, old_in
        return code, out.getvalue(), err.getvalue()

    def test_no_command_returns_2(self):
        code, _, _ = self._capture([])
        self.assertEqual(code, 2)

    def test_trace_json_stdin(self):
        code, out, _ = self._capture(
            ["--format", "json", "trace"], stdin_text=json.dumps(SAMPLE)
        )
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["origins"], ["origin"])
        self.assertEqual(len(payload["sources"]), 3)
        self.assertIn("edges", payload)

    def test_trace_table_stdin(self):
        code, out, _ = self._capture(
            ["trace"], stdin_text=json.dumps(SAMPLE)
        )
        self.assertEqual(code, 0)
        self.assertIn("origin(s)", out)
        self.assertIn("PROPAGATION EDGES", out)

    def test_bad_json_nonzero(self):
        code, _, err = self._capture(["trace"], stdin_text="{not json")
        self.assertEqual(code, 1)
        self.assertIn("error", err)

    def test_missing_file_nonzero(self):
        code, _, err = self._capture(["trace", "does_not_exist.json"])
        self.assertEqual(code, 1)
        self.assertIn("not found", err)


if __name__ == "__main__":
    unittest.main()
