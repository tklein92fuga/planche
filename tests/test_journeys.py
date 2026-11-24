"""Run with python3 -m unittest discover -s tests from the project directory."""
import unittest
import journeys

class JourneysTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=journeys.overview()
        cls.groups={g['id']:g for g in cls.data['groups']}

    def test_full_tree_and_parentage(self):
        self.assertEqual(sum(g['kind']=='meta' for g in self.groups.values()),53)
        self.assertEqual(sum(g['kind']=='sublist' for g in self.groups.values()),1098)
        self.assertEqual(self.groups['science-fiction/cyberpunk']['parent'],'science-fiction')
        for g in self.groups.values():
            if g.get('children'):
                members={i for child in g['children'] for i in self.groups[child]['members']}
                self.assertEqual(set(g['members']),members)
                self.assertEqual(g['total'],len(members))

    def test_no_empty_completion(self):
        for g in self.groups.values():
            if not g['total']:self.assertFalse(g['ready'])
        self.assertFalse(self.groups['science-fiction']['ready'])

    def test_awards_separate_nominees_and_winners(self):
        win=self.groups['uvres-recompensees-par-des-prix/cinema-oscars/meilleur-film']
        nominated=self.groups['uvres-nommees-et-selectionnees/oscars-nominations/meilleur-film']
        self.assertGreater(win['total'],0)
        self.assertGreater(nominated['total'],0)
        self.assertFalse(set(win['members']) & set(nominated['members']))

    def test_pagination_and_cache_are_public(self):
        for _ in range(2):self.assertNotIn('_works',journeys.overview())
        cyber=journeys.detail('science-fiction/cyberpunk',1)
        self.assertEqual(len({i['id'] for i in cyber['items']}),cyber['total'])
        self.assertEqual(journeys.detail('science-fiction/cyberpunk',999)['items'],[])
        self.assertIsNone(journeys.detail('unknown',1))

if __name__=='__main__':unittest.main()
