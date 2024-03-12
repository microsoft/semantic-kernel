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
"""Utils for Config Controller commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import api_adapter as container_api_adapter
from googlecloudsdk.api_lib.krmapihosting import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log

NOT_RUNNING_MSG = ('Config Controller {0} is not running. '
                   'The kubernetes API may not be available.')


def SetLocation():
  """Sets default location to '-' for list command."""
  return '-'


def InstanceAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='name',
      help_text='The name of the Config Controller instance.')


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text=(
          'The name of the Config Controller instance location. Currently, only'
          " ``us-central1'', ``us-east1'', ``us-east4'', ``us-east5'',"
          " ``us-west2'', ``northamerica-northeast1'',"
          " ``northamerica-northeast2'', ``europe-north1'', ``europe-west1'',"
          " ``europe-west3'', ``europe-west6'', ``australia-southeast1'',"
          " ``australia-southeast2'', ``asia-northeast1'', ``asia-northeast2''"
          " and ``asia-southeast1'' are supported."
      ),
  )


def GetInstanceResourceSpec(api_version):
  return concepts.ResourceSpec(
      'krmapihosting.projects.locations.krmApiHosts',
      resource_name='instance',
      api_version=api_version,
      krmApiHostsId=InstanceAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def AddInstanceResourceArg(parser, api_version):
  concept_parsers.ConceptParser.ForResource(
      'name',
      GetInstanceResourceSpec(api_version),
      'The identifier for a Config Controller instance.',
      required=True).AddToParser(parser)


def GetGKECluster(name, location):
  """Fetches the information about the GKE cluster backing the Config Controller."""

  cluster_id = 'krmapihost-' + name
  location_id = location
  project = None

  gke_api = container_api_adapter.NewAPIAdapter('v1')
  log.status.Print('Fetching cluster endpoint and auth data.')
  cluster_ref = gke_api.ParseCluster(cluster_id, location_id, project)
  cluster = gke_api.GetCluster(cluster_ref)

  if not gke_api.IsRunning(cluster):
    log.warning(NOT_RUNNING_MSG.format(cluster_ref.clusterId))

  return cluster, cluster_ref


def AsyncLog(operation):
  """Print log messages for async commands."""
  log.status.Print(
      """
      Check operation [{}] for status.
      To describe the operation, run:

        $ gcloud anthos config operations describe {}"""
      .format(operation.name, operation.name))
  return operation


def PatchRequest(args):
  """Construct a patch request based on the args."""
  instance = args.CONCEPTS.name.Parse()
  messages = apis.GetMessagesModule('krmapihosting',
                                    instance.GetCollectionInfo().api_version)

  # Get the current instance to determine whether full management config is
  # used.
  current = util.GetKrmApiHost(instance.RelativeName())

  # Construct the patch instance and the update mask.
  update_masks = []
  management_config = messages.ManagementConfig()
  bundles_config = messages.BundlesConfig(
      configControllerConfig=messages.ConfigControllerConfig())
  if args.experimental_features:
    update_masks.append(
        'bundles_config.config_controller_config.experimental_features')
    bundles_config.configControllerConfig.experimentalFeatures = args.experimental_features  # pylint: disable=line-too-long

  if current.managementConfig.fullManagementConfig:
    full_management_config = messages.FullManagementConfig()
    if args.man_block:
      full_management_config.manBlock = args.man_block
      update_masks.append('management_config.full_management_config.man_block')
    management_config.fullManagementConfig = full_management_config
  else:
    standard_management_config = messages.StandardManagementConfig()
    if args.man_block:
      standard_management_config.manBlock = args.man_block
      update_masks.append(
          'management_config.standard_management_config.man_block')
    management_config.standardManagementConfig = standard_management_config

  patch = messages.KrmApiHost(managementConfig=management_config,
                              bundlesConfig=bundles_config)
  return messages.KrmapihostingProjectsLocationsKrmApiHostsPatchRequest(
      krmApiHost=patch,
      name=instance.RelativeName(),
      updateMask=','.join(update_masks))
