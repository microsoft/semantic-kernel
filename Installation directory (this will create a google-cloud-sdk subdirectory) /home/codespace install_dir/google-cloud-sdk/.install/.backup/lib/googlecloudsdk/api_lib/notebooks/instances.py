# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""notebooks instances api helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
from googlecloudsdk.api_lib.notebooks import environments as env_util
from googlecloudsdk.api_lib.notebooks import util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

_RESERVATION_AFFINITY_KEY = 'compute.googleapis.com/reservation-name'


def CreateInstance(args, client, messages):
  """Creates the Instance message for the create request.

  Args:
    args: Argparse object from Command.Run
    client(base_api.BaseApiClient): An instance of the specified API client.
    messages: Module containing messages definition for the specified API.

  Returns:
    Instance of the Instance message.
  """

  def GetContainerImageFromExistingEnvironment():
    environment_service = client.projects_locations_environments
    result = environment_service.Get(
        env_util.CreateEnvironmentDescribeRequest(args, messages))
    return result.containerImage

  def GetVmImageFromExistingEnvironment():
    environment_service = client.projects_locations_environments
    result = environment_service.Get(
        env_util.CreateEnvironmentDescribeRequest(args, messages))
    return result.vmImage

  def GetKmsRelativeName():
    if args.IsSpecified('kms_key'):
      return args.CONCEPTS.kms_key.Parse().RelativeName()

  def GetNetworkRelativeName():
    if args.IsSpecified('network'):
      return args.CONCEPTS.network.Parse().RelativeName()

  def GetSubnetRelativeName():
    if args.IsSpecified('subnet'):
      return args.CONCEPTS.subnet.Parse().RelativeName()

  def CreateAcceleratorConfigMessage():
    accelerator_config = messages.AcceleratorConfig
    type_enum = None
    if args.IsSpecified('accelerator_type'):
      type_enum = arg_utils.ChoiceEnumMapper(
          arg_name='accelerator-type',
          message_enum=accelerator_config.TypeValueValuesEnum,
          include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
              arg_utils.EnumNameToChoice(args.accelerator_type))
    return accelerator_config(
        type=type_enum, coreCount=args.accelerator_core_count)

  def GetBootDisk():
    type_enum = None
    if args.IsSpecified('boot_disk_type'):
      instance_message = messages.Instance
      type_enum = arg_utils.ChoiceEnumMapper(
          arg_name='boot-disk-type',
          message_enum=instance_message.BootDiskTypeValueValuesEnum,
          include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
              arg_utils.EnumNameToChoice(args.boot_disk_type))
    return type_enum

  def GetDataDisk():
    type_enum = None
    if args.IsSpecified('data_disk_type'):
      instance_message = messages.Instance
      type_enum = arg_utils.ChoiceEnumMapper(
          arg_name='data-disk-type',
          message_enum=instance_message.DataDiskTypeValueValuesEnum,
          include_filter=lambda x: 'UNSPECIFIED' not in x,
      ).GetEnumForChoice(arg_utils.EnumNameToChoice(args.data_disk_type))
    return type_enum

  def GetDiskEncryption():
    type_enum = None
    if args.IsSpecified('disk_encryption'):
      instance_message = messages.Instance
      type_enum = arg_utils.ChoiceEnumMapper(
          arg_name='disk-encryption',
          message_enum=instance_message.DiskEncryptionValueValuesEnum,
          include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
              arg_utils.EnumNameToChoice(args.disk_encryption))
    return type_enum

  def CreateContainerImageFromArgs():
    if args.IsSpecified('environment'):
      return GetContainerImageFromExistingEnvironment()
    if args.IsSpecified('container_repository'):
      container_image = messages.ContainerImage(
          repository=args.container_repository, tag=args.container_tag)
      return container_image
    return None

  def CreateVmImageFromArgs():
    """Create VmImage Message from an environment or from args."""
    if args.IsSpecified('environment'):
      return GetVmImageFromExistingEnvironment()
    if args.IsSpecified('container_repository'):
      return None
    vm_image = messages.VmImage(project=args.vm_image_project)
    if args.IsSpecified('vm_image_name'):
      vm_image.imageName = args.vm_image_name
    else:
      vm_image.imageFamily = args.vm_image_family
    return vm_image

  def GetInstanceOwnersFromArgs():
    if args.IsSpecified('instance_owners'):
      return [args.instance_owners]
    return []

  def GetLabelsFromArgs():
    if args.IsSpecified('labels'):
      labels_message = messages.Instance.LabelsValue
      return labels_message(additionalProperties=[
          labels_message.AdditionalProperty(key=key, value=value)
          for key, value in args.labels.items()
      ])
    return None

  def GetMetadataFromArgs():
    if args.IsSpecified('metadata'):
      metadata_message = messages.Instance.MetadataValue
      return metadata_message(additionalProperties=[
          metadata_message.AdditionalProperty(key=key, value=value)
          for key, value in args.metadata.items()
      ])
    return None

  def GetShieldedInstanceConfigFromArgs():
    if not (args.IsSpecified('shielded_vm_secure_boot') or
            args.IsSpecified('shielded_vm_vtpm') or
            args.IsSpecified('shielded_vm_integrity_monitoring')):
      return None
    shielded_instance_config_message = messages.ShieldedInstanceConfig
    return shielded_instance_config_message(
        enableIntegrityMonitoring=args.shielded_vm_integrity_monitoring,
        enableSecureBoot=args.shielded_vm_secure_boot,
        enableVtpm=args.shielded_vm_vtpm,
    )

  def GetTagsFromArgs():
    if args.IsSpecified('tags'):
      return args.tags
    return []

  # TODO(b/194714138): Consider adding validation for specific reservation.
  def GetReservationAffinityConfigFromArgs():
    if not (args.IsSpecified('reservation_affinity') or
            args.IsSpecified('reservation')):
      return None

    def GetReservationAffinityEnum():
      type_enum = None
      if args.IsSpecified('reservation_affinity'):
        reservation_affinity_message = messages.ReservationAffinity
        type_enum = arg_utils.ChoiceEnumMapper(
            arg_name='reservation-affinity',
            message_enum=(reservation_affinity_message
                          .ConsumeReservationTypeValueValuesEnum),
            include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
                arg_utils.EnumNameToChoice(args.reservation_affinity))
      return type_enum

    reservation_affinity_enum = GetReservationAffinityEnum()
    reservation_key = None
    reservation_values = []

    if (reservation_affinity_enum == messages.ReservationAffinity
        .ConsumeReservationTypeValueValuesEnum.SPECIFIC_RESERVATION):
      # Currently, the key is fixed and the value is the name of the
      # reservation.
      # The value being a repeated field is reserved for future use when user
      # can specify more than one reservation names from which the VM can take
      # capacity from.
      reservation_key = _RESERVATION_AFFINITY_KEY
      reservation_values = [args.reservation]

    reservation_config_message = messages.ReservationAffinity
    return reservation_config_message(
        consumeReservationType=reservation_affinity_enum,
        key=reservation_key,
        values=reservation_values,
    )

  instance = messages.Instance(
      name=args.instance,
      postStartupScript=args.post_startup_script,
      customGpuDriverPath=args.custom_gpu_driver_path,
      instanceOwners=GetInstanceOwnersFromArgs(),
      kmsKey=GetKmsRelativeName(),
      machineType=args.machine_type,
      network=GetNetworkRelativeName(),
      noProxyAccess=args.no_proxy_access,
      noPublicIp=args.no_public_ip,
      serviceAccount=args.service_account,
      subnet=GetSubnetRelativeName(),
      vmImage=CreateVmImageFromArgs(),
      acceleratorConfig=CreateAcceleratorConfigMessage(),
      bootDiskType=GetBootDisk(),
      bootDiskSizeGb=args.boot_disk_size,
      dataDiskType=GetDataDisk(),
      dataDiskSizeGb=args.data_disk_size,
      noRemoveDataDisk=args.no_remove_data_disk,
      containerImage=CreateContainerImageFromArgs(),
      diskEncryption=GetDiskEncryption(),
      labels=GetLabelsFromArgs(),
      metadata=GetMetadataFromArgs(),
      installGpuDriver=args.install_gpu_driver,
      shieldedInstanceConfig=GetShieldedInstanceConfigFromArgs(),
      reservationAffinity=GetReservationAffinityConfigFromArgs(),
      tags=GetTagsFromArgs(),
  )
  return instance


