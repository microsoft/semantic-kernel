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
"""The command to describe the status of the Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.config_management import utils
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import semver


@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class Fetch(base.DescribeCommand):
  """Prints the Config Management configuration applied to the given membership.

  The output is in the format that is used by the apply subcommand. The fields
  that have not been configured will be shown with default values.

  ## EXAMPLES

  To fetch the applied Config Management configuration, run:

    $ {command}
  """

  feature_name = 'configmanagement'

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(parser)

  def Run(self, args):
    membership = base.ParseMembership(
        args, prompt=True, autoselect=True, search=True
    )

    f = self.GetFeature()
    membership_spec = None
    version = utils.get_backfill_version_from_feature(f, membership)
    for full_name, spec in self.hubclient.ToPyDict(f.membershipSpecs).items():
      if (
          util.MembershipPartialName(full_name)
          == util.MembershipPartialName(membership)
          and spec is not None
      ):
        membership_spec = spec.configmanagement
    if membership_spec is None:
      log.status.Print('Membership {} not initialized'.format(membership))

    # load the config template and merge with config has been applied to the
    # feature spec
    template = yaml.load(utils.APPLY_SPEC_VERSION_1)
    full_config = template['spec']
    merge_config_sync(membership_spec, full_config, version)
    merge_policy_controller(membership_spec, full_config, version)
    merge_hierarchy_controller(membership_spec, full_config)

    return template


def merge_config_sync(spec, config, version):
  """Merge configSync set in feature spec with the config template.

  ConfigSync has nested object structs need to be flatten.

  Args:
    spec: the ConfigManagementMembershipSpec message
    config: the dict loaded from full config template
    version: the version string of the membership
  """
  if not spec or not spec.configSync:
    return
  cs = config[utils.CONFIG_SYNC]
  git = spec.configSync.git
  oci = spec.configSync.oci
  if spec.configSync.enabled is not None:
    cs['enabled'] = spec.configSync.enabled
  else:
    # when enabled is no set in feature spec, it's determined by syncRepo
    if (git and git.syncRepo) or (oci and oci.syncRepo):
      cs['enabled'] = True
  if spec.configSync.sourceFormat:
    cs['sourceFormat'] = spec.configSync.sourceFormat
  if not version or semver.SemVer(version) >= semver.SemVer(
      utils.PREVENT_DRIFT_VERSION
  ):
    if spec.configSync.preventDrift:
      cs['preventDrift'] = spec.configSync.preventDrift
  else:
    del cs['preventDrift']

  if not git and not oci:
    return
  # Update sourceType if version >= 1.12.0
  if not version or semver.SemVer(version) >= semver.SemVer(
      utils.OCI_SUPPORT_VERSION
  ):
    if git:
      cs['sourceType'] = 'git'
    elif oci:
      cs['sourceType'] = 'oci'
  else:
    del cs['sourceType']

  if cs['sourceType'] and cs['sourceType'] == 'oci':
    if oci.syncWaitSecs:
      cs['syncWait'] = oci.syncWaitSecs
    for field in [
        'policyDir',
        'secretType',
        'syncRepo',
        'gcpServiceAccountEmail',
    ]:
      if hasattr(oci, field) and getattr(oci, field) is not None:
        cs[field] = getattr(oci, field)
  else:
    if git.syncWaitSecs:
      cs['syncWait'] = git.syncWaitSecs
    for field in [
        'policyDir',
        'httpsProxy',
        'secretType',
        'syncBranch',
        'syncRepo',
        'syncRev',
        'gcpServiceAccountEmail',
    ]:
      if hasattr(git, field) and getattr(git, field) is not None:
        cs[field] = getattr(git, field)


def merge_policy_controller(spec, config, version):
  """Merge configSync set in feature spec with the config template.

  ConfigSync has nested object structs need to be flatten.

  Args:
    spec: the ConfigManagementMembershipSpec message
    config: the dict loaded from full config template
    version: the version string of the membership
  """
  if not spec or not spec.policyController:
    return
  c = config[utils.POLICY_CONTROLLER]
  for field in list(config[utils.POLICY_CONTROLLER]):
    if (
        hasattr(spec.policyController, field)
        and getattr(spec.policyController, field) is not None
    ):
      c[field] = getattr(spec.policyController, field)

  valid_version = not version or semver.SemVer(version) >= semver.SemVer(
      utils.MONITORING_VERSION
  )
  spec_monitoring = spec.policyController.monitoring
  if not valid_version:
    c.pop('monitoring', None)
  elif spec_monitoring:
    c['monitoring'] = spec_monitoring


def merge_hierarchy_controller(spec, config):
  if not spec or not spec.hierarchyController:
    return
  c = config[utils.HNC]
  for field in list(config[utils.HNC]):
    if (
        hasattr(spec.hierarchyController, field)
        and getattr(spec.hierarchyController, field) is not None
    ):
      c[field] = getattr(spec.hierarchyController, field)
