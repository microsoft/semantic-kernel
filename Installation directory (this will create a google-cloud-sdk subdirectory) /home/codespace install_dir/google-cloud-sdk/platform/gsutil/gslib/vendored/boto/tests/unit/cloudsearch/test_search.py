#!/usr/bin env python

from tests.compat import mock, unittest
from httpretty import HTTPretty

import json
import requests

from boto.cloudsearch.search import SearchConnection, SearchServiceException
from boto.compat import six, map

HOSTNAME = "search-demo-userdomain.us-east-1.cloudsearch.amazonaws.com"
FULL_URL = 'http://%s/2011-02-01/search' % HOSTNAME


class CloudSearchSearchBaseTest(unittest.TestCase):

    hits = [
        {
            'id': '12341',
            'title': 'Document 1',
        },
        {
            'id': '12342',
            'title': 'Document 2',
        },
        {
            'id': '12343',
            'title': 'Document 3',
        },
        {
            'id': '12344',
            'title': 'Document 4',
        },
        {
            'id': '12345',
            'title': 'Document 5',
        },
        {
            'id': '12346',
            'title': 'Document 6',
        },
        {
            'id': '12347',
            'title': 'Document 7',
        },
    ]

    content_type = "text/xml"
    response_status = 200

    def get_args(self, requestline):
        (_, request, _) = requestline.split(b" ")
        (_, request) = request.split(b"?", 1)
        args = six.moves.urllib.parse.parse_qs(request)
        return args

    def setUp(self):
        HTTPretty.enable()
        body = self.response

        if not isinstance(body, bytes):
            body = json.dumps(body).encode('utf-8')

        HTTPretty.register_uri(HTTPretty.GET, FULL_URL,
                               body=body,
                               content_type=self.content_type,
                               status=self.response_status)

    def tearDown(self):
        HTTPretty.disable()

class CloudSearchSearchTest(CloudSearchSearchBaseTest):
    response = {
        'rank': '-text_relevance',
        'match-expr': "Test",
        'hits': {
            'found': 30,
            'start': 0,
            'hit': CloudSearchSearchBaseTest.hits
            },
        'info': {
            'rid': 'b7c167f6c2da6d93531b9a7b314ad030b3a74803b4b7797edb905ba5a6a08',
            'time-ms': 2,
            'cpu-time-ms': 0
        }

    }

    def test_cloudsearch_qsearch(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test')

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'q'], [b"Test"])
        self.assertEqual(args[b'start'], [b"0"])
        self.assertEqual(args[b'size'], [b"10"])

    def test_cloudsearch_bqsearch(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(bq="'Test'")

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'bq'], [b"'Test'"])

    def test_cloudsearch_search_details(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', size=50, start=20)

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'q'], [b"Test"])
        self.assertEqual(args[b'size'], [b"50"])
        self.assertEqual(args[b'start'], [b"20"])

    def test_cloudsearch_facet_single(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', facet=["Author"])

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'facet'], [b"Author"])

    def test_cloudsearch_facet_multiple(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', facet=["author", "cat"])

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'facet'], [b"author,cat"])

    def test_cloudsearch_facet_constraint_single(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(
            q='Test',
            facet_constraints={'author': "'John Smith','Mark Smith'"})

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'facet-author-constraints'],
                         [b"'John Smith','Mark Smith'"])

    def test_cloudsearch_facet_constraint_multiple(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(
            q='Test',
            facet_constraints={'author': "'John Smith','Mark Smith'",
                               'category': "'News','Reviews'"})

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'facet-author-constraints'],
                         [b"'John Smith','Mark Smith'"])
        self.assertEqual(args[b'facet-category-constraints'],
                         [b"'News','Reviews'"])

    def test_cloudsearch_facet_sort_single(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', facet_sort={'author': 'alpha'})

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'facet-author-sort'], [b'alpha'])

    def test_cloudsearch_facet_sort_multiple(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', facet_sort={'author': 'alpha',
                                            'cat': 'count'})

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'facet-author-sort'], [b'alpha'])
        self.assertEqual(args[b'facet-cat-sort'], [b'count'])

    def test_cloudsearch_top_n_single(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', facet_top_n={'author': 5})

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'facet-author-top-n'], [b'5'])

    def test_cloudsearch_top_n_multiple(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', facet_top_n={'author': 5, 'cat': 10})

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'facet-author-top-n'], [b'5'])
        self.assertEqual(args[b'facet-cat-top-n'], [b'10'])

    def test_cloudsearch_rank_single(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', rank=["date"])

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'rank'], [b'date'])

    def test_cloudsearch_rank_multiple(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', rank=["date", "score"])

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'rank'], [b'date,score'])

    def test_cloudsearch_result_fields_single(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', return_fields=['author'])

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'return-fields'], [b'author'])

    def test_cloudsearch_result_fields_multiple(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', return_fields=['author', 'title'])

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b'return-fields'], [b'author,title'])

    def test_cloudsearch_t_field_single(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', t={'year': '2001..2007'})

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b't-year'], [b'2001..2007'])

    def test_cloudsearch_t_field_multiple(self):
        search = SearchConnection(endpoint=HOSTNAME)

        search.search(q='Test', t={'year': '2001..2007', 'score': '10..50'})

        args = self.get_args(HTTPretty.last_request.raw_requestline)

        self.assertEqual(args[b't-year'], [b'2001..2007'])
        self.assertEqual(args[b't-score'], [b'10..50'])

    def test_cloudsearch_results_meta(self):
        """Check returned metadata is parsed correctly"""
        search = SearchConnection(endpoint=HOSTNAME)

        results = search.search(q='Test')

        # These rely on the default response which is fed into HTTPretty
        self.assertEqual(results.rank, "-text_relevance")
        self.assertEqual(results.match_expression, "Test")

    def test_cloudsearch_results_info(self):
        """Check num_pages_needed is calculated correctly"""
        search = SearchConnection(endpoint=HOSTNAME)

        results = search.search(q='Test')

        # This relies on the default response which is fed into HTTPretty
        self.assertEqual(results.num_pages_needed, 3.0)

    def test_cloudsearch_results_matched(self):
        """
        Check that information objects are passed back through the API
        correctly.
        """
        search = SearchConnection(endpoint=HOSTNAME)
        query = search.build_query(q='Test')

        results = search(query)

        self.assertEqual(results.search_service, search)
        self.assertEqual(results.query, query)

    def test_cloudsearch_results_hits(self):
        """Check that documents are parsed properly from AWS"""
        search = SearchConnection(endpoint=HOSTNAME)

        results = search.search(q='Test')

        hits = list(map(lambda x: x['id'], results.docs))

        # This relies on the default response which is fed into HTTPretty
        self.assertEqual(
            hits, ["12341", "12342", "12343", "12344",
                   "12345", "12346", "12347"])

    def test_cloudsearch_results_iterator(self):
        """Check the results iterator"""
        search = SearchConnection(endpoint=HOSTNAME)

        results = search.search(q='Test')
        results_correct = iter(["12341", "12342", "12343", "12344",
                                "12345", "12346", "12347"])
        for x in results:
            self.assertEqual(x['id'], next(results_correct))


    def test_cloudsearch_results_internal_consistancy(self):
        """Check the documents length matches the iterator details"""
        search = SearchConnection(endpoint=HOSTNAME)

        results = search.search(q='Test')

        self.assertEqual(len(results), len(results.docs))

    def test_cloudsearch_search_nextpage(self):
        """Check next page query is correct"""
        search = SearchConnection(endpoint=HOSTNAME)
        query1 = search.build_query(q='Test')
        query2 = search.build_query(q='Test')

        results = search(query2)

        self.assertEqual(results.next_page().query.start,
                         query1.start + query1.size)
        self.assertEqual(query1.q, query2.q)

