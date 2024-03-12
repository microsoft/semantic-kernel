# Copyright (c) 2014 Tellybug, Matt Millar
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


"""
From http://docs.aws.amazon.com/Route53/latest/APIReference/API_CreateHealthCheck.html

POST /2013-04-01/healthcheck HTTP/1.1

<?xml version="1.0" encoding="UTF-8"?>
<CreateHealthCheckRequest xmlns="https://route53.amazonaws.com/doc/2013-04-01/">
   <CallerReference>unique description</CallerReference>
   <HealthCheckConfig>
      <IPAddress>IP address of the endpoint to check</IPAddress>
      <Port>port on the endpoint to check</Port>
      <Type>HTTP | HTTPS | HTTP_STR_MATCH | HTTPS_STR_MATCH | TCP</Type>
      <ResourcePath>path of the file that
         you want Amazon Route 53 to request</ResourcePath>
      <FullyQualifiedDomainName>domain name of the
         endpoint to check</FullyQualifiedDomainName>
      <SearchString>if Type is HTTP_STR_MATCH or HTTPS_STR_MATCH,
         the string to search for in the response body
         from the specified resource</SearchString>
      <RequestInterval>10 | 30</RequestInterval>
      <FailureThreshold>integer between 1 and 10</FailureThreshold>
   </HealthCheckConfig>
</CreateHealthCheckRequest>
"""


class HealthCheck(object):

    """An individual health check"""

    POSTXMLBody = """
        <HealthCheckConfig>
            %(ip_addr_part)s
            <Port>%(port)s</Port>
            <Type>%(type)s</Type>
            <ResourcePath>%(resource_path)s</ResourcePath>
            %(fqdn_part)s
            %(string_match_part)s
            %(request_interval)s
            <FailureThreshold>%(failure_threshold)s</FailureThreshold>
        </HealthCheckConfig>
    """

    XMLIpAddrPart = """<IPAddress>%(ip_addr)s</IPAddress>"""

    XMLFQDNPart = """<FullyQualifiedDomainName>%(fqdn)s</FullyQualifiedDomainName>"""

    XMLStringMatchPart = """<SearchString>%(string_match)s</SearchString>"""

    XMLRequestIntervalPart = """<RequestInterval>%(request_interval)d</RequestInterval>"""

    valid_request_intervals = (10, 30)

    def __init__(self, ip_addr, port, hc_type, resource_path, fqdn=None, string_match=None, request_interval=30, failure_threshold=3):
        """
        HealthCheck object

        :type ip_addr: str
        :param ip_addr: Optional IP Address

        :type port: int
        :param port: Port to check

        :type hc_type: str
        :param hc_type: One of HTTP | HTTPS | HTTP_STR_MATCH | HTTPS_STR_MATCH | TCP

        :type resource_path: str
        :param resource_path: Path to check

        :type fqdn: str
        :param fqdn: domain name of the endpoint to check

        :type string_match: str
        :param string_match: if hc_type is HTTP_STR_MATCH or HTTPS_STR_MATCH, the string to search for in the response body from the specified resource

        :type request_interval: int
        :param request_interval: The number of seconds between the time that Amazon Route 53 gets a response from your endpoint and the time that it sends the next health-check request.

        :type failure_threshold: int
        :param failure_threshold: The number of consecutive health checks that an endpoint must pass or fail for Amazon Route 53 to change the current status of the endpoint from unhealthy to healthy or vice versa.

        """
        self.ip_addr = ip_addr
        self.port = port
        self.hc_type = hc_type
        self.resource_path = resource_path
        self.fqdn = fqdn
        self.string_match = string_match
        self.failure_threshold = failure_threshold

        if request_interval in self.valid_request_intervals:
            self.request_interval = request_interval
        else:
            raise AttributeError(
                "Valid values for request_interval are: %s" %
                ",".join(str(i) for i in self.valid_request_intervals))

        if failure_threshold < 1 or failure_threshold > 10:
            raise AttributeError(
                'Valid values for failure_threshold are 1 - 10.')

    def to_xml(self):
        params = {
            'ip_addr_part': '',
            'port': self.port,
            'type': self.hc_type,
            'resource_path': self.resource_path,
            'fqdn_part': "",
            'string_match_part': "",
            'request_interval': (self.XMLRequestIntervalPart %
                                 {'request_interval': self.request_interval}),
            'failure_threshold': self.failure_threshold,
        }
        if self.fqdn is not None:
            params['fqdn_part'] = self.XMLFQDNPart % {'fqdn': self.fqdn}

        if self.ip_addr:
            params['ip_addr_part'] = self.XMLIpAddrPart % {'ip_addr': self.ip_addr}

        if self.string_match is not None:
            params['string_match_part'] = self.XMLStringMatchPart % {'string_match': self.string_match}

        return self.POSTXMLBody % params
