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
        self.assertTrue(all(g['total']>=4 for g in self.groups.values()))
        self.assertIn('fantasy',self.groups)
        self.assertIn('action',self.groups)
        self.assertIn('fantasy/format-film',self.groups)
        self.assertTrue(all(self.groups[i]['kind']=='sublist' for i in self.groups['fantasy']['children']))
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
        self.assertTrue(all(g['total']>3 for g in self.groups.values()))

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
