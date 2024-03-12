# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Flags for gcloud active-directory commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.active_directory import exceptions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers

VALID_REGIONS = [
    'asia-east1', 'asia-northeast1', 'asia-south1', 'asia-southeast1',
    'australia-southeast1', 'europe-north1', 'europe-west1', 'europe-west2',
    'europe-west3', 'europe-west4', 'northamerica-northeast1',
    'southamerica-east1', 'us-central1', 'us-east1', 'us-east4', 'us-west1',
    'us-west2'
]


def GetOperationResourceSpec():
  """Adds an operation resource spec."""
  return concepts.ResourceSpec(
      'managedidentities.projects.locations.global.operations',
      resource_name='operation',
      disable_auto_completers=False,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      operationsId=OperationAttributeConfig(),
  )


def OperationAttributeConfig():
  """Adds an operation attribute config."""
  return concepts.ResourceParameterAttributeConfig(
      name='operation',
      help_text='Name of the Managed Microsoft AD operation.',
  )


def AddOperationResourceArg(parser, verb, positional=True):
  """Adds an operation resource argument.

  NOTE: May be used only if it's the only resource arg in the command.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the instance ID is a positional rather
      than a flag.
  """
  name = 'NAME' if positional else '--operation'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetOperationResourceSpec(),
      'The operation name {}.'.format(verb),
      required=True).AddToParser(parser)


# Flags for update domain.
def AddRegionFlag(unused_domain_ref, args, patch_request):
  """Adds region to domain."""
  if args.IsSpecified('add_region'):
    locs = patch_request.domain.locations + [args.add_region]
    locs = sorted(set(locs))
    patch_request.domain.locations = locs
    AddFieldToUpdateMask('locations', patch_request)
  return patch_request


def RemoveRegionFlag(unused_domain_ref, args, patch_request):
  """Removes region from domain."""
  if args.IsSpecified('remove_region'):
    locs = [
        loc for loc in patch_request.domain.locations
        if loc != args.remove_region
    ]
    locs = sorted(set(locs))
    if not locs:
      raise exceptions.ActiveDirectoryError('Cannot remove all regions')
    patch_request.domain.locations = locs
    AddFieldToUpdateMask('locations', patch_request)
  return patch_request


def AddAuthorizedNetworksFlag(unused_domain_ref, args, patch_request):
  """Adds authorized networks to domain."""
  if args.IsSpecified('add_authorized_networks'):
    ans = patch_request.domain.authorizedNetworks + args.add_authorized_networks
    ans = sorted(set(ans))
    patch_request.domain.authorizedNetworks = ans
    AddFieldToUpdateMask('authorized_networks', patch_request)
  return patch_request


def RemoveAuthorizedNetworksFlag(unused_domain_ref, args, patch_request):
  """Removes authorized networks from domain."""
  if args.IsSpecified('remove_authorized_networks'):
    ans = [
        an for an in patch_request.domain.authorizedNetworks
        if an not in args.remove_authorized_networks
    ]
    ans = sorted(set(ans))
    patch_request.domain.authorizedNetworks = ans
    AddFieldToUpdateMask('authorized_networks', patch_request)
  return patch_request


def UpdateAuditLogsEnabled(unused_domain_ref, args, patch_request):
  """Updates audit logs config for the domain."""
  if args.IsSpecified('enable_audit_logs'):
    patch_request.domain.auditLogsEnabled = args.enable_audit_logs
    AddFieldToUpdateMask('audit_logs_enabled', patch_request)
  return patch_request


def AddFieldToUpdateMask(field, patch_request):
  """Adds name of field to update mask."""
  update_mask = patch_request.updateMask
  if update_mask:
    if update_mask.count(field) == 0:
      patch_request.updateMask = update_mask + ',' + field
  else:
    patch_request.updateMask = field
  return patch_request


def AdditionalDomainUpdateArguments():
  """Adds all update domain arguments."""
  return DomainUpdateLabelsFlags() + [RegionUpdateFlags(), AuthNetUpdateFlags()]


def RegionUpdateFlags():
  """Defines flags for updating regions."""
  region_group = base.ArgumentGroup(mutex=True)
  region_group.AddArgument(DomainAddRegionFlag())
  region_group.AddArgument(DomainRemoveRegionFlag())
  return region_group


def AuthNetUpdateFlags():
  """Defines flags for updating authorized networks."""
  auth_net_group = base.ArgumentGroup(mutex=True)
  auth_net_group.AddArgument(DomainAddAuthorizedNetworksFlag())
  auth_net_group.AddArgument(DomainRemoveAuthorizedNetworksFlag())
  return auth_net_group


def DomainUpdateLabelsFlags():
  """Defines flags for updating labels."""
  remove_group = base.ArgumentGroup(mutex=True)
  remove_group.AddArgument(labels_util.GetClearLabelsFlag())
  remove_group.AddArgument(labels_util.GetRemoveLabelsFlag(''))
  return [labels_util.GetUpdateLabelsFlag(''), remove_group]


def PeeringUpdateLabelsFlags():
  """Defines flags for updating labels."""
  remove_group = base.ArgumentGroup(mutex=True)
  remove_group.AddArgument(labels_util.GetClearLabelsFlag())
  remove_group.AddArgument(labels_util.GetRemoveLabelsFlag(''))
  return [labels_util.GetUpdateLabelsFlag(''), remove_group]


def BackupUpdateLabelsFlags():
  """Defines flags for updating labels."""
  remove_group = base.ArgumentGroup(mutex=True)
  remove_group.AddArgument(labels_util.GetClearLabelsFlag())
  remove_group.AddArgument(labels_util.GetRemoveLabelsFlag(''))
  return [labels_util.GetUpdateLabelsFlag(''), remove_group]


def RegionsType(value):
  """Defines valid GCP regions."""
  return arg_parsers.ArgList(choices=VALID_REGIONS)(value)


def DomainAddRegionFlag():
  """Defines a flag for adding a region."""
  return base.Argument(
      '--add-region',
      help="""\
      An additional region to provision this domain in.
      If domain is already provisioned in region, nothing will be done in that
      region. Supported regions are: {}.
      """.format(', '.join(VALID_REGIONS)))


def DomainRemoveRegionFlag():
  """Defines a flag for removing a region."""
  return base.Argument(
      '--remove-region',
      help="""\
      A region to de-provision this domain from.
      If domain is already not provisioned in a region, nothing will be done in
      that region. Domains must be left provisioned in at least one region.
      Supported regions are: {}.
      """.format(', '.join(VALID_REGIONS)))


def DomainAddAuthorizedNetworksFlag():
  """Defines a flag for adding an authorized network."""
  return base.Argument(
      '--add-authorized-networks',
      metavar='AUTH_NET1, AUTH_NET2, ...',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help="""\
       A list of URLs of additional networks to peer this domain to in the form
       projects/{project}/global/networks/{network}.
       Networks must belong to the project.
      """)


def DomainRemoveAuthorizedNetworksFlag():
  """Defines a flag for removing an authorized network."""
  return base.Argument(
      '--remove-authorized-networks',
      metavar='AUTH_NET1, AUTH_NET2, ...',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help="""\
       A list of URLs of additional networks to unpeer this domain from in the
       form projects/{project}/global/networks/{network}.
       Networks must belong to the project.
      """)
