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
"""Instance inventory gcloud commands declarative functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.command_lib.compute.os_config import flags
from googlecloudsdk.core import properties

import six

_LIST_URI = ('projects/{project}/locations/{location}/instances/-')
_DESCRIBE_URI = ('projects/{project}/locations/{location}'
                 '/instances/{instance}/inventory')


def SetParentOnListRequestHook(unused_ref, args, request):
  """Add parent field to list request.

  Args:
    unused_ref: A parsed resource reference; unused.
    args: The parsed args namespace from CLI
    request: List request for the API call

  Returns:
    Modified request that includes the name field.
  """
  project = properties.VALUES.core.project.GetOrFail()
  location = args.location or properties.VALUES.compute.zone.Get()

  flags.ValidateZone(location, '--location')

  request.parent = _LIST_URI.format(project=project, location=location)
  return request


def SetNameOnDescribeRequestHook(unused_ref, args, request):
  """Add name field to Describe request.

  Args:
    unused_ref: A parsed resource reference; unused.
    args: The parsed args namespace from CLI
    request: Describe request for the API call

  Returns:
    Modified request that includes the name field.
  """
  instance = args.instance
  project = properties.VALUES.core.project.GetOrFail()
  location = args.location or properties.VALUES.compute.zone.Get()

  flags.ValidateInstance(instance, 'INSTANCE')
  flags.ValidateZone(location, '--location')

  request.name = _DESCRIBE_URI.format(
      project=project, location=location, instance=instance)
  return request


class ListTableRow:
  """View model for table rows of inventories list."""

  def __init__(self, instance_id, instance_name, os_long_name,
               installed_packages, available_packages, update_time,
               osconfig_agent_version):
    self.instance_id = instance_id
    self.instance_name = instance_name
    self.os = os_long_name
    self.installed_packages = installed_packages
    self.available_packages = available_packages
    self.update_time = update_time
    self.osconfig_agent_version = osconfig_agent_version


def CreateTableViewResponseHook(inventory_list, args):
  """Create ListTableRow from ListInventory response.

  Args:
    inventory_list: Response from ListInventory
    args: gcloud invocation args

  Returns:
    ListTableRow
  """
  view = args.view if args.view else 'basic'
  rows = []
  for inventory in inventory_list:
    installed_packages = 0
    available_packages = 0
    if view == 'full' and inventory.items:
      for v in six.itervalues(encoding.MessageToDict(inventory.items)):
        if 'installedPackage' in v:
          installed_packages += 1
        elif 'availablePackage' in v:
          available_packages += 1
    rows.append(
        ListTableRow(
            instance_id=inventory.name.split('/')[-2],
            instance_name=inventory.osInfo.hostname,
            os_long_name=inventory.osInfo.longName,
            installed_packages=installed_packages,
            available_packages=available_packages,
            update_time=inventory.updateTime,
            osconfig_agent_version=inventory.osInfo.osconfigAgentVersion))
  return {view: rows}


class DescribeTableView:
  """View model for inventories describe."""

  def __init__(self, installed_packages, updatedable_packages,
               system_information):
    self.installed_packages = installed_packages
    self.updatedable_packages = updatedable_packages
    self.system_information = system_information


def CreateDescribeTableViewResponseHook(response, args):
  """Create DescribeTableView from GetInventory response.

  Args:
    response: Response from GetInventory
    args: gcloud invocation args

  Returns:
    DescribeTableView
  """
  installed = {}
  available = {}
  if response.osInfo:
    system_information = encoding.MessageToDict(response.osInfo)
  else:
    system_information = {}
  system_information['updateTime'] = response.updateTime
  if args.view == 'full' and response.items:
    for v in six.itervalues(encoding.MessageToDict(response.items)):
      if 'installedPackage' in v:
        dest = installed
        pkg = v['installedPackage']
      elif 'availablePackage' in v:
        dest = available
        pkg = v['availablePackage']
      else:
        continue
      for pkg_type in [
          'yumPackage', 'aptPackage', 'zypperPackage', 'googetPackage',
          'zypperPatch', 'wuaPackage', 'qfePackage', 'cosPackage',
          'windowsApplication'
      ]:
        if pkg_type in pkg:
          if pkg_type not in dest:
            dest[pkg_type] = []
          dest[pkg_type].append(pkg[pkg_type])
          break
  return DescribeTableView(installed, available, system_information)
