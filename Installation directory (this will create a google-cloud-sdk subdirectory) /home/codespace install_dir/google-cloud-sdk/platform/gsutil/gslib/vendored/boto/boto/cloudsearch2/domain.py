# Copyright (c) 2014 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

from boto.cloudsearch2.optionstatus import IndexFieldStatus
from boto.cloudsearch2.optionstatus import ServicePoliciesStatus
from boto.cloudsearch2.optionstatus import ExpressionStatus
from boto.cloudsearch2.optionstatus import AvailabilityOptionsStatus
from boto.cloudsearch2.optionstatus import ScalingParametersStatus
from boto.cloudsearch2.document import DocumentServiceConnection
from boto.cloudsearch2.search import SearchConnection


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
        """
        Constructor - Create a domain object from a layer1 and data params

        :type layer1: :class:`boto.cloudsearch2.layer1.Layer1` object
        :param layer1: A :class:`boto.cloudsearch2.layer1.Layer1` object
            which is used to perform operations on the domain.
        """
        self.layer1 = layer1
        self.update_from_data(data)

    def update_from_data(self, data):
        self.created = data['Created']
        self.deleted = data['Deleted']
        self.processing = data['Processing']
        self.requires_index_documents = data['RequiresIndexDocuments']
        self.domain_id = data['DomainId']
        self.domain_name = data['DomainName']
        self.search_instance_count = data['SearchInstanceCount']
        self.search_instance_type = data.get('SearchInstanceType', None)
        self.search_partition_count = data['SearchPartitionCount']
        self._doc_service = data['DocService']
        self._service_arn = data['ARN']
        self._search_service = data['SearchService']

    @property
    def service_arn(self):
        return self._service_arn

    @property
    def doc_service_endpoint(self):
        return self._doc_service['Endpoint']

    @property
    def search_service_endpoint(self):
        return self._search_service['Endpoint']

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

    def get_analysis_schemes(self):
        """
        Return a list of Analysis Scheme objects.
        """
        return self.layer1.describe_analysis_schemes(self.name)

    def get_availability_options(self):
        """
        Return a :class:`boto.cloudsearch2.option.AvailabilityOptionsStatus`
        object representing the currently defined availability options for
        the domain.
        :return: OptionsStatus object
        :rtype: :class:`boto.cloudsearch2.option.AvailabilityOptionsStatus`
            object
        """
        return AvailabilityOptionsStatus(
            self, refresh_fn=self.layer1.describe_availability_options,
            refresh_key=['DescribeAvailabilityOptionsResponse',
                         'DescribeAvailabilityOptionsResult',
                         'AvailabilityOptions'],
            save_fn=self.layer1.update_availability_options)

    def get_scaling_options(self):
        """
        Return a :class:`boto.cloudsearch2.option.ScalingParametersStatus`
        object representing the currently defined scaling options for the
        domain.
        :return: ScalingParametersStatus object
        :rtype: :class:`boto.cloudsearch2.option.ScalingParametersStatus`
            object
        """
        return ScalingParametersStatus(
            self, refresh_fn=self.layer1.describe_scaling_parameters,
            refresh_key=['DescribeScalingParametersResponse',
                         'DescribeScalingParametersResult',
                         'ScalingParameters'],
            save_fn=self.layer1.update_scaling_parameters)

    def get_access_policies(self):
        """
        Return a :class:`boto.cloudsearch2.option.ServicePoliciesStatus`
        object representing the currently defined access policies for the
        domain.
        :return: ServicePoliciesStatus object
        :rtype: :class:`boto.cloudsearch2.option.ServicePoliciesStatus` object
        """
        return ServicePoliciesStatus(
            self, refresh_fn=self.layer1.describe_service_access_policies,
            refresh_key=['DescribeServiceAccessPoliciesResponse',
                         'DescribeServiceAccessPoliciesResult',
                         'AccessPolicies'],
            save_fn=self.layer1.update_service_access_policies)

    def index_documents(self):
        """
        Tells the search domain to start indexing its documents using
        the latest text processing options and IndexFields. This
        operation must be invoked to make options whose OptionStatus
        has OptionState of RequiresIndexDocuments visible in search
        results.
        """
        self.layer1.index_documents(self.name)

    def get_index_fields(self, field_names=None):
        """
        Return a list of index fields defined for this domain.
        :return: list of IndexFieldStatus objects
        :rtype: list of :class:`boto.cloudsearch2.option.IndexFieldStatus`
            object
        """
        data = self.layer1.describe_index_fields(self.name, field_names)

        data = (data['DescribeIndexFieldsResponse']
                    ['DescribeIndexFieldsResult']
                    ['IndexFields'])

        return [IndexFieldStatus(self, d) for d in data]

    def create_index_field(self, field_name, field_type,
                           default='', facet=False, returnable=False,
                           searchable=False, sortable=False,
                           highlight=False, source_field=None,
                           analysis_scheme=None):
        """
        Defines an ``IndexField``, either replacing an existing
        definition or creating a new one.

        :type field_name: string
        :param field_name: The name of a field in the search index.

        :type field_type: string
        :param field_type: The type of field.  Valid values are
            int | double | literal | text | date | latlon |
            int-array | double-array | literal-array | text-array | date-array

        :type default: string or int
        :param default: The default value for the field.  If the
            field is of type ``int`` this should be an integer value.
            Otherwise, it's a string.

        :type facet: bool
        :param facet: A boolean to indicate whether facets
            are enabled for this field or not.  Does not apply to
            fields of type ``int, int-array, text, text-array``.

        :type returnable: bool
        :param returnable: A boolean to indicate whether values
            of this field can be returned in search results or
            used in ranking.

        :type searchable: bool
        :param searchable: A boolean to indicate whether search
            is enabled for this field or not.

        :type sortable: bool
        :param sortable: A boolean to indicate whether sorting
            is enabled for this field or not. Does not apply to
            fields of array types.

        :type highlight: bool
        :param highlight: A boolean to indicate whether highlighting
            is enabled for this field or not. Does not apply to
            fields of type ``double, int, date, latlon``

        :type source_field: list of strings or string
        :param source_field: For array types, this is the list of fields
            to treat as the source. For singular types, pass a string only.

        :type analysis_scheme: string
        :param analysis_scheme: The analysis scheme to use for this field.
            Only applies to ``text | text-array`` field types

        :return: IndexFieldStatus objects
        :rtype: :class:`boto.cloudsearch2.option.IndexFieldStatus` object

        :raises: BaseException, InternalException, LimitExceededException,
            InvalidTypeException, ResourceNotFoundException
        """
        index = {
            'IndexFieldName': field_name,
            'IndexFieldType': field_type
        }
        if field_type == 'literal':
            index['LiteralOptions'] = {
                'FacetEnabled': facet,
                'ReturnEnabled': returnable,
                'SearchEnabled': searchable,
                'SortEnabled': sortable
            }
            if default:
                index['LiteralOptions']['DefaultValue'] = default
            if source_field:
                index['LiteralOptions']['SourceField'] = source_field
        elif field_type == 'literal-array':
            index['LiteralArrayOptions'] = {
                'FacetEnabled': facet,
                'ReturnEnabled': returnable,
                'SearchEnabled': searchable
            }
            if default:
                index['LiteralArrayOptions']['DefaultValue'] = default
            if source_field:
                index['LiteralArrayOptions']['SourceFields'] = \
                    ','.join(source_field)
        elif field_type == 'int':
            index['IntOptions'] = {
                'DefaultValue': default,
                'FacetEnabled': facet,
                'ReturnEnabled': returnable,
                'SearchEnabled': searchable,
                'SortEnabled': sortable
            }
            if default:
                index['IntOptions']['DefaultValue'] = default
            if source_field:
                index['IntOptions']['SourceField'] = source_field
        elif field_type == 'int-array':
            index['IntArrayOptions'] = {
                'FacetEnabled': facet,
                'ReturnEnabled': returnable,
                'SearchEnabled': searchable
            }
            if default:
                index['IntArrayOptions']['DefaultValue'] = default
            if source_field:
                index['IntArrayOptions']['SourceFields'] = \
                    ','.join(source_field)
        elif field_type == 'date':
            index['DateOptions'] = {
                'FacetEnabled': facet,
                'ReturnEnabled': returnable,
                'SearchEnabled': searchable,
                'SortEnabled': sortable
            }
            if default:
                index['DateOptions']['DefaultValue'] = default
            if source_field:
                index['DateOptions']['SourceField'] = source_field
        elif field_type == 'date-array':
            index['DateArrayOptions'] = {
                'FacetEnabled': facet,
                'ReturnEnabled': returnable,
                'SearchEnabled': searchable
            }
            if default:
                index['DateArrayOptions']['DefaultValue'] = default
            if source_field:
                index['DateArrayOptions']['SourceFields'] = \
                    ','.join(source_field)
        elif field_type == 'double':
            index['DoubleOptions'] = {
                'FacetEnabled': facet,
                'ReturnEnabled': returnable,
                'SearchEnabled': searchable,
                'SortEnabled': sortable
            }
            if default:
                index['DoubleOptions']['DefaultValue'] = default
            if source_field:
                index['DoubleOptions']['SourceField'] = source_field
        elif field_type == 'double-array':
            index['DoubleArrayOptions'] = {
                'FacetEnabled': facet,
                'ReturnEnabled': returnable,
                'SearchEnabled': searchable
            }
            if default:
                index['DoubleArrayOptions']['DefaultValue'] = default
            if source_field:
                index['DoubleArrayOptions']['SourceFields'] = \
                    ','.join(source_field)
        elif field_type == 'text':
            index['TextOptions'] = {
                'ReturnEnabled': returnable,
                'HighlightEnabled': highlight,
                'SortEnabled': sortable
            }
            if default:
                index['TextOptions']['DefaultValue'] = default
            if source_field:
                index['TextOptions']['SourceField'] = source_field
            if analysis_scheme:
                index['TextOptions']['AnalysisScheme'] = analysis_scheme
        elif field_type == 'text-array':
            index['TextArrayOptions'] = {
                'ReturnEnabled': returnable,
                'HighlightEnabled': highlight
            }
            if default:
                index['TextArrayOptions']['DefaultValue'] = default
            if source_field:
                index['TextArrayOptions']['SourceFields'] = \
                    ','.join(source_field)
            if analysis_scheme:
                index['TextArrayOptions']['AnalysisScheme'] = analysis_scheme
        elif field_type == 'latlon':
            index['LatLonOptions'] = {
                'FacetEnabled': facet,
                'ReturnEnabled': returnable,
                'SearchEnabled': searchable,
                'SortEnabled': sortable
            }
            if default:
                index['LatLonOptions']['DefaultValue'] = default
            if source_field:
                index['LatLonOptions']['SourceField'] = source_field

        data = self.layer1.define_index_field(self.name, index)

        data = (data['DefineIndexFieldResponse']
                    ['DefineIndexFieldResult']
                    ['IndexField'])

        return IndexFieldStatus(self, data,
                                self.layer1.describe_index_fields)

    def get_expressions(self, names=None):
        """
        Return a list of rank expressions defined for this domain.
        :return: list of ExpressionStatus objects
        :rtype: list of :class:`boto.cloudsearch2.option.ExpressionStatus`
            object
        """
        fn = self.layer1.describe_expressions
        data = fn(self.name, names)

        data = (data['DescribeExpressionsResponse']
                    ['DescribeExpressionsResult']
                    ['Expressions'])

        return [ExpressionStatus(self, d, fn) for d in data]

    def create_expression(self, name, value):
        """
        Create a new expression.

        :type name: string
        :param name: The name of an expression for processing
            during a search request.

        :type value: string
        :param value: The expression to evaluate for ranking
            or thresholding while processing a search request. The
            Expression syntax is based on JavaScript expressions
            and supports:

            * Single value, sort enabled numeric fields (int, double, date)
            * Other expressions
            * The _score variable, which references a document's relevance
              score
            * The _time variable, which references the current epoch time
            * Integer, floating point, hex, and octal literals
            * Arithmetic operators: + - * / %
            * Bitwise operators: | & ^ ~ << >> >>>
            * Boolean operators (including the ternary operator): && || ! ?:
            * Comparison operators: < <= == >= >
            * Mathematical functions: abs ceil exp floor ln log2 log10 logn
             max min pow sqrt pow
            * Trigonometric functions: acos acosh asin asinh atan atan2 atanh
             cos cosh sin sinh tanh tan
            * The haversin distance function

            Expressions always return an integer value from 0 to the maximum
            64-bit signed integer value (2^63 - 1). Intermediate results are
            calculated as double-precision floating point values and the return
            value is rounded to the nearest integer. If the expression is
            invalid or evaluates to a negative value, it returns 0. If the
            expression evaluates to a value greater than the maximum, it
            returns the maximum value.

            The source data for an Expression can be the name of an
            IndexField of type int or double, another Expression or the
            reserved name _score. The _score source is
            defined to return as a double from 0 to 10.0 (inclusive) to
            indicate how relevant a document is to the search request,
            taking into account repetition of search terms in the
            document and proximity of search terms to each other in
            each matching IndexField in the document.

            For more information about using rank expressions to
            customize ranking, see the Amazon CloudSearch Developer
            Guide.

        :return: ExpressionStatus object
        :rtype: :class:`boto.cloudsearch2.option.ExpressionStatus` object

        :raises: BaseException, InternalException, LimitExceededException,
            InvalidTypeException, ResourceNotFoundException
        """
        data = self.layer1.define_expression(self.name, name, value)

        data = (data['DefineExpressionResponse']
                    ['DefineExpressionResult']
                    ['Expression'])

        return ExpressionStatus(self, data,
                                self.layer1.describe_expressions)

    def get_document_service(self):
        return DocumentServiceConnection(domain=self)

    def get_search_service(self):
        return SearchConnection(domain=self)

    def __repr__(self):
        return '<Domain: %s>' % self.domain_name