def CreateInstanceCreateRequest(args, client, messages):
  parent = util.GetParentForInstance(args)
  instance = CreateInstance(args, client, messages)
  return messages.NotebooksProjectsLocationsInstancesCreateRequest(
      parent=parent, instance=instance, instanceId=args.instance)


def CreateInstanceListRequest(args, messages):
  parent = util.GetParentFromArgs(args)
  return messages.NotebooksProjectsLocationsInstancesListRequest(parent=parent)


def CreateInstanceDeleteRequest(args, messages):
  instance = GetInstanceResource(args).RelativeName()
  return messages.NotebooksProjectsLocationsInstancesDeleteRequest(
      name=instance)


def CreateInstanceDescribeRequest(args, messages):
  instance = GetInstanceResource(args).RelativeName()
  return messages.NotebooksProjectsLocationsInstancesGetRequest(name=instance)


def CreateInstanceRegisterRequest(args, messages):
  instance = GetInstanceResource(args)
  parent = util.GetLocationResource(instance.locationsId,
                                    instance.projectsId).RelativeName()
  register_request = messages.RegisterInstanceRequest(
      instanceId=instance.Name())
  return messages.NotebooksProjectsLocationsInstancesRegisterRequest(
      parent=parent, registerInstanceRequest=register_request)


