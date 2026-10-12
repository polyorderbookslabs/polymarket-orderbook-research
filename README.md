# Polymarket Order Book Research

Reproducible measurement scripts behind our posted research on Polymarket order
book microstructure. Every figure we publish is produced by one of these
scripts against a pinned market and time window — we do not write numbers
before we have measured them.

This repository gets a new directory and/or scripts whenever a published piece
of research exists that depends on them.

## Scripts

`measurement/` contains the scripts used for the strike-ladder repricing post:

- [Polymarket strike ladders repriced as one second: Aug 23, 2026](https://polyorderbooks.com/blog/polymarket-strike-ladder-repriced-one-second)

| Script | Purpose in the research pipeline |
| --- | --- |
| `repricing_discovery.py` | Scan recently resolved Polymarket BTC markets for large repricing events. Coarse `prices` scan per market first; a later step zooms into the best candidate. |
| `repricing_drill.py` | Drill into the Sep 10, 2026 15:14 UTC strike-ladder repricing at 1s: the exact second(s) the ladder repriced, how adjacent strikes moved in the same minute, and the books before/after. |
| `repricing_secondbysecond.py` | Second-by-second view of the 15:13–15:15 UTC repricing window. |
| `repricing_books.py` | Book structure at the 15:14:05 repricing second, plus the search for the 15:44Z second wave. |
| `repricing_flip_books.py` | Books around the 15:14:05 flip for the 78,600 strike and the 15:44 flicker for the 77,600 strike. |
| `repricing_confirm.py` | Confirm the raw books JSON, metrics schema, and the 5m up/down contract at 15:14:05Z. |

## Running them

Standard library only — no third-party dependencies.

```
python measurement/repricing_drill.py
```

Each script needs a free [PolyOrderbooks API key](https://polyorderbooks.com).
Set it in the environment, or put `POLYORDERBOOKS_API_KEY=...` in
`~/.polyorderbooks.env`:

```
export POLYORDERBOOKS_API_KEY=pob_...
```

The default Starter tier (60 requests/minute, 1-day history window, 250ms
resolution) is enough to reproduce every figure in the post.

## Data

The order book data queried by these scripts is the same 1-second L2 archive
published openly as:

- PolyOrderbooks. (2026). *Polymarket Crypto Up/Down Order Books: 1-Second L2
  Depth Across Three Contract Lengths* [Dataset]. Zenodo.
  <https://doi.org/10.5281/zenodo.22084114> — CC BY 4.0.
- Versioned record: <https://zenodo.org/records/22084115>

Prefer the concept DOI for general reference and cite the version DOI (v1.0.0:
`10.5281/zenodo.22084115`) when a result must be reproducible against exact
data.

## Related repositories

- [polyorderbooks-python](https://github.com/polyorderbookslabs/polyorderbooks-python) — official Python SDK on PyPI
- [mcp-server](https://github.com/polyorderbookslabs/mcp-server) — MCP server for Claude / Cursor / any MCP client
- [python-examples](https://github.com/polyorderbookslabs/python-examples) — runnable examples for the SDK

## License

Scripts in this repository are MIT licensed. The underlying dataset is CC BY
4.0 (see [Data](#data)).