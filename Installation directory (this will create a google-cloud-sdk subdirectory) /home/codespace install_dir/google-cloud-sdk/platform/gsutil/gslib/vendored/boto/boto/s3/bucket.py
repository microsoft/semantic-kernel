# Copyright (c) 2006-2010 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
# All rights reserved.
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

from __future__ import division

import boto
from boto import handler
from boto.resultset import ResultSet
from boto.exception import BotoClientError
from boto.s3.acl import Policy, CannedACLStrings, Grant
from boto.s3.key import Key
from boto.s3.prefix import Prefix
from boto.s3.deletemarker import DeleteMarker
from boto.s3.multipart import MultiPartUpload
from boto.s3.multipart import CompleteMultiPartUpload
from boto.s3.multidelete import MultiDeleteResult
from boto.s3.multidelete import Error
from boto.s3.bucketlistresultset import BucketListResultSet
from boto.s3.bucketlistresultset import VersionedBucketListResultSet
from boto.s3.bucketlistresultset import MultiPartUploadListResultSet
from boto.s3.lifecycle import Lifecycle
from boto.s3.tagging import Tags
from boto.s3.cors import CORSConfiguration
from boto.s3.bucketlogging import BucketLogging
from boto.s3 import website
import boto.jsonresponse
import boto.utils
import xml.sax
import xml.sax.saxutils
import re
import base64
from collections import defaultdict
from boto.compat import BytesIO, six, StringIO, urllib
from boto.utils import get_utf8able_str

# as per http://goo.gl/BDuud (02/19/2011)


class S3WebsiteEndpointTranslate(object):

    trans_region = defaultdict(lambda: 's3-website-us-east-1')
    trans_region['eu-west-1'] = 's3-website-eu-west-1'
    trans_region['eu-central-1'] = 's3-website.eu-central-1'
    trans_region['us-west-1'] = 's3-website-us-west-1'
    trans_region['us-west-2'] = 's3-website-us-west-2'
    trans_region['sa-east-1'] = 's3-website-sa-east-1'
    trans_region['ap-northeast-1'] = 's3-website-ap-northeast-1'
    trans_region['ap-southeast-1'] = 's3-website-ap-southeast-1'
    trans_region['ap-southeast-2'] = 's3-website-ap-southeast-2'
    trans_region['cn-north-1'] = 's3-website.cn-north-1'

    @classmethod
    def translate_region(self, reg):
        return self.trans_region[reg]

S3Permissions = ['READ', 'WRITE', 'READ_ACP', 'WRITE_ACP', 'FULL_CONTROL']


