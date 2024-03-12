# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utilities for the sign-url command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import hashlib
import json
import urllib.parse

from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.core import log
from googlecloudsdk.core import requests as core_requests
from googlecloudsdk.core import transport
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import transports
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times
import requests


# Constants that appear in requests represented by signed URLs.
_DIGEST = 'RSA-SHA256'
_SIGNING_ALGORITHM = 'GOOG4-RSA-SHA256'
_UNSIGNED_PAYLOAD = 'UNSIGNED-PAYLOAD'


# Constants for reading credential stores.
JSON_CLIENT_ID_KEY = 'client_email'
JSON_PRIVATE_KEY_KEY = 'private_key'


def get_signed_url(
    client_id,
    duration,
    headers,
    host,
    key,
    verb,
    parameters,
    path,
    region,
    delegates,
):
  """Gets a signed URL for a GCS XML API request.

  https://cloud.google.com/storage/docs/access-control/signed-urls

  Args:
    client_id (str): Email of the service account that makes the request.
    duration (int): Amount of time (seconds) that the URL is valid for.
    headers (dict[str, str]): User-inputted headers for the request.
    host (str): The endpoint URL for the request. This should include a scheme,
      e.g. "https://"
    key (crypto.PKey): Key for the service account specified by client_id.
    verb (str): HTTP verb associated with the request.
    parameters (dict[str, str]): User-inputted parameters for the request.
    path (str): Of the form `/bucket-name/object-name`. Specifies the resource
      that is targeted by the request.
    region (str): The region of the target resource instance.
    delegates (list[str]|None): The list of service accounts in a delegation
      chain specified in --impersonate-service-account.

  Returns:
    A URL (str) used to make the specified request.
  """
  encoded_path = urllib.parse.quote(path, safe='/~')

  signing_time = times.Now(tzinfo=times.UTC)

  _, _, host_without_scheme = host.rpartition('://')
  headers_to_sign = {'host': host_without_scheme}
  headers_to_sign.update(headers)
  canonical_headers_string = ''.join(
      [
          '{}:{}\n'.format(k.lower(), v)
          for k, v in sorted(headers_to_sign.items())
      ]
  )
  canonical_signed_headers_string = ';'.join(sorted(headers_to_sign.keys()))

  canonical_scope = '{date}/{region}/storage/goog4_request'.format(
      date=signing_time.strftime('%Y%m%d'),
      # Lowercase does't seem to be necessary but is used for gsutil parity.
      region=region.lower(),
  )
  canonical_time = signing_time.strftime('%Y%m%dT%H%M%SZ')

  query_params_to_sign = {
      'x-goog-algorithm': _SIGNING_ALGORITHM,
      'x-goog-credential': client_id + '/' + canonical_scope,
      'x-goog-date': canonical_time,
      'x-goog-signedheaders': canonical_signed_headers_string,
      'x-goog-expires': str(duration),
  }
  query_params_to_sign.update(parameters)
  canonical_query_string = '&'.join(
      [
          '{}={}'.format(k, urllib.parse.quote_plus(v))
          for k, v in sorted(query_params_to_sign.items())
      ]
  )

  # https://cloud.google.com/storage/docs/authentication/canonical-requests
  canonical_request_string = '\n'.join([
      verb,
      encoded_path,
      canonical_query_string,
      canonical_headers_string,
      canonical_signed_headers_string,
      _UNSIGNED_PAYLOAD,
  ])

  log.debug('Canonical request string:\n' + canonical_request_string)

  canonical_request_hash = hashlib.sha256(
      canonical_request_string.encode('utf-8')
  ).hexdigest()

  # https://cloud.google.com/storage/docs/authentication/signatures#string-to-sign
  string_to_sign = '\n'.join([
      _SIGNING_ALGORITHM,
      canonical_time,
      canonical_scope,
      canonical_request_hash,
  ])

  log.debug('String to sign:\n' + string_to_sign)

  raw_signature = (
      _sign_with_key(key, string_to_sign)
      if key
      else _sign_with_iam(client_id, string_to_sign, delegates)
  )

  signature = base64.b16encode(raw_signature).lower().decode('utf-8')
  return ('{host}{path}?x-goog-signature={signature}&{query_string}').format(
      host=host,
      path=encoded_path,
      signature=signature,
      query_string=canonical_query_string,
  )


