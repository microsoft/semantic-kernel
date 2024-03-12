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

import boto
import boto.jsonresponse
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo

#boto.set_stream_logger('cloudsearch')


def do_bool(val):
    return 'true' if val in [True, 1, '1', 'true'] else 'false'


class Layer1(AWSQueryConnection):

    APIVersion = '2011-02-01'
    DefaultRegionName = boto.config.get('Boto', 'cs_region_name', 'us-east-1')
    DefaultRegionEndpoint = boto.config.get('Boto', 'cs_region_endpoint',
                                            'cloudsearch.us-east-1.amazonaws.com')

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, host=None, port=None,
                 proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 api_version=None, security_token=None,
                 validate_certs=True, profile_name=None):
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        self.region = region
        AWSQueryConnection.__init__(
            self,
            host=self.region.endpoint,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            is_secure=is_secure,
            port=port,
            proxy=proxy,
            proxy_port=proxy_port,
            proxy_user=proxy_user,
            proxy_pass=proxy_pass,
            debug=debug,
            https_connection_factory=https_connection_factory,
            path=path,
            security_token=security_token,
            validate_certs=validate_certs,
            profile_name=profile_name)

    def _required_auth_capability(self):
        return ['hmac-v4']

    def get_response(self, doc_path, action, params, path='/',
                     parent=None, verb='GET', list_marker=None):
        if not parent:
            parent = self
        response = self.make_request(action, params, path, verb)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            e = boto.jsonresponse.Element(
                list_marker=list_marker if list_marker else 'Set',
                pythonize_name=True)
            h = boto.jsonresponse.XmlHandler(e, parent)
            h.parse(body)
            inner = e
            for p in doc_path:
                inner = inner.get(p)
            if not inner:
                return None if list_marker is None else []
            if isinstance(inner, list):
                return inner
            else:
                return dict(**inner)
        else:
            raise self.ResponseError(response.status, response.reason, body)

    def create_domain(self, domain_name):
        """
        Create a new search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :raises: BaseException, InternalException, LimitExceededException
        """
        doc_path = ('create_domain_response',
                    'create_domain_result',
                    'domain_status')
        params = {'DomainName': domain_name}
        return self.get_response(doc_path, 'CreateDomain',
                                 params, verb='POST')

    def define_index_field(self, domain_name, field_name, field_type,
                           default='', facet=False, result=False,
                           searchable=False, source_attributes=None):
        """
        Defines an ``IndexField``, either replacing an existing
        definition or creating a new one.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

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
        doc_path = ('define_index_field_response',
                    'define_index_field_result',
                    'index_field')
        params = {'DomainName': domain_name,
                  'IndexField.IndexFieldName': field_name,
                  'IndexField.IndexFieldType': field_type}
        if field_type == 'literal':
            params['IndexField.LiteralOptions.DefaultValue'] = default
            params['IndexField.LiteralOptions.FacetEnabled'] = do_bool(facet)
            params['IndexField.LiteralOptions.ResultEnabled'] = do_bool(result)
            params['IndexField.LiteralOptions.SearchEnabled'] = do_bool(searchable)
        elif field_type == 'uint':
            params['IndexField.UIntOptions.DefaultValue'] = default
        elif field_type == 'text':
            params['IndexField.TextOptions.DefaultValue'] = default
            params['IndexField.TextOptions.FacetEnabled'] = do_bool(facet)
            params['IndexField.TextOptions.ResultEnabled'] = do_bool(result)

        return self.get_response(doc_path, 'DefineIndexField',
                                 params, verb='POST')

    def define_rank_expression(self, domain_name, rank_name, rank_expression):
        """
        Defines a RankExpression, either replacing an existing
        definition or creating a new one.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

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
        doc_path = ('define_rank_expression_response',
                    'define_rank_expression_result',
                    'rank_expression')
        params = {'DomainName': domain_name,
                  'RankExpression.RankExpression': rank_expression,
                  'RankExpression.RankName': rank_name}
        return self.get_response(doc_path, 'DefineRankExpression',
                                 params, verb='POST')

    def delete_domain(self, domain_name):
        """
        Delete a search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :raises: BaseException, InternalException
        """
        doc_path = ('delete_domain_response',
                    'delete_domain_result',
                    'domain_status')
        params = {'DomainName': domain_name}
        return self.get_response(doc_path, 'DeleteDomain',
                                 params, verb='POST')

    def delete_index_field(self, domain_name, field_name):
        """
        Deletes an existing ``IndexField`` from the search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :type field_name: string
        :param field_name: A string that represents the name of
            an index field. Field names must begin with a letter and
            can contain the following characters: a-z (lowercase),
            0-9, and _ (underscore). Uppercase letters and hyphens are
            not allowed. The names "body", "docid", and
            "text_relevance" are reserved and cannot be specified as
            field or rank expression names.

        :raises: BaseException, InternalException, ResourceNotFoundException
        """
        doc_path = ('delete_index_field_response',
                    'delete_index_field_result',
                    'index_field')
        params = {'DomainName': domain_name,
                  'IndexFieldName': field_name}
        return self.get_response(doc_path, 'DeleteIndexField',
                                 params, verb='POST')

    def delete_rank_expression(self, domain_name, rank_name):
        """
        Deletes an existing ``RankExpression`` from the search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :type rank_name: string
        :param rank_name: Name of the ``RankExpression`` to delete.

        :raises: BaseException, InternalException, ResourceNotFoundException
        """
        doc_path = ('delete_rank_expression_response',
                    'delete_rank_expression_result',
                    'rank_expression')
        params = {'DomainName': domain_name, 'RankName': rank_name}
        return self.get_response(doc_path, 'DeleteRankExpression',
                                 params, verb='POST')

    def describe_default_search_field(self, domain_name):
        """
        Describes options defining the default search field used by
        indexing for the search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :raises: BaseException, InternalException, ResourceNotFoundException
        """
        doc_path = ('describe_default_search_field_response',
                    'describe_default_search_field_result',
                    'default_search_field')
        params = {'DomainName': domain_name}
        return self.get_response(doc_path, 'DescribeDefaultSearchField',
                                 params, verb='POST')

    def describe_domains(self, domain_names=None):
        """
        Describes the domains (optionally limited to one or more
        domains by name) owned by this account.

        :type domain_names: list
        :param domain_names: Limits the response to the specified domains.

        :raises: BaseException, InternalException
        """
        doc_path = ('describe_domains_response',
                    'describe_domains_result',
                    'domain_status_list')
        params = {}
        if domain_names:
            for i, domain_name in enumerate(domain_names, 1):
                params['DomainNames.member.%d' % i] = domain_name
        return self.get_response(doc_path, 'DescribeDomains',
                                 params, verb='POST',
                                 list_marker='DomainStatusList')

    def describe_index_fields(self, domain_name, field_names=None):
        """
        Describes index fields in the search domain, optionally
        limited to a single ``IndexField``.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :type field_names: list
        :param field_names: Limits the response to the specified fields.

        :raises: BaseException, InternalException, ResourceNotFoundException
        """
        doc_path = ('describe_index_fields_response',
                    'describe_index_fields_result',
                    'index_fields')
        params = {'DomainName': domain_name}
        if field_names:
            for i, field_name in enumerate(field_names, 1):
                params['FieldNames.member.%d' % i] = field_name
        return self.get_response(doc_path, 'DescribeIndexFields',
                                 params, verb='POST',
                                 list_marker='IndexFields')

    def describe_rank_expressions(self, domain_name, rank_names=None):
        """
        Describes RankExpressions in the search domain, optionally
        limited to a single expression.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :type rank_names: list
        :param rank_names: Limit response to the specified rank names.

        :raises: BaseException, InternalException, ResourceNotFoundException
        """
        doc_path = ('describe_rank_expressions_response',
                    'describe_rank_expressions_result',
                    'rank_expressions')
        params = {'DomainName': domain_name}
        if rank_names:
            for i, rank_name in enumerate(rank_names, 1):
                params['RankNames.member.%d' % i] = rank_name
        return self.get_response(doc_path, 'DescribeRankExpressions',
                                 params, verb='POST',
                                 list_marker='RankExpressions')

    def describe_service_access_policies(self, domain_name):
        """
        Describes the resource-based policies controlling access to
        the services in this search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :raises: BaseException, InternalException, ResourceNotFoundException
        """
        doc_path = ('describe_service_access_policies_response',
                    'describe_service_access_policies_result',
                    'access_policies')
        params = {'DomainName': domain_name}
        return self.get_response(doc_path, 'DescribeServiceAccessPolicies',
                                 params, verb='POST')

    def describe_stemming_options(self, domain_name):
        """
        Describes stemming options used by indexing for the search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :raises: BaseException, InternalException, ResourceNotFoundException
        """
        doc_path = ('describe_stemming_options_response',
                    'describe_stemming_options_result',
                    'stems')
        params = {'DomainName': domain_name}
        return self.get_response(doc_path, 'DescribeStemmingOptions',
                                 params, verb='POST')

    def describe_stopword_options(self, domain_name):
        """
        Describes stopword options used by indexing for the search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :raises: BaseException, InternalException, ResourceNotFoundException
        """
        doc_path = ('describe_stopword_options_response',
                    'describe_stopword_options_result',
                    'stopwords')
        params = {'DomainName': domain_name}
        return self.get_response(doc_path, 'DescribeStopwordOptions',
                                 params, verb='POST')

    def describe_synonym_options(self, domain_name):
        """
        Describes synonym options used by indexing for the search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :raises: BaseException, InternalException, ResourceNotFoundException
        """
        doc_path = ('describe_synonym_options_response',
                    'describe_synonym_options_result',
                    'synonyms')
        params = {'DomainName': domain_name}
        return self.get_response(doc_path, 'DescribeSynonymOptions',
                                 params, verb='POST')

    def index_documents(self, domain_name):
        """
        Tells the search domain to start scanning its documents using
        the latest text processing options and ``IndexFields``.  This
        operation must be invoked to make visible in searches any
        options whose <a>OptionStatus</a> has ``OptionState`` of
        ``RequiresIndexDocuments``.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :raises: BaseException, InternalException, ResourceNotFoundException
        """
        doc_path = ('index_documents_response',
                    'index_documents_result',
                    'field_names')
        params = {'DomainName': domain_name}
        return self.get_response(doc_path, 'IndexDocuments', params,
                                 verb='POST', list_marker='FieldNames')

    def update_default_search_field(self, domain_name, default_search_field):
        """
        Updates options defining the default search field used by
        indexing for the search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :type default_search_field: string
        :param default_search_field: The IndexField to use for search
            requests issued with the q parameter. The default is an
            empty string, which automatically searches all text
            fields.

        :raises: BaseException, InternalException, InvalidTypeException,
            ResourceNotFoundException
        """
        doc_path = ('update_default_search_field_response',
                    'update_default_search_field_result',
                    'default_search_field')
        params = {'DomainName': domain_name,
                  'DefaultSearchField': default_search_field}
        return self.get_response(doc_path, 'UpdateDefaultSearchField',
                                 params, verb='POST')

    def update_service_access_policies(self, domain_name, access_policies):
        """
        Updates the policies controlling access to the services in
        this search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :type access_policies: string
        :param access_policies: An IAM access policy as described in
            The Access Policy Language in Using AWS Identity and
            Access Management. The maximum size of an access policy
            document is 100KB.

        :raises: BaseException, InternalException, LimitExceededException,
            ResourceNotFoundException, InvalidTypeException
        """
        doc_path = ('update_service_access_policies_response',
                    'update_service_access_policies_result',
                    'access_policies')
        params = {'AccessPolicies': access_policies,
                  'DomainName': domain_name}
        return self.get_response(doc_path, 'UpdateServiceAccessPolicies',
                                 params, verb='POST')

    def update_stemming_options(self, domain_name, stems):
        """
        Updates stemming options used by indexing for the search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :type stems: string
        :param stems: Maps terms to their stems.  The JSON object
            has a single key called "stems" whose value is a
            dict mapping terms to their stems. The maximum size
            of a stemming document is 500KB.
            Example: {"stems":{"people": "person", "walking":"walk"}}

        :raises: BaseException, InternalException, InvalidTypeException,
            LimitExceededException, ResourceNotFoundException
        """
        doc_path = ('update_stemming_options_response',
                    'update_stemming_options_result',
                    'stems')
        params = {'DomainName': domain_name,
                  'Stems': stems}
        return self.get_response(doc_path, 'UpdateStemmingOptions',
                                 params, verb='POST')

    def update_stopword_options(self, domain_name, stopwords):
        """
        Updates stopword options used by indexing for the search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :type stopwords: string
        :param stopwords: Lists stopwords in a JSON object. The object has a
            single key called "stopwords" whose value is an array of strings.
            The maximum size of a stopwords document is 10KB. Example:
            {"stopwords": ["a", "an", "the", "of"]}

        :raises: BaseException, InternalException, InvalidTypeException,
            LimitExceededException, ResourceNotFoundException
        """
        doc_path = ('update_stopword_options_response',
                    'update_stopword_options_result',
                    'stopwords')
        params = {'DomainName': domain_name,
                  'Stopwords': stopwords}
        return self.get_response(doc_path, 'UpdateStopwordOptions',
                                 params, verb='POST')

    def update_synonym_options(self, domain_name, synonyms):
        """
        Updates synonym options used by indexing for the search domain.

        :type domain_name: string
        :param domain_name: A string that represents the name of a
            domain. Domain names must be unique across the domains
            owned by an account within an AWS region. Domain names
            must start with a letter or number and can contain the
            following characters: a-z (lowercase), 0-9, and -
            (hyphen). Uppercase letters and underscores are not
            allowed.

        :type synonyms: string
        :param synonyms: Maps terms to their synonyms.  The JSON object
            has a single key "synonyms" whose value is a dict mapping terms
            to their synonyms. Each synonym is a simple string or an
            array of strings. The maximum size of a stopwords document
            is 100KB. Example:
            {"synonyms": {"cat": ["feline", "kitten"], "puppy": "dog"}}

        :raises: BaseException, InternalException, InvalidTypeException,
            LimitExceededException, ResourceNotFoundException
        """
        doc_path = ('update_synonym_options_response',
                    'update_synonym_options_result',
                    'synonyms')
        params = {'DomainName': domain_name,
                  'Synonyms': synonyms}
        return self.get_response(doc_path, 'UpdateSynonymOptions',
                                 params, verb='POST')
