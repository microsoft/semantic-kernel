# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Implementation of URL Signing workflow.

see: https://cloud.google.com/storage/docs/access-control#Signed-URLs)
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import calendar
import copy
from datetime import datetime
from datetime import timedelta
import getpass
import json
import re
import sys

import six
from six.moves import urllib
from apitools.base.py.exceptions import HttpError
from apitools.base.py.http_wrapper import MakeRequest
from apitools.base.py.http_wrapper import Request

from boto import config

from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.storage_url import ContainsWildcard
from gslib.storage_url import StorageUrlFromString
from gslib.utils import constants
from gslib.utils.boto_util import GetNewHttp
from gslib.utils.shim_util import GcloudStorageMap, GcloudStorageFlag
from gslib.utils.signurl_helper import CreatePayload, GetFinalUrl

try:
  # Check for openssl.
  # pylint: disable=C6204
  from OpenSSL.crypto import FILETYPE_PEM
  from OpenSSL.crypto import load_pkcs12
  from OpenSSL.crypto import load_privatekey
  from OpenSSL.crypto import sign
  HAVE_OPENSSL = True
except ImportError:
  load_privatekey = None
  load_pkcs12 = None
  sign = None
  HAVE_OPENSSL = False
  FILETYPE_PEM = None

_AUTO_DETECT_REGION = 'auto'
_MAX_EXPIRATION_TIME = timedelta(days=7)
_MAX_EXPIRATION_TIME_WITH_MINUS_U = timedelta(hours=12)

_SYNOPSIS = """
  gsutil signurl [-c <content_type>] [-d <duration>] [-m <http_method>] \\
      [-p <password>] [-r <region>] [-b <project>]  (-u | <private-key-file>) \\
      (gs://<bucket_name> | gs://<bucket_name>/<object_name>)...
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  The signurl command will generate a signed URL that embeds authentication data
  so the URL can be used by someone who does not have a Google account. Please
  see the `Signed URLs documentation
  <https://cloud.google.com/storage/docs/access-control/signed-urls>`_ for
  background about signed URLs.

  Multiple gs:// URLs may be provided and may contain wildcards. A signed URL
  will be produced for each provided URL, authorized
  for the specified HTTP method and valid for the given duration.

  NOTE: Unlike the gsutil ls command, the signurl command does not support
  operations on sub-directories. For example, unless you have an object named
  ``some-directory/`` stored inside the bucket ``some-bucket``, the following
  command returns an error: ``gsutil signurl <private-key-file> gs://some-bucket/some-directory/``

  The signurl command uses the private key for a service account (the
  '<private-key-file>' argument) to generate the cryptographic
  signature for the generated URL. The private key file must be in PKCS12
  or JSON format. If the private key is encrypted the signed URL command will
  prompt for the passphrase used to protect the private key file
  (default 'notasecret'). For more information regarding generating a private
  key for use with the signurl command please see the `Authentication
  documentation.
  <https://cloud.google.com/storage/docs/authentication#generating-a-private-key>`_

  If you used `service account credentials
  <https://cloud.google.com/storage/docs/gsutil/addlhelp/CredentialTypesSupportingVariousUseCases#supported-credential-types_1>`_
  for authentication, you can replace the  <private-key-file> argument with
  the -u or --use-service-account option to use the system-managed private key
  directly. This avoids the need to store a private key file locally, but
  prior to using this flag you must `configure
  <https://cloud.google.com/sdk/gcloud/reference/auth/activate-service-account>`_
  ``gcloud`` to use your service account credentials.

<B>OPTIONS</B>
  -b <project>  Allows you to specify a user project that will be billed for
                requests that use the signed URL. This is useful for generating
                presigned links for buckets that use requester pays.

                Note that it's not valid to specify both the ``-b`` and
                ``--use-service-account`` options together.

  -c            Specifies the content type for which the signed URL is
                valid for.

  -d            Specifies the duration that the signed URL should be valid
                for, default duration is 1 hour.

                Times may be specified with no suffix (default hours), or
                with s = seconds, m = minutes, h = hours, d = days.

                This option may be specified multiple times, in which case
                the duration the link remains valid is the sum of all the
                duration options.

                The max duration allowed is 7 days when ``private-key-file``
                is used.

                The max duration allowed is 12 hours when -u option is used.
                This limitation exists because the system-managed key used to
                sign the URL may not remain valid after 12 hours.

  -m            Specifies the HTTP method to be authorized for use
                with the signed URL, default is GET. You may also specify
                RESUMABLE to create a signed resumable upload start URL. When
                using a signed URL to start a resumable upload session, you will
                need to specify the 'x-goog-resumable:start' header in the
                request or else signature validation will fail.

  -p            Specify the private key password instead of prompting.

  -r <region>   Specifies the `region
                <https://cloud.google.com/storage/docs/locations>`_ in
                which the resources for which you are creating signed URLs are
                stored.

                Default value is 'auto' which will cause gsutil to fetch the
                region for the resource. When auto-detecting the region, the
                current gsutil user's credentials, not the credentials from the
                private-key-file, are used to fetch the bucket's metadata.

                This option must be specified and not 'auto' when generating a
                signed URL to create a bucket.

  -u            Use service account credentials instead of a private key file
                to sign the URL.

                You can also use the ``--use-service-account`` option,
                which is equivalent to ``-u``.
                Note that both options have a maximum allowed duration of
                12 hours for a valid link.



<B>USAGE</B>
  Create a signed URL for downloading an object valid for 10 minutes:

    gsutil signurl -d 10m <private-key-file> gs://<bucket>/<object>

  Create a signed URL, valid for one hour, for uploading a plain text
  file via HTTP PUT:

    gsutil signurl -m PUT -d 1h -c text/plain <private-key-file> \\
        gs://<bucket>/<obj>

  To construct a signed URL that allows anyone in possession of
  the URL to PUT to the specified bucket for one day, creating
  an object of Content-Type image/jpg, run:

    gsutil signurl -m PUT -d 1d -c image/jpg <private-key-file> \\
        gs://<bucket>/<obj>

  To construct a signed URL that allows anyone in possession of
  the URL to POST a resumable upload to the specified bucket for one day,
  creating an object of Content-Type image/jpg, run:

    gsutil signurl -m RESUMABLE -d 1d -c image/jpg <private-key-file> \\
        gs://bucket/<obj>
""")


