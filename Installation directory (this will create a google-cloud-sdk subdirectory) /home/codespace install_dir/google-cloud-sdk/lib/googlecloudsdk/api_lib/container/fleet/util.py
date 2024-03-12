# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Fleet API utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from typing import Union

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources
from googlecloudsdk.generated_clients.apis.gkehub.v1 import gkehub_v1_client as ga_client
from googlecloudsdk.generated_clients.apis.gkehub.v1alpha import gkehub_v1alpha_client as alpha_client
from googlecloudsdk.generated_clients.apis.gkehub.v1alpha import gkehub_v1alpha_messages as alpha_messages
from googlecloudsdk.generated_clients.apis.gkehub.v1beta import gkehub_v1beta_client as beta_client


VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1alpha',
    base.ReleaseTrack.BETA: 'v1beta',
    base.ReleaseTrack.GA: 'v1',
}


def GetMessagesModule(release_track=base.ReleaseTrack.GA):
  return apis.GetMessagesModule('gkehub', VERSION_MAP[release_track])


def FleetMessageModule(release_track: base.ReleaseTrack):
  """Dynamically load Fleet message module based on command track.

  Explicitly import message to enable type hint in Cider-V since
  `apis.GetMessagesModule()` cannot derive type to the specific Python module.

  Args:
    release_track: Determines the generated API message module to be returned.

  Returns:
    An API message module that corresponds to the release track.
  """
  if release_track == base.ReleaseTrack.ALPHA:
    return alpha_messages

  raise NotImplementedError(
      'Fleet command has not been promoted to {} track.'.format(
          release_track.name
      )
  )


def GetClientInstance(
    release_track=base.ReleaseTrack.GA,
) -> Union[
    alpha_client.GkehubV1alpha, beta_client.GkehubV1beta, ga_client.GkehubV1
]:
  return apis.GetClientInstance('gkehub', VERSION_MAP[release_track])


def GetClientClass(release_track=base.ReleaseTrack.GA):
  return apis.GetClientClass('gkehub', VERSION_MAP[release_track])


def LocationResourceName(project, location='global'):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Create(
      'gkehub.projects.locations',
      projectsId=project,
      locationsId=location,
  ).RelativeName()


def MembershipLocation(full_name):
  matches = re.search('projects/.*/locations/(.*)/memberships/(.*)', full_name)
  if matches:
    return matches.group(1)
  raise exceptions.Error(
      'Invalid membership resource name: {}'.format(full_name)
  )


def MembershipResourceName(project, membership, location='global'):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Create(
      'gkehub.projects.locations.memberships',
      projectsId=project,
      locationsId=location,
      membershipsId=membership,
  ).RelativeName()


def MembershipPartialName(full_name):
  matches = re.search('projects/.*/locations/(.*)/memberships/(.*)', full_name)
  if matches:
    return matches.group(1) + '/' + matches.group(2)
  raise exceptions.Error(
      'Invalid membership resource name: {}'.format(full_name)
  )


def MembershipShortname(full_name):
  return resources.REGISTRY.ParseRelativeName(
      full_name, collection='gkehub.projects.locations.memberships'
  ).Name()


def FeatureResourceName(project, feature, location='global'):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Create(
      'gkehub.projects.locations.features',
      projectsId=project,
      locationsId=location,
      featuresId=feature,
  ).RelativeName()


def OperationResourceName(project, operation, location='global'):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Create(
      'gkehub.projects.locations.operations',
      projectsId=project,
      locationsId=location,
      operationsId=operation,
  ).RelativeName()


def FleetRef(
    project,
    fleet='default',
    location='global',
    release_track=base.ReleaseTrack.ALPHA,
) -> resources.Resource:
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': location,
          'fleetsId': fleet,
      },
      collection='gkehub.projects.locations.fleets',
      api_version=VERSION_MAP[release_track],
  )


def FleetResourceName(
    project,
    fleet='default',
    location='global',
    release_track=base.ReleaseTrack.ALPHA,
) -> str:
  # See command_lib/container/fleet/resources.yaml
  return FleetRef(project, fleet, location, release_track).RelativeName()


def FleetParentName(
    project, location='global', release_track=base.ReleaseTrack.ALPHA
):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': location,
      },
      collection='gkehub.projects.locations',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def FleetOrgParentName(organization, location='global'):
  return 'organizations/{0}/locations/{1}'.format(organization, location)


