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
"""Implementation of objects update command for updating object settings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage import stdin_iterator
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.objects import patch_object_task
from googlecloudsdk.command_lib.storage.tasks.objects import rewrite_object_task


def _get_task_iterator(urls, args):
  """Yields PatchObjectTask's or RewriteObjectTask's."""
  requires_rewrite = (
      args.encryption_key or args.clear_encryption_key or args.storage_class)
  if requires_rewrite:
    task_type = rewrite_object_task.RewriteObjectTask
  else:
    task_type = patch_object_task.PatchObjectTask

  user_request_args = (
      user_request_args_factory.get_user_request_args_from_command_args(
          args, metadata_type=user_request_args_factory.MetadataType.OBJECT))
  adds_or_removes_acls = user_request_args_factory.adds_or_removes_acls(
      user_request_args
  )
  # TODO(b/292084011): Remove getattr when object lock is GA.
  updates_retention = getattr(args, 'retain_until', None) or getattr(
      args, 'retention_mode', None
  )
  if requires_rewrite or adds_or_removes_acls:
    fields_scope = cloud_api.FieldsScope.FULL
  elif updates_retention:
    fields_scope = cloud_api.FieldsScope.NO_ACL
  else:
    fields_scope = cloud_api.FieldsScope.SHORT

  if args.all_versions and not (
      args.predefined_acl or args.acl_file or adds_or_removes_acls
  ):
    # TODO(b/264282236) Stop raising error once we confirm that this flag
    # works fine with all types of object update operations.
    raise errors.Error(
        '--all_versions flag is only allowed for ACL modifier flags.')

  if args.recursive:
    recursion_setting = name_expansion.RecursionSetting.YES
  else:
    recursion_setting = name_expansion.RecursionSetting.NO
  for name_expansion_result in name_expansion.NameExpansionIterator(
      urls,
      fields_scope=fields_scope,
      include_buckets=name_expansion.BucketSetting.NO_WITH_ERROR,
      object_state=flags.get_object_state_from_flags(args),
      recursion_requested=recursion_setting,
  ):
    yield task_type(
        name_expansion_result.resource, user_request_args=user_request_args
    )


def _add_common_args(parser):
  """Register flags for this command.

  Args:
    parser (argparse.ArgumentParser): The parser to add the arguments to.

  Returns:
    objects update flag group
  """
  parser.add_argument(
      'url', nargs='*', help='Specifies URLs of objects to update.')

  parser.add_argument(
      '--all-versions',
      action='store_true',
      help='Perform the operation on all object versions.',
  )

  acl_flags_group = parser.add_group()
  flags.add_acl_modifier_flags(acl_flags_group)
  flags.add_preserve_acl_flag(acl_flags_group)

  parser.add_argument(
      '--event-based-hold',
      action=arg_parsers.StoreTrueFalseAction,
      help='Enables or disables an event-based hold on objects.')
  parser.add_argument(
      '-R',
      '-r',
      '--recursive',
      action='store_true',
      help='Recursively update objects under any buckets or directories that'
      ' match the URL expression.')
  parser.add_argument(
      '-s',
      '--storage-class',
      help='Specify the storage class of the object. Using this flag triggers'
      ' a rewrite of underlying object data.')
  parser.add_argument(
      '--temporary-hold',
      action=arg_parsers.StoreTrueFalseAction,
      help='Enables or disables a temporary hold on objects.')

  flags.add_additional_headers_flag(parser)
  flags.add_continue_on_error_flag(parser)
  flags.add_encryption_flags(parser, allow_patch=True)
  flags.add_precondition_flags(parser)
  flags.add_object_metadata_flags(parser, allow_patch=True)
  flags.add_per_object_retention_flags(parser, is_update=True)
  flags.add_read_paths_from_stdin_flag(
      parser,
      help_text=(
          'Read the list of objects to update from stdin. No need to enter'
          ' a source argument if this flag is present.\nExample:'
          ' "storage objects update -I --content-type=new-type"'
      ),
  )


def _add_alpha_args(parser):
  """Register flags for the alpha version of this command.

  Args:
    parser (argparse.ArgumentParser): The parser to add the arguments to.

  Returns:
    objects update flag group
  """
  del parser  # Unused.


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Update Cloud Storage objects."""

  detailed_help = {
      'DESCRIPTION':
          """
      Update Cloud Storage objects.
      """,
      'EXAMPLES':
          """

      Update a Google Cloud Storage object's custom-metadata:

        $ {command} gs://bucket/my-object --custom-metadata=key1=value1,key2=value2

      Rewrite all JPEG images to the NEARLINE storage class:

        $ {command} gs://bucket/*.jpg --storage-class=NEARLINE

       You can also provide a precondition on an object's metageneration in
       order to avoid potential race conditions:

        $ {command} gs://bucket/*.jpg --storage-class=NEARLINE --if-metageneration-match=123456789
      """,
  }

  @staticmethod
  def Args(parser):
    _add_common_args(parser)

  def Run(self, args):
    encryption_util.initialize_key_store(args)
    if not args.predefined_acl and args.preserve_acl is None:
      # Preserve ACLs by default if nothing set by user.
      args.preserve_acl = True

    urls = stdin_iterator.get_urls_iterable(
        args.url, args.read_paths_from_stdin
    )
    task_iterator = _get_task_iterator(urls, args)

    task_status_queue = task_graph_executor.multiprocessing_context.Queue()
    self.exit_code = task_executor.execute_tasks(
        task_iterator,
        parallelizable=True,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            increment_type=task_status.IncrementType.INTEGER,
            manifest_path=None),
        continue_on_error=args.continue_on_error,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update Cloud Storage objects."""

  @staticmethod
  def Args(parser):
    _add_common_args(parser)
    _add_alpha_args(parser)
