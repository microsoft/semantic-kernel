# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""`gcloud access-context-manager zones update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import zones as zones_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import perimeters
from googlecloudsdk.command_lib.accesscontextmanager import policies
from googlecloudsdk.command_lib.util.args import repeated


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class UpdatePerimetersGA(base.UpdateCommand):
  """Update an existing access zone."""
  _INCLUDE_UNRESTRICTED = False
  _API_VERSION = 'v1'

  @staticmethod
  def Args(parser):
    UpdatePerimetersGA.ArgsVersioned(parser, version='v1')

  @staticmethod
  def ArgsVersioned(parser, version='v1'):
    perimeters.AddResourceArg(parser, 'to update')
    perimeters.AddPerimeterUpdateArgs(parser, version=version)

  def Run(self, args):
    client = zones_api.Client(version=self._API_VERSION)
    perimeter_ref = args.CONCEPTS.perimeter.Parse()
    result = repeated.CachedResult.FromFunc(client.Get, perimeter_ref)
    policies.ValidateAccessPolicyArg(perimeter_ref, args)

    return self.Patch(
        client=client,
        args=args,
        result=result,
        perimeter_ref=perimeter_ref,
        description=args.description,
        title=args.title,
        perimeter_type=perimeters.GetTypeEnumMapper(
            version=self._API_VERSION).GetEnumForChoice(args.type),
        resources=perimeters.ParseResources(args, result),
        restricted_services=perimeters.ParseRestrictedServices(args, result),
        levels=perimeters.ParseLevels(args, result,
                                      perimeter_ref.accessPoliciesId),
        vpc_allowed_services=perimeters.ParseVpcRestriction(
            args, result, self._API_VERSION),
        enable_vpc_accessible_services=args.enable_vpc_accessible_services,
        ingress_policies=perimeters.ParseUpdateDirectionalPoliciesArgs(
            args, 'ingress-policies'),
        egress_policies=perimeters.ParseUpdateDirectionalPoliciesArgs(
            args, 'egress-policies'))

  def Patch(self, client, args, result, perimeter_ref, description, title,
            perimeter_type, resources, restricted_services, levels,
            vpc_allowed_services, enable_vpc_accessible_services,
            ingress_policies, egress_policies):
    return client.Patch(
        perimeter_ref,
        description=description,
        title=title,
        perimeter_type=perimeter_type,
        resources=resources,
        restricted_services=restricted_services,
        levels=levels,
        vpc_allowed_services=vpc_allowed_services,
        enable_vpc_accessible_services=enable_vpc_accessible_services,
        ingress_policies=ingress_policies,
        egress_policies=egress_policies)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdatePerimetersAlpha(UpdatePerimetersGA):
  """Update an existing access zone."""
  _INCLUDE_UNRESTRICTED = False
  _API_VERSION = 'v1alpha'

  @staticmethod
  def Args(parser):
    UpdatePerimetersGA.ArgsVersioned(parser, version='v1alpha')


detailed_help = {
    'brief':
        'Update the enforced configuration for an existing Service Perimeter.',
    'DESCRIPTION':
        ('This command updates the enforced configuration (`status`) of a '
         'Service Perimeter.'),
    'EXAMPLES':
        ('To update the enforced configuration for a Service Perimeter:\n\n'
         '  $ {command} my-perimeter '
         '--add-resources="projects/123,projects/456" '
         '--remove-restricted-services="storage.googleapis.com" '
         '--add-access-levels="accessPolicies/123/accessLevels/a_level" '
         '--enable-vpc-accessible-services '
         '--clear-vpc-allowed-services')
}

UpdatePerimetersGA.detailed_help = detailed_help
UpdatePerimetersAlpha.detailed_help = detailed_help
