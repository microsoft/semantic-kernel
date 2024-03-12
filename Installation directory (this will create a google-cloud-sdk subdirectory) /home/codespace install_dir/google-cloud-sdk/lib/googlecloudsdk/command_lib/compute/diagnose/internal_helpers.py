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
"""Helpers for compute diagnose."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer


def PrintHeader(instances):
  """Prints the list of instances to which the command will work on."""
  if not instances:
    log.out.Print('No instances found.')
    return

  log.out.Print('The command will run for the following instances:')
  resource_printer.Print(instances, 'table(name, zone)')
  log.out.Print('')   # Separation


def GetInstanceNetworkTitleString(instance):
  """Returns a string that identifies the instance.

  Args:
    instance: The instance proto.

  Returns:
    A string that identifies the zone and the external ip of the instance.
  """
  external_ip = ssh_utils.GetExternalIPAddress(instance)

  result = '[{instance_name}] ({instance_ip})'.format(
      instance_name=instance.selfLink,
      instance_ip=external_ip)
  return result


def GetZoneFromInstance(instance, resource_registry):
  zone_ref = resource_registry.Parse(instance.zone, collection='compute.zones')
  return zone_ref.Name()
