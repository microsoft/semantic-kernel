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
"""Flags for the config controller command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


def AddAsyncFlag(parser):
  """Adds --async flag."""
  base.ASYNC_FLAG.AddToParser(parser)


def AddMasterIPv4CIDRBlock(parser):
  """Adds --master-ipv4-cidr-block flag."""
  parser.add_argument(
      "--master-ipv4-cidr-block",
      help=("The /28 network that the control plane will use. "
            "Defaults to '172.16.0.128/28' if flag is not provided."))


def AddNetworkFlag(parser):
  """Adds --network flag."""
  parser.add_argument(
      "--network",
      help=("Existing VPC Network to put the GKE cluster and nodes in. "
            "Defaults to 'default' if flag is not provided. If "
            "`--subnet=SUBNET` is also specified, subnet must be a subnetwork "
            "of the network specified by this `--network=NETWORK` flag."))


def AddSubnetFlag(parser):
  """Adds --subnet flag."""
  parser.add_argument(
      "--subnet",
      help=("Specifies the subnet that the VM instances are a part of. "
            "`--network=NETWORK` must also be specified, subnet must be a "
            "subnetwork of the network specified by the `--network=NETWORK` "
            "flag."))


def AddManBlockFlag(parser):
  """Adds --man-block flag."""
  parser.add_argument(
      "--man-block",
      help=("Master Authorized Network. "
            "Allows access to the Kubernetes control plane from this block. "
            "Defaults to '0.0.0.0/0' if flag is not provided."))


def AddManBlockFlagDeprecated(parser):
  """Adds --man-block flag."""
  parser.add_argument(
      "--man-block",
      help=("Master Authorized Network. "
            "Allows access to the Kubernetes control plane from this block. "
            "Defaults to `0.0.0.0/0` if flag is not provided."),
      action=actions.DeprecationAction(
          "--man-block",
          warn="The {flag_name} option is deprecated; use --man-blocks instead.",
          removed=False))


def AddManBlocksFlag(parser):
  """Adds --man-blocks flag."""
  parser.add_argument(
      "--man-blocks",
      type=arg_parsers.ArgList(),
      metavar="BLOCK",
      help=("Master Authorized Network. "
            "Allows users to specify multiple blocks to access the Kubernetes"
            "control plane from this block. "
            "Defaults to `0.0.0.0/0` if flag is not provided."))


def AddClusterIPv4CIDRBlock(parser):
  """Adds --cluster-ipv4-cidr-block flag."""
  parser.add_argument(
      "--cluster-ipv4-cidr-block",
      help=("The IP address range for the cluster pod IPs. "
            "Can be specified as a netmask size (e.g. '/14') or as in CIDR "
            "notation (e.g. '10.100.0.0/20'). Defaults to '/20' if flag is "
            "not provided."))


def AddServicesIPv4CIDRBlack(parser):
  """Adds --services-ipv4-cidr-block flag."""
  parser.add_argument(
      "--services-ipv4-cidr-block",
      help=("The IP address range for the cluster service IPs. Can be "
            "specified as a netmask size (e.g. '/14') or as in CIDR "
            "notation (e.g. '10.100.0.0/20'). Defaults to '/24' if flag is "
            "not provided."))


def AddClusterNamedRangeFlag(parser):
  """Adds --cluster-named-range flag."""
  parser.add_argument(
      "--cluster-named-range",
      help=("The name of the existing secondary range in the clusters "
            "subnetwork to use for pod IP addresses. Alternatively, "
            "`--cluster_cidr_block` can be used to automatically create a "
            "GKE-managed one."))


def AddServicesNamedRange(parser):
  """Adds --services-named-range flag."""
  parser.add_argument(
      "--services-named-range",
      help=("The name of the existing secondary range in the clusters "
            "subnetwork to use for service ClusterIPs. Alternatively, "
            "`--services_cidr_block` can be used to automatically create a "
            "GKE-managed one."))


def AddFullManagement(parser):
  """Adds --full-management flag."""
  parser.add_argument(
      "--full-management",
      # Use store_const so that gcloud doesn't generate a hidden
      # --no-full-management flag. See yaqs/4400496223010684928 for more
      # details.
      action="store_const",
      const=True,
      help=("Enable full cluster management type. This is a preview feature."))


def AddUsePrivateEndpoint(parser):
  """Adds --use-private-endpoint flag."""
  parser.add_argument(
      "--use-private-endpoint",
      action="store_true",
      help=("Only allow access to the master's private endpoint IP."))


def AddExperimentalFeaturesFlag(parser):
  """Adds --experimental-features flag."""
  parser.add_argument(
      "--experimental-features",
      type=arg_parsers.ArgList(),
      metavar="FEATURE",
      help=("Enable experimental features. It can only be enabled in ALPHA "
            "version."))
