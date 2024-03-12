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
"""Flags and helpers for the compute networks peerings commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def AddImportCustomRoutesFlag(parser):
  """Adds importCustomRoutes flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--import-custom-routes',
      action='store_true',
      default=None,
      help="""\
        If set, the network will import custom routes from peer network. Use
        --no-import-custom-routes to disable it.
      """)


def AddExportCustomRoutesFlag(parser):
  """Adds exportCustomRoutes flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--export-custom-routes',
      action='store_true',
      default=None,
      help="""\
        If set, the network will export custom routes to peer network. Use
        --no-export-custom-routes to disable it.
      """)


def AddImportSubnetRoutesWithPublicIpFlag(parser):
  """Adds importSubnetRoutesWithPublicIp flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--import-subnet-routes-with-public-ip',
      action='store_true',
      default=None,
      help="""\
        If set, the network will import subnet routes with addresses in the
        public IP ranges from peer network.
        Use --no-import-subnet-routes-with-public-ip to disable it.
      """)


def AddExportSubnetRoutesWithPublicIpFlag(parser):
  """Adds exportSubnetRoutesWithPublicIp flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--export-subnet-routes-with-public-ip',
      action='store_true',
      default=None,
      help="""\
        If set, the network will export subnet routes with addresses in the
        public IP ranges to peer network.
        Use --no-export-subnet-routes-with-public-ip to disable it.
      """)


def AddStackType(parser):
  """Adds stackType flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--stack-type',
      default=None,
      help="""\
        Stack type of the peering. If not specified, defaults to IPV4_ONLY.

        STACK_TYPE must be one of:

         IPV4_ONLY
            Only IPv4 traffic and routes will be exchanged across this peering.

         IPV4_IPV6
            IPv4 traffic and routes will be exchanged across this peering.
            IPv6 traffic and routes will be exchanged if the matching peering
            configuration also has stack_type set to IPV4_IPV6.
      """)
