"""Versioned editorial taxonomy with conservative, inspectable catalogue assignments."""
import hashlib
import json
import re
import threading
from pathlib import Path
import catalog

LOCK = threading.Lock()
CACHE = None
SIGNATURE = None
DATA = Path(__file__).parent / 'data'

# Exact titles only. An absent title does not create a catalogue record.
CURATED = {
    'Cyberpunk': ['Blade Runner', 'Blade Runner 2049', 'The Matrix', 'Ghost in the Shell', 'Akira', 'Neuromancer', 'Snow Crash', 'Cyberpunk 2077', 'Deus Ex', 'Deus Ex: Human Revolution', 'Deus Ex: Mankind Divided', 'System Shock', 'System Shock 2'],
    'Space opera': ['Dune', 'Dune: Part Two', 'Dune Messiah', 'Star Wars', 'The Empire Strikes Back', 'Return of the Jedi', 'Mass Effect', 'Mass Effect 2', 'Mass Effect 3'],
    'Post-apocalyptique': ['The Road', 'Mad Max: Fury Road', 'Fallout', 'Fallout 2', 'Fallout: New Vegas', 'Metro 2033', 'Metro: Last Light', 'Metro Exodus'],
}

def overview():
    global CACHE, SIGNATURE
    with LOCK:
        with catalog.connect() as conn:
            signature = tuple(conn.execute('SELECT count(*),total(length(genre)),max(updated) FROM works').fetchone())
            signature += ( (DATA/'taxonomy.json').stat().st_mtime_ns,)
            if CACHE is not None and SIGNATURE == signature:
                return {k:v for k,v in CACHE.items() if not k.startswith('_')}
            rows = conn.execute('SELECT *, '+catalog.CANONICAL+' canonical FROM works ORDER BY score DESC,id').fetchall()
        taxonomy = json.loads((DATA/'taxonomy.json').read_text())
        works = {}
        proofs = {}
        for row in rows:
            ident=row['canonical']
            proofs.setdefault(ident,[]).extend(json.loads(row['evidence']))
            if ident not in works:
                item=catalog.serialize(row);item['id']=ident
                item.pop('canonical',None);works[ident]=item
            else:
                for field in ('creator','genre','image','length','edition'):
                    if not works[ident].get(field) and row[field]:
                        works[ident][field]=json.loads(row[field]) if field=='edition' else row[field]
        for ident,item in works.items():
            item['evidence']=list({json.dumps(p,sort_keys=True):p for p in proofs[ident]}.values())
        by_title={}
        by_creator={}
        award_ids=set()
        for ident,w in works.items():
            by_title.setdefault(catalog.normalized(w['title']),set()).add(ident)
            for credit in re.split(r'[,;]',w.get('creator','')):
                by_creator.setdefault(catalog.normalized(credit),set()).add(ident)
            if any(p.get('kind')=='award' for p in proofs[ident]):award_ids.add(ident)
        groups=[]
        def build(node,meta,parent='',trail=()):
            result={k:v for k,v in node.items() if k!='children'}
            result.update(meta=meta['id'],family=meta['family'],parent=parent,breadcrumb=list(trail),items=[])
            if node.get('children'):
                children=[build(c,meta,node['id'],(*trail,node['title'])) for c in node['children']]
                result['children']=[c['id'] for c in children]
                result['members']=sorted({i for c in children for i in c['members']})
                result['ready']=all(c['ready'] for c in children)
                result['populated']=sum(bool(c['total']) for c in children)
            else:
                titles={catalog.normalized(t) for t in CURATED.get(node['title'],[])}
                members=[]
                creator_family='createur' in catalog.normalized(meta['title'])
                award_family=meta['id'].startswith('uvres-')
                candidates=set().union(*(by_title.get(t,set()) for t in titles)) if titles else set()
                if creator_family:candidates.update(by_creator.get(catalog.normalized(node['title']),set()))
                if award_family:candidates.update(award_ids)
                for ident in candidates:
                    w=works[ident]
                    matched=catalog.normalized(w['title']) in titles
                    if creator_family:
                        creator=catalog.normalized(node['title'])
                        credits=[catalog.normalized(c) for c in re.split(r'[,;]',w.get('creator',''))]
                        matched=creator in credits
                    if award_family:
                        nominated='nommees' in meta['id']
                        for proof in proofs[ident]:
                            if proof.get('kind')!='award' or not proof.get('url'):continue
                            is_nomination=bool(proof.get('nomination'))
                            label=re.sub(r'[^a-z0-9]','',catalog.normalized(proof.get('label','')))
                            name=re.sub(r'[^a-z0-9]','',catalog.normalized(node['title']))
                            parent_name=catalog.normalized(trail[-1]) if trail else ''
                            match_award=(('palme' in name and 'palme' in label) or
                                ('liondor' in name and 'liondor' in label) or
                                ('bookerprize'==name and 'booker' in label) or
                                (name in ('gameoftheyear','thegameawardsgameoftheyear') and label=='gameoftheyear' and 'thegameawards.com' in proof['url']) or
                                (name=='meilleurfilm' and 'oscar' in parent_name and ('bestpicture' in label or 'meilleurfilm' in label)))
                            if match_award and is_nomination==nominated:matched=True
                    if matched:members.append(ident)
                result['members']=members
                result['ready']=bool(members)
            result['total']=len(result['members'])
            result['revision']=hashlib.sha256('\n'.join(sorted(result['members'])).encode()).hexdigest()[:16]
            result['items']=[works[i] for i in sorted(result['members'],key=lambda i:-(works[i].get('votes') or 0))[:16]]
            result['subtitle']='Sélection documentée' if result['ready'] else 'Sélection à compléter'
            groups.append(result)
            return result
        for meta in taxonomy['meta_lists']:
            build(meta,meta)
        CACHE={'groups':groups,'version':taxonomy['version'],'coverage':{'populated':sum(g['kind']=='sublist' and g['total']>0 for g in groups),'sublists':taxonomy['counts']['sub_lists']}}
        SIGNATURE=signature
        CACHE['_works']=works
        return {k:v for k,v in CACHE.items() if not k.startswith('_')}

def detail(ident,page):
    data=overview()
    group=next((g for g in data['groups'] if g['id']==ident),None)
    if not group:return None
    result=dict(group)
    ids=sorted(group['members'],key=lambda i:-(CACHE['_works'][i].get('votes') or 0))
    result.update(items=[CACHE['_works'][i] for i in ids[(page-1)*60:page*60]],page=page,pageSize=60)
    return result
