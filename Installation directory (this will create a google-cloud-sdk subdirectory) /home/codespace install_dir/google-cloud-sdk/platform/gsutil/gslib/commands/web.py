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
"""Implementation of website configuration command for buckets."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import sys

from apitools.base.py import encoding

from gslib import metrics
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.exception import NO_URLS_MATCHED_TARGET
from gslib.help_provider import CreateHelpText
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils.constants import NO_MAX
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap

_SET_SYNOPSIS = """
  gsutil web set [-m <main_page_suffix>] [-e <error_page>] gs://<bucket_name>...
"""

_GET_SYNOPSIS = """
  gsutil web get gs://<bucket_name>
"""

_SYNOPSIS = _SET_SYNOPSIS + _GET_SYNOPSIS.lstrip('\n')

_SET_DESCRIPTION = """
<B>SET</B>
  The ``gsutil web set`` command allows you to configure or disable the website
  configuration on your buckets. The ``set`` sub-command has the following
  options (omit both options to unset the configuration):

<B>SET OPTIONS</B>
  -m <index.html>      Specifies the object name to serve when a bucket
                       listing is requested via a custom domain.

  -e <404.html>        Specifies the error page to serve when a request is made
                       for a non-existent object via a custom domain

"""

_GET_DESCRIPTION = """
<B>GET</B>
  The ``gsutil web get`` command retrieves the web semantics configuration for
  a bucket and displays a JSON representation of the configuration.

  In Google Cloud Storage, this would look like the following:

    {
      "notFoundPage": "404.html",
      "mainPageSuffix": "index.html"
    }

"""

_DESCRIPTION = """
  Cloud Storage allows you to configure a bucket to behave like a static
  website when the bucket is accessed through a `custom domain
  <https://cloud.google.com/storage/docs/request-endpoints#custom-domains>`_.
  For example, if you set a ``main_page_suffix``, a subsequent GET bucket
  request through a custom domain serves the specified "main" page instead of
  performing the usual bucket listing. Similarly, if you set an ``error_page``,
  a subsequent GET object request through a custom domain for a non-existent
  object serves the specified error page instead of the standard Cloud Storage
  error.

  Requests to a bucket through other `endpoints
  <https://cloud.google.com/storage/docs/request-endpoints>`_ are unaffected
  by the bucket's website configuration.

  See `Static website examples and tips
  <https://cloud.google.com/storage/docs/static-website>`_ for additional
  examples and information.

  Notes:

  1. Because the main page is only served when a bucket listing request is made
     via a custom domain endpoint, you can continue to use ``gsutil ls`` as you
     normally would for bucket listing.

  2. The main_page_suffix applies to each subdirectory of the bucket. For
     example, with the main_page_suffix configured to be index.html, a GET
     request for ``http://www.example.com`` retrieves
     ``http://www.example.com/index.html`` but shows ``http://www.example.com`` as
     the URL to the requester, and a GET request for
     ``http://www.example.com/photos`` retrieves
     ``http://www.example.com/photos/index.html`` but shows ``http://www.example.com/photos``
     as the URL to the requester.

  3. There is just one 404.html page. For example, a GET request for
     ``http://www.example.com/photos/missing`` retrieves
     ``http://www.example.com/404.html``, not
     ``http://www.example.com/photos/404.html``.

  The web command has two sub-commands:
