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
"""Implementation of rsync command for Cloud Storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import cp_command_util
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import rsync_command_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage.tasks import get_sorted_list_file_task
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status


def _get_list_tasks_and_cleanup_paths(
    args,
    source_container,
    destination_container,
):
  """Generates tasks for creating source/destination inventories.

  Args:
    args (parser_extensions.Namespace): Command line arguments.
    source_container (resource_reference.Resource): Location to find source
      resources.
    destination_container (resource_reference.Resource): Location for
      destination resources.

  Returns:
    A tuple (list_tasks, cleanup_paths).
      list_tasks (List[task.Task]): The tasks to run to create inventories.
      cleanup_paths (List[str]): The paths where inventories are stored. The
        caller is responsible for removing these after transfers complete.
  """
  list_task_arguments = [
      (source_container, False),
      (destination_container, False),
  ]
  # TODO(b/304524534): Replace with args.include_managed_folders.
  if getattr(args, 'include_managed_folders', False):
    list_task_arguments.extend(
        [(source_container, True), (destination_container, True)]
    )

  cleanup_paths = []
  list_tasks = []
  for container, managed_folders_only in list_task_arguments:
    path = rsync_command_util.get_hashed_list_file_path(
        container.storage_url.url_string,
        is_managed_folder_list=managed_folders_only,
    )
    cleanup_paths.append(path)
    task = get_sorted_list_file_task.GetSortedContainerContentsTask(
        container,
        path,
        exclude_pattern_strings=args.exclude,
        ignore_symlinks=args.ignore_symlinks,
        managed_folders_only=managed_folders_only,
        recurse=args.recursive,
    )
    list_tasks.append(task)
  return list_tasks, cleanup_paths


def _perform_rsync(
    args,
    source_container,
    destination_container,
    perform_managed_folder_operations=False,
):
  """Creates and executes tasks for rsync commands.

  Args:
    args (parser_extensions.Namespace): Command line arguments.
    source_container (resource_reference.Resource): Location to find source
      resources.
    destination_container (resource_reference.Resource): Location for
      destination resources.
    perform_managed_folder_operations (bool): If True, generates manifest files
      and performs copy tasks for managed folders. Otherwise, does so for
      objects/files.

  Returns:
    Exit code (int).
  """
  user_request_args = (
      user_request_args_factory.get_user_request_args_from_command_args(
          args, metadata_type=user_request_args_factory.MetadataType.OBJECT
      )
  )

  source_list_path = rsync_command_util.get_hashed_list_file_path(
      source_container.storage_url.url_string,
      is_managed_folder_list=perform_managed_folder_operations,
  )
  destination_list_path = rsync_command_util.get_hashed_list_file_path(
      destination_container.storage_url.url_string,
      is_managed_folder_list=perform_managed_folder_operations,
  )

  task_status_queue = task_graph_executor.multiprocessing_context.Queue()
  operation_iterator = rsync_command_util.get_operation_iterator(
      user_request_args,
      source_list_path,
      source_container,
      destination_list_path,
      destination_container,
      compare_only_hashes=args.checksums_only,
      delete_unmatched_destination_objects=(
          args.delete_unmatched_destination_objects
      ),
      dry_run=args.dry_run,
      ignore_symlinks=args.ignore_symlinks,
      yield_managed_folder_operations=perform_managed_folder_operations,
      skip_if_destination_has_later_modification_time=(
          args.skip_if_dest_has_newer_mtime
      ),
      skip_unsupported=args.skip_unsupported,
      task_status_queue=task_status_queue,
  )
  return task_executor.execute_tasks(
      operation_iterator,
      continue_on_error=args.continue_on_error,
      parallelizable=not perform_managed_folder_operations,
      progress_manager_args=task_status.ProgressManagerArgs(
          task_status.IncrementType.FILES_AND_BYTES,
          manifest_path=user_request_args.manifest_path,
      ),
      task_status_queue=task_status_queue,
  )


class Rsync(base.Command):
  """Synchronize content of two buckets/directories."""

  detailed_help = {
      'DESCRIPTION': """
      *{command}* copies to and updates objects at `DESTINATION` to match
      `SOURCE`. `SOURCE` must specify a directory, bucket, or bucket
      subdirectory. *{command}* does not copy empty directory trees,
      since storage providers use a [flat namespace](https://cloud.google.com/storage/docs/folders).

      Note, shells (like bash, zsh) sometimes attempt to expand wildcards in
      ways that can be surprising. Also, attempting to copy files whose names
      contain wildcard characters can result in problems.

      If synchronizing a large amount of data between clouds you might consider
      setting up a Google Compute Engine account and running *{command}* there.
      Since *{command}* cross-provider data transfers flow through the machine
      where *{command}* is running, doing this can make your transfer run
      significantly faster than on your local workstation.

      """,
      'EXAMPLES': """
      To sync the contents of the local directory `data` to the bucket
      gs://my-bucket/data:

        $ {command} data gs://my-bucket/data

      To recurse into directories use `--recursive`:

        $ {command} data gs://my-bucket/data --recursive

      To make the local directory `my-data` the same as the contents of
      gs://mybucket/data and delete objects in the local directory that are
      not in gs://mybucket/data:

        $ {command} gs://mybucket/data my-data --recursive \
           --delete-unmatched-destination-objects

      To make the contents of gs://mybucket2 the same as gs://mybucket1 and
      delete objects in gs://mybucket2 that are not in gs://mybucket1:

        $ {command} gs://mybucket1 gs://mybucket2 --recursive \
           --delete-unmatched-destination-objects

      To copy all objects from `dir1` into `dir2` and delete all objects
      in `dir2` which are not in `dir1`:

        $ {command} dir1 dir2 --recursive -\
           --delete-unmatched-destination-objects

      To mirror your objects across cloud providers:

        $ {command} gs://my-gs-bucket s3://my-s3-bucket --recursive \
           --delete-unmatched-destination-objects

      To apply gzip compression to only uploaded image files in `dir`:

        $ {command} dir gs://my-bucket/data --gzip-in-flight=jpeg,jpg,gif,png

      To skip the file `dir/data1/a.txt`:

        $ {command} dir gs://my-bucket --exclude="data./.*\\.txt$"

      To skip all .txt and .jpg files:

        $ {command} dir gs://my-bucket --exclude=".*\\.txt$|.*\\.jpg$"
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument('source', help='The source container path.')
    parser.add_argument('destination', help='The destination container path.')

    acl_flags_group = parser.add_group()
    flags.add_preserve_acl_flag(acl_flags_group, hidden=True)
    flags.add_predefined_acl_flag(acl_flags_group)

    flags.add_encryption_flags(parser)
    cp_command_util.add_cp_mv_rsync_flags(parser)
    cp_command_util.add_gzip_in_flight_flags(parser)
    cp_command_util.add_ignore_symlinks_flag(parser, default=True)
    cp_command_util.add_recursion_flag(parser)

    if cls.ReleaseTrack() is base.ReleaseTrack.ALPHA:
      cp_command_util.add_include_managed_folders_flag(parser)

    parser.add_argument(
        '--checksums-only',
        action='store_true',
        help=(
            'When comparing objects with matching names at the'
            ' source and destination, skip modification time check and'
            ' compare object hashes. Normally, hashes are only compared if'
            ' modification times are not available.'
        ),
    )
    parser.add_argument(
        '--delete-unmatched-destination-objects',
        action='store_true',
        help=textwrap.dedent("""\
            Delete extra files under DESTINATION not found under SOURCE.
            By default extra files are not deleted. Managed folders are not
            affected by this flag.

            Note: this option can delete data quickly if you specify the wrong
            source and destination combination."""),
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help=(
            'Print what operations rsync would perform without actually'
            ' executing them.'
        ),
    )
    parser.add_argument(
        '-x',
        '--exclude',
        metavar='REGEX',
        type=arg_parsers.ArgList(),
        help=(r"""Exclude objects matching regex pattern from rsync.

Note that this is a Python regular expression, not a pure wildcard
pattern. For example, matching a string ending in "abc" is
`.*abc$` rather than `*abc`. Also note that the exclude path
is relative, as opposed to absolute
(similar to Linux `rsync` and `tar` exclude options).

For the Windows cmd.exe command line interpreter, use
`^` as an escape character instead of `\` and escape the `|`
character. When using Windows PowerShell, use `'` instead of
`"` and surround the `|` character with `"`."""),
    )
    parser.add_argument(
        '-u',
        '--skip-if-dest-has-newer-mtime',
        action='store_true',
        help=(
            'Skip operating on destination object if it has a newer'
            ' modification time than the source.'
        ),
    )

  def Run(self, args):
    encryption_util.initialize_key_store(args)
    cp_command_util.validate_include_managed_folders(
        args,
        [args.source],
        storage_url.storage_url_from_string(args.destination),
    )
    source_container = rsync_command_util.get_existing_container_resource(
        os.path.expanduser(args.source), args.ignore_symlinks
    )
    destination_container = (
        rsync_command_util.get_existing_or_placeholder_destination_resource(
            os.path.expanduser(args.destination), args.ignore_symlinks
        )
    )

    list_tasks, cleanup_paths = _get_list_tasks_and_cleanup_paths(
        args, source_container, destination_container,
    )

    try:
      exit_code = task_executor.execute_tasks(
          list_tasks,
          continue_on_error=args.continue_on_error,
          parallelizable=True,
      )
      if exit_code:
        self.exit_code = exit_code
        return

      # TODO(b/304524534): Replace with args.include_managed_folders.
      if getattr(args, 'include_managed_folders', False):
        exit_code = _perform_rsync(
            args,
            source_container,
            destination_container,
            perform_managed_folder_operations=True,
        )
        if exit_code:
          # An error occurred setting up managed folders in the destination, so
          # we exit out early, as managed folders regulate permissions and we do
          # not want to copy to a location that is incorrectly configured.
          self.exit_code = exit_code
          return

      self.exit_code = _perform_rsync(
          args,
          source_container,
          destination_container,
          perform_managed_folder_operations=False,
      )

    finally:
      for path in cleanup_paths:
        rsync_command_util.try_to_delete_file(path)
