# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute machine-images commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      status
    )"""


def MakeSourceInstanceArg():
  return compute_flags.ResourceArgument(
      resource_name='instance',
      name='--source-instance',
      completer=compute_completers.InstancesCompleter,
      required=True,
      zonal_collection='compute.instances',
      short_help='The source instance to create a machine image from.',
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION)


def MakeMachineImageArg(plural=False):
  return compute_flags.ResourceArgument(
      name='IMAGE',
      resource_name='machineImage',
      completer=compute_completers.MachineImagesCompleter,
      plural=plural,
      global_collection='compute.machineImages')


def AddNetworkArgs(parser):
  """Set arguments for choosing the network/subnetwork."""
  parser.add_argument(
      '--network',
      help="""\
      Specifies the network for the VMs that are created from the imported
      machine image. If `--subnet` is also specified, then the subnet must
      be a subnetwork of network specified by `--network`. If neither is
      specified, the `default` network is used.
      """)

  parser.add_argument(
      '--subnet',
      help="""\
      Specifies the subnet for the VMs created from the imported machine
      image. If `--network` is also specified, the subnet must be
      a subnetwork of the network specified by `--network`.
      """)


def AddNoRestartOnFailureArgs(parser):
  parser.add_argument(
      '--restart-on-failure',
      action='store_true',
      default=True,
      help="""\
      The VMs created from the imported machine image are restarted if
      they are terminated by Compute Engine. This does not affect terminations
      performed by the user.
      """)


def AddTagsArgs(parser):
  parser.add_argument(
      '--tags',
      type=arg_parsers.ArgList(min_length=1),
      metavar='TAG',
      help="""\
      Specifies a list of tags to apply to the VMs created from the
      imported machine image. These tags allow network firewall rules and routes
      to be applied to specified VMs. See
      gcloud_compute_firewall-rules_create(1) for more details.

      To read more about configuring network tags, read this guide:
      https://cloud.google.com/vpc/docs/add-remove-network-tags

      To list VMs with their respective status and tags, run:

        $ gcloud compute instances list --format='table(name,status,tags.list())'

      To list VMs tagged with a specific tag, `tag1`, run:

        $ gcloud compute instances list --filter='tags:tag1'
      """)


def AddNetworkTierArgs(parser):
  """Adds network tier flag to the parser."""

  parser.add_argument(
      '--network-tier',
      type=lambda x: x.upper(),
      help="""\
        Specifies the network tier that will be used to configure the machine
        image. ``NETWORK_TIER'' must be one of: `PREMIUM`, `STANDARD`. The
        default value is `PREMIUM`.
        """
  )


def AddCanIpForwardArgs(parser):
  parser.add_argument(
      '--can-ip-forward',
      action='store_true',
      help="""\
        If provided, allows the VMs created from the imported machine
        image to send and receive packets with non-matching destination or
        source IP addresses.
        """
  )


def AddPrivateNetworkIpArgs(parser):
  """Set arguments for choosing the network IP address."""
  parser.add_argument(
      '--private-network-ip',
      help="""\
        Specifies the RFC1918 IP to assign to the VMs created from the
        imported machine image. The IP should be in the subnet or legacy network
        IP range.
      """)
