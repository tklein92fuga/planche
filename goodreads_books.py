"""Goodreads ratings with independently identified French editions; no API key required."""
import csv
import gzip
import hashlib
import html
import json
import re
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import catalog

ROOT=Path(__file__).parent
SEED=ROOT/'data/goodreads.json.gz'
DATASET='https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/'
PSYCHOLOGY=[('93981',"L'Interprétation des rêves",'Freud',1900),('357636','Malaise dans la civilisation','Freud',1930),('80459','Le Moi et le Ça','Freud',1923),('612188','Ma vie','Jung',1962),('123632',"L'Homme et ses symboles",'Jung',1964),('32772934','Types psychologiques','Jung',1921),('4069','Découvrir un sens à sa vie','Frankl',1946),('174879','Le développement de la personne','Rogers',1961),('11313628',"Vers une psychologie de l'être",'Maslow',1962)]
GENRES={'classics','fantasy','science-fiction','fiction','historical-fiction','horror','mystery','thriller','romance','philosophy','psychology','psychoanalysis','poetry','plays','drama','dystopia','biography','autobiography','memoir','non-fiction','history','politics','romanticism','modernism','existentialism','realism','naturalism','literature','short-stories','self-help','cognitive-psychology'}

def norm(value):return re.sub(r'[^a-z0-9]','',catalog.normalized(value))
def parse(markup):
    if 'id="__NEXT_DATA__"' not in markup:raise ValueError('Page Goodreads non accessible')
    match=re.search(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',markup,re.S)
    data=json.loads(match[1]) if match else {}
    if data.get('@type')!='Book' or not data.get('aggregateRating'):raise ValueError('Note Goodreads absente')
    state=json.loads(re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',markup,re.S)[1])['props']['pageProps']['apolloState']
    book=next((v for v in state.values() if isinstance(v,dict) and v.get('__typename')=='Book' and v.get('title')==data['name']),{})
    genres=[g['genre']['name'] for g in book.get('bookGenres',[]) if g.get('genre',{}).get('name')]
    rating=data['aggregateRating']
    return dict(title=data['name'],authors=[a['name'] for a in data.get('author',[])],score=float(rating['ratingValue']),votes=int(rating['ratingCount']),genres=genres,image=data.get('image',''),pages=data.get('numberOfPages'),publisher=(book.get('details') or {}).get('publisher'),historical=False,checked=catalog.stamp())

def install(conn):
    if not SEED.exists():
        parts=sorted(ROOT.joinpath('data/goodreads-seed').glob('*.part'))
        if not parts:return
        blob=b''.join(p.read_bytes() for p in parts);gzip.decompress(blob)
        temporary=SEED.with_suffix('.restore');temporary.write_bytes(blob);temporary.replace(SEED)
    digest=hashlib.sha256(SEED.read_bytes()).hexdigest()
    conn.execute('CREATE TABLE IF NOT EXISTS catalog_migrations(name TEXT PRIMARY KEY,version TEXT)')
    previous=conn.execute("SELECT version FROM catalog_migrations WHERE name='goodreads'").fetchone()
    if previous and previous[0]==digest:return
    data=json.loads(gzip.decompress(SEED.read_bytes()))
    for record in data['items']:
        current=conn.execute('SELECT * FROM works WHERE id=?',(record['id'],)).fetchone()
        if current is None:
            item=record.get('new_work')
            if not item or not item.get('edition') or item['edition'].get('language')!='français':continue
            conn.execute('INSERT OR REPLACE INTO works VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(item['id'],'book',item['title'],catalog.normalized(' '.join([item['title'],record['title'],item['creator']])),str(item['year']),record['genre'],item['creator'],item['image'],'',record['score']*20,record['votes'],'[]',json.dumps(item['edition'],ensure_ascii=False),catalog.stamp()))
            current=conn.execute('SELECT * FROM works WHERE id=?',(item['id'],)).fetchone()
        edition=json.loads(current['edition'])
        if not edition or edition.get('language')!='français':continue
        evidence=[p for p in json.loads(current['evidence']) if p.get('source')!='Goodreads']
        proof=dict(source='Goodreads',kind='rating',value=record['score'],scale=5,votes=record['votes'],url=record['url'],checked=record['checked'],label='Lecteurs · instantané historique goodbooks-10k (2017)' if record['historical'] else 'Lecteurs · fiche Goodreads publique')
        evidence.insert(0,proof)
        conn.execute('UPDATE works SET year=?,score=?,votes=?,genre=?,evidence=?,updated=? WHERE id=?',(str(record.get('year') or current['year']),record['score']*20,record['votes'],record['genre'],json.dumps(evidence,ensure_ascii=False),catalog.stamp(),record['id']))
    conn.execute('INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?)',('goodreads','partial',data['message'],data['checked'],len(data['items'])))
    conn.execute("INSERT OR REPLACE INTO catalog_migrations VALUES('goodreads',?)",(digest,));conn.commit()

def collect():
    cache=catalog.CACHE/'goodreads';cache.mkdir(parents=True,exist_ok=True)
    def dataset(name):
        path=cache/name
        if not path.exists():
            with urlopen(DATASET+name,timeout=30,context=catalog.context()) as response:path.write_bytes(response.read())
        return path
    rows=list(csv.DictReader(dataset('books.csv').open()))
    index=defaultdict(list);dataset_by_id={r['goodreads_book_id']:r for r in rows}
    for row in rows:
        for title in [row['title'],row['original_title']]:
            title=re.sub(r'\s*\([^)]*#.*?\)\s*$','',title).strip()
            if len(norm(title))>=4:index[norm(title)].append(row)
    matches=[]
    with catalog.connect() as conn:books=[dict(r) for r in conn.execute("SELECT * FROM works WHERE type='book'")]
    for work in books:
        original=work['search'];author=catalog.normalized(work['creator'])
        if author and author in original:original=original[:original.rfind(author)].strip()
        title=catalog.normalized(work['title'])
        if original.startswith(title):original=original[len(title):].strip()
        hits={}
        for title in [work['title'],original]:
            for row in index.get(norm(title),[]):
                if {norm(a) for a in row['authors'].split(',')}&{norm(a) for a in work['creator'].split(',')}:hits[row['goodreads_book_id']]=row
        if len(hits)==1:matches.append((work,next(iter(hits.values()))))
    counts=defaultdict(int)
    for w,r in matches:counts[r['goodreads_book_id']]+=1
    matches=[(w,r) for w,r in matches if counts[r['goodreads_book_id']]==1]
    tags={r['tag_id']:r['tag_name'] for r in csv.DictReader(dataset('tags.csv').open())}
    shelves=defaultdict(set)
    for row in csv.DictReader(dataset('book_tags.csv').open()):
        tag=tags.get(row['tag_id'],'')
        if tag in GENRES and int(row['count'])>=10:shelves[row['goodreads_book_id']].add(tag.replace('-',' '))
    blocked=threading.Event()
    def live(ident):
        target=cache/(ident+'.html.gz')
        if target.exists():return parse(gzip.decompress(target.read_bytes()).decode())
        if blocked.is_set():raise ValueError('Accès public temporairement limité')
        request=Request('https://www.goodreads.com/book/show/'+ident,headers={'User-Agent':'Mozilla/5.0'})
        try:
            with urlopen(request,timeout=12,context=catalog.context()) as response:
                if response.status!=200:blocked.set();raise ValueError('Accès public limité')
                markup=response.read(3*1024*1024).decode()
        except HTTPError as error:
            if error.code in (403,429):blocked.set()
            raise
        if 'id="__NEXT_DATA__"' not in markup:blocked.set();raise ValueError('Vérification du site requise')
        target.write_bytes(gzip.compress(markup.encode()));return parse(markup)
    # Add foundational psychology works only after a French edition is independently matched.
    for ident,title,author,year in PSYCHOLOGY:
        if any(r['goodreads_book_id']==ident for _,r in matches):continue
        try:
            info=live(ident)
            query='title:"'+title+'" author:'+author+' language:fre'
            result=catalog.fetch('https://openlibrary.org/search.json',q=query,fields=catalog.BOOK_FIELDS,lang='fr',limit=10)
            hit=next((h for h in result.get('docs',[]) if any(norm(author) in norm(a) for a in h.get('author_name',[])) and any(norm(e.get('title','')).startswith(norm(title)) and 'fre' in e.get('language',[]) for e in h.get('editions',{}).get('docs',[]))),None)
            if hit:
                work=catalog.book_item(hit,evidence=[]);work['year']=year
                row=dataset_by_id.get(ident) or dict(goodreads_book_id=ident,title=info['title'],authors=', '.join(info['authors']),average_rating=info['score'],ratings_count=info['votes'])
                work['is_new']=True;matches.append((work,row))
        except (OSError,ValueError,KeyError):continue
    records=[]
    def convert(pair):
        work,row=pair;ident=row['goodreads_book_id']
        info=dict(title=row['title'],score=float(row['average_rating']),votes=int(row['ratings_count']),genres=sorted(shelves[ident]),historical=True,checked=catalog.stamp())
        try:info.update(live(ident))
        except (OSError,ValueError,KeyError):pass
        # A live page must name the same author; otherwise retain the documented historical mapping.
        authors=info.get('authors',[])
        if authors and not {norm(a) for a in authors}&{norm(a) for a in str(row['authors']).split(',')} :return None
        if work.get('is_new') and (info['score']<3.5 or info['votes']<20):return None
        genres=[g for g in info['genres'] if norm(g) in {norm(t) for t in GENRES}]
        original_year=str(int(float(row['original_publication_year']))) if str(row.get('original_publication_year','')).replace('.','',1).lstrip('-').isdigit() else str(work.get('year') or '')
        return dict(id=work['id'],year=original_year,goodreads_id=ident,title=info['title'],url='https://www.goodreads.com/book/show/'+ident,score=info['score'],votes=info['votes'],genre=', '.join(genres),historical=info['historical'],checked=info['checked'],new_work={k:(json.loads(work[k]) if k=='edition' and isinstance(work[k],str) else work.get(k,'')) for k in ('id','title','year','creator','image','edition')})
    with ThreadPoolExecutor(max_workers=3) as pool:
        for number,item in enumerate(pool.map(convert,matches),1):
            if item:records.append(item)
            if number%100==0:print(f'{number}/{len(matches)} livres examinés',flush=True)
    live_count=sum(not r['historical'] for r in records)
    message=f'{len(records)} livres rattachés à Goodreads avec édition française · {live_count} notes actualisées · {len(records)-live_count} instantanés historiques. Les autres livres restent référencés par Open Library.'
    data=dict(checked=catalog.stamp(),message=message,items=records)
    temporary=SEED.with_suffix('.tmp');temporary.write_bytes(gzip.compress(json.dumps(data,ensure_ascii=False).encode()));temporary.replace(SEED)
    with catalog.connect() as conn:install(conn)
    print(message,flush=True)

if __name__=='__main__':collect()
