# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Shared resource flags for Network Security commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def _ServerTlsPolicyAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='server_tls_policy',
      help_text='ID of the server TLS policy for {resource}.',
  )


def _LocationAttributeConfig(region_fallthrough):
  fallthroughs = []
  if region_fallthrough:
    fallthroughs.append(deps.ArgFallthrough('--region'))
  fallthroughs.append(
      deps.Fallthrough(
          lambda: 'global', 'default value of location is [global]'
      )
  )
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='The Cloud location for the {resource}.',
      fallthroughs=fallthroughs,
  )


def _GetServerTlsPolicyResourceSpec(region_fallthrough):
  return concepts.ResourceSpec(
      'networksecurity.projects.locations.serverTlsPolicies',
      resource_name='server_tls_policy',
      serverTlsPoliciesId=_ServerTlsPolicyAttributeConfig(),
      locationsId=_LocationAttributeConfig(region_fallthrough),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def _GetServerTlsPolicyResourcePresentationSpec(
    flag,
    noun,
    verb,
    required=False,
    plural=False,
    group=None,
    region_fallthrough=False,
):
  """Returns ResourcePresentationSpec for server TLS policy resource.

  Args:
    flag: str, the flag name.
    noun: str, the resource.
    verb: str, the verb to describe the resource, such as 'to update'.
    required: bool, if False, means that map ID is optional.
    plural: bool.
    group: args group.
    region_fallthrough: bool, True if the command has a region flag that should
      be used as a fallthrough for the server TLS policy location.

  Returns:
    presentation_specs.ResourcePresentationSpec.
  """
  # 'location' flag is overridden to make it invisible in the documentation.
  flag_overrides = {'location': ''}
  return presentation_specs.ResourcePresentationSpec(
      flag,
      _GetServerTlsPolicyResourceSpec(region_fallthrough),
      '{} {}.'.format(noun, verb),
      required=required,
      plural=plural,
      group=group,
      flag_name_overrides=flag_overrides,
  )


def GetServerTlsPolicyResourceArg(
    verb,
    noun='The server TLS policy',
    name='server-tls-policy',
    required=False,
    plural=False,
    group=None,
    region_fallthrough=False,
):
  """Creates a resource argument for a Server TLS policy.

  Args:
    verb: str, the verb to describe the resource, such as 'to update'.
    noun: str, the resource; default: 'The server TLS policy'.
    name: str, the name of the flag.
    required: bool, if True the flag is required.
    plural: bool, if True the flag is a list.
    group: args group.
    region_fallthrough: bool, True if the command has a region flag that should
      be used as a fallthrough for the server TLS policy location.

  Returns:
    ServerTlsPolicyResourceArg: ConceptParser, holder for Server TLS policy
    argument.
  """
  return concept_parsers.ConceptParser([
      _GetServerTlsPolicyResourcePresentationSpec(
          '--' + name, noun, verb, required, plural, group, region_fallthrough
      ),
  ])


def GetClearServerTLSPolicyForHttpsProxy(name='clear-server-tls-policy'):
  """Returns the flag for clearing the Server TLS policy.

  Args:
    name: str, the name of the flag; default: 'clear-server-tls-policy'.
  """

  return base.Argument(
      '--' + name,
      action='store_true',
      default=False,
      required=False,
      help="""\
      Removes any attached Server TLS policy.
      """,
  )
