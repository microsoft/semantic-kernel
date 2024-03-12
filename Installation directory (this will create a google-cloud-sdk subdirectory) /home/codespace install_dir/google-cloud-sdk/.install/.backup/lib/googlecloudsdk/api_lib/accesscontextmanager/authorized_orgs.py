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
"""API library for Authorized Orgs Desc."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.accesscontextmanager import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import log
from googlecloudsdk.core import resources as core_resources


def _SetIfNotNone(field_name, field_value, obj, update_mask):
  """Sets specified field to the provided value and adds it to update mask.

  Args:
    field_name: The name of the field to set the value of.
    field_value: The value to set the field to. If it is None, the field will
      NOT be set.
    obj: The object on which the value is to be set.
    update_mask: The update mask to add this field to.

  Returns:
    True if the field was set and False otherwise.
  """
  if field_value is not None:
    setattr(obj, field_name, field_value)
    update_mask.append(field_name)
    return True
  return False


class Client(object):
  """High-level API client for Authorized Orgs."""

  def __init__(self, client=None, messages=None, version='v1'):
    self.client = client or util.GetClient(version=version)
    self.messages = messages or self.client.MESSAGES_MODULE

  def Get(self, authorized_orgs_desc_ref):
    return self.client.accessPolicies_authorizedOrgsDescs.Get(
        self.messages
        .AccesscontextmanagerAccessPoliciesAuthorizedOrgsDescsGetRequest(
            name=authorized_orgs_desc_ref.RelativeName()))

  def List(self, policy_ref, limit=None):
    req = self.messages.AccesscontextmanagerAccessPoliciesAuthorizedOrgsDescsListRequest(
        parent=policy_ref.RelativeName())
    return list_pager.YieldFromList(
        self.client.accessPolicies_authorizedOrgsDescs,
        req,
        limit=limit,
        batch_size_attribute='pageSize',
        batch_size=None,
        field='authorizedOrgsDescs')

  def _ApplyPatch(self, authorized_orgs_desc_ref, authorized_orgs_desc,
                  update_mask):
    """Applies a PATCH to the provided Authorized Orgs Desc."""
    m = self.messages
    request_type = (
        m.AccesscontextmanagerAccessPoliciesAuthorizedOrgsDescsPatchRequest)
    request = request_type(
        authorizedOrgsDesc=authorized_orgs_desc,
        name=authorized_orgs_desc_ref.RelativeName(),
        updateMask=','.join(update_mask),
    )
    operation = self.client.accessPolicies_authorizedOrgsDescs.Patch(request)
    poller = util.OperationPoller(
        self.client.accessPolicies_authorizedOrgsDescs, self.client.operations,
        authorized_orgs_desc_ref)
    operation_ref = core_resources.REGISTRY.Parse(
        operation.name, collection='accesscontextmanager.operations')
    return waiter.WaitFor(
        poller, operation_ref,
        'Waiting for PATCH operation [{}]'.format(operation_ref.Name()))

  def Patch(self, authorized_orgs_desc_ref, orgs=None):
    """Patch an authorized orgs desc.

    Args:
      authorized_orgs_desc_ref: AuthorizedOrgsDesc, reference to the
        authorizedOrgsDesc to patch
      orgs: list of str, the names of orgs ( 'organizations/...') or None if not
        updating.

    Returns:
      AuthorizedOrgsDesc, the updated Authorized Orgs Desc.
    """
    m = self.messages
    authorized_orgs_desc = m.AuthorizedOrgsDesc()
    update_mask = []

    _SetIfNotNone('orgs', orgs, authorized_orgs_desc, update_mask)

    # No update mask implies no fields were actually edited, so this is a no-op.
    if not update_mask:
      log.warning(
          'The update specified results in an identical resource. Skipping request.'
      )
      return authorized_orgs_desc

    return self._ApplyPatch(authorized_orgs_desc_ref, authorized_orgs_desc,
                            update_mask)
