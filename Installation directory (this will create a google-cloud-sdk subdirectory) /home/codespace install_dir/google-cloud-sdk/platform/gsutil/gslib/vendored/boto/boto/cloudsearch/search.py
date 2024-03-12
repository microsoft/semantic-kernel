# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.
# All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
from math import ceil
from boto.compat import json, map, six
import requests


class SearchServiceException(Exception):
    pass


class CommitMismatchError(Exception):
    pass


class SearchResults(object):
    def __init__(self, **attrs):
        self.rid = attrs['info']['rid']
        # self.doc_coverage_pct = attrs['info']['doc-coverage-pct']
        self.cpu_time_ms = attrs['info']['cpu-time-ms']
        self.time_ms = attrs['info']['time-ms']
        self.hits = attrs['hits']['found']
        self.docs = attrs['hits']['hit']
        self.start = attrs['hits']['start']
        self.rank = attrs['rank']
        self.match_expression = attrs['match-expr']
        self.query = attrs['query']
        self.search_service = attrs['search_service']

        self.facets = {}
        if 'facets' in attrs:
            for (facet, values) in attrs['facets'].items():
                if 'constraints' in values:
                    self.facets[facet] = dict((k, v) for (k, v) in map(lambda x: (x['value'], x['count']), values['constraints']))

        self.num_pages_needed = ceil(self.hits / self.query.real_size)

    def __len__(self):
        return len(self.docs)

    def __iter__(self):
        return iter(self.docs)

    def next_page(self):
        """Call Cloudsearch to get the next page of search results

        :rtype: :class:`boto.cloudsearch.search.SearchResults`
        :return: the following page of search results
        """
        if self.query.page <= self.num_pages_needed:
            self.query.start += self.query.real_size
            self.query.page += 1
            return self.search_service(self.query)
        else:
            raise StopIteration


class Query(object):

    RESULTS_PER_PAGE = 500

    def __init__(self, q=None, bq=None, rank=None,
                 return_fields=None, size=10,
                 start=0, facet=None, facet_constraints=None,
                 facet_sort=None, facet_top_n=None, t=None):

        self.q = q
        self.bq = bq
        self.rank = rank or []
        self.return_fields = return_fields or []
        self.start = start
        self.facet = facet or []
        self.facet_constraints = facet_constraints or {}
        self.facet_sort = facet_sort or {}
        self.facet_top_n = facet_top_n or {}
        self.t = t or {}
        self.page = 0
        self.update_size(size)

    def update_size(self, new_size):
        self.size = new_size
        self.real_size = Query.RESULTS_PER_PAGE if (self.size >
            Query.RESULTS_PER_PAGE or self.size == 0) else self.size

    def to_params(self):
        """Transform search parameters from instance properties to a dictionary

        :rtype: dict
        :return: search parameters
        """
        params = {'start': self.start, 'size': self.real_size}

        if self.q:
            params['q'] = self.q

        if self.bq:
            params['bq'] = self.bq

        if self.rank:
            params['rank'] = ','.join(self.rank)

        if self.return_fields:
            params['return-fields'] = ','.join(self.return_fields)

        if self.facet:
            params['facet'] = ','.join(self.facet)

        if self.facet_constraints:
            for k, v in six.iteritems(self.facet_constraints):
                params['facet-%s-constraints' % k] = v

        if self.facet_sort:
            for k, v in six.iteritems(self.facet_sort):
                params['facet-%s-sort' % k] = v

        if self.facet_top_n:
            for k, v in six.iteritems(self.facet_top_n):
                params['facet-%s-top-n' % k] = v

        if self.t:
            for k, v in six.iteritems(self.t):
                params['t-%s' % k] = v
        return params


