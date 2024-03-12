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

"""Command provides active assist recommendations for input Terraform plan.

Step 1: Convert Terraform plan into CAI using terraform tools.
Step 2: Fetches the recommendations using the recommender API for resources in
the CAI output.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os.path

from googlecloudsdk.api_lib.recommender import insight
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.terraform import flags
from googlecloudsdk.command_lib.terraform.env_vars import EnvironmentVariables
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import files
from surface.terraform.vet import TerraformToolsTfplanToCaiOperation


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """Lists recommendations relevant to the input terraform plan."""

  detailed_help = {
      'EXAMPLES':
          """
        Lists recommendations relevant to the input terraform plan.

        $ {command} tfplan.json
        """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    It takes arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.
    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.Terraformplanjson().AddToParser(parser)

  def Run(self, args):
    environment_variables = EnvironmentVariables()

    tfplan_to_cai_operation = TerraformToolsTfplanToCaiOperation()
    with files.TemporaryDirectory() as tempdir:
      cai_assets = os.path.join(tempdir, 'cai_assets.json')
      response = tfplan_to_cai_operation(
          command='tfplan-to-cai',
          project=environment_variables.project,
          region='',
          zone='',
          terraform_plan_json=args.terraform_plan_json,
          verbosity='debug',
          output_path=cai_assets,
          env=environment_variables.env_vars)
      self.exit_code = response.exit_code
      if self.exit_code > 0:
        # The streaming binary backed operation handles its own writing to
        # stdout and stderr, so there's nothing left to do here.
        return None
      client = insight.CreateClient(self.ReleaseTrack())

      # TODO(b/265408840): move this to util file. Create different dicts for
      # Alpha, Beta and GA release to control the insight types exposed by each.
      cai_insight_types = {
          'iam_policy': {
              'insight_type': 'google.iam.policy.Insight',
              'location': 'global',
          },
          # TODO(b/265408840): add support for more insight types.
      }

      # Read CAI and call recommender API.
      with files.FileReader(cai_assets) as f:
        try:
          cai_json = json.load(f)
        except json.JSONDecodeError:
          raise exceptions.Error("""Please check the following:
                                 - Input plan file is correct.
                                 - You have appropriate permissions to read
                                 inventory of resources inside the plan file."""
                                )
        for resource in cai_json:
          for cai_type in cai_insight_types:
            if cai_type in resource:
              if cai_insight_types[cai_type]['location'] == 'global':
                location = 'global'
              else:
                # TODO(b/265408382): fetch this location from CAI resource.
                location = 'regional'
                # TODO(b/265408382): handle case if location doesn't exists in
                # CAI (if any).
              if (
                  resource['asset_type']
                  == 'cloudresourcemanager.googleapis.com/Project'
              ):
                resource_parent = 'projects/{}'.format(
                    resource['name'].split('/')[-1]
                )
              else:
                continue
              # TODO(b/265408203): handle cases for other parent types.
              if resource_parent:
                insight_parent = '{}/locations/{}/insightTypes/{}'.format(
                    resource_parent,
                    location,
                    cai_insight_types[cai_type]['insight_type'],
                )
                # TODO(b/265408203): filter recommendations as per the specific
                # resouces under CAI instead of just the insight type filter.
                return client.List(insight_parent, args.page_size, args.limit)
