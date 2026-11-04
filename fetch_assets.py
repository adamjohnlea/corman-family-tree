#!/usr/bin/env python3
"""Download the page's assets locally so the site is fully self-contained.

Two jobs, both idempotent (already-downloaded files are skipped):

  fonts/   the woff2 files for Anton and Archivo (SIL Open Font License),
           plus a fonts.css with @font-face rules pointing at the local files.
  faces/   every person's w92 profile thumbnail from TMDB, named by the
           TMDB profile hash.

Run between build.py and generate_index.py:

    python3 build.py && python3 fetch_assets.py && python3 generate_index.py

Stdlib only. Both fonts/ and faces/ are committed to the repo (only cache/ and
.tmdb-key stay untracked). The fonts are OFL, so redistribution is allowed;
the face images come from TMDB (see the attribution in the footer).
"""

import concurrent.futures as cf
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
FACES = os.path.join(HERE, "faces")

# A desktop-Chrome UA so Google Fonts serves woff2 (not ttf).
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

FONT_CSS_URLS = [
    "https://fonts.googleapis.com/css2?family=Anton&display=swap",
    "https://fonts.googleapis.com/css2?family=Archivo:ital,wght@0,400..700;1,400..700&display=swap",
]
KEEP_SUBSETS = {"latin", "latin-ext"}  # skip cyrillic/greek/vietnamese to stay small
IMG_BASE = "https://image.tmdb.org/t/p/w92"


def _get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return data if binary else data.decode("utf-8")


def fetch_fonts():
    os.makedirs(FONTS, exist_ok=True)
    # Pair each "/* subset */" comment with the @font-face block that follows.
    block_re = re.compile(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})")
    url_re = re.compile(r"url\((https://[^)]+\.woff2)\)")
    kept_blocks = []
    downloaded = 0
    for css_url in FONT_CSS_URLS:
        css = _get(css_url)
        for subset, block in block_re.findall(css):
            if subset not in KEEP_SUBSETS:
                continue
            m = url_re.search(block)
            if not m:
                continue
            src = m.group(1)
            fname = src.rsplit("/", 1)[-1]
            fp = os.path.join(FONTS, fname)
            if not os.path.exists(fp):
                with open(fp, "wb") as fh:
                    fh.write(_get(src, binary=True))
                downloaded += 1
            # Rewrite to a repo-root-relative path (fonts.css is inlined into
            # index.html, which sits at the repo root).
            kept_blocks.append(url_re.sub(f"url(fonts/{fname})", block))
    with open(os.path.join(FONTS, "fonts.css"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(kept_blocks) + "\n")
    print(f"fonts: {downloaded} downloaded, {len(kept_blocks)} @font-face rules",
          file=sys.stderr)


def fetch_faces():
    os.makedirs(FACES, exist_ok=True)
    with open(os.path.join(HERE, "data.json"), encoding="utf-8") as fh:
        rows = json.load(fh)["rows"]
    profiles = sorted({r["profile"] for r in rows if r.get("profile")})

    def one(profile):
        name = profile.lstrip("/")
        fp = os.path.join(FACES, name)
        if os.path.exists(fp):
            return 0
        try:
            with open(fp, "wb") as fh:
                fh.write(_get(IMG_BASE + profile, binary=True))
            return 1
        except Exception as exc:  # noqa: BLE001 - one bad image shouldn't halt
            print(f"  face failed {profile}: {exc}", file=sys.stderr)
            if os.path.exists(fp):
                os.remove(fp)
            return 0

    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        got = sum(ex.map(one, profiles))
    total = sum(os.path.getsize(os.path.join(FACES, p.lstrip("/"))) for p in profiles
                if os.path.exists(os.path.join(FACES, p.lstrip("/"))))
    print(f"faces: {got} downloaded, {len(profiles)} total, "
          f"{total / 1_048_576:.1f} MB on disk", file=sys.stderr)


if __name__ == "__main__":
    fetch_fonts()
    fetch_faces()
