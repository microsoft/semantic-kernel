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

"""Command for uploading a route policy into a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import json
import os

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UploadRoutePolicy(base.SilentCommand):
  """Upload a route policy into a Compute Engine router.

  *{command}* uploads a route policy into a Compute Engine router.
  """

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    UploadRoutePolicy.ROUTER_ARG = flags.RouterArgument()
    UploadRoutePolicy.ROUTER_ARG.AddArgument(parser, operation_type='upload')
    parser.add_argument(
        '--policy-name', help='Name of the route policy to add/replace.'
    )
    parser.add_argument(
        '--file-name',
        required=True,
        help='Local path to the file defining the policy',
    )
    parser.add_argument(
        '--file-format',
        choices=['json', 'yaml'],
        help='Format of the file passed to --file-name',
    )

  def Run(self, args):
    """Issues the request necessary for uploading a route policy into a Router.

    Args:
      args: contains arguments passed to the command.

    Returns:
      The result of patching the router uploading the route policy.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    router_ref = UploadRoutePolicy.ROUTER_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    route_policy = self.ParseRoutePolicyFromFile(
        args.file_name, args.file_format, client.messages
    )
    self.EnsureSamePolicyName(args.policy_name, route_policy)

    request = (
        client.apitools_client.routers,
        'UpdateRoutePolicy',
        client.messages.ComputeRoutersUpdateRoutePolicyRequest(
            **router_ref.AsDict(), routePolicy=route_policy
        ),
    )

    return client.MakeRequests([request])[0]

  def EnsureSamePolicyName(self, policy_name, route_policy):
    if policy_name is not None and hasattr(route_policy, 'name'):
      if policy_name != route_policy.name:
        raise exceptions.BadArgumentException(
            'policy-name',
            'The policy name provided [{0}] does not match the one from the'
            ' file [{1}]'.format(policy_name, route_policy.name),
        )
    if not hasattr(route_policy, 'name') and policy_name is not None:
      route_policy.name = policy_name

  def ParseRoutePolicyFromFile(self, input_file, file_format, messages):
    # Get the imported route policy config.
    resource = self.ParseFile(input_file, file_format)
    if 'resource' in resource:
      resource = resource['resource']
    route_policy = messages_util.DictToMessageWithErrorCheck(
        resource, messages.RoutePolicy
    )
    if 'fingerprint' in resource:
      route_policy.fingerprint = base64.b64decode(resource['fingerprint'])
    return route_policy

  def ParseFile(self, input_file, file_format):
    if os.path.isdir(input_file):
      raise exceptions.BadFileException(
          '[{0}] is a directory'.format(input_file)
      )
    if not os.path.isfile(input_file):
      raise exceptions.BadFileException('No such file [{0}]'.format(input_file))
    try:
      with files.FileReader(input_file) as import_file:
        if file_format == 'json':
          return json.load(import_file)
        return yaml.load(import_file)
    except Exception as exp:
      msg = (
          'Unable to read route policy config from specified file [{0}]'
          ' because {1}'.format(input_file, exp)
      )
      raise exceptions.BadFileException(msg)
