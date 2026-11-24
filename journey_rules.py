"""Explicit metadata mappings. Missing subjects never imply membership."""
import re
import catalog

GENRES={
 'science-fiction':['sci-fi','science fiction','science-fiction'],
 'fantasy':['fantasy','epic fantasy','high fantasy'],
 'fantastique-et-merveilleux':['fantasy','magical realism','supernatural'],
 'horreur':['horror','survival horror'],
 'policier-et-enquete':['crime','mystery','detective'],
 'thriller-et-suspense':['thriller','psychological thriller'],
 'aventure-et-exploration':['adventure','action adventure','open-world adventure'],
 'action':['action','action adventure','open-world action','fps','third-person shooter','tactical fps','fighting'],
 'drames-et-recits-humains':['drama'],
 'comedie-et-satire':['comedy','satire','humor'],
 'amour-et-relations':['romance','love stories'],
 'western-et-frontieres':['western'],
 'histoire-et-memoire':['history','historical fiction','biography'],
 'guerres-et-conflits':['war','military'],
 'documentaire-et-non-fiction':['documentary','nonfiction','non-fiction'],
 'animation-et-mondes-dessines':['animation'],
 'enfance-adolescence-et-initiation':['coming of age','young adult','juvenile fiction','family'],
 'sports-competition-et-performance':['sport','sports','soccer','basketball','baseball','football','racing'],
 'jeux-de-role-et-progression':['rpg','role-playing','action rpg','jrpg','western rpg','tactical rpg','dungeon crawler'],
 'strategie-gestion-et-simulation':['strategy','real-time strategy','turn-based strategy','4x strategy','simulation','management','city-building','grand strategy'],
 'exploration-plateformes-et-enigmes':['platformer','2d platformer','3d platformer','puzzle','puzzle adventure','metroidvania'],
 'poesie-theatre-et-recits-brefs':['poetry','drama (literature)','short stories','plays'],
}
SUBJECTS={
 'Cyberpunk':['cyberpunk'], 'Space opera':['space opera'], 'Post-apocalyptique':['post-apocalyptic','post apocalyptic'],
 'Fantasy épique':['epic fantasy'], 'Dark fantasy':['dark fantasy'], 'Fantasy urbaine':['urban fantasy'],
 'Fantasy humoristique':['humorous fantasy','comic fantasy'], 'Fantasy historique':['historical fantasy'],
 'Horreur psychologique':['psychological horror'], 'Survival horror':['survival horror'],
 'Action-RPG':['action rpg'], 'RPG japonais':['jrpg','japanese rpg'], 'RPG occidentaux':['western rpg'],
 'RPG tactiques':['tactical rpg'], 'Dungeon crawlers':['dungeon crawler'],
 'Grande stratégie':['grand strategy'], '4X et construction d’empires':['4x strategy'],
 'City builders':['city-building'], 'Tower defense':['tower defense'],
 'Simulation de vie':['life simulation'], 'Simulation agricole':['farming sim'],
 'Metroidvania':['metroidvania'], 'Point and click':['point-and-click'],
 'Jeux de rythme':['rhythm'], 'Soulslike':['souls-like','soulslike'],
 'Roguelike':['roguelike'], 'Roguelite':['roguelite'],
 'Stratégie en temps réel':['real-time strategy'], 'Stratégie au tour par tour':['turn-based strategy'],
 'Plateformes en 2D':['2d platformer'], 'Plateformes en 3D':['3d platformer'],
}
COUNTRIES={
 'culture-francaise':['France'], 'culture-japonaise':['Japon'], 'culture-des-etats-unis':['États-Unis'],
 'cultures-du-royaume-uni-et-dirlande':['Royaume-Uni','Irlande'],
 'cultures-germaniques':['Allemagne','Autriche','Suisse'], 'culture-italienne':['Italie'],
 'cultures-iberiques':['Espagne','Portugal'], 'cultures-nordiques':['Suède','Norvège','Danemark','Finlande','Islande'],
 'culture-coreenne':['Corée du Sud','Corée du Nord'],
 'cultures-chinoises-hongkongaises-et-taiwanaises':['Chine','Hong Kong','Taïwan'],
 'cultures-du-canada-et-du-quebec':['Canada'],
 'cultures-doceanie-et-peuples-autochtones':['Australie','Nouvelle-Zélande'],
 'cultures-du-benelux':['Belgique','Pays-Bas','Luxembourg'],
}

def tags(work):return {catalog.normalized(v.strip()) for v in re.split(r'[,;]',work.get('genre','')) if v.strip()}
def root_match(meta,work,countries):
    ident=meta['id']
    return bool(tags(work)&set(GENRES.get(ident,[]))) or bool(set(countries)&set(COUNTRIES.get(ident,[])))
def sub_match(node,work):return bool(tags(work)&set(SUBJECTS.get(node['title'],[])))
