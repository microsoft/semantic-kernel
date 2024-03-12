# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Implementation of gcloud dataflow jobs update-options command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dataflow import job_utils


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class UpdateOptions(base.Command):
  """Update pipeline options on-the-fly for running Dataflow jobs.

  This command can modify properties of running Dataflow jobs. Currently, only
  updating autoscaling settings for Streaming Engine jobs is supported.

  Adjust the autoscaling settings for Streaming Engine Dataflow jobs by
  providing at-least one of --min-num-workers or --max-num-workers or
  --worker-utilization-hint (or all 3), or --unset-worker-utilization-hint
  (which cannot be run at the same time as --worker-utilization-hint but works
  with the others).
  Allow a few minutes for the changes to take effect.

  Note that autoscaling settings can only be modified on-the-fly for Streaming
  Engine jobs. Attempts to modify batch job or Streaming Appliance jobs will
  fail.


  ## EXAMPLES

  Modify autoscaling settings to scale between 5-10 workers:

    $ {command} --min-num-workers=5 --max-num-workers=10

  Require a job to use at least 2 workers:

    $ {command} --min-num-workers=2

  Require a job to use at most 20 workers:

    $ {command} --max-num-workers=20

  Adjust the hint of target worker utilization to 70% for horizontal
  autoscaling:

    $ {command} --worker-utilization-hint=0.7

  "Unset" worker utilization hint so that horizontal scaling will rely on its
  default CPU utilization target:

    $ {command} --unset-worker-utilization-hint
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    job_utils.ArgsForJobRef(parser)
    parser.add_argument(
        '--min-num-workers',
        type=int,
        help=(
            'Lower-bound for autoscaling, between 1-1000. Only supported for'
            ' streaming-engine jobs.'
        ),
    )
    parser.add_argument(
        '--max-num-workers',
        type=int,
        help=(
            'Upper-bound for autoscaling, between 1-1000. Only supported for'
            ' streaming-engine jobs.'
        ),
    )
    parser.add_argument(
        '--worker-utilization-hint',
        type=float,
        help=(
            'Target CPU utilization for autoscaling, ranging from 0.1 to 0.9.'
            ' Only supported for streaming-engine jobs with autoscaling'
            ' enabled.'
        ),
    )
    parser.add_argument(
        '--unset-worker-utilization-hint',
        action='store_true',
        help=(
            'Unset --worker-utilization-hint. This causes the'
            ' job autoscaling to fall back to internal tunings'
            ' if they exist, or otherwise use the default hint value.'
        ),
    )

  def Run(self, args):
    """Called when the user runs gcloud dataflow jobs update-options ...

    Args:
      args: all the arguments that were provided to this command invocation.

    Returns:
      The updated Job
    """
    if (
        args.min_num_workers is None
        and args.max_num_workers is None
        and args.worker_utilization_hint is None
        and not args.unset_worker_utilization_hint
    ):
      raise exceptions.OneOfArgumentsRequiredException(
          [
              '--min-num-workers',
              '--max-num-workers',
              '--worker-utilization-hint',
              '--unset-worker-utilization-hint',
          ],
          'You must provide at-least one field to update',
      )
    elif (
        args.worker_utilization_hint is not None
        and args.unset_worker_utilization_hint
    ):
      raise exceptions.ConflictingArgumentsException(
          'The arguments --worker-utilization-hint and'
          ' --unset-worker-utilization-hint are mutually exclusive (as the'
          ' unset command will unset the given hint), and must be called'
          ' separately.',
      )

    job_ref = job_utils.ExtractJobRef(args)
    return apis.Jobs.UpdateOptions(
        job_ref.jobId,
        project_id=job_ref.projectId,
        region_id=job_ref.location,
        min_num_workers=args.min_num_workers,
        max_num_workers=args.max_num_workers,
        worker_utilization_hint=args.worker_utilization_hint,
        unset_worker_utilization_hint=args.unset_worker_utilization_hint,
    )