def ScopeParentName(project, release_track=base.ReleaseTrack.ALPHA):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': 'global',
      },
      collection='gkehub.projects.locations',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def NamespaceParentName(project, release_track=base.ReleaseTrack.ALPHA):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': 'global',
      },
      collection='gkehub.projects.locations',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def NamespaceResourceName(project, name, release_track=base.ReleaseTrack.ALPHA):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': 'global',
          'namespacesId': name,
      },
      collection='gkehub.projects.locations.namespaces',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def ScopeNamespaceParentName(
    project, scope, release_track=base.ReleaseTrack.ALPHA
):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': 'global',
          'scopesId': scope,
      },
      collection='gkehub.projects.locations.scopes',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def ScopeNamespaceResourceName(
    project, scope, name, release_track=base.ReleaseTrack.ALPHA
):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': 'global',
          'scopesId': scope,
          'namespacesId': name,
      },
      collection='gkehub.projects.locations.scopes.namespaces',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def RBACRoleBindingParentName(
    project, namespace, release_track=base.ReleaseTrack.ALPHA
):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': 'global',
          'namespacesId': namespace,
      },
      collection='gkehub.projects.locations.namespaces',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def ScopeRBACRoleBindingParentName(
    project, scope, release_track=base.ReleaseTrack.ALPHA
):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': 'global',
          'scopesId': scope,
      },
      collection='gkehub.projects.locations.scopes',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def RBACRoleBindingResourceName(
    project, namespace, name, release_track=base.ReleaseTrack.ALPHA
):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': 'global',
          'namespacesId': namespace,
          'rbacrolebindingsId': name,
      },
      collection='gkehub.projects.locations.namespaces.rbacrolebindings',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def ScopeRBACRoleBindingResourceName(
    project, scope, name, release_track=base.ReleaseTrack.ALPHA
):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': 'global',
          'scopesId': scope,
          'rbacrolebindingsId': name,
      },
      collection='gkehub.projects.locations.scopes.rbacrolebindings',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def MembershipRBACRoleBindingResourceName(
    project, location, membership, name, release_track=base.ReleaseTrack.ALPHA
):
  """Parses a Membership RBAC Role Binding resource.

  Args:
    project: the full project ID or number for the resource.
    location: the location of the resource.
    membership: the parent membership of the resource.
    name: the resource name for the role binding.
    release_track: the API version for the resource parsing.

  Returns:
    A Membership RBAC Role Binding resource.
  """
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': location,
          'membershipsId': membership,
          'rbacrolebindingsId': name,
      },
      collection='gkehub.projects.locations.memberships.rbacrolebindings',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def MembershipBindingResourceName(
    project,
    name,
    membership,
    location='global',
    release_track=base.ReleaseTrack.GA,
):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': location,
          'membershipsId': membership,
          'bindingsId': name,
      },
      collection='gkehub.projects.locations.memberships.bindings',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def MembershipBindingParentName(
    project, membership, location='global', release_track=base.ReleaseTrack.GA
):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Parse(
      line=None,
      params={
          'projectsId': project,
          'locationsId': location,
          'membershipsId': membership,
      },
      collection='gkehub.projects.locations.memberships',
      api_version=VERSION_MAP[release_track],
  ).RelativeName()


def ScopeResourceName(project, scope, location='global'):
  # See command_lib/container/fleet/resources.yaml
  return resources.REGISTRY.Create(
      'gkehub.projects.locations.scopes',
      projectsId=project,
      locationsId=location,
      scopesId=scope,
  ).RelativeName()


def OperationRef(operation: alpha_messages.Operation) -> resources.Resource:
  """Parses a gkehub Operation reference from an operation."""
  return resources.REGISTRY.ParseRelativeName(
      operation.name, collection='gkehub.projects.locations.operations'
  )


def RolloutRef(args: parser_extensions.Namespace) -> resources.Resource:
  if getattr(args.CONCEPTS, 'rollout', None):
    return args.CONCEPTS.rollout.Parse()


def RolloutName(args: parser_extensions.Namespace) -> str:
  rollout_ref = RolloutRef(args)
  if rollout_ref:
    return rollout_ref.RelativeName()
  return None


def RolloutParentName(args: parser_extensions.Namespace):
  rollout_ref = RolloutRef(args)
  if rollout_ref:
    return rollout_ref.Parent().RelativeName()
  return None


def RolloutId(args: parser_extensions.Namespace) -> str:
  rollout_ref = RolloutRef(args)
  if rollout_ref:
    return rollout_ref.Name()
  return None
