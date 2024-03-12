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

"""Factory for PeripheralsConfig message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.dataproc.shared_messages import (
    spark_history_server_config_factory as shscf)


class PeripheralsConfigFactory(object):
  """Factory for PeripheralsConfig message.

  Adds related arguments to argument parser and create PeripheralsConfig message
  from parsed arguments.
  """

  def __init__(self, dataproc,
               spark_history_server_config_factory_override=None):
    """Factory class for PeripheralsConfig message.

    Args:
      dataproc: A api_lib.dataproc.Dataproc instance.
      spark_history_server_config_factory_override: Override the default
      SparkHistoryServerConfigFactory instance.
    """
    self.dataproc = dataproc

    self.spark_history_server_config_factory = (
        spark_history_server_config_factory_override)
    if not self.spark_history_server_config_factory:
      self.spark_history_server_config_factory = (
          shscf.SparkHistoryServerConfigFactory(self.dataproc))

  def GetMessage(self, args):
    """Builds a PeripheralsConfig message.

    Args:
      args: Parsed arguments.

    Returns:
      PeripheralsConfig: A PeripheralsConfig message instance. None if all
      fields are None.
    """
    kwargs = {}

    if args.metastore_service:
      kwargs['metastoreService'] = args.metastore_service

    spark_history_server_config = (
        self.spark_history_server_config_factory.GetMessage(args))
    if spark_history_server_config:
      kwargs['sparkHistoryServerConfig'] = spark_history_server_config

    if not kwargs:
      return None

    return self.dataproc.messages.PeripheralsConfig(**kwargs)


def AddArguments(parser):
  """Adds PeripheralsConfig related arguments to parser."""
  parser.add_argument(
      '--metastore-service',
      help=('Name of a Dataproc Metastore service to be used as an '
            'external metastore in the format: '
            '"projects/{project-id}/locations/{region}/services/'
            '{service-name}".'))

  _AddDependency(parser)


def _AddDependency(parser):
  shscf.AddArguments(parser)
