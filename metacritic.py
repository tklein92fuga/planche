"""Metacritic public browse pages, explicit critic-count threshold and resumable collection."""
import gzip
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request,urlopen
import catalog

MIN_SCORE,MIN_CRITICS=70,10
SEED=Path(__file__).parent/'data/metacritic.json.gz'

def browse(markup):
    match=re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>',markup,re.S)
    if not match:raise ValueError('Structure Metacritic inconnue, données précédentes conservées.')
    pool=json.loads(match[1])
    def decode(index,depth=0):
        if index<0 or depth>18:return None
        value=pool[index]
        if isinstance(value,dict):return {k:decode(v,depth+1) for k,v in value.items()}
        if isinstance(value,list):return [decode(v,depth+1) if isinstance(v,int) else v for v in value]
        return value
    for index,value in enumerate(pool):
        if isinstance(value,dict) and 'items' in value and 'total' in value:
            data=decode(index)
            if data.get('items') and all(isinstance(i,dict) and i.get('type')=='game-title' for i in data['items']):return data
    raise ValueError('Liste Metacritic absente, données précédentes conservées.')

def item(row,checked=None):
    score=row.get('criticScoreSummary') or {}
    if not isinstance(score.get('score'),(int,float)) or not isinstance(score.get('reviewCount'),int):return None
    if score['score']<MIN_SCORE or score['reviewCount']<MIN_CRITICS:return None
    slug=row.get('slug','')
    if not re.fullmatch(r'[a-z0-9-]+',slug):return None
    art=row.get('image') or {};path=art.get('bucketPath') or ''
    image='https://www.metacritic.com/a/img/catalog'+path if path.startswith('/provider/') else ''
    evidence=dict(source='Metacritic',kind='rating',value=score['score'],scale=100,votes=score['reviewCount'],label='Metascore · critiques professionnelles',url='https://www.metacritic.com/game/'+slug+'/',checked=checked or catalog.stamp(),platforms=[p['name'] for p in row.get('platforms',[]) if p.get('name')])
    # Browse metascores concern the platform selected by Metacritic; no cross-platform averaging.
    evidence['label']+=' · version de référence Metacritic'
    return dict(id='metacritic:'+slug,type='game',title=row['title'],year=str(row.get('premiereYear') or ''),genre=', '.join(g['name'] for g in row.get('genres',[]) if g.get('name')),creator='',image=image,length='',score=score['score'],votes=score['reviewCount'],evidence=[evidence],edition=None)

def install(conn):
    if not SEED.exists():
        parts=sorted(SEED.parent.joinpath('metacritic-seed').glob('*.part'))
        if not parts:return
        blob=b''.join(p.read_bytes() for p in parts)
        gzip.decompress(blob)
        temporary=SEED.with_suffix('.restore');temporary.write_bytes(blob);temporary.replace(SEED)
    digest='v3:'+hashlib.sha256(SEED.read_bytes()).hexdigest()
    conn.execute('CREATE TABLE IF NOT EXISTS catalog_migrations(name TEXT PRIMARY KEY,version TEXT)')
    previous=conn.execute("SELECT version FROM catalog_migrations WHERE name='metacritic'").fetchone()
    if previous and previous[0]==digest:return
    data=json.loads(gzip.decompress(SEED.read_bytes()))
    records=data['items']
    if not records:raise ValueError('Instantané Metacritic vide.')
    conn.execute('CREATE TABLE IF NOT EXISTS legacy_games AS SELECT * FROM works WHERE 0')
    conn.execute("INSERT INTO legacy_games SELECT * FROM works WHERE id LIKE 'steam:%' AND id NOT IN (SELECT id FROM legacy_games)")
    old={}
    for row in conn.execute('SELECT id,title,year,genre,creator,image FROM legacy_games'):
        old.setdefault((catalog.normalized(row['title']),str(row['year'])),[]).append(row)
    # Insert new ratings before retiring Steam. The transaction preserves personal-library IDs where unambiguous.
    conn.execute("DELETE FROM works WHERE id LIKE 'metacritic:%'")
    for record in records:
        record=dict(record);record['evidence']=[dict(e) for e in record['evidence']]
        hits=old.get((catalog.normalized(record['title']),record['year']),[])
        # Verified award-linked Steam IDs refer to these exact works, including later PC ports.
        known={'metacritic:god-of-war':'steam:1593500','metacritic:sekiro-shadows-die-twice':'steam:814380','metacritic:elden-ring':'steam:1245620','metacritic:it-takes-two':'steam:1426210','metacritic:baldurs-gate-3':'steam:1086940'}
        if not hits and record['id'] in known:
            hits=list(conn.execute('SELECT id,title,year,genre,creator,image FROM legacy_games WHERE id=?',(known[record['id']],)))
        if len(hits)==1:
            record['evidence'][0]['canonical']=hits[0]['id']
            record['creator']=hits[0]['creator'] or ''
        conn.execute('INSERT OR REPLACE INTO works VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(
            record['id'],'game',record['title'],catalog.normalized(' '.join([record['title'],record['genre'],record['creator']])),record['year'],record['genre'],record['creator'],record['image'],'',record['score'],record['votes'],json.dumps(record['evidence'],ensure_ascii=False),'null',data['checked']))
    conn.execute("DELETE FROM works WHERE id LIKE 'steam:%'")
    conn.execute("DELETE FROM sources WHERE id IN ('steam','steam-cursor')")
    conn.execute("UPDATE works SET score=NULL,votes=NULL WHERE type='game' AND id LIKE 'awards:%'")
    conn.execute('INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?)',('metacritic',data['status'],data['message'],data['checked'],len(records)))
    conn.execute("INSERT OR REPLACE INTO catalog_migrations VALUES('metacritic',?)",(digest,))
    conn.commit()

