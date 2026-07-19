#!/usr/bin/env python3
"""Fetch the public GitHub contribution calendar (no token needed).

GitHub serves the calendar as plain HTML at
https://github.com/users/<username>/contributions — the same fragment the
profile page embeds. We parse the day cells and write data/contributions.json
with raw days plus derived stats.

Usage:
    GITHUB_USERNAME=yourname python scripts/fetch_contributions.py
    # or edit USERNAME below
"""
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GITHUB_USERNAME", "YOUR_GITHUB_USERNAME")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"


def fetch_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (profile-readme-art)",
            "Accept": "text/html",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # Tooltip text ("3 contributions on July 4th.") lives in <tool-tip>
    # elements keyed by the cell id. Map id -> count.
    counts_by_id: dict[str, int] = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if not target:
            continue
        text = tip.get_text(" ", strip=True)
        m = re.match(r"(\d+|No)\s+contribution", text)
        if m:
            counts_by_id[target] = 0 if m.group(1) == "No" else int(m.group(1))

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        d = cell["data-date"]
        level = int(cell.get("data-level", 0))
        cid = cell.get("id", "")
        count = counts_by_id.get(cid)
        if count is None:
            # Fallback: some renderings put the text inside the cell
            text = cell.get_text(" ", strip=True)
            m = re.match(r"(\d+|No)\s+contribution", text)
            count = 0 if (not m or m.group(1) == "No") else int(m.group(1))
        days.append({"date": d, "count": count, "level": level})

    days.sort(key=lambda x: x["date"])
    if not days:
        raise SystemExit("No day cells found — GitHub markup may have changed.")
    return days


def derive_stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])

    # Streaks (a contribution day = count > 0). Today may still be 0, so the
    # current streak is allowed to start yesterday.
    active = {d["date"] for d in days if d["count"] > 0}

    def iso(dt: date) -> str:
        return dt.strftime("%Y-%m-%d")

    today = date.fromisoformat(days[-1]["date"])
    cur = 0
    probe = today if iso(today) in active else today - timedelta(days=1)
    while iso(probe) in active:
        cur += 1
        probe -= timedelta(days=1)

    longest = run = 0
    prev = None
    for d in days:
        if d["count"] > 0:
            this = date.fromisoformat(d["date"])
            run = run + 1 if (prev and (this - prev).days == 1) else 1
            longest = max(longest, run)
            prev = this

    monthly: dict[str, int] = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    return {
        "total": total,
        "best_day": {"date": best["date"], "count": best["count"]},
        "current_streak": cur,
        "longest_streak": longest,
        "monthly": monthly,
    }


def main() -> None:
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME
    if username == "YOUR_GITHUB_USERNAME":
        raise SystemExit(
            "Set your username: GITHUB_USERNAME=yourname python scripts/fetch_contributions.py"
        )
    html = fetch_html(username)
    days = parse_days(html)
    payload = {"username": username, "days": days, "stats": derive_stats(days)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(
        f"Wrote {OUT.relative_to(ROOT)} — {len(days)} days, "
        f"{payload['stats']['total']} contributions, "
        f"streak {payload['stats']['current_streak']} (longest {payload['stats']['longest_streak']})"
    )


if __name__ == "__main__":
    main()
