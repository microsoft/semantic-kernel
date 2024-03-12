# Copyright (c) 2006-2010 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
# Copyright (c) 2011 Blue Pines Technologies LLC, Brad Carleton
# www.bluepines.org
# Copyright (c) 2012 42 Lines Inc., Jim Browne
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

from boto.route53 import exception
import random
import uuid
import xml.sax

import boto
from boto.connection import AWSAuthConnection
from boto import handler
import boto.jsonresponse
from boto.route53.record import ResourceRecordSets
from boto.route53.zone import Zone
from boto.compat import six, urllib


HZXML = """<?xml version="1.0" encoding="UTF-8"?>
<CreateHostedZoneRequest xmlns="%(xmlns)s">
  <Name>%(name)s</Name>
  <CallerReference>%(caller_ref)s</CallerReference>
  <HostedZoneConfig>
    <Comment>%(comment)s</Comment>
  </HostedZoneConfig>
</CreateHostedZoneRequest>"""

HZPXML = """<?xml version="1.0" encoding="UTF-8"?>
<CreateHostedZoneRequest xmlns="%(xmlns)s">
  <Name>%(name)s</Name>
  <VPC>
    <VPCId>%(vpc_id)s</VPCId>
    <VPCRegion>%(vpc_region)s</VPCRegion>
  </VPC>
  <CallerReference>%(caller_ref)s</CallerReference>
  <HostedZoneConfig>
    <Comment>%(comment)s</Comment>
  </HostedZoneConfig>
</CreateHostedZoneRequest>"""

# boto.set_stream_logger('dns')


