import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import catalog
import metacritic
import server

class MetacriticTest(unittest.TestCase):
    def record(self,score=70,votes=10):
        return dict(type='game-title',slug='test-game',title='Test Game',premiereYear=2020,criticScoreSummary=dict(score=score,reviewCount=votes),genres=[dict(name='Action RPG')],platforms=[dict(name='PC')],image=dict(bucketPath='/provider/example.jpg'))

    def test_thresholds_are_critics(self):
        record=metacritic.item(self.record())
        self.assertEqual(record['score'],70)
        self.assertEqual(record['votes'],10)
        self.assertEqual(record['evidence'][0]['source'],'Metacritic')
        self.assertIsNone(metacritic.item(self.record(69,100)))
        self.assertIsNone(metacritic.item(self.record(99,9)))
        self.assertIsNone(metacritic.item(self.record(None,100)))

    def test_game_enrichment_uses_local_metacritic(self):
        server.metadata.cache_clear()
        with patch.object(server,'remote',side_effect=AssertionError('No Steam lookup')):
            data=server.metadata('game','Cyberpunk 2077','2020')
        self.assertEqual(data['source'],'Metacritic')
        self.assertEqual(data['genre'],'Action RPG')

    def test_public_nuxt_payload(self):
        pool=[]
        def encode(v):
            n=len(pool);pool.append(None)
            pool[n]={k:encode(x) for k,x in v.items()} if isinstance(v,dict) else [encode(x) for x in v] if isinstance(v,list) else v
            return n
        encode(dict(items=[self.record()],total=1))
        data=metacritic.browse('<script type="application/json" id="__NUXT_DATA__">'+json.dumps(pool)+'</script>')
        self.assertEqual(data['items'][0]['title'],'Test Game')
        with self.assertRaises(ValueError):metacritic.browse('<html>Source inaccessible</html>')

    def test_fresh_seed_migration_and_legacy_progress_ids(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(catalog,'DB',Path(directory)/'catalog.sqlite3'):
            with catalog.connect() as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM works WHERE id LIKE 'steam:%'").fetchone()[0],0)
                count=conn.execute("SELECT count(*) FROM works WHERE id LIKE 'metacritic:%'").fetchone()[0]
                self.assertGreater(count,7000)
                self.assertEqual(conn.execute("SELECT count(*) FROM works WHERE id LIKE 'metacritic:%' AND (score<70 OR votes<10)").fetchone()[0],0)
                proof=conn.execute("SELECT evidence FROM works WHERE id='metacritic:baldurs-gate-3'").fetchone()[0]
                self.assertEqual(json.loads(proof)[0]['canonical'],'steam:1086940')
            results=catalog.search({'type':['game'],'criterion':['award'],'min_score':['90']})
            self.assertTrue(any(i['title']=="Baldur's Gate 3" for i in results['items']))
            with catalog.connect() as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM works WHERE id LIKE 'metacritic:%'").fetchone()[0],count)

if __name__=='__main__':unittest.main()