class SearchConnection(object):

    def __init__(self, domain=None, endpoint=None):
        self.domain = domain
        self.endpoint = endpoint
        if not endpoint:
            self.endpoint = domain.search_service_endpoint

    def build_query(self, q=None, bq=None, rank=None, return_fields=None,
                    size=10, start=0, facet=None, facet_constraints=None,
                    facet_sort=None, facet_top_n=None, t=None):
        return Query(q=q, bq=bq, rank=rank, return_fields=return_fields,
                     size=size, start=start, facet=facet,
                     facet_constraints=facet_constraints,
                     facet_sort=facet_sort, facet_top_n=facet_top_n, t=t)

    def search(self, q=None, bq=None, rank=None, return_fields=None,
               size=10, start=0, facet=None, facet_constraints=None,
               facet_sort=None, facet_top_n=None, t=None):
        """
        Send a query to CloudSearch

        Each search query should use at least the q or bq argument to specify
        the search parameter. The other options are used to specify the
        criteria of the search.

        :type q: string
        :param q: A string to search the default search fields for.

        :type bq: string
        :param bq: A string to perform a Boolean search. This can be used to
            create advanced searches.

        :type rank: List of strings
        :param rank: A list of fields or rank expressions used to order the
            search results. A field can be reversed by using the - operator.
            ``['-year', 'author']``

        :type return_fields: List of strings
        :param return_fields: A list of fields which should be returned by the
            search. If this field is not specified, only IDs will be returned.
            ``['headline']``

        :type size: int
        :param size: Number of search results to specify

        :type start: int
        :param start: Offset of the first search result to return (can be used
            for paging)

        :type facet: list
        :param facet: List of fields for which facets should be returned
            ``['colour', 'size']``

        :type facet_constraints: dict
        :param facet_constraints: Use to limit facets to specific values
            specified as comma-delimited strings in a Dictionary of facets
            ``{'colour': "'blue','white','red'", 'size': "big"}``

        :type facet_sort: dict
        :param facet_sort: Rules used to specify the order in which facet
            values should be returned. Allowed values are *alpha*, *count*,
            *max*, *sum*. Use *alpha* to sort alphabetical, and *count* to sort
            the facet by number of available result.
            ``{'color': 'alpha', 'size': 'count'}``

        :type facet_top_n: dict
        :param facet_top_n: Dictionary of facets and number of facets to
            return.
            ``{'colour': 2}``

        :type t: dict
        :param t: Specify ranges for specific fields
            ``{'year': '2000..2005'}``

        :rtype: :class:`boto.cloudsearch.search.SearchResults`
        :return: Returns the results of this search

        The following examples all assume we have indexed a set of documents
        with fields: *author*, *date*, *headline*

        A simple search will look for documents whose default text search
        fields will contain the search word exactly:

        >>> search(q='Tim') # Return documents with the word Tim in them (but not Timothy)

        A simple search with more keywords will return documents whose default
        text search fields contain the search strings together or separately.

        >>> search(q='Tim apple') # Will match "tim" and "apple"

        More complex searches require the boolean search operator.

        Wildcard searches can be used to search for any words that start with
        the search string.

        >>> search(bq="'Tim*'") # Return documents with words like Tim or Timothy)

        Search terms can also be combined. Allowed operators are "and", "or",
        "not", "field", "optional", "token", "phrase", or "filter"

        >>> search(bq="(and 'Tim' (field author 'John Smith'))")

        Facets allow you to show classification information about the search
        results. For example, you can retrieve the authors who have written
        about Tim:

        >>> search(q='Tim', facet=['Author'])

        With facet_constraints, facet_top_n and facet_sort more complicated
        constraints can be specified such as returning the top author out of
        John Smith and Mark Smith who have a document with the word Tim in it.

        >>> search(q='Tim',
        ...     facet=['Author'],
        ...     facet_constraints={'author': "'John Smith','Mark Smith'"},
        ...     facet=['author'],
        ...     facet_top_n={'author': 1},
        ...     facet_sort={'author': 'count'})
        """

        query = self.build_query(q=q, bq=bq, rank=rank,
                                 return_fields=return_fields,
                                 size=size, start=start, facet=facet,
                                 facet_constraints=facet_constraints,
                                 facet_sort=facet_sort,
                                 facet_top_n=facet_top_n, t=t)
        return self(query)

    def __call__(self, query):
        """Make a call to CloudSearch

        :type query: :class:`boto.cloudsearch.search.Query`
        :param query: A group of search criteria

        :rtype: :class:`boto.cloudsearch.search.SearchResults`
        :return: search results
        """
        url = "http://%s/2011-02-01/search" % (self.endpoint)
        params = query.to_params()

        r = requests.get(url, params=params)
        body = r.content.decode('utf-8')
        try:
            data = json.loads(body)
        except ValueError as e:
            if r.status_code == 403:
                msg = ''
                import re
                g = re.search('<html><body><h1>403 Forbidden</h1>([^<]+)<', body)
                try:
                    msg = ': %s' % (g.groups()[0].strip())
                except AttributeError:
                    pass
                raise SearchServiceException('Authentication error from Amazon%s' % msg)
            raise SearchServiceException("Got non-json response from Amazon. %s" % body, query)

        if 'messages' in data and 'error' in data:
            for m in data['messages']:
                if m['severity'] == 'fatal':
                    raise SearchServiceException("Error processing search %s "
                        "=> %s" % (params, m['message']), query)
        elif 'error' in data:
            raise SearchServiceException("Unknown error processing search %s"
                % json.dumps(data), query)

        data['query'] = query
        data['search_service'] = self

        return SearchResults(**data)

    def get_all_paged(self, query, per_page):
        """Get a generator to iterate over all pages of search results

        :type query: :class:`boto.cloudsearch.search.Query`
        :param query: A group of search criteria

        :type per_page: int
        :param per_page: Number of docs in each :class:`boto.cloudsearch.search.SearchResults` object.

        :rtype: generator
        :return: Generator containing :class:`boto.cloudsearch.search.SearchResults`
        """
        query.update_size(per_page)
        page = 0
        num_pages_needed = 0
        while page <= num_pages_needed:
            results = self(query)
            num_pages_needed = results.num_pages_needed
            yield results
            query.start += query.real_size
            page += 1

    def get_all_hits(self, query):
        """Get a generator to iterate over all search results

        Transparently handles the results paging from Cloudsearch
        search results so even if you have many thousands of results
        you can iterate over all results in a reasonably efficient
        manner.

        :type query: :class:`boto.cloudsearch.search.Query`
        :param query: A group of search criteria

        :rtype: generator
        :return: All docs matching query
        """
        page = 0
        num_pages_needed = 0
        while page <= num_pages_needed:
            results = self(query)
            num_pages_needed = results.num_pages_needed
            for doc in results:
                yield doc
            query.start += query.real_size
            page += 1

    def get_num_hits(self, query):
        """Return the total number of hits for query

        :type query: :class:`boto.cloudsearch.search.Query`
        :param query: a group of search criteria

        :rtype: int
        :return: Total number of hits for query
        """
        query.update_size(1)
        return self(query).hits



