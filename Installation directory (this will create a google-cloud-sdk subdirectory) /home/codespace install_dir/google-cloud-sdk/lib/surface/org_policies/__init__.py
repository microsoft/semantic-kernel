# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""The command group for the Org Policies CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'DESCRIPTION':
        """\
        The gcloud org-policies command group lets you create and manipulate
        Organization Policies.

        The Organization Policy Service gives you centralized and programmatic control
        over your organization's cloud resources. As the organization policy
        administrator, you will be able to configure restrictions across your entire
        resource hierarchy.

        More information on Organization Policies can be found here:
        https://cloud.google.com/resource-manager/docs/organization-policy/overview
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class OrgPolicies(base.Group):
  """Create and manage Organization Policies."""

  category = base.IDENTITY_AND_SECURITY_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190538189):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
    base.EnableUserProjectQuotaWithFallback()


OrgPolicies.detailed_help = DETAILED_HELP
