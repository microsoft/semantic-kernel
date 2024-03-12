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
from boto.kms import exceptions
from boto.compat import six
import base64


class KMSConnection(AWSQueryConnection):
    """
    AWS Key Management Service
    AWS Key Management Service (KMS) is an encryption and key
    management web service. This guide describes the KMS actions that
    you can call programmatically. For general information about KMS,
    see (need an address here). For the KMS developer guide, see (need
    address here).

    AWS provides SDKs that consist of libraries and sample code for
    various programming languages and platforms (Java, Ruby, .Net,
    iOS, Android, etc.). The SDKs provide a convenient way to create
    programmatic access to KMS and AWS. For example, the SDKs take
    care of tasks such as signing requests (see below), managing
    errors, and retrying requests automatically. For more information
    about the AWS SDKs, including how to download and install them,
    see `Tools for Amazon Web Services`_.

    We recommend that you use the AWS SDKs to make programmatic API
    calls to KMS. However, you can also use the KMS Query API to make
    to make direct calls to the KMS web service.

    **Signing Requests**

    Requests must be signed by using an access key ID and a secret
    access key. We strongly recommend that you do not use your AWS
    account access key ID and secret key for everyday work with KMS.
    Instead, use the access key ID and secret access key for an IAM
    user, or you can use the AWS Security Token Service to generate
    temporary security credentials that you can use to sign requests.

    All KMS operations require `Signature Version 4`_.

    **Recording API Requests**

    KMS supports AWS CloudTrail, a service that records AWS API calls
    and related events for your AWS account and delivers them to an
    Amazon S3 bucket that you specify. By using the information
    collected by CloudTrail, you can determine what requests were made
    to KMS, who made the request, when it was made, and so on. To
    learn more about CloudTrail, including how to turn it on and find
    your log files, see the `AWS CloudTrail User Guide`_

    **Additional Resources**

    For more information about credentials and request signing, see
    the following:


    + `AWS Security Credentials`_. This topic provides general
      information about the types of credentials used for accessing AWS.
    + `AWS Security Token Service`_. This guide describes how to
      create and use temporary security credentials.
    + `Signing AWS API Requests`_. This set of topics walks you
      through the process of signing a request using an access key ID
      and a secret access key.
    """
    APIVersion = "2014-11-01"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "kms.us-east-1.amazonaws.com"
    ServiceName = "KMS"
    TargetPrefix = "TrentService"
    ResponseError = JSONResponseError

    _faults = {
        "InvalidGrantTokenException": exceptions.InvalidGrantTokenException,
        "DisabledException": exceptions.DisabledException,
        "LimitExceededException": exceptions.LimitExceededException,
        "DependencyTimeoutException": exceptions.DependencyTimeoutException,
        "InvalidMarkerException": exceptions.InvalidMarkerException,
        "AlreadyExistsException": exceptions.AlreadyExistsException,
        "InvalidCiphertextException": exceptions.InvalidCiphertextException,
        "KeyUnavailableException": exceptions.KeyUnavailableException,
        "InvalidAliasNameException": exceptions.InvalidAliasNameException,
        "UnsupportedOperationException": exceptions.UnsupportedOperationException,
        "InvalidArnException": exceptions.InvalidArnException,
        "KMSInternalException": exceptions.KMSInternalException,
        "InvalidKeyUsageException": exceptions.InvalidKeyUsageException,
        "MalformedPolicyDocumentException": exceptions.MalformedPolicyDocumentException,
        "NotFoundException": exceptions.NotFoundException,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs or kwargs['host'] is None:
            kwargs['host'] = region.endpoint

        super(KMSConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def create_alias(self, alias_name, target_key_id):
        """
        Creates a display name for a customer master key. An alias can
        be used to identify a key and should be unique. The console
        enforces a one-to-one mapping between the alias and a key. An
        alias name can contain only alphanumeric characters, forward
        slashes (/), underscores (_), and dashes (-). An alias must
        start with the word "alias" followed by a forward slash
        (alias/). An alias that begins with "aws" after the forward
        slash (alias/aws...) is reserved by Amazon Web Services (AWS).

        :type alias_name: string
        :param alias_name: String that contains the display name. Aliases that
            begin with AWS are reserved.

        :type target_key_id: string
        :param target_key_id: An identifier of the key for which you are
            creating the alias. This value cannot be another alias.

        """
        params = {
            'AliasName': alias_name,
            'TargetKeyId': target_key_id,
        }
        return self.make_request(action='CreateAlias',
                                 body=json.dumps(params))

    def create_grant(self, key_id, grantee_principal,
                     retiring_principal=None, operations=None,
                     constraints=None, grant_tokens=None):
        """
        Adds a grant to a key to specify who can access the key and
        under what conditions. Grants are alternate permission
        mechanisms to key policies. If absent, access to the key is
        evaluated based on IAM policies attached to the user. By
        default, grants do not expire. Grants can be listed, retired,
        or revoked as indicated by the following APIs. Typically, when
        you are finished using a grant, you retire it. When you want
        to end a grant immediately, revoke it. For more information
        about grants, see `Grants`_.

        #. ListGrants
        #. RetireGrant
        #. RevokeGrant

        :type key_id: string
        :param key_id: A unique key identifier for a customer master key. This
            value can be a globally unique identifier, an ARN, or an alias.

        :type grantee_principal: string
        :param grantee_principal: Principal given permission by the grant to
            use the key identified by the `keyId` parameter.

        :type retiring_principal: string
        :param retiring_principal: Principal given permission to retire the
            grant. For more information, see RetireGrant.

        :type operations: list
        :param operations: List of operations permitted by the grant. This can
            be any combination of one or more of the following values:

        #. Decrypt
        #. Encrypt
        #. GenerateDataKey
        #. GenerateDataKeyWithoutPlaintext
        #. ReEncryptFrom
        #. ReEncryptTo
        #. CreateGrant

        :type constraints: dict
        :param constraints: Specifies the conditions under which the actions
            specified by the `Operations` parameter are allowed.

        :type grant_tokens: list
        :param grant_tokens: List of grant tokens.

        """
        params = {
            'KeyId': key_id,
            'GranteePrincipal': grantee_principal,
        }
        if retiring_principal is not None:
            params['RetiringPrincipal'] = retiring_principal
        if operations is not None:
            params['Operations'] = operations
        if constraints is not None:
            params['Constraints'] = constraints
        if grant_tokens is not None:
            params['GrantTokens'] = grant_tokens
        return self.make_request(action='CreateGrant',
                                 body=json.dumps(params))

    def create_key(self, policy=None, description=None, key_usage=None):
        """
        Creates a customer master key. Customer master keys can be
        used to encrypt small amounts of data (less than 4K) directly,
        but they are most commonly used to encrypt or envelope data
        keys that are then used to encrypt customer data. For more
        information about data keys, see GenerateDataKey and
        GenerateDataKeyWithoutPlaintext.

        :type policy: string
        :param policy: Policy to be attached to the key. This is required and
            delegates back to the account. The key is the root of trust.

        :type description: string
        :param description: Description of the key. We recommend that you
            choose a description that helps your customer decide whether the
            key is appropriate for a task.

        :type key_usage: string
        :param key_usage: Specifies the intended use of the key. Currently this
            defaults to ENCRYPT/DECRYPT, and only symmetric encryption and
            decryption are supported.

        """
        params = {}
        if policy is not None:
            params['Policy'] = policy
        if description is not None:
            params['Description'] = description
        if key_usage is not None:
            params['KeyUsage'] = key_usage
        return self.make_request(action='CreateKey',
                                 body=json.dumps(params))

    def decrypt(self, ciphertext_blob, encryption_context=None,
                grant_tokens=None):
        """
        Decrypts ciphertext. Ciphertext is plaintext that has been
        previously encrypted by using the Encrypt function.

        :type ciphertext_blob: blob
        :param ciphertext_blob: Ciphertext including metadata.

        :type encryption_context: map
        :param encryption_context: The encryption context. If this was
            specified in the Encrypt function, it must be specified here or the
            decryption operation will fail. For more information, see
            `Encryption Context`_.

        :type grant_tokens: list
        :param grant_tokens: A list of grant tokens that represent grants which
            can be used to provide long term permissions to perform decryption.

        """
        if not isinstance(ciphertext_blob, six.binary_type):
            raise TypeError(
                "Value of argument ``ciphertext_blob`` "
                "must be of type %s." % six.binary_type)
        ciphertext_blob = base64.b64encode(ciphertext_blob)
        params = {'CiphertextBlob': ciphertext_blob.decode('utf-8'), }
        if encryption_context is not None:
            params['EncryptionContext'] = encryption_context
        if grant_tokens is not None:
            params['GrantTokens'] = grant_tokens
        response = self.make_request(action='Decrypt',
                                     body=json.dumps(params))
        if response.get('Plaintext') is not None:
            response['Plaintext'] = base64.b64decode(
                response['Plaintext'].encode('utf-8'))
        return response

    def delete_alias(self, alias_name):
        """
        Deletes the specified alias.

        :type alias_name: string
        :param alias_name: The alias to be deleted.

        """
        params = {'AliasName': alias_name, }
        return self.make_request(action='DeleteAlias',
                                 body=json.dumps(params))

    def describe_key(self, key_id):
        """
        Provides detailed information about the specified customer
        master key.

        :type key_id: string
        :param key_id: Unique identifier of the customer master key to be
            described. This can be an ARN, an alias, or a globally unique
            identifier.

        """
        params = {'KeyId': key_id, }
        return self.make_request(action='DescribeKey',
                                 body=json.dumps(params))

    def disable_key(self, key_id):
        """
        Marks a key as disabled, thereby preventing its use.

        :type key_id: string
        :param key_id: Unique identifier of the customer master key to be
            disabled. This can be an ARN, an alias, or a globally unique
            identifier.

        """
        params = {'KeyId': key_id, }
        return self.make_request(action='DisableKey',
                                 body=json.dumps(params))

    def disable_key_rotation(self, key_id):
        """
        Disables rotation of the specified key.

        :type key_id: string
        :param key_id: Unique identifier of the customer master key for which
            rotation is to be disabled. This can be an ARN, an alias, or a
            globally unique identifier.

        """
        params = {'KeyId': key_id, }
        return self.make_request(action='DisableKeyRotation',
                                 body=json.dumps(params))

    def enable_key(self, key_id):
        """
        Marks a key as enabled, thereby permitting its use. You can
        have up to 25 enabled keys at one time.

        :type key_id: string
        :param key_id: Unique identifier of the customer master key to be
            enabled. This can be an ARN, an alias, or a globally unique
            identifier.

        """
        params = {'KeyId': key_id, }
        return self.make_request(action='EnableKey',
                                 body=json.dumps(params))

    def enable_key_rotation(self, key_id):
        """
        Enables rotation of the specified customer master key.

        :type key_id: string
        :param key_id: Unique identifier of the customer master key for which
            rotation is to be enabled. This can be an ARN, an alias, or a
            globally unique identifier.

        """
        params = {'KeyId': key_id, }
        return self.make_request(action='EnableKeyRotation',
                                 body=json.dumps(params))

    def encrypt(self, key_id, plaintext, encryption_context=None,
                grant_tokens=None):
        """
        Encrypts plaintext into ciphertext by using a customer master
        key.

        :type key_id: string
        :param key_id: Unique identifier of the customer master. This can be an
            ARN, an alias, or the Key ID.

        :type plaintext: blob
        :param plaintext: Data to be encrypted.

        :type encryption_context: map
        :param encryption_context: Name:value pair that specifies the
            encryption context to be used for authenticated encryption. For
            more information, see `Authenticated Encryption`_.

        :type grant_tokens: list
        :param grant_tokens: A list of grant tokens that represent grants which
            can be used to provide long term permissions to perform encryption.

        """
        if not isinstance(plaintext, six.binary_type):
            raise TypeError(
                "Value of argument ``plaintext`` "
                "must be of type %s." % six.binary_type)
        plaintext = base64.b64encode(plaintext)
        params = {'KeyId': key_id, 'Plaintext': plaintext.decode('utf-8'), }
        if encryption_context is not None:
            params['EncryptionContext'] = encryption_context
        if grant_tokens is not None:
            params['GrantTokens'] = grant_tokens
        response = self.make_request(action='Encrypt',
                                     body=json.dumps(params))
        if response.get('CiphertextBlob') is not None:
            response['CiphertextBlob'] = base64.b64decode(
                response['CiphertextBlob'].encode('utf-8'))
        return response

    def generate_data_key(self, key_id, encryption_context=None,
                          number_of_bytes=None, key_spec=None,
                          grant_tokens=None):
        """
        Generates a secure data key. Data keys are used to encrypt and
        decrypt data. They are wrapped by customer master keys.

        :type key_id: string
        :param key_id: Unique identifier of the key. This can be an ARN, an
            alias, or a globally unique identifier.

        :type encryption_context: map
        :param encryption_context: Name/value pair that contains additional
            data to be authenticated during the encryption and decryption
            processes that use the key. This value is logged by AWS CloudTrail
            to provide context around the data encrypted by the key.

        :type number_of_bytes: integer
        :param number_of_bytes: Integer that contains the number of bytes to
            generate. Common values are 128, 256, 512, 1024 and so on. 1024 is
            the current limit.

        :type key_spec: string
        :param key_spec: Value that identifies the encryption algorithm and key
            size to generate a data key for. Currently this can be AES_128 or
            AES_256.

        :type grant_tokens: list
        :param grant_tokens: A list of grant tokens that represent grants which
            can be used to provide long term permissions to generate a key.

        """
        params = {'KeyId': key_id, }
        if encryption_context is not None:
            params['EncryptionContext'] = encryption_context
        if number_of_bytes is not None:
            params['NumberOfBytes'] = number_of_bytes
        if key_spec is not None:
            params['KeySpec'] = key_spec
        if grant_tokens is not None:
            params['GrantTokens'] = grant_tokens
        response = self.make_request(action='GenerateDataKey',
                                     body=json.dumps(params))
        if response.get('CiphertextBlob') is not None:
            response['CiphertextBlob'] = base64.b64decode(
                response['CiphertextBlob'].encode('utf-8'))
        if response.get('Plaintext') is not None:
            response['Plaintext'] = base64.b64decode(
                response['Plaintext'].encode('utf-8'))
        return response

    def generate_data_key_without_plaintext(self, key_id,
                                            encryption_context=None,
                                            key_spec=None,
                                            number_of_bytes=None,
                                            grant_tokens=None):
        """
        Returns a key wrapped by a customer master key without the
        plaintext copy of that key. To retrieve the plaintext, see
        GenerateDataKey.

        :type key_id: string
        :param key_id: Unique identifier of the key. This can be an ARN, an
            alias, or a globally unique identifier.

        :type encryption_context: map
        :param encryption_context: Name:value pair that contains additional
            data to be authenticated during the encryption and decryption
            processes.

        :type key_spec: string
        :param key_spec: Value that identifies the encryption algorithm and key
            size. Currently this can be AES_128 or AES_256.

        :type number_of_bytes: integer
        :param number_of_bytes: Integer that contains the number of bytes to
            generate. Common values are 128, 256, 512, 1024 and so on.

        :type grant_tokens: list
        :param grant_tokens: A list of grant tokens that represent grants which
            can be used to provide long term permissions to generate a key.

        """
        params = {'KeyId': key_id, }
        if encryption_context is not None:
            params['EncryptionContext'] = encryption_context
        if key_spec is not None:
            params['KeySpec'] = key_spec
        if number_of_bytes is not None:
            params['NumberOfBytes'] = number_of_bytes
        if grant_tokens is not None:
            params['GrantTokens'] = grant_tokens
        response = self.make_request(action='GenerateDataKeyWithoutPlaintext',
                                     body=json.dumps(params))
        if response.get('CiphertextBlob') is not None:
            response['CiphertextBlob'] = base64.b64decode(
                response['CiphertextBlob'].encode('utf-8'))
        return response

    def generate_random(self, number_of_bytes=None):
        """
        Generates an unpredictable byte string.

        :type number_of_bytes: integer
        :param number_of_bytes: Integer that contains the number of bytes to
            generate. Common values are 128, 256, 512, 1024 and so on. The
            current limit is 1024 bytes.

        """
        params = {}
        if number_of_bytes is not None:
            params['NumberOfBytes'] = number_of_bytes
        response = self.make_request(action='GenerateRandom',
                                     body=json.dumps(params))
        if response.get('Plaintext') is not None:
            response['Plaintext'] = base64.b64decode(
                response['Plaintext'].encode('utf-8'))
        return response

    def get_key_policy(self, key_id, policy_name):
        """
        Retrieves a policy attached to the specified key.

        :type key_id: string
        :param key_id: Unique identifier of the key. This can be an ARN, an
            alias, or a globally unique identifier.

        :type policy_name: string
        :param policy_name: String that contains the name of the policy.
            Currently, this must be "default". Policy names can be discovered
            by calling ListKeyPolicies.

        """
        params = {'KeyId': key_id, 'PolicyName': policy_name, }
        return self.make_request(action='GetKeyPolicy',
                                 body=json.dumps(params))

    def get_key_rotation_status(self, key_id):
        """
        Retrieves a Boolean value that indicates whether key rotation
        is enabled for the specified key.

        :type key_id: string
        :param key_id: Unique identifier of the key. This can be an ARN, an
            alias, or a globally unique identifier.

        """
        params = {'KeyId': key_id, }
        return self.make_request(action='GetKeyRotationStatus',
                                 body=json.dumps(params))

    def list_aliases(self, limit=None, marker=None):
        """
        Lists all of the key aliases in the account.

        :type limit: integer
        :param limit: Specify this parameter when paginating results to
            indicate the maximum number of aliases you want in each response.
            If there are additional aliases beyond the maximum you specify, the
            `Truncated` response element will be set to `true.`

        :type marker: string
        :param marker: Use this parameter when paginating results, and only in
            a subsequent request after you've received a response where the
            results are truncated. Set it to the value of the `NextMarker`
            element in the response you just received.

        """
        params = {}
        if limit is not None:
            params['Limit'] = limit
        if marker is not None:
            params['Marker'] = marker
        return self.make_request(action='ListAliases',
                                 body=json.dumps(params))

    def list_grants(self, key_id, limit=None, marker=None):
        """
        List the grants for a specified key.

        :type key_id: string
        :param key_id: Unique identifier of the key. This can be an ARN, an
            alias, or a globally unique identifier.

        :type limit: integer
        :param limit: Specify this parameter only when paginating results to
            indicate the maximum number of grants you want listed in the
            response. If there are additional grants beyond the maximum you
            specify, the `Truncated` response element will be set to `true.`

        :type marker: string
        :param marker: Use this parameter only when paginating results, and
            only in a subsequent request after you've received a response where
            the results are truncated. Set it to the value of the `NextMarker`
            in the response you just received.

        """
        params = {'KeyId': key_id, }
        if limit is not None:
            params['Limit'] = limit
        if marker is not None:
            params['Marker'] = marker
        return self.make_request(action='ListGrants',
                                 body=json.dumps(params))

    def list_key_policies(self, key_id, limit=None, marker=None):
        """
        Retrieves a list of policies attached to a key.

        :type key_id: string
        :param key_id: Unique identifier of the key. This can be an ARN, an
            alias, or a globally unique identifier.

        :type limit: integer
        :param limit: Specify this parameter only when paginating results to
            indicate the maximum number of policies you want listed in the
            response. If there are additional policies beyond the maximum you
            specify, the `Truncated` response element will be set to `true.`

        :type marker: string
        :param marker: Use this parameter only when paginating results, and
            only in a subsequent request after you've received a response where
            the results are truncated. Set it to the value of the `NextMarker`
            in the response you just received.

        """
        params = {'KeyId': key_id, }
        if limit is not None:
            params['Limit'] = limit
        if marker is not None:
            params['Marker'] = marker
        return self.make_request(action='ListKeyPolicies',
                                 body=json.dumps(params))

    def list_keys(self, limit=None, marker=None):
        """
        Lists the customer master keys.

        :type limit: integer
        :param limit: Specify this parameter only when paginating results to
            indicate the maximum number of keys you want listed in the
            response. If there are additional keys beyond the maximum you
            specify, the `Truncated` response element will be set to `true.`

        :type marker: string
        :param marker: Use this parameter only when paginating results, and
            only in a subsequent request after you've received a response where
            the results are truncated. Set it to the value of the `NextMarker`
            in the response you just received.

        """
        params = {}
        if limit is not None:
            params['Limit'] = limit
        if marker is not None:
            params['Marker'] = marker
        return self.make_request(action='ListKeys',
                                 body=json.dumps(params))

    def put_key_policy(self, key_id, policy_name, policy):
        """
        Attaches a policy to the specified key.

        :type key_id: string
        :param key_id: Unique identifier of the key. This can be an ARN, an
            alias, or a globally unique identifier.

        :type policy_name: string
        :param policy_name: Name of the policy to be attached. Currently, the
            only supported name is "default".

        :type policy: string
        :param policy: The policy, in JSON format, to be attached to the key.

        """
        params = {
            'KeyId': key_id,
            'PolicyName': policy_name,
            'Policy': policy,
        }
        return self.make_request(action='PutKeyPolicy',
                                 body=json.dumps(params))

    def re_encrypt(self, ciphertext_blob, destination_key_id,
                   source_encryption_context=None,
                   destination_encryption_context=None, grant_tokens=None):
        """
        Encrypts data on the server side with a new customer master
        key without exposing the plaintext of the data on the client
        side. The data is first decrypted and then encrypted. This
        operation can also be used to change the encryption context of
        a ciphertext.

        :type ciphertext_blob: blob
        :param ciphertext_blob: Ciphertext of the data to re-encrypt.

        :type source_encryption_context: map
        :param source_encryption_context: Encryption context used to encrypt
            and decrypt the data specified in the `CiphertextBlob` parameter.

        :type destination_key_id: string
        :param destination_key_id: Key identifier of the key used to re-encrypt
            the data.

        :type destination_encryption_context: map
        :param destination_encryption_context: Encryption context to be used
            when the data is re-encrypted.

        :type grant_tokens: list
        :param grant_tokens: Grant tokens that identify the grants that have
            permissions for the encryption and decryption process.

        """
        if not isinstance(ciphertext_blob, six.binary_type):
            raise TypeError(
                "Value of argument ``ciphertext_blob`` "
                "must be of type %s." % six.binary_type)
        ciphertext_blob = base64.b64encode(ciphertext_blob)
        params = {
            'CiphertextBlob': ciphertext_blob,
            'DestinationKeyId': destination_key_id,
        }
        if source_encryption_context is not None:
            params['SourceEncryptionContext'] = source_encryption_context
        if destination_encryption_context is not None:
            params['DestinationEncryptionContext'] = destination_encryption_context
        if grant_tokens is not None:
            params['GrantTokens'] = grant_tokens
        response = self.make_request(action='ReEncrypt',
                                     body=json.dumps(params))
        if response.get('CiphertextBlob') is not None:
            response['CiphertextBlob'] = base64.b64decode(
                response['CiphertextBlob'].encode('utf-8'))
        return response

    def retire_grant(self, grant_token):
        """
        Retires a grant. You can retire a grant when you're done using
        it to clean up. You should revoke a grant when you intend to
        actively deny operations that depend on it.

        :type grant_token: string
        :param grant_token: Token that identifies the grant to be retired.

        """
        params = {'GrantToken': grant_token, }
        return self.make_request(action='RetireGrant',
                                 body=json.dumps(params))

    def revoke_grant(self, key_id, grant_id):
        """
        Revokes a grant. You can revoke a grant to actively deny
        operations that depend on it.

        :type key_id: string
        :param key_id: Unique identifier of the key associated with the grant.

        :type grant_id: string
        :param grant_id: Identifier of the grant to be revoked.

        """
        params = {'KeyId': key_id, 'GrantId': grant_id, }
        return self.make_request(action='RevokeGrant',
                                 body=json.dumps(params))

    def update_key_description(self, key_id, description):
        """
        

        :type key_id: string
        :param key_id:

        :type description: string
        :param description:

        """
        params = {'KeyId': key_id, 'Description': description, }
        return self.make_request(action='UpdateKeyDescription',
                                 body=json.dumps(params))

    def make_request(self, action, body):
        headers = {
            'X-Amz-Target': '%s.%s' % (self.TargetPrefix, action),
            'Host': self.region.endpoint,
            'Content-Type': 'application/x-amz-json-1.1',
            'Content-Length': str(len(body)),
        }
        http_request = self.build_base_http_request(
            method='POST', path='/', auth_path='/', params={},
            headers=headers, data=body)
        response = self._mexe(http_request, sender=None,
                              override_num_retries=10)
        response_body = response.read().decode('utf-8')
        boto.log.debug(response_body)
        if response.status == 200:
            if response_body:
                return json.loads(response_body)
        else:
            json_body = json.loads(response_body)
            fault_name = json_body.get('__type', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)