class Route53Connection(AWSAuthConnection):
    DefaultHost = 'route53.amazonaws.com'
    """The default Route53 API endpoint to connect to."""

    Version = '2013-04-01'
    """Route53 API version."""

    XMLNameSpace = 'https://route53.amazonaws.com/doc/2013-04-01/'
    """XML schema for this Route53 API version."""

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 port=None, proxy=None, proxy_port=None,
                 host=DefaultHost, debug=0, security_token=None,
                 validate_certs=True, https_connection_factory=None,
                 profile_name=None):
        super(Route53Connection, self).__init__(
            host,
            aws_access_key_id, aws_secret_access_key,
            True, port, proxy, proxy_port, debug=debug,
            security_token=security_token,
            validate_certs=validate_certs,
            https_connection_factory=https_connection_factory,
            profile_name=profile_name)

    def _required_auth_capability(self):
        return ['route53']

    def make_request(self, action, path, headers=None, data='', params=None):
        if params:
            pairs = []
            for key, val in six.iteritems(params):
                if val is None:
                    continue
                pairs.append(key + '=' + urllib.parse.quote(str(val)))
            path += '?' + '&'.join(pairs)
        return super(Route53Connection, self).make_request(
            action, path, headers, data,
            retry_handler=self._retry_handler)

    # Hosted Zones

    def get_all_hosted_zones(self, start_marker=None, zone_list=None):
        """
        Returns a Python data structure with information about all
        Hosted Zones defined for the AWS account.

        :param int start_marker: start marker to pass when fetching additional
            results after a truncated list
        :param list zone_list: a HostedZones list to prepend to results
        """
        params = {}
        if start_marker:
            params = {'marker': start_marker}
        response = self.make_request('GET', '/%s/hostedzone' % self.Version,
                                     params=params)
        body = response.read()
        boto.log.debug(body)
        if response.status >= 300:
            raise exception.DNSServerError(response.status,
                                           response.reason,
                                           body)
        e = boto.jsonresponse.Element(list_marker='HostedZones',
                                      item_marker=('HostedZone',))
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        if zone_list:
            e['ListHostedZonesResponse']['HostedZones'].extend(zone_list)
        while 'NextMarker' in e['ListHostedZonesResponse']:
            next_marker = e['ListHostedZonesResponse']['NextMarker']
            zone_list = e['ListHostedZonesResponse']['HostedZones']
            e = self.get_all_hosted_zones(next_marker, zone_list)
        return e

    def get_hosted_zone(self, hosted_zone_id):
        """
        Get detailed information about a particular Hosted Zone.

        :type hosted_zone_id: str
        :param hosted_zone_id: The unique identifier for the Hosted Zone

        """
        uri = '/%s/hostedzone/%s' % (self.Version, hosted_zone_id)
        response = self.make_request('GET', uri)
        body = response.read()
        boto.log.debug(body)
        if response.status >= 300:
            raise exception.DNSServerError(response.status,
                                           response.reason,
                                           body)
        e = boto.jsonresponse.Element(list_marker='NameServers',
                                      item_marker=('NameServer',))
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        return e

    def get_hosted_zone_by_name(self, hosted_zone_name):
        """
        Get detailed information about a particular Hosted Zone.

        :type hosted_zone_name: str
        :param hosted_zone_name: The fully qualified domain name for the Hosted
            Zone

        """
        if hosted_zone_name[-1] != '.':
            hosted_zone_name += '.'
        all_hosted_zones = self.get_all_hosted_zones()
        for zone in all_hosted_zones['ListHostedZonesResponse']['HostedZones']:
            # check that they gave us the FQDN for their zone
            if zone['Name'] == hosted_zone_name:
                return self.get_hosted_zone(zone['Id'].split('/')[-1])

    def create_hosted_zone(self, domain_name, caller_ref=None, comment='',
                           private_zone=False, vpc_id=None, vpc_region=None):
        """
        Create a new Hosted Zone.  Returns a Python data structure with
        information about the newly created Hosted Zone.

        :type domain_name: str
        :param domain_name: The name of the domain. This should be a
            fully-specified domain, and should end with a final period
            as the last label indication.  If you omit the final period,
            Amazon Route 53 assumes the domain is relative to the root.
            This is the name you have registered with your DNS registrar.
            It is also the name you will delegate from your registrar to
            the Amazon Route 53 delegation servers returned in
            response to this request.A list of strings with the image
            IDs wanted.

        :type caller_ref: str
        :param caller_ref: A unique string that identifies the request
            and that allows failed CreateHostedZone requests to be retried
            without the risk of executing the operation twice.  If you don't
            provide a value for this, boto will generate a Type 4 UUID and
            use that.

        :type comment: str
        :param comment: Any comments you want to include about the hosted
            zone.

        :type private_zone: bool
        :param private_zone: Set True if creating a private hosted zone.

        :type vpc_id: str
        :param vpc_id: When creating a private hosted zone, the VPC Id to
            associate to is required.

        :type vpc_region: str
        :param vpc_region: When creating a private hosted zone, the region
            of the associated VPC is required.

        """
        if caller_ref is None:
            caller_ref = str(uuid.uuid4())
        if private_zone:
            params = {'name': domain_name,
                      'caller_ref': caller_ref,
                      'comment': comment,
                      'vpc_id': vpc_id,
                      'vpc_region': vpc_region,
                      'xmlns': self.XMLNameSpace}
            xml_body = HZPXML % params
        else:
            params = {'name': domain_name,
                      'caller_ref': caller_ref,
                      'comment': comment,
                      'xmlns': self.XMLNameSpace}
            xml_body = HZXML % params
        uri = '/%s/hostedzone' % self.Version
        response = self.make_request('POST', uri,
                                     {'Content-Type': 'text/xml'}, xml_body)
        body = response.read()
        boto.log.debug(body)
        if response.status == 201:
            e = boto.jsonresponse.Element(list_marker='NameServers',
                                          item_marker=('NameServer',))
            h = boto.jsonresponse.XmlHandler(e, None)
            h.parse(body)
            return e
        else:
            raise exception.DNSServerError(response.status,
                                           response.reason,
                                           body)

    def delete_hosted_zone(self, hosted_zone_id):
        """
        Delete the hosted zone specified by the given id.

        :type hosted_zone_id: str
        :param hosted_zone_id: The hosted zone's id

        """
        uri = '/%s/hostedzone/%s' % (self.Version, hosted_zone_id)
        response = self.make_request('DELETE', uri)
        body = response.read()
        boto.log.debug(body)
        if response.status not in (200, 204):
            raise exception.DNSServerError(response.status,
                                           response.reason,
                                           body)
        e = boto.jsonresponse.Element()
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        return e

    # Health checks

    POSTHCXMLBody = """<CreateHealthCheckRequest xmlns="%(xmlns)s">
    <CallerReference>%(caller_ref)s</CallerReference>
    %(health_check)s
    </CreateHealthCheckRequest>"""

    def create_health_check(self, health_check, caller_ref=None):
        """
        Create a new Health Check

        :type health_check: HealthCheck
        :param health_check: HealthCheck object

        :type caller_ref: str
        :param caller_ref: A unique string that identifies the request
            and that allows failed CreateHealthCheckRequest requests to be retried
            without the risk of executing the operation twice.  If you don't
            provide a value for this, boto will generate a Type 4 UUID and
            use that.

        """
        if caller_ref is None:
            caller_ref = str(uuid.uuid4())
        uri = '/%s/healthcheck' % self.Version
        params = {'xmlns': self.XMLNameSpace,
                  'caller_ref': caller_ref,
                  'health_check': health_check.to_xml()
                  }
        xml_body = self.POSTHCXMLBody % params
        response = self.make_request('POST', uri, {'Content-Type': 'text/xml'}, xml_body)
        body = response.read()
        boto.log.debug(body)
        if response.status == 201:
            e = boto.jsonresponse.Element()
            h = boto.jsonresponse.XmlHandler(e, None)
            h.parse(body)
            return e
        else:
            raise exception.DNSServerError(response.status, response.reason, body)

    def get_list_health_checks(self, maxitems=None, marker=None):
        """
        Return a list of health checks

        :type maxitems: int
        :param maxitems: Maximum number of items to return

        :type marker: str
        :param marker: marker to get next set of items to list

        """

        params = {}
        if maxitems is not None:
            params['maxitems'] = maxitems
        if marker is not None:
            params['marker'] = marker

        uri = '/%s/healthcheck' % (self.Version, )
        response = self.make_request('GET', uri, params=params)
        body = response.read()
        boto.log.debug(body)
        if response.status >= 300:
            raise exception.DNSServerError(response.status,
                                           response.reason,
                                           body)
        e = boto.jsonresponse.Element(list_marker='HealthChecks',
                                      item_marker=('HealthCheck',))
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        return e

    def get_checker_ip_ranges(self):
        """
        Return a list of Route53 healthcheck IP ranges
        """
        uri = '/%s/checkeripranges' % self.Version
        response = self.make_request('GET', uri)
        body = response.read()
        boto.log.debug(body)
        if response.status >= 300:
            raise exception.DNSServerError(response.status,
                                           response.reason,
                                           body)
        e = boto.jsonresponse.Element(list_marker='CheckerIpRanges', item_marker=('member',))
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        return e

    def delete_health_check(self, health_check_id):
        """
        Delete a health check

        :type health_check_id: str
        :param health_check_id: ID of the health check to delete

        """
        uri = '/%s/healthcheck/%s' % (self.Version, health_check_id)
        response = self.make_request('DELETE', uri)
        body = response.read()
        boto.log.debug(body)
        if response.status not in (200, 204):
            raise exception.DNSServerError(response.status,
                                           response.reason,
                                           body)
        e = boto.jsonresponse.Element()
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        return e

    # Resource Record Sets

    def get_all_rrsets(self, hosted_zone_id, type=None,
                       name=None, identifier=None, maxitems=None):
        """
        Retrieve the Resource Record Sets defined for this Hosted Zone.
        Returns the raw XML data returned by the Route53 call.

        :type hosted_zone_id: str
        :param hosted_zone_id: The unique identifier for the Hosted Zone

        :type type: str
        :param type: The type of resource record set to begin the record
            listing from.  Valid choices are:

                * A
                * AAAA
                * CNAME
                * MX
                * NS
                * PTR
                * SOA
                * SPF
                * SRV
                * TXT

            Valid values for weighted resource record sets:

                * A
                * AAAA
                * CNAME
                * TXT

            Valid values for Zone Apex Aliases:

                * A
                * AAAA

        :type name: str
        :param name: The first name in the lexicographic ordering of domain
                     names to be retrieved

        :type identifier: str
        :param identifier: In a hosted zone that includes weighted resource
            record sets (multiple resource record sets with the same DNS
            name and type that are differentiated only by SetIdentifier),
            if results were truncated for a given DNS name and type,
            the value of SetIdentifier for the next resource record
            set that has the current DNS name and type

        :type maxitems: int
        :param maxitems: The maximum number of records

        """
        params = {'type': type, 'name': name,
                  'identifier': identifier, 'maxitems': maxitems}
        uri = '/%s/hostedzone/%s/rrset' % (self.Version, hosted_zone_id)
        response = self.make_request('GET', uri, params=params)
        body = response.read()
        boto.log.debug(body)
        if response.status >= 300:
            raise exception.DNSServerError(response.status,
                                           response.reason,
                                           body)
        rs = ResourceRecordSets(connection=self, hosted_zone_id=hosted_zone_id)
        h = handler.XmlHandler(rs, self)
        xml.sax.parseString(body, h)
        return rs

    def change_rrsets(self, hosted_zone_id, xml_body):
        """
        Create or change the authoritative DNS information for this
        Hosted Zone.
        Returns a Python data structure with information about the set of
        changes, including the Change ID.

        :type hosted_zone_id: str
        :param hosted_zone_id: The unique identifier for the Hosted Zone

        :type xml_body: str
        :param xml_body: The list of changes to be made, defined in the
            XML schema defined by the Route53 service.

        """
        uri = '/%s/hostedzone/%s/rrset' % (self.Version, hosted_zone_id)
        response = self.make_request('POST', uri,
                                     {'Content-Type': 'text/xml'},
                                     xml_body)
        body = response.read()
        boto.log.debug(body)
        if response.status >= 300:
            raise exception.DNSServerError(response.status,
                                           response.reason,
                                           body)
        e = boto.jsonresponse.Element()
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        return e

    def get_change(self, change_id):
        """
        Get information about a proposed set of changes, as submitted
        by the change_rrsets method.
        Returns a Python data structure with status information about the
        changes.

        :type change_id: str
        :param change_id: The unique identifier for the set of changes.
            This ID is returned in the response to the change_rrsets method.

        """
        uri = '/%s/change/%s' % (self.Version, change_id)
        response = self.make_request('GET', uri)
        body = response.read()
        boto.log.debug(body)
        if response.status >= 300:
            raise exception.DNSServerError(response.status,
                                           response.reason,
                                           body)
        e = boto.jsonresponse.Element()
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        return e

    def create_zone(self, name, private_zone=False,
                    vpc_id=None, vpc_region=None):
        """
        Create a new Hosted Zone.  Returns a Zone object for the newly
        created Hosted Zone.

        :type name: str
        :param name: The name of the domain. This should be a
            fully-specified domain, and should end with a final period
            as the last label indication.  If you omit the final period,
            Amazon Route 53 assumes the domain is relative to the root.
            This is the name you have registered with your DNS registrar.
            It is also the name you will delegate from your registrar to
            the Amazon Route 53 delegation servers returned in
            response to this request.

        :type private_zone: bool
        :param private_zone: Set True if creating a private hosted zone.

        :type vpc_id: str
        :param vpc_id: When creating a private hosted zone, the VPC Id to
            associate to is required.

        :type vpc_region: str
        :param vpc_region: When creating a private hosted zone, the region
            of the associated VPC is required.
        """
        zone = self.create_hosted_zone(name, private_zone=private_zone,
                                       vpc_id=vpc_id, vpc_region=vpc_region)
        return Zone(self, zone['CreateHostedZoneResponse']['HostedZone'])

    def get_zone(self, name):
        """
        Returns a Zone object for the specified Hosted Zone.

        :param name: The name of the domain. This should be a
            fully-specified domain, and should end with a final period
            as the last label indication.
        """
        name = self._make_qualified(name)
        for zone in self.get_zones():
            if name == zone.name:
                return zone

    def get_zones(self):
        """
        Returns a list of Zone objects, one for each of the Hosted
        Zones defined for the AWS account.

        :rtype: list
        :returns: A list of Zone objects.

        """
        zones = self.get_all_hosted_zones()
        return [Zone(self, zone) for zone in
                zones['ListHostedZonesResponse']['HostedZones']]

    def _make_qualified(self, value):
        """
        Ensure passed domain names end in a period (.) character.
        This will usually make a domain fully qualified.
        """
        if type(value) in [list, tuple, set]:
            new_list = []
            for record in value:
                if record and not record[-1] == '.':
                    new_list.append("%s." % record)
                else:
                    new_list.append(record)
            return new_list
        else:
            value = value.strip()
            if value and not value[-1] == '.':
                value = "%s." % value
            return value

    def _retry_handler(self, response, i, next_sleep):
        status = None
        boto.log.debug("Saw HTTP status: %s" % response.status)

        if response.status == 400:
            body = response.read()

            # We need to parse the error first
            err = exception.DNSServerError(
                response.status,
                response.reason,
                body)
            if err.error_code:
                # This is a case where we need to ignore a 400 error, as
                # Route53 returns this. See
                # http://docs.aws.amazon.com/Route53/latest/DeveloperGuide/DNSLimitations.html
                if not err.error_code in (
                        'PriorRequestNotComplete',
                        'Throttling',
                        'ServiceUnavailable',
                        'RequestExpired'):
                    return status
                msg = "%s, retry attempt %s" % (
                    err.error_code,
                    i
                )
                next_sleep = min(random.random() * (2 ** i),
                                 boto.config.get('Boto', 'max_retry_delay', 60))
                i += 1
                status = (msg, i, next_sleep)

        return status
