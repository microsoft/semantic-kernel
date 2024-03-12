# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
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

import xml.sax
import time
import boto
from boto.connection import AWSAuthConnection
from boto import handler
from boto.cloudfront.distribution import Distribution, DistributionSummary, DistributionConfig
from boto.cloudfront.distribution import StreamingDistribution, StreamingDistributionSummary, StreamingDistributionConfig
from boto.cloudfront.identity import OriginAccessIdentity
from boto.cloudfront.identity import OriginAccessIdentitySummary
from boto.cloudfront.identity import OriginAccessIdentityConfig
from boto.cloudfront.invalidation import InvalidationBatch, InvalidationSummary, InvalidationListResultSet
from boto.resultset import ResultSet
from boto.cloudfront.exception import CloudFrontServerError


class CloudFrontConnection(AWSAuthConnection):

    DefaultHost = 'cloudfront.amazonaws.com'
    Version = '2010-11-01'

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 port=None, proxy=None, proxy_port=None,
                 host=DefaultHost, debug=0, security_token=None,
                 validate_certs=True, profile_name=None, https_connection_factory=None):
        super(CloudFrontConnection, self).__init__(host,
                                   aws_access_key_id, aws_secret_access_key,
                                   True, port, proxy, proxy_port, debug=debug,
                                   security_token=security_token,
                                   validate_certs=validate_certs,
                                   https_connection_factory=https_connection_factory,
                                   profile_name=profile_name)

    def get_etag(self, response):
        response_headers = response.msg
        for key in response_headers.keys():
            if key.lower() == 'etag':
                return response_headers[key]
        return None

    def _required_auth_capability(self):
        return ['cloudfront']

    # Generics

    def _get_all_objects(self, resource, tags, result_set_class=None,
                         result_set_kwargs=None):
        if not tags:
            tags = [('DistributionSummary', DistributionSummary)]
        response = self.make_request('GET', '/%s/%s' % (self.Version,
                                                        resource))
        body = response.read()
        boto.log.debug(body)
        if response.status >= 300:
            raise CloudFrontServerError(response.status, response.reason, body)
        rs_class = result_set_class or ResultSet
        rs_kwargs = result_set_kwargs or dict()
        rs = rs_class(tags, **rs_kwargs)
        h = handler.XmlHandler(rs, self)
        xml.sax.parseString(body, h)
        return rs

    def _get_info(self, id, resource, dist_class):
        uri = '/%s/%s/%s' % (self.Version, resource, id)
        response = self.make_request('GET', uri)
        body = response.read()
        boto.log.debug(body)
        if response.status >= 300:
            raise CloudFrontServerError(response.status, response.reason, body)
        d = dist_class(connection=self)
        response_headers = response.msg
        for key in response_headers.keys():
            if key.lower() == 'etag':
                d.etag = response_headers[key]
        h = handler.XmlHandler(d, self)
        xml.sax.parseString(body, h)
        return d

    def _get_config(self, id, resource, config_class):
        uri = '/%s/%s/%s/config' % (self.Version, resource, id)
        response = self.make_request('GET', uri)
        body = response.read()
        boto.log.debug(body)
        if response.status >= 300:
            raise CloudFrontServerError(response.status, response.reason, body)
        d = config_class(connection=self)
        d.etag = self.get_etag(response)
        h = handler.XmlHandler(d, self)
        xml.sax.parseString(body, h)
        return d

    def _set_config(self, distribution_id, etag, config):
        if isinstance(config, StreamingDistributionConfig):
            resource = 'streaming-distribution'
        else:
            resource = 'distribution'
        uri = '/%s/%s/%s/config' % (self.Version, resource, distribution_id)
        headers = {'If-Match': etag, 'Content-Type': 'text/xml'}
        response = self.make_request('PUT', uri, headers, config.to_xml())
        body = response.read()
        boto.log.debug(body)
        if response.status != 200:
            raise CloudFrontServerError(response.status, response.reason, body)
        return self.get_etag(response)

    def _create_object(self, config, resource, dist_class):
        response = self.make_request('POST', '/%s/%s' % (self.Version,
                                                         resource),
                                     {'Content-Type': 'text/xml'},
                                     data=config.to_xml())
        body = response.read()
        boto.log.debug(body)
        if response.status == 201:
            d = dist_class(connection=self)
            h = handler.XmlHandler(d, self)
            xml.sax.parseString(body, h)
            d.etag = self.get_etag(response)
            return d
        else:
            raise CloudFrontServerError(response.status, response.reason, body)

    def _delete_object(self, id, etag, resource):
        uri = '/%s/%s/%s' % (self.Version, resource, id)
        response = self.make_request('DELETE', uri, {'If-Match': etag})
        body = response.read()
        boto.log.debug(body)
        if response.status != 204:
            raise CloudFrontServerError(response.status, response.reason, body)

    # Distributions

    def get_all_distributions(self):
        tags = [('DistributionSummary', DistributionSummary)]
        return self._get_all_objects('distribution', tags)

    def get_distribution_info(self, distribution_id):
        return self._get_info(distribution_id, 'distribution', Distribution)

    def get_distribution_config(self, distribution_id):
        return self._get_config(distribution_id, 'distribution',
                                DistributionConfig)

    def set_distribution_config(self, distribution_id, etag, config):
        return self._set_config(distribution_id, etag, config)

    def create_distribution(self, origin, enabled, caller_reference='',
                            cnames=None, comment='', trusted_signers=None):
        config = DistributionConfig(origin=origin, enabled=enabled,
                                    caller_reference=caller_reference,
                                    cnames=cnames, comment=comment,
                                    trusted_signers=trusted_signers)
        return self._create_object(config, 'distribution', Distribution)

    def delete_distribution(self, distribution_id, etag):
        return self._delete_object(distribution_id, etag, 'distribution')

    # Streaming Distributions

    def get_all_streaming_distributions(self):
        tags = [('StreamingDistributionSummary', StreamingDistributionSummary)]
        return self._get_all_objects('streaming-distribution', tags)

    def get_streaming_distribution_info(self, distribution_id):
        return self._get_info(distribution_id, 'streaming-distribution',
                              StreamingDistribution)

    def get_streaming_distribution_config(self, distribution_id):
        return self._get_config(distribution_id, 'streaming-distribution',
                                StreamingDistributionConfig)

    def set_streaming_distribution_config(self, distribution_id, etag, config):
        return self._set_config(distribution_id, etag, config)

    def create_streaming_distribution(self, origin, enabled,
                                      caller_reference='',
                                      cnames=None, comment='',
                                      trusted_signers=None):
        config = StreamingDistributionConfig(origin=origin, enabled=enabled,
                                             caller_reference=caller_reference,
                                             cnames=cnames, comment=comment,
                                             trusted_signers=trusted_signers)
        return self._create_object(config, 'streaming-distribution',
                                   StreamingDistribution)

    def delete_streaming_distribution(self, distribution_id, etag):
        return self._delete_object(distribution_id, etag,
                                   'streaming-distribution')

    # Origin Access Identity

    def get_all_origin_access_identity(self):
        tags = [('CloudFrontOriginAccessIdentitySummary',
               OriginAccessIdentitySummary)]
        return self._get_all_objects('origin-access-identity/cloudfront', tags)

    def get_origin_access_identity_info(self, access_id):
        return self._get_info(access_id, 'origin-access-identity/cloudfront',
                              OriginAccessIdentity)

    def get_origin_access_identity_config(self, access_id):
        return self._get_config(access_id,
                                'origin-access-identity/cloudfront',
                                OriginAccessIdentityConfig)

    def set_origin_access_identity_config(self, access_id,
                                          etag, config):
        return self._set_config(access_id, etag, config)

    def create_origin_access_identity(self, caller_reference='', comment=''):
        config = OriginAccessIdentityConfig(caller_reference=caller_reference,
                                            comment=comment)
        return self._create_object(config, 'origin-access-identity/cloudfront',
                                   OriginAccessIdentity)

    def delete_origin_access_identity(self, access_id, etag):
        return self._delete_object(access_id, etag,
                                   'origin-access-identity/cloudfront')

    # Object Invalidation

    def create_invalidation_request(self, distribution_id, paths,
                                    caller_reference=None):
        """Creates a new invalidation request
            :see: http://goo.gl/8vECq
        """
        # We allow you to pass in either an array or
        # an InvalidationBatch object
        if not isinstance(paths, InvalidationBatch):
            paths = InvalidationBatch(paths)
        paths.connection = self
        uri = '/%s/distribution/%s/invalidation' % (self.Version,
                                                    distribution_id)
        response = self.make_request('POST', uri,
                                     {'Content-Type': 'text/xml'},
                                     data=paths.to_xml())
        body = response.read()
        if response.status == 201:
            h = handler.XmlHandler(paths, self)
            xml.sax.parseString(body, h)
            return paths
        else:
            raise CloudFrontServerError(response.status, response.reason, body)

    def invalidation_request_status(self, distribution_id,
                                     request_id, caller_reference=None):
        uri = '/%s/distribution/%s/invalidation/%s' % (self.Version,
                                                       distribution_id,
                                                       request_id)
        response = self.make_request('GET', uri, {'Content-Type': 'text/xml'})
        body = response.read()
        if response.status == 200:
            paths = InvalidationBatch([])
            h = handler.XmlHandler(paths, self)
            xml.sax.parseString(body, h)
            return paths
        else:
            raise CloudFrontServerError(response.status, response.reason, body)

    def get_invalidation_requests(self, distribution_id, marker=None,
                                  max_items=None):
        """
        Get all invalidation requests for a given CloudFront distribution.
        This returns an instance of an InvalidationListResultSet that
        automatically handles all of the result paging, etc. from CF - you just
        need to keep iterating until there are no more results.

        :type distribution_id: string
        :param distribution_id: The id of the CloudFront distribution

        :type marker: string
        :param marker: Use this only when paginating results and only in
                       follow-up request after you've received a response where
                       the results are truncated. Set this to the value of the
                       Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results and only in a
                          follow-up request to indicate the maximum number of
                          invalidation requests you want in the response. You
                          will need to pass the next_marker property from the
                          previous InvalidationListResultSet response in the
                          follow-up request in order to get the next 'page' of
                          results.

        :rtype: :class:`boto.cloudfront.invalidation.InvalidationListResultSet`
        :returns: An InvalidationListResultSet iterator that lists invalidation
                  requests for a given CloudFront distribution. Automatically
                  handles paging the results.
        """
        uri = 'distribution/%s/invalidation' % distribution_id
        params = dict()
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        if params:
            uri += '?%s=%s' % params.popitem()
            for k, v in params.items():
                uri += '&%s=%s' % (k, v)
        tags=[('InvalidationSummary', InvalidationSummary)]
        rs_class = InvalidationListResultSet
        rs_kwargs = dict(connection=self, distribution_id=distribution_id,
                         max_items=max_items, marker=marker)
        return self._get_all_objects(uri, tags, result_set_class=rs_class,
                                     result_set_kwargs=rs_kwargs)
