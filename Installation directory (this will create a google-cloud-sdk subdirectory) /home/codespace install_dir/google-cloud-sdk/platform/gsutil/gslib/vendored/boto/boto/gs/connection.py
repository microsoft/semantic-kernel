# Copyright 2010 Google Inc.
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
from boto.gs.bucket import Bucket
from boto.s3.connection import S3Connection
from boto.s3.connection import SubdomainCallingFormat
from boto.s3.connection import check_lowercase_bucketname
from boto.compat import six
from boto.utils import get_utf8able_str

class Location(object):
    DEFAULT = 'US'
    EU = 'EU'

class GSConnection(S3Connection):

    DefaultHost = 'storage.googleapis.com'
    DefaultCallingFormat = 'boto.s3.connection.OrdinaryCallingFormat'
    QueryString = 'Signature=%s&Expires=%d&GoogleAccessId=%s'

    def __init__(self, gs_access_key_id=None, gs_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None,
                 host=DefaultHost, debug=0, https_connection_factory=None,
                 calling_format=None, path='/', suppress_consec_slashes=True):
        super(GSConnection, self).__init__(gs_access_key_id, gs_secret_access_key,
                 is_secure, port, proxy, proxy_port, proxy_user, proxy_pass,
                 host, debug, https_connection_factory, calling_format, path,
                 "google", Bucket,
                 suppress_consec_slashes=suppress_consec_slashes)

    def _required_auth_capability(self):
        """
        Overrides the S3 version of this method to remove the
        @detect_potential_s3sigv4 decorator to avoid sending v4 headers to
        gcs.
        """
        if self.anon:
            return ['anon']
        else:
            return ['s3']

    def create_bucket(self, bucket_name, headers=None,
                      location=Location.DEFAULT, policy=None,
                      storage_class='STANDARD'):
        """
        Creates a new bucket. By default it's located in the USA. You can
        pass Location.EU to create bucket in the EU. You can also pass
        a LocationConstraint for where the bucket should be located, and
        a StorageClass describing how the data should be stored.

        :type bucket_name: string
        :param bucket_name: The name of the new bucket.

        :type headers: dict
        :param headers: Additional headers to pass along with the request to GCS.

        :type location: :class:`boto.gs.connection.Location`
        :param location: The location of the new bucket.

        :type policy: :class:`boto.gs.acl.CannedACLStrings`
        :param policy: A canned ACL policy that will be applied to the new key
                       in GCS.

        :type storage_class: string
        :param storage_class: Either 'STANDARD' or 'DURABLE_REDUCED_AVAILABILITY'.

        """
        check_lowercase_bucketname(bucket_name)

        if policy:
            if headers:
                headers[self.provider.acl_header] = policy
            else:
                headers = {self.provider.acl_header : policy}
        if not location:
            location = Location.DEFAULT
        location_elem = ('<LocationConstraint>%s</LocationConstraint>'
                         % location)
        if storage_class:
            storage_class_elem = ('<StorageClass>%s</StorageClass>'
                                  % storage_class)
        else:
            storage_class_elem = ''
        data = ('<CreateBucketConfiguration>%s%s</CreateBucketConfiguration>'
                 % (location_elem, storage_class_elem))
        response = self.make_request(
            'PUT', get_utf8able_str(bucket_name), headers=headers,
            data=get_utf8able_str(data))
        body = response.read()
        if response.status == 409:
            raise self.provider.storage_create_error(
                response.status, response.reason, body)
        if response.status == 200:
            return self.bucket_class(self, bucket_name)
        else:
            raise self.provider.storage_response_error(
                response.status, response.reason, body)

    def get_bucket(self, bucket_name, validate=True, headers=None):
        """
        Retrieves a bucket by name.

        If the bucket does not exist, an ``S3ResponseError`` will be raised. If
        you are unsure if the bucket exists or not, you can use the
        ``S3Connection.lookup`` method, which will either return a valid bucket
        or ``None``.

        :type bucket_name: string
        :param bucket_name: The name of the bucket

        :type headers: dict
        :param headers: Additional headers to pass along with the request to
            AWS.

        :type validate: boolean
        :param validate: If ``True``, it will try to fetch all keys within the
            given bucket. (Default: ``True``)
        """
        bucket = self.bucket_class(self, bucket_name)
        if validate:
            bucket.get_all_keys(headers, maxkeys=0)
        return bucket
