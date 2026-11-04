#!/usr/bin/env python3
"""Build data.json for The Corman Wall.

Pulls credits from the TMDB API (v3), caches every response under ./cache/,
applies the inclusion rule, and writes ./data.json.

The inclusion rule (ported from the validated spike):
  1. The person has a cast or crew credit on a film Roger Corman
     DIRECTED or PRODUCED (TMDB person 102429), his whole career.
  2. They were "caught before their breakout": their first Corman credit
     is at or before the first widely-seen film in their filmography
     (first film with >= 2000 TMDB votes).
  3. They went on to real, nameable later work (a TMDB known_for).

Source authors (credited only for pre-existing source material: "Novel",
"Short Story", "Comic Book", etc.) are excluded; real writers stay.

Four refinements beyond the spike (see README):
  1. Date-filter the "went on to" so only signature titles dated at or after
     the Corman credit year are shown.
  2. A secondary "already established" signal to exclude veterans whose
     famous work predates TMDB's vote density (the pre-1970 weak spot).
  3. Dedupe a person's multiple credits on one film to a single, most-senior
     Corman role.
  4. (Mobile layout lives in index.html, not here.)

Stdlib only: urllib, json, concurrent.futures. No requests, no networkx.

Usage:
    python3 build.py        # reads ./.tmdb-key, writes ./data.json

.tmdb-key must exist locally and is never committed (see .gitignore).
"""

import concurrent.futures as cf
import json
import os
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
KEY_FILE = os.path.join(HERE, ".tmdb-key")
BASE = "https://api.themoviedb.org/3"

CORMAN_ID = 102429

# Crew jobs that count as "Corman directed or produced it".
PRODUCER_JOBS = {
    "Director",
    "Producer",
    "Executive Producer",
    "Co-Producer",
    "Associate Producer",
}

# Departments we treat as a real working role on a Corman film.
KEEP_DEPTS = {
    "Directing",
    "Writing",
    "Camera",
    "Editing",
    "Production",
    "Sound",
    "Art",
    "Acting",
    "Visual Effects",
}

# Source-material credits: the person's pre-existing work got adapted, they
# did not actually work for Corman. Legit writers ("Writer"/"Screenplay"/
# "Story") are NOT in this set and stay.
SOURCE_JOBS = {
    "Short Story",
    "Comic Book",
    "Novel",
    "Characters",
    "Book",
    "Author",
    "Theatre Play",
    "Play",
    "Opera",
    "Original Material",
    "Graphic Novel",
    "Comic",
    "Based on",
    "Original Story",  # note: "Story" (a real screen credit) is deliberately kept
}

# Documentary / interview appearances that are not real acting roles; dropped
# from the "work after Corman" count so talking-head cameos don't inflate it.
SELF_CHARACTERS = {"self", "himself", "herself", "narrator", "self - narrator"}

# Role seniority for the "before" credit (refinement 3): when a person holds
# several credits on their earliest Corman film, we show the single most
# senior one. Department sets the main order (highest first):
#   Directing > Writing > Production > Camera > Editing > Art > Sound >
#   Visual Effects > (any other kept department) > Acting
# so a real crew role always outranks an Actor (cast) credit on the same film,
# while someone who ONLY acted still shows as Actor. This is why Martin
# Scorsese, credited as both Director and Editor on Boxcar Bertha, shows as
# Director rather than Editor.
DEPT_RANK = {
    "Directing": 9,
    "Writing": 8,
    "Production": 7,
    "Camera": 6,
    "Editing": 5,
    "Art": 4,
    "Sound": 3,
    "Visual Effects": 2,
    # any other kept department falls here (1), above Acting
    "Acting": 0,
}
DEPT_RANK_OTHER = 1  # a kept department not named above, still above Acting

# Tie-break WITHIN a department (higher first); 0 for anything unlisted. The
# producer ladder is the one the design calls out explicitly.
ROLE_RANK = {
    "Producer": 4,
    "Executive Producer": 3,
    "Co-Producer": 2,
    "Associate Producer": 1,
    "Director of Photography": 2,
    "Cinematography": 2,
    "Screenplay": 2,
    "Writer": 2,
    "Story": 1,
    "Production Design": 2,
    "Art Direction": 2,
}

# Tunables.
BREAKOUT_VOTES = 2000  # a film this widely seen counts as a "breakout"
BECAME_VOTES = 500     # vote floor for a nameable later film (known_for fallback)
CAST_DEPTH = 18        # how far down each Corman film's billed cast we look

# --- Refinement 2: the "already established before Corman" signal ----------
# The vote-based breakout test is blind to stars whose famous films predate
# TMDB's vote density (Dorothy Malone, a leading actress through the 1940s-50s
# whose films never clear 2000 votes, so the vote test wrongly reads her as
# "not yet broken out"). Votes cannot fix this: Malone's real theatrical films
# have as few votes as Martin Scorsese's unseen student shorts, so any vote
# floor either misses her or wrongly nukes Scorsese.
#
# The signal the design actually calls for is "no prior substantial lead". We
# count a person's PRIOR BILLED LEAD roles: non-Corman films released before
# their first Corman credit where TMDB billed them in the top LEAD_ORDER_MAX
# of the cast. PRIOR_LEAD_MIN or more of these marks an established screen lead
# Corman did not launch.
#
# It is deliberately craft-aware -- applied ONLY when the person's primary
# craft (TMDB known_for_department) is Acting. That is what keeps actors-
# turned-directors in: Scorsese and Ron Howard acted before Corman, but their
# craft is Directing and Corman launched that. Crew veterans with famous old
# films are caught by the vote-breakout test instead (e.g. a cinematographer
# who shot a 2000+ vote classic before his first Corman credit).
#
# The threshold is tuned against the real data: it sits above every required
# Corman launch (Robert De Niro 4 prior leads, Peter Fonda 4, Stallone 4) and
# below the established stars it must exclude (Dorothy Malone 21, Richard
# Denning 44, Tab Hunter 32, Yvette Mimieux 24). See README.
LEAD_ORDER_MAX = 8
PRIOR_LEAD_MIN = 10


def _cache_path(path, params):
    key = path + "?" + urllib.parse.urlencode(sorted(params.items()))
    safe = (
        key.replace("/", "_")
        .replace("?", "_")
        .replace("&", "_")
        .replace("=", "-")
    )
    return os.path.join(CACHE, safe + ".json")


def get(path, **params):
    """GET a TMDB endpoint, caching the JSON response to ./cache/."""
    params["api_key"] = KEY
    public = {k: v for k, v in params.items() if k != "api_key"}
    fp = _cache_path(path, public)
    if os.path.exists(fp):
        with open(fp) as fh:
            return json.load(fh)
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                data = json.load(resp)
            with open(fp, "w") as fh:
                json.dump(data, fh)
            return data
        except Exception as exc:  # noqa: BLE001 - network is best-effort, cached
            last_err = exc
    return {"_error": str(last_err)}


def _year(date_str):
    if date_str and date_str[:4].isdigit():
        return int(date_str[:4])
    return None


def corman_films():
    """Return {film_id: {'title', 'year'}} for films Corman directed/produced."""
    credits = get(f"/person/{CORMAN_ID}/movie_credits")
    films = {}
    for c in credits.get("crew", []):
        if c.get("job") in PRODUCER_JOBS:
            yr = _year(c.get("release_date"))
            if yr is not None:
                films[c["id"]] = {"title": c.get("title"), "year": yr}
    return films


