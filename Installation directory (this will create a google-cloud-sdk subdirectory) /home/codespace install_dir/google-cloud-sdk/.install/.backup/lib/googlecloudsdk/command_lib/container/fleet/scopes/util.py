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
"""Utils for Fleet scopes commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.command_lib.util.args import labels_util


def SetParentCollection(ref, args, request):
  """Set parent collection with location for created resources.

  Args:
    ref: reference to the scope object.
    args: command line arguments.
    request: API request to be issued

  Returns:
    modified request
  """
  del ref, args  # Unused.
  request.parent = request.parent + '/locations/-'
  return request


def CheckUpdateArguments(ref, args, request):
  del ref, args  # Unused.
  if request.updateMask is None or not request.updateMask:
    request.updateMask = 'name'
  return request


def HandleNamespaceLabelsUpdateRequest(ref, args):
  """Add namespace labels to update request.

  Args:
    ref: reference to the scope object.
    args: command line arguments.

  Returns:
    response

  """
  mask = []
  release_track = args.calliope_command.ReleaseTrack()
  fleetclient = client.FleetClient(release_track)

  labels_diff = labels_util.Diff.FromUpdateArgs(args)
  namespace_labels_diff = labels_util.Diff(
      args.update_namespace_labels,
      args.remove_namespace_labels,
      args.clear_namespace_labels,
  )

  current_scope = fleetclient.GetScope(ref.RelativeName())

  # update GCP labels for namespace resource
  new_labels = labels_diff.Apply(
      fleetclient.messages.Scope.LabelsValue, current_scope.labels
  ).GetOrNone()
  if new_labels:
    mask.append('labels')

  # add cluster namespace level labels to resource
  new_namespace_labels = namespace_labels_diff.Apply(
      fleetclient.messages.Scope.NamespaceLabelsValue,
      current_scope.namespaceLabels,
  ).GetOrNone()
  if new_namespace_labels:
    mask.append('namespace_labels')

  # if there are no fields to update, don't make update api call
  if not mask:
    response = fleetclient.messages.Scope(name=ref.RelativeName())
    return response

  return fleetclient.UpdateScope(
      ref.RelativeName(), new_labels, new_namespace_labels, ','.join(mask)
  )


def HandleNamespaceLabelsCreateRequest(ref, args, request):
  """Add namespace labels to create request.

  Args:
    ref: reference to the scope object.
    args: command line arguments.
    request: API request to be issued

  Returns:
    modified request

  """
  del ref
  release_track = args.calliope_command.ReleaseTrack()
  fleetclient = client.FleetClient(release_track)
  namespace_labels_diff = labels_util.Diff(additions=args.namespace_labels)
  ns_labels = namespace_labels_diff.Apply(
      fleetclient.messages.Scope.NamespaceLabelsValue, None
  ).GetOrNone()
  request.scope.namespaceLabels = ns_labels
  return request
