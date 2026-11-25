"""Public-source catalogue. Python standard library, persistent SQLite, resumable imports."""
import csv
import gzip
import fcntl
import html
import io
import json
import os
import re
import sqlite3
import ssl
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "catalog.sqlite3"
CANONICAL = "COALESCE(json_extract(evidence, '$[0].canonical'), id)"
CACHE = ROOT / "data" / "cache"
LOCK = threading.Lock()
RULES = {
    "imdb": "IMDb ≥ 7/10 · au moins 1 000 votes",
    "books": "Édition française identifiée · Goodreads en priorité, Open Library lorsque le rapprochement reste à vérifier",
    "goodreads": "Notes et fiches Goodreads rapprochées par titre et auteur · éditions françaises conservées",
    "metacritic": "Metacritic ≥ 70/100 · au moins 10 critiques professionnelles",
    "awards": "Prix ou nomination recensé dans Wikidata · sélection internationale",
}
# Awards apply to works, never to their authors as a substitute for a work award.
AWARDS = {
    "film": ["Q102427", "Q154590", "Q179808", "Q209459"],
    "book": ["Q187300", "Q18945", "Q160082", "Q2052291", "Q833633", "Q255032", "Q266012"],
    "game": ["Q78762377"],
}


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    if not DB.exists():
        parts = sorted(ROOT.joinpath("data", "seed").glob("*.part"))
        if parts:
            # Startup restores the packaged snapshot before accepting requests.
            temporary = DB.with_suffix(".restore")
            compressed = b"".join(part.read_bytes() for part in parts)
            temporary.write_bytes(gzip.decompress(compressed))
            os.replace(temporary, DB)
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS works(
            id TEXT PRIMARY KEY, type TEXT NOT NULL, title TEXT NOT NULL,
            search TEXT NOT NULL, year TEXT, genre TEXT, creator TEXT,
            image TEXT, length TEXT, score REAL, votes INTEGER,
            evidence TEXT NOT NULL, edition TEXT, updated TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS works_type ON works(type);
        CREATE TABLE IF NOT EXISTS sources(
            id TEXT PRIMARY KEY, status TEXT, message TEXT, updated TEXT, count INTEGER
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS works_canonical ON works(" + CANONICAL + ")")
    import paths
    paths.install(conn)
    import metacritic
    metacritic.install(conn)
    import goodreads_books
    goodreads_books.install(conn)
    return conn


def normalized(text):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


def context():
    # Some macOS Python installations lack a default CA bundle.
    if Path("/etc/ssl/cert.pem").is_file():
        return ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    return ssl.create_default_context()


def request(url, params=None):
    if params:
        url += "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "Planche/1.1 (personal cultural catalogue)", "Accept": "application/json"})
    for attempt in range(3):
        try:
            return urlopen(req, timeout=90, context=context())
        except OSError as error:
            if attempt == 2:
                raise
            time.sleep(65 if getattr(error, "code", None) == 429 else 2 ** attempt)


def fetch(url, **params):
    with request(url, params) as response:
        return json.load(response)


def source_status(source, status, message, count=None):
    with connect() as conn:
        previous = conn.execute("SELECT count(*) AS count FROM works WHERE id LIKE ?", (source + ":%",)).fetchone()
        conn.execute("INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?)",
                     (source, status, message, stamp(), count if count is not None else previous["count"] if previous else 0))
    print(source, status, message, flush=True)


def store(source, items):
    # Successful source refresh is atomic. Other sources and the previous snapshot survive failures.
    with connect() as conn:
        conn.execute("DELETE FROM works WHERE id LIKE ?", (source + ":%",))
        for item in items:
            conn.execute("INSERT OR REPLACE INTO works VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                item["id"], item["type"], item["title"],
                normalized(" ".join(str(item.get(k) or "") for k in ("title", "original", "creator", "genre"))),
                str(item.get("year") or ""), item.get("genre", ""), item.get("creator", ""),
                item.get("image", ""), str(item.get("length") or ""), item.get("score"),
                item.get("votes"), json.dumps(item["evidence"], ensure_ascii=False),
                json.dumps(item.get("edition"), ensure_ascii=False), stamp()
            ))
    source_status(source, "ready", "Collecte terminée.", len(items))


def download(name):
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / name
    if target.exists() and time.time() - target.stat().st_mtime < 86400:
        return target
    temp = target.with_suffix(".part")
    try:
        with request("https://datasets.imdbws.com/" + name) as remote, temp.open("wb") as output:
            while chunk := remote.read(1024 * 1024):
                output.write(chunk)
        os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)
    return target


