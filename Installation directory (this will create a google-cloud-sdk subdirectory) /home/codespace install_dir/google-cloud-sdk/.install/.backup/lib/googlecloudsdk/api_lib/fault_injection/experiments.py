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
"""Experiment client for Faultinjectiontesting Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.fault_injection import utils as api_lib_utils


class ExperimentsClient(object):
  """Client for faults in Faultinjection Testing API."""

  def __init__(self, client=None, messages=None):
    self.client = client or api_lib_utils.GetClientInstance()
    self.messages = messages or api_lib_utils.GetMessagesModule()
    self._experiments_client = self.client.projects_locations_experiments

  def Describe(self, experiment):
    """Describe a Experiment in the Project/location.

    Args:
      experiment: str, the name for the experiment being described.

    Returns:
      Described Experiment Resource.
    """
    describe_req = self.messages.FaultinjectiontestingProjectsLocationsExperimentsGetRequest(
        name=experiment
    )
    return self._experiments_client.Get(describe_req)

  def Delete(self, experiment):
    """Delete a Experiment in the Project/location.

    Args:
      experiment: str, the name for the Experiment being deleted

    Returns:
      Empty Response Message.
    """
    delete_req = self.messages.FaultinjectiontestingProjectsLocationsExperimentsDeleteRequest(
        name=experiment
    )
    return self._experiments_client.Delete(delete_req)

  def Create(self, experiment, experiment_config, parent):
    """Create a fault in the Project/location.

    Args:
      experiment: str, the name for the experiment being created
      experiment_config: file, the file which contains experiment config
      parent: parent for fault resource

    Returns:
      Experiment.
    """
    create_req = api_lib_utils.ParseCreateExperimentFromYaml(
        experiment, experiment_config, parent
    )

    return self._experiments_client.Create(create_req)

  def Update(self, experiment, experiment_config):
    """Update a experiment in the Project/location.

    Args:
      experiment: str, the name for the experiment being created
      experiment_config: file, the file which contains experiment config

    Returns:
      Experiment.
    """
    patch_req = api_lib_utils.ParseUpdateExperimentFromYaml(
        experiment, experiment_config
    )

    return self._experiments_client.Patch(patch_req)

  def List(
      self,
      parent,
      limit=None,
      page_size=100,
  ):
    """List Experiments in the Projects/Location.

    Args:
      parent: str, projects/{projectId}/locations/{location}
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      Generator of matching Experiments.
    """
    list_req = self.messages.FaultinjectiontestingProjectsLocationsExperimentsListRequest(
        parent=parent
    )
    return list_pager.YieldFromList(
        self._experiments_client,
        list_req,
        field='experiments',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )
