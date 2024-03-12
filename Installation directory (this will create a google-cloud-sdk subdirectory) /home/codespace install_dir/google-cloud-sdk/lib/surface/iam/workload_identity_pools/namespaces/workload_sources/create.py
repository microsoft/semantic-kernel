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
"""Command to create a workload source for a workload identity pool namespace."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.api_lib.iam.workload_identity_pools import workload_sources
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.iam.workload_identity_pools import flags
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log


class CreateGcp(base.CreateCommand):
  """Create a workload source for a workload identity pool namespace."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          The following command creates a workload source for the specified
          workload identity pool namespace that authorizes any Compute Engine
          instance in the Google Cloud project `123` based on their attached
          service account.


            $ {command} project-123 --location="global" \\
            --workload-identity-pool="my-workload-identity-pool" \\
            --namespace="my-namespace" \\
            --single-attribute-selectors="compute.googleapis.com/Instance.attached_service_account.email='foo@bar.iam.gserviceaccount.com'"
            --allow-identity-self-selection
          """,
  }

  @staticmethod
  def Args(parser):
    workload_source_data = yaml_data.ResourceYAMLData.FromPath(
        'iam.workload_identity_pool_namespace_workload_source'
    )
    # b/295594640: The help text for this command should include what the ID
    # represents and format constraints enforced. Figure out if it's possible
    # to add that information to this parser.
    concept_parsers.ConceptParser.ForResource(
        'workload_source',
        concepts.ResourceSpec.FromYaml(
            workload_source_data.GetData(), is_positional=True
        ),
        'The workload source to create.',
        required=True,
    ).AddToParser(parser)
    # Flags for creating workload source
    parser.add_argument(
        '--single-attribute-selectors',
        type=arg_parsers.ArgList(),
        help=(
            'Attributes that a workload must attest for it to be matched by the'
            ' workload source.'
        ),
        metavar='SINGLE_ATTRIBUTE_SELECTORS',
    )
    parser.add_argument(
        '--allow-identity-self-selection',
        action='store_true',
        help=(
            'Allows matched workloads to request any identity within the'
            ' namespace.'
        ),
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    self.CheckArgs(args)

    client, messages = util.GetClientAndMessages()
    workload_source_ref = args.CONCEPTS.workload_source.Parse()

    workload_source = messages.WorkloadSource()
    workload_source.identityAssignments.append(
        messages.IdentityAssignment(
            singleAttributeSelectors=flags.ParseSingleAttributeSelectorArg(
                arg_name='--single-attribute-selectors',
                arg_value=args.single_attribute_selectors,
            ),
            allowIdentitySelfSelection=args.allow_identity_self_selection,
        )
    )

    lro_ref = client.projects_locations_workloadIdentityPools_namespaces_managedIdentities_workloadSources.Create(
        messages.IamProjectsLocationsWorkloadIdentityPoolsNamespacesManagedIdentitiesWorkloadSourcesCreateRequest(
            parent=workload_source_ref.Parent().RelativeName(),
            workloadSource=workload_source,
            workloadSourceId=workload_source_ref.workloadSourcesId,
        )
    )

    log.status.Print(
        'Create request issued for: [{}]'.format(
            workload_source_ref.workloadSourcesId
        )
    )

    if args.async_:
      return lro_ref

    # Wait for the LRO to complete.
    result = workload_sources.WaitForWorkloadSourceOperation(
        client=client,
        lro_ref=lro_ref,
        for_managed_identity=False,
    )
    log.status.Print(
        'Created workload source [{}].'.format(
            workload_source_ref.workloadSourcesId
        )
    )

    return result

  def CheckArgs(self, args):
    if not args.single_attribute_selectors:
      raise gcloud_exceptions.OneOfArgumentsRequiredException(
          ['--single-attribute-selectors'],
          'Must provide at least one selector that will match workload(s) '
          'from the source.',
      )
    if not args.allow_identity_self_selection:
      raise gcloud_exceptions.OneOfArgumentsRequiredException(
          ['--allow-identity-self-selection'],
          'Must define how workload will be assigned an identity.',
      )