def imdb():
    source_status("imdb", "running", "Téléchargement des notes IMDb…")
    ratings = {}
    with gzip.open(download("title.ratings.tsv.gz"), "rt", encoding="utf-8") as stream:
        for row in csv.DictReader(stream, delimiter="\t", quoting=csv.QUOTE_NONE):
            score, votes = float(row["averageRating"]), int(row["numVotes"])
            if score >= 7 and votes >= 1000:
                ratings[row["tconst"]] = (score, votes)
    source_status("imdb", "running", "Lecture des titres, courts métrages et documentaires…")
    items = []
    with gzip.open(download("title.basics.tsv.gz"), "rt", encoding="utf-8") as stream:
        for row in csv.DictReader(stream, delimiter="\t", quoting=csv.QUOTE_NONE):
            ident = row["tconst"]
            if ident not in ratings or row["titleType"] not in ("movie", "short", "tvMovie", "tvShort", "video"):
                continue
            score, votes = ratings[ident]
            clean = lambda k: "" if row[k] == "\\N" else row[k]
            items.append(dict(id="imdb:" + ident, type="film", title=row["primaryTitle"], original=row["originalTitle"],
                              year=clean("startYear"), genre=clean("genres").replace(",", ", "),
                              length=clean("runtimeMinutes"), score=score * 10, votes=votes,
                              evidence=[dict(source="IMDb", kind="rating", value=score, scale=10, votes=votes,
                                             url="https://www.imdb.com/title/" + ident + "/", checked=stamp())]))
    if not items:
        raise ValueError("Aucun film reçu, ancien catalogue conservé.")
    store("imdb", items)


def book_item(hit, evidence=None):
    editions = hit.get("editions", {}).get("docs", [])
    edition = next((e for e in editions if "fre" in e.get("language", [])), None)
    if not edition:
        return None
    cover = edition.get("cover_i") or hit.get("cover_i")
    return dict(id="books:" + hit["key"].split("/")[-1], type="book", title=edition.get("title") or hit["title"],
                original=hit["title"], year=hit.get("first_publish_year"),
                creator=", ".join(hit.get("author_name", [])), image=f"https://covers.openlibrary.org/b/id/{cover}-M.jpg" if cover else "",
                score=float(hit.get("ratings_average") or 0) * 20 or None,
                votes=hit.get("ratings_count"), edition=dict(title=edition["title"], url="https://openlibrary.org" + edition["key"], language="français"),
                evidence=evidence if evidence is not None else [dict(source="Open Library", kind="rating", value=round(hit["ratings_average"], 2), scale=5,
                                votes=hit["ratings_count"], url="https://openlibrary.org" + hit["key"], checked=stamp())])


BOOK_FIELDS = "key,title,author_name,first_publish_year,cover_i,ratings_average,ratings_count,editions,editions.key,editions.title,editions.language,editions.cover_i"


def books():
    items, offset, total = [], 0, None
    while total is None or offset < total:
        source_status("books", "running", f"Lecture des livres avec édition française · {offset} / {total or '…'}")
        data = fetch("https://openlibrary.org/search.json", q="language:fre ratings_count:[20 TO *]",
                     fields=BOOK_FIELDS, lang="fr", sort="key", offset=offset, limit=100)
        total = data.get("numFound", data.get("num_found", 0))
        hits = data.get("docs", [])
        if not hits and offset < total:
            raise ValueError("Pagination incomplète, ancien catalogue conservé.")
        for hit in hits:
            if float(hit.get("ratings_average") or 0) >= 3.5 and int(hit.get("ratings_count") or 0) >= 20:
                item = book_item(hit)
                if item:
                    items.append(item)
        offset += len(hits)
        time.sleep(1)
    if not items:
        raise ValueError("Aucun livre vérifiable reçu.")
    store("books", items)


