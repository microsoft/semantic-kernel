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
"""Utilities for setting up GKE workload identity."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import compute_helpers
from googlecloudsdk.api_lib.dataproc import iam_helpers


class GkeWorkloadIdentity():
  """Sets up GKE Workload Identity."""

  @staticmethod
  def UpdateGsaIamPolicy(project_id, gsa_email, k8s_namespace,
                         k8s_service_accounts):
    """Allow the k8s_service_accounts to use gsa_email via Workload Identity."""
    resource = 'projects/-/serviceAccounts/{gsa_email}'.format(
        gsa_email=gsa_email)
    members = [
        'serviceAccount:{project_id}.svc.id.goog[{k8s_namespace}/{ksa}]'.format(
            project_id=project_id, k8s_namespace=k8s_namespace, ksa=ksa)
        for ksa in k8s_service_accounts
    ]
    iam_helpers.AddIamPolicyBindings(resource, members,
                                     'roles/iam.workloadIdentityUser')


class DefaultDataprocDataPlaneServiceAccount():
  """Find the default Google Service Account used by the Dataproc data plane."""

  @staticmethod
  def Get(project_id):
    return compute_helpers.GetDefaultServiceAccount(project_id)
