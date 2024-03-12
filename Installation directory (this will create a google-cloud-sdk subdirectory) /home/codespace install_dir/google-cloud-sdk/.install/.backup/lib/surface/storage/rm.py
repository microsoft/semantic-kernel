# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Implementation of rm command for deleting resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import folder_util
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage import rm_command_util
from googlecloudsdk.command_lib.storage import stdin_iterator
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.rm import delete_task_iterator_factory
from googlecloudsdk.core import log


class Rm(base.Command):
  """Delete objects and buckets."""

  detailed_help = {
      'DESCRIPTION':
          """
      Delete objects and buckets.
      """,
      'EXAMPLES':
          """

      The following command deletes a Cloud Storage object named ``my-object''
      from the bucket ``my-bucket'':

        $ {command} gs://my-bucket/my-object

      The following command deletes all objects directly within the directory
      ``my-dir'' but no objects within subdirectories:

        $ {command} gs://my-bucket/my-dir/*

      The following command deletes all objects and subdirectories within the
      directory ``my-dir'':

        $ {command} gs://my-bucket/my-dir/**

      Note that for buckets that contain
      [versioned objects](https://cloud.google.com/storage/docs/object-versioning),
      the above command only affects live versions. Use the `--recursive` flag
      instead to delete all versions.

      The following command deletes all versions of all resources in
      ``my-bucket'' and then deletes the bucket.

        $ {command} --recursive gs://my-bucket/

      The following command deletes all text files in the top-level of
      ``my-bucket'', but not text files in subdirectories:

        $ {command} -recursive gs://my-bucket/*.txt

      The following command deletes one wildcard expression per line passed
      in by stdin:

        $ some_program | {command} -I
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'urls',
        nargs='*',
        help='The URLs of the resources to delete.')
    parser.add_argument(
        '--recursive',
        '-R',
        '-r',
        action='store_true',
        help=(
            'Recursively delete the contents of buckets or directories that'
            ' match the path expression.'
            # TODO(b/301935143): Uncomment the following line:
            # ' By default, this will delete managed folders as well.
            ' If the path is set to a bucket, like'
            " ``gs://bucket'', the bucket is also deleted. This option"
            ' implies the `--all-versions` option. If you want to delete only'
            " live object versions, use the ``**'' wildcard instead."
        ),
    )
    parser.add_argument(
        '--all-versions',
        '-a',
        action='store_true',
        help='Delete all'
        ' [versions](https://cloud.google.com/storage/docs/object-versioning)'
        ' of an object.')

    if cls.ReleaseTrack() is base.ReleaseTrack.ALPHA:
      parser.add_argument(
          '--exclude-managed-folders',
          action='store_true',
          default=False,
          help=(
              'Excludes managed folders from command operations. By default'
              ' gcloud storage includes managed folders in recursive removals.'
          ),
      )

    flags.add_additional_headers_flag(parser)
    flags.add_continue_on_error_flag(parser)
    flags.add_precondition_flags(parser)
    flags.add_read_paths_from_stdin_flag(parser)

  def Run(self, args):
    if args.recursive:
      bucket_setting = name_expansion.BucketSetting.YES
      object_state = cloud_api.ObjectState.LIVE_AND_NONCURRENT
      recursion_setting = name_expansion.RecursionSetting.YES
    else:
      bucket_setting = name_expansion.BucketSetting.NO
      object_state = flags.get_object_state_from_flags(args)
      recursion_setting = name_expansion.RecursionSetting.NO_WITH_WARNING

    should_perform_managed_folder_operations = (
        args.recursive
        # TODO(b/304524534): Replace with args.exclude_managed_folders.
        and not getattr(args, 'exclude_managed_folders', True)
    )

    url_found_match_tracker = collections.OrderedDict()
    name_expansion_iterator = name_expansion.NameExpansionIterator(
        stdin_iterator.get_urls_iterable(args.urls, args.read_paths_from_stdin),
        fields_scope=cloud_api.FieldsScope.SHORT,
        include_buckets=bucket_setting,
        managed_folder_setting=folder_util.ManagedFolderSetting.DO_NOT_LIST,
        object_state=object_state,
        raise_error_for_unmatched_urls=not should_perform_managed_folder_operations,
        recursion_requested=recursion_setting,
        url_found_match_tracker=url_found_match_tracker,
    )

    user_request_args = (
        user_request_args_factory.get_user_request_args_from_command_args(args))
    task_status_queue = task_graph_executor.multiprocessing_context.Queue()
    task_iterator_factory = (
        delete_task_iterator_factory.DeleteTaskIteratorFactory(
            name_expansion_iterator,
            task_status_queue=task_status_queue,
            user_request_args=user_request_args))

    log.status.Print('Removing objects:')
    object_exit_code = task_executor.execute_tasks(
        task_iterator_factory.object_iterator(),
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            increment_type=task_status.IncrementType.INTEGER, manifest_path=None
        ),
        continue_on_error=args.continue_on_error,
    )

    if should_perform_managed_folder_operations:
      managed_folder_expansion_iterator = name_expansion.NameExpansionIterator(
          args.urls,
          managed_folder_setting=folder_util.ManagedFolderSetting.LIST_WITHOUT_OBJECTS,
          raise_error_for_unmatched_urls=True,
          # `rm` defaults to including managed folders, but this will raise a
          # precondition error if the command targets a non-UBLA bucket. These
          # errors should be silenced.
          raise_managed_folder_precondition_errors=False,
          recursion_requested=name_expansion.RecursionSetting.YES,
          url_found_match_tracker=url_found_match_tracker,
      )
      managed_folder_exit_code = rm_command_util.remove_managed_folders(
          args,
          managed_folder_expansion_iterator,
          task_status_queue,
          verbose=True,
      )
    else:
      managed_folder_exit_code = 0

    bucket_iterator = plurality_checkable_iterator.PluralityCheckableIterator(
        task_iterator_factory.bucket_iterator())

    # We perform the is_empty check to avoid printing unneccesary status lines.
    if args.recursive and not bucket_iterator.is_empty():
      log.status.Print('Removing buckets:')
      bucket_exit_code = task_executor.execute_tasks(
          bucket_iterator,
          parallelizable=True,
          task_status_queue=task_status_queue,
          progress_manager_args=task_status.ProgressManagerArgs(
              increment_type=task_status.IncrementType.INTEGER,
              manifest_path=None,
          ),
          continue_on_error=args.continue_on_error,
      )
    else:
      bucket_exit_code = 0

    self.exit_code = max(
        object_exit_code, managed_folder_exit_code, bucket_exit_code
    )
