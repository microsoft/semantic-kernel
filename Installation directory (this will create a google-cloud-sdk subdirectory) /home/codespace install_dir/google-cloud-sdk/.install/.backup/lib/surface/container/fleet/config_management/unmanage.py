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
"""The command to unmanage/delete Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.features import base


class Unmanage(base.UpdateCommand):
  """Remove the Config Management Feature Spec for the given membership.

  Remove the Config Management Feature Spec for the given membership. The
  existing ConfigManagement resources in the clusters will become unmanaged.

  ## EXAMPLES

  To remove the Config Management Feature spec for a membership, run:

    $ {command} --membership=MEMBERSHIP_NAME
  """

  feature_name = 'configmanagement'

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(parser)

  def Run(self, args):
    membership = base.ParseMembership(
        args, prompt=True, autoselect=True, search=True
    )

    # Setup a patch to set the MembershipSpec to the empty proto ("delete").
    membership_key = membership
    specs = {membership_key: self.messages.MembershipFeatureSpec()}
    patch = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(specs)
    )

    self.Update(['membership_specs'], patch)
