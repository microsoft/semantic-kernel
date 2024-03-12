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

"""Factory for SparkHistoryServerConfig message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class SparkHistoryServerConfigFactory(object):
  """Factory for SparkHistoryServerConfig message.

  Adds arguments to argument parser and create SparkHistoryServerConfig from
  parsed arguments.
  """

  def __init__(self, dataproc):
    """Factory class for SparkHistoryServerConfig message.

    Args:
      dataproc: An api_lib.dataproc.Dataproc instance.
    """
    self.dataproc = dataproc

  def GetMessage(self, args):
    """Builds a SparkHistoryServerConfig instance.

    Args:
      args: Parsed arguments.

    Returns:
      SparkHistoryServerConfig: A SparkHistoryServerConfig message instance.
      None if all fields are None.
    """
    if args.history_server_cluster:
      return self.dataproc.messages.SparkHistoryServerConfig(
          dataprocCluster=args.history_server_cluster)
    return None


def AddArguments(parser):
  """Adds related arguments to aprser."""
  parser.add_argument(
      '--history-server-cluster',
      help=('Spark History Server configuration for the batch/session job. '
            'Resource name of an existing Dataproc cluster to act as a '
            'Spark History Server for the workload in the format: "projects/'
            '{project_id}/regions/{region}/clusters/{cluster_name}".'))
