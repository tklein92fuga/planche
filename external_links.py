"""Work-card destinations and public French JustWatch offers, matched by identity."""
import json
import re
import threading
import time
from urllib.parse import quote,urlencode
from urllib.request import Request,urlopen
import catalog

LIMIT=threading.BoundedSemaphore(4)

def page(url):
    request=Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; Planche personal catalogue)','Accept':'text/html'})
    with urlopen(request,timeout=7,context=catalog.context()) as response:
        if response.status!=200:raise ValueError('Source momentanément indisponible')
        return response.read(3*1024*1024).decode('utf-8')

def nuxt_entities(markup):
    match=re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>',markup,re.S)
    if not match:raise ValueError('Informations JustWatch indisponibles')
    pool=json.loads(match[1]);memo={}
    def decode(index,depth=0):
        if index<0 or depth>20:return None
        if index in memo:return memo[index]
        v=pool[index]
        if isinstance(v,dict):v={k:decode(i,depth+1) for k,i in v.items()}
        elif isinstance(v,list):v=[decode(i,depth+1) if isinstance(i,int) else i for i in v]
        memo[index]=v
        return v
    entities={};movies=[]
    for i,v in enumerate(pool):
        if not isinstance(v,dict) or '__typename' not in v:continue
        kind=pool[v['__typename']]
        if kind not in ('Movie','MovieContent','Package','Offer'):continue
        item=decode(i)
        if item.get('id'):entities[kind+':'+str(item['id'])]=item
        if kind=='Movie':movies.append(item)
    def resolve(v):return entities.get(v.get('__ref'),{}) if isinstance(v,dict) and '__ref' in v else v
    return movies,resolve

def content(movie,resolve):
    return [resolve(v) for k,v in movie.items() if k.startswith('content(') and isinstance(resolve(v),dict)]

def identity(movie,resolve,work):
    for c in content(movie,resolve):
        external=c.get('externalIds') or {}
        if work['id'].startswith('imdb:') and external.get('imdbId'):
            if external['imdbId']==work['id'].split(':')[1]:return c
            continue
        title=c.get('originalTitle') or c.get('title','')
        if catalog.normalized(title)==catalog.normalized(work['title']) and str(c.get('originalReleaseYear'))==str(work['year']):return c
    return None

def parse_justwatch(markup,work,url):
    movies,resolve=nuxt_entities(markup)
    for movie in movies:
        c=identity(movie,resolve,work)
        if not c:continue
        offers=[];seen=set()
        for key,values in movie.items():
            if not key.startswith('offers(') or any(t in key for t in ('DVD','BLURAY')):continue
            for ref in values or []:
                offer=resolve(ref)
                if not isinstance(offer,dict) or offer.get('country')!='FR' or offer.get('presentationType') in ('DVD','BLURAY','BLURAY_4K'):continue
                mode=offer.get('monetizationType');package=resolve(offer.get('package',{}))
                name=package.get('clearName') if isinstance(package,dict) else ''
                label={'FLATRATE':'Abonnement','FLATRATE_AND_BUY':'Abonnement et achat','RENT':'Location','BUY':'Achat','FREE':'Gratuit','ADS':'Avec publicité','FAST':'Chaîne gratuite'}.get(mode)
                if not name or not label or (name,label) in seen:continue
                seen.add((name,label));offers.append(dict(provider=name,mode=label))
        return dict(url=url,verified=True,offers=offers,country='FR',checked=catalog.stamp())
    raise ValueError('La fiche JustWatch ne correspond pas à cette œuvre')

def justwatch(work):
    search='https://www.justwatch.com/fr/recherche?'+urlencode({'q':work['title']})
    movies,resolve=nuxt_entities(page(search));candidates=[]
    for movie in movies:
        for c in content(movie,resolve):
            path=c.get('fullPath','')
            if path.startswith('/fr/film/') and str(c.get('originalReleaseYear'))==str(work['year']) and path not in candidates:candidates.append(path)
    for path in candidates[:3]:
        try:return parse_justwatch(page('https://www.justwatch.com'+path),work,'https://www.justwatch.com'+path)
        except (OSError,ValueError,TypeError):continue
    return dict(url=search,verified=False,offers=[],country='FR',checked=catalog.stamp())

def steam(work):
    match=re.fullmatch(r'steam:(\d+)',work['id'])
    if match:return dict(url='https://store.steampowered.com/app/'+match[1]+'/',verified=True)
    url='https://store.steampowered.com/api/storesearch/?'+urlencode({'term':work['title'],'l':'french','cc':'FR'})
    with urlopen(Request(url,headers={'User-Agent':'Planche/1.3'}),timeout=6,context=catalog.context()) as response:data=json.load(response)
    candidates=[i for i in data.get('items',[]) if catalog.normalized(i.get('name',''))==catalog.normalized(work['title'])]
    if len(candidates)==1:
        appid=str(int(candidates[0]['id']))
        with urlopen(Request('https://store.steampowered.com/api/appdetails?'+urlencode({'appids':appid,'l':'english'}),headers={'User-Agent':'Planche/1.3'}),timeout=6,context=catalog.context()) as response:detail=json.load(response).get(appid,{}).get('data',{})
        years=re.findall(r'\b(?:19|20)\d{2}\b',detail.get('release_date',{}).get('date',''))
        if detail.get('type')=='game' and years and str(work.get('year','')).isdigit() and abs(int(years[-1])-int(work['year']))<=1:
            return dict(url='https://store.steampowered.com/app/'+appid+'/',verified=True)
    return dict(url='https://store.steampowered.com/search/?'+urlencode({'term':work['title']}),verified=False)

def card(ident):
    with catalog.connect() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS external_cards(id TEXT PRIMARY KEY,data TEXT,checked REAL)')
        old=conn.execute('SELECT data,checked FROM external_cards WHERE id=?',(ident,)).fetchone()
        if old and time.time()-old['checked']<86400:return json.loads(old['data'])
        row=conn.execute('SELECT * FROM works WHERE id=? OR '+catalog.CANONICAL+'=? ORDER BY score DESC LIMIT 1',(ident,ident)).fetchone()
    if not row:return None
    work=catalog.serialize(row);work['id']=ident
    result=dict(links=[],offers=[],country='FR',checked=catalog.stamp())
    try:
        with LIMIT:
            if work['type']=='film':
                found=justwatch(work);result.update(found);result['links']=[dict(label='Voir la fiche JustWatch' if found['verified'] else 'Rechercher sur JustWatch',url=found['url'])]
            elif work['type']=='game':
                found=steam(work);result.update(found);result['links']=[dict(label='Voir la page Steam' if found['verified'] else 'Rechercher sur Steam',url=found['url'])]
            else:
                proof=next((e for e in work['evidence'] if e.get('source')=='Goodreads' and e.get('url','').startswith('https://www.goodreads.com/book/show/')),None)
                result['verified']=bool(proof)
                result['links']=[dict(label='Voir la fiche Goodreads' if proof else 'Rechercher sur Goodreads',url=proof['url'] if proof else 'https://www.goodreads.com/search?'+urlencode({'q':work['title']+' '+work['creator']}))]
                edition=work.get('edition') or {}
                if edition.get('url','').startswith('https://openlibrary.org/'):result['links'].append(dict(label='Édition française',url=edition['url']))
    except (OSError,ValueError,TypeError,KeyError):
        result['verified']=False
        result['message']='La source ne répond pas pour le moment.'
        base={'film':'https://www.justwatch.com/fr/recherche?','game':'https://store.steampowered.com/search/?','book':'https://www.goodreads.com/search?'}[work['type']]
        result['links']=[dict(label='Rechercher sur '+{'film':'JustWatch','game':'Steam','book':'Goodreads'}[work['type']],url=base+urlencode({'term' if work['type']=='game' else 'q':work['title']}))]
    with catalog.connect() as conn:conn.execute('INSERT OR REPLACE INTO external_cards VALUES(?,?,?)',(ident,json.dumps(result,ensure_ascii=False),time.time()))
    return result
