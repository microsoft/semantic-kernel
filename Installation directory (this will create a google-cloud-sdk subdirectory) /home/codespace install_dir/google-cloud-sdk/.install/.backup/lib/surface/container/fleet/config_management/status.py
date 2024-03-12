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
"""The command to get the status of Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import api_util
from googlecloudsdk.command_lib.container.fleet.features import base as feature_base
from googlecloudsdk.core import log


NA = 'NA'

DETAILED_HELP = {
    'EXAMPLES': """\
   Print the status of the Config Management Feature:

    $ {command}

    Name             Status  Last_Synced_Token   Sync_Branch  Last_Synced_Time  Hierarchy_Controller
    managed-cluster  SYNCED  2945500b7f          acme         2020-03-23
    11:12:31 -0700 PDT  INSTALLED

  View the status for the cluster named `managed-cluster-a`:

    $ {command} --filter="acm_status.name:managed-cluster-a"

  Use a regular expression to list status for multiple clusters:

    $ {command} --filter="acm_status.name ~ managed-cluster.*"

  List all clusters where current status is `SYNCED`:

    $ {command} --filter="acm_status.config_sync:SYNCED"

  List all the clusters where sync_branch is `v1` and current Config Sync status
  is not `SYNCED`:

    $ {command} --filter="acm_status.sync_branch:v1 AND -acm_status.config_sync:SYNCED"
  """,
}


class ConfigmanagementFeatureState(object):
  """Feature state class stores ACM status."""

  def __init__(self, clusterName):
    self.name = clusterName
    self.config_sync = NA
    self.last_synced_token = NA
    self.last_synced = NA
    self.sync_branch = NA
    self.policy_controller_state = NA
    self.hierarchy_controller_state = NA

  def update_sync_state(self, fs):
    """Update config_sync state for the membership that has ACM installed.

    Args:
      fs: ConfigManagementFeatureState
    """
    if not (fs.configSyncState and fs.configSyncState.syncState):
      self.config_sync = 'SYNC_STATE_UNSPECIFIED'
    else:
      self.config_sync = fs.configSyncState.syncState.code
      if fs.configSyncState.syncState.syncToken:
        self.last_synced_token = fs.configSyncState.syncState.syncToken[:7]
      self.last_synced = fs.configSyncState.syncState.lastSyncTime
      if has_config_sync_git(fs):
        self.sync_branch = fs.membershipSpec.configSync.git.syncBranch

  def update_policy_controller_state(self, md):
    """Update policy controller state for the membership that has ACM installed.

    Args:
      md: MembershipFeatureState
    """
    # Also surface top-level Feature Authorizer errors.
    if md.state.code.name != 'OK':
      self.policy_controller_state = 'ERROR: {}'.format(md.state.description)
      return
    fs = md.configmanagement
    if not (
        fs.policyControllerState and fs.policyControllerState.deploymentState
    ):
      self.policy_controller_state = NA
      return
    pc_deployment_state = fs.policyControllerState.deploymentState
    expected_deploys = {
        'GatekeeperControllerManager': (
            pc_deployment_state.gatekeeperControllerManagerState
        )
    }
    if (
        fs.membershipSpec
        and fs.membershipSpec.version
        and fs.membershipSpec.version > '1.4.1'
    ):
      expected_deploys['GatekeeperAudit'] = pc_deployment_state.gatekeeperAudit
    for deployment_name, deployment_state in expected_deploys.items():
      if not deployment_state:
        continue
      elif deployment_state.name != 'INSTALLED':
        self.policy_controller_state = '{} {}'.format(
            deployment_name, deployment_state
        )
        return
      self.policy_controller_state = deployment_state.name

  def update_hierarchy_controller_state(self, fs):
    """Update hierarchy controller state for the membership that has ACM installed.

    The PENDING state is set separately after this logic. The PENDING state
    suggests the HC part in feature_spec and feature_state are inconsistent, but
    the HC status from feature_state is not ERROR. This suggests that HC might
    be still in the updating process, so we mark it as PENDING

    Args:
      fs: ConfigmanagementFeatureState
    """
    if not (fs.hierarchyControllerState and fs.hierarchyControllerState.state):
      self.hierarchy_controller_state = NA
      return
    hc_deployment_state = fs.hierarchyControllerState.state

    hnc_state = 'NOT_INSTALLED'
    ext_state = 'NOT_INSTALLED'
    if hc_deployment_state.hnc:
      hnc_state = hc_deployment_state.hnc.name
    if hc_deployment_state.extension:
      ext_state = hc_deployment_state.extension.name
    # partial mapping from ('hnc_state', 'ext_state') to 'HC_STATE',
    # ERROR, PENDING, NA states are identified separately
    deploys_to_status = {
        ('INSTALLED', 'INSTALLED'): 'INSTALLED',
        ('INSTALLED', 'NOT_INSTALLED'): 'INSTALLED',
        ('NOT_INSTALLED', 'NOT_INSTALLED'): NA,
    }
    if (hnc_state, ext_state) in deploys_to_status:
      self.hierarchy_controller_state = deploys_to_status[
          (hnc_state, ext_state)
      ]
    else:
      self.hierarchy_controller_state = 'ERROR'

  def update_pending_state(self, feature_spec_mc, feature_state_mc):
    """Update config sync and policy controller with the pending state.

    Args:
      feature_spec_mc: MembershipConfig
      feature_state_mc: MembershipConfig
    """
    feature_state_pending = (
        feature_state_mc is None and feature_spec_mc is not None
    )
    if feature_state_pending:
      self.last_synced_token = 'PENDING'
      self.last_synced = 'PENDING'
      self.sync_branch = 'PENDING'
    if self.config_sync.__str__() in [
        'SYNCED',
        'NOT_CONFIGURED',
        'NOT_INSTALLED',
        NA,
    ] and (
        feature_state_pending
        or feature_spec_mc.configSync != feature_state_mc.configSync
    ):
      self.config_sync = 'PENDING'
    if (
        self.policy_controller_state.__str__()
        in ['INSTALLED', 'GatekeeperAudit NOT_INSTALLED', NA]
        and feature_state_pending
    ):
      self.policy_controller_state = 'PENDING'
    if (
        self.hierarchy_controller_state.__str__() != 'ERROR'
        and feature_state_pending
        or feature_spec_mc.hierarchyController
        != feature_state_mc.hierarchyController
    ):
      self.hierarchy_controller_state = 'PENDING'


class Status(feature_base.FeatureCommand, base.ListCommand):
  """Print the status of all clusters with Config Management enabled."""

  detailed_help = DETAILED_HELP

  feature_name = 'configmanagement'

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
    multi(acm_status:format='table(
            name:label=Name:sort=1,
            config_sync:label=Status,
            last_synced_token:label="Last_Synced_Token",
            sync_branch:label="Sync_Branch",
            last_synced:label="Last_Synced_Time",
            policy_controller_state:label="Policy_Controller",
            hierarchy_controller_state:label="Hierarchy_Controller"
      )' , acm_errors:format=list)
    """)

  def Run(self, args):
    memberships, unreachable = api_util.ListMembershipsFull()
    if unreachable:
      log.warning(
          'Locations {} are currently unreachable. Status '
          'entries may be incomplete'.format(unreachable)
      )
    if not memberships:
      return None
    f = self.GetFeature()
    acm_status = []
    acm_errors = []

    feature_spec_memberships = {
        util.MembershipPartialName(m): s
        for m, s in self.hubclient.ToPyDict(f.membershipSpecs).items()
        if s is not None and s.configmanagement is not None
    }
    feature_state_memberships = {
        util.MembershipPartialName(m): s
        for m, s in self.hubclient.ToPyDict(f.membershipStates).items()
    }
    for name in memberships:
      name = util.MembershipPartialName(name)
      cluster = ConfigmanagementFeatureState(name)
      if name not in feature_state_memberships:
        if name in feature_spec_memberships:
          # (b/187846229) Show PENDING if feature spec is aware of
          # this membership name but feature state is not
          cluster.update_pending_state(feature_spec_memberships[name], None)
        acm_status.append(cluster)
        continue
      md = feature_state_memberships[name]
      fs = md.configmanagement
      # (b/153587485) Show FeatureState.code if it's not OK
      # as it indicates an unreachable cluster or a dated syncState.code
      if md.state is None or md.state.code is None:
        cluster.config_sync = 'CODE_UNSPECIFIED'
      elif fs is None:
        cluster.config_sync = 'NOT_INSTALLED'
      else:
        # operator errors could occur regardless of the deployment_state
        if has_operator_error(fs):
          append_error(name, fs.operatorState.errors, acm_errors)
        # We should update PoCo state regardless of operator state.
        cluster.update_policy_controller_state(md)
        if not has_operator_state(fs):
          if md.state.code.name != 'OK':
            cluster.config_sync = md.state.code.name
          else:
            cluster.config_sync = 'OPERATOR_STATE_UNSPECIFIED'
        else:
          cluster.config_sync = fs.operatorState.deploymentState.name
          if cluster.config_sync == 'INSTALLED':
            cluster.update_sync_state(fs)
            if has_config_sync_error(fs):
              append_error(
                  name, fs.configSyncState.syncState.errors, acm_errors
              )
            cluster.update_hierarchy_controller_state(fs)
            if name in feature_spec_memberships:
              cluster.update_pending_state(
                  feature_spec_memberships[name].configmanagement,
                  fs.membershipSpec,
              )
      acm_status.append(cluster)
    return {'acm_errors': acm_errors, 'acm_status': acm_status}


def has_operator_state(fs):
  return fs and fs.operatorState and fs.operatorState.deploymentState


def has_operator_error(fs):
  return fs and fs.operatorState and fs.operatorState.errors


def has_config_sync_error(fs):
  return (
      fs
      and fs.configSyncState
      and fs.configSyncState.syncState
      and fs.configSyncState.syncState.errors
  )


def has_config_sync_git(fs):
  return (
      fs.membershipSpec
      and fs.membershipSpec.configSync
      and fs.membershipSpec.configSync.git
  )


def append_error(cluster, state_errors, acm_errors):
  for error in state_errors:
    acm_errors.append({'cluster': cluster, 'error': error.errorMessage})
