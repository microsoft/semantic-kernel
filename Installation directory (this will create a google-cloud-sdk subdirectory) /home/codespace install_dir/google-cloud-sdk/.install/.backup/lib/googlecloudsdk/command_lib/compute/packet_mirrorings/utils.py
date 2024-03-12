# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Helpers for the compute packet mirroring commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import six


def ResolveNetworkURI(project, network, resource_parser):
  """Resolves the URI of a network."""
  if project and network and resource_parser:
    return six.text_type(
        resource_parser.Parse(
            network, collection='compute.networks',
            params={'project': project}))
  return None


def ResolveInstanceURI(project, instance, resource_parser):
  """Resolves the URI of an instance."""
  if project and instance and resource_parser:
    return six.text_type(
        resource_parser.Parse(
            instance,
            collection='compute.instances',
            params={'project': project}))
  return None


def ResolveSubnetURI(project, region, subnet, resource_parser):
  """Resolves the URI of a subnet."""
  if project and region and subnet and resource_parser:
    return six.text_type(
        resource_parser.Parse(
            subnet,
            collection='compute.subnetworks',
            params={
                'project': project,
                'region': region
            }))
  return None


def ResolveForwardingRuleURI(project, region, forwarding_rule, resource_parser):
  """Resolves the URI of a forwarding rule."""
  if project and region and forwarding_rule and resource_parser:
    return six.text_type(
        resource_parser.Parse(
            forwarding_rule,
            collection='compute.forwardingRules',
            params={
                'project': project,
                'region': region
            }))
  return None
