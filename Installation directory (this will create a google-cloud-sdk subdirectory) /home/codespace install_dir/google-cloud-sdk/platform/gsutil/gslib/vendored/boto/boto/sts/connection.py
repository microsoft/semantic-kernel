# Copyright (c) 2011 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2011, Eucalyptus Systems, Inc.
# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

from boto.connection import AWSQueryConnection
from boto.provider import Provider, NO_CREDENTIALS_PROVIDED
from boto.regioninfo import RegionInfo
from boto.sts.credentials import Credentials, FederationToken, AssumedRole
from boto.sts.credentials import DecodeAuthorizationMessage
import boto
import boto.utils
import datetime
import threading

_session_token_cache = {}


class STSConnection(AWSQueryConnection):
    """
    AWS Security Token Service
    The AWS Security Token Service is a web service that enables you
    to request temporary, limited-privilege credentials for AWS
    Identity and Access Management (IAM) users or for users that you
    authenticate (federated users). This guide provides descriptions
    of the AWS Security Token Service API.

    For more detailed information about using this service, go to
    `Using Temporary Security Credentials`_.

    For information about setting up signatures and authorization
    through the API, go to `Signing AWS API Requests`_ in the AWS
    General Reference . For general information about the Query API,
    go to `Making Query Requests`_ in Using IAM . For information
    about using security tokens with other AWS products, go to `Using
    Temporary Security Credentials to Access AWS`_ in Using Temporary
    Security Credentials .

    If you're new to AWS and need additional technical information
    about a specific AWS product, you can find the product's technical
    documentation at `http://aws.amazon.com/documentation/`_.

    We will refer to Amazon Identity and Access Management using the
    abbreviated form IAM. All copyrights and legal protections still
    apply.
    """
    DefaultRegionName = 'us-east-1'
    DefaultRegionEndpoint = 'sts.amazonaws.com'
    APIVersion = '2011-06-15'

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 converter=None, validate_certs=True, anon=False,
                 security_token=None, profile_name=None):
        """
        :type anon: boolean
        :param anon: If this parameter is True, the ``STSConnection`` object
            will make anonymous requests, and it will not use AWS
            Credentials or even search for AWS Credentials to make these
            requests.
        """
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint,
                                connection_cls=STSConnection)
        self.region = region
        self.anon = anon
        self._mutex = threading.Semaphore()
        provider = 'aws'
        # If an anonymous request is sent, do not try to look for credentials.
        # So we pass in dummy values for the access key id, secret access
        # key, and session token. It does not matter that they are
        # not actual values because the request is anonymous.
        if self.anon:
            provider = Provider('aws', NO_CREDENTIALS_PROVIDED,
                                NO_CREDENTIALS_PROVIDED,
                                NO_CREDENTIALS_PROVIDED)
        super(STSConnection, self).__init__(aws_access_key_id,
                                    aws_secret_access_key,
                                    is_secure, port, proxy, proxy_port,
                                    proxy_user, proxy_pass,
                                    self.region.endpoint, debug,
                                    https_connection_factory, path,
                                    validate_certs=validate_certs,
                                    security_token=security_token,
                                    profile_name=profile_name,
                                    provider=provider)

    def _required_auth_capability(self):
        if self.anon:
            return ['sts-anon']
        else:
            return ['hmac-v4']

    def _check_token_cache(self, token_key, duration=None, window_seconds=60):
        token = _session_token_cache.get(token_key, None)
        if token:
            now = datetime.datetime.utcnow()
            expires = boto.utils.parse_ts(token.expiration)
            delta = expires - now
            if delta < datetime.timedelta(seconds=window_seconds):
                msg = 'Cached session token %s is expired' % token_key
                boto.log.debug(msg)
                token = None
        return token

    def _get_session_token(self, duration=None,
                           mfa_serial_number=None, mfa_token=None):
        params = {}
        if duration:
            params['DurationSeconds'] = duration
        if mfa_serial_number:
            params['SerialNumber'] = mfa_serial_number
        if mfa_token:
            params['TokenCode'] = mfa_token
        return self.get_object('GetSessionToken', params,
                                Credentials, verb='POST')

    def get_session_token(self, duration=None, force_new=False,
                          mfa_serial_number=None, mfa_token=None):
        """
        Return a valid session token.  Because retrieving new tokens
        from the Secure Token Service is a fairly heavyweight operation
        this module caches previously retrieved tokens and returns
        them when appropriate.  Each token is cached with a key
        consisting of the region name of the STS endpoint
        concatenated with the requesting user's access id.  If there
        is a token in the cache meeting with this key, the session
        expiration is checked to make sure it is still valid and if
        so, the cached token is returned.  Otherwise, a new session
        token is requested from STS and it is placed into the cache
        and returned.

        :type duration: int
        :param duration: The number of seconds the credentials should
            remain valid.

        :type force_new: bool
        :param force_new: If this parameter is True, a new session token
            will be retrieved from the Secure Token Service regardless
            of whether there is a valid cached token or not.

        :type mfa_serial_number: str
        :param mfa_serial_number: The serial number of an MFA device.
            If this is provided and if the mfa_passcode provided is
            valid, the temporary session token will be authorized with
            to perform operations requiring the MFA device authentication.

        :type mfa_token: str
        :param mfa_token: The 6 digit token associated with the
            MFA device.
        """
        token_key = '%s:%s' % (self.region.name, self.provider.access_key)
        token = self._check_token_cache(token_key, duration)
        if force_new or not token:
            boto.log.debug('fetching a new token for %s' % token_key)
            try:
                self._mutex.acquire()
                token = self._get_session_token(duration,
                                                mfa_serial_number,
                                                mfa_token)
                _session_token_cache[token_key] = token
            finally:
                self._mutex.release()
        return token

    def get_federation_token(self, name, duration=None, policy=None):
        """
        Returns a set of temporary security credentials (consisting of
        an access key ID, a secret access key, and a security token)
        for a federated user. A typical use is in a proxy application
        that is getting temporary security credentials on behalf of
        distributed applications inside a corporate network. Because
        you must call the `GetFederationToken` action using the long-
        term security credentials of an IAM user, this call is
        appropriate in contexts where those credentials can be safely
        stored, usually in a server-based application.

        **Note:** Do not use this call in mobile applications or
        client-based web applications that directly get temporary
        security credentials. For those types of applications, use
        `AssumeRoleWithWebIdentity`.

        The `GetFederationToken` action must be called by using the
        long-term AWS security credentials of the AWS account or an
        IAM user. Credentials that are created by IAM users are valid
        for the specified duration, between 900 seconds (15 minutes)
        and 129600 seconds (36 hours); credentials that are created by
        using account credentials have a maximum duration of 3600
        seconds (1 hour).

        The permissions that are granted to the federated user are the
        intersection of the policy that is passed with the
        `GetFederationToken` request and policies that are associated
        with of the entity making the `GetFederationToken` call.

        For more information about how permissions work, see
        `Controlling Permissions in Temporary Credentials`_ in Using
        Temporary Security Credentials . For information about using
        `GetFederationToken` to create temporary security credentials,
        see `Creating Temporary Credentials to Enable Access for
        Federated Users`_ in Using Temporary Security Credentials .

        :type name: string
        :param name: The name of the federated user. The name is used as an
            identifier for the temporary security credentials (such as `Bob`).
            For example, you can reference the federated user name in a
            resource-based policy, such as in an Amazon S3 bucket policy.

        :type policy: string
        :param policy: A policy that specifies the permissions that are granted
            to the federated user. By default, federated users have no
            permissions; they do not inherit any from the IAM user. When you
            specify a policy, the federated user's permissions are intersection
            of the specified policy and the IAM user's policy. If you don't
            specify a policy, federated users can only access AWS resources
            that explicitly allow those federated users in a resource policy,
            such as in an Amazon S3 bucket policy.

        :type duration: integer
        :param duration: The duration, in seconds, that the session
            should last. Acceptable durations for federation sessions range
            from 900 seconds (15 minutes) to 129600 seconds (36 hours), with
            43200 seconds (12 hours) as the default. Sessions for AWS account
            owners are restricted to a maximum of 3600 seconds (one hour). If
            the duration is longer than one hour, the session for AWS account
            owners defaults to one hour.

        """
        params = {'Name': name}
        if duration:
            params['DurationSeconds'] = duration
        if policy:
            params['Policy'] = policy
        return self.get_object('GetFederationToken', params,
                                FederationToken, verb='POST')

    def assume_role(self, role_arn, role_session_name, policy=None,
                    duration_seconds=None, external_id=None,
                    mfa_serial_number=None,
                    mfa_token=None):
        """
        Returns a set of temporary security credentials (consisting of
        an access key ID, a secret access key, and a security token)
        that you can use to access AWS resources that you might not
        normally have access to. Typically, you use `AssumeRole` for
        cross-account access or federation.

        For cross-account access, imagine that you own multiple
        accounts and need to access resources in each account. You
        could create long-term credentials in each account to access
        those resources. However, managing all those credentials and
        remembering which one can access which account can be time
        consuming. Instead, you can create one set of long-term
        credentials in one account and then use temporary security
        credentials to access all the other accounts by assuming roles
        in those accounts. For more information about roles, see
        `Roles`_ in Using IAM .

        For federation, you can, for example, grant single sign-on
        access to the AWS Management Console. If you already have an
        identity and authentication system in your corporate network,
        you don't have to recreate user identities in AWS in order to
        grant those user identities access to AWS. Instead, after a
        user has been authenticated, you call `AssumeRole` (and
        specify the role with the appropriate permissions) to get
        temporary security credentials for that user. With those
        temporary security credentials, you construct a sign-in URL
        that users can use to access the console. For more
        information, see `Scenarios for Granting Temporary Access`_ in
        AWS Security Token Service .

        The temporary security credentials are valid for the duration
        that you specified when calling `AssumeRole`, which can be
        from 900 seconds (15 minutes) to 3600 seconds (1 hour). The
        default is 1 hour.

        The temporary security credentials that are returned from the
        `AssumeRoleWithWebIdentity` response have the permissions that
        are associated with the access policy of the role being
        assumed and any policies that are associated with the AWS
        resource being accessed. You can further restrict the
        permissions of the temporary security credentials by passing a
        policy in the request. The resulting permissions are an
        intersection of the role's access policy and the policy that
        you passed. These policies and any applicable resource-based
        policies are evaluated when calls to AWS service APIs are made
        using the temporary security credentials.

        To assume a role, your AWS account must be trusted by the
        role. The trust relationship is defined in the role's trust
        policy when the IAM role is created. You must also have a
        policy that allows you to call `sts:AssumeRole`.

        **Important:** You cannot call `Assumerole` by using AWS
        account credentials; access will be denied. You must use IAM
        user credentials to call `AssumeRole`.

        :type role_arn: string
        :param role_arn: The Amazon Resource Name (ARN) of the role that the
            caller is assuming.

        :type role_session_name: string
        :param role_session_name: An identifier for the assumed role session.
            The session name is included as part of the `AssumedRoleUser`.

        :type policy: string
        :param policy: A supplemental policy that is associated with the
            temporary security credentials from the `AssumeRole` call. The
            resulting permissions of the temporary security credentials are an
            intersection of this policy and the access policy that is
            associated with the role. Use this policy to further restrict the
            permissions of the temporary security credentials.

        :type duration_seconds: integer
        :param duration_seconds: The duration, in seconds, of the role session.
            The value can range from 900 seconds (15 minutes) to 3600 seconds
            (1 hour). By default, the value is set to 3600 seconds.

        :type external_id: string
        :param external_id: A unique identifier that is used by third parties
            to assume a role in their customers' accounts. For each role that
            the third party can assume, they should instruct their customers to
            create a role with the external ID that the third party generated.
            Each time the third party assumes the role, they must pass the
            customer's external ID. The external ID is useful in order to help
            third parties bind a role to the customer who created it. For more
            information about the external ID, see `About the External ID`_ in
            Using Temporary Security Credentials .

        :type mfa_serial_number: string
        :param mfa_serial_number: The identification number of the MFA device that
            is associated with the user who is making the AssumeRole call.
            Specify this value if the trust policy of the role being assumed
            includes a condition that requires MFA authentication. The value is
            either the serial number for a hardware device (such as
            GAHT12345678) or an Amazon Resource Name (ARN) for a virtual device
            (such as arn:aws:iam::123456789012:mfa/user). Minimum length of 9.
            Maximum length of 256.

        :type mfa_token: string
        :param mfa_token: The value provided by the MFA device, if the trust
            policy of the role being assumed requires MFA (that is, if the
            policy includes a condition that tests for MFA). If the role being
            assumed requires MFA and if the TokenCode value is missing or
            expired, the AssumeRole call returns an "access denied" errror.
            Minimum length of 6. Maximum length of 6.

        """
        params = {
            'RoleArn': role_arn,
            'RoleSessionName': role_session_name
        }
        if policy is not None:
            params['Policy'] = policy
        if duration_seconds is not None:
            params['DurationSeconds'] = duration_seconds
        if external_id is not None:
            params['ExternalId'] = external_id
        if mfa_serial_number is not None:
            params['SerialNumber'] = mfa_serial_number
        if mfa_token is not None:
            params['TokenCode'] = mfa_token
        return self.get_object('AssumeRole', params, AssumedRole, verb='POST')

    def assume_role_with_saml(self, role_arn, principal_arn, saml_assertion,
                              policy=None, duration_seconds=None):
        """
        Returns a set of temporary security credentials for users who
        have been authenticated via a SAML authentication response.
        This operation provides a mechanism for tying an enterprise
        identity store or directory to role-based AWS access without
        user-specific credentials or configuration.

        The temporary security credentials returned by this operation
        consist of an access key ID, a secret access key, and a
        security token. Applications can use these temporary security
        credentials to sign calls to AWS services. The credentials are
        valid for the duration that you specified when calling
        `AssumeRoleWithSAML`, which can be up to 3600 seconds (1 hour)
        or until the time specified in the SAML authentication
        response's `NotOnOrAfter` value, whichever is shorter.

        The maximum duration for a session is 1 hour, and the minimum
        duration is 15 minutes, even if values outside this range are
        specified.

        Optionally, you can pass an AWS IAM access policy to this
        operation. The temporary security credentials that are
        returned by the operation have the permissions that are
        associated with the access policy of the role being assumed,
        except for any permissions explicitly denied by the policy you
        pass. This gives you a way to further restrict the permissions
        for the federated user. These policies and any applicable
        resource-based policies are evaluated when calls to AWS are
        made using the temporary security credentials.

        Before your application can call `AssumeRoleWithSAML`, you
        must configure your SAML identity provider (IdP) to issue the
        claims required by AWS. Additionally, you must use AWS
        Identity and Access Management (AWS IAM) to create a SAML
        provider entity in your AWS account that represents your
        identity provider, and create an AWS IAM role that specifies
        this SAML provider in its trust policy.

        Calling `AssumeRoleWithSAML` does not require the use of AWS
        security credentials. The identity of the caller is validated
        by using keys in the metadata document that is uploaded for
        the SAML provider entity for your identity provider.

        For more information, see the following resources:


        + `Creating Temporary Security Credentials for SAML
          Federation`_ in the Using Temporary Security Credentials
          guide.
        + `SAML Providers`_ in the Using IAM guide.
        + `Configuring a Relying Party and Claims in the Using IAM
          guide. `_
        + `Creating a Role for SAML-Based Federation`_ in the Using
          IAM guide.

        :type role_arn: string
        :param role_arn: The Amazon Resource Name (ARN) of the role that the
            caller is assuming.

        :type principal_arn: string
        :param principal_arn: The Amazon Resource Name (ARN) of the SAML
            provider in AWS IAM that describes the IdP.

        :type saml_assertion: string
        :param saml_assertion: The base-64 encoded SAML authentication response
            provided by the IdP.
        For more information, see `Configuring a Relying Party and Adding
            Claims`_ in the Using IAM guide.

        :type policy: string
        :param policy:
        An AWS IAM policy in JSON format.

        The temporary security credentials that are returned by this operation
            have the permissions that are associated with the access policy of
            the role being assumed, except for any permissions explicitly
            denied by the policy you pass. These policies and any applicable
            resource-based policies are evaluated when calls to AWS are made
            using the temporary security credentials.

        The policy must be 2048 bytes or shorter, and its packed size must be
            less than 450 bytes.

        :type duration_seconds: integer
        :param duration_seconds:
        The duration, in seconds, of the role session. The value can range from
            900 seconds (15 minutes) to 3600 seconds (1 hour). By default, the
            value is set to 3600 seconds. An expiration can also be specified
            in the SAML authentication response's `NotOnOrAfter` value. The
            actual expiration time is whichever value is shorter.

        The maximum duration for a session is 1 hour, and the minimum duration
            is 15 minutes, even if values outside this range are specified.

        """
        params = {
            'RoleArn': role_arn,
            'PrincipalArn': principal_arn,
            'SAMLAssertion': saml_assertion,
        }
        if policy is not None:
            params['Policy'] = policy
        if duration_seconds is not None:
            params['DurationSeconds'] = duration_seconds
        return self.get_object('AssumeRoleWithSAML', params, AssumedRole,
                               verb='POST')

    def assume_role_with_web_identity(self, role_arn, role_session_name,
                                      web_identity_token, provider_id=None,
                                      policy=None, duration_seconds=None):
        """
        Returns a set of temporary security credentials for users who
        have been authenticated in a mobile or web application with a
        web identity provider, such as Login with Amazon, Facebook, or
        Google. `AssumeRoleWithWebIdentity` is an API call that does
        not require the use of AWS security credentials. Therefore,
        you can distribute an application (for example, on mobile
        devices) that requests temporary security credentials without
        including long-term AWS credentials in the application or by
        deploying server-based proxy services that use long-term AWS
        credentials. For more information, see `Creating a Mobile
        Application with Third-Party Sign-In`_ in AWS Security Token
        Service .

        The temporary security credentials consist of an access key
        ID, a secret access key, and a security token. Applications
        can use these temporary security credentials to sign calls to
        AWS service APIs. The credentials are valid for the duration
        that you specified when calling `AssumeRoleWithWebIdentity`,
        which can be from 900 seconds (15 minutes) to 3600 seconds (1
        hour). By default, the temporary security credentials are
        valid for 1 hour.

        The temporary security credentials that are returned from the
        `AssumeRoleWithWebIdentity` response have the permissions that
        are associated with the access policy of the role being
        assumed. You can further restrict the permissions of the
        temporary security credentials by passing a policy in the
        request. The resulting permissions are an intersection of the
        role's access policy and the policy that you passed. These
        policies and any applicable resource-based policies are
        evaluated when calls to AWS service APIs are made using the
        temporary security credentials.

        Before your application can call `AssumeRoleWithWebIdentity`,
        you must have an identity token from a supported identity
        provider and create a role that the application can assume.
        The role that your application assumes must trust the identity
        provider that is associated with the identity token. In other
        words, the identity provider must be specified in the role's
        trust policy. For more information, see ` Creating Temporary
        Security Credentials for Mobile Apps Using Third-Party
        Identity Providers`_.

        :type role_arn: string
        :param role_arn: The Amazon Resource Name (ARN) of the role that the
            caller is assuming.

        :type role_session_name: string
        :param role_session_name: An identifier for the assumed role session.
            Typically, you pass the name or identifier that is associated with
            the user who is using your application. That way, the temporary
            security credentials that your application will use are associated
            with that user. This session name is included as part of the ARN
            and assumed role ID in the `AssumedRoleUser` response element.

        :type web_identity_token: string
        :param web_identity_token: The OAuth 2.0 access token or OpenID Connect
            ID token that is provided by the identity provider. Your
            application must get this token by authenticating the user who is
            using your application with a web identity provider before the
            application makes an `AssumeRoleWithWebIdentity` call.

        :type provider_id: string
        :param provider_id: Specify this value only for OAuth access tokens. Do
            not specify this value for OpenID Connect ID tokens, such as
            `accounts.google.com`. This is the fully-qualified host component
            of the domain name of the identity provider. Do not include URL
            schemes and port numbers. Currently, `www.amazon.com` and
            `graph.facebook.com` are supported.

        :type policy: string
        :param policy: A supplemental policy that is associated with the
            temporary security credentials from the `AssumeRoleWithWebIdentity`
            call. The resulting permissions of the temporary security
            credentials are an intersection of this policy and the access
            policy that is associated with the role. Use this policy to further
            restrict the permissions of the temporary security credentials.

        :type duration_seconds: integer
        :param duration_seconds: The duration, in seconds, of the role session.
            The value can range from 900 seconds (15 minutes) to 3600 seconds
            (1 hour). By default, the value is set to 3600 seconds.

        """
        params = {
            'RoleArn': role_arn,
            'RoleSessionName': role_session_name,
            'WebIdentityToken': web_identity_token,
        }
        if provider_id is not None:
            params['ProviderId'] = provider_id
        if policy is not None:
            params['Policy'] = policy
        if duration_seconds is not None:
            params['DurationSeconds'] = duration_seconds
        return self.get_object(
            'AssumeRoleWithWebIdentity',
            params,
            AssumedRole,
            verb='POST'
        )

    def decode_authorization_message(self, encoded_message):
        """
        Decodes additional information about the authorization status
        of a request from an encoded message returned in response to
        an AWS request.

        For example, if a user is not authorized to perform an action
        that he or she has requested, the request returns a
        `Client.UnauthorizedOperation` response (an HTTP 403
        response). Some AWS actions additionally return an encoded
        message that can provide details about this authorization
        failure.
        Only certain AWS actions return an encoded authorization
        message. The documentation for an individual action indicates
        whether that action returns an encoded message in addition to
        returning an HTTP code.
        The message is encoded because the details of the
        authorization status can constitute privileged information
        that the user who requested the action should not see. To
        decode an authorization status message, a user must be granted
        permissions via an IAM policy to request the
        `DecodeAuthorizationMessage` (
        `sts:DecodeAuthorizationMessage`) action.

        The decoded message includes the following type of
        information:


        + Whether the request was denied due to an explicit deny or
          due to the absence of an explicit allow. For more information,
          see `Determining Whether a Request is Allowed or Denied`_ in
          Using IAM .
        + The principal who made the request.
        + The requested action.
        + The requested resource.
        + The values of condition keys in the context of the user's
          request.

        :type encoded_message: string
        :param encoded_message: The encoded message that was returned with the
            response.

        """
        params = {
            'EncodedMessage': encoded_message,
        }
        return self.get_object(
            'DecodeAuthorizationMessage',
            params,
            DecodeAuthorizationMessage,
            verb='POST'
        )