def _NowUTC():
  """Returns the current utc time as a datetime object."""
  return datetime.utcnow()


def _DurationToTimeDelta(duration):
  r"""Parses the given duration and returns an equivalent timedelta."""

  match = re.match(r'^(\d+)([dDhHmMsS])?$', duration)
  if not match:
    raise CommandException('Unable to parse duration string')

  duration, modifier = match.groups('h')
  duration = int(duration)
  modifier = modifier.lower()

  if modifier == 'd':
    ret = timedelta(days=duration)
  elif modifier == 'h':
    ret = timedelta(hours=duration)
  elif modifier == 'm':
    ret = timedelta(minutes=duration)
  elif modifier == 's':
    ret = timedelta(seconds=duration)

  return ret


def _GenSignedUrl(key,
                  api,
                  use_service_account,
                  provider,
                  client_id,
                  method,
                  duration,
                  gcs_path,
                  logger,
                  region,
                  content_type=None,
                  billing_project=None,
                  string_to_sign_debug=False,
                  generation=None):
  """Construct a string to sign with the provided key.

  Args:
    key: The private key to use for signing the URL.
    api: The CloudApiDelegator instance
    use_service_account: If True, use the service account credentials
        instead of using the key file to sign the URL
    provider: Cloud storage provider to connect to.  If not present,
        class-wide default is used.
    client_id: Client ID signing this URL.
    method: The HTTP method to be used with the signed URL.
    duration: timedelta for which the constructed signed URL should be valid.
    gcs_path: String path to the bucket of object for signing, in the form
        'bucket' or 'bucket/object'.
    logger: logging.Logger for warning and debug output.
    region: Geographic region in which the requested resource resides.
    content_type: Optional Content-Type for the signed URL. HTTP requests using
        the URL must match this Content-Type.
    billing_project: Specify a user project to be billed for the request.
    string_to_sign_debug: If true AND logger is enabled for debug level,
        print string to sign to debug. Used to differentiate user's
        signed URL from the probing permissions-check signed URL.
    generation: If not None, specifies a version of an object for signing.

  Returns:
    The complete URL (string).
  """
  gs_host = config.get('Credentials', 'gs_host', 'storage.googleapis.com')
  signed_headers = {'host': gs_host}

  if method == 'RESUMABLE':
    method = 'POST'
    signed_headers['x-goog-resumable'] = 'start'
    if not content_type:
      logger.warn('Warning: no Content-Type header was specified with the -c '
                  'flag, so uploads to the resulting Signed URL must not '
                  'specify a Content-Type.')

  if content_type:
    signed_headers['content-type'] = content_type

  if use_service_account:
    final_url = api.SignUrl(provider=provider,
                            method=method,
                            duration=duration,
                            path=gcs_path,
                            generation=generation,
                            logger=logger,
                            region=region,
                            signed_headers=signed_headers,
                            string_to_sign_debug=string_to_sign_debug)
  else:
    if six.PY2:
      digest = b'RSA-SHA256'
    else:
      # Your IDE may complain about this due to a bad docstring in pyOpenSsl:
      # https://github.com/pyca/pyopenssl/issues/741
      digest = 'RSA-SHA256'
    string_to_sign, canonical_query_string = CreatePayload(
        client_id=client_id,
        method=method,
        duration=duration,
        path=gcs_path,
        generation=generation,
        logger=logger,
        region=region,
        signed_headers=signed_headers,
        billing_project=billing_project,
        string_to_sign_debug=string_to_sign_debug)
    raw_signature = sign(key, string_to_sign, digest)
    final_url = GetFinalUrl(raw_signature, gs_host, gcs_path,
                            canonical_query_string)
  return final_url


