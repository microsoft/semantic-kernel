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
"""Implementation of Unix-like rm command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import time

from gslib.cloud_api import BucketNotFoundException
from gslib.cloud_api import NotEmptyException
from gslib.cloud_api import NotFoundException
from gslib.cloud_api import ServiceException
from gslib.command import Command
from gslib.command import DecrementFailureCount
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.exception import NO_URLS_MATCHED_PREFIX
from gslib.exception import NO_URLS_MATCHED_TARGET
from gslib.name_expansion import NameExpansionIterator
from gslib.name_expansion import SeekAheadNameExpansionIterator
from gslib.storage_url import StorageUrlFromString
from gslib.thread_message import MetadataMessage
from gslib.utils import constants
from gslib.utils import parallelism_framework_util
from gslib.utils.cloud_api_helper import GetCloudApiInstance
from gslib.utils.retry_util import Retry
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils.system_util import StdinIterator
from gslib.utils.translation_helper import PreconditionsFromHeaders

_PutToQueueWithTimeout = parallelism_framework_util.PutToQueueWithTimeout

_SYNOPSIS = """
  gsutil rm [-f] [-r] url...
  gsutil rm [-f] [-r] -I
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  NOTE: As part of verifying the existence of objects prior to deletion,
  ``gsutil rm`` makes ``GET`` requests to Cloud Storage for object metadata.
  These requests incur `network and operations charges
  <https://cloud.google.com/storage/pricing>`_.

  The gsutil rm command removes objects and/or buckets.
  For example, the following command removes the object ``kitten.png``:

    gsutil rm gs://bucket/kitten.png

  Use the -r option to specify recursive object deletion. For example, the
  following command removes gs://bucket/subdir and all objects and
  subdirectories under it:

    gsutil rm -r gs://bucket/subdir

  When working with versioning-enabled buckets, note that the -r option removes
  all object versions in the subdirectory. To remove only the live version of
  each object in the subdirectory, use the `** wildcard
  <https://cloud.google.com/storage/docs/wildcards>`_.

  The following command removes all versions of all objects in a bucket, and
  then deletes the bucket:

    gsutil rm -r gs://bucket
    
  To remove all objects and their versions from a bucket without deleting the
  bucket, use the ``-a`` option:

    gsutil rm -a gs://bucket/**

  If you have a large number of objects to remove, use the ``gsutil -m`` option,
  which enables multi-threading/multi-processing:

    gsutil -m rm -r gs://my_bucket/subdir

  You can pass a list of URLs (one per line) to remove on stdin instead of as
  command line arguments by using the -I option. This allows you to use gsutil
  in a pipeline to remove objects identified by a program, such as:

    some_program | gsutil -m rm -I

  The contents of stdin can name cloud URLs and wildcards of cloud URLs.

  Note that ``gsutil rm`` refuses to remove files from the local file system.
  For example, this fails:

    gsutil rm *.txt

  WARNING: Object removal cannot be undone. Cloud Storage is designed to give
  developers a high amount of flexibility and control over their data, and
  Google maintains strict controls over the processing and purging of deleted
  data. If you have concerns that your application software or your users may
  at some point erroneously delete or replace data, see
  `Options for controlling data lifecycles
  <https://cloud.google.com/storage/docs/control-data-lifecycles>`_ for ways to
  protect your data from accidental data deletion.


