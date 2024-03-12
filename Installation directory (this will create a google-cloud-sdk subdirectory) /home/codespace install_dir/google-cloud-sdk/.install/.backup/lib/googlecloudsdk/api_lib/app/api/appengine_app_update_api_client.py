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
"""Functions for creating a client to talk to the App Engine Admin API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.api_lib.app.api import appengine_api_client_base as base
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


DEFAULT_VERSION = 'v1beta'

# 'app update' is currently only exposed in beta.
UPDATE_VERSIONS_MAP = {
    calliope_base.ReleaseTrack.GA: DEFAULT_VERSION,
    calliope_base.ReleaseTrack.ALPHA: DEFAULT_VERSION,
    calliope_base.ReleaseTrack.BETA: DEFAULT_VERSION
}


def GetApiClientForTrack(release_track):
  return AppengineAppUpdateApiClient.GetApiClient(
      UPDATE_VERSIONS_MAP[release_track])


class AppengineAppUpdateApiClient(base.AppengineApiClientBase):
  """Client used by gcloud to communicate with the App Engine API."""

  def __init__(self, client):
    base.AppengineApiClientBase.__init__(self, client)

    self._registry = resources.REGISTRY.Clone()
    # pylint: disable=protected-access
    self._registry.RegisterApiByName('appengine', client._VERSION)

  def PatchApplication(self, split_health_checks=None, service_account=None):
    """Updates an application.

    Args:
      split_health_checks: Boolean, whether to enable split health checks by
        default.
      service_account: str, the app-level default service account to update for
        this App Engine app.

    Returns:
      Long running operation.
    """

    # Create a configuration update request.
    update_mask = ''
    if split_health_checks is not None:
      update_mask += 'featureSettings.splitHealthChecks,'
    if service_account is not None:
      update_mask += 'serviceAccount,'
    application_update = self.messages.Application()
    application_update.featureSettings = self.messages.FeatureSettings(
        splitHealthChecks=split_health_checks)
    application_update.serviceAccount = service_account

    update_request = self.messages.AppengineAppsPatchRequest(
        name=self._FormatApp(),
        application=application_update,
        updateMask=update_mask)

    operation = self.client.apps.Patch(update_request)

    log.debug('Received operation: [{operation}] with mask [{mask}]'.format(
        operation=operation.name,
        mask=update_mask))

    return operations_util.WaitForOperation(self.client.apps_operations,
                                            operation)
