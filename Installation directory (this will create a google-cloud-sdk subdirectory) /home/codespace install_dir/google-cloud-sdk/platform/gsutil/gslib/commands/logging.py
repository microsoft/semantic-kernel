# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
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
"""Implementation of logging configuration command for buckets."""

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
from gslib.storage_url import StorageUrlFromString
from gslib.storage_url import UrlsAreForSingleProvider
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils.constants import NO_MAX
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils import text_util

_SET_SYNOPSIS = """
  gsutil logging set on -b <logging_bucket_name> [-o <log_object_prefix>] gs://<bucket_name>...
  gsutil logging set off gs://<bucket_name>...
"""

_GET_SYNOPSIS = """
  gsutil logging get gs://<bucket_name>
"""

_SYNOPSIS = _SET_SYNOPSIS + _GET_SYNOPSIS.lstrip('\n') + '\n'

_SET_DESCRIPTION = """
<B>SET</B>
  The ``set`` sub-command has two sub-commands:

<B>ON</B>
  The ``gsutil logging set on`` command enables usage and storage logging
  for the buckets named by the specified URLs, outputting log files to the
  bucket specified with the ``-b`` flag. Cloud Storage doesn't validate the
  existence of the output bucket, so users should ensure it already exists,
  and all URLs must name Cloud Storage buckets (e.g., ``gs://bucket``). The
  optional ``-o`` flag specifies the prefix for log object names. The
  default prefix is the bucket name. For example, the command:

    gsutil logging set on -b gs://my_logging_bucket -o UsageLog \\
        gs://my_bucket1 gs://my_bucket2

  causes all read and write activity to objects in ``gs://mybucket1`` and
  ``gs://mybucket2`` to be logged to objects prefixed with the name
  ``UsageLog``, with those log objects written to the bucket
  ``gs://my_logging_bucket``.

  In addition to enabling logging on your bucket(s), you also need to grant
  cloud-storage-analytics@google.com write access to the log bucket, using this
  command:

    gsutil acl ch -g cloud-storage-analytics@google.com:W gs://my_logging_bucket

  Note that log data may contain sensitive information, so you should make
  sure to set an appropriate default bucket ACL to protect that data. (See
  "gsutil help defacl".)

<B>OFF</B>
  This command disables usage and storage logging for the buckets named by the
  specified URLs. All URLs must name Cloud Storage buckets (e.g.,
  ``gs://bucket``).

  No logging data is removed from the log buckets when you disable logging,
  but Google Cloud Storage stops delivering new logs once you have run this
  command.

"""

_GET_DESCRIPTION = """
<B>GET</B>
  If logging is enabled for the specified bucket url, the server responds
  with a JSON document that looks something like this:

    {
      "logBucket": "my_logging_bucket",
      "logObjectPrefix": "UsageLog"
    }

  You can download log data from your log bucket using the gsutil cp command.

"""

_DESCRIPTION = """
  Google Cloud Storage offers `usage logs and storage logs
  <https://cloud.google.com/storage/docs/access-logs>`_ in the form of CSV
  files that you can download and view. Usage logs provide information for all
  of the requests made on a specified bucket and are created hourly. Storage
  logs provide information about the storage consumption of that bucket for
  the last day and are created daily.

  Once set up, usage logs and storage logs are automatically created as new
  objects in a bucket that you specify. Usage logs and storage logs are
  subject to the same pricing as other objects stored in Cloud Storage.

  For a complete list of usage log fields and storage data fields, see
  `Usage and storage log format
  <https://cloud.google.com/storage/docs/access-logs#format>`_.
  
  The ``logging`` command has two sub-commands:
""" + _SET_DESCRIPTION + _GET_DESCRIPTION + """

<B>OPTIONS</B>
  -b bucket_name Specifies the bucket that stores the generated logs. This
                 flag is only available for the ``set on`` command and is
                 required for that command.

  -o log_prefix  Specifies a common prefix for the names of generated
                 logs. This flag is only available for the ``set on``
                 command and is optional for that command.
"""

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)

_get_help_text = CreateHelpText(_GET_SYNOPSIS, _GET_DESCRIPTION)
_set_help_text = CreateHelpText(_SET_SYNOPSIS, _SET_DESCRIPTION)


