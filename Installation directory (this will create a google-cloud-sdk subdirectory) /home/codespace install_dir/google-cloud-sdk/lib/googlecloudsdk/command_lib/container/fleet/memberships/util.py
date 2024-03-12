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
"""Utils for Fleet memberships commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.container.fleet import api_util
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.memberships import errors


def SetInitProjectPath(ref, args, request):
  """Set the appropriate request path in project attribute for initializeHub requests.

  Args:
    ref: reference to the membership object.
    args: command line arguments.
    request: API request to be issued

  Returns:
    modified request
  """
  del ref, args  # Unused.
  request.project = request.project + '/locations/global/memberships'
  return request


def SetParentCollection(ref, args, request):
  """Set parent collection with location for created resources.

  Args:
    ref: reference to the membership object.
    args: command line arguments.
    request: API request to be issued

  Returns:
    modified request
  """
  del ref, args  # Unused.
  request.parent = request.parent + '/locations/-'
  return request


def SetMembershipLocation(ref, args, request):
  """Set membership location for requested resource.

  Args:
    ref: reference to the membership object.
    args: command line arguments.
    request: API request to be issued

  Returns:
    modified request
  """
  del ref  # Unused
  # If a membership is provided
  if args.IsKnownAndSpecified('membership'):
    if resources.MembershipLocationSpecified(args):
      request.name = resources.MembershipResourceName(args)
    else:
      request.name = resources.SearchMembershipResource(args)
  else:
    raise calliope_exceptions.RequiredArgumentException(
        'MEMBERSHIP', 'membership is required for this command.')

  return request


def ExecuteUpdateMembershipRequest(ref, args):
  """Set membership location for requested resource.

  Args:
    ref: API response from update membership call
    args: command line arguments.

  Returns:
    response
  """
  del ref
  if resources.MembershipLocationSpecified(args):
    name = resources.MembershipResourceName(args)
  else:
    name = resources.SearchMembershipResource(args)

  # Update membership from Fleet API.
  release_track = args.calliope_command.ReleaseTrack()
  obj = api_util.GetMembership(name, release_track)
  update_fields = []

  description = external_id = infra_type = None
  if release_track == calliope_base.ReleaseTrack.BETA and args.GetValue(
      'description'):
    update_fields.append('description')
    description = args.GetValue('description')
  if args.GetValue('external_id'):
    update_fields.append('externalId')
    external_id = args.GetValue('external_id')
  if release_track != calliope_base.ReleaseTrack.GA and args.GetValue(
      'infra_type'):
    update_fields.append('infrastructureType')
    infra_type = args.GetValue('infra_type')
  if args.GetValue('clear_labels') or args.GetValue(
      'update_labels') or args.GetValue('remove_labels'):
    update_fields.append('labels')
  update_mask = ','.join(update_fields)
  response = api_util.UpdateMembership(
      name,
      obj,
      update_mask,
      release_track,
      description=description,
      external_id=external_id,
      infra_type=infra_type,
      clear_labels=args.GetValue('clear_labels'),
      update_labels=args.GetValue('update_labels'),
      remove_labels=args.GetValue('remove_labels'),
      issuer_url=None,
      oidc_jwks=None,
      api_server_version=None,
      async_flag=args.GetValue('async'))

  return response


def GetConnectGatewayServiceName(endpoint_override, location):
  """Get the appropriate Connect Gateway endpoint.

  This function checks the environment endpoint overide configuration for
  Fleet and uses it to determine which Connect Gateway endpoint to use.
  The overridden Fleet value will look like
  https://autopush-gkehub.sandbox.googleapis.com/.

  When there is no override set, this command will return a Connect Gateway
  prod endpoint. When an override is set, an appropriate non-prod endpoint
  will be provided instead.

  For example, when the overridden value looks like
  https://autopush-gkehub.sandbox.googleapis.com/,
  the function will return
  autopush-connectgateway.sandbox.googleapis.com.

  Regional prefixes are supported via the location argument. For example, when
  the overridden value looks like
  https://autopush-gkehub.sandbox.googleapis.com/ and location is passed in as
  "us-west1", the function will return
  us-west1-autopush-connectgateway.sandbox.googleapis.com.

  Args:
    endpoint_override: The URL set as the API endpoint override for 'gkehub'.
      None if the override is not set.
    location: The location against which the command is supposed to run. This
      will be used to dynamically modify the service name to a location-specific
      value. If this is the value 'global' or None, a global service name is
      returned.

  Returns:
    The service name to use for this command invocation, optionally modified
    to target a specific location.

  Raises:
    UnknownApiEndpointOverrideError if the Fleet API endpoint override is not
    one of the standard values.
  """

  # Determine the location prefix, if any
  prefix = '' if location in ('global', None) else '{}-'.format(location)
  if (
      not endpoint_override
      or endpoint_override == 'https://gkehub.googleapis.com/'
  ):
    # Production, use full text match to avoid substring false positives
    return '{}connectgateway.googleapis.com'.format(prefix)
  elif 'autopush-gkehub' in endpoint_override:
    return '{}autopush-connectgateway.sandbox.googleapis.com'.format(prefix)
  elif 'staging-gkehub' in endpoint_override:
    return '{}staging-connectgateway.sandbox.googleapis.com'.format(prefix)
  else:
    raise errors.UnknownApiEndpointOverrideError('gkehub')
