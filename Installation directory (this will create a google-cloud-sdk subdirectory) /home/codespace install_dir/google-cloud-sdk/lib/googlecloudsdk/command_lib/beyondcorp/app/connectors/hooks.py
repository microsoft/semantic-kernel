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

"""Hooks for beyondcorp app connectors commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.beyondcorp.app import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.beyondcorp.app import util as command_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


def GetVersionedConnectorMsg(args, msg):
  if args.calliope_command.ReleaseTrack() == base.ReleaseTrack.ALPHA:
    return msg.GoogleCloudBeyondcorpAppconnectorsV1alphaAppConnector
  return msg.GoogleCloudBeyondcorpAppconnectorsV1AppConnector


def GetVersionedConnectorReq(args, req):
  if args.calliope_command.ReleaseTrack() == base.ReleaseTrack.ALPHA:
    return req.googleCloudBeyondcorpAppconnectorsV1alphaAppConnector
  return req.googleCloudBeyondcorpAppconnectorsV1AppConnector


def CheckFieldsSpecified(unused_ref, args, patch_request):
  """Check that update command has one of these flags specified."""
  update_args = [
      'clear_labels',
      'remove_labels',
      'update_labels',
      'display_name',
  ]
  if any(args.IsSpecified(update_arg) for update_arg in update_args):
    return patch_request
  raise exceptions.Error(
      'Must specify at least one field to update. Try --help.')


def UpdateLegacyLabels(unused_ref, args, patch_request):
  """Updates labels of connector."""
  labels_diff = labels_util.Diff.FromUpdateArgs(args)
  if labels_diff.MayHaveUpdates():
    patch_request = command_util.AddFieldToUpdateMask('labels', patch_request)
    messages = api_util.GetMessagesModule(args.calliope_command.ReleaseTrack())
    if patch_request.connector is None:
      patch_request.connector = messages.Connector()
    new_labels = labels_diff.Apply(messages.Connector.LabelsValue,
                                   patch_request.connector.labels).GetOrNone()
    if new_labels:
      patch_request.connector.labels = new_labels
  return patch_request


def UpdateLabels(unused_ref, args, patch_request):
  """Updates labels of appConnector."""
  labels_diff = labels_util.Diff.FromUpdateArgs(args)
  if labels_diff.MayHaveUpdates():
    patch_request = command_util.AddFieldToUpdateMask('labels', patch_request)
    messages = api_util.GetMessagesModule(args.calliope_command.ReleaseTrack())
    app_connector_msg = GetVersionedConnectorReq(args, patch_request)
    if app_connector_msg is None:
      app_connector_msg = GetVersionedConnectorMsg(args, messages)()
    new_labels = labels_diff.Apply(
        GetVersionedConnectorMsg(args, messages).LabelsValue,
        app_connector_msg.labels).GetOrNone()
    if new_labels:
      app_connector_msg.labels = new_labels
  return patch_request


def UpdateLabelsFlags():
  """Defines flags for updating labels."""
  return command_util.UpdateLabelsFlags()


def HideDetailsBeforeDescribing(response, args):
  """Hide details before describing a connector."""
  if args.details or response.resourceInfo is None:
    return response
  response.resourceInfo.resource = None
  response.resourceInfo.sub.clear()
  return response


def PrintMessageInResponse(response, unused_args):
  """Adds direction to use legacy to manage the old connector resources."""
  log.status.Print(
      'These commands now manage new app connector and connection resources. '
      "For old resources, please add 'legacy' in the command.\n"
      'e.g. gcloud alpha beyondcorp app legacy connectors')
  return response
