# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""Implementation of cors configuration command for GCS buckets."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import sys

from gslib import metrics
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.exception import NO_URLS_MATCHED_TARGET
from gslib.help_provider import CreateHelpText
from gslib.storage_url import StorageUrlFromString
from gslib.storage_url import UrlsAreForSingleProvider
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils.constants import NO_MAX
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils.translation_helper import CorsTranslation
from gslib.utils.translation_helper import REMOVE_CORS_CONFIG

_GET_SYNOPSIS = """
  gsutil cors get gs://<bucket_name>
"""

_SET_SYNOPSIS = """
  gsutil cors set <cors-json-file> gs://<bucket_name>...
"""

_GET_DESCRIPTION = """
<B>GET</B>
  Gets the CORS configuration for a single bucket. The output from
  ``cors get`` can be redirected into a file, edited and then updated using
  ``cors set``.
"""

_SET_DESCRIPTION = """
<B>SET</B>
  Sets the CORS configuration for one or more buckets. The ``cors-json-file``
  specified on the command line should be a path to a local file containing
  a JSON-formatted CORS configuration, such as the example described above.
"""

_SYNOPSIS = _SET_SYNOPSIS + _GET_SYNOPSIS.lstrip('\n') + '\n\n'

_DESCRIPTION = ("""
  Gets or sets the Cross-Origin Resource Sharing (CORS) configuration on one or
  more buckets. This command is supported for buckets only, not objects. An
  example CORS JSON file looks like the following:

    [
      {
        "origin": ["http://origin1.example.com"],
        "responseHeader": ["Content-Type"],
        "method": ["GET"],
        "maxAgeSeconds": 3600
      }
    ]

  The above CORS configuration explicitly allows cross-origin GET requests from
  http://origin1.example.com and may include the Content-Type response header.
  The preflight request may be cached for 1 hour.

  Note that requests to the authenticated browser download endpoint ``storage.cloud.google.com``
  do not allow CORS requests. For more information about supported endpoints for CORS, see
  `Cloud Storage CORS support <https://cloud.google.com/storage/docs/cross-origin#server-side-support>`_.

  The following (empty) CORS JSON file removes any CORS configuration for a
  bucket:

    []

  The cors command has two sub-commands:
""" + '\n'.join([_GET_DESCRIPTION, _SET_DESCRIPTION]) + """
For more info about CORS generally, see https://www.w3.org/TR/cors/.
For more info about CORS in Cloud Storage, see the
`CORS concept page <https://cloud.google.com/storage/docs/cross-origin>`_.
""")

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)

_get_help_text = CreateHelpText(_GET_SYNOPSIS, _GET_DESCRIPTION)
_set_help_text = CreateHelpText(_SET_SYNOPSIS, _SET_DESCRIPTION)


class CorsCommand(Command):
  """Implementation of gsutil cors command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'cors',
      command_name_aliases=['getcors', 'setcors'],
      usage_synopsis=_SYNOPSIS,
      min_args=2,
      max_args=NO_MAX,
      supported_sub_args='',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=1,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments={
          'set': [
              CommandArgument.MakeNFileURLsArgument(1),
              CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument(),
          ],
          'get': [CommandArgument.MakeNCloudBucketURLsArgument(1),]
      })
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='cors',
      help_name_aliases=[
          'getcors',
          'setcors',
          'cross-origin',
      ],
      help_type='command_help',
      help_one_line_summary=(
          'Get or set a CORS configuration for one or more buckets'),
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={
          'get': _get_help_text,
          'set': _set_help_text,
      },
  )

  gcloud_storage_map = GcloudStorageMap(
      gcloud_command={
          'get':
              GcloudStorageMap(
                  gcloud_command=[
                      'storage', 'buckets', 'describe',
                      '--format="gsutiljson[key=cors_config,empty=\' has no '
                      'CORS configuration.\',empty_prefix_key=storage_url]"',
                      '--raw'
                  ],
                  flag_map={},
              ),
          'set':
              GcloudStorageMap(
                  gcloud_command=[
                      'storage', 'buckets', 'update', '--cors-file'
                  ],
                  flag_map={},
              ),
      },
      flag_map={},
  )

  def _CalculateUrlsStartArg(self):
    if not self.args:
      self.RaiseWrongNumberOfArgumentsException()
    if self.args[0].lower() == 'set':
      return 2
    else:
      return 1

  def _SetCors(self):
    """Sets CORS configuration on a Google Cloud Storage bucket."""
    cors_arg = self.args[0]
    url_args = self.args[1:]
    # Disallow multi-provider 'cors set' requests.
    if not UrlsAreForSingleProvider(url_args):
      raise CommandException('"%s" command spanning providers not allowed.' %
                             self.command_name)

    # Open, read and parse file containing JSON document.
    cors_file = open(cors_arg, 'r')
    cors_txt = cors_file.read()
    cors_file.close()

    self.api = self.gsutil_api.GetApiSelector(
        StorageUrlFromString(url_args[0]).scheme)

    # Iterate over URLs, expanding wildcards and setting the CORS on each.
    some_matched = False
    for url_str in url_args:
      bucket_iter = self.GetBucketUrlIterFromArg(url_str, bucket_fields=['id'])
      for blr in bucket_iter:
        url = blr.storage_url
        some_matched = True
        self.logger.info('Setting CORS on %s...', blr)
        if url.scheme == 's3':
          self.gsutil_api.XmlPassThroughSetCors(cors_txt,
                                                url,
                                                provider=url.scheme)
        else:
          cors = CorsTranslation.JsonCorsToMessageEntries(cors_txt)
          if not cors:
            cors = REMOVE_CORS_CONFIG
          bucket_metadata = apitools_messages.Bucket(cors=cors)
          self.gsutil_api.PatchBucket(url.bucket_name,
                                      bucket_metadata,
                                      provider=url.scheme,
                                      fields=['id'])
    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(url_args))
    return 0

  def _GetCors(self):
    """Gets CORS configuration for a Google Cloud Storage bucket."""
    bucket_url, bucket_metadata = self.GetSingleBucketUrlFromArg(
        self.args[0], bucket_fields=['cors'])

    if bucket_url.scheme == 's3':
      sys.stdout.write(
          self.gsutil_api.XmlPassThroughGetCors(bucket_url,
                                                provider=bucket_url.scheme))
    else:
      if bucket_metadata.cors:
        sys.stdout.write(
            CorsTranslation.MessageEntriesToJson(bucket_metadata.cors))
      else:
        sys.stdout.write('%s has no CORS configuration.\n' % bucket_url)
    return 0

  def RunCommand(self):
    """Command entry point for the cors command."""
    action_subcommand = self.args.pop(0)
    if action_subcommand == 'get':
      func = self._GetCors
    elif action_subcommand == 'set':
      func = self._SetCors
    else:
      raise CommandException(
          ('Invalid subcommand "%s" for the %s command.\n'
           'See "gsutil help cors".') % (action_subcommand, self.command_name))
    metrics.LogCommandParams(subcommands=[action_subcommand])
    return func()
