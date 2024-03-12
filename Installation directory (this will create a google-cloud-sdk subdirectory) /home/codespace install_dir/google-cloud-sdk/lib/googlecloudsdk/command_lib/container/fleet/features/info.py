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
"""Unified information for working with various features."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class Info(object):
  """Info contains information about a given Feature.

  Attributes:
    display_name: The Feature name as it should be displayed to users.
    api: The API associated with this Feature (for enablement).
    cmd_group: The subgroup for this Feature, e.g. `container fleet <cmd_group`.
  """

  def __init__(self, display_name, api='', cmd_group=''):
    self.display_name = display_name
    self.api = api
    self.cmd_group = cmd_group


_INFO = {
    'anthosobservability': Info(
        display_name='Anthos Observability',
        api='anthosobservability.googleapis.com',
        cmd_group='anthosobservability',
    ),
    'appdevexperience': Info(
        display_name='CloudRun',
        api='appdevelopmentexperience.googleapis.com',
        cmd_group='cloudrun',
    ),
    'authorizer': Info(
        display_name='Authorizer',
        api='gkehub.googleapis.com',
    ),
    'cloudbuild': Info(
        display_name='Cloud Build',
        api='cloudbuild.googleapis.com',
        cmd_group='build',
    ),
    'clouddeploy': Info(
        display_name='Cloud Deploy',
        api='clouddeploy.googleapis.com',
        cmd_group='deploy',
    ),
    'clusterupgrade': Info(
        display_name='Cluster Upgrade',
        api='gkehub.googleapis.com',
        cmd_group='scopes',
    ),
    'configdeliveryargocd': Info(
        display_name='Config Delivery backed by Argo CD',
        api='configdelivery.googleapis.com',
        cmd_group='argocd',
    ),
    'configmanagement': Info(
        display_name='Config Management',
        api='anthosconfigmanagement.googleapis.com',
        cmd_group='config-management',
    ),
    'dataplanev2': Info(
        display_name='Dataplane V2 Encryption',
        api='gkedataplanev2.googleapis.com',
        cmd_group='dataplane-v2-encryption',
    ),
    'fleetobservability': Info(
        display_name='Fleet Observability',
        api='gkehub.googleapis.com',
        cmd_group='fleetobservability',
    ),
    'identityservice': Info(
        display_name='Identity Service',
        api='anthosidentityservice.googleapis.com',
        cmd_group='identity-service',
    ),
    'metering': Info(
        display_name='Metering',
        api='multiclustermetering.googleapis.com',
    ),
    'multiclusteringress': Info(
        display_name='Ingress',
        api='multiclusteringress.googleapis.com',
        cmd_group='ingress',
    ),
    'multiclusterservicediscovery': Info(
        display_name='Multi-cluster Services',
        api='multiclusterservicediscovery.googleapis.com',
        cmd_group='multi-cluster-services',
    ),
    'policycontroller': Info(
        display_name='Policy Controller',
        api='anthospolicycontroller.googleapis.com',
        cmd_group='policycontroller',
    ),
    'servicedirectory': Info(
        display_name='Service Directory',
        api='servicedirectory.googleapis.com',
        cmd_group='service-directory',
    ),
    'servicemesh': Info(
        display_name='Service Mesh',
        api='meshconfig.googleapis.com',
        cmd_group='mesh',
    ),
    'workloadmigration': Info(
        display_name='Workload Migration',
        cmd_group='workload-migration',
    ),
    'namespaceactuation': Info(
        display_name='Namespace Actuation',
        cmd_group='namespaceactuation',
    ),
}


class UnknownFeatureError(exceptions.Error):
  """An error raised when information is requested for an unknown Feature."""

  def __init__(self, name):
    message = '{} is not a supported feature'.format(name)
    super(UnknownFeatureError, self).__init__(message)


def Get(name):
  """Get returns information about a Feature."""
  if name not in _INFO:
    raise UnknownFeatureError(name)
  return _INFO[name]