def steam_rows(markup):
    """Read only search app rows, never bundles or recommendations."""
    rows = []
    for block in re.findall(r'<a\b[^>]*class="search_result_row\b.*?</a>', markup, re.S):
        ident = re.search(r'data-ds-appid="(\d+)"', block)
        title = re.search(r'<span class="title">(.*?)</span>', block, re.S)
        tooltip = re.search(r'data-tooltip-html="([^"]+)"', block)
        if not (ident and title and tooltip):
            continue
        summary = html.unescape(tooltip.group(1))
        match = re.search(r"(\d+)% of the ([\d,]+) user reviews", summary)
        if not match:
            continue
        percent, votes = int(match[1]), int(match[2].replace(",", ""))
        image = re.search(r'<img src="([^"]+)"', block)
        released = re.search(r'class="search_released[^"]*">\s*(.*?)\s*</div>', block, re.S)
        year = re.search(r"\b\d{4}\b", released[1]) if released else None
        rows.append(dict(id="steam:" + ident[1], type="game", title=html.unescape(title[1]),
                         year=year[0] if year else "", image=html.unescape(image[1]) if image else "",
                         score=percent, votes=votes,
                         evidence=[dict(source="Steam", kind="rating", value=percent, scale=100, votes=votes,
                                        label="Avis positifs · langue anglaise", url="https://store.steampowered.com/app/" + ident[1] + "/", checked=stamp())]))
    return rows


def steam():
    offset, total, seen_pages = 0, None, set()
    # Persist each chunk so a stopped run can resume without losing verified games.
    with connect() as conn:
        row = conn.execute("SELECT message FROM sources WHERE id='steam-cursor'").fetchone()
        if row:
            offset = ((int(row["message"]) + 99) // 100) * 100
    start_offset = offset
    while total is None or offset < total:
        source_status("steam", "running", f"Lecture du magasin Steam · {offset} / {total or '…'}")
        data = fetch("https://store.steampowered.com/search/results/", start=offset, count=100,
                     sort_by="Reviews_DESC", category1=998, infinite=1, json=1, l="english", cc="fr",
                     ignore_preferences=1, supportedlang="")
        markup = data.get("results_html", "")
        ids = tuple(re.findall(r'data-ds-itemkey="(App_\d+)"', markup))
        total = int(data.get("total_count", 0))
        if data.get("success") and not ids and offset >= total:
            break
        if not data.get("success") or not ids or ids in seen_pages:
            raise ValueError("Réponse Steam incomplète. Les jeux déjà collectés sont conservés.")
        seen_pages.add(ids)
        total = int(data.get("total_count", 0))
        parsed = steam_rows(markup)
        if not parsed and "data-tooltip-html" in markup:
            raise ValueError("Format des notes Steam non reconnu, reprise possible.")
        qualified = [i for i in parsed if i["score"] >= 80 and i["votes"] >= 100]
        # Merge chunks with the verified cache. At a full refresh, refresh every known row.
        with connect() as conn:
            for item in qualified:
                conn.execute("INSERT OR REPLACE INTO works VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                    item["id"], "game", item["title"], normalized(item["title"]), item["year"], "", "",
                    item["image"], "", item["score"], item["votes"], json.dumps(item["evidence"]), "null", stamp()))
            for item in parsed:
                if item not in qualified:
                    conn.execute("DELETE FROM works WHERE id=?", (item["id"],))
            offset += 100
            conn.execute("INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?)", ("steam-cursor", "cursor", str(offset), stamp(), 0))
        time.sleep(1.2)
    with connect() as conn:
        conn.execute("DELETE FROM sources WHERE id='steam-cursor'")
        count = conn.execute("SELECT count(*) FROM works WHERE type='game' AND id LIKE 'steam:%'").fetchone()[0]
    source_status("steam", "ready", f"Parcours Steam terminé · {offset - start_offset} résultats examinés dans cette session.", count)


