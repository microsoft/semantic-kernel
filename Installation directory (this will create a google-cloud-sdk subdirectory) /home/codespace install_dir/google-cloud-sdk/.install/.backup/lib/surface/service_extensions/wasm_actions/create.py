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
"""gcloud service-extensions wasm-actions create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.service_extensions import flags
from googlecloudsdk.command_lib.service_extensions import util
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


def _GetPossibleValuesOfSupportedEvents():
  """Returns the possible values of the --supported-events flag.

  Returns:
    List of strings.
  """
  return ['request-headers', 'response-headers']


def _ConvertStringSupportedEventToEnum(messages, supported_event):
  """Converts the text representation of an event to enum.

  Args:
    messages: module containing the definitions of messages for the API.
    supported_event: string, for example 'request_headers'.

  Returns:
    a value of messages.WasmAction.SupportedEventsValueListEntryValuesEnum,
    for example
    messages.WasmAction.SupportedEventsValueListEntryValuesEnum.REQUEST_HEADERS
  """
  uppercase_event = supported_event.upper().replace('-', '_')
  if not hasattr(messages.WasmAction.SupportedEventsValueListEntryValuesEnum,
                 uppercase_event):
    # This is theoretically possible if the list of allowed values of
    # --supported-events (returned by _GetPossibleValuesOfSupportedEvents())
    # contains values from the v1alpha1 version that are not yet visible
    # in v1.
    raise ValueError('Unsupported value: ' + supported_event)
  return getattr(messages.WasmAction.SupportedEventsValueListEntryValuesEnum,
                 uppercase_event)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a `WasmAction` resource."""

  detailed_help = {
      'DESCRIPTION':
          textwrap.dedent("""\
          Create a `WasmAction` resource that uses the specified plugin.
          """),
      'EXAMPLES':
          textwrap.dedent("""\
          To create a `WasmAction` called `my-action` using the
          `my-plugin` plugin, run:

          $ {command} my-action --wasm-plugin=my-plugin

          You may also specify the full resource path to a plugin, for example,
          `projects/my-project/locations/global/wasmPlugins/my-plugin`
          """)
  }

  @classmethod
  def Args(cls, parser):
    wasm_action_data = yaml_data.ResourceYAMLData.FromPath(
        'service_extensions.wasmAction')
    wasm_plugin_data = yaml_data.ResourceYAMLData.FromPath(
        'service_extensions.wasmPlugin')

    # Register the wasm_action and --wasm-plugin resource args. They
    # both provide a --location flag, so to avoid a conflict, we
    # configure --wasm-plugin to use wasm_action's location flag.
    concept_parsers.ConceptParser(
        [
            presentation_specs.ResourcePresentationSpec(
                'wasm_action',
                concepts.ResourceSpec.FromYaml(
                    wasm_action_data.GetData(),
                    api_version=util.GetApiVersion(cls.ReleaseTrack())),
                'The ID of the `WasmAction`.',
                required=True),
            presentation_specs.ResourcePresentationSpec(
                '--wasm-plugin',
                concepts.ResourceSpec.FromYaml(
                    wasm_plugin_data.GetData(),
                    api_version=util.GetApiVersion(cls.ReleaseTrack())),
                'ID of the `WasmPlugin` to use for this action.',
                flag_name_overrides={'location': ''},
                required=True)
        ],
        command_level_fallthroughs={
            '--wasm-plugin.location': ['wasm_action.location']
        }).AddToParser(parser)

    parser.add_argument(
        '--supported-events',
        type=arg_parsers.ArgList(choices=_GetPossibleValuesOfSupportedEvents()),
        required=False,
        metavar='EVENT',
        default=[],
        help=textwrap.dedent("""\
          Specify the portion of the request/response payload to be processed by
          the plugin."""),
    )
    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)
    flags.AddDescriptionFlag(parser)

  def Run(self, args):
    api_version = util.GetApiVersion(self.ReleaseTrack())
    messages = apis.GetMessagesModule('networkservices', api_version)

    wasm_action_ref = args.CONCEPTS.wasm_action.Parse()
    wasm_plugin_ref = args.CONCEPTS.wasm_plugin.Parse()
    labels = labels_util.ParseCreateArgs(args, messages.WasmAction.LabelsValue)

    converted_events = [
        _ConvertStringSupportedEventToEnum(messages, event)
        for event in args.supported_events]

    request = messages.NetworkservicesProjectsLocationsWasmActionsCreateRequest(
        parent=wasm_action_ref.Parent().RelativeName(),
        wasmActionId=wasm_action_ref.Name(),
        wasmAction=messages.WasmAction(
            wasmPlugin=wasm_plugin_ref.RelativeName(),
            description=args.description,
            labels=labels,
            supportedEvents=converted_events,
        ),
    )

    # Issue the create request, which returns an operation.
    client = apis.GetClientInstance('networkservices', api_version)
    op_ref = client.projects_locations_wasmActions.Create(request)

    log.status.Print('Create request issued for: [{}]'.format(
        wasm_action_ref.Name()))

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    # Wait for the operation to complete.
    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='networkservices.projects.locations.operations',
        api_version=api_version)
    poller = waiter.CloudOperationPoller(client.projects_locations_wasmActions,
                                         client.projects_locations_operations)
    result = waiter.WaitFor(
        poller, op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name))

    log.status.Print('Created WasmAction [{}].'.format(wasm_action_ref.Name()))

    return result
