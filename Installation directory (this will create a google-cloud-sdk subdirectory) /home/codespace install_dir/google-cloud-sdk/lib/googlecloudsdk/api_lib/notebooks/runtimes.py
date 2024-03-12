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
"""notebooks runtimes api helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
from googlecloudsdk.api_lib.notebooks import util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


def CreateRuntime(args, messages):
  """Creates the Runtime message for the create request.

  Args:
    args: Argparse object from Command.Run
    messages: Module containing messages definition for the specified API.

  Returns:
    Runtime of the Runtime message.
  """

  def GetRuntimeVirtualMachineFromArgs():
    machine_type = 'n1-standard-4'
    if args.IsSpecified('machine_type'):
      machine_type = args.machine_type
    virtual_machine_config = messages.VirtualMachineConfig(
        machineType=machine_type, dataDisk=messages.LocalDisk())
    return messages.VirtualMachine(virtualMachineConfig=virtual_machine_config)

  def GetRuntimeAccessConfigFromArgs():
    runtime_access_config = messages.RuntimeAccessConfig
    type_enum = None
    if args.IsSpecified('runtime_access_type'):
      type_enum = arg_utils.ChoiceEnumMapper(
          arg_name='runtime-access-type',
          message_enum=runtime_access_config.AccessTypeValueValuesEnum,
          include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
              arg_utils.EnumNameToChoice(args.runtime_access_type))
    return runtime_access_config(
        accessType=type_enum, runtimeOwner=args.runtime_owner)

  def GetPostStartupScriptBehavior():
    type_enum = None
    if args.IsSpecified('post_startup_script_behavior'):
      runtime_software_config_message = messages.RuntimeSoftwareConfig
      type_enum = arg_utils.ChoiceEnumMapper(
          arg_name='post-startup-script-behavior',
          message_enum=(runtime_software_config_message
                        .PostStartupScriptBehaviorTypeValueValuesEnum),
          include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
              arg_utils.EnumNameToChoice(args.post_startup_script_behavior))
    return type_enum

  def GetRuntimeSoftwareConfigFromArgs():
    runtime_software_config = messages.RuntimeSoftwareConfig()
    if args.IsSpecified('idle_shutdown_timeout'):
      runtime_software_config.idleShutdownTimeout = args.idle_shutdown_timeout
    if args.IsSpecified('install_gpu_driver'):
      runtime_software_config.installGpuDriver = args.install_gpu_driver
    if args.IsSpecified('custom_gpu_driver_path'):
      runtime_software_config.customGpuDriverPath = args.custom_gpu_driver_path
    if args.IsSpecified('post_startup_script'):
      runtime_software_config.postStartupScript = args.post_startup_script
    if args.IsSpecified('post_startup_script_behavior'):
      runtime_software_config.postStartupScriptBehavior = (
          GetPostStartupScriptBehavior())
    return runtime_software_config

  runtime = messages.Runtime(
      name=args.runtime,
      virtualMachine=GetRuntimeVirtualMachineFromArgs(),
      accessConfig=GetRuntimeAccessConfigFromArgs(),
      softwareConfig=GetRuntimeSoftwareConfigFromArgs(),
  )
  return runtime


def CreateRuntimeCreateRequest(args, messages):
  parent = util.GetParentForRuntime(args)
  runtime = CreateRuntime(args, messages)
  return messages.NotebooksProjectsLocationsRuntimesCreateRequest(
      parent=parent, runtime=runtime, runtimeId=args.runtime)


def CreateRuntimeListRequest(args, messages):
  parent = util.GetParentFromArgs(args)
  return messages.NotebooksProjectsLocationsRuntimesListRequest(parent=parent)


def GetRuntimeResource(args):
  return args.CONCEPTS.runtime.Parse()


def GetSwitchRuntimeRequest(args, messages):
  """Create and return switch runtime request."""
  machine_type = 'n1-standard-4'
  if args.IsSpecified('machine_type'):
    machine_type = args.machine_type
  runtime_accelerator_config = messages.RuntimeAcceleratorConfig()
  if args.IsSpecified('accelerator_core_count'):
    runtime_accelerator_config.coreCount = args.accelerator_core_count
  if args.IsSpecified('accelerator_type'):
    type_enum = arg_utils.ChoiceEnumMapper(
        arg_name='accelerator-type',
        message_enum=runtime_accelerator_config.TypeValueValuesEnum,
        include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
            arg_utils.EnumNameToChoice(args.accelerator_type))
    runtime_accelerator_config.type = type_enum
  return messages.SwitchRuntimeRequest(
      machineType=machine_type, acceleratorConfig=runtime_accelerator_config)


def CreateRuntimeDeleteRequest(args, messages):
  runtime = GetRuntimeResource(args).RelativeName()
  return messages.NotebooksProjectsLocationsRuntimesDeleteRequest(
      name=runtime)


def CreateRuntimeResetRequest(args, messages):
  runtime = GetRuntimeResource(args).RelativeName()
  reset_request = messages.ResetRuntimeRequest()
  return messages.NotebooksProjectsLocationsRuntimesResetRequest(
      name=runtime, resetRuntimeRequest=reset_request)


def CreateRuntimeStartRequest(args, messages):
  runtime = GetRuntimeResource(args).RelativeName()
  start_request = messages.StartRuntimeRequest()
  return messages.NotebooksProjectsLocationsRuntimesStartRequest(
      name=runtime, startRuntimeRequest=start_request)


def CreateRuntimeStopRequest(args, messages):
  runtime = GetRuntimeResource(args).RelativeName()
  stop_request = messages.StopRuntimeRequest()
  return messages.NotebooksProjectsLocationsRuntimesStopRequest(
      name=runtime, stopRuntimeRequest=stop_request)


def CreateRuntimeSwitchRequest(args, messages):
  runtime = GetRuntimeResource(args).RelativeName()
  switch_request = GetSwitchRuntimeRequest(args, messages)
  return messages.NotebooksProjectsLocationsRuntimesSwitchRequest(
      name=runtime, switchRuntimeRequest=switch_request)


def CreateRuntimeDescribeRequest(args, messages):
  runtime = GetRuntimeResource(args).RelativeName()
  return messages.NotebooksProjectsLocationsRuntimesGetRequest(name=runtime)


def CreateRuntimeDiagnoseRequest(args, messages):
  """"Create and return Diagnose request."""
  runtime = GetRuntimeResource(args).RelativeName()
  diagnostic_config = messages.DiagnosticConfig(
      gcsBucket=args.gcs_bucket,
  )
  if args.IsSpecified('relative_path'):
    diagnostic_config.relativePath = args.relative_path
  if args.IsSpecified('enable-repair'):
    diagnostic_config.repairFlagEnabled = True
  if args.IsSpecified('enable-packet-capture'):
    diagnostic_config.packetCaptureFlagEnabled = True
  if args.IsSpecified('enable-copy-home-files'):
    diagnostic_config.copyHomeFilesFlagEnabled = True

  timeout_minutes = None
  if args.IsSpecified('timeout_minutes'):
    timeout_minutes = int(args.timeout_minutes)

  return messages.NotebooksProjectsLocationsRuntimesDiagnoseRequest(
      name=runtime, diagnoseRuntimeRequest=messages.DiagnoseRuntimeRequest(
          diagnosticConfig=diagnostic_config, timeoutMinutes=timeout_minutes))