def collect():
    cache=catalog.CACHE/'metacritic';cache.mkdir(parents=True,exist_ok=True)
    def page(number):
        target=cache/f'{number:04}.json.gz'
        if target.exists() and time.time()-target.stat().st_mtime<86400:return json.loads(gzip.decompress(target.read_bytes()))
        url='https://www.metacritic.com/browse/game/?page='+str(number)
        req=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; Planche personal catalogue)','Accept':'text/html'})
        with urlopen(req,timeout=25,context=catalog.context()) as response:data=browse(response.read(4*1024*1024).decode())
        target.write_bytes(gzip.compress(json.dumps(data).encode()));return data
    records={};seen=set();complete=False;number=1;error=''
    try:
        while number<=1000:
            pages=list(range(number,number+3))
            with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(page,pages))
            for n,data in zip(pages,results):
                raw=data['items'];signature=tuple(i['slug'] for i in raw)
                if signature in seen:raise ValueError('Pagination répétée par la source.')
                seen.add(signature)
                for row in raw:
                    parsed=item(row)
                    if parsed:records[parsed['id']]=parsed
                scores=[r.get('criticScoreSummary',{}).get('score') for r in raw]
                if scores and all(isinstance(s,(int,float)) and s<MIN_SCORE for s in scores):complete=True;break
                if n*len(raw)>=data['total']:complete=True;break
            catalog.source_status('metacritic','running',f'{len(records)} jeux admissibles · {number+2} pages examinées',len(records))
            if complete:break
            number+=3
    except (OSError,ValueError,KeyError,TypeError) as exc:
        error=str(exc)
    if not records:raise ValueError(error or 'Aucun jeu Metacritic admissible, catalogue précédent conservé.')
    # Retain earlier verified records on an interrupted refresh.
    if not complete and SEED.exists():
        prior=json.loads(gzip.decompress(SEED.read_bytes()))
        previous={i['id']:i for i in prior['items']};previous.update(records);records=previous
    message=f'{len(records)} jeux · Metascore ≥ 70 · au moins 10 critiques.'
    message+=' Parcours des pages terminé.' if complete else ' Collecte partielle, relancer pour reprendre. '+error
    data={'checked':catalog.stamp(),'status':'ready' if complete else 'partial','message':message,'items':list(records.values())}
    temporary=SEED.with_suffix('.tmp');temporary.write_bytes(gzip.compress(json.dumps(data,ensure_ascii=False).encode()));temporary.replace(SEED)
    with catalog.connect() as conn:install(conn)
    catalog.source_status('metacritic',data['status'],message,len(records))

if __name__=='__main__':collect()
