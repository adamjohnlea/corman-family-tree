# The Corman Wall

One man, Roger Corman, handed hundreds of unknowns their first real job in
movies. Many of them became some of the most important filmmakers and actors
alive. **The Corman Wall** is a before/after page: for each person it shows the
humble grindhouse credit Corman gave them, next to the signature work they went
on to make.

It is a static web page. One HTML file, no framework, no server, no build step
for the viewer. The data comes from the [TMDB](https://www.themoviedb.org/) API.

## What's in here

| File | What it is |
| --- | --- |
| `build.py` | Pulls credits from TMDB, applies the inclusion rule, writes `data.json`. Stdlib only. |
| `generate_index.py` | Inlines `data.json` into the standalone `index.html`. The page markup, CSS and JS live here. |
| `data.json` | The built dataset (one object per person, plus the film list). |
| `index.html` | The finished, standalone page. This is what gets deployed. |
| `design.md` | The locked design spec. |
| `spike/` | The original throwaway spike the build was ported from. |
| `.tmdb-key` | Your TMDB v3 API key. **Local only, never committed** (see `.gitignore`). |
| `cache/` | On-disk cache of every TMDB response. Local only, never committed. |

## Rebuilding the data

You need a TMDB v3 API key (free, from
<https://www.themoviedb.org/settings/api>). Put it in a file named `.tmdb-key`
in the repo root, with nothing else in it:

```bash
echo 'YOUR_TMDB_V3_KEY' > .tmdb-key
```

`.tmdb-key` and `cache/` are both gitignored and must never be committed. Then:

```bash
python3 build.py && python3 generate_index.py
```

`build.py` caches every API response under `cache/`, so the first run makes the
network calls and later runs are fast and offline. It prints a row count and a
sanity sample to stderr. `generate_index.py` reads `data.json` and writes
`index.html` with the data inlined. Open `index.html` in any browser.

## Who makes the wall (the inclusion rule)

A person is included when, by TMDB:

1. They have a cast or crew credit on a film Corman **directed or produced**
   (his whole career; TMDB person `102429`). No company filter: trusting
   TMDB's credits is more accurate than filtering to Corman's own companies,
   which would wrongly drop real involvement.
2. They were **caught before their breakout**: their first Corman credit is at
   or before the first widely-seen film in their filmography (first film with
   >= 2000 TMDB votes). This correctly catches Scorsese, Ron Howard and
   De Niro, whom a fixed "first N years" window would miss.
3. They **went on to real work**: at least one nameable later film and a TMDB
   `known_for`.

**Source authors are excluded.** People credited only for pre-existing source
material ("Novel", "Short Story", "Comic Book", "Characters", and so on, like
Lovecraft or Poe) did not work for Corman; their old work got adapted. Real
screen writers ("Writer", "Screenplay", "Story") stay.

Each row shows one person once. The left border and the "became known for" tag
are colored by craft. "Their Corman job" is what they did on the film; "went on
to" is TMDB's own curated `known_for`, which is why it reads "Shatner →
Star Trek" and not "Shatner → Over the Hedge".

## The four refinements beyond the spike

The spike was a working proof. The build adds four things on top of it, all in
`build.py` except the last:

1. **Date-filtered "went on to."** TMDB's `known_for` is not date-aware, so
   old-timers showed signature films from *before* Corman (John Ireland →
   _Red River_, 1948). The build drops any "went on to" title dated before the
   person's Corman year. Undated entries (usually TV) are kept.

2. **A craft-aware "already established" test.** The vote-based breakout test is
   blind to stars whose famous films predate TMDB's vote density: a 1950s
   leading actress like Dorothy Malone has films with as few votes as Martin
   Scorsese's unseen student shorts, so no vote threshold can tell them apart.
   Instead the build counts a person's **prior billed lead roles** — non-Corman
   films, released before their first Corman credit, where TMDB billed them in
   the top 8 of the cast. **Ten or more** of those marks an established screen
   lead Corman did not launch, and they are excluded.

   The test is deliberately **acting-only** (it runs only when the person's
   primary craft is Acting). That is what keeps actors-turned-directors in:
   Scorsese and Ron Howard acted before Corman, but their craft is Directing
   and Corman launched that. The threshold of ten was tuned against the real
   data: it sits above every genuine Corman launch (Robert De Niro had 4 prior
   leads, Peter Fonda 4, Sylvester Stallone 4) and below the established stars
   it must remove (Dorothy Malone 21, Richard Denning 44, Tab Hunter 32,
   Yvette Mimieux 24). Crew veterans with a famous old film (a cinematographer
   who shot a 2000+ vote classic, say) are already handled by the breakout test
   in rule 2 above.

3. **Deduped credits.** A person can hold several credits on one Corman film.
   Each person gets one row, and the "before" shows a single role. When someone
   also worked on that film in the craft they ultimately became famous for
   (Scorsese both directed and edited _Boxcar Bertha_), the build shows the
   humbler role instead — _Editor_, not Director — because that surprising
   grindhouse credit is the whole point of the wall.

4. **Mobile layout.** Single column at phone width: face with the name and
   credit, then the "went on to" stacked below, controls that wrap, and no
   horizontal scroll. This lives in `generate_index.py`.

## Honest limits

The data is TMDB's, so it is rough where a career is thin. The thing it gets
right is the two ends of the story: the early Corman credit and the later work.
Where the middle is noisy (a background player whose only famous "later" credit
is a bit part), the page says so rather than pretending to rank fame. There is
no fame score. The wall sorts by objective axes (year caught, work after
Corman, name) and lets the names carry their own weight.

A handful of Corman's producer-side peers (for example Samuel Z. Arkoff, who
co-founded AIP) satisfy the mechanical rule and appear on the wall even though
"launched by Corman" is a stretch for them. They are left in rather than
hand-removed, to keep the rule honest and reproducible.

## Deploying to GitHub Pages

The page is a single static file, so Pages serves it directly. With the repo on
GitHub:

1. Settings → Pages → Build and deployment → Source: **Deploy from a branch**.
2. Branch: `main`, folder: `/ (root)`. Save.
3. GitHub serves `index.html` at the Pages URL within a minute or two.

The API key is never needed to *view* the site (the data is already baked into
`index.html`), so nothing secret ever reaches GitHub. Rebuild locally whenever
you want to refresh the data, then commit the updated `data.json` and
`index.html`.
