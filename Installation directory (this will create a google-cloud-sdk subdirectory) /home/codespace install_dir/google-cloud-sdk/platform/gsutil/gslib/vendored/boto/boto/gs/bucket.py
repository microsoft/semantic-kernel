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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import xml.sax

import boto
from boto import handler
from boto.resultset import ResultSet
from boto.exception import GSResponseError
from boto.exception import InvalidAclError
from boto.gs.acl import ACL, CannedACLStrings
from boto.gs.acl import SupportedPermissions as GSPermissions
from boto.gs.bucketlistresultset import VersionedBucketListResultSet
from boto.gs.cors import Cors
from boto.gs.encryptionconfig import EncryptionConfig
from boto.gs.lifecycle import LifecycleConfig
from boto.gs.key import Key as GSKey
from boto.s3.acl import Policy
from boto.s3.bucket import Bucket as S3Bucket
from boto.utils import get_utf8able_str
from boto.compat import quote
from boto.compat import six

# constants for http query args
DEF_OBJ_ACL = 'defaultObjectAcl'
STANDARD_ACL = 'acl'
CORS_ARG = 'cors'
ENCRYPTION_CONFIG_ARG = 'encryptionConfig'
LIFECYCLE_ARG = 'lifecycle'
STORAGE_CLASS_ARG='storageClass'
_ERROR_DETAILS_REGEX_STR = r'<Details>(?P<details>.*)</Details>'
if six.PY3:
    _ERROR_DETAILS_REGEX_STR = _ERROR_DETAILS_REGEX_STR.encode('ascii')
ERROR_DETAILS_REGEX = re.compile(_ERROR_DETAILS_REGEX_STR)


