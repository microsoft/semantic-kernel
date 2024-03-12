# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Implementation of Retention Policy configuration command for buckets."""

from __future__ import absolute_import

import time

from apitools.base.py import encoding
from gslib import metrics
from gslib.cloud_api import AccessDeniedException
from gslib.cloud_api import Preconditions
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.exception import NO_URLS_MATCHED_TARGET
from gslib.help_provider import CreateHelpText
from gslib.name_expansion import NameExpansionIterator
from gslib.name_expansion import SeekAheadNameExpansionIterator
from gslib.storage_url import StorageUrlFromString
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.thread_message import MetadataMessage
from gslib.utils.cloud_api_helper import GetCloudApiInstance
from gslib.utils.constants import NO_MAX
from gslib.utils.parallelism_framework_util import PutToQueueWithTimeout
from gslib.utils.retention_util import ConfirmLockRequest
from gslib.utils.retention_util import ReleaseEventHoldFuncWrapper
from gslib.utils.retention_util import ReleaseTempHoldFuncWrapper
from gslib.utils.retention_util import RetentionInSeconds
from gslib.utils.retention_util import RetentionPolicyToString
from gslib.utils.retention_util import SetEventHoldFuncWrapper
from gslib.utils.retention_util import SetTempHoldFuncWrapper
from gslib.utils.retention_util import UpdateObjectMetadataExceptionHandler
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils.translation_helper import PreconditionsFromHeaders

_SET_SYNOPSIS = """
  gsutil retention set <retention_period> gs://<bucket_name>...
"""

_CLEAR_SYNOPSIS = """
  gsutil retention clear gs://<bucket_name>...
"""

_GET_SYNOPSIS = """
  gsutil retention get gs://<bucket_name>...
"""

_LOCK_SYNOPSIS = """
  gsutil retention lock gs://<bucket_name>...
"""

_EVENT_DEFAULT_SYNOPSIS = """
  gsutil retention event-default (set|release) gs://<bucket_name>...
"""

_EVENT_SYNOPSIS = """
  gsutil retention event (set|release) gs://<bucket_name>/<object_name>...
"""

_TEMP_SYNOPSIS = """
  gsutil retention temp (set|release) gs://<bucket_name>/<object_name>...
"""

_SET_DESCRIPTION = """
<B>SET</B>
  You can configure a data retention policy for a Cloud Storage bucket that
  governs how long objects in the bucket must be retained. You can also lock the
  data retention policy, permanently preventing the policy from being reduced or
  removed. For more information, see `Retention policies and Bucket Lock
  <https://cloud.google.com/storage/docs/bucket-lock>`_.

  The ``gsutil retention set`` command allows you to set or update the
  retention policy on one or more buckets.

  To remove an unlocked retention policy from one or more
  buckets, use the ``gsutil retention clear`` command.

  The ``set`` sub-command can set a retention policy with the following formats:

<B>SET FORMATS</B>
  Formats for the ``set`` subcommand include:

  <number>s
      Specifies retention period of <number> seconds for objects in this bucket.

  <number>d
      Specifies retention period of <number> days for objects in this bucket.

  <number>m
      Specifies retention period of <number> months for objects in this bucket.

  <number>y
      Specifies retention period of <number> years for objects in this bucket.

  GCS JSON API accepts retention periods as number of seconds. Durations provided
  in terms of days, months or years are converted to their rough equivalent
  values in seconds, using the following conversions:

  - A month is considered to be 31 days or 2,678,400 seconds.
  - A year is considered to be 365.25 days or 31,557,600 seconds.

  Retention periods must be greater than 0 and less than 100 years.
  Retention durations must be in only one form (seconds, days, months,
  or years), and not a combination of them.

  Note that while it is possible to specify retention durations
  shorter than a day (using seconds), enforcement of such retention periods is not
  guaranteed. Such durations may only be used for testing purposes.

<B>EXAMPLES</B>
  Setting a retention policy with a duration of 1 year on a bucket:

    gsutil retention set 1y gs://my-bucket

  Setting a retention policy with a duration of 36 months on a bucket:

    gsutil retention set 36m gs://some-bucket

  You can also provide a precondition on a bucket's metageneration in order to
  avoid potential race conditions. You can use gsutil's '-h' option to specify
  preconditions. For example, the following specifies a precondition that checks
  a bucket's metageneration before setting the retention policy on the bucket:

    gsutil -h "x-goog-if-metageneration-match: 1" \\
      retention set 1y gs://my-bucket
"""

