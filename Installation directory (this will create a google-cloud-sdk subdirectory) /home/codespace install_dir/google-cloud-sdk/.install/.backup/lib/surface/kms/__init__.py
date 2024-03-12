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
"""The command group for all of the Cloud KMS API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class CloudKms(base.Group):
  """Manage cryptographic keys in the cloud.

  The gcloud kms command group lets you generate, use, rotate and destroy
  Google Cloud KMS keys.

  Cloud KMS is a cloud-hosted key management service that lets you manage
  encryption for your cloud services the same way you do on-premises. You can
  generate, use, rotate and destroy AES256 encryption keys. Cloud KMS is
  integrated with IAM and Cloud Audit Logging so that you can manage
  permissions on individual keys, and monitor how these are used. Use Cloud
  KMS to protect secrets and other sensitive data which you need to store in
  Google Cloud Platform.

  More information on Cloud KMS can be found here:
  https://cloud.google.com/kms/ and detailed documentation can be found here:
  https://cloud.google.com/kms/docs/
  """

  category = base.IDENTITY_AND_SECURITY_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190535383):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
    base.DisableUserProjectQuota()

    self.EnableSelfSignedJwtForTracks(
        [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]
    )
