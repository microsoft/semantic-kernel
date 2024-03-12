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
"""Implementation of versioning configuration command for buckets."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib import metrics
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.exception import NO_URLS_MATCHED_TARGET
from gslib.help_provider import CreateHelpText
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils.constants import NO_MAX
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils import shim_util

_SET_SYNOPSIS = """
  gsutil versioning set (on|off) gs://<bucket_name>...
"""

_GET_SYNOPSIS = """
  gsutil versioning get gs://<bucket_name>...
"""

_SYNOPSIS = _SET_SYNOPSIS + _GET_SYNOPSIS.lstrip('\n')

_SET_DESCRIPTION = """
<B>SET</B>
  The "set" sub-command requires an additional sub-command, either "on" or
  "off", which, respectively, will enable or disable versioning for the
  specified bucket(s).

"""

_GET_DESCRIPTION = """
<B>GET</B>
  The "get" sub-command gets the versioning configuration for a
  bucket and displays whether or not it is enabled.
"""

_DESCRIPTION = """
  The `Versioning Configuration
  <https://cloud.google.com/storage/docs/object-versioning>`_ feature
  enables you to configure a Google Cloud Storage bucket to keep old
  versions of objects.

  The gsutil versioning command has two sub-commands:
""" + _SET_DESCRIPTION + _GET_DESCRIPTION

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)

_GCLOUD_FORMAT_STRING = ('--format=value[separator=""](' + 'name.sub("' +
                         shim_util.get_format_flag_caret() +
                         '", "gs://").sub("$", ": "),' + 'versioning.enabled' +
                         '.yesno("Enabled", "Suspended"))')

_get_help_text = CreateHelpText(_GET_SYNOPSIS, _GET_DESCRIPTION)
_set_help_text = CreateHelpText(_SET_SYNOPSIS, _SET_DESCRIPTION)


class VersioningCommand(Command):
  """Implementation of gsutil versioning command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'versioning',
      command_name_aliases=['setversioning', 'getversioning'],
      usage_synopsis=_SYNOPSIS,
      min_args=2,
      max_args=NO_MAX,
      supported_sub_args='',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=2,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments={
          'set': [
              CommandArgument('mode', choices=['on', 'off']),
              CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument()
          ],
          'get': [CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument(),],
      },
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='versioning',
      help_name_aliases=[
          'getversioning',
          'setversioning',
      ],
      help_type='command_help',
      help_one_line_summary=(
          'Enable or suspend versioning for one or more buckets'),
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
                      'storage', 'buckets', 'list', '--raw',
                      _GCLOUD_FORMAT_STRING
                  ],
                  flag_map={},
                  supports_output_translation=True,
              ),
          'set':
              GcloudStorageMap(
                  gcloud_command={
                      'on':
                          GcloudStorageMap(
                              gcloud_command=[
                                  'storage',
                                  'buckets',
                                  'update',
                                  '--versioning',
                              ],
                              flag_map={},
                          ),
                      'off':
                          GcloudStorageMap(
                              gcloud_command=[
                                  'storage',
                                  'buckets',
                                  'update',
                                  '--no-versioning',
                              ],
                              flag_map={},
                          ),
                  },
                  flag_map={},
              )
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

  def _SetVersioning(self):
    """Gets versioning configuration for a bucket."""
    versioning_arg = self.args[0].lower()
    if versioning_arg not in ('on', 'off'):
      raise CommandException('Argument to "%s set" must be either <on|off>' %
                             (self.command_name))
    url_args = self.args[1:]
    if not url_args:
      self.RaiseWrongNumberOfArgumentsException()

    # Iterate over URLs, expanding wildcards and set the versioning
    # configuration on each.
    some_matched = False
    for url_str in url_args:
      bucket_iter = self.GetBucketUrlIterFromArg(url_str, bucket_fields=['id'])
      for blr in bucket_iter:
        url = blr.storage_url
        some_matched = True
        bucket_metadata = apitools_messages.Bucket(
            versioning=apitools_messages.Bucket.VersioningValue())
        if versioning_arg == 'on':
          self.logger.info('Enabling versioning for %s...', url)
          bucket_metadata.versioning.enabled = True
        else:
          self.logger.info('Suspending versioning for %s...', url)
          bucket_metadata.versioning.enabled = False
        self.gsutil_api.PatchBucket(url.bucket_name,
                                    bucket_metadata,
                                    provider=url.scheme,
                                    fields=['id'])
    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(url_args))

  def _GetVersioning(self):
    """Gets versioning configuration for one or more buckets."""
    url_args = self.args

    # Iterate over URLs, expanding wildcards and getting the versioning
    # configuration on each.
    some_matched = False
    for url_str in url_args:
      bucket_iter = self.GetBucketUrlIterFromArg(url_str,
                                                 bucket_fields=['versioning'])
      for blr in bucket_iter:
        some_matched = True
        if blr.root_object.versioning and blr.root_object.versioning.enabled:
          print('%s: Enabled' % blr.url_string.rstrip('/'))
        else:
          print('%s: Suspended' % blr.url_string.rstrip('/'))
    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(url_args))

  def RunCommand(self):
    """Command entry point for the versioning command."""
    action_subcommand = self.args.pop(0)
    if action_subcommand == 'get':
      func = self._GetVersioning
      metrics.LogCommandParams(subcommands=[action_subcommand])
    elif action_subcommand == 'set':
      func = self._SetVersioning
      versioning_arg = self.args[0].lower()
      if versioning_arg in ('on', 'off'):
        metrics.LogCommandParams(
            subcommands=[action_subcommand, versioning_arg])
    else:
      raise CommandException(
          ('Invalid subcommand "%s" for the %s command.\n'
           'See "gsutil help %s".') %
          (action_subcommand, self.command_name, self.command_name))
    func()
    return 0