_CLEAR_DESCRIPTION = """
<B>CLEAR</B>
  The ``gsutil retention clear`` command removes an unlocked retention policy
  from one or more buckets. You cannot remove or reduce the duration of a locked
  retention policy.

<B>EXAMPLES</B>
  Clearing an unlocked retention policy from a bucket:

    gsutil retention clear gs://my-bucket
"""

_GET_DESCRIPTION = """
<B>GET</B>
  The ``gsutil retention get`` command retrieves the retention policy for a given
  bucket and displays a human-readable representation of the configuration.
"""

_LOCK_DESCRIPTION = """
<B>LOCK</B>
  The ``gsutil retention lock`` command PERMANENTLY locks an unlocked
  retention policy on one or more buckets.

  CAUTION: A locked retention policy cannot be removed from a bucket or reduced
  in duration. Once locked, deleting the bucket is the only way to "remove" a
  retention policy.
"""

_EVENT_DEFAULT_DESCRIPTION = """
<B>EVENT-DEFAULT</B>
  The ``gsutil retention event-default`` command sets the default value for an
  event-based hold on one or more buckets.

  By setting the default event-based hold on a bucket, newly-created objects
  inherit that value as their event-based hold (it is not applied
  retroactively).

<B>EXAMPLES</B>
  Setting the default event-based hold on a bucket:

    gsutil retention event-default set gs://my-bucket

  Releasing the default event-based hold on a bucket:

    gsutil retention event-default release gs://my-bucket

  You can also provide a precondition on a bucket's metageneration in order to
  avoid potential race conditions. You can use gsutil's '-h' option to specify
  preconditions. For example, the following specifies a precondition that checks
  a bucket's metageneration before setting the default event-based hold on the bucket:

    gsutil -h "x-goog-if-metageneration-match: 1" \\
      retention event-default set gs://my-bucket
"""

_EVENT_DESCRIPTION = """
<B>EVENT</B>
  The ``gsutil retention event`` command enables or disables an event-based
  hold on an object.

<B>EXAMPLES</B>
  Setting the event-based hold on an object:

    gsutil retention event set gs://my-bucket/my-object

  Releasing the event-based hold on an object:

    gsutil retention event release gs://my-bucket/my-object

  You can also provide a precondition on an object's metageneration in order to
  avoid potential race conditions. You can use gsutil's '-h' option to specify
  preconditions. For example, the following specifies a precondition that checks
  an object's metageneration before setting the event-based hold on the object:

    gsutil -h "x-goog-if-metageneration-match: 1" \\
      retention event set gs://my-bucket/my-object

  If you want to set or release an event-based hold on a large number of objects, then
  you might want to use the top-level '-m' option to perform a parallel update.
  For example, the following command sets an event-based hold on objects ending
  with .jpg in parallel, in the root folder:

      gsutil -m retention event set gs://my-bucket/*.jpg
"""

_TEMP_DESCRIPTION = """
<B>TEMP</B>
  The ``gsutil retention temp`` command enables or disables a temporary hold
  on an object.

<B>EXAMPLES</B>
  Setting the temporary hold on an object:

    gsutil retention temp set gs://my-bucket/my-object

  Releasing the temporary hold on an object:

    gsutil retention temp release gs://my-bucket/my-object

  You can also provide a precondition on an object's metageneration in order to
  avoid potential race conditions. You can use gsutil's '-h' option to specify
  preconditions. For example, the following specifies a precondition that checks
  an object's metageneration before setting the temporary hold on the object:

    gsutil -h "x-goog-if-metageneration-match: 1" \\
      retention temp set gs://my-bucket/my-object

  If you want to set or release a temporary hold on a large number of objects, then
  you might want to use the top-level '-m' option to perform a parallel update.
  For example, the following command sets a temporary hold on objects ending
  with .jpg in parallel, in the root folder:

    gsutil -m retention temp set gs://bucket/*.jpg
"""

_SYNOPSIS = (_SET_SYNOPSIS + _CLEAR_SYNOPSIS + _GET_SYNOPSIS + _LOCK_SYNOPSIS +
             _EVENT_DEFAULT_SYNOPSIS + _EVENT_SYNOPSIS + _TEMP_SYNOPSIS)

