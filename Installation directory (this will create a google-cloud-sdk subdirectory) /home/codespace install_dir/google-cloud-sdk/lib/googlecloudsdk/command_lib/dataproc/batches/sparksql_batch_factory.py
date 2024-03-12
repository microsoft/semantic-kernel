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

"""Factory class for SparkSqlBatch message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc import local_file_uploader


class SparkSqlBatchFactory(object):
  """Factory class for SparkSqlBatch message."""

  def __init__(self, dataproc):
    """Factory class for SparkSqlBatch message.

    Args:
      dataproc: A Dataproc instance.
    """
    self.dataproc = dataproc

  def UploadLocalFilesAndGetMessage(self, args):
    """Uploads local files and creates a SparkSqlBatch message.

    Uploads user local files and change the URIs to local files to uploaded
    URIs.
    Creates a SparkSqlBatch message.

    Args:
      args: Parsed arguments.

    Returns:
      A SparkSqlBatch message instance.

    Raises:
      AttributeError: Bucket is required to upload local files, but not
      specified.
    """

    kwargs = {}

    dependencies = {}

    # Upload requires a list.
    dependencies['queryFileUri'] = [args.SQL_SCRIPT]

    if args.jars:
      dependencies['jarFileUris'] = args.jars

    params = args.vars
    if params:
      kwargs['queryVariables'] = encoding.DictToAdditionalPropertyMessage(
          params,
          self.dataproc.messages.SparkSqlBatch.QueryVariablesValue,
          sort_items=True)

    if local_file_uploader.HasLocalFiles(dependencies):
      if not args.deps_bucket:
        raise AttributeError('--deps-bucket was not specified.')
      dependencies = local_file_uploader.Upload(args.deps_bucket, dependencies)

    # Move main SQL script out of the list.
    dependencies['queryFileUri'] = dependencies['queryFileUri'][0]

    # Merge the dictionaries first for compatibility.
    kwargs.update(dependencies)

    return self.dataproc.messages.SparkSqlBatch(**kwargs)


def AddArguments(parser):
  flags.AddMainSqlScript(parser)
  flags.AddJarFiles(parser)
  flags.AddSqlScriptVariables(parser)
  # Cloud Storage bucket to upload workload dependencies.
  # It is required until we figure out a place to upload user files.
  flags.AddBucket(parser)