def collect_appearances(films):
    """For each Corman film, collect per-person roles.

    Returns (appear, meta):
      appear[pid][film_id] = list of {'job', 'dept'}  (all roles that person
                             held on that film; deduped to one later)
      meta[pid]            = {'name', 'dept', 'pop', 'profile'}
    """
    appear = defaultdict(lambda: defaultdict(list))
    meta = {}

    def fetch(mid):
        return mid, get(f"/movie/{mid}/credits")

    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        for mid, credits in ex.map(fetch, list(films)):
            for p in credits.get("cast", [])[:CAST_DEPTH]:
                appear[p["id"]][mid].append({"job": "Actor", "dept": "Acting"})
                meta.setdefault(p["id"], {
                    "name": p.get("name"),
                    "dept": p.get("known_for_department"),
                    "pop": p.get("popularity", 0),
                    "profile": p.get("profile_path"),
                })
            for p in credits.get("crew", []):
                if p.get("job") in SOURCE_JOBS:
                    continue  # source author, not a Corman collaborator
                if p.get("department") in KEEP_DEPTS:
                    appear[p["id"]][mid].append({
                        "job": p.get("job") or p.get("department"),
                        "dept": p.get("department"),
                    })
                    meta.setdefault(p["id"], {
                        "name": p.get("name"),
                        "dept": p.get("known_for_department"),
                        "pop": p.get("popularity", 0),
                        "profile": p.get("profile_path"),
                    })
    return appear, meta


def pick_role(roles):
    """Refinement 3: collapse a person's several credits on one film to one.

    Pick the single most senior role, department first (see DEPT_RANK), then
    by job within that department (see ROLE_RANK). A real crew role always
    beats an Actor credit on the same film; an Actor-only credit stays Actor.
    """
    def rank(r):
        dept = DEPT_RANK.get(r["dept"], DEPT_RANK_OTHER if r["dept"] else 0)
        return (dept, ROLE_RANK.get(r["job"], 0))
    return max(roles, key=rank)


def person_rows(appear, meta, films):
    """Apply the inclusion rule to every candidate and build raw rows."""
    candidates = [
        pid for pid, fm in appear.items()
        if (meta[pid]["pop"] >= 3.0 or len(fm) >= 2) and pid != CORMAN_ID
    ]

    def fetch(pid):
        return pid, get(f"/person/{pid}/movie_credits")

    rows = []
    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        for pid, data in ex.map(fetch, candidates):
            row = build_row(pid, data, appear, meta, films)
            if row is not None:
                rows.append(row)
    return rows


def build_row(pid, data, appear, meta, films):
    cast = [c for c in data.get("cast", []) if _year(c.get("release_date"))]
    crew = [c for c in data.get("crew", []) if _year(c.get("release_date"))]
    allc = cast + crew
    if not allc:
        return None

    corman_years = [films[m]["year"] for m in appear[pid] if m in films]
    if not corman_years:
        return None
    caught = min(corman_years)

    # The earliest Corman film that caught them, and their most-senior role on it
    # (refinement 3).
    earliest_film = min(
        (m for m in appear[pid] if m in films),
        key=lambda m: films[m]["year"],
    )
    craft = meta[pid]["dept"] or "Crew"
    role = pick_role(appear[pid][earliest_film])
    before = {
        "film": films[earliest_film]["title"],
        "year": films[earliest_film]["year"],
        "role": role["job"],
    }
    corman_dept = role["dept"] or "Crew"
    corman_ids = set(appear[pid])

    # Primary breakout test: first widely-seen film. If they had broken out
    # before Corman caught them, Corman did not launch them.
    breakout_years = [
        _year(c["release_date"]) for c in allc
        if c.get("vote_count", 0) >= BREAKOUT_VOTES
    ]
    breakout = min(breakout_years) if breakout_years else None
    if breakout is not None and caught > breakout:
        return None

    # Refinement 2: craft-aware "already established" signal (see constants).
    # Only actors; crew veterans are handled by the vote-breakout test above.
    if craft == "Acting":
        prior_leads = set()
        for c in cast:
            y = _year(c["release_date"])
            order = c.get("order")
            if (y < caught and c["id"] not in corman_ids
                    and order is not None and order <= LEAD_ORDER_MAX):
                prior_leads.add(c["id"])
        if len(prior_leads) >= PRIOR_LEAD_MIN:
            return None

    # Cleaned "work after Corman": distinct later films where they actually
    # acted or held a real crew job (drop "Thanks" and documentary "Self").
    later_films = set()
    for c in allc:
        y = _year(c["release_date"])
        if y < caught or c["id"] in corman_ids:
            continue
        if c.get("job") == "Thanks":
            continue
        character = (c.get("character") or "").strip().lower()
        if character in SELF_CHARACTERS or "archive" in character:
            continue
        later_films.add(c["id"])
    later_count = len(later_films)

    # Vote-based "became" list (the fallback if known_for is thin), already
    # date-filtered to at/after the Corman year.
    later = [
        c for c in allc
        if _year(c["release_date"]) >= caught and c["id"] not in corman_ids
    ]
    became = sorted(
        (c for c in later if c.get("vote_count", 0) >= BECAME_VOTES),
        key=lambda c: c.get("vote_count", 0),
        reverse=True,
    )
    if not became:
        return None  # must have gone on to something nameable

    seen = set()
    became_titles = []
    for c in became:
        t = c.get("title")
        if t and t not in seen:
            seen.add(t)
            became_titles.append({
                "t": t,
                "y": _year(c["release_date"]),
                "v": c.get("vote_count", 0),
                "tv": False,
            })
        if len(became_titles) >= 4:
            break

    return {
        "id": pid,
        "name": meta[pid]["name"],
        "craft": craft,
        "cormanDept": corman_dept,
        "profile": meta[pid]["profile"],
        "caught": caught,
        "before": before,
        "breakout": breakout,
        "became": became_titles,
        "reach": became[0].get("vote_count", 0),
        "laterCount": later_count,
    }


