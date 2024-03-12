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
"""Hooks for beyondcorp app connections commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.beyondcorp.app import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.beyondcorp.app import util as command_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

APP_ENDPOINT_PARSE_ERROR = ('Error parsing application endpoint [{}]: endpoint '
                            'must be prefixed of the form <host>:<port>.')

CONNECTOR_RESOURCE_NAME = ('projects/{}/locations/{}/connectors/{}')
APPCONNECTOR_RESOURCE_NAME = ('projects/{}/locations/{}/appConnectors/{}')
APPGATEWAY_RESOURCE_NAME = ('projects/{}/locations/{}/appGateways/{}')


def GetVersionedConnectionMsg(args, msg):
  if args.calliope_command.ReleaseTrack() == base.ReleaseTrack.ALPHA:
    return msg.GoogleCloudBeyondcorpAppconnectionsV1alphaAppConnection
  return msg.GoogleCloudBeyondcorpAppconnectionsV1AppConnection


def GetVersionedEndpointMsg(args, msg):
  if args.calliope_command.ReleaseTrack() == base.ReleaseTrack.ALPHA:
    return msg.GoogleCloudBeyondcorpAppconnectionsV1alphaAppConnectionApplicationEndpoint
  return msg.GoogleCloudBeyondcorpAppconnectionsV1AppConnectionApplicationEndpoint


def GetVersionedConnectionReq(args, req):
  if args.calliope_command.ReleaseTrack() == base.ReleaseTrack.ALPHA:
    return req.googleCloudBeyondcorpAppconnectionsV1alphaAppConnection
  return req.googleCloudBeyondcorpAppconnectionsV1AppConnection


class ApplicationEndpointParseError(exceptions.Error):
  """Error if a application endpoint is improperly formatted."""


def ValidateAndParseAppEndpoint(unused_ref, args, request):
  """Validates app endpoint format and sets endpoint host and port after parsing.

  Args:
    unused_ref: The unused request URL.
    args: arguments set by user.
    request: create connection request raised by framework.

  Returns:
    request with modified application endpoint host and port argument.

  Raises:
    ApplicationEndpointParseError:
  """
  if args.IsSpecified('application_endpoint'):
    endpoint_array = args.application_endpoint.split(':')
    if len(endpoint_array) == 2 and endpoint_array[1].isdigit():
      messages = api_util.GetMessagesModule(
          args.calliope_command.ReleaseTrack())
      app_connection = GetVersionedConnectionReq(args, request)
      if app_connection is None:
        app_connection = GetVersionedConnectionMsg(args, messages)()
      if app_connection.applicationEndpoint is None:
        app_connection.applicationEndpoint = GetVersionedEndpointMsg(
            args, messages)()
      app_connection.applicationEndpoint.host = endpoint_array[0]
      app_connection.applicationEndpoint.port = int(endpoint_array[1])
      if args.calliope_command.ReleaseTrack() == base.ReleaseTrack.ALPHA:
        request.googleCloudBeyondcorpAppconnectionsV1alphaAppConnection = app_connection
      else:
        request.googleCloudBeyondcorpAppconnectionsV1AppConnection = app_connection
    else:
      raise ApplicationEndpointParseError(
          APP_ENDPOINT_PARSE_ERROR.format(args.application_endpoint))
  return request


def ValidateAndParseLegacyAppEndpoint(unused_ref, args, request):
  """Validates app endpoint format and sets endpoint host and port after parsing.

  Args:
    unused_ref: The unused request URL.
    args: arguments set by user.
    request: create connection request raised by framework.

  Returns:
    request with modified application endpoint host and port argument.

  Raises:
    ApplicationEndpointParseError:
  """
  if args.IsSpecified('application_endpoint'):
    endpoint_array = args.application_endpoint.split(':')
    if len(endpoint_array) == 2 and endpoint_array[1].isdigit():
      messages = api_util.GetMessagesModule(
          args.calliope_command.ReleaseTrack())
      if request.connection is None:
        request.connection = messages.Connection()
      if request.connection.applicationEndpoint is None:
        request.connection.applicationEndpoint = messages.ApplicationEndpoint()
      request.connection.applicationEndpoint.host = endpoint_array[0]
      request.connection.applicationEndpoint.port = int(endpoint_array[1])
    else:
      raise ApplicationEndpointParseError(
          APP_ENDPOINT_PARSE_ERROR.format(args.application_endpoint))
  return request


def SetConnectors(unused_ref, args, request):
  """Set the connectors to resource based string format.

  Args:
    unused_ref: The unused request URL.
    args: arguments set by user.
    request: create connection request raised by framework.

  Returns:
    request with modified connectors argument.
  """

  if args.IsSpecified('connectors'):
    if not args.IsSpecified('project'):
      args.project = properties.VALUES.core.project.Get()
    for index, connector in enumerate(
        GetVersionedConnectionReq(args, request).connectors):
      if args.calliope_command.ReleaseTrack() == base.ReleaseTrack.ALPHA:
        request.googleCloudBeyondcorpAppconnectionsV1alphaAppConnection.connectors[
            index] = APPCONNECTOR_RESOURCE_NAME.format(args.project,
                                                       args.location, connector)
      else:
        request.googleCloudBeyondcorpAppconnectionsV1AppConnection.connectors[
            index] = APPCONNECTOR_RESOURCE_NAME.format(args.project,
                                                       args.location, connector)
  return request


def SetAppGateway(unused_ref, args, request):
  """Set the app gateway to resource based string format for beta release track.

  Args:
    unused_ref: The unused request URL.
    args: arguments set by user.
    request: create connection request raised by framework.

  Returns:
    request with modified app gateway argument.
  """
  if args.calliope_command.ReleaseTrack(
  ) == base.ReleaseTrack.BETA and args.IsSpecified('app_gateway'):
    if not args.IsSpecified('project'):
      args.project = properties.VALUES.core.project.Get()
    request.googleCloudBeyondcorpAppconnectionsV1AppConnection.gateway.appGateway = APPGATEWAY_RESOURCE_NAME.format(
        args.project, args.location,
        GetVersionedConnectionReq(args, request).gateway.appGateway)
  return request


def SetLegacyConnectors(unused_ref, args, request):
  """Set the connectors to legacy resource based string format.

  Args:
    unused_ref: The unused request URL.
    args: arguments set by user.
    request: create connection request raised by framework.

  Returns:
    request with modified connectors argument.
  """

  if args.IsSpecified('connectors'):
    if not args.IsSpecified('project'):
      args.project = properties.VALUES.core.project.Get()
    for index, connector in enumerate(request.connection.connectors):
      request.connection.connectors[index] = CONNECTOR_RESOURCE_NAME.format(
          args.project, args.location, connector)
  return request


def CheckFieldsSpecified(unused_ref, args, patch_request):
  """Check that update command has one of these flags specified."""
  update_args = [
      'clear_labels',
      'remove_labels',
      'update_labels',
      'display_name',
      'application_endpoint',
      'connectors',
  ]
  if any(args.IsSpecified(update_arg) for update_arg in update_args):
    return patch_request
  raise exceptions.Error(
      'Must specify at least one field to update. Try --help.')


def UpdateLegacyLabels(unused_ref, args, patch_request):
  """Updates labels of legacy connection."""
  labels_diff = labels_util.Diff.FromUpdateArgs(args)
  if labels_diff.MayHaveUpdates():
    patch_request = command_util.AddFieldToUpdateMask('labels', patch_request)
    messages = api_util.GetMessagesModule(args.calliope_command.ReleaseTrack())
    if patch_request.connection is None:
      patch_request.connection = messages.Connection()
    new_labels = labels_diff.Apply(messages.Connection.LabelsValue,
                                   patch_request.connection.labels).GetOrNone()
    if new_labels:
      patch_request.connection.labels = new_labels
  return patch_request


def UpdateLabels(unused_ref, args, patch_request):
  """Updates labels of connection."""
  labels_diff = labels_util.Diff.FromUpdateArgs(args)
  if labels_diff.MayHaveUpdates():
    patch_request = command_util.AddFieldToUpdateMask('labels', patch_request)
    messages = api_util.GetMessagesModule(args.calliope_command.ReleaseTrack())
    app_connection = GetVersionedConnectionReq(args, patch_request)
    if app_connection is None:
      app_connection = GetVersionedConnectionMsg(args, messages)()
    new_labels = labels_diff.Apply(
        GetVersionedConnectionMsg(args, messages).LabelsValue,
        app_connection.labels).GetOrNone()
    if new_labels:
      app_connection.labels = new_labels
  return patch_request


def UpdateApplicationEndpointMask(unused_ref, args, patch_request):
  """Updates application-endpoint mask."""
  if args.IsSpecified('application_endpoint'):
    patch_request = command_util.AddFieldToUpdateMask('application_endpoint',
                                                      patch_request)
  return patch_request


def UpdateLabelsFlags():
  """Defines flags for updating labels."""
  return command_util.UpdateLabelsFlags()


def PrintMessageInResponse(response, unused_args):
  """Adds direction to use legacy to manage the old connector resources."""
  log.status.Print(
      'These commands now manage new app connector and connection resources. '
      "For old resources, please add 'legacy' in the command.\n"
      'e.g. gcloud alpha beyondcorp app legacy connections')
  return response
