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
"""Base classes for [enable|disable|describe] commands for Feature resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import exceptions as core_api_exceptions
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.container.fleet import api_util
from googlecloudsdk.command_lib.container.fleet import base as hub_base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import info
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import retry


class FeatureCommand(hub_base.HubCommand):
  """FeatureCommand is a mixin adding common utils to the Feature commands."""
  feature_name = ''  # Derived commands should set this to their Feature.

  @property
  def feature(self):
    """The Feature info entry for this command's Feature."""
    return info.Get(self.feature_name)

  def FeatureResourceName(self, project=None):
    """Builds the full resource name, using the core project property if no project is specified."""
    return super(FeatureCommand,
                 self).FeatureResourceName(self.feature_name, project)

  def FeatureNotEnabledError(self, project=None):
    """Constructs a new Error for reporting when this Feature is not enabled."""
    project = project or properties.VALUES.core.project.GetOrFail()
    return exceptions.Error('{} Feature for project [{}] is not enabled'.format(
        self.feature.display_name, project))

  def NotAuthorizedError(self, project=None):
    """Constructs a new Error for reporting when accessing this Feature is not authorized."""
    project = project or properties.VALUES.core.project.GetOrFail()
    return exceptions.Error(
        'Not authorized to access {} Feature for project [{}]'.format(
            self.feature.display_name, project))

  def GetFeature(self, project=None):
    """Fetch this command's Feature from the API, handling common errors."""
    try:
      return self.hubclient.GetFeature(self.FeatureResourceName(project))
    except apitools_exceptions.HttpNotFoundError:
      raise self.FeatureNotEnabledError(project)
    except apitools_exceptions.HttpUnauthorizedError:
      raise self.NotAuthorizedError(project)


class EnableCommandMixin(FeatureCommand):
  """A mixin for functionality to enable a Feature."""

  def Enable(self, feature):
    project = properties.VALUES.core.project.GetOrFail()
    if self.feature.api:
      enable_api.EnableServiceIfDisabled(project, self.feature.api)
    parent = util.LocationResourceName(project)
    try:
      # Retry if we still get "API not activated"; it can take a few minutes
      # for Chemist to catch up. See b/28800908.
      # TODO(b/177098463): Add a spinner here?
      retryer = retry.Retryer(max_retrials=4, exponential_sleep_multiplier=1.75)
      op = retryer.RetryOnException(
          self.hubclient.CreateFeature,
          args=(parent, self.feature_name, feature),
          should_retry_if=self._FeatureAPINotEnabled,
          sleep_ms=1000)
    except retry.MaxRetrialsException:
      raise exceptions.Error(
          'Retry limit exceeded waiting for {} to enable'.format(
              self.feature.display_name))
    except apitools_exceptions.HttpConflictError as e:
      # If the error is not due to the object already existing, re-raise.
      error = core_api_exceptions.HttpErrorPayload(e)
      if error.status_description != 'ALREADY_EXISTS':
        raise
      # TODO(b/177098463): Decide if this should be a hard error if a spec was
      # set, but not applied, because the Feature already existed.
      log.status.Print('{} Feature for project [{}] is already enabled'.format(
          self.feature.display_name, project))
      return
    msg = 'Waiting for Feature {} to be created'.format(
        self.feature.display_name)
    return self.WaitForHubOp(self.hubclient.feature_waiter, op=op, message=msg)

  def _FeatureAPINotEnabled(self, exc_type, exc_value, traceback, state):
    del traceback, state  # Unused
    if not self.feature.api:
      return False
    if exc_type != apitools_exceptions.HttpBadRequestError:
      return False
    error = core_api_exceptions.HttpErrorPayload(exc_value)
    # TODO(b/188807249): Add a reference to this error in the error package.
    if not (error.status_description == 'FAILED_PRECONDITION' and
            self.feature.api in error.message and
            'is not enabled' in error.message):
      return False
    log.status.Print('Waiting for service API enablement to finish...')
    return True


class EnableCommand(EnableCommandMixin, calliope_base.CreateCommand):
  """Base class for the command that enables a Feature."""

  def Run(self, args):
    return self.Enable(self.messages.Feature())


