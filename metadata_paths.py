"""Deterministic catalogue facets. Every membership is backed by an explicit field."""
import hashlib
import re
from collections import defaultdict
import catalog
import journey_rules

FACETS={'genre':'Genres et types de jeux','decade':'Décennies de sortie','franchise':'Sagas et univers partagés','developer':'Studios et développeurs','publisher':'Éditeurs','author':'Auteurs','country':'Pays de production'}
LABELS={'sci-fi':'Science-fiction','drama':'Drame','comedy':'Comédie','horror':'Horreur','thriller':'Thriller','romance':'Romance','adventure':'Aventure','crime':'Policier','history':'Histoire','war':'Guerre','animation':'Animation','documentary':'Documentaire','biography':'Biographie','family':'Famille','mystery':'Mystère','fps':'FPS — tir à la première personne','tactical fps':'FPS tactiques','third person shooter':'TPS — tir à la troisième personne','third-person shooter':'TPS — tir à la troisième personne','jrpg':'RPG japonais','western rpg':'RPG occidentaux','action rpg':'Action-RPG','2d platformer':'Plateformes en 2D','3d platformer':'Plateformes en 3D','real-time strategy':'Stratégie en temps réel','turn-based strategy':'Stratégie au tour par tour','turn-based tactics':'Tactique au tour par tour','auto racing sim':'Simulation automobile','auto racing':'Course automobile','point-and-click':'Point and click','rhythm':'Jeux de rythme'}

def game_roots(tags):
    roots=set()
    for tag in tags:
        if any(x in tag for x in ('fps','shooter','shoot-','fighting','beat-')):roots.add('action')
        if 'rpg' in tag or 'role-playing' in tag:roots.add('jeux-de-role-et-progression')
        if any(x in tag for x in ('strategy','tactics','tycoon','city-building','management','4x','virtual life')):roots.add('strategie-gestion-et-simulation')
        if any(x in tag for x in ('platformer','metroidvania','puzzle','rhythm')):roots.add('exploration-plateformes-et-enigmes')
        if any(x in tag for x in ('adventure','point-and-click','visual novel','survival')):roots.add('aventure-et-exploration')
        if any(x in tag for x in ('racing','soccer','basketball','football','golf','hockey','tennis','skating','sports','wrestling','boxing')):roots.add('sports-competition-et-performance')
        if 'rhythm' in tag or tag=='music':roots.add('arts-musique-et-creation')
    return roots

