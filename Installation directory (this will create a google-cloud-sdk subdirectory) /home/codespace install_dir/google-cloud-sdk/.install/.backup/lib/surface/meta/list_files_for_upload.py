# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""The `gcloud meta list-files-for-upload` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util import gcloudignore


class ListFilesForUpload(base.Command):
  """List files for upload.

  List the files that would be uploaded in a given directory.

  Useful for checking the effects of a .gitignore or .gcloudignore file.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'directory', default='.', nargs='?',
        help='The directory in which to show what files would be uploaded')
    parser.display_info.AddFormat('value(.)')

  def Run(self, args):
    file_chooser = gcloudignore.GetFileChooserForDir(args.directory,
                                                     write_on_disk=False)
    file_chooser = file_chooser or gcloudignore.FileChooser([])
    return file_chooser.GetIncludedFiles(args.directory, include_dirs=False)
