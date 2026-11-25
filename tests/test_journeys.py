"""Run with python3 -m unittest discover -s tests from the project directory."""
import unittest
import journeys

class JourneysTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=journeys.overview()
        cls.groups={g['id']:g for g in cls.data['groups']}

    def test_full_tree_and_parentage(self):
        self.assertGreater(len(self.groups),0)
        self.assertEqual(sum(g['kind']=='sublist' for g in self.groups.values()),self.data['coverage']['sublists'])
        self.assertTrue(all(g['total']>=3 for g in self.groups.values()))
        self.assertIn('fantasy',self.groups)
        self.assertIn('action',self.groups)
        carpenter=self.groups['horreur/john-carpenter']
        self.assertEqual(carpenter['parent'],'horreur')
        self.assertGreaterEqual(carpenter['total'],3)
        self.assertTrue(all(i['type']=='film' for i in carpenter['items']))
        self.assertFalse(any('/format-' in g['id'] for g in self.groups.values()))
        self.assertEqual(self.groups['fantasy/terre-du-milieu-seigneur-des-anneaux']['total'],3)
        self.assertTrue(all(self.groups[i]['kind'] in ('sublist','group') for i in self.groups['fantasy']['children']))
        for g in self.groups.values():
            if g['parent']:self.assertIn(g['parent'],self.groups)
        self.assertEqual(self.groups['science-fiction/cyberpunk']['parent'],'science-fiction')
        for g in self.groups.values():
            if g.get('children'):
                members=set(g.get('directMembers',[]))|{i for child in g['children'] for i in self.groups[child]['members']}
                self.assertEqual(set(g['members']),members)
                self.assertEqual(g['total'],len(members))

    def test_no_empty_completion(self):
        for g in self.groups.values():
            if not g['total']:self.assertFalse(g['ready'])
        self.assertTrue(self.groups['science-fiction']['ready'])
        self.assertTrue(all(g['total']>=3 for g in self.groups.values()))

    def test_format_projection_and_historical_membership(self):
        all_world_war=self.groups['guerres-et-conflits/seconde-guerre-mondiale']
        self.assertGreaterEqual(all_world_war['total'],3)
        self.assertTrue(all(i['type']=='film' for i in all_world_war['items']))
        original=list(self.groups['science-fiction/cyberpunk']['members'])
        for kind in ('film','book','game'):
            data=journeys.overview(kind)
            for g in data['groups']:
                self.assertGreaterEqual(g['total'],3)
                if g['kind']!='sublist':self.assertTrue(g['children'])
                self.assertTrue(all(i['type']==kind for i in g['items']))
            g=data['groups'][0]
            detail=journeys.detail(g['id'],1,kind)
            self.assertEqual(detail['total'],g['total'])
            self.assertTrue(all(i['type']==kind for i in detail['items']))
        self.assertEqual(self.groups['science-fiction/cyberpunk']['members'],original)

    def test_metadata_sublist_evidence_and_deduplication(self):
        generated=[g for g in self.groups.values() if g.get('facet')]
        self.assertGreater(len(generated),100)
        seen=set()
        for g in generated:
            self.assertGreaterEqual(len(set(g['members'])),3)
            signature=(g['meta'],tuple(sorted(g['members'])))
            self.assertNotIn(signature,seen)
            seen.add(signature)
            if g['facet']=='decade':
                decade=int(g['criterion']['value'])
                for ident in g['members']:
                    self.assertEqual(int(journeys.CACHE['_works'][ident]['year'])//10*10,decade)
        fps=next(g for g in generated if g['meta']=='action' and g['facet']=='genre' and g['title'].startswith('FPS —'))
        self.assertTrue(all('fps' in journeys.CACHE['_works'][i]['genre'].lower() for i in fps['members']))
        self.assertTrue(any(g['facet']=='publisher' for g in generated))
        self.assertTrue(any(g['facet']=='developer' for g in generated))

    def test_sparse_awards_are_removed(self):
        self.assertNotIn('uvres-recompensees-par-des-prix/cinema-oscars/meilleur-film',self.groups)
        nominated=self.groups['uvres-nommees-et-selectionnees/oscars-nominations/meilleur-film']
        self.assertGreaterEqual(nominated['total'],3)
        goty=self.groups['uvres-recompensees-par-des-prix/jeux-video-the-game-awards/game-of-the-year']
        self.assertGreaterEqual(goty['total'],3)

    def test_pagination_and_cache_are_public(self):
        for _ in range(2):self.assertNotIn('_works',journeys.overview())
        cyber=journeys.detail('science-fiction/cyberpunk',1)
        self.assertEqual(len({i['id'] for i in cyber['items']}),cyber['total'])
        self.assertEqual(journeys.detail('science-fiction/cyberpunk',999)['items'],[])
        self.assertIsNone(journeys.detail('unknown',1))

if __name__=='__main__':unittest.main()