def CreateRuntimeMigrateRequest(args, messages):
  """"Create and return Migrate request."""
  runtime = GetRuntimeResource(args).RelativeName()

  def GetNetworkRelativeName():
    if args.IsSpecified('network'):
      return args.CONCEPTS.network.Parse().RelativeName()

  def GetSubnetRelativeName():
    if args.IsSpecified('subnet'):
      return args.CONCEPTS.subnet.Parse().RelativeName()

  def GetPostStartupScriptOption():
    type_enum = None
    if args.IsSpecified('post_startup_script_option'):
      request_message = messages.MigrateRuntimeRequest
      type_enum = arg_utils.ChoiceEnumMapper(
          arg_name='post-startup-script-option',
          message_enum=request_message.PostStartupScriptOptionValueValuesEnum,
          include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
              arg_utils.EnumNameToChoice(args.post_startup_script_option))
    return type_enum

  return messages.NotebooksProjectsLocationsRuntimesMigrateRequest(
      name=runtime,
      migrateRuntimeRequest=messages.MigrateRuntimeRequest(
          network=GetNetworkRelativeName(),
          subnet=GetSubnetRelativeName(),
          serviceAccount=args.service_account,
          postStartupScriptOption=GetPostStartupScriptOption(),
      ))


def GetRuntimeURI(resource):
  instance = resources.REGISTRY.ParseRelativeName(
      resource.name, collection='notebooks.projects.locations.runtimes')
  return instance.SelfLink()


class OperationType(enum.Enum):
  CREATE = (log.CreatedResource, 'created')
  DELETE = (log.DeletedResource, 'deleted')
  UPDATE = (log.UpdatedResource, 'updated')
  RESET = (log.ResetResource, 'reset')
  MIGRATE = (log.UpdatedResource, 'migrated')


def HandleLRO(operation,
              args,
              runtime_service,
              release_track,
              operation_type=OperationType.CREATE):
  """Handles Long Running Operations for both cases of async.

  Args:
    operation: The operation to poll.
    args: ArgParse instance containing user entered arguments.
    runtime_service: The service to get the resource after the long running
      operation completes.
    release_track: base.ReleaseTrack object.
    operation_type: Enum value of type OperationType indicating the kind of
      operation to wait for.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error

  Returns:
    The Runtime resource if synchronous, else the Operation Resource.
  """
  logging_method = operation_type.value[0]
  if args.async_:
    logging_method(
        util.GetOperationResource(operation.name, release_track),
        kind='notebooks runtime {0}'.format(args.runtime),
        is_async=True)
    return operation
  else:
    response = util.WaitForOperation(
        operation,
        'Waiting for operation on Runtime [{}] to be {} with [{}]'.format(
            args.runtime, operation_type.value[1], operation.name),
        service=runtime_service,
        release_track=release_track,
        is_delete=(operation_type.value[1] == 'deleted'))
    logging_method(
        util.GetOperationResource(operation.name, release_track),
        kind='notebooks runtime {0}'.format(args.runtime),
        is_async=False)
    return response
