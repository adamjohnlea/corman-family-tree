#!/usr/bin/env python3
"""THROWAWAY SPIKE: before/after wall data. Uses cache; applies before-breakout rule."""
import json, os, urllib.request, urllib.parse, concurrent.futures as cf
from collections import defaultdict
SP=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(SP,"cache")
KEY=open("/Users/adamlea/Documents/Claude Cowork/projects/corman-family-tree/.tmdb-key").read().strip()
BASE="https://api.themoviedb.org/3"
def get(path,**p):
    p["api_key"]=KEY
    ck=(path+"?"+urllib.parse.urlencode({k:v for k,v in p.items() if k!="api_key"})).replace("/","_").replace("?","_").replace("&","_").replace("=","-")
    fp=os.path.join(CACHE,ck+".json")
    if os.path.exists(fp): return json.load(open(fp))
    for a in range(3):
        try:
            with urllib.request.urlopen(f"{BASE}{path}?{urllib.parse.urlencode(p)}",timeout=20) as r: d=json.load(r)
            json.dump(d,open(fp,"w")); return d
        except Exception as e:
            if a==2: return {"_error":str(e)}

cr=get("/person/102429/movie_credits")
PJ={"Director","Producer","Executive Producer","Co-Producer","Associate Producer"}
films={}
for c in cr.get("crew",[]):
    if c.get("job") in PJ and c.get("release_date"):
        films[c["id"]]={"title":c.get("title"),"year":int(c["release_date"][:4])}

# per-film credits -> person roles
KEEP={"Directing","Writing","Camera","Editing","Production","Sound","Art","Acting","Visual Effects"}
# source-material credits: their pre-existing work got adapted, they didn't work for Corman
SOURCE={"Short Story","Comic Book","Novel","Characters","Book","Author","Theatre Play","Play","Opera","Original Material","Graphic Novel","Comic","Based on"}
SELF_CH={"self","himself","herself","narrator","self - narrator"}  # documentary/interview appearances, not real roles
appear=defaultdict(dict)   # pid -> {film_id: role_str}
meta={}
def fc(mid): return mid, get(f"/movie/{mid}/credits")
with cf.ThreadPoolExecutor(max_workers=16) as ex:
    for mid,cc in ex.map(fc, list(films)):
        for p in cc.get("cast",[])[:18]:
            appear[p["id"]][mid]={"job":"Actor","dept":"Acting"}
            meta.setdefault(p["id"],{"name":p.get("name"),"dept":p.get("known_for_department"),"pop":p.get("popularity",0),"profile":p.get("profile_path")})
        for p in cc.get("crew",[]):
            if p.get("job") in SOURCE: continue   # source author, not a Corman collaborator
            if p.get("department") in KEEP:
                appear[p["id"]][mid]={"job":(p.get("job") or p.get("department")),"dept":p.get("department")}
                meta.setdefault(p["id"],{"name":p.get("name"),"dept":p.get("known_for_department"),"pop":p.get("popularity",0),"profile":p.get("profile_path")})

cands=[pid for pid,fm in appear.items() if (meta[pid]["pop"]>=3.0 or len(fm)>=2) and pid!=102429]
def pc(pid): return pid, get(f"/person/{pid}/movie_credits")
rows=[]
BREAKOUT_VOTES=2000   # a film this widely seen = a breakout
BECAME_VOTES=500      # nameable later work
with cf.ThreadPoolExecutor(max_workers=16) as ex:
    for pid,data in ex.map(pc, cands):
        allc=[c for c in data.get("cast",[])+data.get("crew",[]) if c.get("release_date")]
        if not allc: continue
        corman_years=[films[m]["year"] for m in appear[pid] if m in films]
        if not corman_years: continue
        caught=min(corman_years)
        # the specific Corman film that caught them (earliest), + their role
        earliest_film=min((m for m in appear[pid] if m in films), key=lambda m:films[m]["year"])
        ej=appear[pid][earliest_film]
        before={"film":films[earliest_film]["title"],"year":films[earliest_film]["year"],"role":ej["job"]}
        corman_dept=ej["dept"]
        # breakout = first widely-seen film
        bo=[int(c["release_date"][:4]) for c in allc if c.get("vote_count",0)>=BREAKOUT_VOTES]
        breakout=min(bo) if bo else None
        # before-breakout rule
        if breakout is not None and caught>breakout: continue
        corman_ids=set(appear[pid])
        later=[c for c in allc if int(c["release_date"][:4])>=caught and c["id"] not in corman_ids]
        # cleaned "work after": distinct films where they actually acted or held a real crew job
        later_films=set()
        for c in allc:
            if int(c["release_date"][:4])<caught or c["id"] in corman_ids: continue
            if c.get("job")=="Thanks": continue
            ch=(c.get("character") or "").strip().lower()
            if ch in SELF_CH or "archive" in ch: continue
            later_films.add(c["id"])
        later_work=len(later_films)
        became=sorted([c for c in later if c.get("vote_count",0)>=BECAME_VOTES], key=lambda c:c.get("vote_count",0), reverse=True)
        if not became: continue   # must have gone on to something nameable
        seen=set(); became_titles=[]
        for c in became:
            t=c.get("title")
            if t and t not in seen: seen.add(t); became_titles.append({"t":t,"y":int(c["release_date"][:4]),"v":c.get("vote_count",0)})
            if len(became_titles)>=4: break
        rows.append({
            "id":pid,"name":meta[pid]["name"],"craft":meta[pid]["dept"] or "Crew","cormanDept":corman_dept or "Crew","profile":meta[pid]["profile"],
            "caught":caught,"before":before,"breakout":breakout,
            "became":became_titles,"reach":became[0].get("vote_count",0),"laterCount":later_work,
        })
# enrich "went on to" with TMDB's own known_for (the signature work), matched by id
def known_for(row):
    s=get("/search/person",query=row["name"]) or {}
    kf=next((res.get("known_for",[]) for res in s.get("results",[]) if res.get("id")==row["id"]), None)
    out=[]
    if kf:
        for k in sorted(kf,key=lambda k:k.get("vote_count",0),reverse=True):
            t=k.get("title") or k.get("name")
            dt=k.get("release_date") or k.get("first_air_date") or ""
            if t and t!=row["before"]["film"]:
                out.append({"t":t,"y":int(dt[:4]) if dt[:4].isdigit() else None,"v":k.get("vote_count",0),"tv":k.get("media_type")=="tv"})
    return row["id"], out
with cf.ThreadPoolExecutor(max_workers=16) as ex:
    kfmap=dict(ex.map(known_for, rows))
for r in rows:
    kf=kfmap.get(r["id"])
    if kf:
        r["became"]=kf[:4]
        r["reach"]=max([k["v"] for k in kf]+[0])
rows.sort(key=lambda r:(-r["reach"]))
json.dump({"rows":rows,"films":sorted({r["before"]["film"] for r in rows})}, open(os.path.join(SP,"wall.json"),"w"))
import sys
print(f"rows: {len(rows)}", file=sys.stderr)
from collections import Counter
print("crafts:", Counter(r["craft"] for r in rows).most_common(), file=sys.stderr)
for r in rows[:14]:
    print(f"  {r['name']:22} [{r['craft'][:6]:6}] {r['before']['film'][:26]:26}({r['before']['year']}) as {str(r['before']['role'])[:16]:16} -> {r['became'][0]['t']}", file=sys.stderr)
