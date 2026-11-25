import gzip,json,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import catalog,external_links,goodreads_books

class WorkCardsTest(unittest.TestCase):
    def test_justwatch_matches_identity_and_filters_physical_offers(self):
        movie={'__typename':'Movie','id':'1','content(locale:fr)':{'__typename':'MovieContent','id':'c','originalTitle':'Alien','originalReleaseYear':1979,'externalIds':{'imdbId':'tt0078748'}},'offers(country:FR)':[
            {'__typename':'Offer','id':'a','country':'FR','presentationType':'HD','monetizationType':'FLATRATE','package':{'clearName':'Test subscription'}},
            {'__typename':'Offer','id':'b','country':'FR','presentationType':'DVD','monetizationType':'BUY','package':{'clearName':'Physical shop'}},
            {'__typename':'Offer','id':'c','country':'US','presentationType':'HD','monetizationType':'BUY','package':{'clearName':'US shop'}}]}
        pool=[]
        def encode(v):
            n=len(pool);pool.append(None)
            pool[n]={k:encode(x) for k,x in v.items()} if isinstance(v,dict) else [encode(x) for x in v] if isinstance(v,list) else v
            return n
        encode(movie);markup='<script id="__NUXT_DATA__">'+json.dumps(pool)+'</script>'
        work={'id':'imdb:tt0078748','title':'Alien','year':1979}
        result=external_links.parse_justwatch(markup,work,'https://www.justwatch.com/fr/film/alien')
        self.assertEqual(result['offers'],[{'provider':'Test subscription','mode':'Abonnement'}])
        with self.assertRaises(ValueError):external_links.parse_justwatch(markup,{**work,'id':'imdb:tt0000000'},'https://example.com')

    def test_portable_goodreads_seed_keeps_french_gate_and_rating_date(self):
        with tempfile.TemporaryDirectory() as d:
            seed=Path(d)/'seed.gz'
            records=[]
            for lang in ['français','english']:
                ident='book:'+lang
                records.append(dict(id=ident,year='1921',title='Original',genre='Psychology',score=4.1,votes=100,url='https://www.goodreads.com/book/show/123',historical=True,checked='2026-11-26',new_work=dict(id=ident,title='Titre',creator='Auteur',year=1921,image='',edition={'language':lang,'url':'https://openlibrary.org/books/1'})))
            seed.write_bytes(gzip.compress(json.dumps({'items':records,'message':'test','checked':'2026-11-26'}).encode()))
            conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
            conn.executescript('CREATE TABLE works(id TEXT PRIMARY KEY,type,title,search,year,genre,creator,image,length,score,votes,evidence,edition,updated); CREATE TABLE sources(id PRIMARY KEY,status,message,updated,count);')
            with patch.object(goodreads_books,'SEED',seed):goodreads_books.install(conn);goodreads_books.install(conn)
            rows=conn.execute('SELECT * FROM works').fetchall();self.assertEqual(len(rows),1)
            proof=json.loads(rows[0]['evidence'])[0]
            self.assertIn('2017',proof['label']);self.assertEqual(rows[0]['year'],'1921')
            self.assertEqual(proof['value'],4.1)

    def test_all_movement_selections_meet_minimum(self):
        import journeys
        groups={g['id']:g for g in journeys.overview()['groups']}
        for slug in ['expressionnisme-allemand','nouvelle-vague','neorealisme-italien','modernisme-litteraire']:
            self.assertGreaterEqual(groups['mouvements-et-courants-culturels/'+slug]['total'],3)
        for slug in ['psychanalyse','psychologie-analytique','humanisme-sens']:
            self.assertGreaterEqual(groups['psychologie-et-developpement-personnel/'+slug]['total'],3)
