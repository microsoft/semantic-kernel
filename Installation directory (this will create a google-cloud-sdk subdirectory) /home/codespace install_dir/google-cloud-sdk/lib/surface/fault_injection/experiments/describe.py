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
"""Command to describe a Experiment in the Project/Location."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.fault_injection import experiments
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.fault_injection import flags


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        to describe a experiment with the id `my-experiment`, run:

          $ {command} my-experiment
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe Experiment."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddDescribeExperimentFlags(parser)

  def Run(self, args):
    """Run the describe command."""
    client = experiments.ExperimentsClient()
    exp_ref = args.CONCEPTS.experiment.Parse()
    if not exp_ref.Name():
      raise exceptions.InvalidArgumentException(
          'experiment', 'experiment id must be non-empty.'
      )
    return client.Describe(experiment=exp_ref.RelativeName())
