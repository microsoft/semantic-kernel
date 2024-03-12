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
"""The command to update Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.config_management import utils
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Upgrade(base.UpdateCommand):
  """Upgrade the version of the Config Management Feature.

  Upgrade a specified membership to any supported version of the Config
  Management Feature.

  ## EXAMPLES

  To upgrade a membership named `MEMBERSHIP_NAME`, run:

    $ {command} --membership=MEMBERSHIP_NAME --version=VERSION
  """

  feature_name = 'configmanagement'

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(parser)
    parser.add_argument(
        '--version',
        type=str,
        help='The version of ACM to change to.',
        required=True,
    )

  def Run(self, args):
    utils.enable_poco_api_if_disabled(self.Project())

    f = self.GetFeature()
    new_version = args.version
    membership = base.ParseMembership(
        args, prompt=True, autoselect=True, search=True
    )
    _, cluster_v = utils.versions_for_member(f, membership)

    if not self._validate_versions(membership, cluster_v, new_version):
      return
    console_io.PromptContinue(
        'You are about to change the {} Feature for membership {} from version'
        ' "{}" to version "{}".'.format(
            self.feature.display_name, membership, cluster_v, new_version
        ),
        throw_if_unattended=True,
        cancel_on_no=True,
    )

    patch = self.messages.MembershipFeatureSpec()
    # If there's an existing spec, copy it to leave the other fields intact.
    for full_name, spec in self.hubclient.ToPyDict(f.membershipSpecs).items():
      if (
          util.MembershipPartialName(full_name)
          == util.MembershipPartialName(membership)
          and spec is not None
      ):
        patch = spec
    if patch.configmanagement is None:
      patch.configmanagement = self.messages.ConfigManagementMembershipSpec()
    patch.configmanagement.version = new_version

    membership_key = membership
    f = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(
            {membership_key: patch}
        )
    )
    self.Update(['membershipSpecs'], f)

  def _validate_versions(self, membership, cluster_v, new_v):
    if cluster_v == new_v:
      log.status.Print(
          'Membership {} already has version {} of the {} Feature installed.'
          .format(membership, cluster_v, self.feature.display_name)
      )
      return False

    return True
