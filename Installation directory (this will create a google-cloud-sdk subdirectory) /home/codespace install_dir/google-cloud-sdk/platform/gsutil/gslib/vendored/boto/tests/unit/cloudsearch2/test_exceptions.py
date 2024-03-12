from boto.compat import json
from tests.compat import mock, unittest

from tests.unit.cloudsearch2.test_search import HOSTNAME, \
                                                CloudSearchSearchBaseTest
from boto.cloudsearch2.search import SearchConnection, SearchServiceException


def fake_loads_value_error(content, *args, **kwargs):
    """Callable to generate a fake ValueError"""
    raise ValueError("HAHAHA! Totally not simplejson & you gave me bad JSON.")


def fake_loads_json_error(content, *args, **kwargs):
    """Callable to generate a fake JSONDecodeError"""
    raise json.JSONDecodeError('Using simplejson & you gave me bad JSON.',
                               '', 0)


class CloudSearchJSONExceptionTest(CloudSearchSearchBaseTest):
    response = b'{}'

    def test_no_simplejson_value_error(self):
        with mock.patch.object(json, 'loads', fake_loads_value_error):
            search = SearchConnection(endpoint=HOSTNAME)

            with self.assertRaisesRegexp(SearchServiceException, 'non-json'):
                search.search(q='test')

    @unittest.skipUnless(hasattr(json, 'JSONDecodeError'),
                         'requires simplejson')
    def test_simplejson_jsondecodeerror(self):
        with mock.patch.object(json, 'loads', fake_loads_json_error):
            search = SearchConnection(endpoint=HOSTNAME)

            with self.assertRaisesRegexp(SearchServiceException, 'non-json'):
                search.search(q='test')