class DisableCommand(FeatureCommand, calliope_base.DeleteCommand):
  """Base class for the command that disables a Feature."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--force',
        action='store_true',
        help='Disable this feature, even if it is currently in use. '
        'Force disablement may result in unexpected behavior.')

  def Run(self, args):
    return self.Disable(args.force)

  def Disable(self, force):
    try:
      op = self.hubclient.DeleteFeature(self.FeatureResourceName(), force=force)
    except apitools_exceptions.HttpNotFoundError:
      return  # Already disabled.
    message = 'Waiting for Feature {} to be deleted'.format(
        self.feature.display_name)
    self.WaitForHubOp(
        self.hubclient.resourceless_waiter, op, message=message, warnings=False)


class DescribeCommand(FeatureCommand, calliope_base.DescribeCommand):
  """Base class for the command that describes the status of a Feature."""

  def Run(self, args):
    return self.GetFeature()


class UpdateCommandMixin(FeatureCommand):
  """A mixin for functionality to update a Feature."""

  def Update(self, mask, patch):
    """Update provides common API, display, and error handling logic."""
    try:
      op = self.hubclient.UpdateFeature(self.FeatureResourceName(), mask, patch)
    except apitools_exceptions.HttpNotFoundError:
      raise self.FeatureNotEnabledError()

    msg = 'Waiting for Feature {} to be updated'.format(
        self.feature.display_name)
    # TODO(b/177098463): Update all downstream tests to handle warnings.
    return self.WaitForHubOp(
        self.hubclient.feature_waiter, op, message=msg, warnings=False
    )


class UpdateCommand(UpdateCommandMixin, calliope_base.UpdateCommand):
  """Base class for the command that updates a Feature.

  Because Features updates are often bespoke actions, there is no default
  `Run` override like some of the other classes.
  """


def ParseMembership(args,
                    prompt=False,
                    autoselect=False,
                    search=False,
                    flag_override=''):
  """Returns a membership on which to run the command, given the arguments.

  Allows for a `--membership` flag or a `MEMBERSHIP_NAME` positional flag.

  Args:
    args: object containing arguments passed as flags with the command
    prompt: whether to prompt in console for a membership when none are provided
      in args
    autoselect: if no membership is provided and only one exists,
      automatically use that one
    search: whether to search for the membership and error if it does not exist
      (not recommended)
    flag_override: to use a custom membership flag name

  Returns:
    membership: A membership resource name string

  Raises:
    exceptions.Error: no memberships were found or memberships are invalid
    calliope_exceptions.RequiredArgumentException: membership was not provided
  """

  # If a membership is provided
  if args.IsKnownAndSpecified('membership') or args.IsKnownAndSpecified(
      'MEMBERSHIP_NAME') or args.IsKnownAndSpecified(flag_override):
    if resources.MembershipLocationSpecified(args,
                                             flag_override) or not search:
      return resources.MembershipResourceName(args, flag_override)
    else:
      return resources.SearchMembershipResource(
          args, flag_override, filter_cluster_missing=True)

  # If nothing is provided
  if not prompt and not autoselect:
    raise MembershipRequiredError(args, flag_override)

  all_memberships, unreachable = api_util.ListMembershipsFull(
      filter_cluster_missing=True)
  if unreachable:
    raise exceptions.Error(
        ('Locations {} are currently unreachable. Please specify '
         'memberships using `--location` or the full resource name '
         '(projects/*/locations/*/memberships/*)').format(unreachable))
  if autoselect and len(all_memberships) == 1:
    log.status.Print('Selecting membership [{}].'.format(all_memberships[0]))
    return all_memberships[0]
  if prompt:
    membership = resources.PromptForMembership(all_memberships)
    if membership is not None:
      return membership
  raise MembershipRequiredError(args, flag_override)


def ParseMembershipsPlural(args,
                           prompt=False,
                           prompt_cancel=True,
                           autoselect=False,
                           allow_cross_project=False,
                           search=False):
  """Parses a list of membership resources from args.

  Allows for a `--memberships` flag and a `--all-memberships` flag.

  Args:
    args: object containing arguments passed as flags with the command
    prompt: whether to prompt in console for a membership when none are provided
      in args
    prompt_cancel: whether to include a 'cancel' option in the prompt
    autoselect: if no memberships are provided and only one exists,
      automatically use that one
    allow_cross_project: whether to allow memberships from different projects
    search: whether to check that the membership exists in the fleet

  Returns:
    memberships: A list of membership resource name strings

  Raises:
    exceptions.Error if no memberships were found or memberships are invalid
    calliope_exceptions.RequiredArgumentException if membership was not provided
  """
  memberships = []

  # If running for all memberships
  if hasattr(args, 'all_memberships') and args.all_memberships:
    all_memberships, unreachable = api_util.ListMembershipsFull(
        filter_cluster_missing=True)
    if unreachable:
      raise exceptions.Error(
          'Locations {} are currently unreachable. Please try again or '
          'specify memberships for this command.'.format(unreachable))
    if not all_memberships:
      raise exceptions.Error('No Memberships available in the fleet.')
    return all_memberships

  # If a membership list is provided
  if args.IsKnownAndSpecified('memberships'):
    if resources.MembershipLocationSpecified(args):
      memberships += resources.PluralMembershipsResourceNames(args)
      if search:
        for membership in memberships:
          if not api_util.GetMembership(membership):
            raise exceptions.Error(
                'Membership {} does not exist in the fleet.'.format(membership))

      if not allow_cross_project and len(
          resources.GetMembershipProjects(memberships)) > 1:
        raise CrossProjectError(resources.GetMembershipProjects(memberships))

    else:
      memberships += resources.SearchMembershipResourcesPlural(
          args, filter_cluster_missing=True)

  if memberships:
    return memberships

  # If nothing is provided
  if not prompt and not autoselect:
    raise MembershipRequiredError(args)

  all_memberships, unreachable = api_util.ListMembershipsFull(
      filter_cluster_missing=True)
  if unreachable:
    raise exceptions.Error(
        ('Locations {} are currently unreachable. Please specify '
         'memberships using `--location` or the full resource name '
         '(projects/*/locations/*/memberships/*)').format(unreachable))
  if autoselect and len(all_memberships) == 1:
    log.status.Print('Selecting membership [{}].'.format(all_memberships[0]))
    return [all_memberships[0]]
  if prompt:
    membership = resources.PromptForMembership(cancel=prompt_cancel)
    if membership:
      memberships.append(membership)
    return memberships
  raise MembershipRequiredError(args)


# This should not be used in the future and only exists to support deprecated
# commands until they are deleted
def ListMemberships():
  """Lists Membership IDs in the fleet for the current project.

  Returns:
    A list of Membership resource IDs in the fleet.
  """
  client = core_apis.GetClientInstance('gkehub', 'v1beta1')
  response = client.projects_locations_memberships.List(
      client.MESSAGES_MODULE.GkehubProjectsLocationsMembershipsListRequest(
          parent=hub_base.HubCommand.LocationResourceName()))

  return [
      util.MembershipShortname(m.name)
      for m in response.resources
      if not _ClusterMissing(m.endpoint)
  ]


def CrossProjectError(projects):
  return exceptions.Error('Memberships for this command must belong to the '
                          'same project and cannot mix project number and '
                          'project ID ({}).'.format(projects))


def MembershipRequiredError(args, flag_override=''):
  """Parses a list of membership resources from args.

  Assumes a `--memberships` flag or a `MEMBERSHIP_NAME` flag unless overridden.

  Args:
    args: argparse.Namespace arguments provided for the command
    flag_override: set to override the name of the membership flag

  Returns:
    memberships: A list of membership resource name strings

  Raises:
    exceptions.Error: if no memberships were found or memberships are invalid
    calliope_exceptions.RequiredArgumentException: if membership was not
      provided
  """
  if flag_override:
    flag = flag_override
  elif args.IsKnownAndSpecified('MEMBERSHIP_NAME'):
    flag = 'MEMBERSHIP_NAME'
  else:
    flag = 'memberships'
  return calliope_exceptions.RequiredArgumentException(
      flag, 'At least one membership is required for this command.')


def _ClusterMissing(m):
  for t in ['gkeCluster', 'multiCloudCluster', 'onPremCluster']:
    if hasattr(m, t):
      return getattr(getattr(m, t), 'clusterMissing', False)
