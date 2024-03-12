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

import boto
from boto.compat import json
from boto.cloudsearch.optionstatus import OptionStatus
from boto.cloudsearch.optionstatus import IndexFieldStatus
from boto.cloudsearch.optionstatus import ServicePoliciesStatus
from boto.cloudsearch.optionstatus import RankExpressionStatus
from boto.cloudsearch.document import DocumentServiceConnection
from boto.cloudsearch.search import SearchConnection

def handle_bool(value):
    if value in [True, 'true', 'True', 'TRUE', 1]:
        return True
    return False


class Domain(object):
    """
    A Cloudsearch domain.

    :ivar name: The name of the domain.

    :ivar id: The internally generated unique identifier for the domain.

    :ivar created: A boolean which is True if the domain is
        created. It can take several minutes to initialize a domain
        when CreateDomain is called. Newly created search domains are
        returned with a False value for Created until domain creation
        is complete

    :ivar deleted: A boolean which is True if the search domain has
        been deleted. The system must clean up resources dedicated to
        the search domain when delete is called. Newly deleted
        search domains are returned from list_domains with a True
        value for deleted for several minutes until resource cleanup
        is complete.

    :ivar processing: True if processing is being done to activate the
        current domain configuration.

    :ivar num_searchable_docs: The number of documents that have been
        submittted to the domain and indexed.

    :ivar requires_index_document: True if index_documents needs to be
        called to activate the current domain configuration.

    :ivar search_instance_count: The number of search instances that are
        available to process search requests.

    :ivar search_instance_type: The instance type that is being used to
        process search requests.

    :ivar search_partition_count: The number of partitions across which
        the search index is spread.
    """

    def __init__(self, layer1, data):
        self.layer1 = layer1
        self.update_from_data(data)

    def update_from_data(self, data):
        self.created = data['created']
        self.deleted = data['deleted']
        self.processing = data['processing']
        self.requires_index_documents = data['requires_index_documents']
        self.domain_id = data['domain_id']
        self.domain_name = data['domain_name']
        self.num_searchable_docs = data['num_searchable_docs']
        self.search_instance_count = data['search_instance_count']
        self.search_instance_type = data.get('search_instance_type', None)
        self.search_partition_count = data['search_partition_count']
        self._doc_service = data['doc_service']
        self._search_service = data['search_service']

    @property
    def doc_service_arn(self):
        return self._doc_service['arn']

    @property
    def doc_service_endpoint(self):
        return self._doc_service['endpoint']

    @property
    def search_service_arn(self):
        return self._search_service['arn']

    @property
    def search_service_endpoint(self):
        return self._search_service['endpoint']

    @property
    def created(self):
        return self._created

    @created.setter
    def created(self, value):
        self._created = handle_bool(value)

    @property
    def deleted(self):
        return self._deleted

    @deleted.setter
    def deleted(self, value):
        self._deleted = handle_bool(value)

    @property
    def processing(self):
        return self._processing

    @processing.setter
    def processing(self, value):
        self._processing = handle_bool(value)

    @property
    def requires_index_documents(self):
        return self._requires_index_documents

    @requires_index_documents.setter
    def requires_index_documents(self, value):
        self._requires_index_documents = handle_bool(value)

    @property
    def search_partition_count(self):
        return self._search_partition_count

    @search_partition_count.setter
    def search_partition_count(self, value):
        self._search_partition_count = int(value)

    @property
    def search_instance_count(self):
        return self._search_instance_count

    @search_instance_count.setter
    def search_instance_count(self, value):
        self._search_instance_count = int(value)

    @property
    def num_searchable_docs(self):
        return self._num_searchable_docs

    @num_searchable_docs.setter
    def num_searchable_docs(self, value):
        self._num_searchable_docs = int(value)

    @property
    def name(self):
        return self.domain_name

    @property
    def id(self):
        return self.domain_id

    def delete(self):
        """
        Delete this domain and all index data associated with it.
        """
        return self.layer1.delete_domain(self.name)

    def get_stemming(self):
        """
        Return a :class:`boto.cloudsearch.option.OptionStatus` object
        representing the currently defined stemming options for
        the domain.
        """
        return OptionStatus(self, None,
                            self.layer1.describe_stemming_options,
                            self.layer1.update_stemming_options)

    def get_stopwords(self):
        """
        Return a :class:`boto.cloudsearch.option.OptionStatus` object
        representing the currently defined stopword options for
        the domain.
        """
        return OptionStatus(self, None,
                            self.layer1.describe_stopword_options,
                            self.layer1.update_stopword_options)

    def get_synonyms(self):
        """
        Return a :class:`boto.cloudsearch.option.OptionStatus` object
        representing the currently defined synonym options for
        the domain.
        """
        return OptionStatus(self, None,
                            self.layer1.describe_synonym_options,
                            self.layer1.update_synonym_options)

    def get_access_policies(self):
        """
        Return a :class:`boto.cloudsearch.option.OptionStatus` object
        representing the currently defined access policies for
        the domain.
        """
        return ServicePoliciesStatus(self, None,
                                     self.layer1.describe_service_access_policies,
                                     self.layer1.update_service_access_policies)

    def index_documents(self):
        """
        Tells the search domain to start indexing its documents using
        the latest text processing options and IndexFields. This
        operation must be invoked to make options whose OptionStatus
        has OptioState of RequiresIndexDocuments visible in search
        results.
        """
        self.layer1.index_documents(self.name)

    def get_index_fields(self, field_names=None):
        """
        Return a list of index fields defined for this domain.
        """
        data = self.layer1.describe_index_fields(self.name, field_names)
        return [IndexFieldStatus(self, d) for d in data]

    def create_index_field(self, field_name, field_type,
        default='', facet=False, result=False, searchable=False,
        source_attributes=[]):
        """
        Defines an ``IndexField``, either replacing an existing
        definition or creating a new one.

        :type field_name: string
        :param field_name: The name of a field in the search index.

        :type field_type: string
        :param field_type: The type of field.  Valid values are
            uint | literal | text

        :type default: string or int
        :param default: The default value for the field.  If the
            field is of type ``uint`` this should be an integer value.
            Otherwise, it's a string.

        :type facet: bool
        :param facet: A boolean to indicate whether facets
            are enabled for this field or not.  Does not apply to
            fields of type ``uint``.

        :type results: bool
        :param results: A boolean to indicate whether values
            of this field can be returned in search results or
            used in ranking.  Does not apply to fields of type ``uint``.

        :type searchable: bool
        :param searchable: A boolean to indicate whether search
            is enabled for this field or not.  Applies only to fields
            of type ``literal``.

        :type source_attributes: list of dicts
        :param source_attributes: An optional list of dicts that
            provide information about attributes for this index field.
            A maximum of 20 source attributes can be configured for
            each index field.

            Each item in the list is a dict with the following keys:

            * data_copy - The value is a dict with the following keys:
                * default - Optional default value if the source attribute
                    is not specified in a document.
                * name - The name of the document source field to add
                    to this ``IndexField``.
            * data_function - Identifies the transformation to apply
                when copying data from a source attribute.
            * data_map - The value is a dict with the following keys:
                * cases - A dict that translates source field values
                    to custom values.
                * default - An optional default value to use if the
                    source attribute is not specified in a document.
                * name - the name of the document source field to add
                    to this ``IndexField``
            * data_trim_title - Trims common title words from a source
                document attribute when populating an ``IndexField``.
                This can be used to create an ``IndexField`` you can
                use for sorting.  The value is a dict with the following
                fields:
                * default - An optional default value.
                * language - an IETF RFC 4646 language code.
                * separator - The separator that follows the text to trim.
                * name - The name of the document source field to add.

        :raises: BaseException, InternalException, LimitExceededException,
            InvalidTypeException, ResourceNotFoundException
        """
        data = self.layer1.define_index_field(self.name, field_name,
                                              field_type, default=default,
                                              facet=facet, result=result,
                                              searchable=searchable,
                                              source_attributes=source_attributes)
        return IndexFieldStatus(self, data,
                                self.layer1.describe_index_fields)

    def get_rank_expressions(self, rank_names=None):
        """
        Return a list of rank expressions defined for this domain.
        """
        fn = self.layer1.describe_rank_expressions
        data = fn(self.name, rank_names)
        return [RankExpressionStatus(self, d, fn) for d in data]

    def create_rank_expression(self, name, expression):
        """
        Create a new rank expression.
        
        :type rank_name: string
        :param rank_name: The name of an expression computed for ranking
            while processing a search request.

        :type rank_expression: string
        :param rank_expression: The expression to evaluate for ranking
            or thresholding while processing a search request. The
            RankExpression syntax is based on JavaScript expressions
            and supports:

            * Integer, floating point, hex and octal literals
            * Shortcut evaluation of logical operators such that an
                expression a || b evaluates to the value a if a is
                true without evaluting b at all
            * JavaScript order of precedence for operators
            * Arithmetic operators: + - * / %
            * Boolean operators (including the ternary operator)
            * Bitwise operators
            * Comparison operators
            * Common mathematic functions: abs ceil erf exp floor
                lgamma ln log2 log10 max min sqrt pow
            * Trigonometric library functions: acosh acos asinh asin
                atanh atan cosh cos sinh sin tanh tan
            * Random generation of a number between 0 and 1: rand
            * Current time in epoch: time
            * The min max functions that operate on a variable argument list

            Intermediate results are calculated as double precision
            floating point values. The final return value of a
            RankExpression is automatically converted from floating
            point to a 32-bit unsigned integer by rounding to the
            nearest integer, with a natural floor of 0 and a ceiling
            of max(uint32_t), 4294967295. Mathematical errors such as
            dividing by 0 will fail during evaluation and return a
            value of 0.

            The source data for a RankExpression can be the name of an
            IndexField of type uint, another RankExpression or the
            reserved name text_relevance. The text_relevance source is
            defined to return an integer from 0 to 1000 (inclusive) to
            indicate how relevant a document is to the search request,
            taking into account repetition of search terms in the
            document and proximity of search terms to each other in
            each matching IndexField in the document.

            For more information about using rank expressions to
            customize ranking, see the Amazon CloudSearch Developer
            Guide.

        :raises: BaseException, InternalException, LimitExceededException,
            InvalidTypeException, ResourceNotFoundException
        """
        data = self.layer1.define_rank_expression(self.name, name, expression)
        return RankExpressionStatus(self, data,
                                    self.layer1.describe_rank_expressions)

    def get_document_service(self):
        return DocumentServiceConnection(domain=self)

    def get_search_service(self):
        return SearchConnection(domain=self)

    def __repr__(self):
        return '<Domain: %s>' % self.domain_name

