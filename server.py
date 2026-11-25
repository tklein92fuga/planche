"""Serve Planche and look up public metadata without exposing API keys."""
import csv
import gzip
import io
import json
import re
import sys
import unicodedata
import zipfile
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlsplit, parse_qs
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

import catalog
import paths

ROOT = Path(__file__).resolve().parent
MAX_BYTES = 8 * 1024 * 1024


def table(body, excel):
    if not excel:
        try:
            value = body.decode("utf-8-sig")
        except UnicodeDecodeError:
            value = body.decode("cp1252")
        try:
            dialect = csv.Sniffer().sniff(value[:4096], delimiters=",;\t")
        except csv.Error:
            dialect = "excel"
        return list(csv.reader(io.StringIO(value), dialect))
    with zipfile.ZipFile(io.BytesIO(body)) as workbook:
        if sum(part.file_size for part in workbook.infolist()) > 40 * 1024 * 1024:
            raise ValueError("Classeur trop volumineux.")
        def xml(path):
            data = workbook.read(path)
            if b"<!DOCTYPE" in data.upper():
                raise ValueError("XML non pris en charge.")
            return ET.fromstring(data)

        strings = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            strings = ["".join(t.text or "" for t in s.iterfind(".//{*}t"))
                       for s in xml("xl/sharedStrings.xml")]
        sheet = xml("xl/workbook.xml").find(".//{*}sheet")
        rel_id = next(v for k, v in sheet.attrib.items() if k.endswith("}id"))
        rel = next(r for r in xml("xl/_rels/workbook.xml.rels") if r.get("Id") == rel_id)
        target = rel.get("Target")
        target = target.lstrip("/") if target.startswith("/") else "xl/" + target
        rows = []
        for row in xml(target).iterfind(".//{*}row"):
            cells = []
            for cell in row.iterfind("{*}c"):
                col = 0
                for letter in re.match(r"[A-Z]*", cell.get("r", "")).group():
                    col = col * 26 + ord(letter) - 64
                if col > 256:
                    continue
                index = col - 1 if col else len(cells)
                cells.extend([""] * max(0, index + 1 - len(cells)))
                value = cell.findtext("{*}v", "")
                if cell.get("t") == "s" and value:
                    value = strings[int(value)]
                if cell.get("t") == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iterfind(".//{*}t"))
                cells[index] = value
            rows.append(cells)
        return rows


def normalize(value):
    chars = unicodedata.normalize("NFKD", value.casefold())
    return "".join(c for c in chars if c.isalnum())


def remote(base, **params):
    request = Request(base + "?" + urlencode(params), headers={"User-Agent": "Planche/1.0 personal culture tracker"})
    with urlopen(request, timeout=4, context=catalog.context()) as response:
        return json.loads(response.read(2 * 1024 * 1024))


@lru_cache(maxsize=512)
def metadata(kind, title, year):
    def matches(name):
        return normalize(name) == normalize(title)

    if kind == "film":
        data = remote("https://itunes.apple.com/search", term=title, country="FR", media="movie", entity="movie", limit=12)
        for hit in data.get("results", []):
            release = hit.get("releaseDate", "")[:4]
            if matches(hit.get("trackName", "")) and (not year or not release or abs(int(year) - int(release)) <= 1):
                return dict(year=release, creator=hit.get("artistName"), genre=hit.get("primaryGenreName"),
                            length=round(hit.get("trackTimeMillis", 0) / 60000) or "", image=hit.get("artworkUrl100", "").replace("100x100", "600x600"), source="Apple")
    if kind == "book":
        data = remote("https://openlibrary.org/search.json", title=title, limit=12,
                      fields="title,author_name,first_publish_year,number_of_pages_median,cover_i")
        for hit in data.get("docs", []):
            release = str(hit.get("first_publish_year", ""))
            if matches(hit.get("title", "")) and (not year or not release or int(release) == int(year)):
                cover = hit.get("cover_i")
                return dict(year=release, creator=", ".join(hit.get("author_name", [])),
                            length=hit.get("number_of_pages_median"), image=f"https://covers.openlibrary.org/b/id/{cover}-M.jpg" if cover else "", source="Open Library")
    if kind == "game":
        with catalog.connect() as conn:
            rows=conn.execute("SELECT * FROM works WHERE type='game' AND id LIKE 'metacritic:%' AND title=? COLLATE NOCASE AND (?='' OR year=?)",(title,year,year)).fetchall()
            if len(rows)==1:
                hit=rows[0]
                return dict(year=hit['year'],creator=hit['creator'],genre=hit['genre'],image=hit['image'],source='Metacritic')
    return {}


