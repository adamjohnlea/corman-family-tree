# The Corman Wall — design

_Design locked 2026-11-03. Built and validated through a working spike first._

## Why this exists

One man, Roger Corman, caught an absurd number of future filmmakers at the very start and let them loose. The piece is an argument: you cannot scroll it without being stunned at how many careers ran through him. Adam wants a stranger to hit it and go "one guy did all this?!"

## What it is

A **before/after wall**. Each row is one person, in one line:

> [face] · the grindhouse credit (film · year · their Corman job) → "became known for [craft]" → their signature later work.

Example rows:
- Martin Scorsese · _Boxcar Bertha_ · 1972 · **Editor** → became known for Directing → _The Wolf of Wall Street, The Departed_
- Dick Miller · _Apache Woman_ · 1955 · **Actor** → Acting → _The Terminator, Gremlins_
- James Cameron · _Battle Beyond the Stars_ · 1980 · **Visual Effects** → Directing → _Avatar, Titanic, The Terminator_

The transformation (humble start → the thing you know them for) is the whole content. It leans on the two things the data is dead certain about: the before and the after.

## Who's on it (the inclusion rule)

Everyone who, by TMDB:
1. Has a cast or crew credit on a film Corman **directed or produced** (his whole career, 1954–today, TMDB person 102429), and
2. Was **caught before their breakout** — their first Corman credit predates their first widely-seen film (first film with >= 2000 TMDB votes). This is "launched," and it correctly includes Scorsese, Ron Howard and De Niro that a fixed "first N years" window wrongly excluded.
3. **Went on to real work** — has at least one nameable later film and a TMDB known_for.

**Excluded:** source authors (people credited only for source material — "Short Story", "Novel", "Comic Book", "Characters" — like Lovecraft, Poe, Stan Lee; their old work got adapted, they didn't work for Corman). Legit writers ("Writer", "Screenplay", "Story") stay.

**No company filter.** Trusting TMDB's credits is more accurate than filtering to Corman's own companies, which would wrongly drop real involvement like _A Time for Killing_ (Harrison Ford, Corman co-directed) and _Boxcar Bertha_ (AIP).

## How it reads and sorts

- **One craft axis = their Corman job** (what they did on the film). What they *became* is reported in the row ("became known for Directing"), not a second filter. Row's left border is colored by the Corman-job craft.
- **"Went on to" = TMDB's own `known_for`** (its curated signature list), not a raw vote-count guess. This is what fixed "Shatner → Star Trek" instead of "Shatner → Over the Hedge."

**Default sort: chronological (year caught, earliest first).** Opens in 1954 and walks his sixty-year run.

**Other sorts:** year caught (latest first) · most work after Corman · shuffle · name A–Z.
- "Most work after Corman" = count of **distinct later films where they actually acted or held a real crew job**, dropping documentary "Self" appearances and "Thanks" credits (those inflated Scorsese from 156 real films to 454).

**Filters:** their Corman job (craft chips) · decade caught · a specific Corman film · free-text name search.

## Known refinements to implement in the build (beyond the spike)

1. **Date-filter the "went on to."** known_for isn't date-aware, so old-timers can show pre-Corman films (John Ireland → _Red River_ 1948). Only show signature titles dated at/after the Corman credit.
2. **Tighten the pre-1970 case.** The vote-based "breakout" test is weak for actors whose famous films predate TMDB's vote density, letting a few established veterans (Dorothy Malone) slip in as if Corman launched them. Add a secondary signal (e.g. they had no prior substantial lead) or flag/exclude.
3. **Dedupe** a person's multiple credits on one film.
4. **Mobile layout** pass (single column, face + stacked before/after).

## Tech and delivery

- **Build:** a Python script hits the TMDB API (key in a local untracked file, never committed), caches every response to disk, applies the rule, and writes a single `data.json`.
- **Page:** one **standalone static HTML** file with the data inlined and the TMDB image CDN for faces. Vanilla JS for sort/filter. No framework, no server.
- **networkx is NOT used.** The original idea was a who-worked-with-whom graph; the design moved to the wall, which is a ranked list, so no graph library is needed.
- **Repo:** a new public GitHub repo, deployed via **GitHub Pages** so Adam has a URL to post. Code lives in a repo under `~/Code` (not in the Cowork notebook).

## Non-goals / anti-goals

- **No faked fame ranking.** There is no honest "fame" number in TMDB (popularity = current trendiness; raw votes = one-blockbuster bias). The wall never pretends to rank importance; it sorts by objective axes and lets names carry their own claim to fame. A "fame dial" would be a lie.
- Not a network graph, not a timeline (both were prototyped and set aside).
- Not exhaustive accuracy to the frame — it's a TMDB-driven piece and says "rough data" honestly where the data is thin.

## What's left to the builder

The spike (`build_wall.py` + `generate_wall.py` in scratchpad) is the working reference. The build turns it into: clean repo code, the four refinements above, a design pass on the page (typography, spacing, mobile, a short header explaining the premise), and GitHub Pages deploy. Exact repo name and the TMDB-key handling in CI/Pages are the two setup details to confirm with Adam.
