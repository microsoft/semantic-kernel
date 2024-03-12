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

from boto.cloudsearch2.layer1 import CloudSearchConnection
from boto.cloudsearch2.domain import Domain
from boto.compat import six


class Layer2(object):

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 host=None, debug=0, session_token=None, region=None,
                 validate_certs=True, sign_request=False):

        if isinstance(region, six.string_types):
            import boto.cloudsearch2
            for region_info in boto.cloudsearch2.regions():
                if region_info.name == region:
                    region = region_info
                    break

        self.layer1 = CloudSearchConnection(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            is_secure=is_secure,
            port=port,
            proxy=proxy,
            proxy_port=proxy_port,
            host=host,
            debug=debug,
            security_token=session_token,
            region=region,
            validate_certs=validate_certs,
            sign_request=sign_request)

    def list_domains(self, domain_names=None):
        """
        Return a list of objects for each domain defined in the
        current account.
        :rtype: list of :class:`boto.cloudsearch2.domain.Domain`
        """
        domain_data = self.layer1.describe_domains(domain_names)

        domain_data = (domain_data['DescribeDomainsResponse']
                                  ['DescribeDomainsResult']
                                  ['DomainStatusList'])

        return [Domain(self.layer1, data) for data in domain_data]

    def create_domain(self, domain_name):
        """
        Create a new CloudSearch domain and return the corresponding object.
        :return: Domain object, or None if the domain isn't found
        :rtype: :class:`boto.cloudsearch2.domain.Domain`
        """
        data = self.layer1.create_domain(domain_name)
        return Domain(self.layer1, data['CreateDomainResponse']
                                       ['CreateDomainResult']
                                       ['DomainStatus'])

    def lookup(self, domain_name):
        """
        Lookup a single domain
        :param domain_name: The name of the domain to look up
        :type domain_name: str

        :return: Domain object, or None if the domain isn't found
        :rtype: :class:`boto.cloudsearch2.domain.Domain`
        """
        domains = self.list_domains(domain_names=[domain_name])
        if len(domains) > 0:
            return domains[0]
