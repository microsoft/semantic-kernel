# Copyright (c) 2014 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.cloudsearch2 import exceptions


class CloudSearchConnection(AWSQueryConnection):
    """
    Amazon CloudSearch Configuration Service
    You use the Amazon CloudSearch configuration service to create,
    configure, and manage search domains. Configuration service
    requests are submitted using the AWS Query protocol. AWS Query
    requests are HTTP or HTTPS requests submitted via HTTP GET or POST
    with a query parameter named Action.

    The endpoint for configuration service requests is region-
    specific: cloudsearch. region .amazonaws.com. For example,
    cloudsearch.us-east-1.amazonaws.com. For a current list of
    supported regions and endpoints, see `Regions and Endpoints`_.
    """
    APIVersion = "2013-01-01"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "cloudsearch.us-east-1.amazonaws.com"
    ResponseError = JSONResponseError

    _faults = {
        "InvalidTypeException": exceptions.InvalidTypeException,
        "LimitExceededException": exceptions.LimitExceededException,
        "InternalException": exceptions.InternalException,
        "DisabledOperationException": exceptions.DisabledOperationException,
        "ResourceNotFoundException": exceptions.ResourceNotFoundException,
        "BaseException": exceptions.BaseException,
    }

    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs or kwargs['host'] is None:
            kwargs['host'] = region.endpoint

        sign_request = kwargs.pop('sign_request', False)
        self.sign_request = sign_request

        super(CloudSearchConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def build_suggesters(self, domain_name):
        """
        Indexes the search suggestions.

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        """
        params = {'DomainName': domain_name, }
        return self._make_request(
            action='BuildSuggesters',
            verb='POST',
            path='/', params=params)

    def create_domain(self, domain_name):
        """
        Creates a new search domain. For more information, see
        `Creating a Search Domain`_ in the Amazon CloudSearch
        Developer Guide .

        :type domain_name: string
        :param domain_name: A name for the domain you are creating. Allowed
            characters are a-z (lower-case letters), 0-9, and hyphen (-).
            Domain names must start with a letter or number and be at least 3
            and no more than 28 characters long.

        """
        params = {'DomainName': domain_name, }
        return self._make_request(
            action='CreateDomain',
            verb='POST',
            path='/', params=params)

    def define_analysis_scheme(self, domain_name, analysis_scheme):
        """
        Configures an analysis scheme that can be applied to a `text`
        or `text-array` field to define language-specific text
        processing options. For more information, see `Configuring
        Analysis Schemes`_ in the Amazon CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        :type analysis_scheme: dict
        :param analysis_scheme: Configuration information for an analysis
            scheme. Each analysis scheme has a unique name and specifies the
            language of the text to be processed. The following options can be
            configured for an analysis scheme: `Synonyms`, `Stopwords`,
            `StemmingDictionary`, and `AlgorithmicStemming`.

        """
        params = {'DomainName': domain_name, }
        self.build_complex_param(params, 'AnalysisScheme',
                                 analysis_scheme)
        return self._make_request(
            action='DefineAnalysisScheme',
            verb='POST',
            path='/', params=params)

    def define_expression(self, domain_name, expression):
        """
        Configures an `Expression` for the search domain. Used to
        create new expressions and modify existing ones. If the
        expression exists, the new configuration replaces the old one.
        For more information, see `Configuring Expressions`_ in the
        Amazon CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        :type expression: dict
        :param expression: A named expression that can be evaluated at search
            time. Can be used to sort the search results, define other
            expressions, or return computed information in the search results.

        """
        params = {'DomainName': domain_name, }
        self.build_complex_param(params, 'Expression',
                                 expression)
        return self._make_request(
            action='DefineExpression',
            verb='POST',
            path='/', params=params)

    def define_index_field(self, domain_name, index_field):
        """
        Configures an `IndexField` for the search domain. Used to
        create new fields and modify existing ones. You must specify
        the name of the domain you are configuring and an index field
        configuration. The index field configuration specifies a
        unique name, the index field type, and the options you want to
        configure for the field. The options you can specify depend on
        the `IndexFieldType`. If the field exists, the new
        configuration replaces the old one. For more information, see
        `Configuring Index Fields`_ in the Amazon CloudSearch
        Developer Guide .

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        :type index_field: dict
        :param index_field: The index field and field options you want to
            configure.

        """
        params = {'DomainName': domain_name, }
        self.build_complex_param(params, 'IndexField',
                                 index_field)
        return self._make_request(
            action='DefineIndexField',
            verb='POST',
            path='/', params=params)

    def define_suggester(self, domain_name, suggester):
        """
        Configures a suggester for a domain. A suggester enables you
        to display possible matches before users finish typing their
        queries. When you configure a suggester, you must specify the
        name of the text field you want to search for possible matches
        and a unique name for the suggester. For more information, see
        `Getting Search Suggestions`_ in the Amazon CloudSearch
        Developer Guide .

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        :type suggester: dict
        :param suggester: Configuration information for a search suggester.
            Each suggester has a unique name and specifies the text field you
            want to use for suggestions. The following options can be
            configured for a suggester: `FuzzyMatching`, `SortExpression`.

        """
        params = {'DomainName': domain_name, }
        self.build_complex_param(params, 'Suggester',
                                 suggester)
        return self._make_request(
            action='DefineSuggester',
            verb='POST',
            path='/', params=params)

    def delete_analysis_scheme(self, domain_name, analysis_scheme_name):
        """
        Deletes an analysis scheme. For more information, see
        `Configuring Analysis Schemes`_ in the Amazon CloudSearch
        Developer Guide .

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        :type analysis_scheme_name: string
        :param analysis_scheme_name: The name of the analysis scheme you want
            to delete.

        """
        params = {
            'DomainName': domain_name,
            'AnalysisSchemeName': analysis_scheme_name,
        }
        return self._make_request(
            action='DeleteAnalysisScheme',
            verb='POST',
            path='/', params=params)

    def delete_domain(self, domain_name):
        """
        Permanently deletes a search domain and all of its data. Once
        a domain has been deleted, it cannot be recovered. For more
        information, see `Deleting a Search Domain`_ in the Amazon
        CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: The name of the domain you want to permanently
            delete.

        """
        params = {'DomainName': domain_name, }
        return self._make_request(
            action='DeleteDomain',
            verb='POST',
            path='/', params=params)

    def delete_expression(self, domain_name, expression_name):
        """
        Removes an `Expression` from the search domain. For more
        information, see `Configuring Expressions`_ in the Amazon
        CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        :type expression_name: string
        :param expression_name: The name of the `Expression` to delete.

        """
        params = {
            'DomainName': domain_name,
            'ExpressionName': expression_name,
        }
        return self._make_request(
            action='DeleteExpression',
            verb='POST',
            path='/', params=params)

    def delete_index_field(self, domain_name, index_field_name):
        """
        Removes an `IndexField` from the search domain. For more
        information, see `Configuring Index Fields`_ in the Amazon
        CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        :type index_field_name: string
        :param index_field_name: The name of the index field your want to
            remove from the domain's indexing options.

        """
        params = {
            'DomainName': domain_name,
            'IndexFieldName': index_field_name,
        }
        return self._make_request(
            action='DeleteIndexField',
            verb='POST',
            path='/', params=params)

    def delete_suggester(self, domain_name, suggester_name):
        """
        Deletes a suggester. For more information, see `Getting Search
        Suggestions`_ in the Amazon CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        :type suggester_name: string
        :param suggester_name: Specifies the name of the suggester you want to
            delete.

        """
        params = {
            'DomainName': domain_name,
            'SuggesterName': suggester_name,
        }
        return self._make_request(
            action='DeleteSuggester',
            verb='POST',
            path='/', params=params)

    def describe_analysis_schemes(self, domain_name,
                                  analysis_scheme_names=None, deployed=None):
        """
        Gets the analysis schemes configured for a domain. An analysis
        scheme defines language-specific text processing options for a
        `text` field. Can be limited to specific analysis schemes by
        name. By default, shows all analysis schemes and includes any
        pending changes to the configuration. Set the `Deployed`
        option to `True` to show the active configuration and exclude
        pending changes. For more information, see `Configuring
        Analysis Schemes`_ in the Amazon CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: The name of the domain you want to describe.

        :type analysis_scheme_names: list
        :param analysis_scheme_names: The analysis schemes you want to
            describe.

        :type deployed: boolean
        :param deployed: Whether to display the deployed configuration (
            `True`) or include any pending changes ( `False`). Defaults to
            `False`.

        """
        params = {'DomainName': domain_name, }
        if analysis_scheme_names is not None:
            self.build_list_params(params,
                                   analysis_scheme_names,
                                   'AnalysisSchemeNames.member')
        if deployed is not None:
            params['Deployed'] = str(
                deployed).lower()
        return self._make_request(
            action='DescribeAnalysisSchemes',
            verb='POST',
            path='/', params=params)

    def describe_availability_options(self, domain_name, deployed=None):
        """
        Gets the availability options configured for a domain. By
        default, shows the configuration with any pending changes. Set
        the `Deployed` option to `True` to show the active
        configuration and exclude pending changes. For more
        information, see `Configuring Availability Options`_ in the
        Amazon CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: The name of the domain you want to describe.

        :type deployed: boolean
        :param deployed: Whether to display the deployed configuration (
            `True`) or include any pending changes ( `False`). Defaults to
            `False`.

        """
        params = {'DomainName': domain_name, }
        if deployed is not None:
            params['Deployed'] = str(
                deployed).lower()
        return self._make_request(
            action='DescribeAvailabilityOptions',
            verb='POST',
            path='/', params=params)

    def describe_domains(self, domain_names=None):
        """
        Gets information about the search domains owned by this
        account. Can be limited to specific domains. Shows all domains
        by default. To get the number of searchable documents in a
        domain, use the console or submit a `matchall` request to your
        domain's search endpoint:
        `q=matchall&q.parser=structured&size=0`. For more information,
        see `Getting Information about a Search Domain`_ in the Amazon
        CloudSearch Developer Guide .

        :type domain_names: list
        :param domain_names: The names of the domains you want to include in
            the response.

        """
        params = {}
        if domain_names is not None:
            self.build_list_params(params,
                                   domain_names,
                                   'DomainNames.member')
        return self._make_request(
            action='DescribeDomains',
            verb='POST',
            path='/', params=params)

    def describe_expressions(self, domain_name, expression_names=None,
                             deployed=None):
        """
        Gets the expressions configured for the search domain. Can be
        limited to specific expressions by name. By default, shows all
        expressions and includes any pending changes to the
        configuration. Set the `Deployed` option to `True` to show the
        active configuration and exclude pending changes. For more
        information, see `Configuring Expressions`_ in the Amazon
        CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: The name of the domain you want to describe.

        :type expression_names: list
        :param expression_names: Limits the `DescribeExpressions` response to
            the specified expressions. If not specified, all expressions are
            shown.

        :type deployed: boolean
        :param deployed: Whether to display the deployed configuration (
            `True`) or include any pending changes ( `False`). Defaults to
            `False`.

        """
        params = {'DomainName': domain_name, }
        if expression_names is not None:
            self.build_list_params(params,
                                   expression_names,
                                   'ExpressionNames.member')
        if deployed is not None:
            params['Deployed'] = str(
                deployed).lower()
        return self._make_request(
            action='DescribeExpressions',
            verb='POST',
            path='/', params=params)

    def describe_index_fields(self, domain_name, field_names=None,
                              deployed=None):
        """
        Gets information about the index fields configured for the
        search domain. Can be limited to specific fields by name. By
        default, shows all fields and includes any pending changes to
        the configuration. Set the `Deployed` option to `True` to show
        the active configuration and exclude pending changes. For more
        information, see `Getting Domain Information`_ in the Amazon
        CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: The name of the domain you want to describe.

        :type field_names: list
        :param field_names: A list of the index fields you want to describe. If
            not specified, information is returned for all configured index
            fields.

        :type deployed: boolean
        :param deployed: Whether to display the deployed configuration (
            `True`) or include any pending changes ( `False`). Defaults to
            `False`.

        """
        params = {'DomainName': domain_name, }
        if field_names is not None:
            self.build_list_params(params,
                                   field_names,
                                   'FieldNames.member')
        if deployed is not None:
            params['Deployed'] = str(
                deployed).lower()
        return self._make_request(
            action='DescribeIndexFields',
            verb='POST',
            path='/', params=params)

    def describe_scaling_parameters(self, domain_name):
        """
        Gets the scaling parameters configured for a domain. A
        domain's scaling parameters specify the desired search
        instance type and replication count. For more information, see
        `Configuring Scaling Options`_ in the Amazon CloudSearch
        Developer Guide .

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        """
        params = {'DomainName': domain_name, }
        return self._make_request(
            action='DescribeScalingParameters',
            verb='POST',
            path='/', params=params)

    def describe_service_access_policies(self, domain_name, deployed=None):
        """
        Gets information about the access policies that control access
        to the domain's document and search endpoints. By default,
        shows the configuration with any pending changes. Set the
        `Deployed` option to `True` to show the active configuration
        and exclude pending changes. For more information, see
        `Configuring Access for a Search Domain`_ in the Amazon
        CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: The name of the domain you want to describe.

        :type deployed: boolean
        :param deployed: Whether to display the deployed configuration (
            `True`) or include any pending changes ( `False`). Defaults to
            `False`.

        """
        params = {'DomainName': domain_name, }
        if deployed is not None:
            params['Deployed'] = str(
                deployed).lower()
        return self._make_request(
            action='DescribeServiceAccessPolicies',
            verb='POST',
            path='/', params=params)

    def describe_suggesters(self, domain_name, suggester_names=None,
                            deployed=None):
        """
        Gets the suggesters configured for a domain. A suggester
        enables you to display possible matches before users finish
        typing their queries. Can be limited to specific suggesters by
        name. By default, shows all suggesters and includes any
        pending changes to the configuration. Set the `Deployed`
        option to `True` to show the active configuration and exclude
        pending changes. For more information, see `Getting Search
        Suggestions`_ in the Amazon CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: The name of the domain you want to describe.

        :type suggester_names: list
        :param suggester_names: The suggesters you want to describe.

        :type deployed: boolean
        :param deployed: Whether to display the deployed configuration (
            `True`) or include any pending changes ( `False`). Defaults to
            `False`.

        """
        params = {'DomainName': domain_name, }
        if suggester_names is not None:
            self.build_list_params(params,
                                   suggester_names,
                                   'SuggesterNames.member')
        if deployed is not None:
            params['Deployed'] = str(
                deployed).lower()
        return self._make_request(
            action='DescribeSuggesters',
            verb='POST',
            path='/', params=params)

    def index_documents(self, domain_name):
        """
        Tells the search domain to start indexing its documents using
        the latest indexing options. This operation must be invoked to
        activate options whose OptionStatus is
        `RequiresIndexDocuments`.

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        """
        params = {'DomainName': domain_name, }
        return self._make_request(
            action='IndexDocuments',
            verb='POST',
            path='/', params=params)

    def list_domain_names(self):
        """
        Lists all search domains owned by an account.
        """
        params = {}
        return self._make_request(
            action='ListDomainNames',
            verb='POST',
            path='/', params=params)

    def update_availability_options(self, domain_name, multi_az):
        """
        Configures the availability options for a domain. Enabling the
        Multi-AZ option expands an Amazon CloudSearch domain to an
        additional Availability Zone in the same Region to increase
        fault tolerance in the event of a service disruption. Changes
        to the Multi-AZ option can take about half an hour to become
        active. For more information, see `Configuring Availability
        Options`_ in the Amazon CloudSearch Developer Guide .

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        :type multi_az: boolean
        :param multi_az: You expand an existing search domain to a second
            Availability Zone by setting the Multi-AZ option to true.
            Similarly, you can turn off the Multi-AZ option to downgrade the
            domain to a single Availability Zone by setting the Multi-AZ option
            to `False`.

        """
        params = {'DomainName': domain_name, 'MultiAZ': multi_az, }
        return self._make_request(
            action='UpdateAvailabilityOptions',
            verb='POST',
            path='/', params=params)

    def update_scaling_parameters(self, domain_name, scaling_parameters):
        """
        Configures scaling parameters for a domain. A domain's scaling
        parameters specify the desired search instance type and
        replication count. Amazon CloudSearch will still automatically
        scale your domain based on the volume of data and traffic, but
        not below the desired instance type and replication count. If
        the Multi-AZ option is enabled, these values control the
        resources used per Availability Zone. For more information,
        see `Configuring Scaling Options`_ in the Amazon CloudSearch
        Developer Guide .

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        :type scaling_parameters: dict
        :param scaling_parameters: The desired instance type and desired number
            of replicas of each index partition.

        """
        params = {'DomainName': domain_name, }
        self.build_complex_param(params, 'ScalingParameters',
                                 scaling_parameters)
        return self._make_request(
            action='UpdateScalingParameters',
            verb='POST',
            path='/', params=params)

    def update_service_access_policies(self, domain_name, access_policies):
        """
        Configures the access rules that control access to the
        domain's document and search endpoints. For more information,
        see ` Configuring Access for an Amazon CloudSearch Domain`_.

        :type domain_name: string
        :param domain_name: A string that represents the name of a domain.
            Domain names are unique across the domains owned by an account
            within an AWS region. Domain names start with a letter or number
            and can contain the following characters: a-z (lowercase), 0-9, and
            - (hyphen).

        :type access_policies: string
        :param access_policies: The access rules you want to configure. These
            rules replace any existing rules.

        """
        params = {
            'DomainName': domain_name,
            'AccessPolicies': access_policies,
        }
        return self._make_request(
            action='UpdateServiceAccessPolicies',
            verb='POST',
            path='/', params=params)

    def build_complex_param(self, params, label, value):
        """Serialize a structure.

        For example::

            param_type = 'structure'
            label = 'IndexField'
            value = {'IndexFieldName': 'a', 'IntOptions': {'DefaultValue': 5}}

        would result in the params dict being updated with these params::

            IndexField.IndexFieldName = a
            IndexField.IntOptions.DefaultValue = 5

        :type params: dict
        :param params: The params dict.  The complex list params
            will be added to this dict.

        :type label: str
        :param label: String label for param key

        :type value: any
        :param value: The value to serialize
        """
        for k, v in value.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    self.build_complex_param(params, label + '.' + k, v)
            elif isinstance(v, bool):
                params['%s.%s' % (label, k)] = v and 'true' or 'false'
            else:
                params['%s.%s' % (label, k)] = v

    def _make_request(self, action, verb, path, params):
        params['ContentType'] = 'JSON'
        response = self.make_request(action=action, verb='POST',
                                     path='/', params=params)
        body = response.read().decode('utf-8')
        boto.log.debug(body)
        if response.status == 200:
            return json.loads(body)
        else:
            json_body = json.loads(body)
            fault_name = json_body.get('Error', {}).get('Code', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)
