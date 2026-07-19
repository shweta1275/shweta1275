#!/usr/bin/env python3
"""Hand-author a neofetch-style info card SVG.

Title bar + colored key/value rows that fade/slide in on a stagger.
Edit LINES below to change the content, then re-run.

Usage:
    python scripts/make_info_card.py            # writes info-card.svg
    STATIC=1 python scripts/make_info_card.py   # frozen frame for previews
"""
import os
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

# ---- content (key, value, key-color) -------------------------------------
GREEN = "#39d353"
BLUE = "#58a6ff"
PURPLE = "#bc8cff"
ORANGE = "#ffa657"
DIM = "#7d8590"
FG = "#c9d1d9"

TITLE = "shweta@github"
LINES = [
    ("Now", "AI & Enterprise Transformation Intern @ PwC India", GREEN),
    ("Prev", "RAG pipelines & LLM apps @ CereLabs", GREEN),
    ("Edu", "B.Tech CE (Hons. Data Science) · KJSCE '27", BLUE),
    ("Stack", "Python · TypeScript · React · Spring Boot", PURPLE),
    ("", "FastAPI · MongoDB · Docker · Azure", PURPLE),
    ("Builds", "FXBoard — live FX dashboard (React+Spring)", ORANGE),
    ("", "CredDefer — HITL loan approvals w/ SHAP", ORANGE),
    ("", "VoiceForm — speech → structured data", ORANGE),
    ("Focus", "data engineering · fintech · agentic AI", BLUE),
]
# --------------------------------------------------------------------------

W, H = 490, 300
FONT = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
KEY_W = 72          # px column for keys
LINE_H = 24
TOP = 78


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" aria-label="{esc(TITLE)} info card">',
        # panel
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" '
        f'fill="#0d1117" stroke="#30363d"/>',
        # title bar
        f'<line x1="0" y1="40" x2="{W}" y2="40" stroke="#30363d"/>',
        '<circle cx="22" cy="20" r="6" fill="#ff5f56"/>',
        '<circle cx="42" cy="20" r="6" fill="#ffbd2e"/>',
        '<circle cx="62" cy="20" r="6" fill="#27c93f"/>',
        f'<text x="{W/2}" y="25" text-anchor="middle" font-family="{FONT}" '
        f'font-size="13" fill="{DIM}">{esc(TITLE)}</text>',
    ]

    if not STATIC:
        svg.insert(
            1,
            "<style>"
            ".l{opacity:0;animation:type .5s ease both;}"
            "@keyframes type{from{opacity:0;transform:translateX(-8px);}"
            "to{opacity:1;transform:translateX(0);}}"
            "@media (prefers-reduced-motion:reduce){.l{animation:none;opacity:1;}}"
            "</style>",
        )

    # header line inside the panel
    rows = [("", f"{esc(TITLE)} — hi, I build things that ship", FG)] + [
        (k, esc(v), c) for k, v, c in LINES
    ]

    y = TOP - LINE_H  # header sits one slot above the first key/value
    for i, (key, value, color) in enumerate(rows):
        y = TOP - LINE_H + i * LINE_H
        cls = "" if STATIC else ' class="l"'
        delay = "" if STATIC else f' style="animation-delay:{0.25 + i * 0.18:.2f}s"'
        group = [f"<g{cls}{delay}>"]
        if key:
            group.append(
                f'<text x="24" y="{y}" font-family="{FONT}" font-size="13" '
                f'font-weight="bold" fill="{color}">{esc(key)}</text>'
            )
            group.append(
                f'<text x="{24 + KEY_W}" y="{y}" font-family="{FONT}" '
                f'font-size="13" fill="{FG}">{value}</text>'
            )
        else:
            fill = FG if i == 0 else DIM
            x = 24 if i == 0 else 24 + KEY_W
            group.append(
                f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="13" '
                f'fill="{fill}">{value}</text>'
            )
        group.append("</g>")
        svg.append("".join(group))

    # blinking cursor after the last line (the one loop we allow)
    cy = y + LINE_H
    if STATIC:
        svg.append(f'<rect x="24" y="{cy - 11}" width="8" height="14" fill="{GREEN}"/>')
    else:
        svg.append(
            f'<rect x="24" y="{cy - 11}" width="8" height="14" fill="{GREEN}">'
            f'<animate attributeName="opacity" values="1;0;1" dur="1.2s" '
            f'begin="{0.25 + len(rows) * 0.18:.2f}s" repeatCount="indefinite"/></rect>'
        )

    svg.append("</svg>")
    OUT.write_text("\n".join(svg))
    print(f"Wrote {OUT.name} ({W}x{H})")


if __name__ == "__main__":
    main()
