# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command to list Cloud Dataflow snapshots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import dataflow_util
from googlecloudsdk.command_lib.dataflow import snapshot_utils
from googlecloudsdk.core import properties


class List(base.Command):
  """List all Cloud Dataflow snapshots in a project in the specified region, optionally filtered by job ID."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To list all Cloud Dataflow snapshots in the us-central1 region, run:

            $ {command} --region=us-central1

          To list all Cloud Dataflow snapshots for a job, run:

            $ {command} --job-id=JOB_ID --region=JOB_REGION
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    snapshot_utils.ArgsForListSnapshot(parser)

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments that were provided to this command invocation.

    Returns:
      A Snapshot message.
    """
    return apis.Snapshots.List(
        job_id=args.job_id,
        project_id=properties.VALUES.core.project.GetOrFail(),
        region_id=dataflow_util.GetRegion(args))
