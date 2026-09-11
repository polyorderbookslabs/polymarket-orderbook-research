"""Second-by-second view of the 15:13-15:15 UTC strike repricing on Sep 10, 2026."""

from __future__ import annotations

import json
import os
import sys
import time
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


def main() -> int:
    key = load_key()
    headers = {"X-API-Key": key}
    start = datetime(2026, 9, 10, 15, 12, 30, tzinfo=timezone.utc)
    end = datetime(2026, 9, 10, 15, 15, 30, tzinfo=timezone.utc)

    for strike in ["79000", "78600", "78400"]:
        slug = f"bitcoin-above-{strike}-on-september-10-2026-12pm-et"
        pts = get_prices(headers, slug, start, end, "1s")
        print(f"=== {strike} : {len(pts)} 1s points")
        for pt in pts:
            sec = pt["t"][11:19]
            if "15:13:00" <= sec <= "15:15:10":
                print(f"  {pt['t']}  p={float(pt['p']):.4f}")
        time.sleep(0.3)

    slug = "bitcoin-above-79000-on-september-10-2026-12pm-et"
    bstart = datetime(2026, 9, 10, 15, 13, 0, tzinfo=timezone.utc)
    bend = datetime(2026, 9, 10, 15, 15, 0, tzinfo=timezone.utc)
    path = (
        f"/v1/markets/{urllib.parse.quote(slug)}/books"
        f"?start_ts={fts(bstart)}&end_ts={fts(bend)}&resolution=1s&limit=120"
    )
    books = http_json(path, headers)
    data = books.get("data") or {}
    labels = list(data.keys())
    print("=== 79k books keys:", labels)
    for label in labels:
        series = data.get(label) or []
        print(f"  {label}: {len(series)} points")
        for bp in series[-3:]:
            bids = (bp.get("bids") or [])[:3]
            asks = (bp.get("asks") or [])[:3]
            bb = f"{bids[0]['price']:.3f}" if bids else None
            ba = f"{asks[0]['price']:.3f}" if asks else None
            print(f"    t={bp['t']} bids={len(bp.get('bids') or [])} asks={len(bp.get('asks') or [])} bestbid={bb} bestask={ba}")
    return 0


if __name__ == "__main__":
    sys.exit(main())