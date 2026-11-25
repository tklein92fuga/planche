import json
import unittest
import enrich_metadata

class CompanyMetadataTest(unittest.TestCase):
    def test_roles_and_franchises_are_explicit(self):
        product=dict(slug='example',title='Example',criticScoreSummary={},production=dict(companies=[dict(typeName='Developer',name='Studio X'),dict(typeName='Publisher',name='Publisher X'),dict(typeName='Producer',name='Not a publisher')]),gameTaxonomy=dict(franchises=[dict(name='Saga X')]))
        pool=[]
        def encode(v):
            n=len(pool);pool.append(None)
            pool[n]={k:encode(i) for k,i in v.items()} if isinstance(v,dict) else [encode(i) for i in v] if isinstance(v,list) else v
            return n
        encode(product)
        html='<script id="__NUXT_DATA__">'+json.dumps(pool)+'</script>'
        record=enrich_metadata.parse(html,'metacritic:example')
        self.assertEqual(record['developers'],['Studio X'])
        self.assertEqual(record['publishers'],['Publisher X'])
        self.assertEqual(record['franchises'],['Saga X'])
        with self.assertRaises(ValueError):enrich_metadata.parse(html,'metacritic:different-work')
