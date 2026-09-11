"""Books around the 15:14:05 flip for 78600 and the 15:44 flicker for 77600."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
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


def books_yes(headers, slug, start, end):
    path = (
        f"/v1/markets/{urllib.parse.quote(slug)}/books"
        f"?start_ts={start}&end_ts={end}&resolution=1s&limit=20"
    )
    page = http_json(path, headers)
    data = page.get("data") or {}
    yes = data.get("Yes") or []
    no = data.get("No") or []
    for yb, nb in zip(yes, no):
        ybids = yb.get("bids") or []
        yasks = yb.get("asks") or []
        nbids = nb.get("bids") or []
        nasks = nb.get("asks") or []
        print(
            f"  {yb['t']} Y:B{bids_s(ybids)} A{bids_s(yasks)} | N:B{bids_s(nbids)} A{bids_s(nasks)}"
        )


def bids_s(levels):
    out = []
    for pr, sz in levels[:3]:
        out.append(f"{pr:.3f}@{sz:.0f}")
    return "[" + ",".join(out) + "]" if out else "[]"


def main() -> int:
    key = load_key()
    headers = {"X-API-Key": key}

    print("=== 78600 flip books 15:14:02-15:14:09Z")
    books_yes(headers, "bitcoin-above-78600-on-september-10-2026-12pm-et",
              "2026-09-10T15:14:02Z", "2026-09-10T15:14:09Z")

    print("=== 77600 flicker books 15:44:03-15:44:10Z")
    books_yes(headers, "bitcoin-above-77600-on-september-10-2026-12pm-et",
              "2026-09-10T15:44:03Z", "2026-09-10T15:44:10Z")
    return 0


if __name__ == "__main__":
    sys.exit(main())