class Bucket(S3Bucket):
    """Represents a Google Cloud Storage bucket."""

    BillingBody = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<BillingConfiguration>'
                   '<RequesterPays>%s</RequesterPays>'
                   '</BillingConfiguration>')
    EncryptionConfigBody = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<EncryptionConfiguration>%s</EncryptionConfiguration>')
    EncryptionConfigDefaultKeyNameFragment = (
        '<DefaultKmsKeyName>%s</DefaultKmsKeyName>')
    StorageClassBody = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                        '<StorageClass>%s</StorageClass>')
    VersioningBody = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                      '<VersioningConfiguration>'
                      '<Status>%s</Status>'
                      '</VersioningConfiguration>')
    WebsiteBody = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                   '<WebsiteConfiguration>%s%s</WebsiteConfiguration>')
    WebsiteMainPageFragment = '<MainPageSuffix>%s</MainPageSuffix>'
    WebsiteErrorFragment = '<NotFoundPage>%s</NotFoundPage>'

    def __init__(self, connection=None, name=None, key_class=GSKey):
        super(Bucket, self).__init__(connection, name, key_class)

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Name':
            self.name = value
        elif name == 'CreationDate':
            self.creation_date = value
        else:
            setattr(self, name, value)

    def get_key(self, key_name, headers=None, version_id=None,
                response_headers=None, generation=None):
        """Returns a Key instance for an object in this bucket.

         Note that this method uses a HEAD request to check for the existence of
         the key.

        :type key_name: string
        :param key_name: The name of the key to retrieve

        :type response_headers: dict
        :param response_headers: A dictionary containing HTTP
            headers/values that will override any headers associated
            with the stored object in the response.  See
            http://goo.gl/06N3b for details.

        :type version_id: string
        :param version_id: Unused in this subclass.

        :type generation: int
        :param generation: A specific generation number to fetch the key at. If
            not specified, the latest generation is fetched.

        :rtype: :class:`boto.gs.key.Key`
        :returns: A Key object from this bucket.
        """
        query_args_l = []
        if generation:
            query_args_l.append('generation=%s' % generation)
        if response_headers:
            for rk, rv in six.iteritems(response_headers):
                query_args_l.append('%s=%s' % (rk, quote(rv)))
        try:
            key, resp = self._get_key_internal(key_name, headers,
                                               query_args_l=query_args_l)
        except GSResponseError as e:
            if e.status == 403 and 'Forbidden' in e.reason:
                # If we failed getting an object, let the user know which object
                # failed rather than just returning a generic 403.
                e.reason = ("Access denied to 'gs://%s/%s'." %
                            (self.name, key_name))
            raise
        return key

    def copy_key(self, new_key_name, src_bucket_name, src_key_name,
                 metadata=None, src_version_id=None, storage_class='STANDARD',
                 preserve_acl=False, encrypt_key=False, headers=None,
                 query_args=None, src_generation=None):
        """Create a new key in the bucket by copying an existing key.

        :type new_key_name: string
        :param new_key_name: The name of the new key

        :type src_bucket_name: string
        :param src_bucket_name: The name of the source bucket

        :type src_key_name: string
        :param src_key_name: The name of the source key

        :type src_generation: int
        :param src_generation: The generation number of the source key to copy.
            If not specified, the latest generation is copied.

        :type metadata: dict
        :param metadata: Metadata to be associated with new key.  If
            metadata is supplied, it will replace the metadata of the
            source key being copied.  If no metadata is supplied, the
            source key's metadata will be copied to the new key.

        :type version_id: string
        :param version_id: Unused in this subclass.

        :type storage_class: string
        :param storage_class: The storage class of the new key.  By
            default, the new key will use the standard storage class.
            Possible values are: STANDARD | DURABLE_REDUCED_AVAILABILITY

        :type preserve_acl: bool
        :param preserve_acl: If True, the ACL from the source key will
            be copied to the destination key.  If False, the
            destination key will have the default ACL.  Note that
            preserving the ACL in the new key object will require two
            additional API calls to GCS, one to retrieve the current
            ACL and one to set that ACL on the new object.  If you
            don't care about the ACL (or if you have a default ACL set
            on the bucket), a value of False will be significantly more
            efficient.

        :type encrypt_key: bool
        :param encrypt_key: Included for compatibility with S3. This argument is
            ignored.

        :type headers: dict
        :param headers: A dictionary of header name/value pairs.

        :type query_args: string
        :param query_args: A string of additional querystring arguments
            to append to the request

        :rtype: :class:`boto.gs.key.Key`
        :returns: An instance of the newly created key object
        """
        if src_generation:
            headers = headers or {}
            headers['x-goog-copy-source-generation'] = str(src_generation)
        return super(Bucket, self).copy_key(
            new_key_name, src_bucket_name, src_key_name, metadata=metadata,
            storage_class=storage_class, preserve_acl=preserve_acl,
            encrypt_key=encrypt_key, headers=headers, query_args=query_args)

    def list_versions(self, prefix='', delimiter='', marker='',
                      generation_marker='', headers=None):
        """
        List versioned objects within a bucket.  This returns an
        instance of an VersionedBucketListResultSet that automatically
        handles all of the result paging, etc. from GCS.  You just need
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
            https://developers.google.com/storage/docs/reference-headers#delimiter
            for more details.

        :type marker: string
        :param marker: The "marker" of where you are in the result set

        :type generation_marker: string
        :param generation_marker: The "generation marker" of where you are in
            the result set.

        :type headers: dict
        :param headers: A dictionary of header name/value pairs.

        :rtype:
            :class:`boto.gs.bucketlistresultset.VersionedBucketListResultSet`
        :return: an instance of a BucketListResultSet that handles paging, etc.
        """
        return VersionedBucketListResultSet(self, prefix, delimiter,
                                            marker, generation_marker,
                                            headers)

    def validate_get_all_versions_params(self, params):
        """
        See documentation in boto/s3/bucket.py.
        """
        self.validate_kwarg_names(params,
                                  ['version_id_marker', 'delimiter', 'marker',
                                   'generation_marker', 'prefix', 'max_keys'])

    def delete_key(self, key_name, headers=None, version_id=None,
                   mfa_token=None, generation=None):
        """
        Deletes a key from the bucket.

        :type key_name: string
        :param key_name: The key name to delete

        :type headers: dict
        :param headers: A dictionary of header name/value pairs.

        :type version_id: string
        :param version_id: Unused in this subclass.

        :type mfa_token: tuple or list of strings
        :param mfa_token: Unused in this subclass.

        :type generation: int
        :param generation: The generation number of the key to delete. If not
            specified, the latest generation number will be deleted.

        :rtype: :class:`boto.gs.key.Key`
        :returns: A key object holding information on what was
            deleted.
        """
        query_args_l = []
        if generation:
            query_args_l.append('generation=%s' % generation)
        self._delete_key_internal(key_name, headers=headers,
                                  version_id=version_id, mfa_token=mfa_token,
                                  query_args_l=query_args_l)

    def set_acl(self, acl_or_str, key_name='', headers=None, version_id=None,
                generation=None, if_generation=None, if_metageneration=None):
        """Sets or changes a bucket's or key's ACL.

        :type acl_or_str: string or :class:`boto.gs.acl.ACL`
        :param acl_or_str: A canned ACL string (see
            :data:`~.gs.acl.CannedACLStrings`) or an ACL object.

        :type key_name: string
        :param key_name: A key name within the bucket to set the ACL for. If not
            specified, the ACL for the bucket will be set.

        :type headers: dict
        :param headers: Additional headers to set during the request.

        :type version_id: string
        :param version_id: Unused in this subclass.

        :type generation: int
        :param generation: If specified, sets the ACL for a specific generation
            of a versioned object. If not specified, the current version is
            modified.

        :type if_generation: int
        :param if_generation: (optional) If set to a generation number, the acl
            will only be updated if its current generation number is this value.

        :type if_metageneration: int
        :param if_metageneration: (optional) If set to a metageneration number,
            the acl will only be updated if its current metageneration number is
            this value.
        """
        if isinstance(acl_or_str, Policy):
            raise InvalidAclError('Attempt to set S3 Policy on GS ACL')
        elif isinstance(acl_or_str, ACL):
            self.set_xml_acl(acl_or_str.to_xml(), key_name, headers=headers,
                             generation=generation,
                             if_generation=if_generation,
                             if_metageneration=if_metageneration)
        else:
            self.set_canned_acl(acl_or_str, key_name, headers=headers,
                                generation=generation,
                                if_generation=if_generation,
                                if_metageneration=if_metageneration)

    def set_def_acl(self, acl_or_str, headers=None):
        """Sets or changes a bucket's default ACL.

        :type acl_or_str: string or :class:`boto.gs.acl.ACL`
        :param acl_or_str: A canned ACL string (see
            :data:`~.gs.acl.CannedACLStrings`) or an ACL object.

        :type headers: dict
        :param headers: Additional headers to set during the request.
        """
        if isinstance(acl_or_str, Policy):
            raise InvalidAclError('Attempt to set S3 Policy on GS ACL')
        elif isinstance(acl_or_str, ACL):
            self.set_def_xml_acl(acl_or_str.to_xml(), headers=headers)
        else:
            self.set_def_canned_acl(acl_or_str, headers=headers)

    def _get_xml_acl_helper(self, key_name, headers, query_args):
        """Provides common functionality for get_xml_acl and _get_acl_helper."""
        response = self.connection.make_request('GET', self.name, key_name,
                                                query_args=query_args,
                                                headers=headers)
        body = response.read()
        if response.status != 200:
            if response.status == 403:
                match = ERROR_DETAILS_REGEX.search(body)
                details = match.group('details') if match else None
                if details:
                    details = (('<Details>%s. Note that Full Control access'
                                ' is required to access ACLs.</Details>') %
                               details)
                    if six.PY3:
                        # All args to re.sub() must be of same type
                        details = details.encode('utf-8')
                    body = re.sub(ERROR_DETAILS_REGEX, details, body)
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)
        return body

    def _get_acl_helper(self, key_name, headers, query_args):
        """Provides common functionality for get_acl and get_def_acl."""
        body = self._get_xml_acl_helper(key_name, headers, query_args)
        acl = ACL(self)
        h = handler.XmlHandler(acl, self)
        xml.sax.parseString(body, h)
        return acl

    def get_acl(self, key_name='', headers=None, version_id=None,
                generation=None):
        """Returns the ACL of the bucket or an object in the bucket.

        :param str key_name: The name of the object to get the ACL for. If not
            specified, the ACL for the bucket will be returned.

        :param dict headers: Additional headers to set during the request.

        :type version_id: string
        :param version_id: Unused in this subclass.

        :param int generation: If specified, gets the ACL for a specific
            generation of a versioned object. If not specified, the current
            version is returned. This parameter is only valid when retrieving
            the ACL of an object, not a bucket.

        :rtype: :class:`.gs.acl.ACL`
        """
        query_args = STANDARD_ACL
        if generation:
            query_args += '&generation=%s' % generation
        return self._get_acl_helper(key_name, headers, query_args)

    def get_xml_acl(self, key_name='', headers=None, version_id=None,
                    generation=None):
        """Returns the ACL string of the bucket or an object in the bucket.

        :param str key_name: The name of the object to get the ACL for. If not
            specified, the ACL for the bucket will be returned.

        :param dict headers: Additional headers to set during the request.

        :type version_id: string
        :param version_id: Unused in this subclass.

        :param int generation: If specified, gets the ACL for a specific
            generation of a versioned object. If not specified, the current
            version is returned. This parameter is only valid when retrieving
            the ACL of an object, not a bucket.

        :rtype: str
        """
        query_args = STANDARD_ACL
        if generation:
            query_args += '&generation=%s' % generation
        return self._get_xml_acl_helper(key_name, headers, query_args)

    def get_def_acl(self, headers=None):
        """Returns the bucket's default ACL.

        :param dict headers: Additional headers to set during the request.

        :rtype: :class:`.gs.acl.ACL`
        """
        return self._get_acl_helper('', headers, DEF_OBJ_ACL)

    def _set_acl_helper(self, acl_or_str, key_name, headers, query_args,
                          generation, if_generation, if_metageneration,
                          canned=False):
        """Provides common functionality for set_acl, set_xml_acl,
        set_canned_acl, set_def_acl, set_def_xml_acl, and
        set_def_canned_acl()."""

        headers = headers or {}
        data = ''
        if canned:
            headers[self.connection.provider.acl_header] = acl_or_str
        else:
            data = acl_or_str

        if generation:
            query_args += '&generation=%s' % generation

        if if_metageneration is not None and if_generation is None:
            raise ValueError("Received if_metageneration argument with no "
                             "if_generation argument. A metageneration has no "
                             "meaning without a content generation.")
        if not key_name and (if_generation or if_metageneration):
            raise ValueError("Received if_generation or if_metageneration "
                             "parameter while setting the ACL of a bucket.")
        if if_generation is not None:
            headers['x-goog-if-generation-match'] = str(if_generation)
        if if_metageneration is not None:
            headers['x-goog-if-metageneration-match'] = str(if_metageneration)

        response = self.connection.make_request(
            'PUT', self.name, key_name,
            data=data, headers=headers, query_args=query_args)
        body = response.read()
        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def set_xml_acl(self, acl_str, key_name='', headers=None, version_id=None,
                    query_args='acl', generation=None, if_generation=None,
                    if_metageneration=None):
        """Sets a bucket's or objects's ACL to an XML string.

        :type acl_str: string
        :param acl_str: A string containing the ACL XML.

        :type key_name: string
        :param key_name: A key name within the bucket to set the ACL for. If not
            specified, the ACL for the bucket will be set.

        :type headers: dict
        :param headers: Additional headers to set during the request.

        :type version_id: string
        :param version_id: Unused in this subclass.

        :type query_args: str
        :param query_args: The query parameters to pass with the request.

        :type generation: int
        :param generation: If specified, sets the ACL for a specific generation
            of a versioned object. If not specified, the current version is
            modified.

        :type if_generation: int
        :param if_generation: (optional) If set to a generation number, the acl
            will only be updated if its current generation number is this value.

        :type if_metageneration: int
        :param if_metageneration: (optional) If set to a metageneration number,
            the acl will only be updated if its current metageneration number is
            this value.
        """
        return self._set_acl_helper(acl_str, key_name=key_name, headers=headers,
                                    query_args=query_args,
                                    generation=generation,
                                    if_generation=if_generation,
                                    if_metageneration=if_metageneration)

    def set_canned_acl(self, acl_str, key_name='', headers=None,
                       version_id=None, generation=None, if_generation=None,
                       if_metageneration=None):
        """Sets a bucket's or objects's ACL using a predefined (canned) value.

        :type acl_str: string
        :param acl_str: A canned ACL string. See
            :data:`~.gs.acl.CannedACLStrings`.

        :type key_name: string
        :param key_name: A key name within the bucket to set the ACL for. If not
            specified, the ACL for the bucket will be set.

        :type headers: dict
        :param headers: Additional headers to set during the request.

        :type version_id: string
        :param version_id: Unused in this subclass.

        :type generation: int
        :param generation: If specified, sets the ACL for a specific generation
            of a versioned object. If not specified, the current version is
            modified.

        :type if_generation: int
        :param if_generation: (optional) If set to a generation number, the acl
            will only be updated if its current generation number is this value.

        :type if_metageneration: int
        :param if_metageneration: (optional) If set to a metageneration number,
            the acl will only be updated if its current metageneration number is
            this value.
        """
        if acl_str not in CannedACLStrings:
            raise ValueError("Provided canned ACL string (%s) is not valid."
                             % acl_str)
        query_args = STANDARD_ACL
        return self._set_acl_helper(acl_str, key_name, headers, query_args,
                                    generation, if_generation,
                                    if_metageneration, canned=True)

    def set_def_canned_acl(self, acl_str, headers=None):
        """Sets a bucket's default ACL using a predefined (canned) value.

        :type acl_str: string
        :param acl_str: A canned ACL string. See
            :data:`~.gs.acl.CannedACLStrings`.

        :type headers: dict
        :param headers: Additional headers to set during the request.
        """
        if acl_str not in CannedACLStrings:
            raise ValueError("Provided canned ACL string (%s) is not valid."
                             % acl_str)
        query_args = DEF_OBJ_ACL
        return self._set_acl_helper(acl_str, '', headers, query_args,
                                    generation=None, if_generation=None,
                                    if_metageneration=None, canned=True)

    def set_def_xml_acl(self, acl_str, headers=None):
        """Sets a bucket's default ACL to an XML string.

        :type acl_str: string
        :param acl_str: A string containing the ACL XML.

        :type headers: dict
        :param headers: Additional headers to set during the request.
        """
        return self.set_xml_acl(acl_str, '', headers,
                                query_args=DEF_OBJ_ACL)

    def get_cors(self, headers=None):
        """Returns a bucket's CORS XML document.

        :param dict headers: Additional headers to send with the request.
        :rtype: :class:`~.cors.Cors`
        """
        response = self.connection.make_request('GET', self.name,
                                                query_args=CORS_ARG,
                                                headers=headers)
        body = response.read()
        if response.status == 200:
            # Success - parse XML and return Cors object.
            cors = Cors()
            h = handler.XmlHandler(cors, self)
            xml.sax.parseString(body, h)
            return cors
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def set_cors(self, cors, headers=None):
        """Sets a bucket's CORS XML document.

        :param str cors: A string containing the CORS XML.
        :param dict headers: Additional headers to send with the request.
        """
        response = self.connection.make_request(
            'PUT', self.name, data=cors,
            query_args=CORS_ARG, headers=headers)
        body = response.read()
        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def get_storage_class(self, headers=None):
        """
        Returns the StorageClass for the bucket.

        :rtype: str
        :return: The StorageClass for the bucket.
        """
        response = self.connection.make_request('GET', self.name,
                                                query_args=STORAGE_CLASS_ARG,
                                                headers=headers)
        body = response.read()
        if response.status == 200:
            rs = ResultSet(self)
            h = handler.XmlHandler(rs, self)
            xml.sax.parseString(body, h)
            return rs.StorageClass
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def set_storage_class(self, storage_class, headers=None):
        """
        Sets a bucket's storage class.

        :param str storage_class: A string containing the storage class.
        :param dict headers: Additional headers to send with the request.
        """
        req_body = self.StorageClassBody % (get_utf8able_str(storage_class))
        self.set_subresource(STORAGE_CLASS_ARG, req_body, headers=headers)

    # Method with same signature as boto.s3.bucket.Bucket.add_email_grant(),
    # to allow polymorphic treatment at application layer.
    def add_email_grant(self, permission, email_address,
                        recursive=False, headers=None):
        """
        Convenience method that provides a quick way to add an email grant
        to a bucket. This method retrieves the current ACL, creates a new
        grant based on the parameters passed in, adds that grant to the ACL
        and then PUT's the new ACL back to GCS.

        :type permission: string
        :param permission: The permission being granted. Should be one of:
                           (READ, WRITE, FULL_CONTROL).

        :type email_address: string
        :param email_address: The email address associated with the GS
                              account your are granting the permission to.

        :type recursive: bool
        :param recursive: A boolean value to controls whether the call
                          will apply the grant to all keys within the bucket
                          or not.  The default value is False.  By passing a
                          True value, the call will iterate through all keys
                          in the bucket and apply the same grant to each key.
                          CAUTION: If you have a lot of keys, this could take
                          a long time!
        """
        if permission not in GSPermissions:
            raise self.connection.provider.storage_permissions_error(
                'Unknown Permission: %s' % permission)
        acl = self.get_acl(headers=headers)
        acl.add_email_grant(permission, email_address)
        self.set_acl(acl, headers=headers)
        if recursive:
            for key in self:
                key.add_email_grant(permission, email_address, headers=headers)

    # Method with same signature as boto.s3.bucket.Bucket.add_user_grant(),
    # to allow polymorphic treatment at application layer.
    def add_user_grant(self, permission, user_id, recursive=False,
                       headers=None):
        """
        Convenience method that provides a quick way to add a canonical user
        grant to a bucket. This method retrieves the current ACL, creates a new
        grant based on the parameters passed in, adds that grant to the ACL and
        then PUTs the new ACL back to GCS.

        :type permission: string
        :param permission:  The permission being granted.  Should be one of:
                            (READ|WRITE|FULL_CONTROL)

        :type user_id: string
        :param user_id:     The canonical user id associated with the GS account
                            you are granting the permission to.

        :type recursive: bool
        :param recursive: A boolean value to controls whether the call
                          will apply the grant to all keys within the bucket
                          or not.  The default value is False.  By passing a
                          True value, the call will iterate through all keys
                          in the bucket and apply the same grant to each key.
                          CAUTION: If you have a lot of keys, this could take
                          a long time!
        """
        if permission not in GSPermissions:
            raise self.connection.provider.storage_permissions_error(
                'Unknown Permission: %s' % permission)
        acl = self.get_acl(headers=headers)
        acl.add_user_grant(permission, user_id)
        self.set_acl(acl, headers=headers)
        if recursive:
            for key in self:
                key.add_user_grant(permission, user_id, headers=headers)

    def add_group_email_grant(self, permission, email_address, recursive=False,
                              headers=None):
        """
        Convenience method that provides a quick way to add an email group
        grant to a bucket. This method retrieves the current ACL, creates a new
        grant based on the parameters passed in, adds that grant to the ACL and
        then PUT's the new ACL back to GCS.

        :type permission: string
        :param permission: The permission being granted. Should be one of:
            READ|WRITE|FULL_CONTROL
            See http://code.google.com/apis/storage/docs/developer-guide.html#authorization
            for more details on permissions.

        :type email_address: string
        :param email_address: The email address associated with the Google
            Group to which you are granting the permission.

        :type recursive: bool
        :param recursive: A boolean value to controls whether the call
                          will apply the grant to all keys within the bucket
                          or not.  The default value is False.  By passing a
                          True value, the call will iterate through all keys
                          in the bucket and apply the same grant to each key.
                          CAUTION: If you have a lot of keys, this could take
                          a long time!
        """
        if permission not in GSPermissions:
            raise self.connection.provider.storage_permissions_error(
                'Unknown Permission: %s' % permission)
        acl = self.get_acl(headers=headers)
        acl.add_group_email_grant(permission, email_address)
        self.set_acl(acl, headers=headers)
        if recursive:
            for key in self:
                key.add_group_email_grant(permission, email_address,
                                          headers=headers)

    # Method with same input signature as boto.s3.bucket.Bucket.list_grants()
    # (but returning different object type), to allow polymorphic treatment
    # at application layer.
    def list_grants(self, headers=None):
        """Returns the ACL entries applied to this bucket.

        :param dict headers: Additional headers to send with the request.
        :rtype: list containing :class:`~.gs.acl.Entry` objects.
        """
        acl = self.get_acl(headers=headers)
        return acl.entries

    def disable_logging(self, headers=None):
        """Disable logging on this bucket.

        :param dict headers: Additional headers to send with the request.
        """
        xml_str = '<?xml version="1.0" encoding="UTF-8"?><Logging/>'
        self.set_subresource('logging', xml_str, headers=headers)

    def enable_logging(self, target_bucket, target_prefix=None, headers=None):
        """Enable logging on a bucket.

        :type target_bucket: bucket or string
        :param target_bucket: The bucket to log to.

        :type target_prefix: string
        :param target_prefix: The prefix which should be prepended to the
            generated log files written to the target_bucket.

        :param dict headers: Additional headers to send with the request.
        """
        if isinstance(target_bucket, Bucket):
            target_bucket = target_bucket.name
        xml_str = '<?xml version="1.0" encoding="UTF-8"?><Logging>'
        xml_str = (xml_str + '<LogBucket>%s</LogBucket>' % target_bucket)
        if target_prefix:
            xml_str = (xml_str +
                       '<LogObjectPrefix>%s</LogObjectPrefix>' % target_prefix)
        xml_str = xml_str + '</Logging>'

        self.set_subresource('logging', xml_str, headers=headers)

    def get_logging_config_with_xml(self, headers=None):
        """Returns the current status of logging configuration on the bucket as
        unparsed XML.

        :param dict headers: Additional headers to send with the request.

        :rtype: 2-Tuple
        :returns: 2-tuple containing:

            1) A dictionary containing the parsed XML response from GCS. The
              overall structure is:

              * Logging

                * LogObjectPrefix: Prefix that is prepended to log objects.
                * LogBucket: Target bucket for log objects.

            2) Unparsed XML describing the bucket's logging configuration.
        """
        response = self.connection.make_request('GET', self.name,
                                                query_args='logging',
                                                headers=headers)
        body = response.read()
        boto.log.debug(body)

        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

        e = boto.jsonresponse.Element()
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        return e, body

    def get_logging_config(self, headers=None):
        """Returns the current status of logging configuration on the bucket.

        :param dict headers: Additional headers to send with the request.

        :rtype: dict
        :returns: A dictionary containing the parsed XML response from GCS. The
            overall structure is:

            * Logging

              * LogObjectPrefix: Prefix that is prepended to log objects.
              * LogBucket: Target bucket for log objects.
        """
        return self.get_logging_config_with_xml(headers)[0]

    def configure_website(self, main_page_suffix=None, error_key=None,
                          headers=None):
        """Configure this bucket to act as a website

        :type main_page_suffix: str
        :param main_page_suffix: Suffix that is appended to a request that is
            for a "directory" on the website endpoint (e.g. if the suffix is
            index.html and you make a request to samplebucket/images/ the data
            that is returned will be for the object with the key name
            images/index.html). The suffix must not be empty and must not
            include a slash character. This parameter is optional and the
            property is disabled if excluded.

        :type error_key: str
        :param error_key: The object key name to use when a 400 error occurs.
            This parameter is optional and the property is disabled if excluded.

        :param dict headers: Additional headers to send with the request.
        """
        if main_page_suffix:
            main_page_frag = self.WebsiteMainPageFragment % main_page_suffix
        else:
            main_page_frag = ''

        if error_key:
            error_frag = self.WebsiteErrorFragment % error_key
        else:
            error_frag = ''

        body = self.WebsiteBody % (main_page_frag, error_frag)
        response = self.connection.make_request(
            'PUT', get_utf8able_str(self.name), data=get_utf8able_str(body),
            query_args='websiteConfig', headers=headers)
        body = response.read()
        if response.status == 200:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def get_website_configuration(self, headers=None):
        """Returns the current status of website configuration on the bucket.

        :param dict headers: Additional headers to send with the request.

        :rtype: dict
        :returns: A dictionary containing the parsed XML response from GCS. The
            overall structure is:

            * WebsiteConfiguration

              * MainPageSuffix: suffix that is appended to request that
                is for a "directory" on the website endpoint.
              * NotFoundPage: name of an object to serve when site visitors
                encounter a 404.
        """
        return self.get_website_configuration_with_xml(headers)[0]

    def get_website_configuration_with_xml(self, headers=None):
        """Returns the current status of website configuration on the bucket as
        unparsed XML.

        :param dict headers: Additional headers to send with the request.

        :rtype: 2-Tuple
        :returns: 2-tuple containing:

            1) A dictionary containing the parsed XML response from GCS. The
              overall structure is:

              * WebsiteConfiguration

                * MainPageSuffix: suffix that is appended to request that is for
                  a "directory" on the website endpoint.
                * NotFoundPage: name of an object to serve when site visitors
                  encounter a 404

            2) Unparsed XML describing the bucket's website configuration.
        """
        response = self.connection.make_request('GET', self.name,
                query_args='websiteConfig', headers=headers)
        body = response.read()
        boto.log.debug(body)

        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

        e = boto.jsonresponse.Element()
        h = boto.jsonresponse.XmlHandler(e, None)
        h.parse(body)
        return e, body

    def delete_website_configuration(self, headers=None):
        """Remove the website configuration from this bucket.

        :param dict headers: Additional headers to send with the request.
        """
        self.configure_website(headers=headers)

    def get_versioning_status(self, headers=None):
        """Returns the current status of versioning configuration on the bucket.

        :rtype: bool
        """
        response = self.connection.make_request('GET', self.name,
                                                query_args='versioning',
                                                headers=headers)
        body = response.read()
        boto.log.debug(body)
        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                    response.status, response.reason, body)
        resp_json = boto.jsonresponse.Element()
        boto.jsonresponse.XmlHandler(resp_json, None).parse(body)
        resp_json = resp_json['VersioningConfiguration']
        return ('Status' in resp_json) and (resp_json['Status'] == 'Enabled')

    def configure_versioning(self, enabled, headers=None):
        """Configure versioning for this bucket.

        :param bool enabled: If set to True, enables versioning on this bucket.
            If set to False, disables versioning.

        :param dict headers: Additional headers to send with the request.
        """
        if enabled == True:
            req_body = self.VersioningBody % ('Enabled')
        else:
            req_body = self.VersioningBody % ('Suspended')
        self.set_subresource('versioning', req_body, headers=headers)

    def get_lifecycle_config(self, headers=None):
        """
        Returns the current lifecycle configuration on the bucket.

        :rtype: :class:`boto.gs.lifecycle.LifecycleConfig`
        :returns: A LifecycleConfig object that describes all current
            lifecycle rules in effect for the bucket.
        """
        response = self.connection.make_request('GET', self.name,
                query_args=LIFECYCLE_ARG, headers=headers)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            lifecycle_config = LifecycleConfig()
            h = handler.XmlHandler(lifecycle_config, self)
            xml.sax.parseString(body, h)
            return lifecycle_config
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def configure_lifecycle(self, lifecycle_config, headers=None):
        """
        Configure lifecycle for this bucket.

        :type lifecycle_config: :class:`boto.gs.lifecycle.LifecycleConfig`
        :param lifecycle_config: The lifecycle configuration you want
            to configure for this bucket.
        """
        xml = lifecycle_config.to_xml()
        response = self.connection.make_request(
            'PUT', self.name, data=xml,
            query_args=LIFECYCLE_ARG, headers=headers)
        body = response.read()
        if response.status == 200:
            return True
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def get_billing_config(self, headers=None):
        """Returns the current status of billing configuration on the bucket.

        :param dict headers: Additional headers to send with the request.

        :rtype: dict
        :returns: A dictionary containing the parsed XML response from GCS. The
            overall structure is:

            * BillingConfiguration

              * RequesterPays: Enabled/Disabled.
        """
        return self.get_billing_configuration_with_xml(headers)[0]

    def get_billing_configuration_with_xml(self, headers=None):
        """Returns the current status of billing configuration on the bucket as
        unparsed XML.

        :param dict headers: Additional headers to send with the request.

        :rtype: 2-Tuple
        :returns: 2-tuple containing:

            1) A dictionary containing the parsed XML response from GCS. The
              overall structure is:

              * BillingConfiguration

                * RequesterPays: Enabled/Disabled.

            2) Unparsed XML describing the bucket's website configuration.
        """
        response = self.connection.make_request('GET', self.name,
                                                query_args='billing',
                                                headers=headers)
        body = response.read()
        boto.log.debug(body)

        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

        e = boto.jsonresponse.Element()
        h = boto.jsonresponse.XmlHandler(e, None);
        h.parse(body)
        return e, body

    def configure_billing(self, requester_pays=False, headers=None):
        """Configure billing for this bucket.

        :param bool requester_pays: If set to True, enables requester pays on
            this bucket. If set to False, disables requester pays.

        :param dict headers: Additional headers to send with the request.
        """
        if requester_pays == True:
            req_body = self.BillingBody % ('Enabled')
        else:
            req_body = self.BillingBody % ('Disabled')
        self.set_subresource('billing', req_body, headers=headers)

    def get_encryption_config(self, headers=None):
        """Returns a bucket's EncryptionConfig.

        :param dict headers: Additional headers to send with the request.
        :rtype: :class:`~.encryption_config.EncryptionConfig`
        """
        response = self.connection.make_request(
            'GET', self.name, query_args=ENCRYPTION_CONFIG_ARG, headers=headers)
        body = response.read()
        if response.status == 200:
            # Success - parse XML and return EncryptionConfig object.
            encryption_config = EncryptionConfig()
            h = handler.XmlHandler(encryption_config, self)
            xml.sax.parseString(body, h)
            return encryption_config
        else:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)

    def _construct_encryption_config_xml(self, default_kms_key_name=None):
        """Creates an XML document for setting a bucket's EncryptionConfig.

        This method is internal as it's only here for testing purposes. As
        managing Cloud KMS resources for testing is complex, we settle for
        testing that we're creating correctly-formed XML for setting a bucket's
        encryption configuration.

        :param str default_kms_key_name: A string containing a fully-qualified
            Cloud KMS key name.
        :rtype: str
        """
        if default_kms_key_name:
            default_kms_key_name_frag = (
                self.EncryptionConfigDefaultKeyNameFragment %
                default_kms_key_name)
        else:
            default_kms_key_name_frag = ''

        return self.EncryptionConfigBody % default_kms_key_name_frag


    def set_encryption_config(self, default_kms_key_name=None, headers=None):
        """Sets a bucket's EncryptionConfig XML document.

        :param str default_kms_key_name: A string containing a fully-qualified
            Cloud KMS key name.
        :param dict headers: Additional headers to send with the request.
        """
        body = self._construct_encryption_config_xml(
            default_kms_key_name=default_kms_key_name)
        response = self.connection.make_request(
            'PUT', self.name, data=body,
            query_args=ENCRYPTION_CONFIG_ARG, headers=headers)
        body = response.read()
        if response.status != 200:
            raise self.connection.provider.storage_response_error(
                response.status, response.reason, body)
