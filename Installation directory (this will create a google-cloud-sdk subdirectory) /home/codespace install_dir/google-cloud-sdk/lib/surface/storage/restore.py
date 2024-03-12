# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Implementation of Unix-like cat command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import enum

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import stdin_iterator
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.objects import bulk_restore_objects_task
from googlecloudsdk.command_lib.storage.tasks.objects import restore_object_task
from googlecloudsdk.core import log


_BULK_RESTORE_FLAGS = [
    'allow_overwrite',
    'deleted_after_time',
    'deleted_before_time',
]
_SYNCHRONOUS_RESTORE_FLAGS = ['all_versions']


class ExecutionMode(enum.Enum):
  ASYNCHRONOUS = 'Asynchronous'
  SYNCHRONOUS = 'Synchronous'


def _raise_if_invalid_flag_combination(args, execution_mode, invalid_flags):
  """Raises error if invalid combination of flags found in user input.

  Args:
    args (parser_extensions.Namespace): User input object.
    execution_mode (ExecutionMode): Determined by presence of --async flag.
    invalid_flags (list[str]): Flags as `args` attributes.

  Raises:
    error.Error: Flag incompatible with execution mode.
  """
  for invalid_flag in invalid_flags:
    if getattr(args, invalid_flag):
      raise errors.Error(
          '{} execution does not support flag: {}.'
          ' See help text with --help.'.format(
              execution_mode.value, invalid_flag
          )
      )


def _url_iterator(args):
  """Extracts, validates, and yields URLs."""
  for url_string in stdin_iterator.get_urls_iterable(
      args.urls, args.read_paths_from_stdin
  ):
    url = storage_url.storage_url_from_string(url_string)
    # TODO(b/292075826): Remove once bucket restore supported.
    errors_util.raise_error_if_not_cloud_object(args.command_path, url)
    errors_util.raise_error_if_not_gcs(args.command_path, url)
    yield url


def _async_restore_task_iterator(args, user_request_args):
  """Yields non-blocking restore tasks."""
  bucket_to_globs = collections.defaultdict(list)
  for url in _url_iterator(args):
    # TODO(b/292075826): Add exception for buckets once bucket restore
    # is supported
    if not wildcard_iterator.contains_wildcard(url.url_string):
      log.warning(
          'Bulk restores are long operations. For restoring a single'
          ' object, you should probably use a synchronous restore'
          ' without the --async flag. URL without wildcards: {}'.format(url)
      )
    bucket_to_globs[storage_url.CloudUrl(url.scheme, url.bucket_name)].append(
        url.object_name
    )

  for bucket_url, object_globs in bucket_to_globs.items():
    yield bulk_restore_objects_task.BulkRestoreObjectsTask(
        bucket_url,
        object_globs,
        allow_overwrite=args.allow_overwrite,
        deleted_after_time=args.deleted_after_time,
        deleted_before_time=args.deleted_before_time,
        user_request_args=user_request_args,
    )


def _sync_restore_task_iterator(args, fields_scope, user_request_args):
  """Yields blocking restore tasks."""
  last_resource = None
  for url in _url_iterator(args):
    resources = list(
        wildcard_iterator.get_wildcard_iterator(
            url.url_string,
            fields_scope=fields_scope,
            object_state=cloud_api.ObjectState.SOFT_DELETED,
        )
    )
    if not resources:
      raise errors.InvalidUrlError(
          'The following URLs matched no objects:\n-{}'.format(url.url_string)
      )
    for resource in resources:
      if args.all_versions:
        yield restore_object_task.RestoreObjectTask(resource, user_request_args)
      else:
        if (
            last_resource
            and last_resource.storage_url.versionless_url_string
            != resource.storage_url.versionless_url_string
        ):
          yield restore_object_task.RestoreObjectTask(
              last_resource, user_request_args
          )
        last_resource = resource
  if last_resource:
    yield restore_object_task.RestoreObjectTask(
        last_resource, user_request_args
    )


def _restore_task_iterator(args):
  """Yields restore tasks."""
  if args.preserve_acl:
    fields_scope = cloud_api.FieldsScope.FULL
  else:
    fields_scope = cloud_api.FieldsScope.SHORT
  user_request_args = (
      user_request_args_factory.get_user_request_args_from_command_args(
          args, metadata_type=user_request_args_factory.MetadataType.OBJECT
      )
  )
  if args.asyncronous:
    return _async_restore_task_iterator(args, user_request_args)
  return _sync_restore_task_iterator(args, fields_scope, user_request_args)


