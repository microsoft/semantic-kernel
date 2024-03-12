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

"""Factory class for SparkRBatch message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc import local_file_uploader


class SparkRBatchFactory(object):
  """Factory class for SparkRBatch message."""

  def __init__(self, dataproc):
    """Factory class for SparkRBatch message.

    Args:
      dataproc: A Dataproc instance.
    """
    self.dataproc = dataproc

  def UploadLocalFilesAndGetMessage(self, args):
    """Upload local files and creates a SparkRBatch message.

    Upload user local files and change local file URIs to point to the uploaded
    URIs.
    Creates a SparkRBatch message based on parsed arguments.

    Args:
      args: Parsed arguments.

    Returns:
      A SparkRBatch message.

    Raises:
      AttributeError: Bucket is required to upload local files, but not
      specified.
    """
    kwargs = {}

    if args.args:
      kwargs['args'] = args.args

    dependencies = {}

    # Upload requires a list.
    dependencies['mainRFileUri'] = [args.MAIN_R_FILE]

    if args.files:
      dependencies['fileUris'] = args.files

    if args.archives:
      dependencies['archiveUris'] = args.archives

    if local_file_uploader.HasLocalFiles(dependencies):
      if not args.deps_bucket:
        raise AttributeError('--deps-bucket was not specified.')
      dependencies = local_file_uploader.Upload(args.deps_bucket, dependencies)

    # Get mainRFileUri out of the list for message construction.
    dependencies['mainRFileUri'] = dependencies['mainRFileUri'][0]

    # Merge the dictionaries first for backward compatibility.
    kwargs.update(dependencies)

    return self.dataproc.messages.SparkRBatch(**kwargs)


def AddArguments(parser):
  flags.AddMainRFile(parser)
  flags.AddArgs(parser)
  flags.AddOtherFiles(parser)
  flags.AddArchives(parser)
  flags.AddBucket(parser)
