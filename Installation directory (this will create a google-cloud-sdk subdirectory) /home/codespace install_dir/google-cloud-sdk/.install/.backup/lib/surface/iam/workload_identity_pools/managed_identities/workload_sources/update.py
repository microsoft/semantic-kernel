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
  """Update a workload source for a workload identity pool managed identity."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          The following command matches Compute Instances within the
          Google Cloud project 123 based on their attached service account.

            $ {command} project-123 --location="global" \
            --workload-identity-pool="my-workload-identity-pool" \
            --namespace="my-namespace" \
            --managed-identity="my-managed-identity" \
            --add-single-attribute-selectors="compute.googleapis.com/Instance.attached_service_account.email='foo@bar.iam.gserviceaccount.com'"

          The following command stops matching Compute Instances within the
          Google Cloud project 123 based on their attached service account.

            $ {command} project-123 --location="global" \
            --workload-identity-pool="my-workload-identity-pool" \
            --namespace="my-namespace" \
            --managed-identity="my-managed-identity" \
            --remove-single-attribute-selectors="compute.googleapis.com/Instance.attached_service_account.email='foo@bar.iam.gserviceaccount.com'"
          """,
  }

  @staticmethod
  def Args(parser):
    workload_source_data = yaml_data.ResourceYAMLData.FromPath(
        'iam.workload_identity_pool_managed_identity_workload_source'
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
            'Add an attribute that a workload can attest for it to be allowed '
            'to receive a managed identity.'
        ),
        metavar='SINGLE_ATTRIBUTE_SELECTORS',
    )
    parser.add_argument(
        '--add-single-attribute-selectors',
        type=arg_parsers.ArgList(),
        help=(
            'Add an attribute that a workload can attest for it to be allowed '
            'to receive a managed identity.'
        ),
        metavar='SINGLE_ATTRIBUTE_SELECTOR',
    )
    parser.add_argument(
        '--remove-single-attribute-selectors',
        type=arg_parsers.ArgList(),
        help=(
            'Removes an attribute that a workload can attest for it to be '
            'allowed to receive a managed identity.'
        ),
        metavar='SINGLE_ATTRIBUTE_SELECTOR',
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    self.CheckArgs(args)

    client, messages = util.GetClientAndMessages()
    workload_source_ref = args.CONCEPTS.workload_source.Parse()

    # Maybe replace the full set of selectors.
    if args.single_attribute_selectors:
      workload_source = messages.WorkloadSource(
          name=workload_source_ref.RelativeName(),
          singleAttributeSelectors=flags.ParseSingleAttributeSelectorArg(
              '--single-attribute-selectors',
              args.single_attribute_selectors,
          ),
      )
    else:
      # If we're doing incremental adds/removes then we need to call the server
      # first to fetch the current set of selectors.
      workload_source = client.projects_locations_workloadIdentityPools_namespaces_workloadSources.Get(
          messages.IamProjectsLocationsWorkloadIdentityPoolsNamespacesWorkloadSourcesGetRequest(
              name=workload_source_ref.RelativeName()
          )
      )
      updated_selector_list = self.ReconcileSingleAttributeSelectorList(
          args, workload_source.singleAttributeSelectors
      )
      workload_source.singleAttributeSelectors.clear()
      workload_source.singleAttributeSelectors.extend(updated_selector_list)

    lro_ref = client.projects_locations_workloadIdentityPools_namespaces_managedIdentities_workloadSources.Patch(
        messages.IamProjectsLocationsWorkloadIdentityPoolsNamespacesManagedIdentitiesWorkloadSourcesPatchRequest(
            name=workload_source.name,
            workloadSource=workload_source,
            updateMask='single_attribute_selectors',
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
        for_managed_identity=True,
    )
    log.status.Print(
        'Updated workload source [{}].'.format(
            workload_source_ref.workloadSourcesId
        )
    )
    return result

  def CheckArgs(self, args):
    if (
        not args.add_single_attribute_selectors
        and not args.remove_single_attribute_selectors
        and not args.single_attribute_selectors
    ):
      raise gcloud_exceptions.OneOfArgumentsRequiredException(
          [
              '--single-attribute-selectors',
              '--add-single-attribute-selectors',
              '--remove-attribute-selectors',
          ],
          'Must add or remove at least one selector that will match workload(s)'
          ' from the source.',
      )

  def ReconcileSingleAttributeSelectorList(self, args, original_selector_list):
    updated_selectors = set()

    # Add all existing selectors
    updated_selectors.update(
        map(self.ToHashableSelector, original_selector_list)
    )

    # Add single attribute selectors
    if args.add_single_attribute_selectors:
      updated_selectors.update(
          map(
              self.ToHashableSelector,
              flags.ParseSingleAttributeSelectorArg(
                  '--add-single-attribute-selectors',
                  args.add_single_attribute_selectors,
              ),
          )
      )

    # Remove single attribute selectors
    if args.remove_single_attribute_selectors:
      for selector in map(
          self.ToHashableSelector,
          flags.ParseSingleAttributeSelectorArg(
              '--remove-single-attribute-selectors',
              args.remove_single_attribute_selectors,
          ),
      ):
        updated_selectors.discard(selector)

    # Covert to proto and return
    return sorted(
        list(map(self.ToProtoSelector, updated_selectors)),
        # Sort results to guarantee stable results across platforms and versions
        key=operator.attrgetter('attribute', 'value'),
    )

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
