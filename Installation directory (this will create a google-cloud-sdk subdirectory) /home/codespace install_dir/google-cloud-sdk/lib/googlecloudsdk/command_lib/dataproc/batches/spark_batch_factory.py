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

"""Factory class for SparkBatch message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc import local_file_uploader


class SparkBatchFactory(object):
  """Factory class for SparkBatch message."""

  def __init__(self, dataproc):
    """Factory class for SparkBatch message.

    Args:
      dataproc: A Dataproc instance.
    """
    self.dataproc = dataproc

  def UploadLocalFilesAndGetMessage(self, args):
    """Uploads local files and creates a SparkBatch message.

    Uploads user local files and change the URIs to local files to point to
    uploaded URIs.
    Creates a SparkBatch message from parsed arguments.

    Args:
      args: Parsed arguments.

    Returns:
      SparkBatch: A SparkBatch message.

    Raises:
      AttributeError: Main class and jar are missing, or both were provided.
      Bucket is required to upload local files, but not specified.
    """
    kwargs = {}

    if args.args:
      kwargs['args'] = args.args

    if not args.main_class and not args.main_jar:
      raise AttributeError('Missing JVM main.')

    if args.main_class and args.main_jar:
      raise AttributeError('Can\'t provide both main class and jar.')

    dependencies = {}

    if args.main_class:
      kwargs['mainClass'] = args.main_class
    else:
      # Upload requires a list.
      dependencies['mainJarFileUri'] = [args.main_jar]

    if args.jars:
      dependencies['jarFileUris'] = args.jars

    if args.files:
      dependencies['fileUris'] = args.files

    if args.archives:
      dependencies['archiveUris'] = args.archives

    if local_file_uploader.HasLocalFiles(dependencies):
      if not args.deps_bucket:
        raise AttributeError('--deps-bucket was not specified.')
      dependencies = local_file_uploader.Upload(args.deps_bucket, dependencies)

    # Move mainJarFileUri out of the list.
    if 'mainJarFileUri' in dependencies:
      dependencies['mainJarFileUri'] = dependencies['mainJarFileUri'][0]

    # Merge the dictionaries first for backward compatibility.
    kwargs.update(dependencies)

    return self.dataproc.messages.SparkBatch(**kwargs)


def AddArguments(parser):
  flags.AddJvmMainMutex(parser)
  flags.AddArgs(parser)
  flags.AddJarFiles(parser)
  flags.AddOtherFiles(parser)
  flags.AddArchives(parser)
  flags.AddBucket(parser)