<B>OPTIONS</B>
  -f          Continues silently (without printing error messages) despite
              errors when removing multiple objects. If some of the objects
              could not be removed, gsutil's exit status will be non-zero even
              if this flag is set. Execution will still halt if an inaccessible
              bucket is encountered. This option is implicitly set when running
              "gsutil -m rm ...".

  -I          Causes gsutil to read the list of objects to remove from stdin.
              This allows you to run a program that generates the list of
              objects to remove.

  -R, -r      The -R and -r options are synonymous. Causes bucket or bucket
              subdirectory contents (all objects and subdirectories that it
              contains) to be removed recursively. If used with a bucket-only
              URL (like gs://bucket), after deleting objects and subdirectories
              gsutil deletes the bucket. This option implies the -a option and
              deletes all object versions. If you only want to delete live
              object versions, use the `** wildcard
              <https://cloud.google.com/storage/docs/wildcards>`_
              instead of -r.

  -a          Delete all versions of an object.
""")


def _RemoveExceptionHandler(cls, e):
  """Simple exception handler to allow post-completion status."""
  if not cls.continue_on_error:
    cls.logger.error(str(e))
  # TODO: Use shared state to track missing bucket names when we get a
  # BucketNotFoundException. Then improve bucket removal logic and exception
  # messages.
  if isinstance(e, BucketNotFoundException):
    cls.bucket_not_found_count += 1
    cls.logger.error(str(e))
  else:
    if _ExceptionMatchesBucketToDelete(cls.bucket_strings_to_delete, e):
      DecrementFailureCount()
    else:
      cls.op_failure_count += 1


# pylint: disable=unused-argument
def _RemoveFoldersExceptionHandler(cls, e):
  """When removing folders, we don't mind if none exist."""
  if ((isinstance(e, CommandException) and NO_URLS_MATCHED_PREFIX in e.reason)
      or isinstance(e, NotFoundException)):
    DecrementFailureCount()
  else:
    raise e


def _RemoveFuncWrapper(cls, name_expansion_result, thread_state=None):
  cls.RemoveFunc(name_expansion_result, thread_state=thread_state)


def _ExceptionMatchesBucketToDelete(bucket_strings_to_delete, e):
  """Returns True if the exception matches a bucket slated for deletion.

  A recursive delete call on an empty bucket will raise an exception when
  listing its objects, but if we plan to delete the bucket that shouldn't
  result in a user-visible error.

  Args:
    bucket_strings_to_delete: Buckets slated for recursive deletion.
    e: Exception to check.

  Returns:
    True if the exception was a no-URLs-matched exception and it matched
    one of bucket_strings_to_delete, None otherwise.
  """
  if bucket_strings_to_delete:
    msg = NO_URLS_MATCHED_TARGET % ''
    if msg in str(e):
      parts = str(e).split(msg)
      return len(parts) == 2 and parts[1] in bucket_strings_to_delete


class RmCommand(Command):
  """Implementation of gsutil rm command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'rm',
      command_name_aliases=['del', 'delete', 'remove'],
      usage_synopsis=_SYNOPSIS,
      min_args=0,
      max_args=constants.NO_MAX,
      supported_sub_args='afIrR',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=0,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[CommandArgument.MakeZeroOrMoreCloudURLsArgument()])
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='rm',
      help_name_aliases=['del', 'delete', 'remove'],
      help_type='command_help',
      help_one_line_summary='Remove objects',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  gcloud_storage_map = GcloudStorageMap(
      gcloud_command=['storage', 'rm'],
      flag_map={
          '-r': GcloudStorageFlag('-r'),
          '-R': GcloudStorageFlag('-r'),
          '-a': GcloudStorageFlag('-a'),
          '-I': GcloudStorageFlag('-I'),
          '-f': GcloudStorageFlag('--continue-on-error'),
      },
  )

  def RunCommand(self):
    """Command entry point for the rm command."""
    # self.recursion_requested is initialized in command.py (so it can be
    # checked in parent class for all commands).
    self.continue_on_error = self.parallel_operations
    self.read_args_from_stdin = False
    self.all_versions = False
    if self.sub_opts:
      for o, unused_a in self.sub_opts:
        if o == '-a':
          self.all_versions = True
        elif o == '-f':
          self.continue_on_error = True
        elif o == '-I':
          self.read_args_from_stdin = True
        elif o == '-r' or o == '-R':
          self.recursion_requested = True
          self.all_versions = True

    if self.read_args_from_stdin:
      if self.args:
        raise CommandException('No arguments allowed with the -I flag.')
      url_strs = StdinIterator()
    else:
      if not self.args:
        raise CommandException('The rm command (without -I) expects at '
                               'least one URL.')
      url_strs = self.args

    # Tracks number of object deletes that failed.
    self.op_failure_count = 0

    # Tracks if any buckets were missing.
    self.bucket_not_found_count = 0

    # Tracks buckets that are slated for recursive deletion.
    bucket_urls_to_delete = []
    self.bucket_strings_to_delete = []

    if self.recursion_requested:
      bucket_fields = ['id']
      for url_str in url_strs:
        url = StorageUrlFromString(url_str)
        if url.IsBucket() or url.IsProvider():
          for blr in self.WildcardIterator(url_str).IterBuckets(
              bucket_fields=bucket_fields):
            bucket_urls_to_delete.append(blr.storage_url)
            self.bucket_strings_to_delete.append(url_str)

    self.preconditions = PreconditionsFromHeaders(self.headers or {})

    try:
      # Expand wildcards, dirs, buckets, and bucket subdirs in URLs.
      name_expansion_iterator = NameExpansionIterator(
          self.command_name,
          self.debug,
          self.logger,
          self.gsutil_api,
          url_strs,
          self.recursion_requested,
          project_id=self.project_id,
          all_versions=self.all_versions,
          continue_on_error=self.continue_on_error or self.parallel_operations)

      seek_ahead_iterator = None
      # Cannot seek ahead with stdin args, since we can only iterate them
      # once without buffering in memory.
      if not self.read_args_from_stdin:
        seek_ahead_iterator = SeekAheadNameExpansionIterator(
            self.command_name,
            self.debug,
            self.GetSeekAheadGsutilApi(),
            url_strs,
            self.recursion_requested,
            all_versions=self.all_versions,
            project_id=self.project_id)

      # Perform remove requests in parallel (-m) mode, if requested, using
      # configured number of parallel processes and threads. Otherwise,
      # perform requests with sequential function calls in current process.
      self.Apply(_RemoveFuncWrapper,
                 name_expansion_iterator,
                 _RemoveExceptionHandler,
                 fail_on_error=(not self.continue_on_error),
                 shared_attrs=['op_failure_count', 'bucket_not_found_count'],
                 seek_ahead_iterator=seek_ahead_iterator)

    # Assuming the bucket has versioning enabled, url's that don't map to
    # objects should throw an error even with all_versions, since the prior
    # round of deletes only sends objects to a history table.
    # This assumption that rm -a is only called for versioned buckets should be
    # corrected, but the fix is non-trivial.
    except CommandException as e:
      # Don't raise if there are buckets to delete -- it's valid to say:
      #   gsutil rm -r gs://some_bucket
      # if the bucket is empty.
      if _ExceptionMatchesBucketToDelete(self.bucket_strings_to_delete, e):
        DecrementFailureCount()
      else:
        raise
    except ServiceException as e:
      if not self.continue_on_error:
        raise

    if self.bucket_not_found_count:
      raise CommandException('Encountered non-existent bucket during listing')

    if self.op_failure_count and not self.continue_on_error:
      raise CommandException('Some files could not be removed.')

    # If this was a gsutil rm -r command covering any bucket subdirs,
    # remove any dir_$folder$ objects (which are created by various web UI
    # tools to simulate folders).
    if self.recursion_requested:
      folder_object_wildcards = []
      for url_str in url_strs:
        url = StorageUrlFromString(url_str)
        if url.IsObject():
          folder_object_wildcards.append(url_str.rstrip('*') + '*_$folder$')
      if folder_object_wildcards:
        self.continue_on_error = True
        try:
          name_expansion_iterator = NameExpansionIterator(
              self.command_name,
              self.debug,
              self.logger,
              self.gsutil_api,
              folder_object_wildcards,
              self.recursion_requested,
              project_id=self.project_id,
              all_versions=self.all_versions)
          # When we're removing folder objects, always continue on error
          self.Apply(_RemoveFuncWrapper,
                     name_expansion_iterator,
                     _RemoveFoldersExceptionHandler,
                     fail_on_error=False)
        except CommandException as e:
          # Ignore exception from name expansion due to an absent folder file.
          if not e.reason.startswith(NO_URLS_MATCHED_PREFIX):
            raise

    # Now that all data has been deleted, delete any bucket URLs.
    for url in bucket_urls_to_delete:
      self.logger.info('Removing %s...', url)

      @Retry(NotEmptyException, tries=3, timeout_secs=1)
      def BucketDeleteWithRetry():
        self.gsutil_api.DeleteBucket(url.bucket_name, provider=url.scheme)

      BucketDeleteWithRetry()

    if self.op_failure_count:
      plural_str = 's' if self.op_failure_count else ''
      raise CommandException('%d file%s/object%s could not be removed.' %
                             (self.op_failure_count, plural_str, plural_str))

    return 0

  def RemoveFunc(self, name_expansion_result, thread_state=None):
    gsutil_api = GetCloudApiInstance(self, thread_state=thread_state)

    exp_src_url = name_expansion_result.expanded_storage_url
    self.logger.info('Removing %s...', exp_src_url)
    try:
      gsutil_api.DeleteObject(exp_src_url.bucket_name,
                              exp_src_url.object_name,
                              preconditions=self.preconditions,
                              generation=exp_src_url.generation,
                              provider=exp_src_url.scheme)
    except NotFoundException as e:
      # DeleteObject will sometimes return a 504 (DEADLINE_EXCEEDED) when
      # the operation was in fact successful. When a retry is attempted in
      # these cases, it will fail with a (harmless) 404. The 404 is harmless
      # since it really just means the file was already deleted, which is
      # what we want anyway. Here we simply downgrade the message to info
      # rather than error and correct the command-level failure total.
      self.logger.info('Cannot find %s', exp_src_url)
      DecrementFailureCount()
    _PutToQueueWithTimeout(gsutil_api.status_queue,
                           MetadataMessage(message_time=time.time()))