def extend(groups,works,taxonomy,companies,countries):
    by_id={g['id']:g for g in groups}
    roots={m['id']:m for m in taxonomy['meta_lists']}
    bases=defaultdict(set)
    # Index each eligible work once. A country is never guessed from language.
    for ident,w in works.items():
        tags=journey_rules.tags(w)
        for meta,values in journey_rules.GENRES.items():
            if tags & set(values):bases[meta].add(ident)
        for meta,values in journey_rules.COUNTRIES.items():
            if set(countries.get(ident,[])) & set(values):bases[meta].add(ident)
        if w['type']=='game':
            for meta in game_roots(tags):bases[meta].add(ident)
        if w['type']=='book' and w.get('creator'):bases['uvres-de-createurs-auteurs-et-studios'].add(ident)
        if ident in companies:
            bases['uvres-de-createurs-auteurs-et-studios'].add(ident)
            if companies[ident].get('franchises'):bases['grandes-sagas-et-univers-partages'].add(ident)
    for g in groups:
        if g['kind']=='meta':bases[g['id']].update(g['members'])
    def summary(g):
        g['members']=sorted(set(g['members']));g['total']=len(g['members']);g['ready']=True
        g['revision']=hashlib.sha256('\n'.join(g['members']).encode()).hexdigest()[:16]
        g['items']=[works[i] for i in sorted(g['members'],key=lambda i:-(works[i].get('votes') or 0))[:16]]
        return g
    for meta_id,base in sorted(bases.items()):
        if len(base)<3 or meta_id not in roots:continue
        meta=roots[meta_id]
        buckets=defaultdict(set);labels={}
        for ident in sorted(base):
            w=works[ident]
            if str(w['year']).isdigit():
                decade=int(w['year'])//10*10
                if 0<decade<=2030:
                    buckets[('decade',str(decade))].add(ident);labels[('decade',str(decade))]=f'Années {decade}'
            root_tags=set(journey_rules.GENRES.get(meta_id,[])[:1])
            for tag in journey_rules.tags(w):
                if tag in root_tags or tag in ('fiction','nonfiction','non-fiction','compilation'):continue
                # Same spelling variants share an explicit gameplay label.
                label=LABELS.get(tag,tag[:1].upper()+tag[1:])
                buckets[('genre',label)].add(ident);labels[('genre',label)]=label
            if w['type']=='book' and w.get('creator'):
                for author in re.split(r',\s+|;',w['creator']):
                    if author.strip():buckets[('author',author.strip())].add(ident);labels[('author',author.strip())]=author.strip()
            for country in countries.get(ident,[]):
                buckets[('country',country)].add(ident);labels[('country',country)]=country
            for facet,field in [('franchise','franchises'),('developer','developers'),('publisher','publishers')]:
                for name in companies.get(ident,{}).get(field,[]):
                    buckets[(facet,name)].add(ident);labels[(facet,name)]=name
        # Merge spelling that differs only by letter case; keep accents and legal studio names.
        merged=defaultdict(set);display={}
        for (facet,key),ids in buckets.items():
            normalized_key=key.strip().casefold()
            merged[(facet,normalized_key)].update(ids)
            display.setdefault((facet,normalized_key),labels[(facet,key)])
        buckets=merged;labels=display
        seen={tuple(sorted(g['members'])) for g in groups if g.get('meta')==meta_id and g['kind']=='sublist'}
        additions=defaultdict(list)
        for (facet,key),ids in sorted(buckets.items(),key=lambda pair:(list(FACETS).index(pair[0][0]),pair[0][1])):
            if len(ids)<3 or (facet=='genre' and ids==base):continue
            signature=tuple(sorted(ids))
            if signature in seen:continue
            seen.add(signature)
            label=labels[(facet,key)]
            title={'franchise':'Saga — ','country':'Production — ','developer':'Développés par ','publisher':'Édités par ','author':'Œuvres de '}.get(facet,'')+label
            group_id=meta_id+'/metadonnees-'+facet
            stable=hashlib.sha256(key.encode()).hexdigest()[:12]
            g=summary(dict(id=group_id+'/'+stable,title=title,kind='sublist',meta=meta_id,family=meta['family'],parent=group_id,breadcrumb=[meta['title'],FACETS[facet]],members=list(ids),facet=facet,criterion=dict(field=facet,value=key),subtitle='Métadonnées du catalogue'))
            by_id[g['id']]=g;additions[facet].append(g)
        if not additions:continue
        if meta_id not in by_id:
            by_id[meta_id]=dict(id=meta_id,title=meta['title'],kind='meta',meta=meta_id,family=meta['family'],parent='',breadcrumb=[],children=[],members=[])
        root=by_id[meta_id]
        for facet,children in additions.items():
            group_id=meta_id+'/metadonnees-'+facet
            group=summary(dict(id=group_id,title=FACETS[facet],kind='group',meta=meta_id,family=meta['family'],parent=meta_id,breadcrumb=[meta['title']],children=[g['id'] for g in children],members=[i for g in children for i in g['members']]))
            by_id[group_id]=group;root['children'].append(group_id)
    # Children precede their parents for medium projection; parent totals are always unions.
    ordered=[];visited=set()
    def visit(ident):
        if ident in visited:return
        visited.add(ident);g=by_id[ident]
        if 'children' in g:
            for child in g['children']:visit(child)
            g['members']=[i for child in g['children'] for i in by_id[child]['members']]
        summary(g);ordered.append(g)
    for root in sorted((g for g in by_id.values() if g['kind']=='meta'),key=lambda g:list(roots).index(g['id'])):visit(root['id'])
    return ordered