def awards():
    source_status("awards", "running", "Lecture des prix et nominations internationaux dans Wikidata…")
    api = "https://www.wikidata.org/w/api.php"
    award_types = {q: kind for kind, ids in AWARDS.items() for q in ids}
    awards_data = fetch(api, action="wbgetentities", ids="|".join(award_types), props="labels", languages="fr|en", format="json")["entities"]
    def label(entity):
        labels = entity.get("labels", {})
        return labels.get("fr", labels.get("en", {})).get("value", "")
    labels = {q: label(e) for q, e in awards_data.items()}
    wanted = {}
    for award, kind in award_types.items():
        for relation in ("P166", "P1411"):
            source_status("awards", "running", "Lecture · " + labels[award])
            offset = 0
            while True:
                response = fetch(api, action="query", list="search",
                                 srsearch=f"haswbstatement:{relation}={award}",
                                 srnamespace=0, srlimit=100, sroffset=offset, format="json")
                if "query" not in response:
                    raise ValueError("Recherche Wikidata indisponible.")
                for hit in response["query"]["search"]:
                    if re.fullmatch(r"Q\d+", hit["title"]):
                        wanted[hit["title"]] = True
                continuation = response.get("continue")
                if not continuation:
                    break
                offset = continuation["sroffset"]
                time.sleep(.5)
    ids, pending = list(wanted), {}
    for index in range(0, len(ids), 40):
        source_status("awards", "running", f"Vérification des récompenses · {index} / {len(ids)}")
        entities = fetch(api, action="wbgetentities", ids="|".join(ids[index:index + 40]),
                         props="labels|claims", languages="fr|en", format="json")["entities"]
        for ident, entity in entities.items():
            claims = entity.get("claims", {})
            humans = any(c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id") == "Q5" for c in claims.get("P31", []))
            for relation in ("P166", "P1411"):
                for claim in claims.get(relation, []):
                    award = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
                    if award not in award_types:
                        continue
                    work_id = ident
                    if humans:
                        # Awarded authors are linked only through the explicitly awarded work.
                        qualifiers = claim.get("qualifiers", {}).get("P1686", [])
                        if not qualifiers:
                            continue
                        work_id = qualifiers[0].get("datavalue", {}).get("value", {}).get("id")
                        if not work_id:
                            continue
                    evidence = dict(source="Wikidata", kind="award", label=labels[award],
                                    nomination=relation == "P1411",
                                    url="https://www.wikidata.org/wiki/" + ident, checked=stamp())
                    entry = pending.setdefault(work_id, dict(type=award_types[award], evidence=[], entity=None))
                    signature = (evidence["label"], evidence["nomination"])
                    if not any((e["label"], e["nomination"]) == signature for e in entry["evidence"]):
                        entry["evidence"].append(evidence)
                    if not humans:
                        entry["entity"] = entity
        time.sleep(.5)
    baseline = ROOT / "data" / "verified-awards.json"
    items = json.loads(baseline.read_text()) if baseline.exists() else []
    for ident, entry in pending.items():
        entity = entry["entity"]
        if entity is None:
            entity = fetch(api, action="wbgetentities", ids=ident, props="labels|claims",
                           languages="fr|en", format="json")["entities"][ident]
        title = label(entity)
        if not title:
            continue
        claims = entity.get("claims", {})
        def claim_value(prop):
            return next((c.get("mainsnak", {}).get("datavalue", {}).get("value") for c in claims.get(prop, [])
                         if c.get("mainsnak", {}).get("datavalue")), None)
        if entry["type"] == "book":
            source_status("awards", "running", "Édition française · " + title)
            time.sleep(1)
            result = fetch("https://openlibrary.org/search.json", q="language:fre", title=title,
                           fields=BOOK_FIELDS, lang="fr", limit=5)
            hit = next((h for h in result.get("docs", []) if normalized(h["title"]) == normalized(title)
                        or any(normalized(e.get("title", "")) == normalized(title)
                               for e in h.get("editions", {}).get("docs", []))), None)
            item = book_item(hit, entry["evidence"]) if hit else None
        else:
            date = claim_value("P577") or {}
            item = dict(type=entry["type"], title=title, year=date.get("time", "")[1:5],
                        evidence=entry["evidence"])
        if item:
            canonical = item.get("id")
            if entry["type"] == "film" and claim_value("P345"):
                canonical = "imdb:" + claim_value("P345")
            if entry["type"] == "game" and claim_value("P1733"):
                canonical = "steam:" + str(claim_value("P1733"))
            if canonical:
                for evidence in item["evidence"]:
                    evidence["canonical"] = canonical
            item["id"] = "awards:" + ident
            items.append(item)
    if not items:
        raise ValueError("Aucune récompense reçue, ancien catalogue conservé.")
    store("awards", items)


def update(selected=None):
    if not LOCK.acquire(blocking=False):
        return False
    ROOT.joinpath("data").mkdir(exist_ok=True)
    lease = ROOT.joinpath("data", ".update.lock").open("w")
    try:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lease.close()
        LOCK.release()
        return False
    import metacritic
    import goodreads_books
    sources = {"imdb": imdb, "books": goodreads_books.collect, "metacritic": metacritic.collect, "awards": awards}
    chosen = [s for s in (selected or sources) if s in sources]

    def run(name):
        try:
            sources[name]()
        except Exception as error:
            source_status(name, "error", f"Collecte interrompue : {error}. Relancer pour réessayer.")

    def job():
        try:
            with ThreadPoolExecutor(max_workers=3) as pool:
                list(pool.map(run, chosen))
        finally:
            fcntl.flock(lease, fcntl.LOCK_UN)
            lease.close()
            LOCK.release()

    threading.Thread(target=job, daemon=True).start()
    return True


def status():
    with connect() as conn:
        counts = {r["type"]: r["n"] for r in conn.execute("SELECT type,count(DISTINCT " + CANONICAL + ") n FROM works GROUP BY type")}
        sources = [dict(r) for r in conn.execute("SELECT * FROM sources WHERE id != 'steam-cursor'")]
    if not LOCK.locked():
        for source in sources:
            if source["status"] == "running" and (datetime.now(timezone.utc) - datetime.fromisoformat(source["updated"])).total_seconds() > 600:
                source["status"] = "interrupted"
                source["message"] = "Collecte interrompue. Cliquer sur Actualiser pour reprendre."
    return dict(counts=counts, total=sum(counts.values()), sources=sources, rules=RULES, running=LOCK.locked() or any(s["status"] == "running" for s in sources))


def search(params):
    clauses, args = [], []
    term = params.get("q", [""])[0][:200]
    for token in normalized(term).split():
        clauses.append("search LIKE ? ESCAPE '\\'")
        args.append("%" + token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
    kind = params.get("type", ["all"])[0]
    if kind in ("film", "book", "game"):
        clauses.append("type=?")
        args.append(kind)
    genre = normalized(params.get("genre", [""])[0][:100]).strip()
    if genre:
        clauses.append("LOWER(genre) LIKE ? ESCAPE '\\'")
        args.append("%" + genre.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
    for parameter, operator in (("year_min", ">="), ("year_max", "<=")):
        raw = params.get(parameter, [""])[0]
        if re.fullmatch(r"[0-9]{1,4}", raw) and 1 <= int(raw) <= 9999:
            clauses.append("CAST(year AS INTEGER) " + (">= ?" if operator == ">=" else "BETWEEN 1 AND ?"))
            args.append(int(raw))
    raw_score = params.get("min_score", [""])[0]
    if re.fullmatch(r"[0-9]{1,3}", raw_score) and 0 <= int(raw_score) <= 100:
        clauses.append("score >= ?")
        args.append(int(raw_score))
    if params.get("criterion", ["all"])[0] == "award":
        clauses.append("EXISTS(SELECT 1 FROM works award_work WHERE award_work.id LIKE 'awards:%' AND COALESCE(json_extract(award_work.evidence,'$[0].canonical'),award_work.id)=COALESCE(json_extract(works.evidence,'$[0].canonical'),works.id))")
    try:
        page = max(1, int(params.get("page", ["1"])[0]))
    except ValueError:
        page = 1
    order = {"votes": "votes DESC", "score": "score DESC, votes DESC", "year": "CAST(year AS INTEGER) DESC", "title": "title COLLATE NOCASE"}.get(params.get("sort", ["votes"])[0], "votes DESC")
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    candidates = "WITH candidates AS (SELECT *, " + CANONICAL + " AS canonical FROM works" + where + "), ranked AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY canonical ORDER BY score DESC, id) AS position FROM candidates) "
    with connect() as conn:
        total = conn.execute(candidates + "SELECT count(*) FROM ranked WHERE position=1", args).fetchone()[0]
        rows = conn.execute(candidates + "SELECT * FROM ranked WHERE position=1 ORDER BY " + order + ", id LIMIT 24 OFFSET ?", args + [(page - 1) * 24]).fetchall()
        items = []
        for row in rows:
            item = serialize(row)
            canonical = row["canonical"]
            linked = conn.execute("SELECT evidence FROM works WHERE " + CANONICAL + "=?", (canonical,))
            evidence, signatures = [], set()
            for linked_row in linked:
                for proof in json.loads(linked_row["evidence"]):
                    signature = (proof["source"], proof.get("label"), proof.get("nomination"))
                    if signature not in signatures:
                        signatures.add(signature)
                        evidence.append(proof)
            item["id"] = canonical
            item["evidence"] = evidence
            item.pop("position", None)
            item.pop("canonical", None)
            items.append(item)
    return dict(total=total, page=page, items=items)


def serialize(row):
    item = dict(row)
    item["evidence"] = json.loads(item["evidence"])
    item["edition"] = json.loads(item["edition"])
    item.pop("search")
    return item


if __name__ == "__main__":
    import sys
    update(sys.argv[1:] or None)
    while LOCK.locked():
        time.sleep(1)
