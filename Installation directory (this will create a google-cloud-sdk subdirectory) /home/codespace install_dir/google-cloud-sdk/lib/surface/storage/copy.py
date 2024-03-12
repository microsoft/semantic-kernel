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

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import copying
from googlecloudsdk.command_lib.storage import paths
from googlecloudsdk.command_lib.storage import storage_parallel
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Deprecate(is_removed=False, warning='This command is deprecated. '
                'Use `gcloud alpha storage cp` instead.')
class Copy(base.Command):
  """Upload, download, and copy Cloud Storage objects."""

  detailed_help = {
      'DESCRIPTION': """\
      Copy files between your local file system and Cloud Storage or from one
      Cloud Storage location to another.
      """,
      'EXAMPLES': """\

      Uploading files:

        To upload a single file to a remote location:

          $ *{command}* path/to/file.txt gs://mybucket/file.txt
          $ *{command}* path/to/file.txt gs://mybucket/

        The above two commands both create gs://mybucket/file.txt.

        To upload multiple files to a remote location:

          $ *{command}* path/to/a.txt other/path/b.txt gs://mybucket/remote-dir/

        The above command will create gs://mybucket/remote-dir/a.txt and
        gs://mybucket/remote-dir/b.txt. If remote-dir does not exist, this command will create
        remote-dir.

        To upload a directory my-dir and all its sub-directories and files:

          $ *{command}* --recursive my-dir gs://mybucket/remote-dir/

        If my-dir has a subdirectory sub-dir and sub-dir has a file a.txt, the above
        command will create gs://mybucket/remote-dir/my-dir/sub-dir/a.txt. The structure of directory
        is kept.

        The following command also uploads all files in my-dir and sub-directories recursively:

          $ *{command}* my-dir/** gs://mybucket/remote-dir/

        The above command flattens the directory strucutre and creates gs://mybucket/remote-dir/a.txt.

        To upload all files in a directory, ignoring the subdirectories:

          $ *{command}*  my-dir/* gs://mybucket/remote-dir/

        If my-dir has a file a.txt and a subdirectory sub-dir. The above command will ceate
        gs://mybucket/remote-dir/a.txt.

        We can combine the wildcards to upload all text files in a directory and all subdirectories
        recursively:

          $ *{command}*  my-dir/**/*.txt gs://mybucket/remote-dir/

      Downloading files:

        To download a single file:

          $ *{command}* gs://mybucket/file.txt local-dir/
          $ *{command}* gs://mybucket/file.txt local-dir/file.txt

        The above two commands both create local-dir/file.txt.

        To download multiple files:

          $ *{command}* gs://mybucket/a.txt gs://mybucket/b.txt local-dir/

        The above command creates local-dir/a.txt and local-dir/b.txt.

        To download a directory and all its sub-directories and files:

          $ *{command}* --recursive gs://mybucket/remote-dir/ local-dir/

        The above command creates local-dir/remote-dir/ which contains all files and subdirectories
        of gs://mybucket/remote-dir/. The structure of directory is kept.

        The following command also downloads all files in gs://mybucket/remote-dir/ to local-dir:

          $ *{command}* gs://mybucket/remote-dir/** local-dir/

        If remote-dir contains files a.txt and sub-dir/b.txt, the above command flattens the
        directory structure and creates local-dir/a.txt and local-dir/b.txt.

        To download all files, ignoring the subdirectories::

          $ *{command}* gs://mybucket/remote-dir/* local-dir/

        We can combine the wildcards to download all text files under remote-dir and its
        subdirectories:

          $ *{command}* gs://mybucket/remote-dir/**/*.txt local-dir/

      Coping between Cloud Storage locations:

        To copy a single file to another location:

          $ *{command}* gs://mybucket/file.txt gs://otherbucket/file.txt
          $ *{command}* gs://mybucket/file.txt gs://otherbucket/

        The above two commands both create gs://otherbucket/file.txt.

        To copy multiple files to a new location:

          $ *{command}* gs://mybucket/a.txt gs://mybucket/b.txt gs://otherbucket/target-dir/

        The above command creates gs://otherbucket/target-dir/a.txt and
        gs://otherbucket/target-dir/b.txt. If target-dir does not exist, this command will create
        target-dir.

        To copy all files and subdirectories in one location to another:

          $ *{command}* --recursive gs://mybucket/source-dir/ gs://otherbucket/target-dir/

        If source-dir has a subdirectory sub-dir and sub-dir has a file a.txt, the above
        command will create gs://mybucket/target-dir/source-dir/sub-dir/a.txt. The structure of
        directory is kept.

        The following command also copies all files in source-dir and its sub-directories:

          $ *{command}* gs://mybucket/source-dir/** gs://mybucket/target-dir/

        The above command flattens the directory strucutre and creates gs://mybucket/target-dir/a.txt.

        To copy all files in a directory, ignoring the subdirectories:

          $ *{command}* gs://mybucket/source-dir/* gs://mybucket/target-dir/

        If source-dir has a file a.txt and a subdirectory sub-dir. The above command will ceate
        gs://mybucket/target-dir/a.txt.

        We can combine the wildcards to copy all text in one location and all its sub-directories:

          $ *{command}* gs://mybucket/source-dir/**/*.txt gs://mybucket/target-dir/
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'source',
        nargs='+',
        help='The source file to copy.')
    parser.add_argument(
        'destination',
        help='The destination to copy the file to.')
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Recursively copy the contents of any directories that match the '
             'path expression.')
    parser.add_argument(
        '--num-threads',
        type=int,
        hidden=True,
        default=16,
        help='The number of threads to use for the copy.')

  def Run(self, args):
    sources = [paths.Path(p) for p in args.source]
    dest = paths.Path(args.destination)
    copier = copying.CopyTaskGenerator()
    tasks = copier.GetCopyTasks(sources, dest, recursive=args.recursive)
    storage_parallel.ExecuteTasks(
        tasks, num_threads=args.num_threads, progress_bar_label='Copying Files')
    log.status.write('Copied [{}] file{}.\n'.format(
        len(tasks), 's' if len(tasks) > 1 else ''))
