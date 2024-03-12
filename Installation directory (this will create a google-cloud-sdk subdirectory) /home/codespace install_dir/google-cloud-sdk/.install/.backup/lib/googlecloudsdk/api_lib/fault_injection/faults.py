# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Fault client for Faultinjectiontesting Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.fault_injection import utils as api_lib_utils


class FaultsClient(object):
  """Client for faults in Faultinjection Testing API."""

  def __init__(self, client=None, messages=None):
    self.client = client or api_lib_utils.GetClientInstance()
    self.messages = messages or api_lib_utils.GetMessagesModule()
    self._faults_client = self.client.projects_locations_faults

  def Describe(self, fault):
    """Describe a Fault in the Project/location.

    Args:
      fault: str, the name for the fault being described.

    Returns:
      Described Fault Resource.
    """
    describe_req = (
        self.messages.FaultinjectiontestingProjectsLocationsFaultsGetRequest(
            name=fault
        )
    )
    return self._faults_client.Get(describe_req)

  def Delete(self, fault):
    """Delete a fault in the Project/location.

    Args:
      fault: str, the name for the fault being deleted

    Returns:
      Empty Response Message.
    """
    delete_req = (
        self.messages.FaultinjectiontestingProjectsLocationsFaultsDeleteRequest(
            name=fault
        )
    )
    return self._faults_client.Delete(delete_req)

  def Create(self, fault, faultconfig, parent):
    """Create a fault in the Project/location.

    Args:
      fault: str, the name for the fault being created
      faultconfig: file, the file which contains fault config
      parent: parent for fault resource

    Returns:
      Fault.
    """
    create_req = (api_lib_utils.ParseCreateFaultFromYaml(
        fault, faultconfig, parent
        ))

    return self._faults_client.Create(create_req)

  def Update(self, fault, faultconfig):
    """Update a fault in the Project/location.

    Args:
      fault: str, the name for the fault being created
      faultconfig: file, the file which contains fault config

    Returns:
      Fault.
    """
    patch_req = (api_lib_utils.ParseUpdateFaultFromYaml(fault, faultconfig))

    return self._faults_client.Patch(patch_req)

  def List(
      self,
      parent,
      limit=None,
      page_size=100,
  ):
    """List Faults in the Projects/Location.

    Args:
      parent: str, projects/{projectId}/locations/{location}
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      Generator of matching Faults.
    """
    list_req = (
        self.messages.FaultinjectiontestingProjectsLocationsFaultsListRequest(
            parent=parent
        )
    )
    return list_pager.YieldFromList(
        self._faults_client,
        list_req,
        field='faults',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )
