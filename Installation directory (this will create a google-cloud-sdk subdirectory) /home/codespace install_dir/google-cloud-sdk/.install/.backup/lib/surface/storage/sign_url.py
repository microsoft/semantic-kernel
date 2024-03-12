# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Implementation of sign url command for Cloud Storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
import textwrap

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage import sign_url_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import iso_duration
from googlecloudsdk.core.util import times


_INSTALL_PY_OPEN_SSL_MESSAGE = (
    'This command requires the pyOpenSSL library.'
    ' Please install it and set the environment variable'
    ' CLOUDSDK_PYTHON_SITEPACKAGES to 1 before re-running this command.'
)

_PROVIDE_SERVICE_ACCOUNT_MESSAGE = (
    'This command requires a service account to sign a URL. Please authenticate'
    ' with a service account, or provide the global'
    " '--impersonate-service-account' flag."
)


@functools.lru_cache(maxsize=None)
def _get_region_with_cache(scheme, bucket_name):
  api_client = api_factory.get_api(scheme)
  try:
    bucket_resource = api_client.get_bucket(bucket_name)
  except api_errors.CloudApiError:
    raise command_errors.Error(
        'Failed to auto-detect the region for {}. Please ensure you have'
        " storage.buckets.get permission on the bucket, or specify the bucket's"
        " region using the '--region' flag.".format(bucket_name),
    )
  return bucket_resource.location


def _get_region(args, resource):
  if args.region:
    return args.region

  if resource.storage_url.is_bucket():
    raise command_errors.Error(
        'Generating signed URLs for creating buckets requires a region to'
        ' be specified using the --region flag.'
    )

  return _get_region_with_cache(
      resource.storage_url.scheme, resource.storage_url.bucket_name
  )


