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

import uuid
import base64
import time
from boto.compat import six, json
from boto.cloudfront.identity import OriginAccessIdentity
from boto.cloudfront.object import Object, StreamingObject
from boto.cloudfront.signers import ActiveTrustedSigners, TrustedSigners
from boto.cloudfront.logging import LoggingInfo
from boto.cloudfront.origin import S3Origin, CustomOrigin
from boto.s3.acl import ACL

class DistributionConfig(object):

    def __init__(self, connection=None, origin=None, enabled=False,
                 caller_reference='', cnames=None, comment='',
                 trusted_signers=None, default_root_object=None,
                 logging=None):
        """
        :param origin: Origin information to associate with the
                       distribution.  If your distribution will use
                       an Amazon S3 origin, then this should be an
                       S3Origin object. If your distribution will use
                       a custom origin (non Amazon S3), then this
                       should be a CustomOrigin object.
        :type origin: :class:`boto.cloudfront.origin.S3Origin` or
                      :class:`boto.cloudfront.origin.CustomOrigin`

        :param enabled: Whether the distribution is enabled to accept
                        end user requests for content.
        :type enabled: bool

        :param caller_reference: A unique number that ensures the
                                 request can't be replayed.  If no
                                 caller_reference is provided, boto
                                 will generate a type 4 UUID for use
                                 as the caller reference.
        :type enabled: str

        :param cnames: A CNAME alias you want to associate with this
                       distribution. You can have up to 10 CNAME aliases
                       per distribution.
        :type enabled: array of str

        :param comment: Any comments you want to include about the
                        distribution.
        :type comment: str

        :param trusted_signers: Specifies any AWS accounts you want to
                                permit to create signed URLs for private
                                content. If you want the distribution to
                                use signed URLs, this should contain a
                                TrustedSigners object; if you want the
                                distribution to use basic URLs, leave
                                this None.
        :type trusted_signers: :class`boto.cloudfront.signers.TrustedSigners`

        :param default_root_object: Designates a default root object.
                                    Only include a DefaultRootObject value
                                    if you are going to assign a default
                                    root object for the distribution.
        :type comment: str

        :param logging: Controls whether access logs are written for the
                        distribution. If you want to turn on access logs,
                        this should contain a LoggingInfo object; otherwise
                        it should contain None.
        :type logging: :class`boto.cloudfront.logging.LoggingInfo`

        """
        self.connection = connection
        self.origin = origin
        self.enabled = enabled
        if caller_reference:
            self.caller_reference = caller_reference
        else:
            self.caller_reference = str(uuid.uuid4())
        self.cnames = []
        if cnames:
            self.cnames = cnames
        self.comment = comment
        self.trusted_signers = trusted_signers
        self.logging = logging
        self.default_root_object = default_root_object

    def __repr__(self):
        return "DistributionConfig:%s" % self.origin

    def to_xml(self):
        s = '<?xml version="1.0" encoding="UTF-8"?>\n'
        s += '<DistributionConfig xmlns="http://cloudfront.amazonaws.com/doc/2010-07-15/">\n'
        if self.origin:
            s += self.origin.to_xml()
        s += '  <CallerReference>%s</CallerReference>\n' % self.caller_reference
        for cname in self.cnames:
            s += '  <CNAME>%s</CNAME>\n' % cname
        if self.comment:
            s += '  <Comment>%s</Comment>\n' % self.comment
        s += '  <Enabled>'
        if self.enabled:
            s += 'true'
        else:
            s += 'false'
        s += '</Enabled>\n'
        if self.trusted_signers:
            s += '<TrustedSigners>\n'
            for signer in self.trusted_signers:
                if signer == 'Self':
                    s += '  <Self></Self>\n'
                else:
                    s += '  <AwsAccountNumber>%s</AwsAccountNumber>\n' % signer
            s += '</TrustedSigners>\n'
        if self.logging:
            s += '<Logging>\n'
            s += '  <Bucket>%s</Bucket>\n' % self.logging.bucket
            s += '  <Prefix>%s</Prefix>\n' % self.logging.prefix
            s += '</Logging>\n'
        if self.default_root_object:
            dro = self.default_root_object
            s += '<DefaultRootObject>%s</DefaultRootObject>\n' % dro
        s += '</DistributionConfig>\n'
        return s

    def startElement(self, name, attrs, connection):
        if name == 'TrustedSigners':
            self.trusted_signers = TrustedSigners()
            return self.trusted_signers
        elif name == 'Logging':
            self.logging = LoggingInfo()
            return self.logging
        elif name == 'S3Origin':
            self.origin = S3Origin()
            return self.origin
        elif name == 'CustomOrigin':
            self.origin = CustomOrigin()
            return self.origin
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'CNAME':
            self.cnames.append(value)
        elif name == 'Comment':
            self.comment = value
        elif name == 'Enabled':
            if value.lower() == 'true':
                self.enabled = True
            else:
                self.enabled = False
        elif name == 'CallerReference':
            self.caller_reference = value
        elif name == 'DefaultRootObject':
            self.default_root_object = value
        else:
            setattr(self, name, value)

