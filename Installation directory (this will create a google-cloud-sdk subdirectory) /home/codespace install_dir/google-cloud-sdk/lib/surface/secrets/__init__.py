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
"""The command group for the Google Secret Manager API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA,
                    base.ReleaseTrack.ALPHA)
class CloudSecrets(base.Group):
  """Manage secrets on Google Cloud.

  Google Secret Manager allows users to store and retrieve secrets such as API
  keys, certificates, passwords on Google Cloud. Google Secret Manager is
  integrated with Cloud IAM and Cloud Audit Logging so users can manage
  permissions on individual secrets and monitor how these are used.

  To learn more about Google Secret Manager, visit:

      https://cloud.google.com/secret-manager/

  To read API and usage documentation, visit:

      https://cloud.google.com/secret-manager/docs/

  """

  category = base.IDENTITY_AND_SECURITY_CATEGORY

  def Filter(self, context, args):
    del context, args

    # This is technically the default, but some gcloud commands like IAM have
    # user project override off by default, so we enable it here explicitly.
    base.EnableUserProjectQuota()
