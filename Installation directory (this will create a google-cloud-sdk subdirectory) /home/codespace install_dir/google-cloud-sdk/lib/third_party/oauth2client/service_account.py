# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""oauth2client Service account credentials class."""

import base64
import copy
import datetime
import json
import time

import oauth2client
from oauth2client import _helpers
from oauth2client import client
from oauth2client import crypt
from oauth2client import transport
from oauth2client import util


_PASSWORD_DEFAULT = 'notasecret'
_PKCS12_KEY = '_private_key_pkcs12'
_PKCS12_ERROR = r"""
This library only implements PKCS#12 support via the pyOpenSSL library.
Either install pyOpenSSL, or please convert the .p12 file
to .pem format:
    $ cat key.p12 | \
    >   openssl pkcs12 -nodes -nocerts -passin pass:notasecret | \
    >   openssl rsa > key.pem
"""


class ServiceAccountCredentials(client.AssertionCredentials):
    """Service Account credential for OAuth 2.0 signed JWT grants.

    Supports

    * JSON keyfile (typically contains a PKCS8 key stored as
      PEM text)
    * ``.p12`` key (stores PKCS12 key and certificate)

    Makes an assertion to server using a signed JWT assertion in exchange
    for an access token.

    This credential does not require a flow to instantiate because it
    represents a two legged flow, and therefore has all of the required
    information to generate and refresh its own access tokens.

    Args:
        service_account_email: string, The email associated with the
                               service account.
        signer: ``crypt.Signer``, A signer which can be used to sign content.
        scopes: List or string, (Optional) Scopes to use when acquiring
                an access token.
        private_key_id: string, (Optional) Private key identifier. Typically
                        only used with a JSON keyfile. Can be sent in the
                        header of a JWT token assertion.
        client_id: string, (Optional) Client ID for the project that owns the
                   service account.
        user_agent: string, (Optional) User agent to use when sending
                    request.
        token_uri: string, URI for token endpoint. For convenience defaults
                   to Google's endpoints but any OAuth 2.0 provider can be
                   used.
        revoke_uri: string, URI for revoke endpoint.  For convenience defaults
                   to Google's endpoints but any OAuth 2.0 provider can be
                   used.
        kwargs: dict, Extra key-value pairs (both strings) to send in the
                payload body when making an assertion.
    """

    MAX_TOKEN_LIFETIME_SECS = 3600
    """Max lifetime of the token (one hour, in seconds)."""

    NON_SERIALIZED_MEMBERS = (
        frozenset(['_signer']) |
        client.AssertionCredentials.NON_SERIALIZED_MEMBERS)
    """Members that aren't serialized when object is converted to JSON."""

    # Can be over-ridden by factory constructors. Used for
    # serialization/deserialization purposes.
    _private_key_pkcs8_pem = None
    _private_key_pkcs12 = None
    _private_key_password = None

    def __init__(self,
                 service_account_email,
                 signer,
                 scopes='',
                 private_key_id=None,
                 client_id=None,
                 user_agent=None,
                 token_uri=oauth2client.GOOGLE_TOKEN_URI,
                 revoke_uri=oauth2client.GOOGLE_REVOKE_URI,
                 **kwargs):

        super(ServiceAccountCredentials, self).__init__(
            None, user_agent=user_agent, token_uri=token_uri,
            revoke_uri=revoke_uri)

        self._service_account_email = service_account_email
        self._signer = signer
        self._scopes = util.scopes_to_string(scopes)
        self._private_key_id = private_key_id
        self.client_id = client_id
        self._user_agent = user_agent
        self._kwargs = kwargs

    def _to_json(self, strip, to_serialize=None):
        """Utility function that creates JSON repr. of a credentials object.

        Over-ride is needed since PKCS#12 keys will not in general be JSON
        serializable.

        Args:
            strip: array, An array of names of members to exclude from the
                   JSON.
            to_serialize: dict, (Optional) The properties for this object
                          that will be serialized. This allows callers to
                          modify before serializing.

        Returns:
            string, a JSON representation of this instance, suitable to pass to
            from_json().
        """
        if to_serialize is None:
            to_serialize = copy.copy(self.__dict__)
        pkcs12_val = to_serialize.get(_PKCS12_KEY)
        if pkcs12_val is not None:
            to_serialize[_PKCS12_KEY] = base64.b64encode(pkcs12_val)
        return super(ServiceAccountCredentials, self)._to_json(
            strip, to_serialize=to_serialize)

    @classmethod
    def _from_parsed_json_keyfile(cls, keyfile_dict, scopes,
                                  token_uri=None, revoke_uri=None):
        """Helper for factory constructors from JSON keyfile.

        Args:
            keyfile_dict: dict-like object, The parsed dictionary-like object
                          containing the contents of the JSON keyfile.
            scopes: List or string, Scopes to use when acquiring an
                    access token.
            token_uri: string, URI for OAuth 2.0 provider token endpoint.
                       If unset and not present in keyfile_dict, defaults
                       to Google's endpoints.
            revoke_uri: string, URI for OAuth 2.0 provider revoke endpoint.
                       If unset and not present in keyfile_dict, defaults
                       to Google's endpoints.

        Returns:
            ServiceAccountCredentials, a credentials object created from
            the keyfile contents.

        Raises:
            ValueError, if the credential type is not :data:`SERVICE_ACCOUNT`.
            KeyError, if one of the expected keys is not present in
                the keyfile.
        """
        creds_type = keyfile_dict.get('type')
        if creds_type != client.SERVICE_ACCOUNT:
            raise ValueError('Unexpected credentials type', creds_type,
                             'Expected', client.SERVICE_ACCOUNT)

        service_account_email = keyfile_dict['client_email']
        private_key_pkcs8_pem = keyfile_dict['private_key']
        private_key_id = keyfile_dict['private_key_id']
        client_id = keyfile_dict['client_id']
        if not token_uri:
            token_uri = keyfile_dict.get('token_uri',
                                         oauth2client.GOOGLE_TOKEN_URI)
        if not revoke_uri:
            revoke_uri = keyfile_dict.get('revoke_uri',
                                          oauth2client.GOOGLE_REVOKE_URI)

        signer = crypt.Signer.from_string(private_key_pkcs8_pem)
        credentials = cls(service_account_email, signer, scopes=scopes,
                          private_key_id=private_key_id,
                          client_id=client_id, token_uri=token_uri,
                          revoke_uri=revoke_uri)
        credentials._private_key_pkcs8_pem = private_key_pkcs8_pem
        return credentials

    @classmethod
    def from_json_keyfile_name(cls, filename, scopes='',
                               token_uri=None, revoke_uri=None):

        """Factory constructor from JSON keyfile by name.

        Args:
            filename: string, The location of the keyfile.
            scopes: List or string, (Optional) Scopes to use when acquiring an
                    access token.
            token_uri: string, URI for OAuth 2.0 provider token endpoint.
                       If unset and not present in the key file, defaults
                       to Google's endpoints.
            revoke_uri: string, URI for OAuth 2.0 provider revoke endpoint.
                       If unset and not present in the key file, defaults
                       to Google's endpoints.

        Returns:
            ServiceAccountCredentials, a credentials object created from
            the keyfile.

        Raises:
            ValueError, if the credential type is not :data:`SERVICE_ACCOUNT`.
            KeyError, if one of the expected keys is not present in
                the keyfile.
        """
        with open(filename, 'r') as file_obj:
            client_credentials = json.load(file_obj)
        return cls._from_parsed_json_keyfile(client_credentials, scopes,
                                             token_uri=token_uri,
                                             revoke_uri=revoke_uri)

    @classmethod
    def from_json_keyfile_dict(cls, keyfile_dict, scopes='',
                               token_uri=None, revoke_uri=None):
        """Factory constructor from parsed JSON keyfile.

        Args:
            keyfile_dict: dict-like object, The parsed dictionary-like object
                          containing the contents of the JSON keyfile.
            scopes: List or string, (Optional) Scopes to use when acquiring an
                    access token.
            token_uri: string, URI for OAuth 2.0 provider token endpoint.
                       If unset and not present in keyfile_dict, defaults
                       to Google's endpoints.
            revoke_uri: string, URI for OAuth 2.0 provider revoke endpoint.
                       If unset and not present in keyfile_dict, defaults
                       to Google's endpoints.

        Returns:
            ServiceAccountCredentials, a credentials object created from
            the keyfile.

        Raises:
            ValueError, if the credential type is not :data:`SERVICE_ACCOUNT`.
            KeyError, if one of the expected keys is not present in
                the keyfile.
        """
        return cls._from_parsed_json_keyfile(keyfile_dict, scopes,
                                             token_uri=token_uri,
                                             revoke_uri=revoke_uri)

    @classmethod
    def _from_p12_keyfile_contents(cls, service_account_email,
                                   private_key_pkcs12,
                                   private_key_password=None, scopes='',
                                   token_uri=oauth2client.GOOGLE_TOKEN_URI,
                                   revoke_uri=oauth2client.GOOGLE_REVOKE_URI):
        """Factory constructor from JSON keyfile.

        Args:
            service_account_email: string, The email associated with the
                                   service account.
            private_key_pkcs12: string, The contents of a PKCS#12 keyfile.
            private_key_password: string, (Optional) Password for PKCS#12
                                  private key. Defaults to ``notasecret``.
            scopes: List or string, (Optional) Scopes to use when acquiring an
                    access token.
            token_uri: string, URI for token endpoint. For convenience defaults
                       to Google's endpoints but any OAuth 2.0 provider can be
                       used.
            revoke_uri: string, URI for revoke endpoint. For convenience
                        defaults to Google's endpoints but any OAuth 2.0
                        provider can be used.

        Returns:
            ServiceAccountCredentials, a credentials object created from
            the keyfile.

        Raises:
            NotImplementedError if pyOpenSSL is not installed / not the
            active crypto library.
        """
        if private_key_password is None:
            private_key_password = _PASSWORD_DEFAULT
        if crypt.Signer is not crypt.OpenSSLSigner:
            raise NotImplementedError(_PKCS12_ERROR)
        signer = crypt.Signer.from_string(private_key_pkcs12,
                                          private_key_password)
        credentials = cls(service_account_email, signer, scopes=scopes,
                          token_uri=token_uri, revoke_uri=revoke_uri)
        credentials._private_key_pkcs12 = private_key_pkcs12
        credentials._private_key_password = private_key_password
        return credentials

    @classmethod
    def from_p12_keyfile(cls, service_account_email, filename,
                         private_key_password=None, scopes='',
                         token_uri=oauth2client.GOOGLE_TOKEN_URI,
                         revoke_uri=oauth2client.GOOGLE_REVOKE_URI):

        """Factory constructor from JSON keyfile.

        Args:
            service_account_email: string, The email associated with the
                                   service account.
            filename: string, The location of the PKCS#12 keyfile.
            private_key_password: string, (Optional) Password for PKCS#12
                                  private key. Defaults to ``notasecret``.
            scopes: List or string, (Optional) Scopes to use when acquiring an
                    access token.
            token_uri: string, URI for token endpoint. For convenience defaults
                       to Google's endpoints but any OAuth 2.0 provider can be
                       used.
            revoke_uri: string, URI for revoke endpoint. For convenience
                        defaults to Google's endpoints but any OAuth 2.0
                        provider can be used.

        Returns:
            ServiceAccountCredentials, a credentials object created from
            the keyfile.

        Raises:
            NotImplementedError if pyOpenSSL is not installed / not the
            active crypto library.
        """
        with open(filename, 'rb') as file_obj:
            private_key_pkcs12 = file_obj.read()
        return cls._from_p12_keyfile_contents(
            service_account_email, private_key_pkcs12,
            private_key_password=private_key_password, scopes=scopes,
            token_uri=token_uri, revoke_uri=revoke_uri)

    @classmethod
    def from_p12_keyfile_buffer(cls, service_account_email, file_buffer,
                                private_key_password=None, scopes='',
                                token_uri=oauth2client.GOOGLE_TOKEN_URI,
                                revoke_uri=oauth2client.GOOGLE_REVOKE_URI):
        """Factory constructor from JSON keyfile.

        Args:
            service_account_email: string, The email associated with the
                                   service account.
            file_buffer: stream, A buffer that implements ``read()``
                         and contains the PKCS#12 key contents.
            private_key_password: string, (Optional) Password for PKCS#12
                                  private key. Defaults to ``notasecret``.
            scopes: List or string, (Optional) Scopes to use when acquiring an
                    access token.
            token_uri: string, URI for token endpoint. For convenience defaults
                       to Google's endpoints but any OAuth 2.0 provider can be
                       used.
            revoke_uri: string, URI for revoke endpoint. For convenience
                        defaults to Google's endpoints but any OAuth 2.0
                        provider can be used.

        Returns:
            ServiceAccountCredentials, a credentials object created from
            the keyfile.

        Raises:
            NotImplementedError if pyOpenSSL is not installed / not the
            active crypto library.
        """
        private_key_pkcs12 = file_buffer.read()
        return cls._from_p12_keyfile_contents(
            service_account_email, private_key_pkcs12,
            private_key_password=private_key_password, scopes=scopes,
            token_uri=token_uri, revoke_uri=revoke_uri)

    def _generate_assertion(self):
        """Generate the assertion that will be used in the request."""
        now = int(time.time())
        payload = {
            'aud': self.token_uri,
            'scope': self._scopes,
            'iat': now,
            'exp': now + self.MAX_TOKEN_LIFETIME_SECS,
            'iss': self._service_account_email,
        }
        payload.update(self._kwargs)
        return crypt.make_signed_jwt(self._signer, payload,
                                     key_id=self._private_key_id)

    def sign_blob(self, blob):
        """Cryptographically sign a blob (of bytes).

        Implements abstract method
        :meth:`oauth2client.client.AssertionCredentials.sign_blob`.

        Args:
            blob: bytes, Message to be signed.

        Returns:
            tuple, A pair of the private key ID used to sign the blob and
            the signed contents.
        """
        return self._private_key_id, self._signer.sign(blob)

    @property
    def service_account_email(self):
        """Get the email for the current service account.

        Returns:
            string, The email associated with the service account.
        """
        return self._service_account_email

    @property
    def serialization_data(self):
        # NOTE: This is only useful for JSON keyfile.
        return {
            'type': 'service_account',
            'client_email': self._service_account_email,
            'private_key_id': self._private_key_id,
            'private_key': self._private_key_pkcs8_pem,
            'client_id': self.client_id,
        }

    @classmethod
    def from_json(cls, json_data):
        """Deserialize a JSON-serialized instance.

        Inverse to :meth:`to_json`.

        Args:
            json_data: dict or string, Serialized JSON (as a string or an
                       already parsed dictionary) representing a credential.

        Returns:
            ServiceAccountCredentials from the serialized data.
        """
        if not isinstance(json_data, dict):
            json_data = json.loads(_helpers._from_bytes(json_data))

        private_key_pkcs8_pem = None
        pkcs12_val = json_data.get(_PKCS12_KEY)
        password = None
        if pkcs12_val is None:
            private_key_pkcs8_pem = json_data['_private_key_pkcs8_pem']
            signer = crypt.Signer.from_string(private_key_pkcs8_pem)
        else:
            # NOTE: This assumes that private_key_pkcs8_pem is not also
            #       in the serialized data. This would be very incorrect
            #       state.
            pkcs12_val = base64.b64decode(pkcs12_val)
            password = json_data['_private_key_password']
            signer = crypt.Signer.from_string(pkcs12_val, password)

        credentials = cls(
            json_data['_service_account_email'],
            signer,
            scopes=json_data['_scopes'],
            private_key_id=json_data['_private_key_id'],
            client_id=json_data['client_id'],
            user_agent=json_data['_user_agent'],
            **json_data['_kwargs']
        )
        if private_key_pkcs8_pem is not None:
            credentials._private_key_pkcs8_pem = private_key_pkcs8_pem
        if pkcs12_val is not None:
            credentials._private_key_pkcs12 = pkcs12_val
        if password is not None:
            credentials._private_key_password = password
        credentials.invalid = json_data['invalid']
        credentials.access_token = json_data['access_token']
        credentials.token_uri = json_data['token_uri']
        credentials.revoke_uri = json_data['revoke_uri']
        token_expiry = json_data.get('token_expiry', None)
        if token_expiry is not None:
            credentials.token_expiry = datetime.datetime.strptime(
                token_expiry, client.EXPIRY_FORMAT)
        return credentials

    def create_scoped_required(self):
        return not self._scopes

    def create_scoped(self, scopes):
        result = self.__class__(self._service_account_email,
                                self._signer,
                                scopes=scopes,
                                private_key_id=self._private_key_id,
                                client_id=self.client_id,
                                user_agent=self._user_agent,
                                **self._kwargs)
        result.token_uri = self.token_uri
        result.revoke_uri = self.revoke_uri
        result._private_key_pkcs8_pem = self._private_key_pkcs8_pem
        result._private_key_pkcs12 = self._private_key_pkcs12
        result._private_key_password = self._private_key_password
        return result

    def create_with_claims(self, claims):
        """Create credentials that specify additional claims.

        Args:
            claims: dict, key-value pairs for claims.

        Returns:
            ServiceAccountCredentials, a copy of the current service account
            credentials with updated claims to use when obtaining access
            tokens.
        """
        new_kwargs = dict(self._kwargs)
        new_kwargs.update(claims)
        result = self.__class__(self._service_account_email,
                                self._signer,
                                scopes=self._scopes,
                                private_key_id=self._private_key_id,
                                client_id=self.client_id,
                                user_agent=self._user_agent,
                                **new_kwargs)
        result.token_uri = self.token_uri
        result.revoke_uri = self.revoke_uri
        result._private_key_pkcs8_pem = self._private_key_pkcs8_pem
        result._private_key_pkcs12 = self._private_key_pkcs12
        result._private_key_password = self._private_key_password
        return result

    def create_delegated(self, sub):
        """Create credentials that act as domain-wide delegation of authority.

        Use the ``sub`` parameter as the subject to delegate on behalf of
        that user.

        For example::

          >>> account_sub = 'foo@email.com'
          >>> delegate_creds = creds.create_delegated(account_sub)

        Args:
            sub: string, An email address that this service account will
                 act on behalf of (via domain-wide delegation).

        Returns:
            ServiceAccountCredentials, a copy of the current service account
            updated to act on behalf of ``sub``.
        """
        return self.create_with_claims({'sub': sub})