""" + _SET_DESCRIPTION + _GET_DESCRIPTION

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)

_get_help_text = CreateHelpText(_GET_SYNOPSIS, _GET_DESCRIPTION)
_set_help_text = CreateHelpText(_SET_SYNOPSIS, _SET_DESCRIPTION)


class WebCommand(Command):
  """Implementation of gsutil web command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'web',
      command_name_aliases=['setwebcfg', 'getwebcfg'],
      usage_synopsis=_SYNOPSIS,
      min_args=2,
      max_args=NO_MAX,
      supported_sub_args='m:e:',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=1,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments={
          'set': [CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument()],
          'get': [CommandArgument.MakeNCloudBucketURLsArgument(1)],
      },
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='web',
      help_name_aliases=['getwebcfg', 'setwebcfg'],
      help_type='command_help',
      help_one_line_summary=('Set a website configuration for a bucket'),
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
                      '--format="gsutiljson[key=website_config,empty=\' has '
                      'no website configuration.\',empty_prefix_key='
                      'storage_url]"', '--raw'
                  ],
                  flag_map={},
                  supports_output_translation=True,
              ),
          # "set" subcommand handled in get_gcloud_storage_args.
      },
      flag_map={},
  )

  def get_gcloud_storage_args(self):
    if self.args[0] == 'set':
      set_command_map = GcloudStorageMap(
          gcloud_command={
              'set':
                  GcloudStorageMap(
                      gcloud_command=[
                          'storage',
                          'buckets',
                          'update',
                      ],
                      flag_map={
                          '-e': GcloudStorageFlag('--web-error-page'),
                          '-m': GcloudStorageFlag('--web-main-page-suffix'),
                      })
          },
          flag_map={},
      )
      if not ('-e' in self.args or '-m' in self.args):
        set_command_map.gcloud_command['set'].gcloud_command += [
            '--clear-web-error-page', '--clear-web-main-page-suffix'
        ]

      gcloud_storage_map = set_command_map
    else:
      gcloud_storage_map = WebCommand.gcloud_storage_map

    return super().get_gcloud_storage_args(gcloud_storage_map)

  def _GetWeb(self):
    """Gets website configuration for a bucket."""
    bucket_url, bucket_metadata = self.GetSingleBucketUrlFromArg(
        self.args[0], bucket_fields=['website'])

    if bucket_url.scheme == 's3':
      sys.stdout.write(
          self.gsutil_api.XmlPassThroughGetWebsite(bucket_url,
                                                   provider=bucket_url.scheme))
    else:
      if bucket_metadata.website and (bucket_metadata.website.mainPageSuffix or
                                      bucket_metadata.website.notFoundPage):
        sys.stdout.write(
            str(encoding.MessageToJson(bucket_metadata.website)) + '\n')
      else:
        sys.stdout.write('%s has no website configuration.\n' % bucket_url)

    return 0

  def _SetWeb(self):
    """Sets website configuration for a bucket."""
    main_page_suffix = None
    error_page = None
    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-m':
          main_page_suffix = a
        elif o == '-e':
          error_page = a

    url_args = self.args

    website = apitools_messages.Bucket.WebsiteValue(
        mainPageSuffix=main_page_suffix, notFoundPage=error_page)

    # Iterate over URLs, expanding wildcards and setting the website
    # configuration on each.
    some_matched = False
    for url_str in url_args:
      bucket_iter = self.GetBucketUrlIterFromArg(url_str, bucket_fields=['id'])
      for blr in bucket_iter:
        url = blr.storage_url
        some_matched = True
        self.logger.info('Setting website configuration on %s...', blr)
        bucket_metadata = apitools_messages.Bucket(website=website)
        self.gsutil_api.PatchBucket(url.bucket_name,
                                    bucket_metadata,
                                    provider=url.scheme,
                                    fields=['id'])
    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(url_args))
    return 0

  def RunCommand(self):
    """Command entry point for the web command."""
    action_subcommand = self.args.pop(0)
    self.ParseSubOpts(check_args=True)
    if action_subcommand == 'get':
      func = self._GetWeb
    elif action_subcommand == 'set':
      func = self._SetWeb
    else:
      raise CommandException(
          ('Invalid subcommand "%s" for the %s command.\n'
           'See "gsutil help web".') % (action_subcommand, self.command_name))

    # Commands with both suboptions and subcommands need to reparse for
    # suboptions, so we log again.
    metrics.LogCommandParams(subcommands=[action_subcommand],
                             sub_opts=self.sub_opts)
    return func()
