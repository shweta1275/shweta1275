#!/usr/bin/env python3
"""Render data/contributions.json as an animated SVG contribution calendar.

53-week x 7-day grid of rounded boxes, revealed once with a diagonal
slide-down (CSS keyframes that play on load and freeze — no looping),
plus month labels, a Less->More legend, and a stats footer.

Usage:
    python scripts/render_heatmap_svg.py            # writes contrib-heatmap.svg
    STATIC=1 python scripts/render_heatmap_svg.py   # frozen frame (no animation)
"""
import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

# none -> brightest (level 5 is a neon top end for best-day pop)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 12          # box size
GAP = 3            # gap between boxes
RADIUS = 3
PAD_L = 34         # room for day labels
PAD_T = 28         # room for month labels
PAD_R = 14
PAD_B = 40         # room for legend + footer
BG = "none"        # transparent — sits on GitHub's own background
FG_DIM = "#7d8590"
FONT = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"

STATIC = os.environ.get("STATIC") == "1"


def main() -> None:
    data = json.loads(SRC.read_text())
    days = data["days"]
    stats = data["stats"]
    best_date = stats["best_day"]["date"]

    # Column = week. GitHub weeks start on Sunday (weekday: Mon=0..Sun=6 -> Sun=0..Sat=6).
    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # Sunday -> 0
    cells = []
    for i, d in enumerate(days):
        idx = i + offset
        week, dow = divmod(idx, 7)
        cells.append((week, dow, d))
    n_weeks = cells[-1][0] + 1

    width = PAD_L + n_weeks * (CELL + GAP) - GAP + PAD_R
    height = PAD_T + 7 * (CELL + GAP) - GAP + PAD_B

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" '
        f'aria-label="{stats["total"]} contributions in the last year">'
    ]

    if not STATIC:
        svg.append(
            "<style>"
            ".d{opacity:0;animation:drop .45s cubic-bezier(.2,.7,.3,1) both;}"
            "@keyframes drop{from{opacity:0;transform:translateY(-14px);}"
            "to{opacity:1;transform:translateY(0);}}"
            ".t{opacity:0;animation:fade .6s ease both;}"
            "@keyframes fade{to{opacity:1;}}"
            "@media (prefers-reduced-motion:reduce){.d,.t{animation:none;opacity:1;}}"
            "</style>"
        )

    def text(x, y, s, size=10, fill=FG_DIM, anchor="start", delay=0.0, cls="t"):
        style = f' style="animation-delay:{delay:.2f}s"' if (not STATIC and cls) else ""
        klass = f' class="{cls}"' if (not STATIC and cls) else ""
        return (
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}"{klass}{style}>{s}</text>'
        )

    # Month labels: first week each month appears in
    seen, month_labels = set(), []
    for week, dow, d in cells:
        m = d["date"][:7]
        if m not in seen:
            seen.add(m)
            month_labels.append((week, date.fromisoformat(d["date"]).strftime("%b")))
    for week, label in month_labels[1:]:  # skip partial first month
        svg.append(text(PAD_L + week * (CELL + GAP), PAD_T - 10, label))

    # Day labels
    for dow, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = PAD_T + dow * (CELL + GAP) + CELL - 3
        svg.append(text(2, y, label))

    # Day boxes — diagonal stagger: delay grows with week + dow
    for week, dow, d in cells:
        x = PAD_L + week * (CELL + GAP)
        y = PAD_T + dow * (CELL + GAP)
        level = d["level"]
        if d["date"] == best_date and d["count"] > 0:
            level = 5  # neon top end for the single best day
        fill = PALETTE[min(level, 5)]
        if STATIC:
            svg.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="{RADIUS}" fill="{fill}"><title>{d["count"]} on {d["date"]}</title></rect>'
            )
        else:
            delay = (week + dow) * 0.022
            svg.append(
                f'<rect class="d" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="{RADIUS}" fill="{fill}" style="animation-delay:{delay:.3f}s">'
                f"<title>{d['count']} on {d['date']}</title></rect>"
            )

    # Footer: stats left, legend right
    footer_y = PAD_T + 7 * (CELL + GAP) - GAP + 24
    late = 0.0 if STATIC else (n_weeks + 7) * 0.022
    svg.append(
        text(
            PAD_L,
            footer_y,
            f'{stats["total"]:,} contributions in the last year'
            f'  ·  current streak {stats["current_streak"]}d'
            f'  ·  longest {stats["longest_streak"]}d',
            size=11,
            fill="#c9d1d9",
            delay=late,
        )
    )
    legend_x = width - PAD_R - 6 * (CELL + GAP) - 66
    svg.append(text(legend_x - 8, footer_y, "Less", anchor="end", delay=late))
    for i, c in enumerate(PALETTE):
        svg.append(
            f'<rect x="{legend_x + i * (CELL + GAP)}" y="{footer_y - 10}" '
            f'width="{CELL}" height="{CELL}" rx="{RADIUS}" fill="{c}"/>'
        )
    svg.append(
        text(legend_x + 6 * (CELL + GAP) + 4, footer_y, "More", delay=late)
    )

    svg.append("</svg>")
    OUT.write_text("\n".join(svg))
    print(f"Wrote {OUT.name} ({width}x{height}, {n_weeks} weeks)")


if __name__ == "__main__":
    main()
