"""Core engine for CLAIMTRACE.

Model
-----
A *claim* spreads across *sources* (accounts, sites, outlets). Each
*observation* records that a source carried the claim at a given timestamp,
optionally citing the source it picked it up from (``via``) and the textual
variant of the claim it carried.

From a set of observations we build a provenance graph:

  * Nodes are sources, each annotated with the *earliest* time the claim was
    seen there (its first appearance).
  * Edges are propagation links. An explicit ``via`` produces a confident edge.
    Where no ``via`` is given, we *infer* the most likely upstream source: the
    source that (a) appeared strictly earlier and (b) is closest in time, with
    a bonus for textual similarity of the claim variant. This mirrors how a
    rumor's likely entry point is the nearest-preceding carrier.

The earliest source(s) with no inbound edge are the candidate *origins*.

This is real, deterministic logic - no stubs, standard library only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Observation:
    """A single timestamped sighting of the claim at a source."""

    source: str
    timestamp: datetime
    variant: str = ""
    via: Optional[str] = None  # explicitly attributed upstream source

    def iso(self) -> str:
        return self.timestamp.astimezone(timezone.utc).isoformat()


@dataclass
class Edge:
    src: str          # upstream source
    dst: str          # downstream source
    inferred: bool    # True if reconstructed, False if explicit `via`
    lag_seconds: float
    confidence: float

    def to_dict(self) -> dict:
        return {
            "from": self.src,
            "to": self.dst,
            "inferred": self.inferred,
            "lag_seconds": round(self.lag_seconds, 3),
            "confidence": round(self.confidence, 4),
        }


@dataclass
class ProvenanceGraph:
    # source -> earliest appearance time
    first_seen: Dict[str, datetime] = field(default_factory=dict)
    # source -> variant carried at first appearance
    first_variant: Dict[str, str] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)

    def sources(self) -> List[str]:
        return sorted(self.first_seen, key=lambda s: (self.first_seen[s], s))


@dataclass
class TraceResult:
    origins: List[str]
    earliest_time: Optional[str]
    graph: ProvenanceGraph
    paths: Dict[str, List[str]]      # source -> path back to its origin
    spread_seconds: float            # origin -> last appearance span

    def to_dict(self) -> dict:
        g = self.graph
        return {
            "origins": self.origins,
            "earliest_time": self.earliest_time,
            "spread_seconds": round(self.spread_seconds, 3),
            "sources": [
                {
                    "source": s,
                    "first_seen": g.first_seen[s].astimezone(timezone.utc).isoformat(),
                    "variant": g.first_variant.get(s, ""),
                }
                for s in g.sources()
            ],
            "edges": [e.to_dict() for e in g.edges],
            "paths": self.paths,
        }


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
def _parse_ts(value: str) -> datetime:
    """Parse an ISO-8601 timestamp; assume UTC if naive."""
    txt = value.strip()
    if txt.endswith("Z"):
        txt = txt[:-1] + "+00:00"
    dt = datetime.fromisoformat(txt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def parse_observations(raw: object) -> List[Observation]:
    """Parse observations from a decoded JSON object or list.

    Accepts either a list of records or an object with an ``observations`` key.
    Each record requires ``source`` and ``timestamp``; ``variant`` and ``via``
    are optional. Raises ValueError on malformed input.
    """
    if isinstance(raw, dict):
        records = raw.get("observations")
        if records is None:
            raise ValueError("input object missing 'observations' array")
    else:
        records = raw

    if not isinstance(records, list):
        raise ValueError("observations must be a JSON array")
    if not records:
        raise ValueError("no observations provided")

    obs: List[Observation] = []
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            raise ValueError(f"observation #{i} is not an object")
        try:
            source = str(rec["source"]).strip()
            ts = _parse_ts(str(rec["timestamp"]))
        except KeyError as exc:
            raise ValueError(f"observation #{i} missing field {exc}") from None
        except ValueError as exc:
            raise ValueError(f"observation #{i} bad timestamp: {exc}") from None
        if not source:
            raise ValueError(f"observation #{i} has empty source")
        via = rec.get("via")
        via = str(via).strip() if via else None
        obs.append(
            Observation(
                source=source,
                timestamp=ts,
                variant=str(rec.get("variant", "")).strip(),
                via=via,
            )
        )
    return obs


# --------------------------------------------------------------------------- #
# Similarity
# --------------------------------------------------------------------------- #
def _tokens(text: str) -> set:
    return {t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split()}


def _jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


# --------------------------------------------------------------------------- #
# Graph construction
# --------------------------------------------------------------------------- #
def build_graph(observations: List[Observation]) -> ProvenanceGraph:
    """Collapse observations into a provenance graph keyed on first appearance."""
    g = ProvenanceGraph()

    # Earliest appearance per source (and the variant at that moment).
    for o in observations:
        cur = g.first_seen.get(o.source)
        if cur is None or o.timestamp < cur:
            g.first_seen[o.source] = o.timestamp
            g.first_variant[o.source] = o.variant

    # 1) Explicit `via` edges (confident).
    explicit: Dict[str, Tuple[str, float]] = {}
    for o in observations:
        if not o.via or o.via == o.source:
            continue
        up = o.via
        if up not in g.first_seen:
            # Citing an unseen source: register it at the citing time as a floor.
            g.first_seen[up] = o.timestamp
            g.first_variant.setdefault(up, "")
        lag = (g.first_seen[o.source] - g.first_seen[up]).total_seconds()
        # Keep the earliest explicit attribution per downstream source.
        prev = explicit.get(o.source)
        if prev is None or g.first_seen[up] < prev[1]:
            explicit[o.source] = (up, g.first_seen[up].timestamp())
            g.edges.append(
                Edge(src=up, dst=o.source, inferred=False,
                     lag_seconds=max(lag, 0.0), confidence=1.0)
            )

    # 2) Infer an upstream for sources lacking an explicit `via`.
    ordered = g.sources()  # by (time, name)
    for dst in ordered:
        if dst in explicit:
            continue
        dst_time = g.first_seen[dst]
        best: Optional[Tuple[float, str, float]] = None  # (score, src, lag)
        for src in ordered:
            if src == dst:
                continue
            src_time = g.first_seen[src]
            if src_time >= dst_time:
                continue  # upstream must precede downstream
            lag = (dst_time - src_time).total_seconds()
            # Recency: nearer-in-time predecessors are more likely the source.
            recency = 1.0 / (1.0 + lag / 3600.0)  # hours
            sim = _jaccard(g.first_variant.get(dst, ""), g.first_variant.get(src, ""))
            score = 0.65 * recency + 0.35 * sim
            if best is None or score > best[0]:
                best = (score, src, lag)
        if best is not None:
            score, src, lag = best
            g.edges.append(
                Edge(src=src, dst=dst, inferred=True,
                     lag_seconds=lag, confidence=round(score, 4))
            )

    return g


def _origins(g: ProvenanceGraph) -> List[str]:
    """Sources with no inbound edge - the candidate entry points."""
    has_in = {e.dst for e in g.edges}
    roots = [s for s in g.first_seen if s not in has_in]
    return sorted(roots, key=lambda s: (g.first_seen[s], s))


def _path_to_origin(g: ProvenanceGraph, source: str) -> List[str]:
    """Walk inbound edges back to an origin (cycle-safe)."""
    parent: Dict[str, str] = {}
    for e in g.edges:
        # Prefer explicit edges; otherwise highest confidence.
        prev = parent.get(e.dst)
        if prev is None:
            parent[e.dst] = e.src
        else:
            # choose the more confident attribution
            prev_edge = next(
                (x for x in g.edges if x.dst == e.dst and x.src == prev), None
            )
            if prev_edge and e.confidence > prev_edge.confidence:
                parent[e.dst] = e.src

    path = [source]
    seen = {source}
    cur = source
    while cur in parent:
        nxt = parent[cur]
        if nxt in seen:
            break
        path.append(nxt)
        seen.add(nxt)
        cur = nxt
    path.reverse()
    return path


def trace(observations: List[Observation]) -> TraceResult:
    """Run the full provenance trace."""
    g = build_graph(observations)
    origins = _origins(g)
    earliest = min(g.first_seen.values()) if g.first_seen else None
    latest = max(g.first_seen.values()) if g.first_seen else None
    spread = (latest - earliest).total_seconds() if earliest and latest else 0.0

    paths = {s: _path_to_origin(g, s) for s in g.sources()}

    return TraceResult(
        origins=origins,
        earliest_time=earliest.astimezone(timezone.utc).isoformat() if earliest else None,
        graph=g,
        paths=paths,
        spread_seconds=spread,
    )
