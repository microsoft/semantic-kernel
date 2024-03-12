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
"""Client class for Cloud Billing API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.billing import utils


class AccountsClient(object):
  """High-level client for billing accounts service."""

  def __init__(self, client=None, messages=None):
    self.client = client or utils.GetClient()
    self.messages = messages or self.client.MESSAGES_MODULE
    self._service = self.client.billingAccounts

  def Get(self, account_ref):
    return self._service.Get(
        self.messages.CloudbillingBillingAccountsGetRequest(
            name=account_ref.RelativeName()))

  def List(self, limit=None):
    return list_pager.YieldFromList(
        self._service,
        self.messages.CloudbillingBillingAccountsListRequest(),
        field='billingAccounts',
        batch_size_attribute='pageSize',
        limit=limit
    )


class ProjectsClient(object):
  """High-level client for billing projects service."""

  def __init__(self, client=None, messages=None):
    self.client = client or utils.GetClient()
    self.messages = messages or self.client.MESSAGES_MODULE
    # Don't make a self._service alias because there are multiple services
    # related to projects

  def Get(self, project_ref):
    return self.client.projects.GetBillingInfo(
        self.messages.CloudbillingProjectsGetBillingInfoRequest(
            name=project_ref.RelativeName(),
        )
    )

  def Link(self, project_ref, account_ref):
    """Link the given account to the given project.

    Args:
      project_ref: a Resource reference to the project to be linked to
      account_ref: a Resource reference to the account to link, or None to
        unlink the project from its current account.

    Returns:
      ProjectBillingInfo, the new ProjectBillingInfo
    """
    billing_account_name = account_ref.RelativeName() if account_ref else ''
    return self.client.projects.UpdateBillingInfo(
        self.messages.CloudbillingProjectsUpdateBillingInfoRequest(
            name=project_ref.RelativeName(),
            projectBillingInfo=self.messages.ProjectBillingInfo(
                billingAccountName=billing_account_name
            )
        )
    )

  def List(self, account_ref, limit=None):
    return list_pager.YieldFromList(
        self.client.billingAccounts_projects,
        self.messages.CloudbillingBillingAccountsProjectsListRequest(
            name=account_ref.RelativeName(),
        ),
        field='projectBillingInfo',
        batch_size_attribute='pageSize',
        limit=limit
    )
