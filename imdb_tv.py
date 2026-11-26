"""IMDb television series/miniseries snapshot, using the film rating thresholds."""
import csv,gzip,hashlib,json
from pathlib import Path
import catalog
ROOT=Path(__file__).parent
SEED=ROOT/'data/imdb-tv.json.gz'
TV_TYPES={'tvSeries','tvMiniSeries'}
FILM_TYPES={'movie','short','tvMovie','tvShort','video'}

def item(row,score,votes):
    title_type=row.get('titleType')
    if score<7 or votes<1000 or title_type not in TV_TYPES|FILM_TYPES:return None
    clean=lambda key:'' if row.get(key) in (None,'\\N') else row[key]
    proof=dict(source='IMDb',kind='rating',value=score,scale=10,votes=votes,url='https://www.imdb.com/title/'+row['tconst']+'/',checked=catalog.stamp())
    if title_type in TV_TYPES:
        proof.update(titleType=title_type,endYear=clean('endYear'),runtimeUnit='minutes par épisode')
    return dict(id='imdb:'+row['tconst'],type='tv' if title_type in TV_TYPES else 'film',title=clean('primaryTitle'),original=clean('originalTitle'),year=clean('startYear'),genre=clean('genres').replace(',',', '),length=clean('runtimeMinutes'),score=score*10,votes=votes,evidence=[proof])

def install(conn):
    if not SEED.exists():
        parts=sorted((ROOT/'data/imdb-tv-seed').glob('*.part'))
        if not parts:return
        blob=b''.join(p.read_bytes() for p in parts);gzip.decompress(blob)
        temporary=SEED.with_suffix('.restore');temporary.write_bytes(blob);temporary.replace(SEED)
    digest=hashlib.sha256(SEED.read_bytes()).hexdigest()
    conn.execute('CREATE TABLE IF NOT EXISTS catalog_migrations(name TEXT PRIMARY KEY,version TEXT)')
    previous=conn.execute("SELECT version FROM catalog_migrations WHERE name='imdb-tv'").fetchone()
    if previous and previous[0]==digest:return
    data=json.loads(gzip.decompress(SEED.read_bytes()))
    rows=data['items']
    if not rows or any(r['type']!='tv' or r['score']<70 or r['votes']<1000 for r in rows):raise ValueError('Instantané de séries invalide')
    for r in rows:
        conn.execute('INSERT OR REPLACE INTO works VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(r['id'],'tv',r['title'],catalog.normalized(' '.join([r['title'],r.get('original',''),r.get('genre','')])),str(r.get('year','')),r.get('genre',''),'','',str(r.get('length','')),r['score'],r['votes'],json.dumps(r['evidence'],ensure_ascii=False),'null',data['checked']))
    conn.execute('INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?)',('imdb-tv','ready',f"{len(rows)} séries et mini-séries IMDb · épisodes individuels exclus",data['checked'],len(rows)))
    conn.execute("INSERT OR REPLACE INTO catalog_migrations VALUES('imdb-tv',?)",(digest,));conn.commit()

def collect():
    ratings={}
    print('Lecture des notes IMDb…',flush=True)
    with gzip.open(catalog.download('title.ratings.tsv.gz'),'rt',encoding='utf-8') as stream:
        for r in csv.DictReader(stream,delimiter='\t',quoting=csv.QUOTE_NONE):
            score,votes=float(r['averageRating']),int(r['numVotes'])
            if score>=7 and votes>=1000:ratings[r['tconst']]=(score,votes)
    rows=[]
    print('Lecture des séries et mini-séries IMDb…',flush=True)
    with gzip.open(catalog.download('title.basics.tsv.gz'),'rt',encoding='utf-8') as stream:
        for r in csv.DictReader(stream,delimiter='\t',quoting=csv.QUOTE_NONE):
            if r['titleType'] in TV_TYPES and r['tconst'] in ratings:rows.append(item(r,*ratings[r['tconst']]))
    if not rows:raise ValueError('Aucune série reçue; ancien catalogue conservé')
    data=dict(checked=catalog.stamp(),items=rows)
    SEED.parent.mkdir(parents=True,exist_ok=True);temporary=SEED.with_suffix('.tmp');temporary.write_bytes(gzip.compress(json.dumps(data,ensure_ascii=False).encode()));temporary.replace(SEED)
    with catalog.connect() as conn:install(conn)
    print(f'{len(rows)} séries et mini-séries installées.',flush=True)

if __name__=='__main__':collect()
