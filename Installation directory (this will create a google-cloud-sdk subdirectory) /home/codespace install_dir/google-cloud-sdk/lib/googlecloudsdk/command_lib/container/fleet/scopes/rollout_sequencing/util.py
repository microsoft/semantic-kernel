# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utils for Fleet Scopes Cluster Upgrade Feature command preparations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container.fleet.scopes.rollout_sequencing import base
from googlecloudsdk.core import log


def DescribeClusterUpgrade(response, args):
  """Adds Cluster Upgrade Feature information to describe Scope request.

  This is a modify_request_hook for gcloud declarative YAML.

  Args:
    response: Scope message.
    args: command line arguments.

  Returns:
    response with optional Cluster Upgrade Feature information
  """
  cmd = base.DescribeCommand(args)
  if cmd.IsClusterUpgradeRequest():
    feature = cmd.GetFeature()
    return cmd.GetScopeWithClusterUpgradeInfo(response, feature)
  return response


# TODO(b/257544684): Remove this once scope update IAM permission is ready.
def HandleUpdateRequest(ref, args):
  cmd = base.UpdateCommand(args)
  response = cmd.hubclient.messages.Scope(name=ref.RelativeName())
  return response


def UpdateClusterUpgrade(response, args):
  """Updates Cluster Upgrade feature.

  Args:
    response: reference to the Scope object.
    args: command line arguments.

  Returns:
    response
  """
  update_cmd = base.UpdateCommand(args)
  if update_cmd.IsClusterUpgradeRequest():
    # This code should be unreachable due to the ValidateAsync modify request
    # hook, but the warning has been included as a safety measure if something
    # goes wrong.
    if args.IsKnownAndSpecified('async_') and args.async_:
      msg = ('Both --async and Rollout Sequencing flag(s) specified. Cannot '
             'modify cluster upgrade feature until scope operation has '
             'completed. Ignoring Rollout Sequencing flag(s). Use synchronous '
             'update command to apply desired cluster upgrade feature changes '
             'to the current scope.')
      log.warning(msg)
      return response

    enable_cmd = base.EnableCommand(args)
    feature = enable_cmd.GetWithForceEnable()
    scope_name = base.ClusterUpgradeCommand.GetScopeNameWithProjectNumber(
        response.name)
    updated_feature = update_cmd.Update(feature, scope_name)
    describe_cmd = base.DescribeCommand(args)
    return describe_cmd.AddClusterUpgradeInfoToScope(response, scope_name,
                                                     updated_feature)
  return response


def ValidateAsync(ref, args, request):
  # Free up unused ref argument that is required for modify request hooks.
  del ref
  cmd = base.ClusterUpgradeCommand(args)
  is_async = (args.IsKnownAndSpecified('async_') and args.async_)
  if cmd.IsClusterUpgradeRequest() and is_async:
    raise exceptions.ConflictingArgumentsException(
        '--async cannot be specified with Rollout Sequencing flags')
  return request


class UpgradeSelector(arg_parsers.ArgDict):
  """Extends the ArgDict type to properly parse --upgrade-selector argument."""

  def __init__(self):
    super(UpgradeSelector, self).__init__(
        spec={'name': str, 'version': str},
        required_keys=['name', 'version'],
        max_length=2,
    )
