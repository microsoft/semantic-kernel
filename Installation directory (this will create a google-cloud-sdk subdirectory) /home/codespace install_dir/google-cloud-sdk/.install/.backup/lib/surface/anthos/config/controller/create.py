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
"""Command to create new Config Controller instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import util as container_util
from googlecloudsdk.api_lib.krmapihosting import util as krmapihosting_api
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.anthos.config.controller import create_utils
from googlecloudsdk.command_lib.anthos.config.controller import flags
from googlecloudsdk.command_lib.anthos.config.controller import utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create Anthos Config Controller instances."""

  _API_VERSION = "v1"

  detailed_help = {
      "DESCRIPTION":
          "Create an Anthos Config Controller instance.",
      "EXAMPLES": ("""
        To create an Anthos Config Controller instance with the name ``acc-default'', run:

          $ {command} acc-default --location=us-central1
      """)
  }

  @staticmethod
  def Args(parser):
    utils.AddInstanceResourceArg(parser, Create._API_VERSION)
    flags.AddAsyncFlag(parser)
    flags.AddMasterIPv4CIDRBlock(parser)
    flags.AddNetworkFlag(parser)
    flags.AddSubnetFlag(parser)
    flags.AddManBlockFlagDeprecated(parser)
    flags.AddManBlocksFlag(parser)
    flags.AddClusterIPv4CIDRBlock(parser)
    flags.AddServicesIPv4CIDRBlack(parser)
    flags.AddClusterNamedRangeFlag(parser)
    flags.AddServicesNamedRange(parser)
    flags.AddUsePrivateEndpoint(parser)
    flags.AddFullManagement(parser)

  def Run(self, args):
    client = krmapihosting_api.GetClientInstance(api_version=self._API_VERSION)

    instance_ref = args.CONCEPTS.name.Parse()

    release_track = args.calliope_command.ReleaseTrack()
    op_ref = client.projects_locations_krmApiHosts.Create(
        create_utils.CreateUpdateRequest(release_track, instance_ref, args))
    log.status.Print("Create request issued for: [{}]".format(
        instance_ref.krmApiHostsId))
    if args.async_:
      ops = op_ref.name.split("/")
      log.status.Print("Check operation [{}] for status.\n"
                       "To describe the operation, run:\n\n"
                       "$ gcloud anthos config operations describe {} "
                       "--location {}"
                       .format(op_ref.name, ops[-1], args.location))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name, collection="krmapihosting.projects.locations.operations",
        api_version=self._API_VERSION)
    poller = waiter.CloudOperationPoller(client.projects_locations_krmApiHosts,
                                         client.projects_locations_operations)
    result = waiter.WaitFor(
        poller, op_resource,
        "Waiting for operation [{}] to complete".format(op_ref.name))
    log.status.Print("Created instance [{}].".format(
        instance_ref.krmApiHostsId))

    container_util.CheckKubectlInstalled()
    cluster, cluster_ref = utils.GetGKECluster(instance_ref.krmApiHostsId,
                                               instance_ref.locationsId)
    container_util.ClusterConfig.Persist(cluster, cluster_ref.projectId)

    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create Anthos Config Controller instances."""

  _API_VERSION = "v1alpha1"

  @staticmethod
  def Args(parser):
    utils.AddInstanceResourceArg(parser, CreateAlpha._API_VERSION)
    flags.AddAsyncFlag(parser)
    flags.AddMasterIPv4CIDRBlock(parser)
    flags.AddNetworkFlag(parser)
    flags.AddSubnetFlag(parser)
    flags.AddManBlockFlagDeprecated(parser)
    flags.AddManBlocksFlag(parser)
    flags.AddClusterIPv4CIDRBlock(parser)
    flags.AddServicesIPv4CIDRBlack(parser)
    flags.AddClusterNamedRangeFlag(parser)
    flags.AddServicesNamedRange(parser)
    flags.AddFullManagement(parser)
    flags.AddUsePrivateEndpoint(parser)
    flags.AddExperimentalFeaturesFlag(parser)
