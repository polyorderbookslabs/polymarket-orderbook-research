"""Scan recently resolved Polymarket BTC markets for large repricing events.

Requires a free PolyOrderbooks API key: set POLYORDERBOOKS_API_KEY, or put the
variable in ~/.polyorderbooks.env. Keeps requests low:
a coarse prices scan per market first, then (a separate step) zoom into the
best candidate at 1s with books and metrics.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
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


def http_json(path: str, headers: dict, timeout: float = 90) -> dict:
    req = urllib.request.Request(BASE + path, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def fmt_ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    key = load_key()
    headers = {"X-API-Key": key}
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=3)

    page = http_json(
        "/v1/markets?search=bitcoin&limit=1000&sort=updated_at&order=desc&include_closed=true",
        headers,
    )
    markets = [
        m
        for m in page.get("data", [])
        if m.get("is_resolved")
        and m.get("end_date")
        and window_start <= parse_ts(m["end_date"]) <= now
    ]
    print(f"resolved bitcoin markets in last 3 days: {len(markets)}")

    events: list[dict] = []
    seen_shape = False
    for m in markets[:40]:
        slug = m["slug"]
        end = parse_ts(m["end_date"])
        start = end - timedelta(minutes=100)
        path = (
            f"/v1/markets/{urllib.parse.quote(slug)}/prices"
            f"?start_ts={fmt_ts(start)}&end_ts={fmt_ts(end)}&resolution=60s&limit=200"
        )
        try:
            prices = http_json(path, headers)
        except Exception as exc:
            print(f"  {slug}: ERROR {exc}")
            continue
        series = prices.get("data") or {}
        yes = series.get("Yes") or []
        if not yes:
            continue
        prices_1m, deltas = [], []
        point0 = yes[0]
        field = "p" if "p" in point0 else list(point0.keys())[1]
        if not seen_shape:
            print(f"  sample point keys: {list(point0.keys())}")
            seen_shape = True
        for pt in yes:
            val = float(pt[field])
            prices_1m.append((pt["t"], val))
        for i in range(1, len(prices_1m)):
            deltas.append(abs(prices_1m[i][1] - prices_1m[i - 1][1]))
        if not deltas:
            continue
        max_step = max(deltas)
        step_i = deltas.index(max_step) + 1
        lo = min(v for _, v in prices_1m)
        hi = max(v for _, v in prices_1m)
        events.append(
            {
                "slug": slug,
                "end": m["end_date"],
                "points": len(prices_1m),
                "lo": round(lo, 4),
                "hi": round(hi, 4),
                "range": round(hi - lo, 4),
                "max_60s_step": round(max_step, 4),
                "max_step_at": prices_1m[step_i][0],
            }
        )
        time.sleep(0.3)

    events.sort(key=lambda e: e["range"], reverse=True)
    print("\nTOP BY PRICE RANGE (Yes price):")
    for e in events[:15]:
        print(
            f"  {e['slug']}: range={e['range']} (lo {e['lo']} hi {e['hi']}) "
            f"max60sStep={e['max_60s_step']} @ {e['max_step_at']} pts={e['points']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())