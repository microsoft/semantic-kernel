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
"""Implements command to look up all effective guest policies of an instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_projector
import six


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Lookup(base.Command):
  """Display the guest policies that are applied to an instance.

  ## EXAMPLES

    To view all guest policies that are applied to an instance named
    `my-instance`, run:

          $ {command} my-instance

  """

  _OS_ARCHITECTURE_KEY = 'Architecture'
  _OS_SHORTNAME_KEY = 'ShortName'
  _OS_VERSION_KEY = 'Version'
  _OS_INFO_FIELD_KEYS = (_OS_ARCHITECTURE_KEY, _OS_SHORTNAME_KEY,
                         _OS_VERSION_KEY)

  def _GetInstanceRef(self, holder, args):
    return flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(holder.client),
    )

  def _GetGuestInventoryGuestAttributes(self, instance_ref):
    try:
      holder = base_classes.ComputeApiHolder(base.ReleaseTrack.GA)
      client = holder.client
      messages = client.messages
      request = messages.ComputeInstancesGetGuestAttributesRequest(
          instance=instance_ref.Name(),
          project=instance_ref.project,
          queryPath='guestInventory/',
          zone=instance_ref.zone)
      response = client.apitools_client.instances.GetGuestAttributes(request)
      return response.queryValue.items
    except Exception as e:
      if ('The resource \'guestInventory/\' of type \'Guest Attribute\' was not'
          ' found.') in six.text_type(e):
        return []
      raise e

  def _GetOsInfo(self, guest_attributes):
    guest_attributes_json = resource_projector.MakeSerializable(
        guest_attributes)

    os_info = {}
    for guest_attribute in guest_attributes_json:
      guest_attribute_key = guest_attribute['key']
      if guest_attribute_key in self._OS_INFO_FIELD_KEYS:
        os_info[guest_attribute_key] = guest_attribute['value']

    return os_info

  def _CreateRequest(self, messages, instance_name, os_architecture,
                     os_shortname, os_version):
    return messages.OsconfigProjectsZonesInstancesLookupEffectiveGuestPolicyRequest(
        instance=instance_name,
        lookupEffectiveGuestPolicyRequest=messages
        .LookupEffectiveGuestPolicyRequest(
            osArchitecture=os_architecture,
            osShortName=os_shortname,
            osVersion=os_version,
        ),
    )

  def _GetResponse(self, service, request):
    return service.LookupEffectiveGuestPolicy(request)

  @staticmethod
  def Args(parser):
    """See base class."""
    flags.INSTANCE_ARG.AddArgument(
        parser, operation_type='look up guest policies for')
    parser.display_info.AddFormat("""
      table(
        packages:format="table[box,title="PACKAGES"](
          source,
          package.name,
          package.desiredState,
          package.manager,
          package.version)",
        packageRepositories:format="table[box,title='PACKAGE REPOSITORIES'](
          source,
          packageRepository.apt:format='table[box,title="APT"](
            uri,
            distribution,
            components.list())',
          packageRepository.goo:format='table[box,title="GOO"](
            name,
            url)',
          packageRepository.yum:format='table[box,title="YUM"](
            id,
            baseUrl)',
          packageRepository.zypper:format='table[box,title="ZYPPER"](
            id,
            baseUrl)')",
        softwareRecipes:format="table[box,title='SOFTWARE RECIPES'](
          source,
          softwareRecipe.name,
          softwareRecipe.version,
          softwareRecipe.desiredState
        )"
      )
    """)

  def Run(self, args):
    """See base class."""
    release_track = self.ReleaseTrack()

    holder = base_classes.ComputeApiHolder(release_track)
    instance_ref = self._GetInstanceRef(holder, args)

    guest_attributes = self._GetGuestInventoryGuestAttributes(instance_ref)
    os_info = self._GetOsInfo(guest_attributes)
    os_architecture = os_info.get(self._OS_ARCHITECTURE_KEY)
    os_shortname = os_info.get(self._OS_SHORTNAME_KEY)
    os_version = os_info.get(self._OS_VERSION_KEY)

    client = osconfig_api_utils.GetClientInstance(release_track)
    messages = osconfig_api_utils.GetClientMessages(release_track)

    request = self._CreateRequest(messages, instance_ref.RelativeName(),
                                  os_architecture, os_shortname, os_version)
    response = self._GetResponse(client.projects_zones_instances, request)

    if not any([
        response.packages, response.packageRepositories,
        response.softwareRecipes
    ]):
      log.status.Print('No effective guest policy found for [{}].'.format(
          instance_ref.RelativeName()))

    return response