class LoggingCommand(Command):
  """Implementation of gsutil logging command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'logging',
      command_name_aliases=['disablelogging', 'enablelogging', 'getlogging'],
      usage_synopsis=_SYNOPSIS,
      min_args=2,
      max_args=NO_MAX,
      supported_sub_args='b:o:',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=0,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[
          CommandArgument('mode', choices=['on', 'off']),
          CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument(),
      ],
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='logging',
      help_name_aliases=[
          'loggingconfig',
          'logs',
          'log',
          'getlogging',
          'enablelogging',
          'disablelogging',
      ],
      help_type='command_help',
      help_one_line_summary='Configure or retrieve logging on buckets',
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
                      'storage', 'buckets', 'list',
                      '--format="gsutiljson[key=logging_config,empty=\' has '
                      'no logging configuration.\',empty_prefix_key='
                      'storage_url]"', '--raw'
                  ],
                  flag_map={},
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
                              ],
                              flag_map={
                                  '-b':
                                      GcloudStorageFlag('--log-bucket'),
                                  '-o':
                                      GcloudStorageFlag('--log-object-prefix'),
                              },
                          ),
                      'off':
                          GcloudStorageMap(
                              gcloud_command=[
                                  'storage',
                                  'buckets',
                                  'update',
                                  '--clear-log-bucket',
                                  '--clear-log-object-prefix',
                              ],
                              flag_map={},
                          ),
                  },
                  flag_map={},
              )
      },
      flag_map={},
  )

  def _Get(self):
    """Gets logging configuration for a bucket."""
    bucket_url, bucket_metadata = self.GetSingleBucketUrlFromArg(
        self.args[0], bucket_fields=['logging'])

    if bucket_url.scheme == 's3':
      text_util.print_to_fd(self.gsutil_api.XmlPassThroughGetLogging(
          bucket_url, provider=bucket_url.scheme),
                            end='')
    else:
      if (bucket_metadata.logging and bucket_metadata.logging.logBucket and
          bucket_metadata.logging.logObjectPrefix):
        text_util.print_to_fd(
            str(encoding.MessageToJson(bucket_metadata.logging)))
      else:
        text_util.print_to_fd('%s has no logging configuration.' % bucket_url)
    return 0

  def _Enable(self):
    """Enables logging configuration for a bucket."""
    # Disallow multi-provider 'logging set on' calls, because the schemas
    # differ.
    if not UrlsAreForSingleProvider(self.args):
      raise CommandException('"logging set on" command spanning providers not '
                             'allowed.')
    target_bucket_url = None
    target_prefix = None
    for opt, opt_arg in self.sub_opts:
      if opt == '-b':
        target_bucket_url = StorageUrlFromString(opt_arg)
      if opt == '-o':
        target_prefix = opt_arg

    if not target_bucket_url:
      raise CommandException('"logging set on" requires \'-b <log_bucket>\' '
                             'option')
    if not target_bucket_url.IsBucket():
      raise CommandException('-b option must specify a bucket URL.')

    # Iterate over URLs, expanding wildcards and setting logging on each.
    some_matched = False
    for url_str in self.args:
      bucket_iter = self.GetBucketUrlIterFromArg(url_str, bucket_fields=['id'])
      for blr in bucket_iter:
        url = blr.storage_url
        some_matched = True
        self.logger.info('Enabling logging on %s...', blr)
        logging = apitools_messages.Bucket.LoggingValue(
            logBucket=target_bucket_url.bucket_name,
            logObjectPrefix=target_prefix or url.bucket_name)

        bucket_metadata = apitools_messages.Bucket(logging=logging)
        self.gsutil_api.PatchBucket(url.bucket_name,
                                    bucket_metadata,
                                    provider=url.scheme,
                                    fields=['id'])
    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(self.args))
    return 0

  def _Disable(self):
    """Disables logging configuration for a bucket."""
    # Iterate over URLs, expanding wildcards, and disabling logging on each.
    some_matched = False
    for url_str in self.args:
      bucket_iter = self.GetBucketUrlIterFromArg(url_str, bucket_fields=['id'])
      for blr in bucket_iter:
        url = blr.storage_url
        some_matched = True
        self.logger.info('Disabling logging on %s...', blr)
        logging = apitools_messages.Bucket.LoggingValue()

        bucket_metadata = apitools_messages.Bucket(logging=logging)
        self.gsutil_api.PatchBucket(url.bucket_name,
                                    bucket_metadata,
                                    provider=url.scheme,
                                    fields=['id'])
    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(self.args))
    return 0

  def RunCommand(self):
    """Command entry point for the logging command."""
    # Parse the subcommand and alias for the new logging command.
    action_subcommand = self.args.pop(0)
    if action_subcommand == 'get':
      func = self._Get
      metrics.LogCommandParams(subcommands=[action_subcommand])
    elif action_subcommand == 'set':
      state_subcommand = self.args.pop(0)
      if not self.args:
        self.RaiseWrongNumberOfArgumentsException()
      if state_subcommand == 'on':
        func = self._Enable
        metrics.LogCommandParams(
            subcommands=[action_subcommand, state_subcommand])
      elif state_subcommand == 'off':
        func = self._Disable
        metrics.LogCommandParams(
            subcommands=[action_subcommand, state_subcommand])
      else:
        raise CommandException(
            ('Invalid subcommand "%s" for the "%s %s" command.\n'
             'See "gsutil help logging".') %
            (state_subcommand, self.command_name, action_subcommand))
    else:
      raise CommandException(('Invalid subcommand "%s" for the %s command.\n'
                              'See "gsutil help logging".') %
                             (action_subcommand, self.command_name))
    self.ParseSubOpts(check_args=True)
    # Commands with both suboptions and subcommands need to reparse for
    # suboptions, so we log again.
    metrics.LogCommandParams(sub_opts=self.sub_opts)
    func()
    return 0
