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
"""Command for describing instance's OS inventory data."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import json
import zlib

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.command_lib.compute.instances.os_inventory import exceptions
from googlecloudsdk.core.resource import resource_projector
import six


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe a Compute Engine virtual instance's OS inventory data.

  *{command}* displays all OS inventory data associated with a Compute
  Engine virtual machine instance.

  ## EXAMPLES

  To see OS inventory of an instance named my-instance, run:

        $ {command} my-instance
  """

  _GUEST_ATTRIBUTES_PACKAGE_FIELD_KEYS = ('InstalledPackages', 'PackageUpdates')

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser, operation_type='describe')

    parser.display_info.AddFormat("""
          multi(
            InstalledPackages.cos:format=
              "table[box,title='Installed Packages (COS)']
                (Name:sort=1,Version)",
            InstalledPackages.deb:format=
              "table[box,title='Installed Packages (DEB)']
                (Name:sort=1,Arch,Version)",
            InstalledPackages.gem:format=
              "table[box,title='Installed Packages (Gem)']
                (Name:sort=1,Arch,Version)",
            InstalledPackages.googet:format=
              "table[box,title='Installed Packages (GooGet)']
                (Name:sort=1,Arch,Version)",
            InstalledPackages.pip:format=
              "table[box,title='Installed Packages (Pip)']
                (Name:sort=1,Arch,Version)",
            InstalledPackages.rpm:format=
              "table[box,title='Installed Packages (RPM)']
                (Name:sort=1,Arch,Version)",
            InstalledPackages.zypperPatches:format=
              "table[box,title='Installed Patches (Zypper Patch)'](
                Name:sort=1,
                Category,
                Severity,
                Summary:wrap=14)",
            InstalledPackages.wua:format=
              "table[all-box,title='Installed Packages (Windows Update Agent)'](
                Title:sort=1:wrap,
                Categories.list():wrap,
                KBArticleIDs.list():wrap=14,
                SupportURL:wrap=11,
                LastDeploymentChangeTime:wrap=15:label='LAST_DEPLOYMENT')",
            InstalledPackages.qfe:format=
              "table[box,title='Installed Packages (Quick Fix Engineering)']
                (Caption,Description:wrap=15,HotFixID:sort=1,InstalledOn)",
            PackageUpdates.apt:format=
              "table[box,title='Package Updates Available (Apt)']
                (Name:sort=1,Arch,Version)",
            PackageUpdates.gem:format=
              "table[box,title='Package Updates Available (Gem)']
                (Name:sort=1,Arch,Version)",
            PackageUpdates.googet:format=
              "table[box,title='Package Updates Available (GooGet)']
                (Name:sort=1,Arch,Version)",
            PackageUpdates.pip:format=
              "table[box,title='Package Updates Available (Pip)']
                (Name:sort=1,Arch,Version)",
            PackageUpdates.yum:format=
              "table[box,title='Package Updates Available (Yum)']
                (Name:sort=1,Arch,Version)",
            PackageUpdates.zypperPatches:format=
              "table[box,title='Patches Available (Zypper Patch)'](
                Name:sort=1,
                Category,
                Severity,
                Summary:wrap=14)",
            PackageUpdates.wua:format=
              "table[all-box,title='Package Updates Available (Windows Update Agent)'](
                Title:sort=1:wrap,
                Categories.list():wrap,
                KBArticleIDs.list():wrap=14,
                SupportURL:wrap=11,
                LastDeploymentChangeTime:wrap=15:label='LAST_DEPLOYMENT')",
            SystemInformation:format="default"
          )
        """)

  def _GetInstanceRef(self, holder, args):
    return flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(holder.client))

  def _GetGuestInventoryGuestAttributes(self, holder, instance_ref):
    try:
      client = holder.client
      messages = client.messages
      request = messages.ComputeInstancesGetGuestAttributesRequest(
          instance=instance_ref.Name(),
          project=instance_ref.project,
          queryPath='guestInventory/',
          zone=instance_ref.zone)
      response = holder.client.MakeRequests(
          [(holder.client.apitools_client.instances, 'GetGuestAttributes',
            request)])[0]

      for item in response.queryValue.items:
        if item.key in self._GUEST_ATTRIBUTES_PACKAGE_FIELD_KEYS:
          item.value = zlib.decompress(
              base64.b64decode(item.value), zlib.MAX_WBITS | 32)

      return response.queryValue.items
    except calliope_exceptions.ToolException as e:
      if ('The resource \'guestInventory/\' of type \'Guest Attribute\' was not'
          ' found.') in six.text_type(e):
        problems = [
            (404,
             'OS inventory data was not found. Make sure the OS Config agent '
             'is running on this instance.')
        ]
        utils.RaiseException(
            problems,
            exceptions.OsInventoryNotFoundException,
            error_message='Could not fetch resource:')
      raise e

  def _GetFormattedGuestAttributes(self, guest_attributes):
    guest_attributes_json = resource_projector.MakeSerializable(
        guest_attributes)

    formatted_guest_attributes = {'SystemInformation': {}}
    for guest_attribute in guest_attributes_json:
      guest_attribute_key = guest_attribute['key']

      # Only reformat the guest attribute value
      # for certain fields that contain JSON data.
      if guest_attribute_key in self._GUEST_ATTRIBUTES_PACKAGE_FIELD_KEYS:
        formatted_guest_attributes[guest_attribute_key] = json.loads(
            guest_attribute['value'])
      else:
        formatted_guest_attributes['SystemInformation'][
            guest_attribute_key] = guest_attribute['value']

    return json.loads(json.dumps(formatted_guest_attributes))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    instance_ref = self._GetInstanceRef(holder, args)
    guest_attributes_json = self._GetGuestInventoryGuestAttributes(
        holder, instance_ref)
    return self._GetFormattedGuestAttributes(guest_attributes_json)