def CreateInstanceResetRequest(args, messages):
  instance = GetInstanceResource(args).RelativeName()
  reset_request = messages.ResetInstanceRequest()
  return messages.NotebooksProjectsLocationsInstancesResetRequest(
      name=instance, resetInstanceRequest=reset_request)


def CreateInstanceStartRequest(args, messages):
  instance = GetInstanceResource(args).RelativeName()
  start_request = messages.StartInstanceRequest()
  return messages.NotebooksProjectsLocationsInstancesStartRequest(
      name=instance, startInstanceRequest=start_request)


def CreateInstanceStopRequest(args, messages):
  instance = GetInstanceResource(args).RelativeName()
  stop_request = messages.StopInstanceRequest()
  return messages.NotebooksProjectsLocationsInstancesStopRequest(
      name=instance, stopInstanceRequest=stop_request)


def CreateSetAcceleratorRequest(args, messages):
  """Create and return Accelerator update request."""
  instance = GetInstanceResource(args).RelativeName()
  set_acc_request = messages.SetInstanceAcceleratorRequest()
  accelerator_config = messages.SetInstanceAcceleratorRequest
  if args.IsSpecified('accelerator_core_count'):
    set_acc_request.coreCount = args.accelerator_core_count
  if args.IsSpecified('accelerator_type'):
    type_enum = arg_utils.ChoiceEnumMapper(
        arg_name='accelerator-type',
        message_enum=accelerator_config.TypeValueValuesEnum,
        include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
            arg_utils.EnumNameToChoice(args.accelerator_type))
    set_acc_request.type = type_enum
  return messages.NotebooksProjectsLocationsInstancesSetAcceleratorRequest(
      name=instance, setInstanceAcceleratorRequest=set_acc_request)


def CreateSetLabelsRequest(args, messages):
  instance = GetInstanceResource(args).RelativeName()
  set_label_request = messages.SetInstanceLabelsRequest()
  labels_message = messages.SetInstanceLabelsRequest.LabelsValue
  set_label_request.labels = labels_message(additionalProperties=[
      labels_message.AdditionalProperty(key=key, value=value)
      for key, value in args.labels.items()
  ])
  return messages.NotebooksProjectsLocationsInstancesSetLabelsRequest(
      name=instance, setInstanceLabelsRequest=set_label_request)


def CreateSetMachineTypeRequest(args, messages):
  instance = GetInstanceResource(args).RelativeName()
  set_machine_request = messages.SetInstanceMachineTypeRequest(
      machineType=args.machine_type)
  return messages.NotebooksProjectsLocationsInstancesSetMachineTypeRequest(
      name=instance, setInstanceMachineTypeRequest=set_machine_request)


def CreateInstanceGetHealthRequest(args, messages):
  instance = GetInstanceResource(args).RelativeName()
  return messages.NotebooksProjectsLocationsInstancesGetInstanceHealthRequest(
      name=instance)


