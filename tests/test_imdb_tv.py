import gzip,json,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import imdb_tv

class IMDbTVTest(unittest.TestCase):
    def row(self,kind='tvSeries'):
        return dict(tconst='tt0903747',titleType=kind,primaryTitle='Breaking Bad',originalTitle='Breaking Bad',startYear='2008',endYear='2013',genres='Crime,Drama,Thriller',runtimeMinutes='45')
    def test_series_miniseries_and_film_are_separate(self):
        for kind in ('tvSeries','tvMiniSeries'):
            item=imdb_tv.item(self.row(kind),7,1000)
            self.assertEqual(item['type'],'tv');self.assertEqual(item['evidence'][0]['endYear'],'2013')
        self.assertEqual(imdb_tv.item(self.row('movie'),7,1000)['type'],'film')
        self.assertIsNone(imdb_tv.item(self.row('tvEpisode'),9.9,100000))
        self.assertIsNone(imdb_tv.item(self.row(),6.9,10000));self.assertIsNone(imdb_tv.item(self.row(),9.0,999))
        row=self.row();row['endYear']='\\N';self.assertEqual(imdb_tv.item(row,8,1000)['evidence'][0]['endYear'],'')
    def test_seed_preserves_films_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            seed=Path(d)/'series.gz';item=imdb_tv.item(self.row(),9.5,10000)
            seed.write_bytes(gzip.compress(json.dumps({'checked':'2026-11-26','items':[item]}).encode()))
            c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
            c.executescript("CREATE TABLE works(id TEXT PRIMARY KEY,type,title,search,year,genre,creator,image,length,score,votes,evidence,edition,updated);CREATE TABLE sources(id PRIMARY KEY,status,message,updated,count);INSERT INTO works(id,type) VALUES('imdb:film','film');")
            with patch.object(imdb_tv,'SEED',seed):imdb_tv.install(c);imdb_tv.install(c)
            self.assertEqual(c.execute('SELECT count(*) FROM works').fetchone()[0],2)
            self.assertEqual(c.execute("SELECT type FROM works WHERE id='imdb:film'").fetchone()[0],'film')
            self.assertEqual(c.execute("SELECT type FROM works WHERE id='imdb:tt0903747'").fetchone()[0],'tv')
