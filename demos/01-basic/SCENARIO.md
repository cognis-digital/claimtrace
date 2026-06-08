# Demo 01 - Tracing a debunked contamination rumor

A false claim ("the city reservoir is contaminated with industrial runoff,
water unsafe") spread across six sources over one morning. Some carriers cited
where they picked it up (`via`); others did not.

`observations.json` contains the timestamped sightings. CLAIMTRACE collapses
these into an **earliest-known-appearance graph**, attributes propagation
links (explicit `via` edges plus inferred nearest-preceding-source edges),
and identifies the **origin**.

## Run it

```bash
# Human-readable table
python -m claimtrace trace demos/01-basic/observations.json

# Machine-readable JSON
python -m claimtrace --format json trace demos/01-basic/observations.json

# Or pipe via stdin
cat demos/01-basic/observations.json | python -m claimtrace trace
```

## What to expect

- **Origin**: `anon_forum_thread` - the earliest appearance (06:12Z) with no
  inbound attribution. This is the rumor's entry point.
- **Explicit edges**: `anon_forum_thread -> @RiverWatchTrue` and
  `@RiverWatchTrue -> @CivicAlertsFeed` (confidence 1.0, from `via`).
- **Inferred edges**: sources without a `via` (e.g. `localnews-clickblog`,
  `regional-tv-station`, `@ViralRepost88`) are linked to their most likely
  upstream source - the nearest preceding carrier, weighted by how similar the
  claim wording is.
- **Spread span**: ~8 hours from first to last appearance.

The takeaway: even when most reposters never say where they got it, the
earliest-appearance graph still surfaces the single low-credibility entry point
behind the wave - exactly what a fact-checker needs to attribute provenance.
