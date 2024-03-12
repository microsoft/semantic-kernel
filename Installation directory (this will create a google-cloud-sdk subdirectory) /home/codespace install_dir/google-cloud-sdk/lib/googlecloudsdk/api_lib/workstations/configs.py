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
"""Cloud Workstations configs API utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.api_lib.workstations.util import GetClientInstance
from googlecloudsdk.api_lib.workstations.util import GetMessagesModule
from googlecloudsdk.api_lib.workstations.util import VERSION_MAP
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
import six

IMAGE_URL_MAP = {
    'codeoss': 'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest',
    'intellij': 'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/intellij-ultimate:latest',
    'pycharm': 'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/pycharm:latest',
    'rider': 'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/rider:latest',
    'webstorm': 'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/webstorm:latest',
    'phpstorm': 'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/phpstorm:latest',
    'rubymine': 'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/rubymine:latest',
    'goland': 'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/goland:latest',
    'clion': 'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/clion:latest',
    'base-image': 'us-central1-docker.pkg.dev/cloud-workstations-images/predefined/base:latest',
}


class Configs:
  """The Configs set of Cloud Workstations API functions."""

  def __init__(self, release_track=base.ReleaseTrack.BETA):
    self.api_version = VERSION_MAP.get(release_track)
    self.client = GetClientInstance(release_track)
    self.messages = GetMessagesModule(release_track)
    self._service = (
        self.client.projects_locations_workstationClusters_workstationConfigs
    )

  def Create(self, args):
    """Create a new workstation configuration.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Workstation configuration that was created.
    """
    config_name = args.CONCEPTS.config.Parse().RelativeName()
    parent = config_name.split('/workstationConfigs/')[0]
    config_id = config_name.split('/workstationConfigs/')[1]

    config = self.messages.WorkstationConfig()
    config.name = config_name
    config.idleTimeout = '{}s'.format(args.idle_timeout)
    config.runningTimeout = '{}s'.format(args.running_timeout)
    if args.labels:
      config.labels = self.messages.WorkstationConfig.LabelsValue(
          additionalProperties=[
              self.messages.WorkstationConfig.LabelsValue.AdditionalProperty(
                  key=key, value=value
              )
              for key, value in sorted(six.iteritems(args.labels))
          ]
      )
    config.disableTcpConnections = args.disable_tcp_connections

    # GCE Instance Config
    config.host = self.messages.Host()
    config.host.gceInstance = self.messages.GceInstance()
    config.host.gceInstance.machineType = args.machine_type
    config.host.gceInstance.serviceAccount = args.service_account
    if args.service_account_scopes:
      config.host.gceInstance.serviceAccountScopes = args.service_account_scopes
    if args.network_tags:
      config.host.gceInstance.tags = args.network_tags
    config.host.gceInstance.poolSize = args.pool_size
    config.host.gceInstance.disablePublicIpAddresses = (
        args.disable_public_ip_addresses
    )
    config.host.gceInstance.shieldedInstanceConfig = (
        self.messages.GceShieldedInstanceConfig(
            enableSecureBoot=args.shielded_secure_boot,
            enableVtpm=args.shielded_vtpm,
            enableIntegrityMonitoring=args.shielded_integrity_monitoring,
        )
    )
    config.host.gceInstance.confidentialInstanceConfig = (
        self.messages.GceConfidentialInstanceConfig(
            enableConfidentialCompute=args.enable_confidential_compute
        )
    )
    config.host.gceInstance.enableNestedVirtualization = (
        args.enable_nested_virtualization
    )
    config.host.gceInstance.bootDiskSizeGb = args.boot_disk_size
    if (
        self.api_version != VERSION_MAP.get(base.ReleaseTrack.GA)
        and args.IsKnownAndSpecified('disable_ssh_to_vm')
    ):
      config.host.gceInstance.disableSsh = args.disable_ssh_to_vm
    if (
        self.api_version != VERSION_MAP.get(base.ReleaseTrack.GA)
        and args.accelerator_type
        and args.accelerator_count
    ):
      accelerators = [
          self.messages.Accelerator(
              type=args.accelerator_type,
              count=args.accelerator_count,
          )
      ]
      config.host.gceInstance.accelerators = accelerators

    # Persistent directory
    pd = self.messages.PersistentDirectory()
    pd.mountPath = '/home'
    if args.pd_reclaim_policy == 'retain':
      reclaim_policy = (
          self.messages.GceRegionalPersistentDisk.ReclaimPolicyValueValuesEnum.RETAIN
      )
    else:
      reclaim_policy = (
          self.messages.GceRegionalPersistentDisk.ReclaimPolicyValueValuesEnum.DELETE
      )

    pd.gcePd = self.messages.GceRegionalPersistentDisk(
        sizeGb=args.pd_disk_size,
        fsType='ext4',
        diskType=args.pd_disk_type,
        reclaimPolicy=reclaim_policy,
    )
    config.persistentDirectories.append(pd)

    # Ephemeral directory
    if args.ephemeral_directory:
      for directory in args.ephemeral_directory:
        pd = self.messages.EphemeralDirectory()
        pd.mountPath = directory.get('mount-path')
        pd.gcePd = self.messages.GcePersistentDisk(
            diskType=directory.get('disk-type'),
            sourceSnapshot=directory.get('source-snapshot'),
            sourceImage=directory.get('source-image'),
            readOnly=directory.get('read-only'),
        )
        config.ephemeralDirectories.append(pd)

    # Container
    config.container = self.messages.Container()
    if args.container_custom_image:
      config.container.image = args.container_custom_image
    elif args.container_predefined_image:
      config.container.image = IMAGE_URL_MAP.get(
          args.container_predefined_image
      )
    if args.container_command:
      config.container.command = args.container_command
    if args.container_args:
      config.container.args = args.container_args
    if args.container_env:
      env_val = self.messages.Container.EnvValue()
      for key, value in args.container_env.items():
        env_val.additionalProperties.append(
            self.messages.Container.EnvValue.AdditionalProperty(
                key=key, value=value
            )
        )
      config.container.env = env_val
    config.container.workingDir = args.container_working_dir
    config.container.runAsUser = args.container_run_as_user

    # Encryption key
    encryption_key = self.messages.CustomerEncryptionKey()
    if args.kms_key:
      encryption_key.kmsKey = args.kms_key
    if args.kms_key_service_account:
      encryption_key.kmsKeyServiceAccount = args.kms_key_service_account
    config.encryptionKey = encryption_key

    if args.enable_audit_agent:
      config.enableAuditAgent = args.enable_audit_agent

    if args.replica_zones:
      config.replicaZones = args.replica_zones

    create_req = self.messages.WorkstationsProjectsLocationsWorkstationClustersWorkstationConfigsCreateRequest(
        parent=parent, workstationConfigId=config_id, workstationConfig=config
    )
    op_ref = self._service.Create(create_req)

    log.status.Print('Create request issued for: [{}]'.format(config_id))

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='workstations.projects.locations.operations',
        api_version=self.api_version,
    )
    poller = waiter.CloudOperationPoller(
        self._service, self.client.projects_locations_operations
    )

    result = waiter.WaitFor(
        poller,
        op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name),
    )
    log.status.Print('Created configuration [{}].'.format(config_id))

    return result

  def Update(self, args):
    """Updates an existing workstation configuration.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Workstation configuration that was updated.
    """
    config_name = args.CONCEPTS.config.Parse().RelativeName()
    config_id = config_name.split('/workstationConfigs/')[1]

    config = self.messages.WorkstationConfig()
    config.name = config_name
    update_mask = []

    if args.IsSpecified('idle_timeout'):
      config.idleTimeout = '{}s'.format(args.idle_timeout)
      update_mask.append('idle_timeout')

    if args.IsSpecified('running_timeout'):
      config.runningTimeout = '{}s'.format(args.running_timeout)
      update_mask.append('running_timeout')

    if args.IsSpecified('labels'):
      config.labels = self.messages.WorkstationConfig.LabelsValue(
          additionalProperties=[
              self.messages.WorkstationConfig.LabelsValue.AdditionalProperty(
                  key=key, value=value
              )
              for key, value in sorted(six.iteritems(args.labels))
          ]
      )
      update_mask.append('labels')

    # GCE Instance Config
    config.host = self.messages.Host()
    config.host.gceInstance = self.messages.GceInstance()
    if args.IsSpecified('machine_type'):
      config.host.gceInstance.machineType = args.machine_type
      update_mask.append('host.gce_instance.machine_type')

    if args.IsSpecified('service_account'):
      config.host.gceInstance.serviceAccount = args.service_account
      update_mask.append('host.gce_instance.service_account')

    if args.IsSpecified('service_account_scopes'):
      config.host.gceInstance.serviceAccountScopes = args.service_account_scopes
      update_mask.append('host.gce_instance.service_account_scopes')

    if args.IsSpecified('network_tags'):
      config.host.gceInstance.tags = args.network_tags
      update_mask.append('host.gce_instance.tags')

    if args.IsSpecified('pool_size'):
      config.host.gceInstance.poolSize = args.pool_size
      update_mask.append('host.gce_instance.pool_size')

    if args.IsSpecified('disable_public_ip_addresses'):
      config.host.gceInstance.disablePublicIpAddresses = (
          args.disable_public_ip_addresses
      )
      update_mask.append('host.gce_instance.disable_public_ip_addresses')

    if args.IsSpecified('boot_disk_size'):
      config.host.gceInstance.bootDiskSizeGb = args.boot_disk_size
      update_mask.append('host.gce_instance.boot_disk_size_gb')

    if self.api_version != VERSION_MAP.get(base.ReleaseTrack.GA) and (
        args.IsKnownAndSpecified('disable_ssh_to_vm') or
        args.IsKnownAndSpecified('enable_ssh_to_vm')
    ):
      if args.IsKnownAndSpecified('disable_ssh_to_vm'):
        config.host.gceInstance.disableSsh = args.disable_ssh_to_vm
      else:
        config.host.gceInstance.disableSsh = not args.enable_ssh_to_vm
      update_mask.append('host.gce_instance.disable_ssh')

    if args.IsSpecified('enable_confidential_compute'):
      config.host.gceInstance.confidentialInstanceConfig = (
          self.messages.GceConfidentialInstanceConfig(
              enableConfidentialCompute=args.enable_confidential_compute
          )
      )
      update_mask.append(
          'host.gce_instance.confidential_instance_config.enable_confidential_compute'
      )

    if args.IsSpecified('enable_audit_agent'):
      config.enableAuditAgent = args.enable_audit_agent
      update_mask.append('enable_audit_agent')

    if args.IsSpecified('disable_tcp_connections'):
      config.disableTcpConnections = args.disable_tcp_connections
      update_mask.append('disable_tcp_connections')

    if args.IsSpecified('enable_tcp_connections'):
      config.disableTcpConnections = not args.enable_tcp_connections
      update_mask.append('disable_tcp_connections')

    if args.IsSpecified('enable_nested_virtualization'):
      config.host.gceInstance.enableNestedVirtualization = (
          args.enable_nested_virtualization
      )
      update_mask.append('host.gce_instance.enable_nested_virtualization')

    # Shielded Instance Config
    gce_shielded_instance_config = self.messages.GceShieldedInstanceConfig()
    if args.IsSpecified('shielded_secure_boot'):
      gce_shielded_instance_config.enableSecureBoot = args.shielded_secure_boot
      update_mask.append(
          'host.gce_instance.shielded_instance_config.enable_secure_boot'
      )

    if args.IsSpecified('shielded_vtpm'):
      gce_shielded_instance_config.enableVtpm = args.shielded_vtpm
      update_mask.append(
          'host.gce_instance.shielded_instance_config.enable_vtpm'
      )

    if args.IsSpecified('shielded_integrity_monitoring'):
      gce_shielded_instance_config.enableIntegrityMonitoring = (
          args.shielded_integrity_monitoring
      )
      update_mask.append(
          'host.gce_instance.shielded_instance_config.enable_integrity_monitoring'
      )

    config.host.gceInstance.shieldedInstanceConfig = (
        gce_shielded_instance_config
    )

    if self.api_version != VERSION_MAP.get(base.ReleaseTrack.GA) and (
        args.IsSpecified('accelerator_type')
        or args.IsSpecified('accelerator_count')
    ):
      accelerators = [
          self.messages.Accelerator(
              type=args.accelerator_type,
              count=args.accelerator_count,
          )
      ]
      config.host.gceInstance.accelerators = accelerators
      update_mask.append(
          'host.gce_instance.accelerators'
      )

    # Container
    config.container = self.messages.Container()
    if args.IsSpecified('container_custom_image'):
      config.container.image = args.container_custom_image
      update_mask.append('container.image')
    elif args.IsSpecified('container_predefined_image'):
      config.container.image = IMAGE_URL_MAP.get(
          args.container_predefined_image
      )
      update_mask.append('container.image')

    if args.IsSpecified('container_command'):
      config.container.command = args.container_command
      update_mask.append('container.command')

    if args.IsSpecified('container_args'):
      config.container.args = args.container_args
      update_mask.append('container.args')

    if args.IsSpecified('container_env'):
      env_val = self.messages.Container.EnvValue()
      for key, value in args.container_env.items():
        env_val.additionalProperties.append(
            self.messages.Container.EnvValue.AdditionalProperty(
                key=key, value=value
            )
        )
      config.container.env = env_val
      update_mask.append('container.env')

    if args.IsSpecified('container_working_dir'):
      config.container.workingDir = args.container_working_dir
      update_mask.append('container.working_dir')

    if args.IsSpecified('container_run_as_user'):
      config.container.runAsUser = args.container_run_as_user
      update_mask.append('container.run_as_user')

    if not update_mask:
      log.error('No fields were specified.')
      return

    update_req = self.messages.WorkstationsProjectsLocationsWorkstationClustersWorkstationConfigsPatchRequest(
        name=config_name,
        workstationConfig=config,
        updateMask=','.join(update_mask),
    )
    op_ref = self._service.Patch(update_req)

    log.status.Print('Update request issued for: [{}]'.format(config_id))

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='workstations.projects.locations.operations',
        api_version=self.api_version,
    )
    poller = waiter.CloudOperationPoller(
        self._service, self.client.projects_locations_operations
    )

    result = waiter.WaitFor(
        poller,
        op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name),
    )
    log.status.Print('Updated configuration [{}].'.format(config_id))

    return result
