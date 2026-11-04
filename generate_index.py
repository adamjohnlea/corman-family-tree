#!/usr/bin/env python3
"""Generate the standalone index.html for The Corman Wall.

Reads ./data.json and inlines it into a single self-contained HTML file with
vanilla JS for sort and filter. The only runtime dependency is TMDB's image
CDN for the faces; there is no framework, no server, and no build step for the
viewer. Run after build.py:

    python3 build.py && python3 generate_index.py

The page markup, styling and interaction all live in this file -- it is the
design source of truth. index.html is a generated artifact.
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
:root{
  --bg:#0b0d11; --panel:#14181f; --panel-2:#10141b;
  --ink:#eef1f6; --ink-dim:#cdd4e0; --mut:#8b94a4;
  --acc:#e8a24b; --line:#20262f; --line-soft:#1a1f28;
  --serif:Georgia,'Iowan Old Style','Times New Roman',serif;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,Roboto,sans-serif;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:var(--sans); font-size:16px; line-height:1.5;
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
}
a{color:inherit}

/* ---- header ---------------------------------------------------------- */
.head{
  position:sticky; top:0; z-index:10;
  background:rgba(11,13,17,.94); backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line);
}
.head-inner{max-width:1040px; margin:0 auto; padding:20px 20px 14px}
.brand{display:flex; align-items:baseline; gap:14px; flex-wrap:wrap}
h1{
  font-family:var(--serif); font-weight:700; font-size:30px;
  letter-spacing:-.01em; margin:0; line-height:1;
}
.count{color:var(--acc); font-weight:700; font-size:15px; letter-spacing:.01em}
.lede{
  color:var(--ink-dim); font-size:15px; line-height:1.55;
  margin:12px 0 0; max-width:62ch;
}
.rough{color:var(--mut); font-size:12.5px; margin:8px 0 0; max-width:62ch}
.rough b{color:var(--ink-dim); font-weight:600}

/* ---- controls -------------------------------------------------------- */
.controls{display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-top:16px}
.field{position:relative; display:flex; align-items:center}
input,select{
  background:var(--panel-2); border:1px solid var(--line); color:var(--ink);
  border-radius:9px; padding:9px 12px; font-size:14px; font-family:inherit;
}
input::placeholder{color:var(--mut)}
input:focus,select:focus{outline:2px solid var(--acc); outline-offset:1px; border-color:transparent}
#q{min-width:190px}
select{cursor:pointer; appearance:none; padding-right:30px;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path d='M1 1l4 4 4-4' stroke='%238b94a4' stroke-width='1.5' fill='none' stroke-linecap='round'/></svg>");
  background-repeat:no-repeat; background-position:right 11px center;
}
.reset{
  background:none; border:1px solid var(--line); color:var(--mut);
  border-radius:9px; padding:9px 12px; font-size:13px; cursor:pointer;
}
.reset:hover{color:var(--ink); border-color:var(--mut)}

.filters{margin-top:12px; display:flex; flex-direction:column; gap:9px}
.filtrow{display:flex; gap:10px; align-items:flex-start; flex-wrap:wrap}
.flabel{
  font-size:10.5px; letter-spacing:.09em; text-transform:uppercase;
  color:var(--mut); min-width:118px; padding-top:6px; flex-shrink:0;
}
.chips{display:flex; gap:7px; flex-wrap:wrap; flex:1}
.chip{
  font-size:12px; padding:5px 11px; border:1px solid var(--line);
  border-radius:999px; color:var(--mut); cursor:pointer;
  display:inline-flex; align-items:center; gap:6px; font-family:inherit;
  background:none; line-height:1.2; transition:border-color .12s,color .12s;
}
.chip:hover{color:var(--ink-dim); border-color:var(--mut)}
.chip .dot{width:8px; height:8px; border-radius:50%; background:#555; flex-shrink:0}
.chip[aria-pressed="true"]{color:#0b0d11; font-weight:650; border-color:transparent}

/* ---- wall ------------------------------------------------------------ */
.wrap{max-width:1040px; margin:0 auto; padding:4px 20px 96px}
.empty{color:var(--mut); padding:60px 4px; text-align:center; font-size:15px}
.row{
  display:grid; grid-template-columns:52px 1fr 26px 1.05fr;
  gap:16px; align-items:center;
  padding:15px 12px 15px 16px;
  border-bottom:1px solid var(--line-soft);
  border-left:3px solid var(--c,transparent);
}
.row:hover{background:var(--panel)}
.face{
  width:52px; height:70px; border-radius:8px; object-fit:cover;
  background:var(--line); display:block;
}
.noface{
  width:52px; height:70px; border-radius:8px; background:var(--line);
  display:flex; align-items:center; justify-content:center;
  color:#5b667e; font-size:20px; font-weight:700; font-family:var(--serif);
}
.name{font-weight:650; font-size:16.5px; letter-spacing:-.005em}
.credit{color:var(--mut); font-size:13.5px; margin-top:3px; line-height:1.45}
.credit .film{color:var(--ink-dim); font-family:var(--serif); font-style:italic; font-size:14.5px}
.credit .role{color:var(--ink); font-weight:600}
.became{
  margin-top:7px; font-size:10.5px; letter-spacing:.07em; text-transform:uppercase;
  color:var(--mut);
}
.became b{font-weight:700}
.arrow{color:var(--acc); font-size:19px; text-align:center; line-height:1}
.after .after-label{
  font-size:10.5px; letter-spacing:.09em; text-transform:uppercase; color:var(--mut);
}
.after .titles{font-size:14.5px; font-weight:600; margin-top:3px; line-height:1.4}
.after .titles .t{font-family:var(--serif); font-style:italic; font-weight:600}
.after .titles .yr{color:var(--mut); font-weight:400; font-style:normal; font-family:var(--sans); font-size:12.5px}
.after .titles .sep{color:var(--line); font-weight:400; margin:0 5px}

/* ---- mobile ---------------------------------------------------------- */
@media(max-width:640px){
  body{font-size:15px}
  .head-inner{padding:16px 16px 12px}
  h1{font-size:25px}
  .wrap{padding:4px 16px 72px}
  #q{min-width:0; flex:1}
  .field{flex:1 1 auto}
  select{flex:1 1 auto}
  .flabel{min-width:0; width:100%; padding-top:0}
  .row{
    grid-template-columns:52px 1fr; gap:12px 14px;
    padding:16px 4px; align-items:start;
  }
  .arrow{display:none}
  .after{grid-column:1 / -1; padding-top:12px; margin-top:2px; border-top:1px dashed var(--line)}
  .after .after-label{color:var(--acc)}
}
@media(prefers-reduced-motion:reduce){*{transition:none !important}}
</style>
</head>
<body>
<header class="head">
  <div class="head-inner">
    <div class="brand">
      <h1>The Corman Wall</h1>
      <span class="count" id="count"></span>
    </div>
    <p class="lede">Roger Corman handed hundreds of unknowns their first real job in movies. Below is where each one started with him, and what they went on to make.</p>
    <p class="rough">Credits come from TMDB, so the data runs <b>rough where a career is thin</b>. The early credit and the later work are what it gets right.</p>
    <div class="controls">
      <div class="field"><input id="q" type="search" placeholder="Search a name..." aria-label="Search by name"></div>
      <select id="sort" aria-label="Sort order">
        <option value="caughtold">Year caught: earliest first</option>
        <option value="caughtnew">Year caught: latest first</option>
        <option value="after">Most work after Corman</option>
        <option value="shuffle">Shuffle</option>
        <option value="name">Name A to Z</option>
      </select>
      <select id="film" aria-label="Filter by first Corman film"><option value="">First Corman film: any</option>__FILMS__</select>
      <button class="reset" id="reset" type="button">Reset</button>
    </div>
    <div class="filters">
      <div class="filtrow"><span class="flabel" id="lbl-job">Their Corman job</span><div class="chips" id="cjob" role="group" aria-labelledby="lbl-job"></div></div>
      <div class="filtrow"><span class="flabel" id="lbl-dec">Decade caught</span><div class="chips" id="cdec" role="group" aria-labelledby="lbl-dec"></div></div>
    </div>
  </div>
</header>
<main class="wrap" id="wall" aria-live="polite"></main>

<script id="wall-data" type="application/json">__DATA__</script>
<script>
"use strict";
const DATA = JSON.parse(document.getElementById("wall-data").textContent);
const ROWS = DATA.rows;

// Craft colors: the Corman-job axis (left border) and "became known for".
const COL = {
  Acting:"#e8625f", Directing:"#f0a93a", Writing:"#63d2bf", Camera:"#5f93e0",
  Editing:"#b58ce6", Production:"#86c56a", Sound:"#dd8cc4",
  "Visual Effects":"#7fd05b", Art:"#e0bd5f", "Costume & Make-Up":"#d98f7a",
};
const col = c => COL[c] || "#8b94a4";
const esc = s => String(s).replace(/[&<>"]/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]));
const el = id => document.getElementById(id);

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

function chip(label, color, pressed, onClick){
  const b = document.createElement("button");
  b.type = "button"; b.className = "chip"; b.setAttribute("aria-pressed", pressed);
  b.onclick = onClick;
  b.innerHTML = (color ? `<span class="dot" style="background:${color}"></span>` : "") + esc(label);
  if (pressed){ b.style.background = color || "#3a4454"; b.style.borderColor = "transparent"; }
  return b;
}
function renderChips(){
  const j = el("cjob"); j.innerHTML = "";
  jobs.forEach(job => j.appendChild(
    chip(job, col(job), fJob.has(job), () => { toggle(fJob, job); renderChips(); draw(); })));
  const d = el("cdec"); d.innerHTML = "";
  decades.forEach(dec => d.appendChild(
    chip(dec + "s", null, fDec.has(dec), () => { toggle(fDec, dec); renderChips(); draw(); })));
}
const toggle = (set, v) => set.has(v) ? set.delete(v) : set.add(v);

const SORTS = {
  caughtold:(a, b) => a.caught - b.caught || a.name.localeCompare(b.name),
  caughtnew:(a, b) => b.caught - a.caught || a.name.localeCompare(b.name),
  after:(a, b) => b.laterCount - a.laterCount || a.name.localeCompare(b.name),
  name:(a, b) => a.name.localeCompare(b.name),
};
function shuffle(a){ for (let i = a.length - 1; i > 0; i--){ const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } }

function rowHTML(r){
  const c = col(r.cormanDept);
  const face = r.profile
    ? `<img class="face" loading="lazy" src="https://image.tmdb.org/t/p/w92${r.profile}" alt="${esc(r.name)}">`
    : `<div class="noface" aria-hidden="true">${esc((r.name[0] || "?"))}</div>`;
  const titles = r.became.slice(0, 3).map(b => {
    const yr = b.tv ? ` <span class="yr">(TV)</span>` : (b.y ? ` <span class="yr">(${b.y})</span>` : "");
    return `<span class="t">${esc(b.t)}</span>${yr}`;
  }).join(`<span class="sep">/</span>`);
  return `${face}
    <div class="before">
      <div class="name">${esc(r.name)}</div>
      <div class="credit"><span class="film">${esc(r.before.film)}</span> &middot; ${r.before.year} &middot; <span class="role">${esc(r.before.role)}</span></div>
      <div class="became">became known for <b style="color:${col(r.craft)}">${esc(r.craft)}</b></div>
    </div>
    <div class="arrow" aria-hidden="true">&rarr;</div>
    <div class="after">
      <div class="after-label">went on to</div>
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

  el("count").textContent = rs.length + (rs.length === 1 ? " career" : " careers");
  const wall = el("wall");
  if (!rs.length){ wall.innerHTML = `<p class="empty">No one matches those filters. <button class="reset" onclick="document.getElementById('reset').click()">Reset</button></p>`; return; }
  const frag = document.createDocumentFragment();
  rs.forEach(r => {
    const a = document.createElement("article");
    a.className = "row";
    a.style.setProperty("--c", col(r.cormanDept));
    a.innerHTML = rowHTML(r);
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

    html = TEMPLATE.replace("__FILMS__", films_opts).replace("__DATA__", blob)
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"wrote index.html ({len(html):,} bytes, {len(data['rows'])} rows)")


def _attr(s):
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def _text(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    main()