class StreamingDistributionConfig(DistributionConfig):

    def __init__(self, connection=None, origin='', enabled=False,
                 caller_reference='', cnames=None, comment='',
                 trusted_signers=None, logging=None):
        super(StreamingDistributionConfig, self).__init__(connection=connection,
                                    origin=origin, enabled=enabled,
                                    caller_reference=caller_reference,
                                    cnames=cnames, comment=comment,
                                    trusted_signers=trusted_signers,
                                    logging=logging)
    def to_xml(self):
        s = '<?xml version="1.0" encoding="UTF-8"?>\n'
        s += '<StreamingDistributionConfig xmlns="http://cloudfront.amazonaws.com/doc/2010-07-15/">\n'
        if self.origin:
            s += self.origin.to_xml()
        s += '  <CallerReference>%s</CallerReference>\n' % self.caller_reference
        for cname in self.cnames:
            s += '  <CNAME>%s</CNAME>\n' % cname
        if self.comment:
            s += '  <Comment>%s</Comment>\n' % self.comment
        s += '  <Enabled>'
        if self.enabled:
            s += 'true'
        else:
            s += 'false'
        s += '</Enabled>\n'
        if self.trusted_signers:
            s += '<TrustedSigners>\n'
            for signer in self.trusted_signers:
                if signer == 'Self':
                    s += '  <Self/>\n'
                else:
                    s += '  <AwsAccountNumber>%s</AwsAccountNumber>\n' % signer
            s += '</TrustedSigners>\n'
        if self.logging:
            s += '<Logging>\n'
            s += '  <Bucket>%s</Bucket>\n' % self.logging.bucket
            s += '  <Prefix>%s</Prefix>\n' % self.logging.prefix
            s += '</Logging>\n'
        s += '</StreamingDistributionConfig>\n'
        return s

class DistributionSummary(object):

    def __init__(self, connection=None, domain_name='', id='',
                 last_modified_time=None, status='', origin=None,
                 cname='', comment='', enabled=False):
        self.connection = connection
        self.domain_name = domain_name
        self.id = id
        self.last_modified_time = last_modified_time
        self.status = status
        self.origin = origin
        self.enabled = enabled
        self.cnames = []
        if cname:
            self.cnames.append(cname)
        self.comment = comment
        self.trusted_signers = None
        self.etag = None
        self.streaming = False

    def __repr__(self):
        return "DistributionSummary:%s" % self.domain_name

    def startElement(self, name, attrs, connection):
        if name == 'TrustedSigners':
            self.trusted_signers = TrustedSigners()
            return self.trusted_signers
        elif name == 'S3Origin':
            self.origin = S3Origin()
            return self.origin
        elif name == 'CustomOrigin':
            self.origin = CustomOrigin()
            return self.origin
        return None

    def endElement(self, name, value, connection):
        if name == 'Id':
            self.id = value
        elif name == 'Status':
            self.status = value
        elif name == 'LastModifiedTime':
            self.last_modified_time = value
        elif name == 'DomainName':
            self.domain_name = value
        elif name == 'Origin':
            self.origin = value
        elif name == 'CNAME':
            self.cnames.append(value)
        elif name == 'Comment':
            self.comment = value
        elif name == 'Enabled':
            if value.lower() == 'true':
                self.enabled = True
            else:
                self.enabled = False
        elif name == 'StreamingDistributionSummary':
            self.streaming = True
        else:
            setattr(self, name, value)

    def get_distribution(self):
        return self.connection.get_distribution_info(self.id)

