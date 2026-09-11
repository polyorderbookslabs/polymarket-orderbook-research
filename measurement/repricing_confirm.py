"""Confirm: raw books JSON, metrics schema, and the 5m up/down contract at 15:14:05Z."""

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


def main() -> int:
    key = load_key()
    headers = {"X-API-Key": key}

    slug790 = "bitcoin-above-79000-on-september-10-2026-12pm-et"
    path = (
        f"/v1/markets/{urllib.parse.quote(slug790)}/books"
        f"?start_ts=2026-09-10T15:14:04Z&end_ts=2026-09-10T15:14:08Z&resolution=1s&limit=5"
    )
    books = http_json(path, headers)
    data = books.get("data") or {}
    for label in ["Yes", "No"]:
        series = data.get(label) or []
        if series:
            print(f"=== RAW {label} first book point:")
            print(json.dumps(series[0], indent=1))

    mpath = f"/v1/markets/{urllib.parse.quote(slug790)}/metrics?start_ts=2026-09-10T15:09:00Z&end_ts=2026-09-10T15:30:00Z&resolution=1m&limit=200"
    metrics = http_json(mpath, headers)
    pts = metrics.get("data") or []
    print(f"=== metrics {len(pts)} pts; keys: {list(pts[0].keys()) if pts else 'none'}")
    for pt in pts:
        mm = pt["t"][11:16]
        if "15:13" <= mm <= "15:16":
            print(f"  {pt['t']} " + " ".join(f"{k}={v}" for k, v in pt.items() if k != "t" and not isinstance(v, dict)))

    upd = "btc-updown-5m-1789053600"
    det = http_json(f"/v1/markets/{urllib.parse.quote(upd)}", headers)
    print(f"=== {upd}: q={det.get('question')} end={det.get('end_date')} status={det.get('status')}")
    start = datetime(2026, 9, 10, 15, 13, 30, tzinfo=timezone.utc)
    end = datetime(2026, 9, 10, 15, 15, 0, tzinfo=timezone.utc)
    pts = get_prices(headers, upd, start, end, "1s")
    prev = None
    print(f"  {len(pts)} 1s points:")
    for pt in pts:
        v = float(pt["p"])
        if v != prev:
            print(f"    {pt['t']}  {v:.4f}")
        prev = v
    return 0


if __name__ == "__main__":
    sys.exit(main())