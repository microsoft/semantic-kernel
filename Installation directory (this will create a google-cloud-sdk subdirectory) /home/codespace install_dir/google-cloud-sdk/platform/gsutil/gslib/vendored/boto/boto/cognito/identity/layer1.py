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
from boto.cognito.identity import exceptions


class CognitoIdentityConnection(AWSQueryConnection):
    """
    Amazon Cognito
    Amazon Cognito is a web service that delivers scoped temporary
    credentials to mobile devices and other untrusted environments.
    Amazon Cognito uniquely identifies a device and supplies the user
    with a consistent identity over the lifetime of an application.

    Using Amazon Cognito, you can enable authentication with one or
    more third-party identity providers (Facebook, Google, or Login
    with Amazon), and you can also choose to support unauthenticated
    access from your app. Cognito delivers a unique identifier for
    each user and acts as an OpenID token provider trusted by AWS
    Security Token Service (STS) to access temporary, limited-
    privilege AWS credentials.

    To provide end-user credentials, first make an unsigned call to
    GetId. If the end user is authenticated with one of the supported
    identity providers, set the `Logins` map with the identity
    provider token. `GetId` returns a unique identifier for the user.

    Next, make an unsigned call to GetOpenIdToken, which returns the
    OpenID token necessary to call STS and retrieve AWS credentials.
    This call expects the same `Logins` map as the `GetId` call, as
    well as the `IdentityID` originally returned by `GetId`. The token
    returned by `GetOpenIdToken` can be passed to the STS operation
    `AssumeRoleWithWebIdentity`_ to retrieve AWS credentials.
    """
    APIVersion = "2014-06-30"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "cognito-identity.us-east-1.amazonaws.com"
    ServiceName = "CognitoIdentity"
    TargetPrefix = "AWSCognitoIdentityService"
    ResponseError = JSONResponseError

    _faults = {
        "LimitExceededException": exceptions.LimitExceededException,
        "ResourceConflictException": exceptions.ResourceConflictException,
        "DeveloperUserAlreadyRegisteredException": exceptions.DeveloperUserAlreadyRegisteredException,
        "TooManyRequestsException": exceptions.TooManyRequestsException,
        "InvalidParameterException": exceptions.InvalidParameterException,
        "ResourceNotFoundException": exceptions.ResourceNotFoundException,
        "InternalErrorException": exceptions.InternalErrorException,
        "NotAuthorizedException": exceptions.NotAuthorizedException,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs or kwargs['host'] is None:
            kwargs['host'] = region.endpoint

        super(CognitoIdentityConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def create_identity_pool(self, identity_pool_name,
                             allow_unauthenticated_identities,
                             supported_login_providers=None,
                             developer_provider_name=None,
                             open_id_connect_provider_ar_ns=None):
        """
        Creates a new identity pool. The identity pool is a store of
        user identity information that is specific to your AWS
        account. The limit on identity pools is 60 per account.

        :type identity_pool_name: string
        :param identity_pool_name: A string that you provide.

        :type allow_unauthenticated_identities: boolean
        :param allow_unauthenticated_identities: TRUE if the identity pool
            supports unauthenticated logins.

        :type supported_login_providers: map
        :param supported_login_providers: Optional key:value pairs mapping
            provider names to provider app IDs.

        :type developer_provider_name: string
        :param developer_provider_name: The "domain" by which Cognito will
            refer to your users. This name acts as a placeholder that allows
            your backend and the Cognito service to communicate about the
            developer provider. For the `DeveloperProviderName`, you can use
            letters as well as period ( `.`), underscore ( `_`), and dash (
            `-`).
        Once you have set a developer provider name, you cannot change it.
            Please take care in setting this parameter.

        :type open_id_connect_provider_ar_ns: list
        :param open_id_connect_provider_ar_ns:

        """
        params = {
            'IdentityPoolName': identity_pool_name,
            'AllowUnauthenticatedIdentities': allow_unauthenticated_identities,
        }
        if supported_login_providers is not None:
            params['SupportedLoginProviders'] = supported_login_providers
        if developer_provider_name is not None:
            params['DeveloperProviderName'] = developer_provider_name
        if open_id_connect_provider_ar_ns is not None:
            params['OpenIdConnectProviderARNs'] = open_id_connect_provider_ar_ns
        return self.make_request(action='CreateIdentityPool',
                                 body=json.dumps(params))

    def delete_identity_pool(self, identity_pool_id):
        """
        Deletes a user pool. Once a pool is deleted, users will not be
        able to authenticate with the pool.

        :type identity_pool_id: string
        :param identity_pool_id: An identity pool ID in the format REGION:GUID.

        """
        params = {'IdentityPoolId': identity_pool_id, }
        return self.make_request(action='DeleteIdentityPool',
                                 body=json.dumps(params))

    def describe_identity_pool(self, identity_pool_id):
        """
        Gets details about a particular identity pool, including the
        pool name, ID description, creation date, and current number
        of users.

        :type identity_pool_id: string
        :param identity_pool_id: An identity pool ID in the format REGION:GUID.

        """
        params = {'IdentityPoolId': identity_pool_id, }
        return self.make_request(action='DescribeIdentityPool',
                                 body=json.dumps(params))

    def get_id(self, account_id, identity_pool_id, logins=None):
        """
        Generates (or retrieves) a Cognito ID. Supplying multiple
        logins will create an implicit linked account.

        :type account_id: string
        :param account_id: A standard AWS account ID (9+ digits).

        :type identity_pool_id: string
        :param identity_pool_id: An identity pool ID in the format REGION:GUID.

        :type logins: map
        :param logins: A set of optional name-value pairs that map provider
            names to provider tokens.
        The available provider names for `Logins` are as follows:

        + Facebook: `graph.facebook.com`
        + Google: `accounts.google.com`
        + Amazon: `www.amazon.com`

        """
        params = {
            'AccountId': account_id,
            'IdentityPoolId': identity_pool_id,
        }
        if logins is not None:
            params['Logins'] = logins
        return self.make_request(action='GetId',
                                 body=json.dumps(params))

    def get_open_id_token(self, identity_id, logins=None):
        """
        Gets an OpenID token, using a known Cognito ID. This known
        Cognito ID is returned by GetId. You can optionally add
        additional logins for the identity. Supplying multiple logins
        creates an implicit link.

        The OpenId token is valid for 15 minutes.

        :type identity_id: string
        :param identity_id: A unique identifier in the format REGION:GUID.

        :type logins: map
        :param logins: A set of optional name-value pairs that map provider
            names to provider tokens.

        """
        params = {'IdentityId': identity_id, }
        if logins is not None:
            params['Logins'] = logins
        return self.make_request(action='GetOpenIdToken',
                                 body=json.dumps(params))

    def get_open_id_token_for_developer_identity(self, identity_pool_id,
                                                 logins, identity_id=None,
                                                 token_duration=None):
        """
        Registers (or retrieves) a Cognito `IdentityId` and an OpenID
        Connect token for a user authenticated by your backend
        authentication process. Supplying multiple logins will create
        an implicit linked account. You can only specify one developer
        provider as part of the `Logins` map, which is linked to the
        identity pool. The developer provider is the "domain" by which
        Cognito will refer to your users.

        You can use `GetOpenIdTokenForDeveloperIdentity` to create a
        new identity and to link new logins (that is, user credentials
        issued by a public provider or developer provider) to an
        existing identity. When you want to create a new identity, the
        `IdentityId` should be null. When you want to associate a new
        login with an existing authenticated/unauthenticated identity,
        you can do so by providing the existing `IdentityId`. This API
        will create the identity in the specified `IdentityPoolId`.

        :type identity_pool_id: string
        :param identity_pool_id: An identity pool ID in the format REGION:GUID.

        :type identity_id: string
        :param identity_id: A unique identifier in the format REGION:GUID.

        :type logins: map
        :param logins: A set of optional name-value pairs that map provider
            names to provider tokens. Each name-value pair represents a user
            from a public provider or developer provider. If the user is from a
            developer provider, the name-value pair will follow the syntax
            `"developer_provider_name": "developer_user_identifier"`. The
            developer provider is the "domain" by which Cognito will refer to
            your users; you provided this domain while creating/updating the
            identity pool. The developer user identifier is an identifier from
            your backend that uniquely identifies a user. When you create an
            identity pool, you can specify the supported logins.

        :type token_duration: long
        :param token_duration: The expiration time of the token, in seconds.
            You can specify a custom expiration time for the token so that you
            can cache it. If you don't provide an expiration time, the token is
            valid for 15 minutes. You can exchange the token with Amazon STS
            for temporary AWS credentials, which are valid for a maximum of one
            hour. The maximum token duration you can set is 24 hours. You
            should take care in setting the expiration time for a token, as
            there are significant security implications: an attacker could use
            a leaked token to access your AWS resources for the token's
            duration.

        """
        params = {
            'IdentityPoolId': identity_pool_id,
            'Logins': logins,
        }
        if identity_id is not None:
            params['IdentityId'] = identity_id
        if token_duration is not None:
            params['TokenDuration'] = token_duration
        return self.make_request(action='GetOpenIdTokenForDeveloperIdentity',
                                 body=json.dumps(params))

    def list_identities(self, identity_pool_id, max_results, next_token=None):
        """
        Lists the identities in a pool.

        :type identity_pool_id: string
        :param identity_pool_id: An identity pool ID in the format REGION:GUID.

        :type max_results: integer
        :param max_results: The maximum number of identities to return.

        :type next_token: string
        :param next_token: A pagination token.

        """
        params = {
            'IdentityPoolId': identity_pool_id,
            'MaxResults': max_results,
        }
        if next_token is not None:
            params['NextToken'] = next_token
        return self.make_request(action='ListIdentities',
                                 body=json.dumps(params))

    def list_identity_pools(self, max_results, next_token=None):
        """
        Lists all of the Cognito identity pools registered for your
        account.

        :type max_results: integer
        :param max_results: The maximum number of identities to return.

        :type next_token: string
        :param next_token: A pagination token.

        """
        params = {'MaxResults': max_results, }
        if next_token is not None:
            params['NextToken'] = next_token
        return self.make_request(action='ListIdentityPools',
                                 body=json.dumps(params))

    def lookup_developer_identity(self, identity_pool_id, identity_id=None,
                                  developer_user_identifier=None,
                                  max_results=None, next_token=None):
        """
        Retrieves the `IdentityID` associated with a
        `DeveloperUserIdentifier` or the list of
        `DeveloperUserIdentifier`s associated with an `IdentityId` for
        an existing identity. Either `IdentityID` or
        `DeveloperUserIdentifier` must not be null. If you supply only
        one of these values, the other value will be searched in the
        database and returned as a part of the response. If you supply
        both, `DeveloperUserIdentifier` will be matched against
        `IdentityID`. If the values are verified against the database,
        the response returns both values and is the same as the
        request. Otherwise a `ResourceConflictException` is thrown.

        :type identity_pool_id: string
        :param identity_pool_id: An identity pool ID in the format REGION:GUID.

        :type identity_id: string
        :param identity_id: A unique identifier in the format REGION:GUID.

        :type developer_user_identifier: string
        :param developer_user_identifier: A unique ID used by your backend
            authentication process to identify a user. Typically, a developer
            identity provider would issue many developer user identifiers, in
            keeping with the number of users.

        :type max_results: integer
        :param max_results: The maximum number of identities to return.

        :type next_token: string
        :param next_token: A pagination token. The first call you make will
            have `NextToken` set to null. After that the service will return
            `NextToken` values as needed. For example, let's say you make a
            request with `MaxResults` set to 10, and there are 20 matches in
            the database. The service will return a pagination token as a part
            of the response. This token can be used to call the API again and
            get results starting from the 11th match.

        """
        params = {'IdentityPoolId': identity_pool_id, }
        if identity_id is not None:
            params['IdentityId'] = identity_id
        if developer_user_identifier is not None:
            params['DeveloperUserIdentifier'] = developer_user_identifier
        if max_results is not None:
            params['MaxResults'] = max_results
        if next_token is not None:
            params['NextToken'] = next_token
        return self.make_request(action='LookupDeveloperIdentity',
                                 body=json.dumps(params))

    def merge_developer_identities(self, source_user_identifier,
                                   destination_user_identifier,
                                   developer_provider_name, identity_pool_id):
        """
        Merges two users having different `IdentityId`s, existing in
        the same identity pool, and identified by the same developer
        provider. You can use this action to request that discrete
        users be merged and identified as a single user in the Cognito
        environment. Cognito associates the given source user (
        `SourceUserIdentifier`) with the `IdentityId` of the
        `DestinationUserIdentifier`. Only developer-authenticated
        users can be merged. If the users to be merged are associated
        with the same public provider, but as two different users, an
        exception will be thrown.

        :type source_user_identifier: string
        :param source_user_identifier: User identifier for the source user. The
            value should be a `DeveloperUserIdentifier`.

        :type destination_user_identifier: string
        :param destination_user_identifier: User identifier for the destination
            user. The value should be a `DeveloperUserIdentifier`.

        :type developer_provider_name: string
        :param developer_provider_name: The "domain" by which Cognito will
            refer to your users. This is a (pseudo) domain name that you
            provide while creating an identity pool. This name acts as a
            placeholder that allows your backend and the Cognito service to
            communicate about the developer provider. For the
            `DeveloperProviderName`, you can use letters as well as period (.),
            underscore (_), and dash (-).

        :type identity_pool_id: string
        :param identity_pool_id: An identity pool ID in the format REGION:GUID.

        """
        params = {
            'SourceUserIdentifier': source_user_identifier,
            'DestinationUserIdentifier': destination_user_identifier,
            'DeveloperProviderName': developer_provider_name,
            'IdentityPoolId': identity_pool_id,
        }
        return self.make_request(action='MergeDeveloperIdentities',
                                 body=json.dumps(params))

    def unlink_developer_identity(self, identity_id, identity_pool_id,
                                  developer_provider_name,
                                  developer_user_identifier):
        """
        Unlinks a `DeveloperUserIdentifier` from an existing identity.
        Unlinked developer users will be considered new identities
        next time they are seen. If, for a given Cognito identity, you
        remove all federated identities as well as the developer user
        identifier, the Cognito identity becomes inaccessible.

        :type identity_id: string
        :param identity_id: A unique identifier in the format REGION:GUID.

        :type identity_pool_id: string
        :param identity_pool_id: An identity pool ID in the format REGION:GUID.

        :type developer_provider_name: string
        :param developer_provider_name: The "domain" by which Cognito will
            refer to your users.

        :type developer_user_identifier: string
        :param developer_user_identifier: A unique ID used by your backend
            authentication process to identify a user.

        """
        params = {
            'IdentityId': identity_id,
            'IdentityPoolId': identity_pool_id,
            'DeveloperProviderName': developer_provider_name,
            'DeveloperUserIdentifier': developer_user_identifier,
        }
        return self.make_request(action='UnlinkDeveloperIdentity',
                                 body=json.dumps(params))

    def unlink_identity(self, identity_id, logins, logins_to_remove):
        """
        Unlinks a federated identity from an existing account.
        Unlinked logins will be considered new identities next time
        they are seen. Removing the last linked login will make this
        identity inaccessible.

        :type identity_id: string
        :param identity_id: A unique identifier in the format REGION:GUID.

        :type logins: map
        :param logins: A set of optional name-value pairs that map provider
            names to provider tokens.

        :type logins_to_remove: list
        :param logins_to_remove: Provider names to unlink from this identity.

        """
        params = {
            'IdentityId': identity_id,
            'Logins': logins,
            'LoginsToRemove': logins_to_remove,
        }
        return self.make_request(action='UnlinkIdentity',
                                 body=json.dumps(params))

    def update_identity_pool(self, identity_pool_id, identity_pool_name,
                             allow_unauthenticated_identities,
                             supported_login_providers=None,
                             developer_provider_name=None,
                             open_id_connect_provider_ar_ns=None):
        """
        Updates a user pool.

        :type identity_pool_id: string
        :param identity_pool_id: An identity pool ID in the format REGION:GUID.

        :type identity_pool_name: string
        :param identity_pool_name: A string that you provide.

        :type allow_unauthenticated_identities: boolean
        :param allow_unauthenticated_identities: TRUE if the identity pool
            supports unauthenticated logins.

        :type supported_login_providers: map
        :param supported_login_providers: Optional key:value pairs mapping
            provider names to provider app IDs.

        :type developer_provider_name: string
        :param developer_provider_name: The "domain" by which Cognito will
            refer to your users.

        :type open_id_connect_provider_ar_ns: list
        :param open_id_connect_provider_ar_ns:

        """
        params = {
            'IdentityPoolId': identity_pool_id,
            'IdentityPoolName': identity_pool_name,
            'AllowUnauthenticatedIdentities': allow_unauthenticated_identities,
        }
        if supported_login_providers is not None:
            params['SupportedLoginProviders'] = supported_login_providers
        if developer_provider_name is not None:
            params['DeveloperProviderName'] = developer_provider_name
        if open_id_connect_provider_ar_ns is not None:
            params['OpenIdConnectProviderARNs'] = open_id_connect_provider_ar_ns
        return self.make_request(action='UpdateIdentityPool',
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