class StreamingDistributionSummary(DistributionSummary):

    def get_distribution(self):
        return self.connection.get_streaming_distribution_info(self.id)

class Distribution(object):

    def __init__(self, connection=None, config=None, domain_name='',
                 id='', last_modified_time=None, status=''):
        self.connection = connection
        self.config = config
        self.domain_name = domain_name
        self.id = id
        self.last_modified_time = last_modified_time
        self.status = status
        self.in_progress_invalidation_batches = 0
        self.active_signers = None
        self.etag = None
        self._bucket = None
        self._object_class = Object

    def __repr__(self):
        return "Distribution:%s" % self.domain_name

    def startElement(self, name, attrs, connection):
        if name == 'DistributionConfig':
            self.config = DistributionConfig()
            return self.config
        elif name == 'ActiveTrustedSigners':
            self.active_signers = ActiveTrustedSigners()
            return self.active_signers
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'Id':
            self.id = value
        elif name == 'LastModifiedTime':
            self.last_modified_time = value
        elif name == 'Status':
            self.status = value
        elif name == 'InProgressInvalidationBatches':
            self.in_progress_invalidation_batches = int(value)
        elif name == 'DomainName':
            self.domain_name = value
        else:
            setattr(self, name, value)

    def update(self, enabled=None, cnames=None, comment=None):
        """
        Update the configuration of the Distribution.  The only values
        of the DistributionConfig that can be directly updated are:

         * CNAMES
         * Comment
         * Whether the Distribution is enabled or not

        Any changes to the ``trusted_signers`` or ``origin`` properties of
        this distribution's current config object will also be included in
        the update. Therefore, to set the origin access identity for this
        distribution, set ``Distribution.config.origin.origin_access_identity``
        before calling this update method.

        :type enabled: bool
        :param enabled: Whether the Distribution is active or not.

        :type cnames: list of str
        :param cnames: The DNS CNAME's associated with this
                        Distribution.  Maximum of 10 values.

        :type comment: str or unicode
        :param comment: The comment associated with the Distribution.

        """
        new_config = DistributionConfig(self.connection, self.config.origin,
                                        self.config.enabled, self.config.caller_reference,
                                        self.config.cnames, self.config.comment,
                                        self.config.trusted_signers,
                                        self.config.default_root_object)
        if enabled is not None:
            new_config.enabled = enabled
        if cnames is not None:
            new_config.cnames = cnames
        if comment is not None:
            new_config.comment = comment
        self.etag = self.connection.set_distribution_config(self.id, self.etag, new_config)
        self.config = new_config
        self._object_class = Object

    def enable(self):
        """
        Activate the Distribution.  A convenience wrapper around
        the update method.
        """
        self.update(enabled=True)

    def disable(self):
        """
        Deactivate the Distribution.  A convenience wrapper around
        the update method.
        """
        self.update(enabled=False)

    def delete(self):
        """
        Delete this CloudFront Distribution.  The content
        associated with the Distribution is not deleted from
        the underlying Origin bucket in S3.
        """
        self.connection.delete_distribution(self.id, self.etag)

    def _get_bucket(self):
        if isinstance(self.config.origin, S3Origin):
            if not self._bucket:
                bucket_dns_name = self.config.origin.dns_name
                bucket_name = bucket_dns_name.replace('.s3.amazonaws.com', '')
                from boto.s3.connection import S3Connection
                s3 = S3Connection(self.connection.aws_access_key_id,
                                  self.connection.aws_secret_access_key,
                                  proxy=self.connection.proxy,
                                  proxy_port=self.connection.proxy_port,
                                  proxy_user=self.connection.proxy_user,
                                  proxy_pass=self.connection.proxy_pass)
                self._bucket = s3.get_bucket(bucket_name)
                self._bucket.distribution = self
                self._bucket.set_key_class(self._object_class)
            return self._bucket
        else:
            raise NotImplementedError('Unable to get_objects on CustomOrigin')

    def get_objects(self):
        """
        Return a list of all content objects in this distribution.

        :rtype: list of :class:`boto.cloudfront.object.Object`
        :return: The content objects
        """
        bucket = self._get_bucket()
        objs = []
        for key in bucket:
            objs.append(key)
        return objs

    def set_permissions(self, object, replace=False):
        """
        Sets the S3 ACL grants for the given object to the appropriate
        value based on the type of Distribution.  If the Distribution
        is serving private content the ACL will be set to include the
        Origin Access Identity associated with the Distribution.  If
        the Distribution is serving public content the content will
        be set up with "public-read".

        :type object: :class:`boto.cloudfront.object.Object`
        :param enabled: The Object whose ACL is being set

        :type replace: bool
        :param replace: If False, the Origin Access Identity will be
                        appended to the existing ACL for the object.
                        If True, the ACL for the object will be
                        completely replaced with one that grants
                        READ permission to the Origin Access Identity.

        """
        if isinstance(self.config.origin, S3Origin):
            if self.config.origin.origin_access_identity:
                id = self.config.origin.origin_access_identity.split('/')[-1]
                oai = self.connection.get_origin_access_identity_info(id)
                policy = object.get_acl()
                if replace:
                    policy.acl = ACL()
                policy.acl.add_user_grant('READ', oai.s3_user_id)
                object.set_acl(policy)
            else:
                object.set_canned_acl('public-read')

    def set_permissions_all(self, replace=False):
        """
        Sets the S3 ACL grants for all objects in the Distribution
        to the appropriate value based on the type of Distribution.

        :type replace: bool
        :param replace: If False, the Origin Access Identity will be
                        appended to the existing ACL for the object.
                        If True, the ACL for the object will be
                        completely replaced with one that grants
                        READ permission to the Origin Access Identity.

        """
        bucket = self._get_bucket()
        for key in bucket:
            self.set_permissions(key, replace)

    def add_object(self, name, content, headers=None, replace=True):
        """
        Adds a new content object to the Distribution.  The content
        for the object will be copied to a new Key in the S3 Bucket
        and the permissions will be set appropriately for the type
        of Distribution.

        :type name: str or unicode
        :param name: The name or key of the new object.

        :type content: file-like object
        :param content: A file-like object that contains the content
                        for the new object.

        :type headers: dict
        :param headers: A dictionary containing additional headers
                        you would like associated with the new
                        object in S3.

        :rtype: :class:`boto.cloudfront.object.Object`
        :return: The newly created object.
        """
        if self.config.origin.origin_access_identity:
            policy = 'private'
        else:
            policy = 'public-read'
        bucket = self._get_bucket()
        object = bucket.new_key(name)
        object.set_contents_from_file(content, headers=headers, policy=policy)
        if self.config.origin.origin_access_identity:
            self.set_permissions(object, replace)
        return object

    def create_signed_url(self, url, keypair_id,
                          expire_time=None, valid_after_time=None,
                          ip_address=None, policy_url=None,
                          private_key_file=None, private_key_string=None):
        """
        Creates a signed CloudFront URL that is only valid within the specified
        parameters.

        :type url: str
        :param url: The URL of the protected object.

        :type keypair_id: str
        :param keypair_id: The keypair ID of the Amazon KeyPair used to sign
            theURL.  This ID MUST correspond to the private key
            specified with private_key_file or private_key_string.

        :type expire_time: int
        :param expire_time: The expiry time of the URL. If provided, the URL
            will expire after the time has passed. If not provided the URL will
            never expire. Format is a unix epoch.
            Use int(time.time() + duration_in_sec).

        :type valid_after_time: int
        :param valid_after_time: If provided, the URL will not be valid until
            after valid_after_time. Format is a unix epoch.
            Use int(time.time() + secs_until_valid).

        :type ip_address: str
        :param ip_address: If provided, only allows access from the specified
            IP address.  Use '192.168.0.10' for a single IP or
            use '192.168.0.0/24' CIDR notation for a subnet.

        :type policy_url: str
        :param policy_url: If provided, allows the signature to contain
            wildcard globs in the URL.  For example, you could
            provide: 'http://example.com/media/\*' and the policy
            and signature would allow access to all contents of
            the media subdirectory. If not specified, only
            allow access to the exact url provided in 'url'.

        :type private_key_file: str or file object.
        :param private_key_file: If provided, contains the filename of the
            private key file used for signing or an open
            file object containing the private key
            contents.  Only one of private_key_file or
            private_key_string can be provided.

        :type private_key_string: str
        :param private_key_string: If provided, contains the private key string
            used for signing. Only one of private_key_file or
            private_key_string can be provided.

        :rtype: str
        :return: The signed URL.
        """
        # Get the required parameters
        params = self._create_signing_params(
                     url=url, keypair_id=keypair_id, expire_time=expire_time,
                     valid_after_time=valid_after_time, ip_address=ip_address,
                     policy_url=policy_url, private_key_file=private_key_file,
                     private_key_string=private_key_string)

        #combine these into a full url
        if "?" in url:
            sep = "&"
        else:
            sep = "?"
        signed_url_params = []
        for key in ["Expires", "Policy", "Signature", "Key-Pair-Id"]:
            if key in params:
                param = "%s=%s" % (key, params[key])
                signed_url_params.append(param)
        signed_url = url + sep + "&".join(signed_url_params)
        return signed_url

    def _create_signing_params(self, url, keypair_id,
                          expire_time=None, valid_after_time=None,
                          ip_address=None, policy_url=None,
                          private_key_file=None, private_key_string=None):
        """
        Creates the required URL parameters for a signed URL.
        """
        params = {}
        # Check if we can use a canned policy
        if expire_time and not valid_after_time and not ip_address and not policy_url:
            # we manually construct this policy string to ensure formatting
            # matches signature
            policy = self._canned_policy(url, expire_time)
            params["Expires"] = str(expire_time)
        else:
            # If no policy_url is specified, default to the full url.
            if policy_url is None:
                policy_url = url
            # Can't use canned policy
            policy = self._custom_policy(policy_url, expires=expire_time,
                                         valid_after=valid_after_time,
                                         ip_address=ip_address)

            encoded_policy = self._url_base64_encode(policy)
            params["Policy"] = encoded_policy
        #sign the policy
        signature = self._sign_string(policy, private_key_file, private_key_string)
        #now base64 encode the signature (URL safe as well)
        encoded_signature = self._url_base64_encode(signature)
        params["Signature"] = encoded_signature
        params["Key-Pair-Id"] = keypair_id
        return params

    @staticmethod
    def _canned_policy(resource, expires):
        """
        Creates a canned policy string.
        """
        policy = ('{"Statement":[{"Resource":"%(resource)s",'
                  '"Condition":{"DateLessThan":{"AWS:EpochTime":'
                  '%(expires)s}}}]}' % locals())
        return policy

    @staticmethod
    def _custom_policy(resource, expires=None, valid_after=None, ip_address=None):
        """
        Creates a custom policy string based on the supplied parameters.
        """
        condition = {}
        # SEE: http://docs.amazonwebservices.com/AmazonCloudFront/latest/DeveloperGuide/RestrictingAccessPrivateContent.html#CustomPolicy
        # The 'DateLessThan' property is required.
        if not expires:
            # Defaults to ONE day
            expires = int(time.time()) + 86400
        condition["DateLessThan"] = {"AWS:EpochTime": expires}
        if valid_after:
            condition["DateGreaterThan"] = {"AWS:EpochTime": valid_after}
        if ip_address:
            if '/' not in ip_address:
                ip_address += "/32"
            condition["IpAddress"] = {"AWS:SourceIp": ip_address}
        policy = {"Statement": [{
                     "Resource": resource,
                     "Condition": condition}]}
        return json.dumps(policy, separators=(",", ":"))

    @staticmethod
    def _sign_string(message, private_key_file=None, private_key_string=None):
        """
        Signs a string for use with Amazon CloudFront.
        Requires the rsa library be installed.
        """
        try:
            import rsa
        except ImportError:
            raise NotImplementedError("Boto depends on the python rsa "
                                      "library to generate signed URLs for "
                                      "CloudFront")
        # Make sure only one of private_key_file and private_key_string is set
        if private_key_file and private_key_string:
            raise ValueError("Only specify the private_key_file or the private_key_string not both")
        if not private_key_file and not private_key_string:
            raise ValueError("You must specify one of private_key_file or private_key_string")
        # If private_key_file is a file name, open it and read it
        if private_key_string is None:
            if isinstance(private_key_file, six.string_types):
                with open(private_key_file, 'r') as file_handle:
                    private_key_string = file_handle.read()
            # Otherwise, treat it like a file
            else:
                private_key_string = private_key_file.read()

        # Sign it!
        private_key = rsa.PrivateKey.load_pkcs1(private_key_string)
        signature = rsa.sign(str(message), private_key, 'SHA-1')
        return signature

    @staticmethod
    def _url_base64_encode(msg):
        """
        Base64 encodes a string using the URL-safe characters specified by
        Amazon.
        """
        msg_base64 = base64.b64encode(msg)
        msg_base64 = msg_base64.replace('+', '-')
        msg_base64 = msg_base64.replace('=', '_')
        msg_base64 = msg_base64.replace('/', '~')
        return msg_base64