class Bucket(object):

    LoggingGroup = 'http://acs.amazonaws.com/groups/s3/LogDelivery'

    BucketPaymentBody = """<?xml version="1.0" encoding="UTF-8"?>
       <RequestPaymentConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
         <Payer>%s</Payer>
       </RequestPaymentConfiguration>"""

    VersioningBody = """<?xml version="1.0" encoding="UTF-8"?>
       <VersioningConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
         <Status>%s</Status>
         <MfaDelete>%s</MfaDelete>
       </VersioningConfiguration>"""

    VersionRE = '<Status>([A-Za-z]+)</Status>'
    MFADeleteRE = '<MfaDelete>([A-Za-z]+)</MfaDelete>'

    def __init__(self, connection=None, name=None, key_class=Key):
        self.name = name
        self.connection = connection
        self.key_class = key_class

    def __repr__(self):
        return '<Bucket: %s>' % self.name

    def __iter__(self):
        return iter(BucketListResultSet(self))

    def __contains__(self, key_name):
        return not (self.get_key(key_name) is None)

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Name':
            self.name = value
        elif name == 'CreationDate':
            self.creation_date = value
        else:
            setattr(self, name, value)

    def set_key_class(self, key_class):
        """
        Set the Key class associated with this bucket.  By default, this
        would be the boto.s3.key.Key class but if you want to subclass that
        for some reason this allows you to associate your new class with a
        bucket so that when you call bucket.new_key() or when you get a listing
        of keys in the bucket you will get an instances of your key class
        rather than the default.

        :type key_class: class
        :param key_class: A subclass of Key that can be more specific
        """
        self.key_class = key_class

    def lookup(self, key_name, headers=None):
        """
        Deprecated: Please use get_key method.

        :type key_name: string
        :param key_name: The name of the key to retrieve

        :rtype: :class:`boto.s3.key.Key`
        :returns: A Key object from this bucket.
        """
        return self.get_key(key_name, headers=headers)

    def get_key(self, key_name, headers=None, version_id=None,
                response_headers=None, validate=True):
        """
        Check to see if a particular key exists within the bucket.  This
        method uses a HEAD request to check for the existence of the key.
        Returns: An instance of a Key object or None

        :param key_name: The name of the key to retrieve
        :type key_name: string

        :param headers: The headers to send when retrieving the key
        :type headers: dict

        :param version_id:
        :type version_id: string

        :param response_headers: A dictionary containing HTTP
            headers/values that will override any headers associated
            with the stored object in the response.  See
            http://goo.gl/EWOPb for details.
        :type response_headers: dict

        :param validate: Verifies whether the key exists. If ``False``, this
            will not hit the service, constructing an in-memory object.
            Default is ``True``.
        :type validate: bool

        :rtype: :class:`boto.s3.key.Key`
        :returns: A Key object from this bucket.
        """
        if validate is False:
            if headers or version_id or response_headers:
                raise BotoClientError(
                    "When providing 'validate=False', no other params " + \
                    "are allowed."
                )

            # This leans on the default behavior of ``new_key`` (not hitting
            # the service). If that changes, that behavior should migrate here.
            return self.new_key(key_name)

        query_args_l = []
        if version_id:
            query_args_l.append('versionId=%s' % version_id)
        if response_headers:
            for rk, rv in six.iteritems(response_headers):
                query_args_l.append('%s=%s' % (rk, urllib.parse.quote(rv)))

        key, resp = self._get_key_internal(key_name, headers, query_args_l)
        return key

    def _get_key_internal(self, key_name, headers, query_args_l):
        query_args = '&'.join(query_args_l) or None
        response = self.connection.make_request('HEAD', self.name, key_name,
                                                headers=headers,
                                                query_args=query_args)
        response.read()
        # Allow any success status (2xx) - for example this lets us
        # support Range gets, which return status 206:
        if response.status // 100 == 2:
            k = self.key_class(self)
            provider = self.connection.provider
            k.metadata = boto.utils.get_aws_metadata(response.msg, provider)
            for field in Key.base_fields:
                k.__dict__[field.lower().replace('-', '_')] = \
                    response.getheader(field)
            # the following machinations are a workaround to the fact that
            # apache/fastcgi omits the content-length header on HEAD
            # requests when the content-length is zero.
            # See http://goo.gl/0Tdax for more details.
            clen = response.getheader('content-length')
            if clen:
                k.size = int(response.getheader('content-length'))
            else:
                k.size = 0
            k.name = key_name
            k.handle_version_headers(response)
            k.handle_encryption_headers(response)
            k.handle_restore_headers(response)
            k.handle_storage_class_header(response)
            k.handle_addl_headers(response.getheaders())
            return k, response
        else:
            if response.status == 404:
                return None, response
            else:
                raise self.connection.provider.storage_response_error(
                    response.status, response.reason, '')

    def list(self, prefix='', delimiter='', marker='', headers=None,
             encoding_type=None):
        """
        List key objects within a bucket.  This returns an instance of an
        BucketListResultSet that automatically handles all of the result
        paging, etc. from S3.  You just need to keep iterating until
        there are no more results.

        Called with no arguments, this will return an iterator object across
        all keys within the bucket.

        The Key objects returned by the iterator are obtained by parsing
        the results of a GET on the bucket, also known as the List Objects
        request.  The XML returned by this request contains only a subset
        of the information about each key.  Certain metadata fields such
        as Content-Type and user metadata are not available in the XML.
        Therefore, if you want these additional metadata fields you will
        have to do a HEAD request on the Key in the bucket.

        :type prefix: string
        :param prefix: allows you to limit the listing to a particular
            prefix.  For example, if you call the method with
            prefix='/foo/' then the iterator will only cycle through
            the keys that begin with the string '/foo/'.

        :type delimiter: string
        :param delimiter: can be used in conjunction with the prefix
            to allow you to organize and browse your keys
            hierarchically. See http://goo.gl/Xx63h for more details.

        :type marker: string
        :param marker: The "marker" of where you are in the result set

        :param encoding_type: Requests Amazon S3 to encode the response and
            specifies the encoding method to use.

            An object key can contain any Unicode character; however, XML 1.0
            parser cannot parse some characters, such as characters with an
            ASCII value from 0 to 10. For characters that are not supported in
            XML 1.0, you can add this parameter to request that Amazon S3
            encode the keys in the response.

            Valid options: ``url``
        :type encoding_type: string

        :rtype: :class:`boto.s3.bucketlistresultset.BucketListResultSet`
        :return: an instance of a BucketListResultSet that handles paging, etc
        """
        return BucketListResultSet(self, prefix, delimiter, marker, headers,
                                   encoding_type=encoding_type)

    def list_versions(self, prefix='', delimiter='', key_marker='',
                      version_id_marker='', headers=None, encoding_type=None):
        """
        List version objects within a bucket.  This returns an
        instance of an VersionedBucketListResultSet that automatically
        handles all of the result paging, etc. from S3.  You just need
        to keep iterating until there are no more results.  Called
        with no arguments, this will return an iterator object across
        all keys within the bucket.

        :type prefix: string
        :param prefix: allows you to limit the listing to a particular
            prefix.  For example, if you call the method with
            prefix='/foo/' then the iterator will only cycle through
            the keys that begin with the string '/foo/'.

        :type delimiter: string
        :param delimiter: can be used in conjunction with the prefix
            to allow you to organize and browse your keys
            hierarchically. See:

            http://aws.amazon.com/releasenotes/Amazon-S3/213

            for more details.

        :type key_marker: string
        :param key_marker: The "marker" of where you are in the result set

        :param encoding_type: Requests Amazon S3 to encode the response and
            specifies the encoding method to use.

            An object key can contain any Unicode character; however, XML 1.0
            parser cannot parse some characters, such as characters with an
            ASCII value from 0 to 10. For characters that are not supported in
            XML 1.0, you can add this parameter to request that Amazon S3
            encode the keys in the response.

            Valid options: ``url``
        :type encoding_type: string

        :rtype: :class:`boto.s3.bucketlistresultset.BucketListResultSet`
        :return: an instance of a BucketListResultSet that handles paging, etc
        """
        return VersionedBucketListResultSet(self, prefix, delimiter,
                                            key_marker, version_id_marker,
                                            headers,
                                            encoding_type=encoding_type)

    def list_multipart_uploads(self, key_marker='',
                               upload_id_marker='',
                               headers=None, encoding_type=None):
        """
        List multipart upload objects within a bucket.  This returns an
        instance of an MultiPartUploadListResultSet that automatically
        handles all of the result paging, etc. from S3.  You just need
        to keep iterating until there are no more results.

        :type key_marker: string
        :param key_marker: The "marker" of where you are in the result set

        :type upload_id_marker: string
        :param upload_id_marker: The upload identifier

        :param encoding_type: Requests Amazon S3 to encode the response and
            specifies the encoding method to use.

            An object key can contain any Unicode character; however, XML 1.0
            parser cannot parse some characters, such as characters with an
            ASCII value from 0 to 10. For characters that are not supported in
            XML 1.0, you can add this parameter to request that Amazon S3
            encode the keys in the response.

            Valid options: ``url``
        :type encoding_type: string

        :rtype: :class:`boto.s3.bucketlistresultset.MultiPartUploadListResultSet`
        :return: an instance of a BucketListResultSet that handles paging, etc
        """
        return MultiPartUploadListResultSet(self, key_marker,
                                            upload_id_marker,
                                            headers,
                                            encoding_type=encoding_type)

    def _get_all_query_args(self, params, initial_query_string=''):
        pairs = []

        if initial_query_string:
            pairs.append(initial_query_string)

        for key, value in sorted(params.items(), key=lambda x: x[0]):
            if value is None:
                continue
            key = key.replace('_', '-')
            if key == 'maxkeys':
                key = 'max-keys'
            if not isinstance(value, six.string_types + (six.binary_type,)):
                value = six.text_type(value)
            if not isinstance(value, six.binary_type):
                value = value.encode('utf-8')
            if value:
                pairs.append(u'%s=%s' % (
                    urllib.parse.quote(key),
                    urllib.parse.quote(value)
                ))

        return '&'.join(pairs)

    def _get_all(self, element_map, initial_query_string='',
                 headers=None, **params):
        query_args = self._get_all_query_args(
            params,
            initial_query_string=initial_query_string
        )
        response = self.connection.make_request('GET', self.name,
                                                headers=headers,
                                                query_args=query_args)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            rs = ResultSet(element_map)
            h = handler.XmlHandler(rs, self)
            if not isinstance(body, bytes):
                body = body.encode('utf-8')
            xml.sax.parseString(body, h)
            return rs
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def validate_kwarg_names(self, kwargs, names):
        """
        Checks that all named arguments are in the specified list of names.

        :type kwargs: dict
        :param kwargs: Dictionary of kwargs to validate.

        :type names: list
        :param names: List of possible named arguments.
        """
        for kwarg in kwargs:
            if kwarg not in names:
                raise TypeError('Invalid argument "%s"!' % kwarg)

    def get_all_keys(self, headers=None, **params):
        """
        A lower-level method for listing contents of a bucket.  This
        closely models the actual S3 API and requires you to manually
        handle the paging of results.  For a higher-level method that
        handles the details of paging for you, you can use the list
        method.

        :type max_keys: int
        :param max_keys: The maximum number of keys to retrieve

        :type prefix: string
        :param prefix: The prefix of the keys you want to retrieve

        :type marker: string
        :param marker: The "marker" of where you are in the result set

        :type delimiter: string
        :param delimiter: If this optional, Unicode string parameter
            is included with your request, then keys that contain the
            same string between the prefix and the first occurrence of
            the delimiter will be rolled up into a single result
            element in the CommonPrefixes collection. These rolled-up
            keys are not returned elsewhere in the response.

        :param encoding_type: Requests Amazon S3 to encode the response and
            specifies the encoding method to use.

            An object key can contain any Unicode character; however, XML 1.0
            parser cannot parse some characters, such as characters with an
            ASCII value from 0 to 10. For characters that are not supported in
            XML 1.0, you can add this parameter to request that Amazon S3
            encode the keys in the response.

            Valid options: ``url``
        :type encoding_type: string

        :rtype: ResultSet
        :return: The result from S3 listing the keys requested

        """
        self.validate_kwarg_names(params, ['maxkeys', 'max_keys', 'prefix',
                                           'marker', 'delimiter',
                                           'encoding_type'])
        return self._get_all([('Contents', self.key_class),
                              ('CommonPrefixes', Prefix)],
                             '', headers, **params)

    def get_all_versions(self, headers=None, **params):
        """
        A lower-level, version-aware method for listing contents of a
        bucket.  This closely models the actual S3 API and requires
        you to manually handle the paging of results.  For a
        higher-level method that handles the details of paging for
        you, you can use the list method.

        :type max_keys: int
        :param max_keys: The maximum number of keys to retrieve

        :type prefix: string
        :param prefix: The prefix of the keys you want to retrieve

        :type key_marker: string
        :param key_marker: The "marker" of where you are in the result set
            with respect to keys.

        :type version_id_marker: string
        :param version_id_marker: The "marker" of where you are in the result
            set with respect to version-id's.

        :type delimiter: string
        :param delimiter: If this optional, Unicode string parameter
            is included with your request, then keys that contain the
            same string between the prefix and the first occurrence of
            the delimiter will be rolled up into a single result
            element in the CommonPrefixes collection. These rolled-up
            keys are not returned elsewhere in the response.

        :param encoding_type: Requests Amazon S3 to encode the response and
            specifies the encoding method to use.

            An object key can contain any Unicode character; however, XML 1.0
            parser cannot parse some characters, such as characters with an
            ASCII value from 0 to 10. For characters that are not supported in
            XML 1.0, you can add this parameter to request that Amazon S3
            encode the keys in the response.

            Valid options: ``url``
        :type encoding_type: string

        :rtype: ResultSet
        :return: The result from S3 listing the keys requested
        """
        self.validate_get_all_versions_params(params)
        return self._get_all([('Version', self.key_class),
                              ('CommonPrefixes', Prefix),
                              ('DeleteMarker', DeleteMarker)],
                             'versions', headers, **params)

    def validate_get_all_versions_params(self, params):
        """
        Validate that the parameters passed to get_all_versions are valid.
        Overridden by subclasses that allow a different set of parameters.

        :type params: dict
        :param params: Parameters to validate.
        """
        self.validate_kwarg_names(
                params, ['maxkeys', 'max_keys', 'prefix', 'key_marker',
                         'version_id_marker', 'delimiter', 'encoding_type'])

    def get_all_multipart_uploads(self, headers=None, **params):
        """
        A lower-level, version-aware method for listing active
        MultiPart uploads for a bucket.  This closely models the
        actual S3 API and requires you to manually handle the paging
        of results.  For a higher-level method that handles the
        details of paging for you, you can use the list method.

        :type max_uploads: int
        :param max_uploads: The maximum number of uploads to retrieve.
            Default value is 1000.

        :type key_marker: string
        :param key_marker: Together with upload_id_marker, this
            parameter specifies the multipart upload after which
            listing should begin.  If upload_id_marker is not
            specified, only the keys lexicographically greater than
            the specified key_marker will be included in the list.

            If upload_id_marker is specified, any multipart uploads
            for a key equal to the key_marker might also be included,
            provided those multipart uploads have upload IDs
            lexicographically greater than the specified
            upload_id_marker.

        :type upload_id_marker: string
        :param upload_id_marker: Together with key-marker, specifies
            the multipart upload after which listing should begin. If
            key_marker is not specified, the upload_id_marker
            parameter is ignored.  Otherwise, any multipart uploads
            for a key equal to the key_marker might be included in the
            list only if they have an upload ID lexicographically
            greater than the specified upload_id_marker.

        :type encoding_type: string
        :param encoding_type: Requests Amazon S3 to encode the response and
            specifies the encoding method to use.

            An object key can contain any Unicode character; however, XML 1.0
            parser cannot parse some characters, such as characters with an
            ASCII value from 0 to 10. For characters that are not supported in
            XML 1.0, you can add this parameter to request that Amazon S3
            encode the keys in the response.

            Valid options: ``url``

        :type delimiter: string
        :param delimiter: Character you use to group keys.
            All keys that contain the same string between the prefix, if
            specified, and the first occurrence of the delimiter after the
            prefix are grouped under a single result element, CommonPrefixes.
            If you don't specify the prefix parameter, then the substring
            starts at the beginning of the key. The keys that are grouped
            under CommonPrefixes result element are not returned elsewhere
            in the response.

        :type prefix: string
        :param prefix: Lists in-progress uploads only for those keys that
            begin with the specified prefix. You can use prefixes to separate
            a bucket into different grouping of keys. (You can think of using
            prefix to make groups in the same way you'd use a folder in a
            file system.)

        :rtype: ResultSet
        :return: The result from S3 listing the uploads requested

        """
        self.validate_kwarg_names(params, ['max_uploads', 'key_marker',
                                           'upload_id_marker', 'encoding_type',
                                           'delimiter', 'prefix'])
        return self._get_all([('Upload', MultiPartUpload),
                              ('CommonPrefixes', Prefix)],
                             'uploads', headers, **params)

    def new_key(self, key_name=None):
        """
        Creates a new key

        :type key_name: string
        :param key_name: The name of the key to create

        :rtype: :class:`boto.s3.key.Key` or subclass
        :returns: An instance of the newly created key object
        """
        if not key_name:
            raise ValueError('Empty key names are not allowed')
        return self.key_class(self, key_name)

    def generate_url(self, expires_in, method='GET', headers=None,
                     force_http=False, response_headers=None,
                     expires_in_absolute=False):
        return self.connection.generate_url(expires_in, method, self.name,
                                            headers=headers,
                                            force_http=force_http,
                                            response_headers=response_headers,
                                            expires_in_absolute=expires_in_absolute)

    def delete_keys(self, keys, quiet=False, mfa_token=None, headers=None):
        """
        Deletes a set of keys using S3's Multi-object delete API. If a
        VersionID is specified for that key then that version is removed.
        Returns a MultiDeleteResult Object, which contains Deleted
        and Error elements for each key you ask to delete.

        :type keys: list
        :param keys: A list of either key_names or (key_name, versionid) pairs
            or a list of Key instances.

        :type quiet: boolean
        :param quiet: In quiet mode the response includes only keys
            where the delete operation encountered an error. For a
            successful deletion, the operation does not return any
            information about the delete in the response body.

        :type mfa_token: tuple or list of strings
        :param mfa_token: A tuple or list consisting of the serial
            number from the MFA device and the current value of the
            six-digit token associated with the device.  This value is
            required anytime you are deleting versioned objects from a
            bucket that has the MFADelete option on the bucket.

        :returns: An instance of MultiDeleteResult
        """
        ikeys = iter(keys)
        result = MultiDeleteResult(self)
        provider = self.connection.provider
        query_args = 'delete'

        def delete_keys2(hdrs):
            hdrs = hdrs or {}
            data = u"""<?xml version="1.0" encoding="UTF-8"?>"""
            data += u"<Delete>"
            if quiet:
                data += u"<Quiet>true</Quiet>"
            count = 0
            while count < 1000:
                try:
                    key = next(ikeys)
                except StopIteration:
                    break
                if isinstance(key, six.string_types):
                    key_name = key
                    version_id = None
                elif isinstance(key, tuple) and len(key) == 2:
                    key_name, version_id = key
                elif (isinstance(key, Key) or isinstance(key, DeleteMarker)) and key.name:
                    key_name = key.name
                    version_id = key.version_id
                else:
                    if isinstance(key, Prefix):
                        key_name = key.name
                        code = 'PrefixSkipped'   # Don't delete Prefix
                    else:
                        key_name = repr(key)   # try get a string
                        code = 'InvalidArgument'  # other unknown type
                    message = 'Invalid. No delete action taken for this object.'
                    error = Error(key_name, code=code, message=message)
                    result.errors.append(error)
                    continue
                count += 1
                data += u"<Object><Key>%s</Key>" % xml.sax.saxutils.escape(key_name)
                if version_id:
                    data += u"<VersionId>%s</VersionId>" % version_id
                data += u"</Object>"
            data += u"</Delete>"
            if count <= 0:
                return False  # no more
            data = data.encode('utf-8')
            fp = BytesIO(data)
            md5 = boto.utils.compute_md5(fp)
            hdrs['Content-MD5'] = md5[1]
            hdrs['Content-Type'] = 'text/xml'
            if mfa_token:
                hdrs[provider.mfa_header] = ' '.join(mfa_token)
            response = self.connection.make_request('POST', self.name,
                                                    headers=hdrs,
                                                    query_args=query_args,
                                                    data=data)
            body = response.read()
            if response.status == 200:
                h = handler.XmlHandler(result, self)
                if not isinstance(body, bytes):
                    body = body.encode('utf-8')
                xml.sax.parseString(body, h)
                return count >= 1000  # more?
            else:
                raise provider.storage_response_error(response.status,
                                                      response.reason,
                                                      body)
        while delete_keys2(headers):
            pass
        return result

    def delete_key(self, key_name, headers=None, version_id=None,
                   mfa_token=None):
        """
        Deletes a key from the bucket.  If a version_id is provided,
        only that version of the key will be deleted.

        :type key_name: string
        :param key_name: The key name to delete

        :type version_id: string
        :param version_id: The version ID (optional)

        :type mfa_token: tuple or list of strings
        :param mfa_token: A tuple or list consisting of the serial
            number from the MFA device and the current value of the
            six-digit token associated with the device.  This value is
            required anytime you are deleting versioned objects from a
            bucket that has the MFADelete option on the bucket.

        :rtype: :class:`boto.s3.key.Key` or subclass
        :returns: A key object holding information on what was
            deleted.  The Caller can see if a delete_marker was
            created or removed and what version_id the delete created
            or removed.
        """
        if not key_name:
            raise ValueError('Empty key names are not allowed')
        return self._delete_key_internal(key_name, headers=headers,
                                         version_id=version_id,
                                         mfa_token=mfa_token,
                                         query_args_l=None)

    def _delete_key_internal(self, key_name, headers=None, version_id=None,
                             mfa_token=None, query_args_l=None):
        query_args_l = query_args_l or []
        provider = self.connection.provider
        if version_id:
            query_args_l.append('versionId=%s' % version_id)
        query_args = '&'.join(query_args_l) or None
        if mfa_token:
            if not headers:
                headers = {}
            headers[provider.mfa_header] = ' '.join(mfa_token)
        response = self.connection.make_request('DELETE', self.name, key_name,
                                                headers=headers,
                                                query_args=query_args)
        body = response.read()
        if response.status != 204:
            raise provider.storage_response_error(response.status,
                                                  response.reason, body)
        else:
            # return a key object with information on what was deleted.
            k = self.key_class(self)
            k.name = key_name
            k.handle_version_headers(response)
            k.handle_addl_headers(response.getheaders())
            return k

    def copy_key(self, new_key_name, src_bucket_name,
                 src_key_name, metadata=None, src_version_id=None,
                 storage_class='STANDARD', preserve_acl=False,
                 encrypt_key=False, headers=None, query_args=None):
        """
        Create a new key in the bucket by copying another existing key.

        :type new_key_name: string
        :param new_key_name: The name of the new key

        :type src_bucket_name: string
        :param src_bucket_name: The name of the source bucket

        :type src_key_name: string
        :param src_key_name: The name of the source key

        :type src_version_id: string
        :param src_version_id: The version id for the key.  This param
            is optional.  If not specified, the newest version of the
            key will be copied.

        :type metadata: dict
        :param metadata: Metadata to be associated with new key.  If
            metadata is supplied, it will replace the metadata of the
            source key being copied.  If no metadata is supplied, the
            source key's metadata will be copied to the new key.

        :type storage_class: string
        :param storage_class: The storage class of the new key.  By
            default, the new key will use the standard storage class.
            Possible values are: STANDARD | REDUCED_REDUNDANCY

        :type preserve_acl: bool
        :param preserve_acl: If True, the ACL from the source key will
            be copied to the destination key.  If False, the
            destination key will have the default ACL.  Note that
            preserving the ACL in the new key object will require two
            additional API calls to S3, one to retrieve the current
            ACL and one to set that ACL on the new object.  If you
            don't care about the ACL, a value of False will be
            significantly more efficient.

        :type encrypt_key: bool
        :param encrypt_key: If True, the new copy of the object will
            be encrypted on the server-side by S3 and will be stored
            in an encrypted form while at rest in S3.

        :type headers: dict
        :param headers: A dictionary of header name/value pairs.

        :type query_args: string
        :param query_args: A string of additional querystring arguments
            to append to the request

        :rtype: :class:`boto.s3.key.Key` or subclass
        :returns: An instance of the newly created key object
        """
        headers = headers or {}
        provider = self.connection.provider
        src_key_name = get_utf8able_str(src_key_name)
        
        if preserve_acl:
            if self.name == src_bucket_name:
                src_bucket = self
            else:
                src_bucket = self.connection.get_bucket(
                    src_bucket_name, validate=False, headers=headers)
            acl = src_bucket.get_xml_acl(src_key_name, headers=headers)
        if encrypt_key:
            headers[provider.server_side_encryption_header] = 'AES256'
        src = '%s/%s' % (src_bucket_name, urllib.parse.quote(src_key_name))
        if src_version_id:
            src += '?versionId=%s' % src_version_id
        headers[provider.copy_source_header] = str(src)
        # make sure storage_class_header key exists before accessing it
        if provider.storage_class_header and storage_class:
            headers[provider.storage_class_header] = storage_class
        if metadata is not None:
            headers[provider.metadata_directive_header] = 'REPLACE'
            headers = boto.utils.merge_meta(headers, metadata, provider)
        elif not query_args:  # Can't use this header with multi-part copy.
            headers[provider.metadata_directive_header] = 'COPY'
        response = self.connection.make_request('PUT', self.name, new_key_name,
                                                headers=headers,
                                                query_args=query_args)
        body = response.read()
        if response.status == 200:
            key = self.new_key(new_key_name)
            h = handler.XmlHandler(key, self)
            xml.sax.parseString(body, h)
            if hasattr(key, 'Error'):
                raise provider.storage_copy_error(key.Code, key.Message, body)
            key.handle_version_headers(response)
            key.handle_addl_headers(response.getheaders())
            if preserve_acl:
                self.set_xml_acl(acl, new_key_name)
            return key
        else:
            raise provider.storage_response_error(response.status,
                                                  response.reason, body)

    def set_canned_acl(self, acl_str, key_name='', headers=None,
                       version_id=None):
        assert acl_str in CannedACLStrings

        if headers:
            headers[self.connection.provider.acl_header] = acl_str
        else:
            headers = {self.connection.provider.acl_header: acl_str}

        query_args = 'acl'
        if version_id:
            query_args += '&versionId=%s' % version_id
        response = self.connection.make_request('PUT', self.name, key_name,
                headers=headers, query_args=query_args)
        body = response.read()
        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def get_xml_acl(self, key_name='', headers=None, version_id=None):
        query_args = 'acl'
        if version_id:
            query_args += '&versionId=%s' % version_id
        response = self.connection.make_request('GET', self.name, key_name,
                                                query_args=query_args,
                                                headers=headers)
        body = response.read()
        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)
        return body

    def set_xml_acl(self, acl_str, key_name='', headers=None, version_id=None,
                    query_args='acl'):
        if version_id:
            query_args += '&versionId=%s' % version_id
        if not isinstance(acl_str, bytes):
            acl_str = acl_str.encode('utf-8')
        response = self.connection.make_request('PUT', self.name, key_name,
                                                data=acl_str,
                                                query_args=query_args,
                                                headers=headers)
        body = response.read()
        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def set_acl(self, acl_or_str, key_name='', headers=None, version_id=None):
        if isinstance(acl_or_str, Policy):
            self.set_xml_acl(acl_or_str.to_xml(), key_name,
                             headers, version_id)
        else:
            self.set_canned_acl(acl_or_str, key_name,
                                headers, version_id)

    def get_acl(self, key_name='', headers=None, version_id=None):
        query_args = 'acl'
        if version_id:
            query_args += '&versionId=%s' % version_id
        response = self.connection.make_request('GET', self.name, key_name,
                                                query_args=query_args,
                                                headers=headers)
        body = response.read()
        if response.status == 200:
            policy = Policy(self)
            h = handler.XmlHandler(policy, self)
            if not isinstance(body, bytes):
                body = body.encode('utf-8')
            xml.sax.parseString(body, h)
            return policy
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def set_subresource(self, subresource, value, key_name='', headers=None,
                        version_id=None):
        """
        Set a subresource for a bucket or key.

        :type subresource: string
        :param subresource: The subresource to set.

        :type value: string
        :param value: The value of the subresource.

        :type key_name: string
        :param key_name: The key to operate on, or None to operate on the
            bucket.

        :type headers: dict
        :param headers: Additional HTTP headers to include in the request.

        :type src_version_id: string
        :param src_version_id: Optional. The version id of the key to
            operate on. If not specified, operate on the newest
            version.
        """
        if not subresource:
            raise TypeError('set_subresource called with subresource=None')
        query_args = subresource
        if version_id:
            query_args += '&versionId=%s' % version_id
        if not isinstance(value, bytes):
            value = value.encode('utf-8')
        response = self.connection.make_request('PUT', self.name, key_name,
                                                data=value,
                                                query_args=query_args,
                                                headers=headers)
        body = response.read()
        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def get_subresource(self, subresource, key_name='', headers=None,
                        version_id=None):
        """
        Get a subresource for a bucket or key.

        :type subresource: string
        :param subresource: The subresource to get.

        :type key_name: string
        :param key_name: The key to operate on, or None to operate on the
            bucket.

        :type headers: dict
        :param headers: Additional HTTP headers to include in the request.

        :type src_version_id: string
        :param src_version_id: Optional. The version id of the key to
            operate on. If not specified, operate on the newest
            version.

        :rtype: string
        :returns: The value of the subresource.
        """
        if not subresource:
            raise TypeError('get_subresource called with subresource=None')
        query_args = subresource
        if version_id:
            query_args += '&versionId=%s' % version_id
        response = self.connection.make_request('GET', self.name, key_name,
                                                query_args=query_args,
                                                headers=headers)
        body = response.read()
        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)
        return body

    def make_public(self, recursive=False, headers=None):
        self.set_canned_acl('public-read', headers=headers)
        if recursive:
            for key in self:
                self.set_canned_acl('public-read', key.name, headers=headers)

    def add_email_grant(self, permission, email_address,
                        recursive=False, headers=None):
        """
        Convenience method that provides a quick way to add an email grant
        to a bucket. This method retrieves the current ACL, creates a new
        grant based on the parameters passed in, adds that grant to the ACL
        and then PUT's the new ACL back to S3.

        :type permission: string
        :param permission: The permission being granted. Should be one of:
            (READ, WRITE, READ_ACP, WRITE_ACP, FULL_CONTROL).

        :type email_address: string
        :param email_address: The email address associated with the AWS
            account your are granting the permission to.

        :type recursive: boolean
        :param recursive: A boolean value to controls whether the
            command will apply the grant to all keys within the bucket
            or not.  The default value is False.  By passing a True
            value, the call will iterate through all keys in the
            bucket and apply the same grant to each key.  CAUTION: If
            you have a lot of keys, this could take a long time!
        """
        if permission not in S3Permissions:
            raise self.connection.provider.storage_permissions_error(
                'Unknown Permission: %s' % permission)
        policy = self.get_acl(headers=headers)
        policy.acl.add_email_grant(permission, email_address)
        self.set_acl(policy, headers=headers)
        if recursive:
            for key in self:
                key.add_email_grant(permission, email_address, headers=headers)

    def add_user_grant(self, permission, user_id, recursive=False,
                       headers=None, display_name=None):
        """
        Convenience method that provides a quick way to add a canonical
        user grant to a bucket.  This method retrieves the current ACL,
        creates a new grant based on the parameters passed in, adds that
        grant to the ACL and then PUT's the new ACL back to S3.

        :type permission: string
        :param permission: The permission being granted. Should be one of:
            (READ, WRITE, READ_ACP, WRITE_ACP, FULL_CONTROL).

        :type user_id: string
        :param user_id:     The canonical user id associated with the AWS
            account your are granting the permission to.

        :type recursive: boolean
        :param recursive: A boolean value to controls whether the
            command will apply the grant to all keys within the bucket
            or not.  The default value is False.  By passing a True
            value, the call will iterate through all keys in the
            bucket and apply the same grant to each key.  CAUTION: If
            you have a lot of keys, this could take a long time!

        :type display_name: string
        :param display_name: An option string containing the user's
            Display Name.  Only required on Walrus.
        """
        if permission not in S3Permissions:
            raise self.connection.provider.storage_permissions_error(
                'Unknown Permission: %s' % permission)
        policy = self.get_acl(headers=headers)
        policy.acl.add_user_grant(permission, user_id,
                                  display_name=display_name)
        self.set_acl(policy, headers=headers)
        if recursive:
            for key in self:
                key.add_user_grant(permission, user_id, headers=headers,
                                   display_name=display_name)

    def list_grants(self, headers=None):
        policy = self.get_acl(headers=headers)
        return policy.acl.grants

    def get_location(self, headers=None):
        """
        Returns the LocationConstraint for the bucket.

        :rtype: str
        :return: The LocationConstraint for the bucket or the empty
            string if no constraint was specified when bucket was created.
        """
        response = self.connection.make_request('GET', self.name,
                                                headers=headers,
                                                query_args='location')
        body = response.read()
        if response.status == 200:
            rs = ResultSet(self)
            h = handler.XmlHandler(rs, self)
            if not isinstance(body, bytes):
                body = body.encode('utf-8')
            xml.sax.parseString(body, h)
            return rs.LocationConstraint
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def set_xml_logging(self, logging_str, headers=None):
        """
        Set logging on a bucket directly to the given xml string.

        :type logging_str: unicode string
        :param logging_str: The XML for the bucketloggingstatus which
            will be set.  The string will be converted to utf-8 before
            it is sent.  Usually, you will obtain this XML from the
            BucketLogging object.

        :rtype: bool
        :return: True if ok or raises an exception.
        """
        body = logging_str
        if not isinstance(body, bytes):
            body = body.encode('utf-8')
        response = self.connection.make_request('PUT', self.name, data=body,
                query_args='logging', headers=headers)
        body = response.read()
        if response.status == 200:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def enable_logging(self, target_bucket, target_prefix='',
                       grants=None, headers=None):
        """
        Enable logging on a bucket.

        :type target_bucket: bucket or string
        :param target_bucket: The bucket to log to.

        :type target_prefix: string
        :param target_prefix: The prefix which should be prepended to the
            generated log files written to the target_bucket.

        :type grants: list of Grant objects
        :param grants: A list of extra permissions which will be granted on
            the log files which are created.

        :rtype: bool
        :return: True if ok or raises an exception.
        """
        if isinstance(target_bucket, Bucket):
            target_bucket = target_bucket.name
        blogging = BucketLogging(target=target_bucket, prefix=target_prefix,
                                 grants=grants)
        return self.set_xml_logging(blogging.to_xml(), headers=headers)

    def disable_logging(self, headers=None):
        """
        Disable logging on a bucket.

        :rtype: bool
        :return: True if ok or raises an exception.
        """
        blogging = BucketLogging()
        return self.set_xml_logging(blogging.to_xml(), headers=headers)

    def get_logging_status(self, headers=None):
        """
        Get the logging status for this bucket.

        :rtype: :class:`boto.s3.bucketlogging.BucketLogging`
        :return: A BucketLogging object for this bucket.
        """
        response = self.connection.make_request('GET', self.name,
                query_args='logging', headers=headers)
        body = response.read()
        if response.status == 200:
            blogging = BucketLogging()
            h = handler.XmlHandler(blogging, self)
            if not isinstance(body, bytes):
                body = body.encode('utf-8')
            xml.sax.parseString(body, h)
            return blogging
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def set_as_logging_target(self, headers=None):
        """
        Setup the current bucket as a logging target by granting the necessary
        permissions to the LogDelivery group to write log files to this bucket.
        """
        policy = self.get_acl(headers=headers)
        g1 = Grant(permission='WRITE', type='Group', uri=self.LoggingGroup)
        g2 = Grant(permission='READ_ACP', type='Group', uri=self.LoggingGroup)
        policy.acl.add_grant(g1)
        policy.acl.add_grant(g2)
        self.set_acl(policy, headers=headers)

    def get_request_payment(self, headers=None):
        response = self.connection.make_request('GET', self.name,
                query_args='requestPayment', headers=headers)
        body = response.read()
        if response.status == 200:
            return body
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def set_request_payment(self, payer='BucketOwner', headers=None):
        body = self.BucketPaymentBody % payer
        response = self.connection.make_request('PUT', self.name, data=body,
                query_args='requestPayment', headers=headers)
        body = response.read()
        if response.status == 200:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def configure_versioning(self, versioning, mfa_delete=False,
                             mfa_token=None, headers=None):
        """
        Configure versioning for this bucket.

        ..note:: This feature is currently in beta.

        :type versioning: bool
        :param versioning: A boolean indicating whether version is
            enabled (True) or disabled (False).

        :type mfa_delete: bool
        :param mfa_delete: A boolean indicating whether the
            Multi-Factor Authentication Delete feature is enabled
            (True) or disabled (False).  If mfa_delete is enabled then
            all Delete operations will require the token from your MFA
            device to be passed in the request.

        :type mfa_token: tuple or list of strings
        :param mfa_token: A tuple or list consisting of the serial
            number from the MFA device and the current value of the
            six-digit token associated with the device.  This value is
            required when you are changing the status of the MfaDelete
            property of the bucket.
        """
        if versioning:
            ver = 'Enabled'
        else:
            ver = 'Suspended'
        if mfa_delete:
            mfa = 'Enabled'
        else:
            mfa = 'Disabled'
        body = self.VersioningBody % (ver, mfa)
        if mfa_token:
            if not headers:
                headers = {}
            provider = self.connection.provider
            headers[provider.mfa_header] = ' '.join(mfa_token)
        response = self.connection.make_request('PUT', self.name, data=body,
                query_args='versioning', headers=headers)
        body = response.read()
        if response.status == 200:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def get_versioning_status(self, headers=None):
        """
        Returns the current status of versioning on the bucket.

        :rtype: dict
        :returns: A dictionary containing a key named 'Versioning'
            that can have a value of either Enabled, Disabled, or
            Suspended. Also, if MFADelete has ever been enabled on the
            bucket, the dictionary will contain a key named
            'MFADelete' which will have a value of either Enabled or
            Suspended.
        """
        response = self.connection.make_request('GET', self.name,
                query_args='versioning', headers=headers)
        body = response.read()
        if not isinstance(body, six.string_types):
            body = body.decode('utf-8')
        boto.log.debug(body)
        if response.status == 200:
            d = {}
            ver = re.search(self.VersionRE, body)
            if ver:
                d['Versioning'] = ver.group(1)
            mfa = re.search(self.MFADeleteRE, body)
            if mfa:
                d['MfaDelete'] = mfa.group(1)
            return d
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def configure_lifecycle(self, lifecycle_config, headers=None):
        """
        Configure lifecycle for this bucket.

        :type lifecycle_config: :class:`boto.s3.lifecycle.Lifecycle`
        :param lifecycle_config: The lifecycle configuration you want
            to configure for this bucket.
        """
        xml = lifecycle_config.to_xml()
        #xml = xml.encode('utf-8')
        fp = StringIO(xml)
        md5 = boto.utils.compute_md5(fp)
        if headers is None:
            headers = {}
        headers['Content-MD5'] = md5[1]
        headers['Content-Type'] = 'text/xml'
        response = self.connection.make_request('PUT', self.name,
                                                data=fp.getvalue(),
                                                query_args='lifecycle',
                                                headers=headers)
        body = response.read()
        if response.status == 200:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def get_lifecycle_config(self, headers=None):
        """
        Returns the current lifecycle configuration on the bucket.

        :rtype: :class:`boto.s3.lifecycle.Lifecycle`
        :returns: A LifecycleConfig object that describes all current
            lifecycle rules in effect for the bucket.
        """
        response = self.connection.make_request('GET', self.name,
                query_args='lifecycle', headers=headers)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            lifecycle = Lifecycle()
            h = handler.XmlHandler(lifecycle, self)
            if not isinstance(body, bytes):
                body = body.encode('utf-8')
            xml.sax.parseString(body, h)
            return lifecycle
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def delete_lifecycle_configuration(self, headers=None):
        """
        Removes all lifecycle configuration from the bucket.
        """
        response = self.connection.make_request('DELETE', self.name,
                                                query_args='lifecycle',
                                                headers=headers)
        body = response.read()
        boto.log.debug(body)
        if response.status == 204:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def configure_website(self, suffix=None, error_key=None,
                          redirect_all_requests_to=None,
                          routing_rules=None,
                          headers=None):
        """
        Configure this bucket to act as a website

        :type suffix: str
        :param suffix: Suffix that is appended to a request that is for a
            "directory" on the website endpoint (e.g. if the suffix is
            index.html and you make a request to samplebucket/images/
            the data that is returned will be for the object with the
            key name images/index.html).  The suffix must not be empty
            and must not include a slash character.

        :type error_key: str
        :param error_key: The object key name to use when a 4XX class
            error occurs.  This is optional.

        :type redirect_all_requests_to: :class:`boto.s3.website.RedirectLocation`
        :param redirect_all_requests_to: Describes the redirect behavior for
            every request to this bucket's website endpoint. If this value is
            non None, no other values are considered when configuring the
            website configuration for the bucket. This is an instance of
            ``RedirectLocation``.

        :type routing_rules: :class:`boto.s3.website.RoutingRules`
        :param routing_rules: Object which specifies conditions
            and redirects that apply when the conditions are met.

        """
        config = website.WebsiteConfiguration(
                suffix, error_key, redirect_all_requests_to,
                routing_rules)
        return self.set_website_configuration(config, headers=headers)

    def set_website_configuration(self, config, headers=None):
        """
        :type config: boto.s3.website.WebsiteConfiguration
        :param config: Configuration data
        """
        return self.set_website_configuration_xml(config.to_xml(),
          headers=headers)


    def set_website_configuration_xml(self, xml, headers=None):
        """Upload xml website configuration"""
        response = self.connection.make_request('PUT', self.name, data=xml,
                                                query_args='website',
                                                headers=headers)
        body = response.read()
        if response.status == 200:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def get_website_configuration(self, headers=None):
        """
        Returns the current status of website configuration on the bucket.

        :rtype: dict
        :returns: A dictionary containing a Python representation
            of the XML response from S3. The overall structure is:

        * WebsiteConfiguration

          * IndexDocument

            * Suffix : suffix that is appended to request that
              is for a "directory" on the website endpoint
            * ErrorDocument

              * Key : name of object to serve when an error occurs

        """
        return self.get_website_configuration_with_xml(headers)[0]

    def get_website_configuration_obj(self, headers=None):
        """Get the website configuration as a
        :class:`boto.s3.website.WebsiteConfiguration` object.
        """
        config_xml = self.get_website_configuration_xml(headers=headers)
        config = website.WebsiteConfiguration()
        h = handler.XmlHandler(config, self)
        xml.sax.parseString(config_xml, h)
        return config

    def get_website_configuration_with_xml(self, headers=None):
        """
        Returns the current status of website configuration on the bucket as
        unparsed XML.

        :rtype: 2-Tuple
        :returns: 2-tuple containing:

            1) A dictionary containing a Python representation \
                of the XML response. The overall structure is:

              * WebsiteConfiguration

                * IndexDocument

                  * Suffix : suffix that is appended to request that \
                    is for a "directory" on the website endpoint

                  * ErrorDocument

                    * Key : name of object to serve when an error occurs


            2) unparsed XML describing the bucket's website configuration

        """

        body = self.get_website_configuration_xml(headers=headers)
        e = boto.jsonresponse.Element()
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        return e, body

    def get_website_configuration_xml(self, headers=None):
        """Get raw website configuration xml"""
        response = self.connection.make_request('GET', self.name,
                query_args='website', headers=headers)
        body = response.read().decode('utf-8')
        boto.log.debug(body)

        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)
        return body

    def delete_website_configuration(self, headers=None):
        """
        Removes all website configuration from the bucket.
        """
        response = self.connection.make_request('DELETE', self.name,
                query_args='website', headers=headers)
        body = response.read()
        boto.log.debug(body)
        if response.status == 204:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def get_website_endpoint(self):
        """
        Returns the fully qualified hostname to use is you want to access this
        bucket as a website.  This doesn't validate whether the bucket has
        been correctly configured as a website or not.
        """
        l = [self.name]
        l.append(S3WebsiteEndpointTranslate.translate_region(self.get_location()))
        l.append('.'.join(self.connection.host.split('.')[-2:]))
        return '.'.join(l)

    def get_policy(self, headers=None):
        """
        Returns the JSON policy associated with the bucket.  The policy
        is returned as an uninterpreted JSON string.
        """
        response = self.connection.make_request('GET', self.name,
                query_args='policy', headers=headers)
        body = response.read()
        if response.status == 200:
            return body
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def set_policy(self, policy, headers=None):
        """
        Add or replace the JSON policy associated with the bucket.

        :type policy: str
        :param policy: The JSON policy as a string.
        """
        response = self.connection.make_request('PUT', self.name,
                                                data=policy,
                                                query_args='policy',
                                                headers=headers)
        body = response.read()
        if response.status >= 200 and response.status <= 204:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def delete_policy(self, headers=None):
        response = self.connection.make_request('DELETE', self.name,
                                                data='/?policy',
                                                query_args='policy',
                                                headers=headers)
        body = response.read()
        if response.status >= 200 and response.status <= 204:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def set_cors_xml(self, cors_xml, headers=None):
        """
        Set the CORS (Cross-Origin Resource Sharing) for a bucket.

        :type cors_xml: str
        :param cors_xml: The XML document describing your desired
            CORS configuration.  See the S3 documentation for details
            of the exact syntax required.
        """
        fp = StringIO(cors_xml)
        md5 = boto.utils.compute_md5(fp)
        if headers is None:
            headers = {}
        headers['Content-MD5'] = md5[1]
        headers['Content-Type'] = 'text/xml'
        response = self.connection.make_request('PUT', self.name,
                                                data=fp.getvalue(),
                                                query_args='cors',
                                                headers=headers)
        body = response.read()
        if response.status == 200:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def set_cors(self, cors_config, headers=None):
        """
        Set the CORS for this bucket given a boto CORSConfiguration
        object.

        :type cors_config: :class:`boto.s3.cors.CORSConfiguration`
        :param cors_config: The CORS configuration you want
            to configure for this bucket.
        """
        return self.set_cors_xml(cors_config.to_xml())

    def get_cors_xml(self, headers=None):
        """
        Returns the current CORS configuration on the bucket as an
        XML document.
        """
        response = self.connection.make_request('GET', self.name,
                query_args='cors', headers=headers)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            return body
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def get_cors(self, headers=None):
        """
        Returns the current CORS configuration on the bucket.

        :rtype: :class:`boto.s3.cors.CORSConfiguration`
        :returns: A CORSConfiguration object that describes all current
            CORS rules in effect for the bucket.
        """
        body = self.get_cors_xml(headers)
        cors = CORSConfiguration()
        h = handler.XmlHandler(cors, self)
        xml.sax.parseString(body, h)
        return cors

    def delete_cors(self, headers=None):
        """
        Removes all CORS configuration from the bucket.
        """
        response = self.connection.make_request('DELETE', self.name,
                                                query_args='cors',
                                                headers=headers)
        body = response.read()
        boto.log.debug(body)
        if response.status == 204:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def initiate_multipart_upload(self, key_name, headers=None,
                                  reduced_redundancy=False,
                                  metadata=None, encrypt_key=False,
                                  policy=None):
        """
        Start a multipart upload operation.

        .. note::

            Note: After you initiate multipart upload and upload one or more
            parts, you must either complete or abort multipart upload in order
            to stop getting charged for storage of the uploaded parts. Only
            after you either complete or abort multipart upload, Amazon S3
            frees up the parts storage and stops charging you for the parts
            storage.

        :type key_name: string
        :param key_name: The name of the key that will ultimately
            result from this multipart upload operation.  This will be
            exactly as the key appears in the bucket after the upload
            process has been completed.

        :type headers: dict
        :param headers: Additional HTTP headers to send and store with the
            resulting key in S3.

        :type reduced_redundancy: boolean
        :param reduced_redundancy: In multipart uploads, the storage
            class is specified when initiating the upload, not when
            uploading individual parts.  So if you want the resulting
            key to use the reduced redundancy storage class set this
            flag when you initiate the upload.

        :type metadata: dict
        :param metadata: Any metadata that you would like to set on the key
            that results from the multipart upload.

        :type encrypt_key: bool
        :param encrypt_key: If True, the new copy of the object will
            be encrypted on the server-side by S3 and will be stored
            in an encrypted form while at rest in S3.

        :type policy: :class:`boto.s3.acl.CannedACLStrings`
        :param policy: A canned ACL policy that will be applied to the
            new key (once completed) in S3.
        """
        query_args = 'uploads'
        provider = self.connection.provider
        headers = headers or {}
        if policy:
            headers[provider.acl_header] = policy
        if reduced_redundancy:
            storage_class_header = provider.storage_class_header
            if storage_class_header:
                headers[storage_class_header] = 'REDUCED_REDUNDANCY'
            # TODO: what if the provider doesn't support reduced redundancy?
            # (see boto.s3.key.Key.set_contents_from_file)
        if encrypt_key:
            headers[provider.server_side_encryption_header] = 'AES256'
        if metadata is None:
            metadata = {}

        headers = boto.utils.merge_meta(headers, metadata,
                self.connection.provider)
        response = self.connection.make_request('POST', self.name, key_name,
                                                query_args=query_args,
                                                headers=headers)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            resp = MultiPartUpload(self)
            h = handler.XmlHandler(resp, self)
            if not isinstance(body, bytes):
                body = body.encode('utf-8')
            xml.sax.parseString(body, h)
            return resp
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def complete_multipart_upload(self, key_name, upload_id,
                                  xml_body, headers=None):
        """
        Complete a multipart upload operation.
        """
        query_args = 'uploadId=%s' % upload_id
        if headers is None:
            headers = {}
        headers['Content-Type'] = 'text/xml'
        response = self.connection.make_request('POST', self.name, key_name,
                                                query_args=query_args,
                                                headers=headers, data=xml_body)
        contains_error = False
        body = response.read().decode('utf-8')
        # Some errors will be reported in the body of the response
        # even though the HTTP response code is 200.  This check
        # does a quick and dirty peek in the body for an error element.
        if body.find('<Error>') > 0:
            contains_error = True
        boto.log.debug(body)
        if response.status == 200 and not contains_error:
            resp = CompleteMultiPartUpload(self)
            h = handler.XmlHandler(resp, self)
            if not isinstance(body, bytes):
                body = body.encode('utf-8')
            xml.sax.parseString(body, h)
            # Use a dummy key to parse various response headers
            # for versioning, encryption info and then explicitly
            # set the completed MPU object values from key.
            k = self.key_class(self)
            k.handle_version_headers(response)
            k.handle_encryption_headers(response)
            resp.version_id = k.version_id
            resp.encrypted = k.encrypted
            return resp
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def cancel_multipart_upload(self, key_name, upload_id, headers=None):
        """
        To verify that all parts have been removed, so you don't get charged
        for the part storage, you should call the List Parts operation and
        ensure the parts list is empty.
        """
        query_args = 'uploadId=%s' % upload_id
        response = self.connection.make_request('DELETE', self.name, key_name,
                                                query_args=query_args,
                                                headers=headers)
        body = response.read()
        boto.log.debug(body)
        if response.status != 204:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def delete(self, headers=None):
        return self.connection.delete_bucket(self.name, headers=headers)

    def get_tags(self, headers=None):
        response = self.get_xml_tags(headers)
        tags = Tags()
        h = handler.XmlHandler(tags, self)
        if not isinstance(response, bytes):
            response = response.encode('utf-8')
        xml.sax.parseString(response, h)
        return tags

    def get_xml_tags(self, headers=None):
        response = self.connection.make_request('GET', self.name,
                                                query_args='tagging',
                                                headers=headers)
        body = response.read()
        if response.status == 200:
            return body
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def set_xml_tags(self, tag_str, headers=None, query_args='tagging'):
        if headers is None:
            headers = {}
        md5 = boto.utils.compute_md5(StringIO(tag_str))
        headers['Content-MD5'] = md5[1]
        headers['Content-Type'] = 'text/xml'
        if not isinstance(tag_str, bytes):
            tag_str = tag_str.encode('utf-8')
        response = self.connection.make_request('PUT', self.name,
                                                data=tag_str,
                                                query_args=query_args,
                                                headers=headers)
        body = response.read()
        if response.status != 204:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)
        return True

    def set_tags(self, tags, headers=None):
        return self.set_xml_tags(tags.to_xml(), headers=headers)

    def delete_tags(self, headers=None):
        response = self.connection.make_request('DELETE', self.name,
                                                query_args='tagging',
                                                headers=headers)
        body = response.read()
        boto.log.debug(body)
        if response.status == 204:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)
