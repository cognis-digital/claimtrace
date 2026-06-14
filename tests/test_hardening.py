"""Hardening tests: edge cases, error paths, and input validation."""
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claimtrace.core import (  # noqa: E402
    parse_observations,
    build_graph,
    trace,
)
from claimtrace.cli import main  # noqa: E402


# ---------------------------------------------------------------------------
# core.py — parse_observations edge cases
# ---------------------------------------------------------------------------

class TestParseObservationsEdgeCases(unittest.TestCase):
    def test_none_input_raises_valueerror(self):
        with self.assertRaises(ValueError) as ctx:
            parse_observations(None)
        self.assertIn("null", str(ctx.exception).lower())

    def test_integer_input_raises_valueerror(self):
        with self.assertRaises(ValueError):
            parse_observations(42)

    def test_missing_observations_key_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_observations({"data": []})
        self.assertIn("observations", str(ctx.exception))

    def test_observations_not_list_raises(self):
        with self.assertRaises(ValueError):
            parse_observations({"observations": "not-a-list"})

    def test_empty_source_field_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_observations([
                {"source": "   ", "timestamp": "2026-01-01T00:00:00Z"}
            ])
        self.assertIn("empty source", str(ctx.exception))

    def test_bad_timestamp_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_observations([
                {"source": "a", "timestamp": "not-a-date"}
            ])
        self.assertIn("timestamp", str(ctx.exception))

    def test_missing_timestamp_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_observations([{"source": "a"}])
        self.assertIn("timestamp", str(ctx.exception))


# ---------------------------------------------------------------------------
# core.py — build_graph: duplicate via bug was triggering TypeError
# ---------------------------------------------------------------------------

class TestBuildGraphDuplicateVia(unittest.TestCase):
    """Multiple observations attributing the same downstream to the same upstream
    must not raise TypeError and must produce exactly one explicit edge per
    downstream source."""

    def _sample(self):
        return [
            {"source": "origin", "timestamp": "2026-01-01T00:00:00Z"},
            {"source": "spreader", "timestamp": "2026-01-01T01:00:00Z",
             "via": "origin"},
            # Second observation of spreader still citing origin
            {"source": "spreader", "timestamp": "2026-01-01T01:30:00Z",
             "via": "origin"},
        ]

    def test_no_type_error_on_duplicate_via(self):
        obs = parse_observations(self._sample())
        # Must not raise TypeError
        g = build_graph(obs)
        explicit_to_spreader = [
            e for e in g.edges if e.dst == "spreader" and not e.inferred
        ]
        self.assertEqual(len(explicit_to_spreader), 1,
                         "expected exactly one explicit edge per downstream source")

    def test_duplicate_via_trace_completes(self):
        obs = parse_observations(self._sample())
        result = trace(obs)
        self.assertEqual(result.origins, ["origin"])


# ---------------------------------------------------------------------------
# core.py — single-source trace (no edges, no spread)
# ---------------------------------------------------------------------------

class TestSingleSource(unittest.TestCase):
    def test_single_source_origin_and_no_spread(self):
        obs = parse_observations([
            {"source": "lone", "timestamp": "2026-06-01T12:00:00Z"}
        ])
        result = trace(obs)
        self.assertEqual(result.origins, ["lone"])
        self.assertAlmostEqual(result.spread_seconds, 0.0)
        self.assertEqual(result.graph.edges, [])

    def test_single_source_path_is_self(self):
        obs = parse_observations([
            {"source": "lone", "timestamp": "2026-06-01T12:00:00Z"}
        ])
        result = trace(obs)
        self.assertEqual(result.paths["lone"], ["lone"])


# ---------------------------------------------------------------------------
# core.py — via citing an unseen / future source
# ---------------------------------------------------------------------------

class TestViaUnseenSource(unittest.TestCase):
    def test_via_unseen_registered_as_floor(self):
        obs = parse_observations([
            {"source": "b", "timestamp": "2026-01-01T01:00:00Z", "via": "a"},
        ])
        g = build_graph(obs)
        self.assertIn("a", g.first_seen,
                      "unseen via-source should be registered in the graph")
        explicit = [e for e in g.edges if e.src == "a" and e.dst == "b" and not e.inferred]
        self.assertEqual(len(explicit), 1)

    def test_via_self_is_ignored(self):
        obs = parse_observations([
            {"source": "a", "timestamp": "2026-01-01T00:00:00Z", "via": "a"},
        ])
        g = build_graph(obs)
        self_edges = [e for e in g.edges if e.src == "a" and e.dst == "a"]
        self.assertEqual(self_edges, [], "self-loop via must not create an edge")


# ---------------------------------------------------------------------------
# cli.py — I/O error handling
# ---------------------------------------------------------------------------

class TestCLIErrors(unittest.TestCase):
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

    def test_empty_stdin_returns_nonzero(self):
        code, _, err = self._capture(["trace"], stdin_text="")
        self.assertNotEqual(code, 0)
        self.assertTrue(err.strip(), "stderr must have an error message")

    def test_whitespace_only_stdin_returns_nonzero(self):
        code, _, err = self._capture(["trace"], stdin_text="   \n  ")
        self.assertNotEqual(code, 0)
        self.assertIn("error", err.lower())

    def test_directory_path_returns_nonzero(self):
        # Passing a directory instead of a file should exit non-zero with a
        # clear message (not a raw traceback).
        with tempfile.TemporaryDirectory() as d:
            code, _, err = self._capture(["trace", d])
        self.assertNotEqual(code, 0)
        self.assertTrue(err.strip())

    def test_null_json_value_returns_nonzero(self):
        """JSON literal null maps to Python None; must error cleanly."""
        code, _, err = self._capture(["trace"], stdin_text="null")
        self.assertEqual(code, 1)
        self.assertIn("error", err.lower())

    def test_json_array_of_non_objects_returns_nonzero(self):
        code, _, err = self._capture(["trace"], stdin_text='[1, 2, 3]')
        self.assertEqual(code, 1)
        self.assertIn("error", err.lower())

    def test_valid_single_source_json_returns_zero(self):
        payload = json.dumps([
            {"source": "sole", "timestamp": "2026-06-01T10:00:00Z"}
        ])
        code, out, _ = self._capture(
            ["--format", "json", "trace"], stdin_text=payload
        )
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["origins"], ["sole"])


if __name__ == "__main__":
    unittest.main()