_DESCRIPTION = (_SET_DESCRIPTION + _CLEAR_DESCRIPTION + _GET_DESCRIPTION +
                _LOCK_DESCRIPTION + _EVENT_DEFAULT_DESCRIPTION +
                _EVENT_DESCRIPTION + _TEMP_DESCRIPTION)

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)

_set_help_text = CreateHelpText(_SET_SYNOPSIS, _SET_DESCRIPTION)
_clear_help_text = CreateHelpText(_CLEAR_SYNOPSIS, _CLEAR_DESCRIPTION)
_get_help_text = CreateHelpText(_GET_SYNOPSIS, _GET_DESCRIPTION)
_lock_help_text = CreateHelpText(_LOCK_SYNOPSIS, _LOCK_DESCRIPTION)
_event_default_help_text = CreateHelpText(_EVENT_DEFAULT_SYNOPSIS,
                                          _EVENT_DEFAULT_DESCRIPTION)
_event_help_text = CreateHelpText(_EVENT_SYNOPSIS, _EVENT_DESCRIPTION)
_temp_help_text = CreateHelpText(_TEMP_SYNOPSIS, _TEMP_DESCRIPTION)


class RetentionCommand(Command):
  """Implementation of gsutil retention command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'retention',
      command_name_aliases=[],
      usage_synopsis=_SYNOPSIS,
      min_args=2,
      max_args=NO_MAX,
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=1,
      gs_api_support=[ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments={
          'set': [CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument()],
          'clear': [CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument()],
          'get': [CommandArgument.MakeNCloudBucketURLsArgument(1)],
          'lock': [CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument()],
          'event-default': {
              'set': [CommandArgument.MakeZeroOrMoreCloudURLsArgument()],
              'release': [CommandArgument.MakeZeroOrMoreCloudURLsArgument()]
          },
          'event': {
              'set': [CommandArgument.MakeZeroOrMoreCloudURLsArgument()],
              'release': [CommandArgument.MakeZeroOrMoreCloudURLsArgument()]
          },
          'temp': {
              'set': [CommandArgument.MakeZeroOrMoreCloudURLsArgument()],
              'release': [CommandArgument.MakeZeroOrMoreCloudURLsArgument()]
          },
      })

  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='retention',
      help_name_aliases=[],
      help_type='command_help',
      help_one_line_summary=(
          'Provides utilities to interact with Retention Policy feature.'),
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={
          'get': _get_help_text,
          'set': _set_help_text,
          'clear': _clear_help_text,
          'lock': _lock_help_text,
          'event-default': _event_default_help_text,
          'event': _event_help_text,
          'temp': _temp_help_text
      },
  )

  def get_gcloud_storage_args(self):
    if self.args[0] == 'set':
      gcloud_storage_map = GcloudStorageMap(
          gcloud_command={
              'set':
                  GcloudStorageMap(
                      gcloud_command=[
                          'storage', 'buckets', 'update',
                          '--retention-period={}s'.format(
                              RetentionInSeconds(self.args[1]))
                      ] + self.args[2:],  # Adds target bucket URLs.
                      flag_map={}),
          },
          flag_map={})
      # Don't trigger unneeded translation now that complete command is above.
      self.args = self.args[:1]
    else:
      gcloud_storage_map = GcloudStorageMap(
          gcloud_command={
              'clear':
                  GcloudStorageMap(
                      gcloud_command=[
                          'storage', 'buckets', 'update',
                          '--clear-retention-period'
                      ],
                      flag_map={},
                  ),
              'event':
                  GcloudStorageMap(
                      gcloud_command={
                          'set':
                              GcloudStorageMap(
                                  gcloud_command=[
                                      'storage', 'objects', 'update',
                                      '--event-based-hold'
                                  ],
                                  flag_map={},
                              ),
                          'release':
                              GcloudStorageMap(
                                  gcloud_command=[
                                      'storage', 'objects', 'update',
                                      '--no-event-based-hold'
                                  ],
                                  flag_map={},
                              ),
                      },
                      flag_map={},
                  ),
              'event-default':
                  GcloudStorageMap(
                      gcloud_command={
                          'set':
                              GcloudStorageMap(
                                  gcloud_command=[
                                      'storage', 'buckets', 'update',
                                      '--default-event-based-hold'
                                  ],
                                  flag_map={},
                              ),
                          'release':
                              GcloudStorageMap(
                                  gcloud_command=[
                                      'storage', 'buckets', 'update',
                                      '--no-default-event-based-hold'
                                  ],
                                  flag_map={},
                              ),
                      },
                      flag_map={},
                  ),
              'get':
                  GcloudStorageMap(gcloud_command=[
                      'storage', 'buckets', 'describe',
                      '--format=yaml(retentionPolicy)', '--raw'
                  ],
                                   flag_map={}),
              'lock':
                  GcloudStorageMap(
                      gcloud_command=[
                          'storage', 'buckets', 'update',
                          '--lock-retention-period'
                      ],
                      flag_map={},
                  ),
              'temp':
                  GcloudStorageMap(
                      gcloud_command={
                          'set':
                              GcloudStorageMap(
                                  gcloud_command=[
                                      'storage', 'objects', 'update',
                                      '--temporary-hold'
                                  ],
                                  flag_map={},
                              ),
                          'release':
                              GcloudStorageMap(
                                  gcloud_command=[
                                      'storage', 'objects', 'update',
                                      '--no-temporary-hold'
                                  ],
                                  flag_map={},
                              ),
                      },
                      flag_map={},
                  ),
          },
          flag_map={},
      )
    return super().get_gcloud_storage_args(gcloud_storage_map)

  def RunCommand(self):
    """Command entry point for the retention command."""
    # If the only credential type the user supplies in their boto file is HMAC,
    # GetApiSelector logic will force us to use the XML API, which bucket lock
    # does not support at the moment.
    if self.gsutil_api.GetApiSelector('gs') != ApiSelector.JSON:
      raise CommandException(('The {} command can only be used with the GCS '
                              'JSON API. If you have only supplied hmac '
                              'credentials in your boto file, please instead '
                              'supply a credential type that can be used with '
                              'the JSON API.').format(self.command_name))

    self.preconditions = PreconditionsFromHeaders(self.headers)

    action_subcommand = self.args.pop(0)
    self.ParseSubOpts(check_args=True)
    if action_subcommand == 'set':
      func = self._SetRetention
    elif action_subcommand == 'clear':
      func = self._ClearRetention
    elif action_subcommand == 'get':
      func = self._GetRetention
    elif action_subcommand == 'lock':
      func = self._LockRetention
    elif action_subcommand == 'event-default':
      func = self._DefaultEventHold
    elif action_subcommand == 'event':
      func = self._EventHold
    elif action_subcommand == 'temp':
      func = self._TempHold
    else:
      raise CommandException(
          ('Invalid subcommand "{}" for the {} command.\n'
           'See "gsutil help retention".').format(action_subcommand,
                                                  self.command_name))

    # Commands with both suboptions and subcommands need to reparse for
    # suboptions, so we log again.
    metrics.LogCommandParams(subcommands=[action_subcommand],
                             sub_opts=self.sub_opts)
    return func()

  def BucketUpdateFunc(self, url_args, bucket_metadata_update, fields,
                       log_msg_template):
    preconditions = Preconditions(
        meta_gen_match=self.preconditions.meta_gen_match)

    # Iterate over URLs, expanding wildcards and setting the new bucket metadata
    # on each bucket.
    some_matched = False
    for url_str in url_args:
      bucket_iter = self.GetBucketUrlIterFromArg(url_str, bucket_fields=['id'])
      for blr in bucket_iter:
        url = blr.storage_url
        some_matched = True
        self.logger.info(log_msg_template, blr)
        self.gsutil_api.PatchBucket(url.bucket_name,
                                    bucket_metadata_update,
                                    preconditions=preconditions,
                                    provider=url.scheme,
                                    fields=fields)
    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(url_args))

  def ObjectUpdateMetadataFunc(self,
                               patch_obj_metadata,
                               log_template,
                               name_expansion_result,
                               thread_state=None):
    """Updates metadata on an object using PatchObjectMetadata.

    Args:
      patch_obj_metadata: Metadata changes that should be applied to the
                          existing object.
      log_template: The log template that should be printed for each object.
      name_expansion_result: NameExpansionResult describing target object.
      thread_state: gsutil Cloud API instance to use for the operation.
    """
    gsutil_api = GetCloudApiInstance(self, thread_state=thread_state)

    exp_src_url = name_expansion_result.expanded_storage_url
    self.logger.info(log_template, exp_src_url)

    cloud_obj_metadata = encoding.JsonToMessage(
        apitools_messages.Object, name_expansion_result.expanded_result)

    preconditions = Preconditions(
        gen_match=self.preconditions.gen_match,
        meta_gen_match=self.preconditions.meta_gen_match)
    if preconditions.gen_match is None:
      preconditions.gen_match = cloud_obj_metadata.generation
    if preconditions.meta_gen_match is None:
      preconditions.meta_gen_match = cloud_obj_metadata.metageneration

    gsutil_api.PatchObjectMetadata(exp_src_url.bucket_name,
                                   exp_src_url.object_name,
                                   patch_obj_metadata,
                                   generation=exp_src_url.generation,
                                   preconditions=preconditions,
                                   provider=exp_src_url.scheme,
                                   fields=['id'])
    PutToQueueWithTimeout(gsutil_api.status_queue,
                          MetadataMessage(message_time=time.time()))

  def _GetObjectNameExpansionIterator(self, url_args):
    return NameExpansionIterator(
        self.command_name,
        self.debug,
        self.logger,
        self.gsutil_api,
        url_args,
        self.recursion_requested,
        all_versions=self.all_versions,
        continue_on_error=self.parallel_operations,
        bucket_listing_fields=['generation', 'metageneration'])

  def _GetSeekAheadNameExpansionIterator(self, url_args):
    return SeekAheadNameExpansionIterator(self.command_name,
                                          self.debug,
                                          self.GetSeekAheadGsutilApi(),
                                          url_args,
                                          self.recursion_requested,
                                          all_versions=self.all_versions,
                                          project_id=self.project_id)

  def _SetRetention(self):
    """Set retention retention_period on one or more buckets."""

    seconds = RetentionInSeconds(self.args[0])
    retention_policy = (apitools_messages.Bucket.RetentionPolicyValue(
        retentionPeriod=seconds))

    log_msg_template = 'Setting Retention Policy on %s...'
    bucket_metadata_update = apitools_messages.Bucket(
        retentionPolicy=retention_policy)
    url_args = self.args[1:]
    self.BucketUpdateFunc(url_args,
                          bucket_metadata_update,
                          fields=['id', 'retentionPolicy'],
                          log_msg_template=log_msg_template)
    return 0

  def _ClearRetention(self):
    """Clear retention retention_period on one or more buckets."""
    retention_policy = (apitools_messages.Bucket.RetentionPolicyValue(
        retentionPeriod=None))
    log_msg_template = 'Clearing Retention Policy on %s...'
    bucket_metadata_update = apitools_messages.Bucket(
        retentionPolicy=retention_policy)
    url_args = self.args
    self.BucketUpdateFunc(url_args,
                          bucket_metadata_update,
                          fields=['id', 'retentionPolicy'],
                          log_msg_template=log_msg_template)
    return 0

  def _GetRetention(self):
    """Get Retention Policy for a single bucket."""
    bucket_url, bucket_metadata = self.GetSingleBucketUrlFromArg(
        self.args[0], bucket_fields=['retentionPolicy'])
    print(RetentionPolicyToString(bucket_metadata.retentionPolicy, bucket_url))
    return 0

  def _LockRetention(self):
    """Lock Retention Policy on one or more buckets."""
    url_args = self.args
    # Iterate over URLs, expanding wildcards and setting the Retention Policy
    # configuration on each.
    some_matched = False
    for url_str in url_args:
      bucket_iter = self.GetBucketUrlIterFromArg(url_str, bucket_fields=['id'])
      for blr in bucket_iter:
        url = blr.storage_url
        some_matched = True
        # Get bucket metadata to provide a precondition.
        bucket_metadata = self.gsutil_api.GetBucket(
            url.bucket_name,
            provider=url.scheme,
            fields=['id', 'metageneration', 'retentionPolicy'])
        if (not (bucket_metadata.retentionPolicy and
                 bucket_metadata.retentionPolicy.retentionPeriod)):
          # TODO: implement '-c' flag to continue_on_error
          raise CommandException(
              'Bucket "{}" does not have an Unlocked Retention Policy.'.format(
                  url.bucket_name))
        elif bucket_metadata.retentionPolicy.isLocked is True:
          self.logger.error('Retention Policy on "%s" is already locked.', blr)
        elif ConfirmLockRequest(url.bucket_name,
                                bucket_metadata.retentionPolicy):
          self.logger.info('Locking Retention Policy on %s...', blr)
          self.gsutil_api.LockRetentionPolicy(url.bucket_name,
                                              bucket_metadata.metageneration,
                                              provider=url.scheme)
        else:
          self.logger.error(
              '  Abort Locking Retention Policy on {}'.format(blr))
    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(url_args))
    return 0

  def _DefaultEventHold(self):
    """Sets default value for Event-Based Hold on one or more buckets."""
    hold = None
    if self.args:
      if self.args[0].lower() == 'set':
        hold = True
      elif self.args[0].lower() == 'release':
        hold = False
      else:
        raise CommandException(
            ('Invalid subcommand "{}" for the "retention event-default"'
             ' command.\nSee "gsutil help retention event".').format(
                 self.sub_opts))

    verb = 'Setting' if hold else 'Releasing'
    log_msg_template = '{} default Event-Based Hold on %s...'.format(verb)
    bucket_metadata_update = apitools_messages.Bucket(
        defaultEventBasedHold=hold)
    url_args = self.args[1:]
    self.BucketUpdateFunc(url_args,
                          bucket_metadata_update,
                          fields=['id', 'defaultEventBasedHold'],
                          log_msg_template=log_msg_template)
    return 0

  def _EventHold(self):
    """Sets or unsets Event-Based Hold on one or more objects."""
    sub_command_name = 'event'
    sub_command_full_name = 'Event-Based'
    hold = self._ProcessHoldArgs(sub_command_name)
    url_args = self.args[1:]
    obj_metadata_update_wrapper = (SetEventHoldFuncWrapper
                                   if hold else ReleaseEventHoldFuncWrapper)
    self._SetHold(obj_metadata_update_wrapper, url_args, sub_command_full_name)
    return 0

  def _TempHold(self):
    """Sets or unsets Temporary Hold on one or more objects."""
    sub_command_name = 'temp'
    sub_command_full_name = 'Temporary'
    hold = self._ProcessHoldArgs(sub_command_name)
    url_args = self.args[1:]
    obj_metadata_update_wrapper = (SetTempHoldFuncWrapper
                                   if hold else ReleaseTempHoldFuncWrapper)
    self._SetHold(obj_metadata_update_wrapper, url_args, sub_command_full_name)
    return 0

  def _ProcessHoldArgs(self, sub_command_name):
    """Processes command args for Temporary and Event-Based Hold sub-command.

    Args:
      sub_command_name: The name of the subcommand: "temp" / "event"

    Returns:
      Returns a boolean value indicating whether to set (True) or
      release (False)the Hold.
    """
    hold = None
    if self.args[0].lower() == 'set':
      hold = True
    elif self.args[0].lower() == 'release':
      hold = False
    else:
      raise CommandException(
          ('Invalid subcommand "{}" for the "retention {}" command.\n'
           'See "gsutil help retention {}".').format(self.args[0],
                                                     sub_command_name,
                                                     sub_command_name))
    return hold

  def _SetHold(self, obj_metadata_update_wrapper, url_args,
               sub_command_full_name):
    """Common logic to set or unset Event-Based/Temporary Hold on objects.

    Args:
      obj_metadata_update_wrapper: The function for updating related fields in
                                   Object metadata.
      url_args: List of object URIs.
      sub_command_full_name: The full name for sub-command:
                             "Temporary" / "Event-Based"
    """
    if len(url_args) == 1 and not self.recursion_requested:
      url = StorageUrlFromString(url_args[0])
      if not (url.IsCloudUrl() and url.IsObject()):
        raise CommandException('URL ({}) must name an object'.format(
            url_args[0]))

    name_expansion_iterator = self._GetObjectNameExpansionIterator(url_args)
    seek_ahead_iterator = self._GetSeekAheadNameExpansionIterator(url_args)

    # Used to track if any objects' metadata failed to be set.
    self.everything_set_okay = True

    try:
      # TODO: implement '-c' flag to continue_on_error

      # Perform requests in parallel (-m) mode, if requested, using
      # configured number of parallel processes and threads. Otherwise,
      # perform requests with sequential function calls in current process.
      self.Apply(obj_metadata_update_wrapper,
                 name_expansion_iterator,
                 UpdateObjectMetadataExceptionHandler,
                 fail_on_error=True,
                 seek_ahead_iterator=seek_ahead_iterator)

    except AccessDeniedException as e:
      if e.status == 403:
        self._WarnServiceAccounts()
      raise

    if not self.everything_set_okay:
      raise CommandException(
          '{} Hold for some objects could not be set.'.format(
              sub_command_full_name))
