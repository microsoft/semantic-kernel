# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Support library to handle the release subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import client_util
from googlecloudsdk.core import log

TARGET_FILTER_TEMPLATE = ('targetSnapshots.name:"{}"'
                          ' AND renderState="SUCCEEDED"')
RELEASE_PARENT_TEMPLATE = 'projects/{}/locations/{}/deliveryPipelines/{}'


class ReleaseClient(object):
  """Client for release service in the Cloud Deploy API."""

  def __init__(self, client=None, messages=None):
    """Initialize a release.ReleaseClient.

    Args:
      client: base_api.BaseApiClient, the client class for Cloud Deploy.
      messages: module containing the definitions of messages for Cloud Deploy.
    """
    self.client = client or client_util.GetClientInstance()
    self.messages = messages or client_util.GetMessagesModule(client)
    self._service = self.client.projects_locations_deliveryPipelines_releases

  def Create(self, release_ref, release_config):
    """Create the release resource.

    Args:
      release_ref: release resource object.
      release_config: release message.

    Returns:
      The operation message.
    """
    log.debug('creating release: %r', release_config)

    return self._service.Create(
        self.messages
        .ClouddeployProjectsLocationsDeliveryPipelinesReleasesCreateRequest(
            parent=release_ref.Parent().RelativeName(),
            release=release_config,
            releaseId=release_ref.Name()))

  def Get(self, name):
    """Gets a release resource.

    Args:
      name: release resource name.

    Returns:
      release message.
    """
    request = self.messages.ClouddeployProjectsLocationsDeliveryPipelinesReleasesGetRequest(
        name=name)
    return self._service.Get(request)

  def ListReleasesByTarget(self, target_ref_project_number, project_id,
                           pipeline_id):
    """Lists the releases in a target.

    Args:
      target_ref_project_number: target reference with project number in the
        name.
      project_id: str, project ID.
      pipeline_id: str, delivery pipeline ID.

    Returns:
      a list of release messages.
    """
    target_dict = target_ref_project_number.AsDict()
    request = self.messages.ClouddeployProjectsLocationsDeliveryPipelinesReleasesListRequest(
        parent=RELEASE_PARENT_TEMPLATE.format(project_id,
                                              target_dict['locationsId'],
                                              pipeline_id),
        filter=TARGET_FILTER_TEMPLATE.format(
            target_ref_project_number.RelativeName()))
    return self._service.List(request).releases

  def Abandon(self, name):
    """Abandons a release.

    Args:
      name: release resource name.

    Returns:
      AbandonReleaseResponse message.
    """
    request = self.messages.ClouddeployProjectsLocationsDeliveryPipelinesReleasesAbandonRequest(
        name=name)
    return self._service.Abandon(request)
