#!/usr/bin/env python3
import json, os, time
SP=os.path.dirname(os.path.abspath(__file__))
data=json.load(open(os.path.join(SP,"wall.json")))
HTML=r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Corman Wall — spike</title>
<style>
:root{--bg:#0c0e12;--panel:#161a22;--ink:#e8ecf2;--mut:#8a93a3;--acc:#e8884b;--line:#242a35}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif}
.head{position:sticky;top:0;z-index:5;background:rgba(12,14,18,.97);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:14px 20px}
.titlerow{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
h1{font-size:19px;margin:0} .count{color:var(--acc);font-weight:700}
.sub{color:var(--mut);font-size:12px} .sub b{color:#cfd6e2}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:10px}
.filtrow{display:flex;gap:8px;align-items:center;margin-top:9px;flex-wrap:wrap}
.flabel{font-size:10px;letter-spacing:.5px;text-transform:uppercase;color:var(--mut);min-width:92px}
input,select{background:#10141b;border:1px solid var(--line);color:var(--ink);border-radius:8px;padding:7px 10px;font-size:13px;font-family:inherit}
input#q{min-width:170px} select{cursor:pointer}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{font-size:11px;padding:4px 10px;border:1px solid var(--line);border-radius:20px;color:var(--mut);cursor:pointer;user-select:none;display:flex;align-items:center;gap:5px}
.chip i{width:8px;height:8px;border-radius:50%;display:inline-block;background:#555}
.reset{color:var(--mut);font-size:12px;cursor:pointer;text-decoration:underline;background:none;border:none}
.wrap{max-width:1000px;margin:0 auto;padding:6px 20px 80px}
.row{display:grid;grid-template-columns:44px 1fr 24px 1fr;gap:12px;align-items:center;padding:12px 10px 12px 14px;border-bottom:1px solid #1b2029;border-left:3px solid transparent}
.row:hover{background:#12161d}
.thumb{width:44px;height:60px;border-radius:7px;object-fit:cover;background:#242a35}
.noimg{width:44px;height:60px;border-radius:7px;background:#20262f;display:flex;align-items:center;justify-content:center;color:#55607a;font-size:16px;font-weight:700}
.nm{font-weight:650;font-size:15px}
.meta{color:var(--mut);font-size:12.5px;margin-top:3px}
.meta .role{color:var(--ink);font-weight:600}
.became-tag{display:inline-block;margin-top:5px;font-size:10.5px;letter-spacing:.3px;text-transform:uppercase;color:var(--mut)}
.became-tag b{font-weight:700}
.arrow{color:var(--acc);font-size:18px;text-align:center}
.after .lead{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.4px}
.after .titles{font-size:14px;font-weight:600;margin-top:2px;line-height:1.35}
.after .titles span{color:var(--mut);font-weight:400}
@media(max-width:640px){.row{grid-template-columns:38px 1fr;row-gap:4px}.arrow{display:none}.after{grid-column:2}.flabel{min-width:0;width:100%}}
</style></head><body>
<div class="head">
  <div class="titlerow"><h1>The Corman Wall</h1><span class="count" id="count"></span><span class="sub">a grindhouse credit → what you know them for · <b>spike, rough data</b></span></div>
  <div class="controls">
    <input id="q" placeholder="search a name...">
    <select id="sort">
      <option value="caughtold">Sort: year (earliest first)</option>
      <option value="caughtnew">Sort: year (latest first)</option>
      <option value="after">Sort: most work after Corman</option>
      <option value="shuffle">Sort: shuffle</option>
      <option value="name">Sort: name A–Z</option>
    </select>
    <select id="film"><option value="">First Corman film: any</option>__FILMS__</select>
    <button class="reset" id="reset">reset all</button>
  </div>
  <div class="filtrow"><span class="flabel">Their Corman job</span><div class="chips" id="cjob"></div></div>
  <div class="filtrow"><span class="flabel">Decade</span><div class="chips" id="cdec"></div></div>
</div>
<div class="wrap" id="wall"></div>
<script>
const ROWS=__DATA__.rows;
const COL={Acting:"#e85d5d",Directing:"#f0a030",Writing:"#6fd0c0",Camera:"#5b8dd9",Editing:"#b088e0",Production:"#86c06a",Sound:"#d98cc0","Visual Effects":"#7fd05b",Art:"#d9b35b"};
const col=c=>COL[c]||"#8a93a3";
const byCount=(key)=>[...new Set(ROWS.map(r=>r[key]))].sort((a,b)=>ROWS.filter(r=>r[key]==b).length-ROWS.filter(r=>r[key]==a).length);
const jobs=byCount("cormanDept");
const decades=[...new Set(ROWS.map(r=>Math.floor(r.caught/10)*10))].sort();
let fJob=new Set(), fDec=new Set();
const el=id=>document.getElementById(id);
function mkchip(label,color,on,click){const d=document.createElement("span");d.className="chip";d.onclick=click;
  d.innerHTML=(color?`<i style="background:${color}"></i>`:"")+label;
  if(on){d.style.background=color||"#3a4454";d.style.color="#0c0e12";d.style.fontWeight=600;d.style.borderColor="transparent";}
  return d;}
function chips(){
  let c=el("cjob");c.innerHTML="";jobs.forEach(j=>c.appendChild(mkchip(j,col(j),fJob.has(j),()=>{fJob.has(j)?fJob.delete(j):fJob.add(j);chips();draw();})));
  c=el("cdec");c.innerHTML="";decades.forEach(d=>c.appendChild(mkchip(d+"s",null,fDec.has(d),()=>{fDec.has(d)?fDec.delete(d):fDec.add(d);chips();draw();})));
}
function draw(){
  const q=el("q").value.trim().toLowerCase(), sort=el("sort").value, film=el("film").value;
  let rs=ROWS.filter(r=>{
    if(q&&!r.name.toLowerCase().includes(q))return false;
    if(fJob.size&&!fJob.has(r.cormanDept))return false;
    if(fDec.size&&!fDec.has(Math.floor(r.caught/10)*10))return false;
    if(film&&r.before.film!==film)return false;
    return true;});
  if(sort==="shuffle"){for(let i=rs.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[rs[i],rs[j]]=[rs[j],rs[i]];}}
  else{const S={caughtnew:(a,b)=>b.caught-a.caught,caughtold:(a,b)=>a.caught-b.caught||a.name.localeCompare(b.name),after:(a,b)=>b.laterCount-a.laterCount,name:(a,b)=>a.name.localeCompare(b.name)};rs.sort(S[sort]);}
  el("count").textContent=rs.length+" careers";
  const w=el("wall");const frag=document.createDocumentFragment();
  rs.forEach(r=>{
    const d=document.createElement("div");d.className="row";d.style.borderLeftColor=col(r.cormanDept);
    const img=r.profile?`<img class="thumb" src="https://image.tmdb.org/t/p/w92${r.profile}">`:`<div class="noimg">${r.name[0]}</div>`;
    const became=r.became.slice(0,3).map(b=>`${b.t}${b.tv?' <span>(TV)</span>':(b.y?` <span>(${b.y})</span>`:'')}`).join(" · ");
    const diff=r.cormanDept!==r.craft;
    d.innerHTML=`${img}
      <div><div class="nm">${r.name}</div>
        <div class="meta">${r.before.film} · ${r.before.year} · <span class="role">${r.before.role}</span></div>
        <div class="became-tag">became known for <b style="color:${col(r.craft)}">${r.craft}</b></div></div>
      <div class="arrow">→</div>
      <div class="after"><div class="lead">went on to</div><div class="titles">${became}</div></div>`;
    frag.appendChild(d);
  });
  w.innerHTML="";w.appendChild(frag);
}
el("q").oninput=draw; el("sort").onchange=draw; el("film").onchange=draw;
el("reset").onclick=()=>{el("q").value="";el("sort").value="caughtold";el("film").value="";fJob.clear();fDec.clear();chips();draw();};
chips();draw();
</script></body></html>"""
films_opts="".join(f'<option value="{f}">{f}</option>' for f in data["films"])
out=HTML.replace("__FILMS__",films_opts).replace("__DATA__",json.dumps(data))
fn=f"wall-{int(time.time())}.html"
open(os.path.join(SP,"site",fn),"w").write(out)
print(fn)