def _sign_with_iam(account_email, string_to_sign, delegates):
  """Generates a signature using the IAM sign-blob method.

  Args:
    account_email (str): Email of the service account to sign as.
    string_to_sign (str): String to sign.
    delegates (list[str]|None): The list of service accounts in a delegation
      chain specified in --impersonate-service-account.

  Returns:
    A raw signature for the specified string.
  """
  # If X is some user account and Y is a service account:
  # X needs roles/iam.serviceAccountTokenCreator on Y in order to impersonate Y.
  # X needs roles/iam.serviceAccountTokenCreator on Y in order to signBlob as Y.
  # Y needs roles/iam.serviceAccountTokenCreator on itself to signBlob alone.
  # Therefore, when X impersonates Y, we know that the permissions are
  # provisioned correctly for X to signBlob as Y, but we don't know if Y has
  # permissions to call signBlob alone. To take advantage of the permissions,
  # you need to issue the signBlob call as X and pass Y as a parameter. To do
  # this we revert to the original X credentials by turning off impersonation.
  # This is why we override the http_client using apis_internal in this section.
  http_client = transports.GetApitoolsTransport(
      response_encoding=transport.ENCODING, allow_account_impersonation=False
  )
  # pylint: disable=protected-access
  client = apis_internal._GetClientInstance(
      'iamcredentials', 'v1', http_client=http_client
  )
  messages = client.MESSAGES_MODULE
  response = client.projects_serviceAccounts.SignBlob(
      messages.IamcredentialsProjectsServiceAccountsSignBlobRequest(
          name=iam_util.EmailToAccountResourceName(account_email),
          signBlobRequest=messages.SignBlobRequest(
              payload=bytes(string_to_sign, 'utf-8'),
              delegates=[
                  iam_util.EmailToAccountResourceName(delegate)
                  for delegate in delegates or []
              ],
          ),
      )
  )
  return response.signedBlob


def _sign_with_key(key, string_to_sign):
  """Generates a signature using OpenSSL.crypto.

  Args:
    key (crypto.PKey): Key for the signing service account.
    string_to_sign (str): String to sign.

  Returns:
      A raw signature for the specified string.
  """
  from OpenSSL import crypto  # pylint: disable=g-import-not-at-top
  return crypto.sign(key, string_to_sign.encode('utf-8'), _DIGEST)


def get_signing_information_from_json(raw_data, password_bytes=None):
  """Loads signing information from a JSON or P12 private key.

  JSON keys from GCP do not use a passphrase by default, so we follow gsutil in
  not prompting the user for a password.

  P12 keystores from GCP do use a default ('notasecret'), so we will prompt the
  user if they do not provide a password.

  Args:
    raw_data (str): Un-parsed JSON data from the key file or creds store.
    password_bytes (bytes): A password used to decrypt encrypted private keys.

  Returns:
    A tuple (client_id: str, key: crypto.PKey), which can be used to sign URLs.
  """
  from OpenSSL import crypto  # pylint:disable=g-import-not-at-top
  try:
    # Expects JSON formatted like the return value of the iam service-account
    # keys create command:
    # https://cloud.google.com/iam/docs/keys-create-delete#iam-service-account-keys-create-gcloud
    parsed_json = json.loads(raw_data)
    client_id = parsed_json[JSON_CLIENT_ID_KEY]
    key = crypto.load_privatekey(
        crypto.FILETYPE_PEM,
        parsed_json[JSON_PRIVATE_KEY_KEY],
        passphrase=password_bytes,
    )
    return client_id, key

  except ValueError:  # Failed to parse JSON. Try P12.
    if not password_bytes:
      # If the user does not provide a password, we prompt for one for parity
      # with gsutil. Gsutil likely chose this behavior as P12 files provided by
      # GCP use a default password ('notasecret'). Gsutil does not supply the
      # default password here, however.
      # https://support.google.com/cloud/answer/6158849?hl=en#serviceaccounts&zippy=%2Cservice-accounts:~:text=provide%20the%20password-,notasecret,-.%20Note%20that%20while
      password_bytes = console_io.PromptPassword(
          "Keystore password (default: 'notasecret'): "
      )

    keystore = crypto.load_pkcs12(raw_data, passphrase=password_bytes)
    client_id = keystore.get_certificate().get_subject().CN
    return client_id, keystore.get_privatekey()


