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
"""Create Command for Job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.fault_injection import jobs
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.fault_injection import flags
from googlecloudsdk.core import resources


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To create a Job with the id `my-job` experiment `my-experiment`
        and fault-targets `target1 and target2`, run:

          $ {command} my-job --experiment=my-experiment --fault-targets="target1", "target2"
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Fault injection testing job."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddCreateJobFlags(parser)

  @staticmethod
  def ParseResourceArgs(args):
    """Parse, validate and return the CA and KMS key version args from the CLI.

    Args:
      args: The parsed arguments from the command-line.

    Returns:
      Tuple containing the Resource objects for the KMS key version and CA,
      respectively.
    """
    job_ref = args.CONCEPTS.job.Parse()
    # TODO(b/149316889): Use concepts library once attribute fallthroughs work.
    exp_ref = resources.REGISTRY.Parse(
        args.experiment,
        collection='faultinjectiontesting.projects.locations.experiments',
        params={
            'projectsId': job_ref.projectsId,
            'locationsId': job_ref.locationsId,
        },
    )

    if exp_ref.projectsId != job_ref.projectsId:
      raise exceptions.InvalidArgumentException(
          'Experiment',
          'Experiment must be in the same project as the JOB'
          'version.',
      )

    if exp_ref.locationsId != job_ref.locationsId:
      raise exceptions.InvalidArgumentException(
          'Experiment',
          'Experiment must be in the same location as the Job'
          'version.',
      )

    return (job_ref, exp_ref)

  def Run(self, args):
    """Run the create command."""
    client = jobs.JobsClient()
    # job_ref = args.CONCEPTS.job.Parse()
    # exp_ref = args.CONCEPTS.experiment.Parse()
    job_ref, exp_ref = self.ParseResourceArgs(args)
    parent_ref = job_ref.Parent()
    if not job_ref.Name():
      raise exceptions.InvalidArgumentException(
          'job', 'job id must be non-empty.'
      )
    if not exp_ref.Name():
      raise exceptions.InvalidArgumentException(
          'job', 'experiment must be non-empty.'
      )
    if not args.fault_targets:
      raise exceptions.InvalidArgumentException(
          'job', 'fault targets must be non-empty.'
      )
    # if args.fault_targets.
    return client.Create(
        job_id=job_ref.Name(),
        experiment_id=exp_ref.RelativeName(),
        fault_targets=args.fault_targets,
        dry_run=args.dry_run,
        parent=parent_ref.RelativeName(),
    )