def CreateInstanceIsUpgradeableRequest(args, messages):
  instance = GetInstanceResource(args).RelativeName()
  return messages.NotebooksProjectsLocationsInstancesIsUpgradeableRequest(
      notebookInstance=instance)


def CreateInstanceUpgradeRequest(args, messages):
  instance = GetInstanceResource(args).RelativeName()
  upgrade_request = messages.UpgradeInstanceRequest()
  return messages.NotebooksProjectsLocationsInstancesUpgradeRequest(
      name=instance, upgradeInstanceRequest=upgrade_request)


def CreateInstanceRollbackRequest(args, messages):
  instance = GetInstanceResource(args).RelativeName()
  rollback_request = messages.RollbackInstanceRequest(
      targetSnapshot=args.target_snapshot)
  return messages.NotebooksProjectsLocationsInstancesRollbackRequest(
      name=instance, rollbackInstanceRequest=rollback_request)


def CreateInstanceDiagnoseRequest(args, messages):
  """"Create and return Diagnose request."""
  instance = GetInstanceResource(args).RelativeName()
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

  return messages.NotebooksProjectsLocationsInstancesDiagnoseRequest(
      name=instance, diagnoseInstanceRequest=messages.DiagnoseInstanceRequest(
          diagnosticConfig=diagnostic_config, timeoutMinutes=timeout_minutes))


def CreateInstanceMigrateRequest(args, messages):
  """"Create and return Migrate request."""
  instance = GetInstanceResource(args).RelativeName()

  def GetPostStartupScriptOption():
    type_enum = None
    if args.IsSpecified('post_startup_script_option'):
      request_message = messages.MigrateInstanceRequest
      type_enum = arg_utils.ChoiceEnumMapper(
          arg_name='post-startup-script-option',
          message_enum=request_message.PostStartupScriptOptionValueValuesEnum,
          include_filter=lambda x: 'UNSPECIFIED' not in x).GetEnumForChoice(
              arg_utils.EnumNameToChoice(args.post_startup_script_option))
    return type_enum

  return messages.NotebooksProjectsLocationsInstancesMigrateRequest(
      name=instance,
      migrateInstanceRequest=messages.MigrateInstanceRequest(
          postStartupScriptOption=GetPostStartupScriptOption(),
      ))


def GetInstanceResource(args):
  return args.CONCEPTS.instance.Parse()


def GetInstanceURI(resource):
  instance = resources.REGISTRY.ParseRelativeName(
      resource.name, collection='notebooks.projects.locations.instances')
  return instance.SelfLink()


class OperationType(enum.Enum):
  CREATE = (log.CreatedResource, 'created')
  UPDATE = (log.UpdatedResource, 'updated')
  UPGRADE = (log.UpdatedResource, 'upgraded')
  ROLLBACK = (log.UpdatedResource, 'rolled back')
  DELETE = (log.DeletedResource, 'deleted')
  RESET = (log.ResetResource, 'reset')
  MIGRATE = (log.UpdatedResource, 'migrated')


def HandleLRO(operation,
              args,
              instance_service,
              release_track,
              operation_type=OperationType.UPDATE):
  """Handles Long Running Operations for both cases of async.

  Args:
    operation: The operation to poll.
    args: ArgParse instance containing user entered arguments.
    instance_service: The service to get the resource after the long running
      operation completes.
    release_track: base.ReleaseTrack object.
    operation_type: Enum value of type OperationType indicating the kind of
      operation to wait for.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error

  Returns:
    The Instance resource if synchronous, else the Operation Resource.
  """
  logging_method = operation_type.value[0]
  if args.async_:
    logging_method(
        util.GetOperationResource(operation.name, release_track),
        kind='notebooks instance {0}'.format(args.instance),
        is_async=True)
    return operation
  else:
    response = util.WaitForOperation(
        operation,
        'Waiting for operation on Instance [{}] to be {} with [{}]'.format(
            args.instance, operation_type.value[1], operation.name),
        service=instance_service,
        release_track=release_track,
        is_delete=(operation_type.value[1] == 'deleted'))
    logging_method(
        util.GetOperationResource(operation.name, release_track),
        kind='notebooks instance {0}'.format(args.instance),
        is_async=False)
    return response
