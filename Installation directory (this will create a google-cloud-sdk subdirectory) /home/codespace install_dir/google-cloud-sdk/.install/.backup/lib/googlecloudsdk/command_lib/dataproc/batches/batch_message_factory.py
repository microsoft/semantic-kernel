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

"""Factory class for Batch message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.dataproc.shared_messages import (
    environment_config_factory as ecf,
)
from googlecloudsdk.command_lib.dataproc.shared_messages import (
    runtime_config_factory as rcf,
)
from googlecloudsdk.command_lib.util.args import labels_util


class BatchMessageFactory(object):
  """Factory class for Batch message.

  Factory class for configuring argument parser and creating a Batch message
  from the parsed arguments.
  """

  INVALID_BATCH_TYPE_ERR_MSG = 'Invalid batch job type: {}.'
  MISSING_BATCH_ERR_MSG = 'Missing batch job.'

  def __init__(
      self,
      dataproc,
      runtime_config_factory_override=None,
      environment_config_factory_override=None,
  ):
    """Builder class for Batch message.

    Batch message factory. Only the flags added in AddArguments are handled.
    User need to provide batch job type specific message during message
    creation.

    Args:
      dataproc: A api_lib.dataproc.Dataproc instance.
      runtime_config_factory_override: Override the default RuntimeConfigFactory
        instance.
      environment_config_factory_override: Override the default
        EnvironmentConfigFactory instance.
    """
    self.dataproc = dataproc

    # Construct available batch type to keyword mapping.
    self._batch2key = {
        self.dataproc.messages.SparkBatch: 'sparkBatch',
        self.dataproc.messages.SparkRBatch: 'sparkRBatch',
        self.dataproc.messages.SparkSqlBatch: 'sparkSqlBatch',
        self.dataproc.messages.PySparkBatch: 'pysparkBatch',
    }

    self.runtime_config_factory = runtime_config_factory_override
    if not self.runtime_config_factory:
      self.runtime_config_factory = rcf.RuntimeConfigFactory(
          self.dataproc, include_autotuning=True, include_cohort=True
      )

    self.environment_config_factory = environment_config_factory_override
    if not self.environment_config_factory:
      self.environment_config_factory = ecf.EnvironmentConfigFactory(
          self.dataproc
      )

  def GetMessage(self, args, batch_job):
    """Creates a Batch message from given args.

    Create a Batch message from given arguments. Only the arguments added in
    AddAddArguments are handled. User need to provide bath job type specific
    message during message creation.

    Args:
      args: Parsed argument.
      batch_job: Batch type job instance.

    Returns:
      A Batch message instance.

    Raises:
      AttributeError: When batch_job is invalid.
    """
    if not batch_job:
      raise AttributeError(BatchMessageFactory.MISSING_BATCH_ERR_MSG)

    if not isinstance(batch_job, tuple(self._batch2key.keys())):
      raise AttributeError(
          BatchMessageFactory.INVALID_BATCH_TYPE_ERR_MSG.format(type(batch_job))
      )

    kwargs = {}

    kwargs[self._batch2key[type(batch_job)]] = batch_job

    if args.labels:
      kwargs['labels'] = labels_util.ParseCreateArgs(
          args, self.dataproc.messages.Batch.LabelsValue
      )

    runtime_config = self.runtime_config_factory.GetMessage(args)
    if runtime_config:
      kwargs['runtimeConfig'] = runtime_config

    environment_config = self.environment_config_factory.GetMessage(args)
    if environment_config:
      kwargs['environmentConfig'] = environment_config

    if not kwargs:
      return None

    return self.dataproc.messages.Batch(**kwargs)


def AddArguments(parser):
  """Adds arguments related to Batch message.

  Add Batch arguments to the given parser. Job specific arguments are not
  handled, and need to be set during factory instantiation.

  Args:
    parser: A argument parser.
  """
  labels_util.AddCreateLabelsFlags(parser)

  _AddDependency(parser)


def _AddDependency(parser):
  rcf.AddArguments(parser, include_autotuning=True, include_cohort=True)
  ecf.AddArguments(parser)