class SignUrl(base.Command):
  """Generate a URL with embedded authentication that can be used by anyone."""

  detailed_help = {
      'DESCRIPTION': """
      *{command}* will generate a signed URL that embeds authentication data so
      the URL can be used by someone who does not have a Google account. Use the
      global ``--impersonate-service-account'' flag to specify the service
      account that will be used to sign the specified URL or authenticate with
      a service account directly. Otherwise, a service account key is required.
      Please see the [Signed URLs documentation](https://cloud.google.com/storage/docs/access-control/signed-urls)
      for background about signed URLs.

      Note, `{command}` does not support operations on sub-directories. For
      example, unless you have an object named `some-directory/` stored inside
      the bucket `some-bucket`, the following command returns an error:
      `{command} gs://some-bucket/some-directory/`.
      """,
      'EXAMPLES': """
      To create a signed url for downloading an object valid for 10 minutes with
      the credentials of an impersonated service account:

        $ {command} gs://my-bucket/file.txt --duration=10m --impersonate-service-account=sa@my-project.iam.gserviceaccount.com

      To create a signed url that will bill to my-billing-project when already
      authenticated as a service account:

        $ {command} gs://my-bucket/file.txt --query-params=userProject=my-billing-project

      To create a signed url, valid for one hour, for uploading a plain text
      file via HTTP PUT:

        $ {command} gs://my-bucket/file.txt --http-verb=PUT --duration=1h --headers=content-type=text/plain --impersonate-service-account=sa@my-project.iam.gserviceaccount.com

      To create a signed URL that initiates a resumable upload for a plain text
      file using a private key file:

        $ {command} gs://my-bucket/file.txt --http-verb=POST --headers=x-goog-resumable=start,content-type=text/plain --private-key-file=key.json
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        nargs='+',
        help='The URLs to be signed. May contain wildcards.')

    parser.add_argument(
        '-d',
        '--duration',
        default=3600,  # 1 hour.
        type=arg_parsers.Duration(upper_bound='7d'),
        help=textwrap.dedent(
            """\
            Specifies the duration that the signed url should be valid for,
            default duration is 1 hour. For example 10s for 10 seconds.
            See $ gcloud topic datetimes for information on duration formats.

            The max duration allowed is 12 hours. This limitation exists because
            the system-managed key used to sign the URL may not remain valid
            after 12 hours.

            Alternatively, the max duration allowed is 7 days when signing with
            either the ``--private-key-file'' flag or an account that authorized
            with ``gcloud auth activate-service-account''."""
        ),
    )
    parser.add_argument(
        '--headers',
        action=arg_parsers.UpdateAction,
        default={},
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(),
        help=textwrap.dedent("""\
            Specifies the headers to be used in the signed request.
            Possible headers are listed in the XML API's documentation:
            https://cloud.google.com/storage/docs/xml-api/reference-headers#headers
            """),
    )
    parser.add_argument(
        '-m',
        '--http-verb',
        default='GET',
        help=textwrap.dedent("""\
            Specifies the HTTP verb to be authorized for use with the signed
            URL, default is GET. When using a signed URL to start
            a resumable upload session, you will need to specify the
            ``x-goog-resumable:start'' header in the request or else signature
            validation will fail."""),
    )
    parser.add_argument(
        '--private-key-file',
        help=textwrap.dedent("""\
            The service account private key used to generate the cryptographic
            signature for the generated URL. Must be in PKCS12 or JSON format.
            If encrypted, will prompt for the passphrase used to protect the
            private key file (default ``notasecret'').

            Note: Service account keys are a security risk if not managed
            correctly. Review [best practices for managing service account keys](https://cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys)
            before using this option."""),
    )
    parser.add_argument(
        '-p',
        '--private-key-password',
        help='Specifies the PRIVATE_KEY_FILE password instead of prompting.',
    )
    parser.add_argument(
        '--query-params',
        action=arg_parsers.UpdateAction,
        default={},
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(),
        help=textwrap.dedent("""\
            Specifies the query parameters to be used in the signed request.
            Possible query parameters are listed in the XML API's documentation:
            https://cloud.google.com/storage/docs/xml-api/reference-headers#query
            """),
    )
    parser.add_argument(
        '-r',
        '--region',
        help=textwrap.dedent("""\
            Specifies the region in which the resources for which you are
            creating signed URLs are stored.

            Default value is ``auto'' which will cause {command} to fetch the
            region for the resource. When auto-detecting the region, the current
            user's credentials, not the credentials from PRIVATE_KEY_FILE,
            are used to fetch the bucket's metadata."""),
    )

  def Run(self, args):
    key = None
    delegates = None
    creds = c_store.Load(prevent_refresh=True, use_google_auth=False)
    delegate_chain = args.impersonate_service_account or (
        properties.VALUES.auth.impersonate_service_account.Get())
    if args.private_key_file:
      try:
        client_id, key = sign_url_util.get_signing_information_from_file(
            args.private_key_file, args.private_key_password
        )
      except ModuleNotFoundError as error:
        if 'OpenSSL' in str(error):
          raise command_errors.Error(_INSTALL_PY_OPEN_SSL_MESSAGE)
        raise
    elif delegate_chain:
      impersonated_account, delegates = c_store.ParseImpersonationAccounts(
          delegate_chain
      )
      client_id = impersonated_account
    elif (
        c_creds.CredentialType.FromCredentials(creds)
        == c_creds.CredentialType.GCE
    ):
      client_id = properties.VALUES.core.account.Get()
    elif c_creds.IsServiceAccountCredentials(creds):
      try:
        client_id, key = sign_url_util.get_signing_information_from_json(
            c_creds.ToJson(creds)
        )
      except ModuleNotFoundError as error:
        if 'OpenSSL' in str(error):
          raise command_errors.Error(_INSTALL_PY_OPEN_SSL_MESSAGE)
        raise
    else:
      raise command_errors.Error(_PROVIDE_SERVICE_ACCOUNT_MESSAGE)

    # Signed URLs always hit the XML API, regardless of what API is preferred
    # for other operations.
    host = properties.VALUES.storage.gs_xml_endpoint_url.Get()

    has_provider_url = any(
        storage_url.storage_url_from_string(url_string).is_provider()
        for url_string in args.url
    )
    if has_provider_url:
      raise command_errors.Error(
          'The sign-url command does not support provider-only URLs.'
      )

    for url_string in args.url:
      url = storage_url.storage_url_from_string(url_string)
      if wildcard_iterator.contains_wildcard(url_string):
        resources = wildcard_iterator.get_wildcard_iterator(url_string)
      else:
        resources = [resource_reference.UnknownResource(url)]

      for resource in resources:
        if resource.storage_url.is_bucket():
          path = '/{}'.format(resource.storage_url.bucket_name)
        else:
          path = '/{}/{}'.format(
              resource.storage_url.bucket_name, resource.storage_url.object_name
          )

        parameters = dict(args.query_params)
        if url.generation:
          parameters['generation'] = url.generation

        region = _get_region(args, resource)

        signed_url = sign_url_util.get_signed_url(
            client_id=client_id,
            duration=args.duration,
            headers=args.headers,
            host=host,
            key=key,
            verb=args.http_verb,
            parameters=parameters,
            path=path,
            region=region,
            delegates=delegates,
        )

        expiration_time = times.GetDateTimePlusDuration(
            times.Now(tzinfo=times.UTC),
            iso_duration.Duration(seconds=args.duration),
        )
        yield {
            'resource': str(resource),
            'http_verb': args.http_verb,
            'expiration': times.FormatDateTime(
                expiration_time, fmt='%Y-%m-%d %H:%M:%S'
            ),
            'signed_url': signed_url,
        }

        sign_url_util.probe_access_to_resource(
            client_id=client_id,
            host=host,
            key=key,
            path=path,
            region=region,
            requested_headers=args.headers,
            requested_http_verb=args.http_verb,
            requested_parameters=parameters,
            requested_resource=resource,
        )
