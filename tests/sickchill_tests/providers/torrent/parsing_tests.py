"""
Test Provider Result Parsing
When recording new cassettes:
    Delete the cassette yml file with the same base filename as this file in the cassettes dir next to this file
    Be sure to adjust the self.search_strings so they return results. They must be identical to search strings generated by SickChill
"""

import re
import sys
import unittest
from functools import wraps

import mock
import validators
from vcr_unittest import VCRTestCase

import sickchill.oldbeard.providers
from sickchill import movies, settings

settings.CPU_PRESET = 'NORMAL'


disabled_provider_tests = {
    # ???
    'Cpasbien': ['test_rss_search', 'test_episode_search', 'test_season_search'],
    'SkyTorrents': ['test_rss_search', 'test_episode_search', 'test_season_search'],
    # api_maintenance still
    'TorrentProject': ['test_rss_search', 'test_episode_search', 'test_season_search', 'test_cache_update', 'test_result_values'],
    # Have to trick it into thinking is an anime search, and add string overrides
    'TokyoToshokan': ['test_rss_search', 'test_episode_search', 'test_season_search'],
    'LimeTorrents': ['test_rss_search', 'test_episode_search', 'test_season_search'],
    'Torrentz': ['test_rss_search', 'test_episode_search', 'test_season_search', 'test_cache_update', 'test_result_values'],
    'ThePirateBay': ['test_rss_search', 'test_episode_search', 'test_season_search', 'test_cache_update', 'test_result_values'],
    'EZTV': ['test_rss_search', 'test_episode_search', 'test_season_search', 'test_cache_update', 'test_result_values'],
    'Rarbg': ['test_season_search']
}

test_string_overrides = {
    'Cpasbien': {'Episode': ['The 100 S07E08'], 'Season': ['The 100 S06']},
    'Torrent9': {'Episode': ['The 100 S07E08'], 'Season': ['The 100 S06']},
    'Nyaa': {'Episode': ['Fairy Tail S2'], 'Season': ['Fairy Tail S2']},
    'TokyoToshokan': {'Episode': ['Fairy Tail S2'], 'Season': ['Fairy Tail S2']},
    'HorribleSubs': {'Episode': ['Fairy Tail S2'], 'Season': ['Fairy Tail S2']},
    'Demonoid': {'Episode': ['Star Trek Picard S01E04'], 'Season': ['Locke and Key 2020 S01']},
    'ilCorsaroNero': {'Episode': ['The 100 S06E02']},
    'Rarbg': {'Season': ['The 100 S06']},
}

magnet_regex = re.compile(r'magnet:\?xt=urn:btih:\w{32,40}(:?&dn=[\w. %+-]+)*(:?&tr=(:?tcp|https?|udp)[\w%. +-]+)*')


def override_log(msg, *args, **kwargs):
    """Override the SickChill logger so we can see the debug output from providers"""
    _ = args, kwargs
    print(msg)


