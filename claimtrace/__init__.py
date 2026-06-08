"""CLAIMTRACE - Misinformation provenance tracer.

Builds an earliest-known-appearance graph from timestamped observations of a
claim spreading across sources, then identifies the origin(s) and the most
likely propagation paths.
"""
from .core import (
    Observation,
    ProvenanceGraph,
    TraceResult,
    parse_observations,
    build_graph,
    trace,
)

TOOL_NAME = "claimtrace"
TOOL_VERSION = "1.0.0"

__all__ = [
    "Observation",
    "ProvenanceGraph",
    "TraceResult",
    "parse_observations",
    "build_graph",
    "trace",
    "TOOL_NAME",
    "TOOL_VERSION",
]