def _ReadKeystore(ks_contents, passwd):
  ks = load_pkcs12(ks_contents, passwd)
  client_email = ks.get_certificate().get_subject().CN

  return ks.get_privatekey(), client_email


def _ReadJSONKeystore(ks_contents, passwd=None):
  """Read the client email and private key from a JSON keystore.

  Assumes this keystore was downloaded from the Cloud Platform Console.
  By default, JSON keystore private keys from the Cloud Platform Console
  aren't encrypted so the passwd is optional as load_privatekey will
  prompt for the PEM passphrase if the key is encrypted.

  Arguments:
    ks_contents: JSON formatted string representing the keystore contents. Must
                 be a valid JSON string and contain the fields 'private_key'
                 and 'client_email'.
    passwd: Passphrase for encrypted private keys.

  Returns:
    key: Parsed private key from the keystore.
    client_email: The email address for the service account.

  Raises:
    ValueError: If unable to parse ks_contents or keystore is missing
                required fields.
  """
  # ensuring that json.loads receives unicode in Python 3 and bytes in Python 2
  # Previous to Python 3.6, there was no automatic conversion and str was req.
  ks = json.loads(six.ensure_str(ks_contents))

  if 'client_email' not in ks or 'private_key' not in ks:
    raise ValueError('JSON keystore doesn\'t contain required fields')

  client_email = ks['client_email']
  if passwd:
    key = load_privatekey(FILETYPE_PEM, ks['private_key'], passwd)
  else:
    key = load_privatekey(FILETYPE_PEM, ks['private_key'])

  return key, client_email


