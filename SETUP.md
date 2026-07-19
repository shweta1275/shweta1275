# Setup

## 1. The magic repo
Create a public repo named exactly your GitHub username, and put all of
this in it. Its README.md renders at the top of your profile.

    gh repo create <YOUR_USERNAME> --public --clone

## 2. Generate the heatmap + card (works right now)
    python -m venv .venv && source .venv/bin/activate
    pip install -r scripts/requirements.txt
    GITHUB_USERNAME=<YOUR_USERNAME> python scripts/fetch_contributions.py
    python scripts/render_heatmap_svg.py
    python scripts/make_info_card.py      # edit LINES in the script first

## 3. The ASCII portrait (needs your photo, run locally once)
    pip install pillow numpy opencv-python rembg
    python scripts/prep_photo.py path/to/your-photo.jpg
    python scripts/make_ascii_svg.py      # writes ascii-portrait.svg

Tips: a photo with clear light on your face works best; rembg downloads
a model (~170 MB) on first run. Do NOT commit source-photo.jpg or
source-prepped.png if you don't want the raw photo public.

## 4. Push and automate
    git add -A && git commit -m "profile art" && git push

Then in the repo: Actions tab -> "Update profile art" -> Run workflow
(one manual run to confirm it commits a fresh contrib-heatmap.svg).
After that the cron refreshes it daily. The workflow reads your username
automatically from the repo owner — nothing to configure.

## Previews
Every generator accepts STATIC=1 to emit a frozen frame for local
preview (e.g. `STATIC=1 python scripts/render_heatmap_svg.py`).
GitHub plays the animations because they live inside the SVGs (SMIL +
CSS keyframes) — no JS, no external CSS, no token, no third-party
stats service.
