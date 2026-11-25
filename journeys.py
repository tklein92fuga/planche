"""Versioned editorial taxonomy with conservative, inspectable catalogue assignments."""
import hashlib
import json
import re
import threading
from pathlib import Path
import catalog
import journey_rules
import metadata_paths

LOCK = threading.Lock()
CACHE = None
SIGNATURE = None
DATA = Path(__file__).parent / 'data'
MIN_WORKS = 3

# Exact titles only. An absent title does not create a catalogue record.
CURATED = {
    'Cyberpunk': ['Blade Runner', 'Blade Runner 2049', 'The Matrix', 'Ghost in the Shell', 'Akira', 'Neuromancer', 'Snow Crash', 'Cyberpunk 2077', 'Deus Ex', 'Deus Ex: Human Revolution', 'Deus Ex: Mankind Divided', 'System Shock', 'System Shock 2'],
    'Space opera': ['Dune', 'Dune: Part Two', 'Dune Messiah', 'Star Wars', 'The Empire Strikes Back', 'Return of the Jedi', 'Mass Effect', 'Mass Effect 2', 'Mass Effect 3'],
    'Post-apocalyptique': ['The Road', 'Mad Max: Fury Road', 'Fallout', 'Fallout 2', 'Fallout: New Vegas', 'Metro 2033', 'Metro: Last Light', 'Metro Exodus'],
}

def overview(kind="all"):
    global CACHE, SIGNATURE
    with LOCK:
        with catalog.connect() as conn:
            signature = tuple(conn.execute('SELECT count(*),total(length(genre)),max(updated) FROM works').fetchone())
            signature += ((DATA/'taxonomy.json').stat().st_mtime_ns,(DATA/'editorial-lists.json').stat().st_mtime_ns,(DATA/'company-metadata.json').stat().st_mtime_ns if (DATA/'company-metadata.json').exists() else 0)
            if CACHE is not None and SIGNATURE == signature:
                return project(CACHE,kind)
            countries={r['id']:json.loads(r['countries']) for r in conn.execute('SELECT id,countries FROM work_details')}
            rows = conn.execute('SELECT *, '+catalog.CANONICAL+' canonical FROM works ORDER BY score DESC,id').fetchall()
        taxonomy = json.loads((DATA/'taxonomy.json').read_text())
        editorial=json.loads((DATA/'editorial-lists.json').read_text())
        for meta in taxonomy['meta_lists']:
            meta['children'].extend(node for node in editorial if node['meta']==meta['id'])
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
        tagged={}
        for ident,w in works.items():
            for tag in journey_rules.tags(w):tagged.setdefault(tag,set()).add(ident)
        groups=[]
        def build(node,meta,parent='',trail=()):
            result={k:v for k,v in node.items() if k not in ('children','selection')}
            result.update(meta=meta['id'],family=meta['family'],parent=parent,breadcrumb=list(trail),items=[])
            if node.get('children'):
                children=[child for c in node['children'] if (child:=build(c,meta,node['id'],(*trail,node['title']))) ]
                own=[]
                if not children:return None
                result['directMembers']=own
                result['children']=[c['id'] for c in children]
                result['members']=sorted(set(own)|{i for c in children for i in c['members']})
                result['ready']=all(c['ready'] for c in children)
                result['populated']=sum(bool(c['total']) for c in children)
            else:
                titles={catalog.normalized(t) for t in CURATED.get(node['title'],[])}
                members=[]
                creator_family='createur' in catalog.normalized(meta['title'])
                award_family=meta['id'].startswith('uvres-')
                candidates=set().union(*(by_title.get(t,set()) for t in titles)) if titles else set()
                selected_ids={i['id'] for i in node.get('selection',[]) if i.get('id')}
                selections={(catalog.normalized(i['title']),str(i['year']),i['type']) for i in node.get('selection',[]) if i.get('title')}
                candidates.update(selected_ids & works.keys())
                for title,year,kind in selections:candidates.update(by_title.get(title,set()))
                if creator_family:candidates.update(by_creator.get(catalog.normalized(node['title']),set()))
                if award_family:candidates.update(award_ids)
                for tag in journey_rules.SUBJECTS.get(node['title'],[]):candidates.update(tagged.get(tag,set()))
                for ident in candidates:
                    w=works[ident]
                    matched=ident in selected_ids or catalog.normalized(w['title']) in titles or journey_rules.sub_match(node,w) or (catalog.normalized(w['title']),str(w['year']),w['type']) in selections
                    if creator_family:
                        creator=catalog.normalized(node['title'])
                        credits=[catalog.normalized(c) for c in re.split(r'[,;]',w.get('creator',''))]
                        matched=matched or creator in credits
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
            if result['total'] < MIN_WORKS:return None
            result['revision']=hashlib.sha256('\n'.join(sorted(result['members'])).encode()).hexdigest()[:16]
            result['items']=[works[i] for i in sorted(result['members'],key=lambda i:-(works[i].get('votes') or 0))[:16]]
            result['subtitle']='Sélection documentée' if result['ready'] else 'Sélection à compléter'
            groups.append(result)
            return result
        epochs=next(m for m in taxonomy['meta_lists'] if m['id']=='mouvements-et-courants-culturels')
        epoch_nodes=[]
        for decade in range(1920,2030,10):
            selected_works=[dict(title=w['title'],year=str(w['year']),type='film') for w in works.values() if w['type']=='film' and str(w['year']).isdigit() and decade<=int(w['year'])<decade+10]
            if len(selected_works)>=MIN_WORKS:
                epoch_nodes.append(dict(id=epochs['id']+'/sorties-'+str(decade),title='Cinéma des années '+str(decade),kind='sublist',selection=selected_works))
        epochs['children'].append(dict(id=epochs['id']+'/epoques-du-cinema',title='Époques du cinéma',kind='group',children=epoch_nodes))
        book_epochs=[]
        for start,end,label in [(0,1499,'Avant 1500'),(1500,1699,'XVIe et XVIIe siècles'),(1700,1799,'XVIIIe siècle'),(1800,1899,'XIXe siècle'),(1900,1945,'1900–1945'),(1946,1999,'1946–1999'),(2000,2099,'Depuis 2000')]:
            selected=[{'id':w['id']} for w in works.values() if w['type']=='book' and str(w['year']).isdigit() and start<=int(w['year'])<=end]
            if len(selected)>=MIN_WORKS:book_epochs.append(dict(id=epochs['id']+'/livres-epoque-'+str(start),title='Livres · '+label,kind='sublist',selection=selected))
        epochs['children'].append(dict(id=epochs['id']+'/epoques-litteraires',title='Époques de publication des livres',kind='group',children=book_epochs))
        for meta in taxonomy['meta_lists']:
            build(meta,meta)
        records=json.loads((DATA/'company-metadata.json').read_text()) if (DATA/'company-metadata.json').exists() else []
        canonical={row['id']:row['canonical'] for row in rows}
        companies={canonical[r['id']]:r for r in records if r['id'] in canonical}
        groups=metadata_paths.extend(groups,works,taxonomy,companies,countries)
        CACHE={'groups':groups,'version':taxonomy['version'],'coverage':{'populated':sum(g['kind']=='sublist' and g['total']>0 for g in groups),'sublists':sum(g['kind']=='sublist' for g in groups),'metaLists':sum(g['kind']=='meta' for g in groups),'minimumWorks':MIN_WORKS}}
        SIGNATURE=signature
        CACHE['_works']=works
        return project(CACHE,kind)

