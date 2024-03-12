# -*- coding: utf-8 -*-
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Impl. of default bucket storage class command for Google Cloud Storage."""

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
from gslib.utils.text_util import NormalizeStorageClass
from gslib.utils import shim_util

_SET_SYNOPSIS = """
  gsutil defstorageclass set <storage-class> gs://<bucket_name>...
"""

_GET_SYNOPSIS = """
  gsutil defstorageclass get gs://<bucket_name>...
"""

_SYNOPSIS = _SET_SYNOPSIS + _GET_SYNOPSIS.lstrip('\n')

_SET_DESCRIPTION = """
<B>SET</B>
  The "defstorageclass set" command sets the default
  `storage class <https://cloud.google.com/storage/docs/storage-classes>`_ for
  the specified bucket(s). If you specify a default storage class for a certain
  bucket, Google Cloud Storage applies the default storage class to all new
  objects uploaded to that bucket, except when the storage class is overridden
  by individual upload requests.

  Setting a default storage class on a bucket provides a convenient way to
  ensure newly uploaded objects have a specific storage class. If you don't set
  the bucket's default storage class, it will default to Standard.
"""

_GET_DESCRIPTION = """
<B>GET</B>
  Gets the default storage class for a bucket.
"""

_DESCRIPTION = """
  The defstorageclass command has two sub-commands:
""" + '\n'.join([_SET_DESCRIPTION + _GET_DESCRIPTION])

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)

_get_help_text = CreateHelpText(_GET_SYNOPSIS, _GET_DESCRIPTION)
_set_help_text = CreateHelpText(_SET_SYNOPSIS, _SET_DESCRIPTION)

# The url_string for buckets ends with a slash.
# Substitute the last slash with a colon.
_GCLOUD_FORMAT_STRING = ('--format=value[separator=\": \"](name.sub("' +
                         shim_util.get_format_flag_caret() + '", "gs://"),'
                         'storageClass)')
SHIM_GET_COMMAND_MAP = GcloudStorageMap(
    # Using a list because a string gets splitted up on space and the
    # format string below has a space.
    gcloud_command=[
        'storage', 'buckets', 'list', _GCLOUD_FORMAT_STRING, '--raw'
    ],
    flag_map={},
)
SHIM_SET_COMMAND_MAP = GcloudStorageMap(
    gcloud_command=['storage', 'buckets', 'update', '--default-storage-class'],
    flag_map={},
)


class DefStorageClassCommand(Command):
  """Implementation of gsutil defstorageclass command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'defstorageclass',
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
              # FreeTextArgument allows for using storage class abbreviations.
              CommandArgument.MakeFreeTextArgument(),
              CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument(),
          ],
          'get': [CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument(),],
      },
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='defstorageclass',
      help_name_aliases=['defaultstorageclass'],
      help_type='command_help',
      help_one_line_summary='Get or set the default storage class on buckets',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={
          'get': _get_help_text,
          'set': _set_help_text,
      },
  )

  gcloud_storage_map = GcloudStorageMap(
      gcloud_command={
          'get': SHIM_GET_COMMAND_MAP,
          'set': SHIM_SET_COMMAND_MAP,
      },
      flag_map={},
  )

  def _CheckIsGsUrl(self, url_str):
    if not url_str.startswith('gs://'):
      raise CommandException(
          '"%s" does not support the URL "%s". Did you mean to use a gs:// '
          'URL?' % (self.command_name, url_str))

  def _CalculateUrlsStartArg(self):
    if not self.args:
      self.RaiseWrongNumberOfArgumentsException()
    if self.args[0].lower() == 'set':
      return 2
    else:
      return 1

  def _SetDefStorageClass(self):
    """Sets the default storage class for a bucket."""
    # At this point, "set" has been popped off the front of self.args.
    normalized_storage_class = NormalizeStorageClass(self.args[0])
    url_args = self.args[1:]
    if not url_args:
      self.RaiseWrongNumberOfArgumentsException()

    some_matched = False
    for url_str in url_args:
      self._CheckIsGsUrl(url_str)
      # Throws a CommandException if the argument is not a bucket.
      bucket_iter = self.GetBucketUrlIterFromArg(url_str, bucket_fields=['id'])
      for blr in bucket_iter:
        some_matched = True
        bucket_metadata = apitools_messages.Bucket()
        self.logger.info('Setting default storage class to "%s" for bucket %s' %
                         (normalized_storage_class, blr.url_string.rstrip('/')))
        bucket_metadata.storageClass = normalized_storage_class
        self.gsutil_api.PatchBucket(blr.storage_url.bucket_name,
                                    bucket_metadata,
                                    provider=blr.storage_url.scheme,
                                    fields=['id'])
    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(url_args))

  def _GetDefStorageClass(self):
    """Gets the default storage class for a bucket."""
    # At this point, "get" has been popped off the front of self.args.
    url_args = self.args
    some_matched = False
    for url_str in url_args:
      self._CheckIsGsUrl(url_str)
      bucket_iter = self.GetBucketUrlIterFromArg(url_str,
                                                 bucket_fields=['storageClass'])
      for blr in bucket_iter:
        some_matched = True
        print('%s: %s' %
              (blr.url_string.rstrip('/'), blr.root_object.storageClass))
    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(url_args))

  def RunCommand(self):
    """Command entry point for the defstorageclass command."""
    action_subcommand = self.args.pop(0)
    subcommand_args = [action_subcommand]
    if action_subcommand == 'get':
      func = self._GetDefStorageClass
    elif action_subcommand == 'set':
      func = self._SetDefStorageClass
      normalized_storage_class = NormalizeStorageClass(self.args[0])
      subcommand_args.append(normalized_storage_class)
    else:
      raise CommandException(
          ('Invalid subcommand "%s" for the %s command.\n'
           'See "gsutil help %s".') %
          (action_subcommand, self.command_name, self.command_name))
    metrics.LogCommandParams(subcommands=subcommand_args)
    func()
    return 0
