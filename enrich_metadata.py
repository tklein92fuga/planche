"""Optional public Metacritic company metadata; no fabricated roles or gameplay tags."""
import concurrent.futures
import gzip
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request,urlopen
import catalog

TARGET=Path(__file__).parent/'data/company-metadata.json'

def parse(markup,ident):
    match=re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>',markup,re.S)
    if not match:raise ValueError('Métadonnées absentes')
    pool=json.loads(match[1])
    def decode(index,depth=0):
        if index<0 or depth>16:return None
        value=pool[index]
        if isinstance(value,dict):return {k:decode(v,depth+1) for k,v in value.items()}
        if isinstance(value,list):return [decode(v,depth+1) if isinstance(v,int) else v for v in value]
        return value
    for i,v in enumerate(pool):
        if isinstance(v,dict) and 'production' in v and 'criticScoreSummary' in v:
            item=decode(i)
            if item.get('slug')!=ident.split(':',1)[1]:continue
            companies=item.get('production',{}).get('companies',[])
            return dict(id=ident,franchises=sorted({f['name'] for f in (item.get('gameTaxonomy') or {}).get('franchises',[]) if f.get('name')}),developers=sorted({c['name'] for c in companies if c.get('typeName')=='Developer' and c.get('name')}),publishers=sorted({c['name'] for c in companies if c.get('typeName')=='Publisher' and c.get('name')}),source='https://www.metacritic.com/game/'+item['slug']+'/',checked=catalog.stamp())
    raise ValueError('Jeu non identifié')

def save(records):
    temporary=TARGET.with_suffix('.tmp')
    temporary.write_text(json.dumps(list(records.values()),ensure_ascii=False,indent=2))
    temporary.replace(TARGET)

def collect():
    with catalog.connect() as c:
        top=c.execute("SELECT id FROM works WHERE id LIKE 'metacritic:%' ORDER BY score DESC,votes DESC LIMIT 250").fetchall()
        popular=c.execute("SELECT id FROM works WHERE id LIKE 'metacritic:%' ORDER BY votes DESC LIMIT 250").fetchall()
    ids=sorted({r[0] for r in [*top,*popular]})
    records={r['id']:r for r in json.loads(TARGET.read_text())} if TARGET.exists() else {}
    cache=catalog.CACHE/'companies';cache.mkdir(parents=True,exist_ok=True)
    def fetch(ident):
        if ident in records and 'franchises' in records[ident]:
            checked=datetime.fromisoformat(records[ident]['checked'])
            if (datetime.now(timezone.utc)-checked).total_seconds()<7*86400:return records[ident]
        path=cache/(ident.split(':')[1]+'.html.gz')
        if path.exists() and time.time()-path.stat().st_mtime<7*86400:text=gzip.decompress(path.read_bytes()).decode()
        else:
            url='https://www.metacritic.com/game/'+ident.split(':')[1]+'/'
            with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; Planche personal catalogue)'}),timeout=20,context=catalog.context()) as response:text=response.read(4*1024*1024).decode()
            path.write_bytes(gzip.compress(text.encode()))
        return parse(text,ident)
    failures=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(fetch,ident):ident for ident in ids}
        for index,future in enumerate(concurrent.futures.as_completed(futures),1):
            try:
                record=future.result();records[record['id']]=record
            except (OSError,ValueError,KeyError,TypeError):failures+=1
            if index%20==0:
                save(records)
                print(f'{index}/{len(ids)} fiches · {len(records)} enrichies · {failures} indisponibles',flush=True)
    save(records)
    print(f'Terminé: {len(records)} fiches, {failures} indisponibles',flush=True)

if __name__=='__main__':collect()