class Restore(base.Command):
  """Restore one or more soft-deleted objects."""

  # TODO(b/292075826): Update docstring and help once bucket restore supported.
  detailed_help = {
      'DESCRIPTION': """
      The restore command restores soft-deleted objects:

        $ {command} url...

      """,
      'EXAMPLES': """

      Restore latest soft-deleted version of object in a bucket.

        $ {command} gs://bucket/file1.txt

      Restore a specific soft-deleted version of object in a bucket by specifying the generation.

        $ {command} gs://bucket/file1.txt#123

      Restore all soft-deleted versions of object in a bucket.

        $ {command} gs://bucket/file1.txt --all-versions

      Restore several objects in a bucket (with or without generation):

        $ {command} gs://bucket/file1.txt gs://bucket/file2.txt#456

      Restore the latest soft-deleted version of all text objects in a bucket:

        $ {command} gs://bucket/**.txt

      Restore a list of objects read from stdin (with or without generation):

        $ cat list-of-files.txt | {command} --read-paths-from-stdin

      Restore object with its original ACL policy:

        $ {command} gs://bucket/file1.txt --preserve-acl

      Restore all objects in a bucket asynchronously:

        $ {command} gs://bucket/** --async

      Restore all text files in a bucket asynchronously:

        $ {command} gs://bucket/**.txt --async

      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('urls', nargs='*', help='The url of objects to list.')
    flags.add_precondition_flags(parser)
    flags.add_preserve_acl_flag(parser)
    flags.add_read_paths_from_stdin_flag(parser)

    synchronous_restore_flag_group = parser.add_group(
        help='SYNCHRONOUS RESTORE OPTIONS'
    )
    synchronous_restore_flag_group.add_argument(
        '-a',
        '--all-versions',
        action='store_true',
        help=(
            'Restores all versions of soft-deleted objects.'
            '\n\nThis flag is only useful for buckets with [object versioning]'
            ' (https://cloud.google.com/storage/docs/object-versioning)'
            ' enabled. In this case, the latest soft-deleted version will'
            ' become live and the previous generations will become noncurrent.'
            '\n\nIf versioning is disabled, the latest soft-deleted version'
            ' will become live and previous generations will be soft-deleted'
            ' again.'
            '\n\nThis flag disables parallelism to preserve version order.'
        ),
    )

    parser.add_argument(
        '--async',
        # Can't create `async` attribute because "async" is a keyword.
        dest='asyncronous',
        action='store_true',
        help=(
            'Initiates an asynchronous bulk restore operation on the specified'
            ' bucket.'
        ),
    )
    bulk_restore_flag_group = parser.add_group(help='BULK RESTORE OPTIONS')
    bulk_restore_flag_group.add_argument(
        '--allow-overwrite',
        action='store_true',
        help=(
            'If included, live objects will be overwritten. If versioning is'
            ' enabled, this will result in a noncurrent object. If versioning'
            ' is not enabled, this will result in a soft-deleted object.'
        ),
    )
    bulk_restore_flag_group.add_argument(
        '--deleted-after-time',
        type=arg_parsers.Datetime.Parse,
        help=(
            'Restores only the objects that were soft-deleted after this time.'
        ),
    )
    bulk_restore_flag_group.add_argument(
        '--deleted-before-time',
        type=arg_parsers.Datetime.Parse,
        help=(
            'Restores only the objects that were soft-deleted before this time.'
        ),
    )

  def Run(self, args):
    task_status_queue = task_graph_executor.multiprocessing_context.Queue()

    if args.asyncronous:
      _raise_if_invalid_flag_combination(
          args, ExecutionMode.ASYNCHRONOUS, _SYNCHRONOUS_RESTORE_FLAGS
      )
    else:
      _raise_if_invalid_flag_combination(
          args, ExecutionMode.SYNCHRONOUS, _BULK_RESTORE_FLAGS
      )

    self.exit_code = task_executor.execute_tasks(
        task_iterator=_restore_task_iterator(args),
        parallelizable=not args.all_versions,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            increment_type=task_status.IncrementType.INTEGER, manifest_path=None
        ),
    )
