"""Thematic paths and verified work artwork."""
import json
import re
import threading
import time
from urllib.request import Request, urlopen
from urllib.parse import quote
import catalog

ART_LOCK = threading.BoundedSemaphore(2)


def install(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS work_details(id TEXT PRIMARY KEY,countries TEXT DEFAULT '[]',image TEXT DEFAULT '',checked REAL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS detail_seeds(name TEXT PRIMARY KEY,version INTEGER);
        CREATE INDEX IF NOT EXISTS works_title_type ON works(type,title COLLATE NOCASE,year);
    """)
    seed = catalog.ROOT / "data" / "countries.json"
    if seed.exists():
        version = seed.stat().st_mtime_ns
        previous = conn.execute("SELECT version FROM detail_seeds WHERE name='countries'").fetchone()
        if previous is None or previous[0] != version:
            for ident, countries in json.loads(seed.read_text()).items():
                conn.execute("INSERT INTO work_details(id,countries) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET countries=excluded.countries",
                             (ident, json.dumps(sorted(set(countries)), ensure_ascii=False)))
            conn.execute("INSERT OR REPLACE INTO detail_seeds VALUES('countries',?)", (version,))
            conn.commit()

    for filename in ("work-metadata.json", "verified-awards.json"):
        seed = catalog.ROOT / "data" / filename
        if not seed.exists():
            continue
        version = seed.stat().st_mtime_ns
        previous = conn.execute("SELECT version FROM detail_seeds WHERE name=?", (filename,)).fetchone()
        if previous is not None and previous[0] == version:
            continue
        for item in json.loads(seed.read_text()):
            if filename == "verified-awards.json":
                conn.execute("INSERT OR REPLACE INTO works VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                    item["id"],item["type"],item["title"],
                    catalog.normalized(" ".join(str(item.get(k) or "") for k in ("title","creator","genre"))),
                    str(item.get("year") or ""),item.get("genre",""),item.get("creator",""),item.get("image",""),
                    str(item.get("length") or ""),item.get("score"),item.get("votes"),json.dumps(item["evidence"],ensure_ascii=False),
                    json.dumps(item.get("edition"),ensure_ascii=False),catalog.stamp()))
            else:
                if item.get("image"):
                    conn.execute("INSERT INTO work_details(id,image,checked) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET image=excluded.image,checked=excluded.checked",
                                 (item["id"],item["image"],item.get("checked",0)))
                if item.get("genre"):
                    conn.execute("UPDATE works SET genre=?,creator=CASE WHEN creator='' THEN ? ELSE creator END WHERE id=?",
                                 (item["genre"],item.get("creator",""),item["id"]))
        conn.execute("INSERT OR REPLACE INTO detail_seeds VALUES(?,?)",(filename,version))
        conn.commit()
    source = conn.execute("SELECT message FROM sources WHERE id='awards'").fetchone()
    if source and source[0].startswith("4 distinctions"):
        count=conn.execute("SELECT count(*) FROM works WHERE id LIKE 'awards:%'").fetchone()[0]
        conn.execute("UPDATE sources SET status='partial',count=?,message=? WHERE id='awards'",
                     (count,"Références vérifiées auprès des organisateurs. Couverture internationale à compléter."))
        conn.commit()


def definitions():
    with catalog.connect() as conn:
        rows = conn.execute("SELECT type,genre FROM works WHERE genre != ''").fetchall()
        genres = {}
        for row in rows:
            for genre in row["genre"].split(","):
                genre = genre.strip()
                if genre:
                    genres[(row["type"], genre)] = genres.get((row["type"], genre), 0) + 1
        countries = sorted({name for row in conn.execute("SELECT countries FROM work_details") for name in json.loads(row[0])})
        awards = {}
        for row in conn.execute("SELECT evidence FROM works WHERE id LIKE 'awards:%'"):
            for proof in json.loads(row[0]):
                if proof.get("kind") == "award":
                    awards[proof["label"]] = True
    translations = {"Drama":"Drame","Comedy":"Comédie","Sci-Fi":"Science-fiction","Thriller":"Thriller","Action":"Action","Adventure":"Aventure","Crime":"Policier","Animation":"Animation","Horror":"Horreur","Documentary":"Documentaire","Fantasy":"Fantastique","Romance":"Romance"}
    result = []
    for (kind, genre), count in sorted(genres.items(), key=lambda pair: (-pair[1], pair[0])):
        if count >= 3:
            result.append(dict(id="genre:" + kind + ":" + genre, category="Genres", title=translations.get(genre,genre),
                               subtitle={"film":"Films","book":"Livres","game":"Jeux vidéo"}[kind], type=kind, genre=genre))
    result += [dict(id="country:"+c, category="Pays", title=c, subtitle="Pays d’origine référencé", country=c) for c in countries]
    result += [dict(id="award:"+a, category="Récompenses", title=a, subtitle="Lauréats et nominations référencés", award=a) for a in sorted(awards)]
    return result


def group_items(definition, full=False, page=1):
    conditions, args = [], []
    if definition.get("genre"):
        conditions += ["w.type=?", "(',' || REPLACE(w.genre, ', ', ',') || ',') LIKE ?"]
        args += [definition["type"], "%,"+definition["genre"]+",%"]
    if definition.get("country"):
        conditions.append("EXISTS(SELECT 1 FROM work_details d,json_each(d.countries) c WHERE d.id="+catalog.CANONICAL.replace("evidence","w.evidence").replace(", id)",", w.id)")+" AND c.value=?)")
        args.append(definition["country"])
    if definition.get("award"):
        conditions.append("EXISTS(SELECT 1 FROM json_each(w.evidence) e WHERE json_extract(e.value,'$.label')=?)")
        args.append(definition["award"])
    canonical = catalog.CANONICAL.replace("evidence", "w.evidence").replace(", id)", ", w.id)")
    cte = "WITH ranked AS (SELECT w.*, "+canonical+" AS canonical,ROW_NUMBER() OVER(PARTITION BY "+canonical+" ORDER BY score DESC,w.id) n FROM works w WHERE "+" AND ".join(conditions)+") "
    with catalog.connect() as conn:
        members = [r[0] for r in conn.execute(cte+"SELECT canonical FROM ranked WHERE n=1",args)]
        limit = 60 if full else 32
        rows = conn.execute(cte+"SELECT * FROM ranked WHERE n=1 ORDER BY votes DESC,id LIMIT ? OFFSET ?",args+[limit,(page-1)*limit if full else 0]).fetchall()
    items = []
    for row in rows:
        item = catalog.serialize(row)
        item["id"] = item.pop("canonical")
        item.pop("n",None)
        items.append(item)
    return dict(**definition,total=len(members),members=members,items=items,page=page,pageSize=limit)


def overview(kind="all"):
    import journeys
    return journeys.overview(kind)


def detail(ident,page,kind="all"):
    import journeys
    return journeys.detail(ident,page,kind)


def resolve(items):
    resolved = {}
    with catalog.connect() as conn:
        for item in items:
            if item.get("catalogId"):
                resolved[item["id"]]=item["catalogId"]
                continue
            rows=conn.execute("SELECT DISTINCT "+catalog.CANONICAL+" canonical FROM works WHERE type=? AND title=? COLLATE NOCASE AND (?='' OR year=?)",
                              (item.get("type",""),item.get("title",""),str(item.get("year") or ""),str(item.get("year") or ""))).fetchall()
            if not rows and item.get("type")=="game":
                row=conn.execute("SELECT DISTINCT "+catalog.CANONICAL+" canonical FROM works WHERE type='game' AND title=? COLLATE NOCASE AND (?='' OR year=?)",
                                 (item.get("title","")+" - The Final Cut",str(item.get("year") or ""),str(item.get("year") or ""))).fetchall()
                rows=row
            if len(rows)==1:
                resolved[item["id"]]=rows[0][0]
    return resolved


def artwork(ident):
    if not re.fullmatch(r"(imdb:tt\d+|books:OL\d+W|steam:\d+|metacritic:[a-z0-9-]+)",ident) and not (ident.startswith("awards:") and len(ident)<300):
        return ""
    with ART_LOCK:
        with catalog.connect() as conn:
            existing=conn.execute("SELECT image,checked FROM work_details WHERE id=?",(ident,)).fetchone()
            if existing and time.time()-existing["checked"]<86400*7:
                return existing["image"]
            row=conn.execute("SELECT * FROM works WHERE id=? OR "+catalog.CANONICAL+"=? ORDER BY score DESC LIMIT 1",(ident,ident)).fetchone()
        if not row:
            return ""
        image=row["image"] or ""
        if row["type"]=="game" and not row["id"].startswith("metacritic:"):
            appid=ident.split(":")[1] if ident.startswith("steam:") else ""
            if not appid:
                found=catalog.fetch("https://store.steampowered.com/api/storesearch/",term=row["title"],l="english",cc="fr")
                match=next((i for i in found.get("items",[]) if catalog.normalized(i.get("name",""))==catalog.normalized(row["title"])),None)
                appid=str(match["id"]) if match else ""
            if appid:
                image="https://cdn.cloudflare.steamstatic.com/steam/apps/"+appid+"/library_600x900.jpg"
        elif row["type"]=="film":
            titles = [row["title"], row["title"] + " (" + row["year"] + " film)", row["title"] + " (film)"]
            for title in titles:
                try:
                    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(title.replace(" ", "_"),safe="")
                    request = Request(url,headers={"User-Agent":"Planche/1.1 personal culture catalogue"})
                    with urlopen(request,timeout=8,context=catalog.context()) as response:
                        summary = json.loads(response.read(2*1024*1024))
                except (OSError,ValueError):
                    continue
                art = summary.get("originalimage") or summary.get("thumbnail") or {}
                description = summary.get("description","").lower()
                if "film" in description and art.get("source") and art.get("height",0)>art.get("width",0):
                    image = art["source"]
                    break
        with catalog.connect() as conn:
            conn.execute("INSERT INTO work_details(id,image,checked) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET image=excluded.image,checked=excluded.checked",
                         (ident,image,time.time()))
        return image