def enrich_known_for(rows):
    """Replace "became" with TMDB's own known_for (its curated signature list),
    date-filtered so only titles at/after the Corman year show (refinement 1)."""

    def fetch(row):
        search = get("/search/person", query=row["name"]) or {}
        kf = next(
            (r.get("known_for", []) for r in search.get("results", [])
             if r.get("id") == row["id"]),
            None,
        )
        out = []
        if kf:
            for k in sorted(kf, key=lambda k: k.get("vote_count", 0), reverse=True):
                t = k.get("title") or k.get("name")
                dt = k.get("release_date") or k.get("first_air_date") or ""
                y = _year(dt)
                if not t or t == row["before"]["film"]:
                    continue
                # Refinement 1: drop signature titles dated before the Corman
                # credit (e.g. John Ireland -> Red River 1948). Undated entries
                # (usually TV) get the benefit of the doubt and stay.
                if y is not None and y < row["caught"]:
                    continue
                out.append({
                    "t": t,
                    "y": y,
                    "v": k.get("vote_count", 0),
                    "tv": k.get("media_type") == "tv",
                })
        return row["id"], out

    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        kf_map = dict(ex.map(fetch, rows))

    for r in rows:
        kf = kf_map.get(r["id"])
        if kf:  # known_for survived the date filter: use it
            r["became"] = kf[:4]
            r["reach"] = max(k["v"] for k in kf)
        # else: keep the vote-based became list, which is already date-filtered


def main():
    global KEY
    if not os.path.exists(KEY_FILE):
        sys.exit(
            f"error: {KEY_FILE} not found. Create it with your TMDB v3 API key "
            "(it is gitignored and never committed)."
        )
    with open(KEY_FILE) as fh:
        KEY = fh.read().strip()
    os.makedirs(CACHE, exist_ok=True)

    films = corman_films()
    print(f"corman films (directed/produced): {len(films)}", file=sys.stderr)

    appear, meta = collect_appearances(films)
    print(f"people appearing on those films: {len(appear)}", file=sys.stderr)

    rows = person_rows(appear, meta, films)
    enrich_known_for(rows)

    rows.sort(key=lambda r: (r["caught"], r["name"]))
    out = {
        "rows": rows,
        "films": sorted({r["before"]["film"] for r in rows}),
    }
    with open(os.path.join(HERE, "data.json"), "w") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))

    print(f"rows: {len(rows)}", file=sys.stderr)
    print("crafts:", Counter(r["craft"] for r in rows).most_common(), file=sys.stderr)
    for r in rows[:14]:
        print(
            f"  {r['name'][:22]:22} [{r['craft'][:6]:6}] "
            f"{r['before']['film'][:26]:26}({r['before']['year']}) "
            f"as {str(r['before']['role'])[:16]:16} -> {r['became'][0]['t']}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    KEY = ""
    main()
