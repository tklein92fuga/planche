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
        for kind in ('film','tv','book','game'):
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

    def test_no_identical_sublists_in_any_format(self):
        for kind in ('all','film','tv','game','book'):
            groups=journeys.overview(kind)['groups'];seen=set();by_id={g['id']:g for g in groups}
            for g in groups:
                self.assertEqual(len(g['members']),len(set(g['members'])))
                if g['kind']=='sublist':
                    signature=tuple(sorted(g['members']))
                    self.assertNotIn(signature,seen,(kind,g['id']))
                    seen.add(signature)
                else:
                    self.assertTrue(g['children'])
                    self.assertEqual(set(g['members']),{i for c in g['children'] for i in by_id[c]['members']})
                if g['parent']:self.assertIn(g['parent'],by_id)

    def test_duplicate_removal_preserves_overlap_and_editorial_selection(self):
        works={i:dict(id=i,votes=0) for i in 'abcd'}
        def leaf(ident,members,**extra):return dict(id=ident,kind='sublist',meta='m',parent='m',members=list(members),**extra)
        groups=[leaf('auto','cba',facet='genre'),leaf('editorial','abc'),leaf('different','bcd'),dict(id='m',kind='meta',parent='',children=['auto','editorial','different'],members=list('abcd'))]
        cleaned,removed=journeys.deduplicate(groups,works)
        self.assertEqual(removed,{'auto':'editorial'})
        self.assertEqual({g['id'] for g in cleaned},{'editorial','different','m'})
        self.assertEqual(cleaned[-1]['members'],list('abcd'))
        self.assertEqual(groups[-1]['children'],['auto','editorial','different'])

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
