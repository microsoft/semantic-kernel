# -*- coding: utf-8 -*-
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""This module provides the rpo command to gsutil."""

from __future__ import absolute_import
from __future__ import print_function

import textwrap

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

VALID_RPO_VALUES = ('ASYNC_TURBO', 'DEFAULT')
VALID_RPO_VALUES_STRING = '({})'.format('|'.join(VALID_RPO_VALUES))

_SET_SYNOPSIS = """
  gsutil rpo set {} gs://<bucket_name>...
""".format(VALID_RPO_VALUES_STRING)

_GET_SYNOPSIS = """
  gsutil rpo get gs://<bucket_name>...
"""

_SYNOPSIS = _SET_SYNOPSIS + _GET_SYNOPSIS.lstrip('\n')

_SET_DESCRIPTION = """
<B>SET</B>
  The ``rpo set`` command configures turbo replication
  for dual-region Google Cloud Storage buckets.

<B>SET EXAMPLES</B>
  Configure your buckets to use turbo replication:

    gsutil rpo set ASYNC_TURBO gs://redbucket gs://bluebucket

  Configure your buckets to NOT use turbo replication:

    gsutil rpo set DEFAULT gs://redbucket gs://bluebucket
"""

_GET_DESCRIPTION = """
<B>GET</B>
  The ``rpo get`` command returns the replication setting
  for the specified Cloud Storage buckets.

<B>GET EXAMPLES</B>
  Check if your buckets are using turbo replication:

    gsutil rpo get gs://redbucket gs://bluebucket
"""

_DESCRIPTION = """
  The ``rpo`` command is used to retrieve or configure the
  `replication setting
  <https://cloud.google.com/storage/docs/availability-durability#cross-region-redundancy>`_
  of dual-region Cloud Storage buckets.
  This command has two sub-commands: ``get`` and ``set``.
""" + _GET_DESCRIPTION + _SET_DESCRIPTION

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)
_set_help_text = CreateHelpText(_SET_SYNOPSIS, _SET_DESCRIPTION)
_get_help_text = CreateHelpText(_GET_SYNOPSIS, _GET_DESCRIPTION)

GET_COMMAND = GcloudStorageMap(gcloud_command=[
    'storage', 'buckets', 'list',
    '--format=value[separator=": "](format("gs://{}", name),'
    'rpo.yesno(no="None"))', '--raw'
],
                               flag_map={})

SET_COMMAND = GcloudStorageMap(
    gcloud_command=[
        'storage', 'buckets', 'update', '--recovery-point-objective'
    ],
    flag_map={},
)


class RpoCommand(Command):
  """Implements the gsutil rpo command."""

  command_spec = Command.CreateCommandSpec(
      'rpo',
      command_name_aliases=[],
      usage_synopsis=_SYNOPSIS,
      min_args=2,
      max_args=NO_MAX,
      supported_sub_args='',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=2,
      gs_api_support=[ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments={
          'get': [CommandArgument.MakeNCloudURLsArgument(1)],
          'set': [
              CommandArgument('mode', choices=list(VALID_RPO_VALUES)),
              CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument(),
          ],
      })
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='rpo',
      help_name_aliases=[],
      help_type='command_help',
      help_one_line_summary='Configure replication',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={
          'get': _get_help_text,
          'set': _set_help_text,
      },
  )

  gcloud_storage_map = GcloudStorageMap(
      gcloud_command={
          'get': GET_COMMAND,
          'set': SET_COMMAND,
      },
      flag_map={},
  )

  def _ValidateBucketListingRefAndReturnBucketName(self, blr):
    if blr.storage_url.scheme != 'gs':
      raise CommandException(
          'The %s command can only be used with gs:// bucket URLs.' %
          self.command_name)

  def _GetRpo(self, blr):
    """Gets the rpo setting for a bucket."""
    bucket_url = blr.storage_url

    bucket_metadata = self.gsutil_api.GetBucket(bucket_url.bucket_name,
                                                fields=['rpo'],
                                                provider=bucket_url.scheme)
    rpo = bucket_metadata.rpo
    bucket = str(bucket_url).rstrip('/')
    print('%s: %s' % (bucket, rpo))

  def _SetRpo(self, blr, rpo_value):
    """Sets the rpo setting for a bucket."""
    bucket_url = blr.storage_url
    formatted_rpo_value = rpo_value
    if formatted_rpo_value not in VALID_RPO_VALUES:
      raise CommandException(
          'Invalid value for rpo set.'
          ' Should be one of {}'.format(VALID_RPO_VALUES_STRING))

    bucket_metadata = apitools_messages.Bucket(rpo=formatted_rpo_value)

    self.logger.info('Setting rpo %s for %s' %
                     (formatted_rpo_value, str(bucket_url).rstrip('/')))

    self.gsutil_api.PatchBucket(bucket_url.bucket_name,
                                bucket_metadata,
                                fields=['rpo'],
                                provider=bucket_url.scheme)
    return 0

  def _Rpo(self):
    """Handles rpo command on Cloud Storage buckets."""
    subcommand = self.args.pop(0)

    if subcommand not in ('get', 'set'):
      raise CommandException('rpo only supports get|set')

    subcommand_func = None
    subcommand_args = []

    if subcommand == 'get':
      subcommand_func = self._GetRpo
    elif subcommand == 'set':
      subcommand_func = self._SetRpo
      setting_arg = self.args.pop(0)
      subcommand_args.append(setting_arg)

    # TODO: Remove this as rpo should work for XML as well.
    if self.gsutil_api.GetApiSelector('gs') != ApiSelector.JSON:
      raise CommandException('\n'.join(
          textwrap.wrap(('The "%s" command can only be with the Cloud Storage '
                         'JSON API.') % self.command_name)))

    # Iterate over bucket args, performing the specified subsubcommand.
    some_matched = False
    url_args = self.args
    if not url_args:
      self.RaiseWrongNumberOfArgumentsException()
    for url_str in url_args:
      # Throws a CommandException if the argument is not a bucket.
      bucket_iter = self.GetBucketUrlIterFromArg(url_str)
      for bucket_listing_ref in bucket_iter:
        # TODO: Make this more general when adding RPO support for the XML API.
        if self.gsutil_api.GetApiSelector(
            bucket_listing_ref.storage_url.scheme) != ApiSelector.JSON:
          raise CommandException('\n'.join(
              textwrap.wrap(('The "%s" command can only be used for GCS '
                             'buckets.') % self.command_name)))

        some_matched = True
        subcommand_func(bucket_listing_ref, *subcommand_args)

    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(url_args))
    return 0

  def RunCommand(self):
    """Command entry point for the rpo command."""
    action_subcommand = self.args[0]
    self.ParseSubOpts(check_args=True)

    if action_subcommand == 'get' or action_subcommand == 'set':
      metrics.LogCommandParams(sub_opts=self.sub_opts)
      metrics.LogCommandParams(subcommands=[action_subcommand])
      return self._Rpo()
    else:
      raise CommandException('Invalid subcommand "%s", use get|set instead.' %
                             action_subcommand)
