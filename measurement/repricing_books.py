"""Book structure at the 15:14:05 repricing second + find the 15:44Z second wave."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

KEY_PATH = Path.home() / ".polyorderbooks.env"
BASE = "https://api.polyorderbooks.com"


def load_key() -> str:
    key = os.environ.get("POLYORDERBOOKS_API_KEY")
    if key:
        return key
    if KEY_PATH.exists():
        for line in KEY_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith("POLYORDERBOOKS_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("set POLYORDERBOOKS_API_KEY or put a key at ~/.polyorderbooks.env")


def http_json(path: str, headers: dict) -> dict:
    req = urllib.request.Request(BASE + path, headers=headers)
    with urllib.request.urlopen(req, timeout=90) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def fts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_prices(headers, slug, start, end, resolution="1s"):
    path = (
        f"/v1/markets/{urllib.parse.quote(slug)}/prices"
        f"?start_ts={fts(start)}&end_ts={fts(end)}&resolution={resolution}&limit=200"
    )
    page = http_json(path, headers)
    return (page.get("data") or {}).get("Yes") or []


def pbuf(headers, slug, m1, s1, m2, s2):
    start = datetime(2026, 9, 10, 15, m1, s1, tzinfo=timezone.utc)
    end = datetime(2026, 9, 10, 15, m2, s2, tzinfo=timezone.utc)
    pts = get_prices(headers, slug, start, end, "1s")
    prev = None
    for pt in pts:
        v = float(pt["p"])
        if v != prev:
            print(f"    {pt['t']}  {v:.4f}")
        prev = v
    print(f"    -> {len(pts)} 1s points")


def main() -> int:
    key = load_key()
    headers = {"X-API-Key": key}

    slug = "bitcoin-above-79000-on-september-10-2026-12pm-et"
    bstart = datetime(2026, 9, 10, 15, 14, 0, tzinfo=timezone.utc)
    bend = datetime(2026, 9, 10, 15, 14, 15, tzinfo=timezone.utc)
    path = (
        f"/v1/markets/{urllib.parse.quote(slug)}/books"
        f"?start_ts={fts(bstart)}&end_ts={fts(bend)}&resolution=1s&limit=30"
    )
    books = http_json(path, headers)
    data = books.get("data") or {}
    for label in ["Yes", "No"]:
        series = data.get(label) or []
        print(f"=== {label} books: {len(series)} points; sample keys: {list(series[0].keys()) if series else 'none'}")
        for bp in series:
            tb = bp.get("t", "?")
            bids = bp.get("bids") or {}
            asks = bp.get("asks") or {}
            bkeys = sorted(bids, key=float, reverse=True)[:3] if isinstance(bids, dict) else []
            akeys = sorted(asks, key=float)[:3] if isinstance(asks, dict) else []
            bq = " ".join(f"{k}@{bids[k]}" for k in bkeys)
            aq = " ".join(f"{k}@{asks[k]}" for k in akeys)
            print(f"  {tb} nb={len(bids)} na={len(asks)} B:[{bq}] A:[{aq}]")

    print("=== 77600 second-wave probe (15:42-15:46Z)")
    pbuf(headers, "bitcoin-above-77600-on-september-10-2026-12pm-et", 42, 0, 46, 0)
    print("=== 78400 after 15:14 second-wave probe (15:42-15:46Z)")
    pbuf(headers, "bitcoin-above-78400-on-september-10-2026-12pm-et", 42, 0, 46, 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())