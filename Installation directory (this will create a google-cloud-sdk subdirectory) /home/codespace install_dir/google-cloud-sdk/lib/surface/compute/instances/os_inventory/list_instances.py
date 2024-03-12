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
"""Command for listing instances with specific OS inventory data values."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import json
import os
import zlib

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.resource import resource_projector


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class ListInstances(base.ListCommand):
  r"""List instances with specific OS inventory data values.

  {command} displays all Compute Engine instances in a project matching
  an inventory filter. Run $ gcloud topic filters to see the supported filter
  syntax.

  ## EXAMPLES

  To list all instances with OS inventory data in a project in table form, run:

        $ {command}

  To list the URIs of all instances whose OS short name contains rhel, run:

        $ {command} --inventory-filter="ShortName:rhel" --uri

  To list the URIs of all instances whose OS short name is equal to rhel, run:

        $ {command} --os-shortname="rhel" --uri

  To list all instances with package google-cloud-sdk of version 235.0.0-0
  installed, run:

        $ {command} --package-name="google-cloud-sdk" \
        --package-version="235.0.0-0"

  To list all instances with package name matching a regex ^google-cloud*
  available for update through apt, run:

        $ {command} --inventory-filter="\
        PackageUpdates.apt[].Name~^google-cloud*"

  To list all instances with package update google-cloud-sdk of version greater
  than or equal to 235.0.0-0 available through apt, run:

        $ {command} --inventory-filter="\
        PackageUpdates.apt[].['google-cloud-sdk'].Version>=235.0.0-0"

  To list all instances missing the Stackdriver monitoring package
  stackdriver-agent, run:

        $ {command} --inventory-filter="\
        NOT(InstalledPackages:stackdriver-agent)"

  To list all Windows instances with an installed qfe hotfix whose ID equals
  KB4462930, run:

        $ {command} --inventory-filter="\
        InstalledPackages.qfe[].HotFixID=KB4462930"

  To list all Windows instances with a wua update whose description contains the
  word Security, run:

        $ {command} --inventory-filter="\
        InstalledPackages.wua[].Description:Security"

  """

  _GUEST_ATTRIBUTES_PACKAGE_FIELD_KEYS = ('InstalledPackages', 'PackageUpdates')

  _SPECIAL_PACKAGE_MANAGERS = ('wua', 'qfe', 'zypperPatches')
  _REGULAR_PACKAGE_MANAGERS = ('cos', 'deb', 'googet', 'rpm', 'gem', 'pip')

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    parser.display_info.AddUriFunc(utils.MakeGetUriFunc())
    parser.display_info.AddCacheUpdater(completers.InstancesCompleter)
    parser.add_argument(
        '--inventory-filter',
        type=str,
        help="""Filter expression for matching against OS inventory criteria""")
    filter_group = parser.add_group(
        help='Exact match values for OS inventory data:')
    filter_group.add_argument(
        '--os-shortname',
        type=str,
        help="""If specified, only instances with this OS shortname in their
        inventory data will be displayed.""")
    filter_group.add_argument(
        '--os-version',
        type=str,
        help="""If specified, only instances with this OS version in their
        inventory data will be displayed.""")
    filter_group.add_argument(
        '--kernel-version',
        type=str,
        help="""If specified, only instances with this kernel version in their
        inventory data will be displayed.""")
    filter_group.add_argument(
        '--package-name',
        type=str,
        help="""If specified, only instances with an installed package of this
        name in their inventory data will be displayed.""")
    filter_group.add_argument(
        '--package-version',
        type=str,
        help="""If specified with a package name, only instances with the
        installed package of this version in their inventory data will be
        displayed.""")

  def _GetGuestAttributesRequest(self, messages, instance_name, project, zone):
    return messages.ComputeInstancesGetGuestAttributesRequest(
        instance=instance_name,
        project=project,
        queryPath='guestInventory/',
        zone=zone)

  def _GetAllGuestInventoryGuestAttributes(self, holder, instances):
    client = holder.client
    messages = client.messages
    project = properties.VALUES.core.project.GetOrFail()

    requests = [
        self._GetGuestAttributesRequest(messages, instance['name'], project,
                                        os.path.basename(instance['zone']))
        for instance in instances
    ]
    responses = holder.client.AsyncRequests(
        [
            (client.apitools_client.instances, 'GetGuestAttributes', request)
            for request in requests
        ]
    )

    for response in filter(None, responses):
      for item in response.queryValue.items:
        if item.key in self._GUEST_ATTRIBUTES_PACKAGE_FIELD_KEYS:
          item.value = zlib.decompress(
              base64.b64decode(item.value), zlib.MAX_WBITS | 32)
    return responses

  def _GetFormattedGuestAttributes(self, guest_attributes):
    guest_attributes_json = resource_projector.MakeSerializable(
        guest_attributes)

    formatted_guest_attributes = {}
    for guest_attribute in guest_attributes_json:
      guest_attribute_key = guest_attribute['key']

      # Only reformat the guest attribute value
      # for certain fields that contain JSON data.
      if guest_attribute_key in self._GUEST_ATTRIBUTES_PACKAGE_FIELD_KEYS:
        formatted_packages_info = {}
        guest_attribute_json = json.loads(guest_attribute['value'])
        for package_manager, package_list in guest_attribute_json.items():
          if package_manager in self._SPECIAL_PACKAGE_MANAGERS:
            # No reformatting for special package managers.
            formatted_packages_info[package_manager] = package_list
          else:
            # Reformat package info published by standard package managers
            formatted_packages_list = []
            for package in package_list:
              name = package['Name']
              info = {'Arch': package['Arch'], 'Version': package['Version']}
              formatted_packages_list.append({'Name': name, name: info})
            formatted_packages_info[package_manager] = formatted_packages_list
        guest_attribute['value'] = formatted_packages_info

      formatted_guest_attributes[guest_attribute_key] = guest_attribute['value']

    return json.loads(json.dumps(formatted_guest_attributes))

  def _GetInventoryFilteredInstances(self, instances, responses, query):
    filtered_instances = []

    for instance, response in zip(instances, responses):
      # No listing instances without inventory data.
      if instance is not None and response is not None:
        guest_attributes = response.queryValue.items
        formatted_guest_attributes_json = self._GetFormattedGuestAttributes(
            guest_attributes)
        if query.Evaluate(formatted_guest_attributes_json):
          filtered_instances.append(instance)

    return filtered_instances

  def _GetInventoryFilterQuery(self, args):
    query_list = []

    def _AppendQuery(query):
      query_list.append('({})'.format(query))

    if args.inventory_filter:
      _AppendQuery(args.inventory_filter)
    if args.os_shortname:
      _AppendQuery('ShortName=' + args.os_shortname)
    if args.os_version:
      _AppendQuery('Version=' + args.os_version)
    if args.kernel_version:
      _AppendQuery('KernelVersion=' + args.kernel_version)

    installed_packages_query_prefixes = [
        'InstalledPackages.' + package_manager + '[].'
        for package_manager in self._REGULAR_PACKAGE_MANAGERS
    ]
    if args.package_version:
      if not args.package_name:
        raise exceptions.InvalidArgumentException(
            '--package-version',
            'package version must be specified together with a package name. '
            'e.g. --package-name google-cloud-sdk --package-version 235.0.0-0')
      else:
        package_name = '[\'{}\']'.format(args.package_name)
        _AppendQuery(' OR '.join([
            '({})'.format(prefix + package_name + '.Version=' +
                          args.package_version)
            for prefix in installed_packages_query_prefixes
        ]))
    else:
      if args.package_name:
        _AppendQuery(' OR '.join([
            '({})'.format(prefix + 'Name=' + args.package_name)
            for prefix in installed_packages_query_prefixes
        ]))

    return ' AND '.join(query_list)

  def Run(self, args):
    query = resource_filter.Compile(self._GetInventoryFilterQuery(args))

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)
    list_implementation = lister.MultiScopeLister(
        client,
        zonal_service=client.apitools_client.instances,
        aggregation_service=client.apitools_client.instances)

    instances_iterator = lister.Invoke(request_data, list_implementation)
    instances = list(instances_iterator)

    responses = self._GetAllGuestInventoryGuestAttributes(holder, instances)
    return self._GetInventoryFilteredInstances(instances, responses, query)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListInstancesAlpha(ListInstances):
  r"""List instances with specific OS inventory data values.

  {command} displays all Google Compute Engine instances in a project matching
  an inventory filter. Run $ gcloud topic filters to see the supported filter
  syntax.

  ## EXAMPLES

  To list all instances with OS inventory data in a project in table form, run:

        $ {command}

  To list the URIs of all instances whose OS short name contains rhel, run:

        $ {command} --inventory-filter="ShortName:rhel" --uri

  To list the URIs of all instances whose OS short name is equal to rhel, run:

        $ {command} --os-shortname="rhel" --uri

  To list all instances with package google-cloud-sdk of version 235.0.0-0
  installed, run:

        $ {command} --package-name="google-cloud-sdk" \
        --package-version="235.0.0-0"

  To list all instances with package name matching a regex ^google-cloud*
  available for update through apt, run:

        $ {command} --inventory-filter="\
        PackageUpdates.apt[].Name~^google-cloud*"

  To list all instances with package update google-cloud-sdk of version greater
  than or equal to 235.0.0-0 available through apt, run:

        $ {command} --inventory-filter="\
        PackageUpdates.apt[].['google-cloud-sdk'].Version>=235.0.0-0"

  To list all instances missing the Stackdriver monitoring package
  stackdriver-agent, run:

        $ {command} --inventory-filter="\
        NOT(InstalledPackages:stackdriver-agent)"

  To list all Windows instances with an installed qfe hotfix whose ID equals
  KB4462930, run:

        $ {command} --inventory-filter="\
        InstalledPackages.qfe[].HotFixID=KB4462930"

  To list all Windows instances with a wua update whose description contains the
  word Security, run:

        $ {command} --inventory-filter="\
        InstalledPackages.wua[].Description:Security"

  """