class UrlSignCommand(Command):
  """Implementation of gsutil url_sign command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'signurl',
      command_name_aliases=['signedurl', 'queryauth'],
      usage_synopsis=_SYNOPSIS,
      min_args=1,
      max_args=constants.NO_MAX,
      supported_sub_args='m:d:b:c:p:r:u',
      supported_private_args=['use-service-account'],
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=1,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[
          CommandArgument.MakeZeroOrMoreFileURLsArgument(),
          CommandArgument.MakeZeroOrMoreCloudURLsArgument(),
      ],
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='signurl',
      help_name_aliases=[
          'signedurl',
          'queryauth',
      ],
      help_type='command_help',
      help_one_line_summary='Create a signed URL',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  def get_gcloud_storage_args(self):
    # TODO (b/287273841): Replace `copy` with a better pattern for
    # translating flag values.
    original_args = copy.deepcopy(self.args)
    original_sub_opts = copy.deepcopy(self.sub_opts)
    gcloud_command = [
        'storage', 'sign-url',
        '--format=csv[separator="\\t"](resource:label="URL",'
        ' http_verb:label="HTTP Method",'
        ' expiration:label="Expiration",'
        ' signed_url:label="Signed URL")', '--private-key-file=' + self.args[0]
    ]
    self.args = self.args[1:]

    duration_arg_idx = None
    http_verb_arg_idx = None
    content_type_arg_idx = None
    billing_project_arg_idx = None

    for i, (flag, _) in enumerate(self.sub_opts):
      if flag == '-d':
        duration_arg_idx = i
      elif flag == '-m':
        http_verb_arg_idx = i
      elif flag == '-c':
        content_type_arg_idx = i
      elif flag == '-b':
        billing_project_arg_idx = i

    if duration_arg_idx is not None:
      # Convert duration to seconds, which gcloud can handle.
      seconds = str(
          int(
              _DurationToTimeDelta(
                  self.sub_opts[duration_arg_idx][1]).total_seconds())) + 's'
      self.sub_opts[duration_arg_idx] = ('-d', seconds)

    if http_verb_arg_idx is not None:
      if self.sub_opts[http_verb_arg_idx][1] == 'RESUMABLE':
        self.sub_opts[http_verb_arg_idx] = ('-m', 'POST')
        gcloud_command += ['--headers=x-goog-resumable=start']

    if content_type_arg_idx is not None:
      content_type_value = self.sub_opts[content_type_arg_idx][1]
      self.sub_opts[content_type_arg_idx] = ('-c', 'content-type=' +
                                             content_type_value)

    if billing_project_arg_idx is not None:
      project_value = self.sub_opts[billing_project_arg_idx][1]
      self.sub_opts[billing_project_arg_idx] = ('-b',
                                                'userProject=' + project_value)

    fully_translated_command = super().get_gcloud_storage_args(
        GcloudStorageMap(gcloud_command=gcloud_command,
                         flag_map={
                             '-m': GcloudStorageFlag('--http-verb'),
                             '-d': GcloudStorageFlag('--duration'),
                             '-b': GcloudStorageFlag('--query-params'),
                             '-c': GcloudStorageFlag('--headers'),
                             '-r': GcloudStorageFlag('--region'),
                             '-p': GcloudStorageFlag('--private-key-password'),
                         }))

    # Ensures dry run mode works correctly, as flag translation requires
    # mutating command state.
    # TODO(b/287273841): Refactor so that there's a better pattern for
    # translating flag values.
    self.args = original_args
    self.sub_opts = original_sub_opts
    return fully_translated_command

  def _ParseAndCheckSubOpts(self):
    # Default argument values
    delta = None
    method = 'GET'
    content_type = ''
    passwd = None
    region = _AUTO_DETECT_REGION
    use_service_account = False
    billing_project = None

    for o, v in self.sub_opts:
      # TODO(PY3-ONLY): Delete this if block.
      if six.PY2:
        v = v.decode(sys.stdin.encoding or constants.UTF8)
      if o == '-d':
        if delta is not None:
          delta += _DurationToTimeDelta(v)
        else:
          delta = _DurationToTimeDelta(v)
      elif o == '-m':
        method = v
      elif o == '-c':
        content_type = v
      elif o == '-p':
        passwd = v
      elif o == '-r':
        region = v
      elif o == '-u' or o == '--use-service-account':
        use_service_account = True
      elif o == '-b':
        billing_project = v
      else:
        self.RaiseInvalidArgumentException()

    if delta is None:
      delta = timedelta(hours=1)
    else:
      if use_service_account and delta > _MAX_EXPIRATION_TIME_WITH_MINUS_U:
        # This restriction comes from the IAM SignBlob API. The SignBlob
        # API uses a system-managed key which can guarantee validation only
        # up to 12 hours. b/156160482#comment4
        raise CommandException(
            'Max valid duration allowed is %s when -u flag is used. For longer'
            ' duration, consider using the private-key-file instead of the -u'
            ' option.' % _MAX_EXPIRATION_TIME_WITH_MINUS_U)
      elif delta > _MAX_EXPIRATION_TIME:
        raise CommandException('Max valid duration allowed is '
                               '%s' % _MAX_EXPIRATION_TIME)

    if method not in ['GET', 'PUT', 'DELETE', 'HEAD', 'RESUMABLE']:
      raise CommandException('HTTP method must be one of'
                             '[GET|HEAD|PUT|DELETE|RESUMABLE]')

    if not use_service_account and len(self.args) < 2:
      raise CommandException(
          'The command requires a key file argument and one or more '
          'URL arguments if the --use-service-account flag is missing. '
          'Run `gsutil help signurl` for more info')

    if use_service_account and billing_project:
      raise CommandException(
          'Specifying both the -b and --use-service-account options together is'
          'invalid.')

    return method, delta, content_type, passwd, region, use_service_account, billing_project

  def _ProbeObjectAccessWithClient(self, key, use_service_account, provider,
                                   client_email, gcs_path, generation, logger,
                                   region, billing_project):
    """Performs a head request against a signed URL to check for read access."""

    # Choose a reasonable time in the future; if the user's system clock is
    # 60 or more seconds behind the server's this will generate an error.
    signed_url = _GenSignedUrl(key=key,
                               api=self.gsutil_api,
                               use_service_account=use_service_account,
                               provider=provider,
                               client_id=client_email,
                               method='HEAD',
                               duration=timedelta(seconds=60),
                               gcs_path=gcs_path,
                               generation=generation,
                               logger=logger,
                               region=region,
                               billing_project=billing_project,
                               string_to_sign_debug=True)

    try:
      h = GetNewHttp()
      req = Request(signed_url, 'HEAD')
      response = MakeRequest(h, req)

      if response.status_code not in [200, 403, 404]:
        raise HttpError.FromResponse(response)

      return response.status_code
    except HttpError as http_error:
      if http_error.has_attr('response'):
        error_response = http_error.response
        error_string = ('Unexpected HTTP response code %s while querying '
                        'object readability. Is your system clock accurate?' %
                        error_response.status_code)
        if error_response.content:
          error_string += ' Content: %s' % error_response.content
      else:
        error_string = ('Expected an HTTP response code of '
                        '200 while querying object readability, but received '
                        'an error: %s' % http_error)
      raise CommandException(error_string)

  def _EnumerateStorageUrls(self, in_urls):
    ret = []

    for url_str in in_urls:
      if ContainsWildcard(url_str):
        ret.extend([blr.storage_url for blr in self.WildcardIterator(url_str)])
      else:
        ret.append(StorageUrlFromString(url_str))

    return ret

  def RunCommand(self):
    """Command entry point for signurl command."""
    if not HAVE_OPENSSL:
      raise CommandException(
          'The signurl command requires the pyopenssl library (try pip '
          'install pyopenssl or easy_install pyopenssl)')

    method, delta, content_type, passwd, region, use_service_account, billing_project = (
        self._ParseAndCheckSubOpts())
    arg_start_index = 0 if use_service_account else 1
    storage_urls = self._EnumerateStorageUrls(self.args[arg_start_index:])
    region_cache = {}

    key = None
    if not use_service_account:
      try:
        key, client_email = _ReadJSONKeystore(
            open(self.args[0], 'rb').read(), passwd)
      except ValueError:
        # Ignore and try parsing as a pkcs12.
        if not passwd:
          passwd = getpass.getpass('Keystore password:')
        try:
          key, client_email = _ReadKeystore(
              open(self.args[0], 'rb').read(), passwd)
        except ValueError:
          raise CommandException('Unable to parse private key from {0}'.format(
              self.args[0]))
    else:
      client_email = self.gsutil_api.GetServiceAccountId(provider='gs')

    print('URL\tHTTP Method\tExpiration\tSigned URL')
    for url in storage_urls:
      if url.scheme != 'gs':
        raise CommandException('Can only create signed urls from gs:// urls')
      if url.IsBucket():
        if region == _AUTO_DETECT_REGION:
          raise CommandException('Generating signed URLs for creating buckets'
                                 ' requires a region be specified via the -r '
                                 'option. Run `gsutil help signurl` for more '
                                 'information about the \'-r\' option.')
        gcs_path = url.bucket_name
        if method == 'RESUMABLE':
          raise CommandException('Resumable signed URLs require an object '
                                 'name.')
      else:
        # Need to URL encode the object name as Google Cloud Storage does when
        # computing the string to sign when checking the signature.
        gcs_path = '{0}/{1}'.format(
            url.bucket_name,
            urllib.parse.quote(url.object_name.encode(constants.UTF8),
                               safe=b'/~'))

      if region == _AUTO_DETECT_REGION:
        if url.bucket_name in region_cache:
          bucket_region = region_cache[url.bucket_name]
        else:
          try:
            _, bucket = self.GetSingleBucketUrlFromArg(
                'gs://{}'.format(url.bucket_name), bucket_fields=['location'])
          except Exception as e:
            raise CommandException(
                '{}: Failed to auto-detect location for bucket \'{}\'. Please '
                'ensure you have storage.buckets.get permission on the bucket '
                'or specify the bucket\'s location using the \'-r\' option.'.
                format(e.__class__.__name__, url.bucket_name))
          bucket_region = bucket.location.lower()
          region_cache[url.bucket_name] = bucket_region
      else:
        bucket_region = region
      final_url = _GenSignedUrl(key=key,
                                api=self.gsutil_api,
                                use_service_account=use_service_account,
                                provider=url.scheme,
                                client_id=client_email,
                                method=method,
                                duration=delta,
                                gcs_path=gcs_path,
                                generation=url.generation,
                                logger=self.logger,
                                region=bucket_region,
                                content_type=content_type,
                                billing_project=billing_project,
                                string_to_sign_debug=True)

      expiration = calendar.timegm((datetime.utcnow() + delta).utctimetuple())
      expiration_dt = datetime.fromtimestamp(expiration)

      time_str = expiration_dt.strftime('%Y-%m-%d %H:%M:%S')
      # TODO(PY3-ONLY): Delete this if block.
      if six.PY2:
        time_str = time_str.decode(constants.UTF8)

      url_info_str = '{0}\t{1}\t{2}\t{3}'.format(url.url_string, method,
                                                 time_str, final_url)

      # TODO(PY3-ONLY): Delete this if block.
      if six.PY2:
        url_info_str = url_info_str.encode(constants.UTF8)

      print(url_info_str)

      response_code = self._ProbeObjectAccessWithClient(
          key, use_service_account, url.scheme, client_email, gcs_path,
          url.generation, self.logger, bucket_region, billing_project)

      if response_code == 404:
        if url.IsBucket() and method != 'PUT':
          raise CommandException(
              'Bucket {0} does not exist. Please create a bucket with '
              'that name before a creating signed URL to access it.'.format(
                  url))
        else:
          if method != 'PUT' and method != 'RESUMABLE':
            raise CommandException(
                'Object {0} does not exist. Please create/upload an object '
                'with that name before a creating signed URL to access it.'.
                format(url))
      elif response_code == 403:
        self.logger.warn(
            '%s does not have permissions on %s, using this link will likely '
            'result in a 403 error until at least READ permissions are granted',
            client_email or 'The account', url)

    return 0
