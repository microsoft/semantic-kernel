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
"""Command to update a workload source under a workload identity pool managed identity."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import operator

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


class Update(base.UpdateCommand):
  """Update a workload source for a workload identity pool namespace."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          The following command matches Compute Engine instances within the
          Google Cloud project 123 based on their attached service account.

            $ {command} project-123 --location="global" \
            --workload-identity-pool="my-workload-identity-pool" \
            --namespace="my-namespace" \
            --single-attribute-selectors="compute.googleapis.com/Instance.attached_service_account.email='foo@bar.iam.gserviceaccount.com'"
            --allow-identity-self-selection

          The following command stops matching Compute Engine instances within
          the Google Cloud project 123 based on their attached service account.

            $ {command} project-123 --location="global" \
            --workload-identity-pool="my-workload-identity-pool" \
            --namespace="my-namespace" \
            --single-attribute-selectors="compute.googleapis.com/Instance.attached_service_account.email='foo@bar.iam.gserviceaccount.com'"
            --no-allow-identity-self-selection
          """,
  }

  @staticmethod
  def Args(parser):
    workload_source_data = yaml_data.ResourceYAMLData.FromPath(
        'iam.workload_identity_pool_namespace_workload_source'
    )
    concept_parsers.ConceptParser.ForResource(
        'workload_source',
        concepts.ResourceSpec.FromYaml(
            workload_source_data.GetData(), is_positional=True
        ),
        'The workload source to update.',
        required=True,
    ).AddToParser(parser)
    # Flags for updating workload source
    parser.add_argument(
        '--single-attribute-selectors',
        type=arg_parsers.ArgList(),
        help=(
            'An attribute that a workload can attest for it to be allow to '
            'receive a managed identity.'
        ),
        metavar='SINGLE_ATTRIBUTE_SELECTORS',
    )
    parser.add_argument(
        '--allow-identity-self-selection',
        action=arg_parsers.StoreTrueFalseAction,
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

    # Read current workload source from storage
    workload_source = client.projects_locations_workloadIdentityPools_namespaces_workloadSources.Get(
        messages.IamProjectsLocationsWorkloadIdentityPoolsNamespacesWorkloadSourcesGetRequest(
            name=workload_source_ref.RelativeName()
        )
    )

    # Reconcile the list of adds and deletes
    reconciled_identity_assignment_list = self.ReconcileIdentityAssignments(
        args, workload_source.identityAssignments
    )
    workload_source.identityAssignments.clear()
    workload_source.identityAssignments.extend(
        reconciled_identity_assignment_list
    )

    # Write back the updated workload source
    lro_ref = client.projects_locations_workloadIdentityPools_namespaces_workloadSources.Patch(
        messages.IamProjectsLocationsWorkloadIdentityPoolsNamespacesWorkloadSourcesPatchRequest(
            name=workload_source.name,
            workloadSource=workload_source,
            updateMask='identity_assignments',
        )
    )
    log.status.Print(
        'Update request issued for: [{}]'.format(
            workload_source_ref.workloadSourcesId
        )
    )

    if args.async_:
      return lro_ref

    # Wait for the LRO to complete.
    result = workload_sources.WaitForWorkloadSourceOperation(
        client=client,
        lro_ref=lro_ref,
    )
    log.status.Print(
        'Updated workload source [{}].'.format(
            workload_source_ref.workloadSourcesId
        )
    )

    return result

  def CheckArgs(self, args):
    if not args.single_attribute_selectors:
      raise gcloud_exceptions.OneOfArgumentsRequiredException(
          ['--single-attribute-selectors'],
          'Must provide at least one selector that will match workload(s)'
          ' from the source.',
      )
    if args.allow_identity_self_selection is None:
      raise gcloud_exceptions.OneOfArgumentsRequiredException(
          ['--[no-]allow-identity-self-selection'],
          'Must add or remove at least one identity assignment.',
      )

  def ReconcileIdentityAssignments(self, args, original_identity_assignments):
    """Reconciles the identity assignment changes with the original list."""
    _, messages = util.GetClientAndMessages()
    updated_selectors = set()

    # Add all existing selectors
    for identity_assignment in original_identity_assignments:
      updated_selectors.update(
          map(
              self.ToHashableSelector,
              identity_assignment.singleAttributeSelectors,
          )
      )

    if args.allow_identity_self_selection is not None:
      hashable_selectors = set(
          map(
              self.ToHashableSelector,
              flags.ParseSingleAttributeSelectorArg(
                  '--single-attribute-selectors',
                  args.single_attribute_selectors,
              ),
          )
      )
      # Add single attribute selectors
      if args.allow_identity_self_selection:
        updated_selectors |= hashable_selectors
      # Remove single attribute selectors
      else:
        updated_selectors -= hashable_selectors

    if updated_selectors == set():
      return []

    # Convert to proto and return
    identity_assignment_proto = messages.IdentityAssignment()
    identity_assignment_proto.singleAttributeSelectors.extend(
        sorted(
            list(map(self.ToProtoSelector, updated_selectors)),
            # Sort results to guarantee stable results across platforms and
            # versions
            key=operator.attrgetter('attribute', 'value'),
        )
    )
    # The only values left in updated_selectors are ones where
    # allow_identity_self_selection is true.
    identity_assignment_proto.allowIdentitySelfSelection = True
    return [identity_assignment_proto]

  def ToHashableSelector(self, proto_selector):
    """Converts the given SingleAttributeSelector proto into a hashable type."""
    return tuple([proto_selector.attribute, proto_selector.value])

  def ToProtoSelector(self, hashable_selector):
    """Converts the given hashable SingleAttributeSelector into a proto."""
    _, messages = util.GetClientAndMessages()
    return messages.SingleAttributeSelector(
        attribute=hashable_selector[0],
        value=hashable_selector[1],
    )
