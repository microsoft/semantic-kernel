# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Command to list Cloud Storage objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.storage import expansion
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_parallel
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.Hidden
@base.Deprecate(is_removed=False, warning='This command is deprecated. '
                'Use `gcloud alpha storage rm` instead.')
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  """Delete Cloud Storage objects and buckets."""

  detailed_help = {
      'DESCRIPTION': """\
      *{command}* lets you delete Cloud Storage objects and buckets. You can
      specify one or more paths (including wildcards) and all matching objects
      and buckets will be deleted.
      """,
      'EXAMPLES': """\
      To delete an object, run:

        $ *{command}* gs://mybucket/a.txt

      To delete all objects in a directory, run:

        $ *{command}* gs://mybucket/remote-dir/*

      The above command will delete all objects under remote-dir/ but not its sub-directories.

      To delete a directory and all its objects and subdirectories, run:

        $ *{command}* --recursive gs://mybucket/remote-dir
        $ *{command}* gs://mybucket/remote-dir/**

      To delete all objects and subdirectories of a directory, without deleting the directory
      itself, run:

        $ *{command}* --recursive gs://mybucket/remote-dir/*

        or

        $ *{command}* gs://mybucket/remote-dir/**

      To delete all objects and directories in a bucket without deleting the bucket itself, run:

        $ *{command}* gs://mybucket/**

      To delete all text files in a bucket or a directory, run:

        $ *{command}* gs://mybucket/*.txt
        $ *{command}* gs://mybucket/remote-dir/*.txt

      To go beyond directory boundary and delete all text files in a bucket or a directory, run:

        $ *{command}* gs://mybucket/**/*.txt
        $ *{command}* gs://mybucket/remote-dir/**/*.txt

      To delete a bucket, run:

        $ *{command}* gs://mybucket

      You can use wildcards in bucket names. To delete all buckets with prefix of `my`, run:

        $ *{command}* --recursive gs://my*
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'path',
        nargs='+',
        help='The path of objects and directories to delete. The path must '
             'begin with gs:// and may or may not contain wildcard characters.')
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Recursively delete the contents of any directories that match '
             'the path expression.')
    parser.add_argument(
        '--num-threads',
        type=int,
        hidden=True,
        default=16,
        help='The number of threads to use for the delete.')

    flags.add_additional_headers_flag(parser)

  def Run(self, args):
    paths = args.path or ['gs://']
    expander = expansion.GCSPathExpander()
    objects, dirs = expander.ExpandPaths(paths)
    if dirs and not args.recursive:
      raise exceptions.RequiredArgumentException(
          '--recursive',
          'Source path matches directories but --recursive was not specified.')

    buckets = []
    dir_paths = []
    for d in dirs:
      obj_ref = storage_util.ObjectReference.FromUrl(d, allow_empty_object=True)
      if not obj_ref.name:
        buckets.append(obj_ref.bucket_ref)
      dir_paths.append(d + '**')
    sub_objects, _ = expander.ExpandPaths(dir_paths)
    objects.update(sub_objects)

    tasks = []
    for o in sorted(objects):
      tasks.append(storage_parallel.ObjectDeleteTask(
          storage_util.ObjectReference.FromUrl(o)))

    if buckets:
      # Extra warnings and confirmation if any buckets will be deleted.
      log.warning('Deleting a bucket is irreversible and makes that bucket '
                  'name available for others to claim.')
      message = 'This command will delete the following buckets:\n  '
      message += '\n  '.join([b.bucket for b in buckets])
      console_io.PromptContinue(
          message=message, throw_if_unattended=True, cancel_on_no=True)

    # TODO(b/120033753): Handle long lists of items.
    message = 'You are about to delete the following:'
    message += ''.join(['\n  ' + b.ToUrl() for b in buckets])
    message += ''.join(['\n  ' + t.obj_ref.ToUrl() for t in tasks])
    console_io.PromptContinue(
        message=message, throw_if_unattended=True, cancel_on_no=True)

    storage_parallel.ExecuteTasks(tasks, num_threads=args.num_threads,
                                  progress_bar_label='Deleting Files')
    log.status.write(
        'Deleted [{}] file{}.\n'.format(
            len(tasks), 's' if len(tasks) > 1 else ''))

    storage_client = storage_api.StorageClient()
    for b in buckets:
      storage_client.DeleteBucket(b)
      log.DeletedResource(b.ToUrl(), kind='bucket')
