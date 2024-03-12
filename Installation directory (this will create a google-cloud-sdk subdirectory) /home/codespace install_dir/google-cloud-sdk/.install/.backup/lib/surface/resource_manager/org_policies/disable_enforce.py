# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command to turn off enforcement of a boolean constraint."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import org_policies
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import org_policies_base
from googlecloudsdk.command_lib.resource_manager import org_policies_flags as flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class DisableEnforce(base.Command):
  """Turns off enforcement of boolean Organization Policy constraint.

  Turns off enforcement of a boolean Organization Policy constraint at
  the specified resource.

  ## EXAMPLES

  The following command disables enforcement of the Organization Policy boolean
  constraint `compute.disableSerialPortAccess` on project `foo-project`:

    $ {command} compute.disableSerialPortAccess --project=foo-project
  """

  @staticmethod
  def Args(parser):
    flags.AddIdArgToParser(parser)
    flags.AddParentResourceFlagsToParser(parser)

  def Run(self, args):
    service = org_policies_base.OrgPoliciesService(args)
    messages = org_policies.OrgPoliciesMessages()

    return service.SetOrgPolicy(
        org_policies_base.SetOrgPolicyRequest(
            args,
            messages.OrgPolicy(
                constraint=org_policies.FormatConstraint(args.id),
                booleanPolicy=messages.BooleanPolicy(enforced=False))))
