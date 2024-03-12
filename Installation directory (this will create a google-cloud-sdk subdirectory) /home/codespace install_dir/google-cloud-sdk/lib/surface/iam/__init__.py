# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""The super-group for the IAM CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Iam(base.Group):
  """Manage IAM service accounts and keys.

     The gcloud iam command group lets you manage Google Cloud Identity &
     Access Management (IAM) service accounts and keys.

     Cloud IAM authorizes who can take action on specific resources, giving you
     full control and visibility to manage cloud resources centrally. For
     established enterprises with complex organizational structures, hundreds of
     workgroups and potentially many more projects, Cloud IAM provides a unified
     view into security policy across your entire organization, with built-in
     auditing to ease compliance processes.

     More information on Cloud IAM can be found here:
     https://cloud.google.com/iam and detailed documentation can be found here:
     https://cloud.google.com/iam/docs/
  """

  category = base.IDENTITY_AND_SECURITY_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190535430):  Determine if command group works with project number
    base.RequireProjectID(args)
    base.DisableUserProjectQuota()

    self.EnableSelfSignedJwtForTracks(
        [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]
    )