class StreamingDistribution(Distribution):

    def __init__(self, connection=None, config=None, domain_name='',
                 id='', last_modified_time=None, status=''):
        super(StreamingDistribution, self).__init__(connection, config,
                              domain_name, id, last_modified_time, status)
        self._object_class = StreamingObject

    def startElement(self, name, attrs, connection):
        if name == 'StreamingDistributionConfig':
            self.config = StreamingDistributionConfig()
            return self.config
        else:
            return super(StreamingDistribution, self).startElement(name, attrs,
                connection)

    def update(self, enabled=None, cnames=None, comment=None):
        """
        Update the configuration of the StreamingDistribution.  The only values
        of the StreamingDistributionConfig that can be directly updated are:

         * CNAMES
         * Comment
         * Whether the Distribution is enabled or not

        Any changes to the ``trusted_signers`` or ``origin`` properties of
        this distribution's current config object will also be included in
        the update. Therefore, to set the origin access identity for this
        distribution, set
        ``StreamingDistribution.config.origin.origin_access_identity``
        before calling this update method.

        :type enabled: bool
        :param enabled: Whether the StreamingDistribution is active or not.

        :type cnames: list of str
        :param cnames: The DNS CNAME's associated with this
                        Distribution.  Maximum of 10 values.

        :type comment: str or unicode
        :param comment: The comment associated with the Distribution.

        """
        new_config = StreamingDistributionConfig(self.connection,
                                                 self.config.origin,
                                                 self.config.enabled,
                                                 self.config.caller_reference,
                                                 self.config.cnames,
                                                 self.config.comment,
                                                 self.config.trusted_signers)
        if enabled is not None:
            new_config.enabled = enabled
        if cnames is not None:
            new_config.cnames = cnames
        if comment is not None:
            new_config.comment = comment
        self.etag = self.connection.set_streaming_distribution_config(self.id,
                                                                      self.etag,
                                                                      new_config)
        self.config = new_config
        self._object_class = StreamingObject

    def delete(self):
        self.connection.delete_streaming_distribution(self.id, self.etag)