def lookup(item):
    try:
        kind, title, year = item["type"], str(item["title"])[:200], str(item.get("year", ""))
        return metadata(kind, title, year if re.fullmatch(r"\d{4}", year) else "")
    except (OSError, ValueError, TypeError, KeyError):
        return {}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "static"), **kwargs)

    def reply(self, status, value):
        payload = json.dumps(value, ensure_ascii=False).encode()
        compressed=len(payload)>65536 and "gzip" in self.headers.get("Accept-Encoding", "")
        if compressed:payload=gzip.compress(payload,compresslevel=5)
        self.send_response(status)
        if compressed:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = urlsplit(self.path)
        if path.path == "/api/paths":
            self.reply(200, paths.overview(parse_qs(path.query).get("type",["all"])[0]))
        elif path.path == "/api/paths/detail":
            params = parse_qs(path.query)
            try:
                page = max(1,int(params.get("page",["1"])[0]))
                result = paths.detail(params.get("id",[""])[0],page,params.get("type",["all"])[0])
                self.reply(200 if result else 404,result or {"error":"Liste introuvable."})
            except ValueError:
                self.reply(400,{"error":"Page invalide."})
        elif path.path == "/api/catalog/art":
            try:
                params = parse_qs(path.query)
                ident = params.get("id",[""])[0]
                if not ident and params.get("title"):
                    item = {key:params.get(key,[""])[0][:200] for key in ("title","type","year")}
                    item["id"]="art"
                    ident=paths.resolve([item]).get("art","")
                url = paths.artwork(ident)
            except (OSError,ValueError,KeyError):
                url = ""
            if url.startswith("https://"):
                self.send_response(302)
                self.send_header("Location",url)
                self.send_header("Cache-Control","private, max-age=86400")
                self.end_headers()
            else:
                self.send_error(404,"Visuel indisponible")
        elif path.path == "/api/catalog":
            self.reply(200, catalog.search(parse_qs(path.query)))
        elif path.path == "/api/catalog/status":
            self.reply(200, catalog.status())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/catalog/resolve":
            try:
                length=int(self.headers.get("Content-Length",0))
                if not 0 < length <= MAX_BYTES:
                    raise ValueError("Requête trop volumineuse.")
                items=json.loads(self.rfile.read(length))
                if not isinstance(items,list) or len(items)>10000:
                    raise ValueError("Bibliothèque trop volumineuse.")
                self.reply(200,paths.resolve(items))
            except (ValueError,TypeError,KeyError):
                self.reply(400,{"error":"Bibliothèque invalide."})
            return
        if self.path == "/api/catalog/update":
            self.reply(202, {"started": catalog.update()})
            return
        if self.path not in ("/api/csv", "/api/xlsx", "/api/enrich"):
            self.reply(404, {"error": "Route inconnue."})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 < length <= MAX_BYTES:
                raise ValueError("Fichier vide ou supérieur à 8 Mo.")
            body = self.rfile.read(length)
            if self.path == "/api/enrich":
                items = json.loads(body)
                if not isinstance(items, list) or len(items) > 4:
                    raise ValueError("Quatre recherches maximum par requête.")
                with ThreadPoolExecutor(max_workers=2) as pool:
                    result = list(pool.map(lookup, items))
            else:
                result = table(body, self.path == "/api/xlsx")
                if len(result) > 10001:
                    raise ValueError("Le fichier dépasse 10 000 lignes.")
            self.reply(200, result)
        except (ValueError, TypeError, KeyError, AttributeError, IndexError, StopIteration,
                zipfile.BadZipFile, ET.ParseError, csv.Error) as error:
            self.reply(400, {"error": str(error) or "Fichier illisible."})


if __name__ == "__main__":
    catalog.connect().close()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        print(f"Planche est disponible sur http://127.0.0.1:{port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
