# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Execute a workflow and wait for the execution to complete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.workflows import cache
from googlecloudsdk.api_lib.workflows import workflows
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.workflows import flags
from googlecloudsdk.command_lib.workflows import hooks
from googlecloudsdk.core import resources

EXECUTION_COLLECTION = 'workflowexecutions.projects.locations.workflows.executions'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Run(base.DescribeCommand):
  """Execute a workflow and wait for the execution to complete."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To execute a workflow named my-workflow with the data that will be passed to the workflow, run:

          $ {command} my-workflow `--data=my-data`

        To add two labels {foo: bar, baz: qux} to the execution, run:

          $ {command} my-workflow `--data=my-data` `--labels=foo=bar,baz=qux`
        """,
  }

  @staticmethod
  def CommonArgs(parser):
    flags.AddWorkflowResourceArg(parser, verb='to execute')
    flags.AddDataArg(parser)

  @staticmethod
  def Args(parser):
    Run.CommonArgs(parser)
    flags.AddLoggingArg(parser)
    flags.AddDisableOverflowBufferArg(parser)
    labels_util.AddCreateLabelsFlags(parser)

  def CallLogLevel(self, args):
    return args.call_log_level

  def Labels(self, args):
    return flags.ParseExecutionLabels(args)

  def OverflowBufferingDisabled(self, args):
    return args.disable_concurrency_quota_overflow_buffering

  def Run(self, args):
    """Execute a workflow and wait for the completion of the execution."""
    hooks.print_default_location_warning(None, args, None)
    api_version = workflows.ReleaseTrackToApiVersion(self.ReleaseTrack())
    workflow_ref = flags.ParseWorkflow(args)
    client = workflows.WorkflowExecutionClient(api_version)
    execution = client.Create(
        workflow_ref,
        args.data,
        self.CallLogLevel(args),
        self.Labels(args),
        self.OverflowBufferingDisabled(args),
    )
    cache.cache_execution_id(execution.name)
    execution_ref = resources.REGISTRY.Parse(
        execution.name, collection=EXECUTION_COLLECTION
    )
    return client.WaitForExecution(execution_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaRun(Run):
  """Execute a workflow and wait for the execution to complete."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To execute a workflow named my-workflow with the data that will be passed to the workflow, run:

          $ {command} my-workflow --data=my-data
        """,
  }

  @staticmethod
  def Args(parser):
    Run.CommonArgs(parser)
    flags.AddBetaLoggingArg(parser)

  def CallLogLevel(self, args):
    return args.call_log_level

  def Labels(self, args):
    return None

  def OverflowBufferingDisabled(self, args):
    return False


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaRun(Run):
  """Execute a workflow and wait for the execution to complete."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
        To execute a workflow named my-workflow with the data that will be passed to the workflow, run:

          $ {command} my-workflow --data=my-data
        """,
  }

  @staticmethod
  def Args(parser):
    Run.CommonArgs(parser)

  def CallLogLevel(self, args):
    return None

  def Labels(self, args):
    return None

  def OverflowBufferingDisabled(self, args):
    return False
