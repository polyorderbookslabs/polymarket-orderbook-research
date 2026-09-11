"""Drill into the Sep 10, 2026 15:14 UTC BTC strike-ladder repricing at 1s.

Aim: measure (a) the exact second(s) the bid/ask ladder repriced on the
bitcoin-above-79k noon contract, (b) how the adjacent strikes moved in the same
minute, and (c) what the books looked like before/after. Keeps request count low.
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


def http_json(path: str, headers: dict) -> dict:
    req = urllib.request.Request(BASE + path, headers=headers)
    with urllib.request.urlopen(req, timeout=90) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def fts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_prices(headers, slug, start, end, resolution) -> list:
    out: list = []
    cursor = None
    for _ in range(8):
        path = (
            f"/v1/markets/{urllib.parse.quote(slug)}/prices"
            f"?start_ts={fts(start)}&end_ts={fts(end)}&resolution={resolution}&limit=200"
            + (f"&cursor={urllib.parse.quote(cursor)}" if cursor else "")
        )
        page = http_json(path, headers)
        data = page.get("data") or {}
        series = data.get("Yes") or []
        out.extend(series)
        cursor = (page.get("metadata") or {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(0.4)
    return out


def main() -> int:
    key = load_key()
    headers = {"X-API-Key": key}

    slug = "bitcoin-above-79000-on-september-10-2026-12pm-et"
    win_start = datetime(2026, 9, 10, 15, 6, 0, tzinfo=timezone.utc)
    win_end = datetime(2026, 9, 10, 15, 20, 0, tzinfo=timezone.utc)

    prices_1s = get_prices(headers, slug, win_start, win_end, "1s")
    print(f"1s price points: {len(prices_1s)}")
    vals_in = [float(pt["p"]) for pt in prices_1s if pt.get("t") and pt["t"] >= fts(win_start)]
    steps = [
        (i, float(prices_1s[i]["p"]) - float(prices_1s[i - 1]["p"]))
        for i in range(1, len(prices_1s))
    ]
    if steps:
        up = max(steps, key=lambda s: s[1])
        dn = min(steps, key=lambda s: s[1])
        print(f"largest 1s upward step: {up[1]:.4f} at {prices_1s[up[0]]['t']}")
        print(f"largest 1s downward step: {dn[1]:.4f} at {prices_1s[dn[0]]['t']}")
    for pt in prices_1s:
        if "15:13:45" <= pt["t"][11:] <= "15:15:00":
            print(f"  {pt['t']} p={float(pt['p']):.4f}")
    print("first/last:", prices_1s[0]["t"], float(prices_1s[0]["p"]), "|", prices_1s[-1]["t"], float(prices_1s[-1]["p"]))

    m_start = datetime(2026, 9, 10, 15, 0, 0, tzinfo=timezone.utc)
    m_end = datetime(2026, 9, 10, 16, 0, 0, tzinfo=timezone.utc)
    for strike in ["79000", "78600", "78400", "77600"]:
        s = f"bitcoin-above-{strike}-on-september-10-2026-12pm-et"
        path = (
            f"/v1/markets/{urllib.parse.quote(s)}/metrics"
            f"?start_ts={fts(m_start)}&end_ts={fts(m_end)}&resolution=1m&limit=200"
        )
        metrics = http_json(path, headers)
        pts = metrics.get("data") or []
        if pts:
            keys = list(pts[0].keys())
            v = [float(pt[strike_key]) for pt in pts if (strike_key := next((k for k in pt if k in ("mid", "price", "spread")), None))]
            # print first metric point to reveal schema once
            if strike == "79000":
                print("metric keys:", keys)
            row = pts[0]
            print(f"{slug_tail(strike)}: n={len(pts)}")
            for pt in pts:
                mm = pt.get("t", "")[11:16]
                if "15:13" <= mm <= "15:16":
                    print(f"    {pt['t']} {compact(pt)}")
        else:
            print(f"{strike}: NO METRICS")
        time.sleep(0.4)
    return 0


def slug_tail(strike: str) -> str:
    return f"{strike}"


def compact(pt: dict) -> str:
    keys = ["spread", "bid_depth", "ask_depth", "volume", "price", "mid"]
    parts = []
    for k in keys:
        if k in pt:
            v = pt[k]
            parts.append(f"{k}={v:.6f}" if isinstance(v, float) else f"{k}={v}")
    return " ".join(parts)


if __name__ == "__main__":
    sys.exit(main())