class CloudSearchSearchFacetTest(CloudSearchSearchBaseTest):
    response = {
        'rank': '-text_relevance',
        'match-expr': "Test",
        'hits': {
            'found': 30,
            'start': 0,
            'hit': CloudSearchSearchBaseTest.hits
            },
        'info': {
            'rid': 'b7c167f6c2da6d93531b9a7b314ad030b3a74803b4b7797edb905ba5a6a08',
            'time-ms': 2,
            'cpu-time-ms': 0
        },
        'facets': {
            'tags': {},
            'animals': {'constraints': [{'count': '2', 'value': 'fish'}, {'count': '1', 'value': 'lions'}]},
        }
    }

    def test_cloudsearch_search_facets(self):
        #self.response['facets'] = {'tags': {}}

        search = SearchConnection(endpoint=HOSTNAME)

        results = search.search(q='Test', facet=['tags'])

        self.assertTrue('tags' not in results.facets)
        self.assertEqual(results.facets['animals'], {u'lions': u'1', u'fish': u'2'})


class CloudSearchNonJsonTest(CloudSearchSearchBaseTest):
    response = b'<html><body><h1>500 Internal Server Error</h1></body></html>'
    response_status = 500
    content_type = 'text/xml'

    def test_response(self):
        search = SearchConnection(endpoint=HOSTNAME)

        with self.assertRaises(SearchServiceException):
            search.search(q='Test')


class CloudSearchUnauthorizedTest(CloudSearchSearchBaseTest):
    response = b'<html><body><h1>403 Forbidden</h1>foo bar baz</body></html>'
    response_status = 403
    content_type = 'text/html'

    def test_response(self):
        search = SearchConnection(endpoint=HOSTNAME)

        with self.assertRaisesRegexp(SearchServiceException, 'foo bar baz'):
            search.search(q='Test')


class FakeResponse(object):
    status_code = 405
    content = b''


class CloudSearchConnectionTest(unittest.TestCase):
    cloudsearch = True

    def setUp(self):
        super(CloudSearchConnectionTest, self).setUp()
        self.conn = SearchConnection(
            endpoint='test-domain.cloudsearch.amazonaws.com'
        )

    def test_expose_additional_error_info(self):
        mpo = mock.patch.object
        fake = FakeResponse()
        fake.content = b'Nopenopenope'

        # First, in the case of a non-JSON, non-403 error.
        with mpo(requests, 'get', return_value=fake) as mock_request:
            with self.assertRaises(SearchServiceException) as cm:
                self.conn.search(q='not_gonna_happen')

            self.assertTrue('non-json response' in str(cm.exception))
            self.assertTrue('Nopenopenope' in str(cm.exception))

        # Then with JSON & an 'error' key within.
        fake.content = json.dumps({
            'error': "Something went wrong. Oops."
        }).encode('utf-8')

        with mpo(requests, 'get', return_value=fake) as mock_request:
            with self.assertRaises(SearchServiceException) as cm:
                self.conn.search(q='no_luck_here')

            self.assertTrue('Unknown error' in str(cm.exception))
            self.assertTrue('went wrong. Oops' in str(cm.exception))