def get_signing_information_from_file(path, password=None):
  """Loads signing information from a JSON or P12 private key file.

  Args:
    path (str): The location of the file.
    password (str|None): The password used to decrypt encrypted private keys.

  Returns:
    A tuple (client_id: str, key: crypto.PKey), which can be used to sign URLs.
  """
  if password:
    password_bytes = password.encode('utf-8')
  else:
    password_bytes = None

  with files.BinaryFileReader(path) as file:
    raw_data = file.read()

  return get_signing_information_from_json(raw_data, password_bytes)


def probe_access_to_resource(
    client_id,
    host,
    key,
    path,
    region,
    requested_headers,
    requested_http_verb,
    requested_parameters,
    requested_resource,
):
  """Checks if provided credentials offer appropriate access to a resource.

  Args:
    client_id (str): Email of the service account that makes the request.
    host (str): The endpoint URL for the request.
    key (crypto.PKey): Key for the service account specified by client_id.
    path (str): Of the form `/bucket-name/object-name`. Specifies the resource
      that is targeted by the request.
    region (str): The region of the target resource instance.
    requested_headers (dict[str, str]): Headers used in the user's request.
      These do not need to be passed into the HEAD request performed by this
      function, but they do need to be checked for this function to raise
      appropriate errors for different use cases (e.g. for resumable uploads).
    requested_http_verb (str): Method the user requested.
    requested_parameters (dict[str, str]): URL parameters the user requested.
    requested_resource (resource_reference.Resource): Resource the user
      requested to access.

  Raises:
    errors.Error if the requested resource is not available for the requested
      operation.
  """
  parameters = {}

  # Preserve a custom billing project if set.
  if 'userProject' in requested_parameters:
    parameters['userProject'] = requested_parameters['userProject']

  url = get_signed_url(
      client_id=client_id,
      duration=60,
      headers={},  # TODO(b/282927706): Add user agent.
      host=host,
      key=key,
      verb='HEAD',
      parameters=parameters,
      path=path,
      region=region,
      delegates=None,
  )
  session = core_requests.GetSession()
  response = session.head(url)

  if response.status_code == 404:
    if requested_http_verb == 'PUT':
      # PUT requests typically create resources, so 404s are not useful
      # information. POST requests typically modify existing resources, so 404s
      # are relevant.
      return

    # Resumable uploads are initiated with a POST request, but create a
    # resource, so we can also silence errors here.
    is_resumable_upload = 'x-goog-resumable' in requested_headers
    if is_resumable_upload:
      return

    if requested_resource.storage_url.is_bucket():
      raise errors.Error(
          'Bucket {} does not exist. Please create a bucket with that name'
          ' before creating a signed URL to access it.'.format(
              requested_resource.storage_url
          )
      )

    else:
      raise errors.Error(
          'Object {} does not exist. Please create an object with that name'
          ' before creating a signed URL to access it.'.format(
              requested_resource.storage_url
          )
      )

  elif response.status_code == 403:
    log.warning(
        '{} does not have permissions on {}. Using this link will likely result'
        ' in a 403 error until at least READ permissions are granted.'.format(
            client_id, requested_resource.storage_url
        )
    )

  else:
    try:
      response.raise_for_status()
    except requests.exceptions.HTTPError as error:
      raise errors.Error(
          'Expected an HTTP response code of 200 while querying object'
          ' readability, but received an error: {}'.format(error)
      )