class BaseParser(type):

    class TestCase(VCRTestCase):
        provider = None

        def __init__(self, test):
            """Initialize the test suite"""
            super().__init__(test)

            self.provider.session.verify = False

            self.provider.username = self.username
            self.provider.password = self.password
            settings.movie_list = movies.MoviesList()

        @property
        def username(self):
            # TODO: Make this read usernames from somewhere
            return ''

        @property
        def password(self):
            # TODO: Make this read passwords from somewhere
            return ''

        def search_strings(self, mode):
            _search_strings = {
                'RSS': [''],
                'Episode': ['The 100 S07E08'],
                'Season': ['Game of Thrones S08'],
                'Movie': ['Black Panther 2018']
            }
            _search_strings.update(self.provider.cache.search_params)
            _search_strings.update(test_string_overrides.get(self.provider.name, {}))
            return {mode: _search_strings[mode]}

        def magic_skip(func):  # pylint:disable=no-self-argument
            @wraps(func)
            def magic(self, *args, **kwargs):
                if func.__name__ in disabled_provider_tests.get(self.provider.name, []):
                    self.skipTest('Test is programmatically disabled for provider {}'.format(self.provider.name))
                func(self, *args, **kwargs)
            return magic

        def _get_vcr_kwargs(self):
            """Don't allow the suite to write to cassettes unless we say so"""
            return {'record_mode': 'new_episodes'}

        def _get_cassette_name(self):
            """Returns the filename to use for the cassette"""
            return self.provider.get_id() + '.yaml'

        def shortDescription(self):
            if self._testMethodDoc:
                return self._testMethodDoc.replace('the provider', self.provider.name)
            return None

        @magic_skip
        def test_rss_search(self):
            """Check that the provider parses rss search results"""
            with mock.patch('sickchill.settings.SSL_VERIFY', 'ilcorsaronero' not in self.provider.name.lower()):
                results = self.provider.search(self.search_strings('RSS'))

            if self.provider.enable_daily:
                self.assertTrue(self.cassette.requests)
                self.assertTrue(results, self.cassette.requests[-1].url)
                self.assertTrue(len(self.cassette))

        @magic_skip
        def test_episode_search(self):
            """Check that the provider parses episode search results"""
            with mock.patch('sickchill.settings.SSL_VERIFY', 'ilcorsaronero' not in self.provider.name.lower()):
                results = self.provider.search(self.search_strings('Episode'))

            self.assertTrue(self.cassette.requests)
            self.assertTrue(results, results)
            self.assertTrue(results, (r.url for r in self.cassette.requests))
            self.assertTrue(len(self.cassette))

        @magic_skip
        def test_season_search(self):
            """Check that the provider parses season search results"""
            with mock.patch('sickchill.settings.SSL_VERIFY', 'ilcorsaronero' not in self.provider.name.lower()):
                results = self.provider.search(self.search_strings('Season'))

            self.assertTrue(self.cassette.requests)
            self.assertTrue(results, self.cassette.requests[-1].url)
            self.assertTrue(len(self.cassette))

        @magic_skip
        def test_cache_update(self):
            """Check that the provider's cache parses rss search results"""
            with mock.patch('sickchill.settings.SSL_VERIFY', 'ilcorsaronero' not in self.provider.name.lower()):
                self.provider.cache.update_cache()

        @magic_skip
        def test_result_values(self):
            """Check that the provider returns results in proper format"""
            with mock.patch('sickchill.settings.SSL_VERIFY', 'ilcorsaronero' not in self.provider.name.lower()):
                results = self.provider.search(self.search_strings('Episode'))
            for result in results:
                self.assertIsInstance(result, dict)
                self.assertEqual(sorted(result), ['hash', 'leechers', 'link', 'seeders', 'size', 'title'])

                self.assertIsInstance(result['title'], str)
                self.assertIsInstance(result['link'], str)
                self.assertIsInstance(result['hash'], str)
                self.assertIsInstance(result['seeders'], int)
                self.assertIsInstance(result['leechers'], int)
                self.assertIsInstance(result['size'], int)

                self.assertTrue(len(result['title']))
                self.assertTrue(len(result['link']))
                self.assertTrue(len(result['hash']) in (0, 32, 40))
                self.assertTrue(result['seeders'] >= 0)
                self.assertTrue(result['leechers'] >= 0)

                self.assertTrue(result['size'] >= -1)

                if result['link'].startswith('magnet'):
                    self.assertTrue(magnet_regex.match(result['link']))
                else:
                    self.assertTrue(validators.url(result['link']), result['link'])

                self.assertIsInstance(self.provider._get_size(result), int)
                self.assertTrue(all(self.provider._get_title_and_url(result)))
                self.assertTrue(self.provider._get_size(result))

            @unittest.skip('Not yet implemented')
            def test_season_search_strings_format(self):
                """Check format of the provider's season search strings"""
                pass

            @unittest.skip('Not yet implemented')
            def test_episode_search_strings_format(self):
                """Check format of the provider's season search strings"""
                pass


def generate_test_cases():
    """
    Auto Generate TestCases from providers and add them to globals()
    """
    for p in sickchill.oldbeard.providers.__all__:
        provider = sickchill.oldbeard.providers.getProviderModule(p).Provider()
        if provider.can_backlog and provider.provider_type == 'torrent' and provider.public:
            generated_class = type(str(provider.name), (BaseParser.TestCase,), {'provider': provider})
            globals()[generated_class.__name__] = generated_class
            del generated_class


generate_test_cases()

if __name__ == '__main__':
    import inspect
    print('=====> Testing %s', __file__)

    def override_log(msg, *args, **kwargs):
        """Override the SickChill logger so we can see the debug output from providers"""
        _ = args, kwargs
        print(msg)

    sickchill.logger.info = override_log
    sickchill.logger.debug = override_log
    sickchill.logger.error = override_log
    sickchill.logger.warning = override_log

    suite = unittest.TestSuite()
    members = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    for _, provider_test_class in members:
        if provider_test_class not in (BaseParser, BaseParser.TestCase):
            suite.addTest(unittest.TestLoader().loadTestsFromTestCase(provider_test_class))

    unittest.TextTestRunner(verbosity=3).run(suite)