def _datetime_to_secs(utc_time):
    # TODO(issue 298): use time_delta.total_seconds()
    # time_delta.total_seconds() not supported in Python 2.6
    epoch = datetime.datetime(1970, 1, 1)
    time_delta = utc_time - epoch
    return time_delta.days * 86400 + time_delta.seconds


class _JWTAccessCredentials(ServiceAccountCredentials):
    """Self signed JWT credentials.

    Makes an assertion to server using a self signed JWT from service account
    credentials.  These credentials do NOT use OAuth 2.0 and instead
    authenticate directly.
    """
    _MAX_TOKEN_LIFETIME_SECS = 3600
    """Max lifetime of the token (one hour, in seconds)."""

    def __init__(self,
                 service_account_email,
                 signer,
                 scopes=None,
                 private_key_id=None,
                 client_id=None,
                 user_agent=None,
                 token_uri=oauth2client.GOOGLE_TOKEN_URI,
                 revoke_uri=oauth2client.GOOGLE_REVOKE_URI,
                 additional_claims=None):
        if additional_claims is None:
            additional_claims = {}
        super(_JWTAccessCredentials, self).__init__(
            service_account_email,
            signer,
            private_key_id=private_key_id,
            client_id=client_id,
            user_agent=user_agent,
            token_uri=token_uri,
            revoke_uri=revoke_uri,
            **additional_claims)

    def authorize(self, http):
        """Authorize an httplib2.Http instance with a JWT assertion.

        Unless specified, the 'aud' of the assertion will be the base
        uri of the request.

        Args:
            http: An instance of ``httplib2.Http`` or something that acts
                  like it.
        Returns:
            A modified instance of http that was passed in.
        Example::
            h = httplib2.Http()
            h = credentials.authorize(h)
        """
        transport.wrap_http_for_jwt_access(self, http)
        return http

    def get_access_token(self, http=None, additional_claims=None):
        """Create a signed jwt.

        Args:
            http: unused
            additional_claims: dict, additional claims to add to
                the payload of the JWT.
        Returns:
            An AccessTokenInfo with the signed jwt
        """
        if additional_claims is None:
            if self.access_token is None or self.access_token_expired:
                self.refresh(None)
            return client.AccessTokenInfo(
              access_token=self.access_token, expires_in=self._expires_in())
        else:
            # Create a 1 time token
            token, unused_expiry = self._create_token(additional_claims)
            return client.AccessTokenInfo(
              access_token=token, expires_in=self._MAX_TOKEN_LIFETIME_SECS)

    def revoke(self, http):
        """Cannot revoke JWTAccessCredentials tokens."""
        pass

    def create_scoped_required(self):
        # JWTAccessCredentials are unscoped by definition
        return True

    def create_scoped(self, scopes, token_uri=oauth2client.GOOGLE_TOKEN_URI,
                      revoke_uri=oauth2client.GOOGLE_REVOKE_URI):
        # Returns an OAuth2 credentials with the given scope
        result = ServiceAccountCredentials(self._service_account_email,
                                           self._signer,
                                           scopes=scopes,
                                           private_key_id=self._private_key_id,
                                           client_id=self.client_id,
                                           user_agent=self._user_agent,
                                           token_uri=token_uri,
                                           revoke_uri=revoke_uri,
                                           **self._kwargs)
        if self._private_key_pkcs8_pem is not None:
            result._private_key_pkcs8_pem = self._private_key_pkcs8_pem
        if self._private_key_pkcs12 is not None:
            result._private_key_pkcs12 = self._private_key_pkcs12
        if self._private_key_password is not None:
            result._private_key_password = self._private_key_password
        return result

    def refresh(self, http):
        self._refresh(None)

    def _refresh(self, http_request):
        self.access_token, self.token_expiry = self._create_token()

    def _create_token(self, additional_claims=None):
        now = client._UTCNOW()
        lifetime = datetime.timedelta(seconds=self._MAX_TOKEN_LIFETIME_SECS)
        expiry = now + lifetime
        payload = {
            'iat': _datetime_to_secs(now),
            'exp': _datetime_to_secs(expiry),
            'iss': self._service_account_email,
            'sub': self._service_account_email
        }
        payload.update(self._kwargs)
        if additional_claims is not None:
            payload.update(additional_claims)
        jwt = crypt.make_signed_jwt(self._signer, payload,
                                    key_id=self._private_key_id)
        return jwt.decode('ascii'), expiry