def detail(ident,page,kind="all"):
    data=overview(kind)
    group=next((g for g in data['groups'] if g['id']==ident),None)
    if not group:return None
    result=dict(group)
    ids=sorted(group['members'],key=lambda i:-(CACHE['_works'][i].get('votes') or 0))
    result.update(items=[CACHE['_works'][i] for i in ids[(page-1)*60:page*60]],page=page,pageSize=60)
    return result


def project(data,kind):
    public={k:v for k,v in data.items() if not k.startswith('_')}
    if kind not in ('film','book','game'):return public
    groups=[]
    for original in data['groups']:
        ids=[ident for ident in original['members'] if data['_works'][ident]['type']==kind]
        if len(ids)<MIN_WORKS:continue
        g=dict(original,members=ids,total=len(ids),items=[data['_works'][i] for i in sorted(ids,key=lambda i:-(data['_works'][i].get('votes') or 0))[:16]])
        idset=set(ids)
        if 'directMembers' in g:g['directMembers']=[i for i in g['directMembers'] if i in idset]
        groups.append(g)
    kept={}
    for g in groups:
        if 'children' in g:
            g['children']=[i for i in g['children'] if i in kept]
            if not g['children']:continue
            ids=sorted({ident for child in g['children'] for ident in kept[child]['members']})
            g.update(members=ids,total=len(ids),items=[data['_works'][i] for i in sorted(ids,key=lambda i:-(data['_works'][i].get('votes') or 0))[:16]])
        kept[g['id']]=g
    groups=list(kept.values())
    return dict(public,groups=groups,media=kind,coverage=dict(populated=sum(g['kind']=='sublist' for g in groups),sublists=sum(g['kind']=='sublist' for g in groups),metaLists=sum(g['kind']=='meta' for g in groups),minimumWorks=MIN_WORKS))
