#!/usr/bin/env python3
"""Generate the standalone index.html for The Corman Wall.

Reads ./data.json and inlines it into a single self-contained HTML file with
vanilla JS for sort and filter. Runtime dependencies are TMDB's image CDN for
the faces and Google Fonts for the display/text faces; there is no framework,
no server, and no build step for the viewer. Run after build.py:

    python3 build.py && python3 generate_index.py

The page markup, styling and interaction all live in this file -- it is the
design source of truth. index.html is a generated artifact.

Visual direction: a drive-in / exploitation-cinema "marquee". Loud hero
(the sheer scale), quiet rows. Warm near-black, aged-paper ink, one hot
marquee-orange accent. Anton (condensed poster) for the hero and the year
spine; Archivo for everything you actually read.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Roger Corman handed hundreds of unknowns their first job in movies. Where each one started with him, and what they went on to make.">
<title>The Corman Wall</title>
<style>
/* self-hosted fonts (Anton + Archivo, SIL Open Font License) */
__FONTFACE__
:root{
  --bg:#0c0906; --bg-2:#15100a; --ink:#f3ebda; --ink-dim:#d7ccb5;
  --mut:#948673; --faint:#6a5f4f; --line:#2a2017; --line-2:#1d160f;
  --hot:#ff5b24; --hot-dim:#c7461c; --ember:#f0a23a;
  --poster:'Anton',Impact,'Haettenschweiler','Arial Narrow Bold',sans-serif;
  --text:'Archivo',-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:var(--text); font-size:16px; line-height:1.5;
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
}

/* ---- hero / masthead ------------------------------------------------- */
.hero{max-width:1080px; margin:0 auto; padding:46px 24px 30px}
.masthead{
  font-family:var(--poster); font-weight:400; font-size:16px;
  letter-spacing:.22em; color:var(--mut); text-transform:uppercase; margin:0 0 20px;
}
.claim{
  font-family:var(--poster); font-weight:400; line-height:.92;
  font-size:clamp(52px,9.2vw,116px); letter-spacing:.005em; margin:0;
  text-transform:uppercase; color:var(--ink);
}
.claim .n{color:var(--hot)}
.claim .run{display:block; color:var(--ink-dim)}
.bulbs{
  height:12px; margin:22px 0 20px;
  background:radial-gradient(circle at center, var(--hot) 0 2.1px, transparent 2.6px);
  background-size:19px 12px; background-position:left center; background-repeat:repeat-x;
  opacity:.9;
}
.lede{color:var(--ink-dim); font-size:17px; line-height:1.55; margin:0; max-width:60ch}
.rough{color:var(--mut); font-size:13px; margin:10px 0 0; max-width:60ch}
.rough b{color:var(--ink-dim); font-weight:600}

/* ---- controls -------------------------------------------------------- */
.controls{
  position:sticky; top:0; z-index:10; background:rgba(12,9,6,.95);
  backdrop-filter:blur(9px); border-top:1px solid var(--line);
  border-bottom:1px solid var(--line);
}
.controls-inner{max-width:1080px; margin:0 auto; padding:13px 24px}
.ctrl-top{display:flex; align-items:baseline; gap:18px 22px; flex-wrap:wrap}
.showing{
  font-family:var(--poster); font-size:15px; letter-spacing:.08em; color:var(--hot);
  text-transform:uppercase; white-space:nowrap;
}
.spacer{flex:1 1 40px}
input#q,select{
  font-family:inherit; font-size:14px; color:var(--ink);
  background:transparent; border:0; border-bottom:1px solid var(--line);
  border-radius:0; padding:6px 2px;
}
input#q{min-width:150px}
input#q::placeholder{color:var(--mut)}
input#q:focus,select:focus{outline:0; border-bottom-color:var(--hot)}
select{cursor:pointer; appearance:none; padding-right:20px;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='9' height='6' viewBox='0 0 9 6'><path d='M1 1l3.5 3.5L8 1' stroke='%23948673' stroke-width='1.4' fill='none' stroke-linecap='round'/></svg>");
  background-repeat:no-repeat; background-position:right 2px center;
}
select option{background:var(--bg-2); color:var(--ink)}
.reset{
  font-family:inherit; font-size:13px; color:var(--mut); background:none; border:0;
  cursor:pointer; padding:6px 0; border-bottom:1px solid transparent;
}
.reset:hover{color:var(--ink); border-bottom-color:var(--mut)}
.toggles{display:flex; flex-direction:column; gap:7px; margin-top:11px}
.trow{display:flex; gap:12px 10px; align-items:baseline; flex-wrap:wrap}
.tkey{
  font-size:12px; color:var(--faint); min-width:54px; flex-shrink:0; font-style:italic;
}
.chips{display:flex; flex-wrap:wrap; gap:7px 17px; flex:1}
.chip{
  font-family:inherit; font-size:13.5px; color:var(--mut); background:none; border:0;
  padding:2px 1px; cursor:pointer; border-bottom:2px solid transparent; line-height:1.3;
}
.chip:hover{color:var(--ink-dim)}
.chip[aria-pressed="true"]{color:var(--hot); border-bottom-color:var(--hot)}

/* ---- wall ------------------------------------------------------------ */
.wrap{max-width:1080px; margin:0 auto; padding:0 24px 110px}
.empty{color:var(--mut); padding:70px 4px; text-align:center; font-size:16px}
.empty button{color:var(--hot); background:none; border:0; cursor:pointer; font:inherit; text-decoration:underline}
.row{
  display:grid; grid-template-columns:62px 54px minmax(0,1fr) minmax(0,1.12fr);
  gap:20px; align-items:start; padding:19px 4px; border-bottom:1px solid var(--line-2);
}
.row:hover{background:var(--bg-2)}
.year{
  font-family:var(--poster); font-size:28px; line-height:.9; color:var(--hot);
  padding-top:2px; letter-spacing:.01em;
}
.year.dim{color:var(--faint)}  /* a year repeated from the row above recedes */
.face{
  width:54px; height:72px; border-radius:3px; object-fit:cover; background:var(--line);
  display:block; filter:grayscale(1) contrast(1.04) brightness(.94) sepia(.18);
  transition:filter .3s ease;
}
.row:hover .face{filter:none}
.noface{
  width:54px; height:72px; border-radius:3px; background:var(--line); display:flex;
  align-items:center; justify-content:center; color:var(--faint);
  font-family:var(--poster); font-size:26px;
}
.name{font-weight:600; font-size:17px; letter-spacing:-.003em; line-height:1.2}
.credit{color:var(--mut); font-size:14px; margin-top:4px; line-height:1.45}
.credit .film{color:var(--ink-dim); font-style:italic; font-weight:500}
.credit .yr{color:var(--faint)}
.credit .role{color:var(--ink-dim)}
.after{border-left:1px solid var(--line); padding-left:20px; min-width:0}
.craft{font-size:13px; color:var(--hot); margin-bottom:5px; line-height:1.3}
.titles{font-size:15px; line-height:1.5; color:var(--ink)}
.titles .t{font-style:italic; font-weight:500}
.titles .yr{color:var(--faint); font-style:normal; font-size:12.5px}
.titles .sep{color:var(--line); margin:0 7px}

/* ---- mobile ---------------------------------------------------------- */
@media(max-width:680px){
  body{font-size:15px}
  .hero{padding:34px 18px 22px}
  .claim{font-size:clamp(44px,13vw,70px)}
  .controls-inner{padding:12px 18px}
  .wrap{padding:0 18px 80px}
  input#q{flex:1 1 130px; min-width:0}
  .row{
    grid-template-columns:44px 1fr; gap:4px 14px; padding:20px 2px; align-items:start;
  }
  .year{grid-row:1 / span 2; font-size:24px}
  .face{grid-column:2; width:50px; height:66px; margin-bottom:4px}
  .nmwrap{grid-column:2}
  .after{
    grid-column:1 / -1; border-left:0; padding-left:0; margin-top:12px;
    padding-top:12px; border-top:1px solid var(--line-2);
  }
}
/* ---- footer ---------------------------------------------------------- */
.foot{
  max-width:1080px; margin:0 auto; padding:26px 24px 60px;
  border-top:1px solid var(--line); color:var(--mut); font-size:13px; line-height:1.6;
}
.foot a{color:var(--ink-dim); text-decoration:underline; text-underline-offset:2px}
.foot a:hover{color:var(--hot)}
@media(max-width:680px){.foot{padding:22px 18px 48px}}
@media(prefers-reduced-motion:reduce){*{transition:none !important}}
</style>
</head>
<body>
<header class="hero">
  <p class="masthead">The Corman Wall</p>
  <h1 class="claim">One man.<br><span class="n" id="bigN">600</span> careers.<br><span class="run"><span id="runFrom">1954</span> &mdash; today.</span></h1>
  <div class="bulbs" aria-hidden="true"></div>
  <p class="lede">Roger Corman put hundreds of unknowns to work on cheap, fast movies, then watched them become some of the most important filmmakers and actors alive. Here is where each one started with him, and what they made next.</p>
  <p class="rough">Credits come from TMDB, so the record runs <b>rough where a career is thin</b>. The early job and the later work are what it gets right.</p>
</header>

<div class="controls">
  <div class="controls-inner">
    <div class="ctrl-top">
      <span class="showing" id="showing"></span>
      <span class="spacer"></span>
      <input id="q" type="search" placeholder="Search a name" aria-label="Search by name">
      <select id="sort" aria-label="Sort order">
        <option value="caughtold">Earliest first</option>
        <option value="caughtnew">Latest first</option>
        <option value="after">Most work after Corman</option>
        <option value="shuffle">Shuffle</option>
        <option value="name">Name A to Z</option>
      </select>
      <select id="film" aria-label="Filter by first Corman film"><option value="">Any Corman film</option>__FILMS__</select>
      <button class="reset" id="reset" type="button">Reset</button>
    </div>
    <div class="toggles">
      <div class="trow"><span class="tkey">job</span><div class="chips" id="cjob" role="group" aria-label="Filter by their Corman job"></div></div>
      <div class="trow"><span class="tkey">decade</span><div class="chips" id="cdec" role="group" aria-label="Filter by decade caught"></div></div>
    </div>
  </div>
</div>

<main class="wrap" id="wall" aria-live="polite"></main>

<footer class="foot">
  <p>Faces and credits come from <a href="https://www.themoviedb.org" target="_blank" rel="noopener">TMDB</a>. This product uses the TMDB API but is not endorsed or certified by TMDB.</p>
</footer>

<script id="wall-data" type="application/json">__DATA__</script>
<script>
"use strict";
const DATA = JSON.parse(document.getElementById("wall-data").textContent);
const ROWS = DATA.rows;

const esc = s => String(s).replace(/[&<>"]/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));
const el = id => document.getElementById(id);

// Craft as a plain lowercase noun ("became a director") -- no color coding.
const CRAFT_NOUN = {
  Acting:"an actor", Directing:"a director", Writing:"a writer",
  Camera:"a cinematographer", Editing:"an editor", Production:"a producer",
  Sound:"a sound mixer", Art:"an art director",
  "Visual Effects":"a visual-effects artist", "Costume & Make-Up":"a costume and make-up artist",
};
const craftNoun = c => CRAFT_NOUN[c] || ("known for " + String(c).toLowerCase());

// Filter options ordered by frequency (most common first).
const freq = key => {
  const c = {};
  ROWS.forEach(r => { c[r[key]] = (c[r[key]] || 0) + 1; });
  return Object.keys(c).sort((a, b) => c[b] - c[a]);
};
const jobs = freq("cormanDept");
const decade = r => Math.floor(r.caught / 10) * 10;
const decades = [...new Set(ROWS.map(decade))].sort((a, b) => a - b);

const fJob = new Set(), fDec = new Set();
const toggle = (set, v) => set.has(v) ? set.delete(v) : set.add(v);

function chip(label, pressed, onClick){
  const b = document.createElement("button");
  b.type = "button"; b.className = "chip"; b.setAttribute("aria-pressed", pressed);
  b.textContent = label; b.onclick = onClick;
  return b;
}
function renderChips(){
  const j = el("cjob"); j.innerHTML = "";
  jobs.forEach(job => j.appendChild(
    chip(job, fJob.has(job), () => { toggle(fJob, job); renderChips(); draw(); })));
  const d = el("cdec"); d.innerHTML = "";
  decades.forEach(dec => d.appendChild(
    chip(dec + "s", fDec.has(dec), () => { toggle(fDec, dec); renderChips(); draw(); })));
}

const SORTS = {
  caughtold:(a, b) => a.caught - b.caught || a.name.localeCompare(b.name),
  caughtnew:(a, b) => b.caught - a.caught || a.name.localeCompare(b.name),
  after:(a, b) => b.laterCount - a.laterCount || a.name.localeCompare(b.name),
  name:(a, b) => a.name.localeCompare(b.name),
};
function shuffle(a){ for (let i = a.length - 1; i > 0; i--){ const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } }

function rowHTML(r, dimYear){
  const face = r.profile
    ? `<img class="face" loading="lazy" src="faces${r.profile}" alt="${esc(r.name)}">`
    : `<div class="noface" aria-hidden="true">${esc(r.name[0] || "?")}</div>`;
  const titles = r.became.slice(0, 3).map(b => {
    const yr = b.tv ? ` <span class="yr">(TV)</span>` : (b.y ? ` <span class="yr">(${b.y})</span>` : "");
    return `<span class="t">${esc(b.t)}</span>${yr}`;
  }).join(`<span class="sep">/</span>`);
  return `<div class="year${dimYear ? " dim" : ""}">${r.caught}</div>
    ${face}
    <div class="nmwrap">
      <div class="name">${esc(r.name)}</div>
      <div class="credit"><span class="film">${esc(r.before.film)}</span> <span class="yr">(${r.before.year})</span>, <span class="role">${esc(String(r.before.role).toLowerCase())}</span></div>
    </div>
    <div class="after">
      <div class="craft">became ${esc(craftNoun(r.craft))}</div>
      <div class="titles">${titles}</div>
    </div>`;
}

function draw(){
  const q = el("q").value.trim().toLowerCase();
  const sort = el("sort").value;
  const film = el("film").value;
  let rs = ROWS.filter(r => {
    if (q && !r.name.toLowerCase().includes(q)) return false;
    if (fJob.size && !fJob.has(r.cormanDept)) return false;
    if (fDec.size && !fDec.has(decade(r))) return false;
    if (film && r.before.film !== film) return false;
    return true;
  });
  if (sort === "shuffle") shuffle(rs);
  else rs.sort(SORTS[sort]);

  const full = rs.length === ROWS.length;
  el("showing").textContent = full
    ? rs.length + " careers"
    : rs.length + " of " + ROWS.length;
  const wall = el("wall");
  if (!rs.length){
    wall.innerHTML = `<p class="empty">No one matches that. <button onclick="document.getElementById('reset').click()">Clear the filters</button></p>`;
    return;
  }
  const frag = document.createDocumentFragment();
  let lastYear = null;
  rs.forEach(r => {
    const a = document.createElement("article");
    a.className = "row";
    a.innerHTML = rowHTML(r, r.caught === lastYear);
    lastYear = r.caught;
    frag.appendChild(a);
  });
  wall.innerHTML = "";
  wall.appendChild(frag);
}

el("q").oninput = draw;
el("sort").onchange = draw;
el("film").onchange = draw;
el("reset").onclick = () => {
  el("q").value = ""; el("sort").value = "caughtold"; el("film").value = "";
  fJob.clear(); fDec.clear(); renderChips(); draw();
};

// Hero scale, from the data itself.
el("bigN").textContent = ROWS.length;
el("runFrom").textContent = Math.min(...ROWS.map(r => r.caught));

renderChips();
draw();
</script>
</body>
</html>
"""


def main():
    with open(os.path.join(HERE, "data.json"), encoding="utf-8") as fh:
        data = json.load(fh)

    films_opts = "".join(
        f'<option value="{_attr(f)}">{_text(f)}</option>' for f in data["films"]
    )
    # Inline the data; escape "</" so no title can close the <script> tag early.
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    # Inline the self-hosted @font-face rules (no third-party font request).
    with open(os.path.join(HERE, "fonts", "fonts.css"), encoding="utf-8") as fh:
        fontface = fh.read().strip()

    html = (TEMPLATE
            .replace("__FONTFACE__", fontface)
            .replace("__FILMS__", films_opts)
            .replace("__DATA__", blob))
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"wrote index.html ({len(html):,} bytes, {len(data['rows'])} rows)")


def _attr(s):
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def _text(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    main()
