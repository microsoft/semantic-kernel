# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for creating instance templates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import json

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import instance_template_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import metadata_utils
from googlecloudsdk.api_lib.compute import partner_metadata_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import resource_manager_tags_utils
from googlecloudsdk.command_lib.compute.instance_templates import flags as instance_templates_flags
from googlecloudsdk.command_lib.compute.instance_templates import mesh_util
from googlecloudsdk.command_lib.compute.instance_templates import service_proxy_aux_data
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags as maintenance_flags
from googlecloudsdk.command_lib.compute.sole_tenancy import flags as sole_tenancy_flags
from googlecloudsdk.command_lib.compute.sole_tenancy import util as sole_tenancy_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
import six


def _CommonArgs(
    parser,
    release_track,
    support_source_instance,
    support_local_ssd_size=False,
    support_kms=False,
    support_multi_writer=False,
    support_mesh=False,
    support_host_error_timeout_seconds=False,
    support_numa_node_count=False,
    support_visible_core_count=False,
    support_max_run_duration=False,
    support_region_instance_template=False,
    support_subnet_region=False,
    support_network_attachments=False,
    support_replica_zones=True,
    support_local_ssd_recovery_timeout=False,
    support_network_queue_count=False,
    support_storage_pool=False,
    support_maintenance_interval=False,
    support_specific_then_x_affinity=False,
    support_graceful_shutdown=False,
    support_ipv6_only=False,
    support_vlan_nic=False,
):
  """Adding arguments applicable for creating instance templates."""
  parser.display_info.AddFormat(instance_templates_flags.DEFAULT_LIST_FORMAT)
  metadata_utils.AddMetadataArgs(parser)
  instances_flags.AddDiskArgs(parser, enable_kms=support_kms)
  instances_flags.AddCreateDiskArgs(
      parser,
      enable_kms=support_kms,
      support_boot=True,
      support_multi_writer=support_multi_writer,
      support_replica_zones=support_replica_zones,
      support_storage_pool=support_storage_pool,
  )
  if support_local_ssd_size:
    instances_flags.AddLocalSsdArgsWithSize(parser)
  else:
    instances_flags.AddLocalSsdArgs(parser)
  instances_flags.AddCanIpForwardArgs(parser)
  instances_flags.AddAddressArgs(
      parser,
      instances=False,
      support_network_attachments=support_network_attachments,
      support_network_queue_count=support_network_queue_count,
      support_vlan_nic=support_vlan_nic,
      support_ipv6_only=support_ipv6_only,
  )
  instances_flags.AddAcceleratorArgs(parser)
  instances_flags.AddMachineTypeArgs(parser)
  deprecate_maintenance_policy = release_track in [base.ReleaseTrack.ALPHA]
  instances_flags.AddMaintenancePolicyArgs(parser, deprecate_maintenance_policy)
  instances_flags.AddNoRestartOnFailureArgs(parser)
  instances_flags.AddPreemptibleVmArgs(parser)
  instances_flags.AddServiceAccountAndScopeArgs(parser, False)
  instances_flags.AddTagsArgs(parser)
  instances_flags.AddCustomMachineTypeArgs(parser)
  instances_flags.AddImageArgs(parser)
  instances_flags.AddNetworkArgs(parser)
  instances_flags.AddShieldedInstanceConfigArgs(parser)
  labels_util.AddCreateLabelsFlags(parser)
  instances_flags.AddNetworkTierArgs(parser, instance=True)
  instances_flags.AddPrivateNetworkIpArgs(parser)
  instances_flags.AddMinNodeCpuArg(parser)
  instances_flags.AddNestedVirtualizationArgs(parser)
  instances_flags.AddThreadsPerCoreArgs(parser)
  instances_flags.AddEnableUefiNetworkingArgs(parser)
  instances_flags.AddResourceManagerTagsArgs(parser)
  if support_numa_node_count:
    instances_flags.AddNumaNodeCountArgs(parser)
  instances_flags.AddStackTypeArgs(parser, support_ipv6_only)
  instances_flags.AddIpv6NetworkTierArgs(parser)
  maintenance_flags.AddResourcePoliciesArgs(
      parser, 'added to', 'instance-template'
  )
  instances_flags.AddProvisioningModelVmArgs(parser)
  instances_flags.AddInstanceTerminationActionVmArgs(parser)
  instances_flags.AddIPv6AddressArgs(parser)
  instances_flags.AddIPv6PrefixLengthArgs(parser)
  instances_flags.AddInternalIPv6AddressArgs(parser)
  instances_flags.AddInternalIPv6PrefixLengthArgs(parser)

  if support_max_run_duration:
    instances_flags.AddMaxRunDurationVmArgs(parser)

  instance_templates_flags.AddServiceProxyConfigArgs(
      parser, release_track=release_track
  )
  if support_mesh:
    instance_templates_flags.AddMeshArgs(parser)

  sole_tenancy_flags.AddNodeAffinityFlagToParser(parser)

  instances_flags.AddLocationHintArg(parser)

  if support_visible_core_count:
    instances_flags.AddVisibleCoreCountArgs(parser)

  instances_flags.AddNetworkPerformanceConfigsArgs(parser)

  if support_region_instance_template:
    if support_subnet_region:
      parser.add_argument(
          '--subnet-region', help='Specifies the region of the subnetwork.'
      )
    parser.add_argument(
        '--instance-template-region',
        help='Specifies the region of the regional instance template.',
    )

  flags.AddRegionFlag(
      parser, resource_type='subnetwork', operation_type='attach'
  )

  parser.add_argument(
      '--description',
      help='Specifies a textual description for the instance template.',
  )

  Create.InstanceTemplateArg = (
      instance_templates_flags.MakeInstanceTemplateArg()
  )
  Create.InstanceTemplateArg.AddArgument(parser, operation_type='create')
  if support_source_instance:
    instance_templates_flags.MakeSourceInstanceArg().AddArgument(parser)
    instance_templates_flags.AddConfigureDiskArgs(parser)

  instances_flags.AddReservationAffinityGroup(
      parser,
      group_text="""\
Specifies the reservation for instances created from this template.
""",
      affinity_text="""\
The type of reservation for instances created from this template.
""",
      support_specific_then_x_affinity=support_specific_then_x_affinity,
  )

  parser.display_info.AddCacheUpdater(completers.InstanceTemplatesCompleter)
  if support_host_error_timeout_seconds:
    instances_flags.AddHostErrorTimeoutSecondsArgs(parser)

  if support_local_ssd_recovery_timeout:
    instances_flags.AddLocalSsdRecoveryTimeoutArgs(parser)

  if support_maintenance_interval:
    instances_flags.AddMaintenanceIntervalArgs(parser)

  if support_graceful_shutdown:
    instances_flags.AddGracefulShutdownArgs(parser, is_create=True)


def _ValidateInstancesFlags(
    args, support_kms=False, support_max_run_duration=False
):
  """Validate flags for instance template that affects instance creation.

  Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
      support_kms: If KMS is supported.
      support_max_run_duration: max-run-durrations is supported in instance
        scheduling.
  """
  instances_flags.ValidateDiskCommonFlags(args)
  instances_flags.ValidateDiskBootFlags(args, enable_kms=support_kms)
  instances_flags.ValidateCreateDiskFlags(args)
  instances_flags.ValidateLocalSsdFlags(args)
  instances_flags.ValidateNicFlags(args)
  instances_flags.ValidateServiceAccountAndScopeArgs(args)
  instances_flags.ValidateAcceleratorArgs(args)
  instances_flags.ValidateReservationAffinityGroup(args)
  instances_flags.ValidateNetworkPerformanceConfigsArgs(args)
  instances_flags.ValidateInstanceScheduling(
      args, support_max_run_duration=support_max_run_duration
  )


def _AddSourceInstanceToTemplate(
    compute_api, args, instance_template, support_source_instance
):
  """Set the source instance for the template."""

  if not support_source_instance or not args.source_instance:
    return
  source_instance_arg = instance_templates_flags.MakeSourceInstanceArg()
  source_instance_ref = source_instance_arg.ResolveAsResource(
      args, compute_api.resources
  )
  instance_template.sourceInstance = source_instance_ref.SelfLink()
  if args.configure_disk:
    messages = compute_api.client.messages
    instance_template.sourceInstanceParams = messages.SourceInstanceParams()
    for disk in args.configure_disk:
      disk_config = messages.DiskInstantiationConfig()
      # device-name is required argument with --configure-disk
      disk_config.deviceName = disk.get('device-name')
      disk_config.autoDelete = disk.get('auto-delete')
      instantiate_from = disk.get('instantiate-from')
      if instantiate_from:
        disk_config.instantiateFrom = (
            messages.DiskInstantiationConfig.InstantiateFromValueValuesEnum(
                disk.get('instantiate-from').upper().replace('-', '_')
            )
        )
      disk_config.customImage = disk.get('custom-image')
      instance_template.sourceInstanceParams.diskConfigs.append(disk_config)

  instance_template.properties = None


def BuildShieldedInstanceConfigMessage(messages, args):
  """Common routine for creating instance template.

  Build a shielded VM config message.

  Args:
      messages: The client messages.
      args: the arguments passed to the test.

  Returns:
      A shielded VM config message.
  """
  # Set the default values for ShieldedInstanceConfig parameters

  shielded_instance_config_message = None
  enable_secure_boot = None
  enable_vtpm = None
  enable_integrity_monitoring = None
  if not (
      hasattr(args, 'shielded_vm_secure_boot')
      or hasattr(args, 'shielded_vm_vtpm')
      or hasattr(args, 'shielded_vm_integrity_monitoring')
  ):
    return shielded_instance_config_message

  if (
      not args.IsSpecified('shielded_vm_secure_boot')
      and not args.IsSpecified('shielded_vm_vtpm')
      and not args.IsSpecified('shielded_vm_integrity_monitoring')
  ):
    return shielded_instance_config_message

  if args.shielded_vm_secure_boot is not None:
    enable_secure_boot = args.shielded_vm_secure_boot
  if args.shielded_vm_vtpm is not None:
    enable_vtpm = args.shielded_vm_vtpm
  if args.shielded_vm_integrity_monitoring is not None:
    enable_integrity_monitoring = args.shielded_vm_integrity_monitoring
  # compute message for shielded VM configuration.
  shielded_instance_config_message = (
      instance_utils.CreateShieldedInstanceConfigMessage(
          messages, enable_secure_boot, enable_vtpm, enable_integrity_monitoring
      )
  )

  return shielded_instance_config_message


def BuildConfidentialInstanceConfigMessage(
    messages, args, support_confidential_compute_type=False,
    support_confidential_compute_type_tdx=False):
  """Builds a confidential instance configuration message."""
  return instance_utils.CreateConfidentialInstanceMessage(
      messages, args, support_confidential_compute_type,
      support_confidential_compute_type_tdx)


def PackageLabels(labels_cls, labels):
  # Sorted for test stability
  return labels_cls(
      additionalProperties=[
          labels_cls.AdditionalProperty(key=key, value=value)
          for key, value in sorted(six.iteritems(labels))
      ]
  )


# Function copied from labels_util.
# Temporary fix for adoption tracking of Managed Envoy.
# TODO(b/146051298) Remove this fix when structured metadata is available.
def ParseCreateArgsWithServiceProxy(args, labels_cls, labels_dest='labels'):
  """Initializes labels based on args and the given class."""
  labels = getattr(args, labels_dest)
  if getattr(args, 'service_proxy', False):
    if labels is None:
      labels = collections.OrderedDict()
    labels['gce-service-proxy'] = 'on'

  if labels is None:
    return None
  return PackageLabels(labels_cls, labels)


def AddScopesForServiceProxy(args):
  if getattr(args, 'service_proxy', False):
    if args.scopes is None:
      args.scopes = constants.DEFAULT_SCOPES[:]

    if (
        'cloud-platform' not in args.scopes
        and 'https://www.googleapis.com/auth/cloud-platform' not in args.scopes
    ):
      args.scopes.append('cloud-platform')


def AddServiceProxyArgsToMetadata(args):
  """Inserts the Service Proxy arguments provided by the user to the instance metadata.

  Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
  """
  if getattr(args, 'service_proxy', False):
    service_proxy_config = collections.OrderedDict()
    proxy_spec = collections.OrderedDict()

    service_proxy_config['_disclaimer'] = service_proxy_aux_data.DISCLAIMER
    service_proxy_config['api-version'] = '0.2'

    # add --service-proxy flag data to metadata.
    if 'serving-ports' in args.service_proxy:
      # convert list of strings to list of integers.
      serving_ports = list(
          map(int, args.service_proxy['serving-ports'].split(';'))
      )
      # find unique ports by converting list of integers to set of integers.
      unique_serving_ports = set(serving_ports)
      # convert it back to list of integers.
      # this is done to make it JSON serializable.
      serving_ports = list(unique_serving_ports)
      service_proxy_config['service'] = {
          'serving-ports': serving_ports,
      }

    if 'proxy-port' in args.service_proxy:
      proxy_spec['proxy-port'] = args.service_proxy['proxy-port']

    if 'tracing' in args.service_proxy:
      proxy_spec['tracing'] = args.service_proxy['tracing']

    if 'access-log' in args.service_proxy:
      proxy_spec['access-log'] = args.service_proxy['access-log']

    proxy_spec['network'] = args.service_proxy.get('network', '')

    if 'scope' in args.service_proxy:
      proxy_spec['scope'] = args.service_proxy['scope']

    if 'mesh' in args.service_proxy:
      proxy_spec['mesh'] = args.service_proxy['mesh']

    if 'project-number' in args.service_proxy:
      proxy_spec['project-number'] = args.service_proxy['project-number']

    if 'source' in args.service_proxy:
      proxy_spec['primary-source'] = args.service_proxy['source']
      proxy_spec['secondary-source'] = args.service_proxy['source']

    traffic_interception = collections.OrderedDict()
    if 'intercept-all-outbound-traffic' in args.service_proxy:
      traffic_interception['intercept-all-outbound'] = True
      if 'exclude-outbound-ip-ranges' in args.service_proxy:
        traffic_interception['exclude-outbound-ip-ranges'] = args.service_proxy[
            'exclude-outbound-ip-ranges'
        ].split(';')
      if 'exclude-outbound-port-ranges' in args.service_proxy:
        traffic_interception['exclude-outbound-port-ranges'] = (
            args.service_proxy['exclude-outbound-port-ranges'].split(';')
        )
    if 'intercept-dns' in args.service_proxy:
      traffic_interception['intercept-dns'] = True
    if traffic_interception:
      service_proxy_config['traffic-interception'] = traffic_interception

    if getattr(args, 'service_proxy_xds_version', False):
      proxy_spec['xds-version'] = args.service_proxy_xds_version

    # add --service-proxy-labels flag data to metadata.
    if getattr(args, 'service_proxy_labels', False):
      service_proxy_config['labels'] = args.service_proxy_labels

    args.metadata['enable-osconfig'] = 'true'
    gce_software_declaration = collections.OrderedDict()
    service_proxy_agent_recipe = collections.OrderedDict()

    service_proxy_agent_recipe['name'] = 'install-gce-service-proxy-agent'
    service_proxy_agent_recipe['desired_state'] = 'INSTALLED'

    if getattr(args, 'service_proxy_agent_location', False):
      service_proxy_agent_recipe['installSteps'] = [
          {
              'scriptRun': {
                  'script': (
                      service_proxy_aux_data.startup_script_with_location_template
                      % args.service_proxy_agent_location
                  )
              }
          }
      ]
    else:
      service_proxy_agent_recipe['installSteps'] = [
          {'scriptRun': {'script': service_proxy_aux_data.startup_script}}
      ]

    gce_software_declaration['softwareRecipes'] = [service_proxy_agent_recipe]

    args.metadata['gce-software-declaration'] = json.dumps(
        gce_software_declaration
    )
    args.metadata['enable-guest-attributes'] = 'TRUE'

    if proxy_spec:
      service_proxy_config['proxy-spec'] = proxy_spec

    args.metadata['gce-service-proxy'] = json.dumps(service_proxy_config)


def ConfigureMeshTemplate(args, instance_template_ref, network_interfaces):
  """Adds Anthos Service Mesh configuration into the instance template.

  Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
      instance_template_ref: Reference to the current instance template to be
        created.
      network_interfaces: network interfaces configured for the instance
        template.
  """

  if getattr(args, 'mesh', False):
    # Add the required scopes.
    if args.scopes is None:
      args.scopes = constants.DEFAULT_SCOPES[:]
    if (
        'cloud-platform' not in args.scopes
        and 'https://www.googleapis.com/auth/cloud-platform' not in args.scopes
    ):
      args.scopes.append('cloud-platform')

    workload_namespace, workload_name = mesh_util.ParseWorkload(
        args.mesh['workload']
    )
    with mesh_util.KubernetesClient(
        gke_cluster=args.mesh['gke-cluster']
    ) as kube_client:
      log.status.Print(
          'Verifying GKE cluster and Anthos Service Mesh installation...'
      )
      namespaces = ['default', 'istio-system', workload_namespace]
      if kube_client.NamespacesExist(
          *namespaces
      ) and kube_client.HasNamespaceReaderPermissions(*namespaces):
        membership_manifest = kube_client.GetMembershipCR()
        # Verify Identity Provider CR existence only.
        _ = kube_client.GetIdentityProviderCR()

        namespace_manifest = kube_client.GetNamespace(workload_namespace)
        workload_manifest = kube_client.GetWorkloadGroupCR(
            workload_namespace, workload_name
        )
        mesh_util.VerifyWorkloadSetup(workload_manifest)

        asm_revision = mesh_util.RetrieveWorkloadRevision(namespace_manifest)
        mesh_config = kube_client.RetrieveMeshConfig(asm_revision)

        log.status.Print(
            'Configuring the instance template for Anthos Service Mesh...'
        )
        project_id = instance_template_ref.project
        mesh_util.ConfigureInstanceTemplate(
            args,
            kube_client,
            project_id,
            network_interfaces[0].network,
            workload_namespace,
            workload_name,
            workload_manifest,
            membership_manifest,
            asm_revision,
            mesh_config,
        )


def _RunCreate(
    compute_api,
    args,
    support_source_instance,
    support_kms=False,
    support_post_key_revocation_action_type=False,
    support_multi_writer=False,
    support_mesh=False,
    support_host_error_timeout_seconds=False,
    support_numa_node_count=False,
    support_visible_core_count=False,
    support_max_run_duration=False,
    support_region_instance_template=False,
    support_subnet_region=False,
    support_confidential_compute_type=False,
    support_confidential_compute_type_tdx=False,
    support_ipv6_reservation=False,
    support_internal_ipv6_reservation=False,
    support_replica_zones=True,
    support_local_ssd_recovery_timeout=False,
    support_performance_monitoring_unit=False,
    support_storage_pool=False,
    support_partner_metadata=False,
    support_maintenance_interval=False,
    support_specific_then_x_affinity=False,
    support_graceful_shutdown=False,
):
  """Common routine for creating instance template.

  This is shared between various release tracks.

  Args:
      compute_api: The compute api.
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
      support_source_instance: indicates whether source instance is supported.
      support_kms: Indicate whether KMS is integrated or not.
      support_post_key_revocation_action_type: Indicate whether
        post_key_revocation_action_type is supported.
      support_multi_writer: Indicates whether a disk can have multiple writers.
      support_mesh: Indicates whether adding VM to a Anthos Service Mesh is
        supported.
      support_host_error_timeout_seconds: Indicate the timeout in seconds for
        host error detection.
      support_numa_node_count: Indicates whether setting NUMA node count is
        supported.
      support_visible_core_count: Indicates whether setting a custom visible
      support_max_run_duration: Indicate whether max-run-duration or
        termination-time is supported.
      support_region_instance_template: Indicate whether create region instance
        template is supported.
      support_subnet_region: Indicate whether subnet_region flag enhancement
        should be supported.
      support_confidential_compute_type: Indicate what confidential compute type
        is used.
      support_confidential_compute_type_tdx: Indicate if confidential compute
        type 'TDX' is supported.
      support_ipv6_reservation: Indicate the external IPv6 address is supported.
      support_internal_ipv6_reservation: Indicate the internal IPv6 address is
        supported.
      support_replica_zones: Indicate the replicaZones param is supported for
        create-on-create disk.
      support_local_ssd_recovery_timeout: Indicate whether the local SSD
        recovery timeout is set.
      support_performance_monitoring_unit: Indicate whether the PMU is
        supported.
      support_storage_pool: Indicate whether storage pool is supported.
      support_partner_metadata: Indicate whether partner metadata is supported.
      support_maintenance_interval: Indicate whether maintenance interval was
        set.
      support_specific_then_x_affinity: Indicate whether specific_then_x was
        set.
      support_graceful_shutdown: Indicate whether graceful shutdown is
        supported.

  Returns:
      A resource object dispatched by display.Displayer().
  """
  _ValidateInstancesFlags(
      args,
      support_kms=support_kms,
      support_max_run_duration=support_max_run_duration,
  )
  instances_flags.ValidateNetworkTierArgs(args)

  instance_templates_flags.ValidateServiceProxyFlags(args)
  if support_source_instance:
    instance_templates_flags.ValidateSourceInstanceFlags(args)
  if support_mesh:
    instance_templates_flags.ValidateMeshFlag(args)

  if support_region_instance_template:
    subnet_region_flag = 'region'
    if support_subnet_region:
      subnet_region_flag = 'subnet_region'
    instance_template_region = getattr(args, 'instance_template_region', None)
    subnet_region = getattr(args, subnet_region_flag, None)
    if (subnet_region is not None
        and instance_template_region is not None
        and instance_template_region != subnet_region):
      raise exceptions.InvalidArgumentException(
          '--instance-template-region',
          'Values of `--instance-template-region` and `--{}` must match'.format(
              subnet_region_flag))

  client = compute_api.client

  boot_disk_size_gb = utils.BytesToGb(args.boot_disk_size)
  utils.WarnIfDiskSizeIsTooSmall(boot_disk_size_gb, args.boot_disk_type)

  instance_template_ref = Create.InstanceTemplateArg.ResolveAsResource(
      args, compute_api.resources
  )

  AddScopesForServiceProxy(args)
  AddServiceProxyArgsToMetadata(args)

  if hasattr(args, 'network_interface') and args.network_interface:
    if support_subnet_region:
      subnet_region = getattr(args, 'subnet_region', None)
    else:
      subnet_region = getattr(args, 'region', None)
    network_interfaces = (
        instance_template_utils.CreateNetworkInterfaceMessages
    )(
        resources=compute_api.resources,
        scope_lister=flags.GetDefaultScopeLister(client),
        messages=client.messages,
        network_interface_arg=args.network_interface,
        subnet_region=subnet_region,
    )
  else:
    network_tier = getattr(args, 'network_tier', None)
    stack_type = getattr(args, 'stack_type', None)
    ipv6_network_tier = getattr(args, 'ipv6_network_tier', None)
    external_ipv6_address = getattr(args, 'external_ipv6_address', None)
    external_ipv6_prefix_length = getattr(
        args, 'external_ipv6_prefix_length', None
    )
    ipv6_address = None
    ipv6_prefix_length = None
    internal_ipv6_address = None
    internal_ipv6_prefix_length = None

    if support_subnet_region:
      subnet_region = getattr(args, 'subnet_region', None)
    else:
      subnet_region = getattr(args, 'region', None)

    if support_ipv6_reservation:
      ipv6_address = getattr(args, 'ipv6_address', None)
      ipv6_prefix_length = getattr(args, 'ipv6_prefix_length', None)

    if support_internal_ipv6_reservation:
      internal_ipv6_address = getattr(args, 'internal_ipv6_address', None)
      internal_ipv6_prefix_length = getattr(
          args, 'internal_ipv6_prefix_length', None
      )

    network_interfaces = [
        instance_template_utils.CreateNetworkInterfaceMessage(
            resources=compute_api.resources,
            scope_lister=flags.GetDefaultScopeLister(client),
            messages=client.messages,
            network=args.network,
            private_ip=args.private_network_ip,
            subnet_region=subnet_region,
            subnet=args.subnet,
            address=(
                instance_template_utils.EPHEMERAL_ADDRESS
                if not args.no_address and not args.address
                else args.address
            ),
            network_tier=network_tier,
            stack_type=stack_type,
            ipv6_network_tier=ipv6_network_tier,
            ipv6_address=ipv6_address,
            ipv6_prefix_length=ipv6_prefix_length,
            external_ipv6_address=external_ipv6_address,
            external_ipv6_prefix_length=external_ipv6_prefix_length,
            internal_ipv6_address=internal_ipv6_address,
            internal_ipv6_prefix_length=internal_ipv6_prefix_length,
        )
    ]

  if support_mesh:
    ConfigureMeshTemplate(args, instance_template_ref, network_interfaces)

  metadata = metadata_utils.ConstructMetadataMessage(
      client.messages,
      metadata=args.metadata,
      metadata_from_file=args.metadata_from_file,
  )

  # Compute the shieldedInstanceConfig message.
  shieldedinstance_config_message = BuildShieldedInstanceConfigMessage(
      messages=client.messages, args=args
  )

  confidential_instance_config_message = (
      BuildConfidentialInstanceConfigMessage(
          messages=client.messages,
          args=args,
          support_confidential_compute_type=support_confidential_compute_type,
          support_confidential_compute_type_tdx=(
              support_confidential_compute_type_tdx)))

  node_affinities = sole_tenancy_util.GetSchedulingNodeAffinityListFromArgs(
      args, client.messages
  )

  location_hint = None
  if args.IsSpecified('location_hint'):
    location_hint = args.location_hint

  provisioning_model = None
  if hasattr(args, 'provisioning_model') and args.IsSpecified(
      'provisioning_model'
  ):
    provisioning_model = args.provisioning_model

  termination_action = None
  if hasattr(args, 'instance_termination_action') and args.IsSpecified(
      'instance_termination_action'
  ):
    termination_action = args.instance_termination_action

  max_run_duration = None
  if hasattr(args, 'max_run_duration') and args.IsSpecified('max_run_duration'):
    max_run_duration = args.max_run_duration

  termination_time = None
  if hasattr(args, 'termination_time') and args.IsSpecified('termination_time'):
    termination_time = args.termination_time

  host_error_timeout_seconds = None
  if support_host_error_timeout_seconds and args.IsSpecified(
      'host_error_timeout_seconds'
  ):
    host_error_timeout_seconds = args.host_error_timeout_seconds

  local_ssd_recovery_timeout = None
  if support_local_ssd_recovery_timeout and args.IsSpecified(
      'local_ssd_recovery_timeout'
  ):
    local_ssd_recovery_timeout = args.local_ssd_recovery_timeout

  should_set_maintenance_interval = (
      support_maintenance_interval and args.IsSpecified('maintenance_interval')
  )
  maintenance_interval = (
      args.maintenance_interval if should_set_maintenance_interval else None
  )

  graceful_shutdown = instance_utils.ExtractGracefulShutdownFromArgs(
      args, support_graceful_shutdown
  )

  scheduling = instance_utils.CreateSchedulingMessage(
      messages=client.messages,
      maintenance_policy=args.maintenance_policy,
      preemptible=args.preemptible,
      restart_on_failure=args.restart_on_failure,
      node_affinities=node_affinities,
      min_node_cpu=args.min_node_cpu,
      location_hint=location_hint,
      provisioning_model=provisioning_model,
      instance_termination_action=termination_action,
      host_error_timeout_seconds=host_error_timeout_seconds,
      max_run_duration=max_run_duration,
      termination_time=termination_time,
      local_ssd_recovery_timeout=local_ssd_recovery_timeout,
      maintenance_interval=maintenance_interval,
      graceful_shutdown=graceful_shutdown,
  )

  if args.no_service_account:
    service_account = None
  else:
    service_account = args.service_account
  service_accounts = instance_utils.CreateServiceAccountMessages(
      messages=client.messages,
      scopes=[] if args.no_scopes else args.scopes,
      service_account=service_account,
  )

  # create boot disk through args.boot_disk_device_name
  create_boot_disk = not (
      instance_utils.UseExistingBootDisk(
          (args.disk or []) + (args.create_disk or [])
      )
  )
  if create_boot_disk:
    image_expander = image_utils.ImageExpander(client, compute_api.resources)
    try:
      image_uri, _ = image_expander.ExpandImageFlag(
          user_project=instance_template_ref.project,
          image=args.image,
          image_family=args.image_family,
          image_project=args.image_project,
          return_image_resource=True,
      )
    except utils.ImageNotFoundError as e:
      if args.IsSpecified('image_project'):
        raise e
      image_uri, _ = image_expander.ExpandImageFlag(
          user_project=instance_template_ref.project,
          image=args.image,
          image_family=args.image_family,
          image_project=args.image_project,
          return_image_resource=False,
      )
      raise utils.ImageNotFoundError(
          'The resource [{}] was not found. Is the image located in another '
          'project? Use the --image-project flag to specify the '
          'project where the image is located.'.format(image_uri)
      )
  else:
    image_uri = None

  if args.tags:
    tags = client.messages.Tags(items=args.tags)
  else:
    tags = None

  disks = instance_template_utils.CreateDiskMessages(
      args,
      client,
      compute_api.resources,
      instance_template_ref.project,
      image_uri,
      boot_disk_size_gb=boot_disk_size_gb,
      create_boot_disk=create_boot_disk,
      support_kms=support_kms,
      support_multi_writer=support_multi_writer,
      support_replica_zones=support_replica_zones,
      support_storage_pool=support_storage_pool,
  )

  machine_type = instance_utils.InterpretMachineType(
      machine_type=args.machine_type,
      custom_cpu=args.custom_cpu,
      custom_memory=args.custom_memory,
      ext=getattr(args, 'custom_extensions', None),
      vm_type=getattr(args, 'custom_vm_type', None),
  )

  guest_accelerators = instance_template_utils.CreateAcceleratorConfigMessages(
      client.messages, getattr(args, 'accelerator', None)
  )

  if support_region_instance_template and args.IsSpecified(
      'instance_template_region'
  ):
    instance_template = client.messages.InstanceTemplate(
        properties=client.messages.InstanceProperties(
            machineType=machine_type,
            disks=disks,
            canIpForward=args.can_ip_forward,
            metadata=metadata,
            minCpuPlatform=args.min_cpu_platform,
            networkInterfaces=network_interfaces,
            serviceAccounts=service_accounts,
            scheduling=scheduling,
            tags=tags,
            guestAccelerators=guest_accelerators,
        ),
        description=args.description,
        name=instance_template_ref.Name(),
        region=getattr(args, 'instance_template_region', None),
    )
  else:
    instance_template = client.messages.InstanceTemplate(
        properties=client.messages.InstanceProperties(
            machineType=machine_type,
            disks=disks,
            canIpForward=args.can_ip_forward,
            metadata=metadata,
            minCpuPlatform=args.min_cpu_platform,
            networkInterfaces=network_interfaces,
            serviceAccounts=service_accounts,
            scheduling=scheduling,
            tags=tags,
            guestAccelerators=guest_accelerators,
        ),
        description=args.description,
        name=instance_template_ref.Name(),
    )

  instance_template.properties.shieldedInstanceConfig = (
      shieldedinstance_config_message
  )

  instance_template.properties.reservationAffinity = (
      instance_utils.GetReservationAffinity(
          args, client, support_specific_then_x_affinity
      )
  )

  instance_template.properties.confidentialInstanceConfig = (
      confidential_instance_config_message
  )

  if args.IsSpecified('network_performance_configs'):
    instance_template.properties.networkPerformanceConfig = (
        instance_utils.GetNetworkPerformanceConfig(args, client)
    )

  if args.IsSpecified('resource_policies'):
    instance_template.properties.resourcePolicies = getattr(
        args, 'resource_policies', []
    )

  if support_post_key_revocation_action_type and args.IsSpecified(
      'post_key_revocation_action_type'
  ):
    instance_template.properties.postKeyRevocationActionType = arg_utils.ChoiceToEnum(
        args.post_key_revocation_action_type,
        client.messages.InstanceProperties.PostKeyRevocationActionTypeValueValuesEnum,
    )

  if args.IsSpecified('key_revocation_action_type'):
    instance_template.properties.keyRevocationActionType = arg_utils.ChoiceToEnum(
        args.key_revocation_action_type,
        client.messages.InstanceProperties.KeyRevocationActionTypeValueValuesEnum,
    )

  if args.private_ipv6_google_access_type is not None:
    instance_template.properties.privateIpv6GoogleAccess = (
        instances_flags.GetPrivateIpv6GoogleAccessTypeFlagMapperForTemplate(
            client.messages
        ).GetEnumForChoice(args.private_ipv6_google_access_type)
    )

  # Create an AdvancedMachineFeatures message if any of the features requiring
  # one have been specified.
  has_visible_core_count = (
      support_visible_core_count and args.visible_core_count is not None
  )
  if (
      args.enable_nested_virtualization is not None
      or args.threads_per_core is not None
      or (support_numa_node_count and args.numa_node_count is not None)
      or has_visible_core_count
      or args.enable_uefi_networking is not None
      or (
          support_performance_monitoring_unit
          and args.performance_monitoring_unit
      )
  ):
    visible_core_count = (
        args.visible_core_count if has_visible_core_count else None
    )

    instance_template.properties.advancedMachineFeatures = (
        instance_utils.CreateAdvancedMachineFeaturesMessage(
            client.messages,
            args.enable_nested_virtualization,
            args.threads_per_core,
            args.numa_node_count if support_numa_node_count else None,
            visible_core_count,
            args.enable_uefi_networking,
            args.performance_monitoring_unit
            if support_performance_monitoring_unit
            else None,
        )
    )

  if args.resource_manager_tags:
    ret_resource_manager_tags = (
        resource_manager_tags_utils.GetResourceManagerTags(
            args.resource_manager_tags
        )
    )
    if ret_resource_manager_tags is not None:
      properties = client.messages.InstanceProperties
      instance_template.properties.resourceManagerTags = (
          properties.ResourceManagerTagsValue(
              additionalProperties=[
                  properties.ResourceManagerTagsValue.AdditionalProperty(
                      key=key, value=value)
                  for key, value in sorted(
                      six.iteritems(ret_resource_manager_tags))])
      )

  if support_partner_metadata and (
      args.partner_metadata or args.partner_metadata_from_file
  ):
    properties = client.messages.InstanceProperties
    partner_metadata_dict = partner_metadata_utils.CreatePartnerMetadataDict(
        args
    )
    partner_metadata_utils.ValidatePartnerMetadata(partner_metadata_dict)
    partner_metadata_message = properties.PartnerMetadataValue()
    for namespace, structured_entries in partner_metadata_dict.items():
      partner_metadata_message.additionalProperties.append(
          properties.PartnerMetadataValue.AdditionalProperty(
              key=namespace,
              value=partner_metadata_utils.ConvertStructuredEntries(
                  structured_entries
              ),
          )
      )
    instance_template.properties.partnerMetadata = partner_metadata_message

  request = client.messages.ComputeInstanceTemplatesInsertRequest(
      instanceTemplate=instance_template, project=instance_template_ref.project
  )

  if support_region_instance_template and args.IsSpecified(
      'instance_template_region'
  ):
    request = client.messages.ComputeRegionInstanceTemplatesInsertRequest(
        instanceTemplate=instance_template,
        project=instance_template_ref.project,
        region=instance_template.region,
    )

  request.instanceTemplate.properties.labels = ParseCreateArgsWithServiceProxy(
      args, client.messages.InstanceProperties.LabelsValue
  )

  _AddSourceInstanceToTemplate(
      compute_api, args, instance_template, support_source_instance
  )

  if support_region_instance_template and args.IsSpecified(
      'instance_template_region'
  ):
    return client.MakeRequests(
        [(client.apitools_client.regionInstanceTemplates, 'Insert', request)]
    )
  else:
    return client.MakeRequests(
        [(client.apitools_client.instanceTemplates, 'Insert', request)]
    )


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Compute Engine virtual machine instance template.

  *{command}* facilitates the creation of Compute Engine
  virtual machine instance templates. For example, running:

      $ {command} INSTANCE-TEMPLATE

  will create one instance templates called 'INSTANCE-TEMPLATE'.

  Instance templates are global resources, and can be used to create
  instances in any zone.
  """

  _support_source_instance = True
  _support_kms = True
  _support_post_key_revocation_action_type = False
  _support_multi_writer = False
  _support_mesh = False
  _support_numa_node_count = False
  _support_visible_core_count = True
  _support_max_run_duration = False
  _support_region_instance_template = True
  _support_subnet_region = False
  _support_confidential_compute_type = False
  _support_confidential_compute_type_tdx = False
  _support_network_attachments = False
  _support_replica_zones = True
  _support_local_ssd_size = True
  _support_network_queue_count = True
  _support_performance_monitoring_unit = False
  _support_internal_ipv6_reservation = True
  _support_storage_pool = False
  _support_partner_metadata = False
  _support_local_ssd_recovery_timeout = True
  _support_specific_then_x_affinity = False
  _support_graceful_shutdown = False
  _support_vlan_nic = False

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        release_track=base.ReleaseTrack.GA,
        support_source_instance=cls._support_source_instance,
        support_kms=cls._support_kms,
        support_multi_writer=cls._support_multi_writer,
        support_mesh=cls._support_mesh,
        support_numa_node_count=cls._support_numa_node_count,
        support_visible_core_count=cls._support_visible_core_count,
        support_max_run_duration=cls._support_max_run_duration,
        support_region_instance_template=cls._support_region_instance_template,
        support_subnet_region=cls._support_subnet_region,
        support_network_attachments=cls._support_network_attachments,
        support_replica_zones=cls._support_replica_zones,
        support_local_ssd_size=cls._support_local_ssd_size,
        support_network_queue_count=cls._support_network_queue_count,
        support_storage_pool=cls._support_storage_pool,
        support_local_ssd_recovery_timeout=cls._support_local_ssd_recovery_timeout,
        support_specific_then_x_affinity=cls._support_specific_then_x_affinity,
        support_graceful_shutdown=cls._support_graceful_shutdown,
        support_vlan_nic=cls._support_vlan_nic,
    )
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.GA)
    instances_flags.AddPrivateIpv6GoogleAccessArgForTemplate(
        parser, utils.COMPUTE_GA_API_VERSION
    )
    instances_flags.AddConfidentialComputeArgs(
        parser,
        support_confidential_compute_type=cls
        ._support_confidential_compute_type,
        support_confidential_compute_type_tdx=cls
        ._support_confidential_compute_type_tdx)
    instance_templates_flags.AddKeyRevocationActionTypeArgs(parser)

  def Run(self, args):
    """Creates and runs an InstanceTemplates.Insert request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      A resource object dispatched by display.Displayer().
    """
    return _RunCreate(
        base_classes.ComputeApiHolder(base.ReleaseTrack.GA),
        args,
        support_source_instance=self._support_source_instance,
        support_kms=self._support_kms,
        support_post_key_revocation_action_type=self._support_post_key_revocation_action_type,
        support_multi_writer=self._support_multi_writer,
        support_mesh=self._support_mesh,
        support_numa_node_count=self._support_numa_node_count,
        support_visible_core_count=self._support_visible_core_count,
        support_max_run_duration=self._support_max_run_duration,
        support_region_instance_template=self._support_region_instance_template,
        support_subnet_region=self._support_subnet_region,
        support_confidential_compute_type=self._support_confidential_compute_type,
        support_confidential_compute_type_tdx=self._support_confidential_compute_type_tdx,
        support_replica_zones=self._support_replica_zones,
        support_performance_monitoring_unit=self._support_performance_monitoring_unit,
        support_internal_ipv6_reservation=self._support_internal_ipv6_reservation,
        support_storage_pool=self._support_storage_pool,
        support_partner_metadata=self._support_partner_metadata,
        support_local_ssd_recovery_timeout=self._support_local_ssd_recovery_timeout,
        support_specific_then_x_affinity=self._support_specific_then_x_affinity,
        support_graceful_shutdown=self._support_graceful_shutdown,
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Compute Engine virtual machine instance template.

  *{command}* facilitates the creation of Compute Engine
  virtual machine instance templates. For example, running:

      $ {command} INSTANCE-TEMPLATE

  will create one instance templates called 'INSTANCE-TEMPLATE'.

  Instance templates are global resources, and can be used to create
  instances in any zone.
  """

  _support_source_instance = True
  _support_kms = True
  _support_post_key_revocation_action_type = True
  _support_multi_writer = True
  _support_mesh = True
  _support_host_error_timeout_seconds = True
  _support_numa_node_count = False
  _support_visible_core_count = True
  _support_max_run_duration = True
  _support_region_instance_template = True
  _support_subnet_region = False
  _support_confidential_compute_type = True
  _support_confidential_compute_type_tdx = True
  _support_network_attachments = False
  _support_replica_zones = True
  _support_local_ssd_recovery_timeout = True
  _support_local_ssd_size = True
  _support_network_queue_count = True
  _support_performance_monitoring_unit = False
  _support_internal_ipv6_reservation = True
  _support_storage_pool = False
  _support_partner_metadata = False
  _support_maintenance_interval = True
  _support_specific_then_x_affinity = True
  _support_graceful_shutdown = False
  _support_vlan_nic = False

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        release_track=base.ReleaseTrack.BETA,
        support_local_ssd_size=cls._support_local_ssd_size,
        support_source_instance=cls._support_source_instance,
        support_kms=cls._support_kms,
        support_multi_writer=cls._support_multi_writer,
        support_mesh=cls._support_mesh,
        support_host_error_timeout_seconds=cls._support_host_error_timeout_seconds,
        support_visible_core_count=cls._support_visible_core_count,
        support_max_run_duration=cls._support_max_run_duration,
        support_region_instance_template=cls._support_region_instance_template,
        support_subnet_region=cls._support_subnet_region,
        support_network_attachments=cls._support_network_attachments,
        support_replica_zones=cls._support_replica_zones,
        support_local_ssd_recovery_timeout=cls._support_local_ssd_recovery_timeout,
        support_network_queue_count=cls._support_network_queue_count,
        support_storage_pool=cls._support_storage_pool,
        support_maintenance_interval=cls._support_maintenance_interval,
        support_specific_then_x_affinity=cls._support_specific_then_x_affinity,
        support_graceful_shutdown=cls._support_graceful_shutdown,
        support_vlan_nic=cls._support_vlan_nic,
    )
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.BETA)
    instances_flags.AddPrivateIpv6GoogleAccessArgForTemplate(
        parser, utils.COMPUTE_BETA_API_VERSION
    )
    instances_flags.AddConfidentialComputeArgs(
        parser,
        support_confidential_compute_type=cls
        ._support_confidential_compute_type,
        support_confidential_compute_type_tdx=cls
        ._support_confidential_compute_type_tdx)
    instances_flags.AddPostKeyRevocationActionTypeArgs(parser)
    instance_templates_flags.AddKeyRevocationActionTypeArgs(parser)

  def Run(self, args):
    """Creates and runs an InstanceTemplates.Insert request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      A resource object dispatched by display.Displayer().
    """
    return _RunCreate(
        base_classes.ComputeApiHolder(base.ReleaseTrack.BETA),
        args=args,
        support_source_instance=self._support_source_instance,
        support_kms=self._support_kms,
        support_post_key_revocation_action_type=self._support_post_key_revocation_action_type,
        support_multi_writer=self._support_multi_writer,
        support_mesh=self._support_mesh,
        support_host_error_timeout_seconds=self._support_host_error_timeout_seconds,
        support_numa_node_count=self._support_numa_node_count,
        support_visible_core_count=self._support_visible_core_count,
        support_max_run_duration=self._support_max_run_duration,
        support_region_instance_template=self._support_region_instance_template,
        support_subnet_region=self._support_subnet_region,
        support_confidential_compute_type=self._support_confidential_compute_type,
        support_confidential_compute_type_tdx=self._support_confidential_compute_type_tdx,
        support_replica_zones=self._support_replica_zones,
        support_local_ssd_recovery_timeout=self._support_local_ssd_recovery_timeout,
        support_performance_monitoring_unit=self._support_performance_monitoring_unit,
        support_internal_ipv6_reservation=self._support_internal_ipv6_reservation,
        support_storage_pool=self._support_storage_pool,
        support_partner_metadata=self._support_partner_metadata,
        support_maintenance_interval=self._support_maintenance_interval,
        support_specific_then_x_affinity=self._support_specific_then_x_affinity,
        support_graceful_shutdown=self._support_graceful_shutdown,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a Compute Engine virtual machine instance template.

  *{command}* facilitates the creation of Compute Engine
  virtual machine instance templates. For example, running:

      $ {command} INSTANCE-TEMPLATE

  will create one instance templates called 'INSTANCE-TEMPLATE'.

  Instance templates are global resources, and can be used to create
  instances in any zone.
  """

  _support_source_instance = True
  _support_kms = True
  _support_post_key_revocation_action_type = True
  _support_multi_writer = True
  _support_mesh = True
  _support_host_error_timeout_seconds = True
  _support_numa_node_count = True
  _support_visible_core_count = True
  _support_max_run_duration = True
  _support_region_instance_template = True
  _support_subnet_region = True
  _support_confidential_compute_type = True
  _support_confidential_compute_type_tdx = True
  _support_network_attachments = True
  _support_replica_zones = True
  _support_local_ssd_recovery_timeout = True
  _support_network_queue_count = True
  _support_local_ssd_size = True
  _support_performance_monitoring_unit = True
  _support_internal_ipv6_reservation = True
  _support_storage_pool = True
  _support_partner_metadata = True
  _support_maintenance_interval = True
  _support_specific_then_x_affinity = True
  _support_graceful_shutdown = True
  _support_vlan_nic = True
  _support_ipv6_only = True

  @classmethod
  def Args(cls, parser):
    _CommonArgs(
        parser,
        release_track=base.ReleaseTrack.ALPHA,
        support_local_ssd_size=cls._support_local_ssd_size,
        support_source_instance=cls._support_source_instance,
        support_kms=cls._support_kms,
        support_multi_writer=cls._support_multi_writer,
        support_mesh=cls._support_mesh,
        support_host_error_timeout_seconds=cls._support_host_error_timeout_seconds,
        support_numa_node_count=cls._support_numa_node_count,
        support_visible_core_count=cls._support_visible_core_count,
        support_max_run_duration=cls._support_max_run_duration,
        support_region_instance_template=cls._support_region_instance_template,
        support_subnet_region=cls._support_subnet_region,
        support_network_attachments=cls._support_network_attachments,
        support_replica_zones=cls._support_replica_zones,
        support_local_ssd_recovery_timeout=cls._support_local_ssd_recovery_timeout,
        support_network_queue_count=cls._support_network_queue_count,
        support_storage_pool=cls._support_storage_pool,
        support_maintenance_interval=cls._support_maintenance_interval,
        support_specific_then_x_affinity=cls._support_specific_then_x_affinity,
        support_graceful_shutdown=cls._support_graceful_shutdown,
        support_ipv6_only=cls._support_ipv6_only,
        support_vlan_nic=cls._support_vlan_nic,
    )
    instances_flags.AddLocalNvdimmArgs(parser)
    instances_flags.AddMinCpuPlatformArgs(parser, base.ReleaseTrack.ALPHA)
    instances_flags.AddConfidentialComputeArgs(
        parser,
        support_confidential_compute_type=cls
        ._support_confidential_compute_type,
        support_confidential_compute_type_tdx=cls
        ._support_confidential_compute_type_tdx)
    instances_flags.AddPrivateIpv6GoogleAccessArgForTemplate(
        parser, utils.COMPUTE_ALPHA_API_VERSION
    )
    instances_flags.AddPostKeyRevocationActionTypeArgs(parser)
    instances_flags.AddIPv6AddressAlphaArgs(parser)
    instances_flags.AddIPv6PrefixLengthAlphaArgs(parser)
    instance_templates_flags.AddKeyRevocationActionTypeArgs(parser)
    instances_flags.AddPerformanceMonitoringUnitArgs(parser)
    partner_metadata_utils.AddPartnerMetadataArgs(parser)

  def Run(self, args):
    """Creates and runs an InstanceTemplates.Insert request.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      A resource object dispatched by display.Displayer().
    """
    return _RunCreate(
        base_classes.ComputeApiHolder(base.ReleaseTrack.ALPHA),
        args=args,
        support_source_instance=self._support_source_instance,
        support_kms=self._support_kms,
        support_post_key_revocation_action_type=self._support_post_key_revocation_action_type,
        support_multi_writer=self._support_multi_writer,
        support_mesh=self._support_mesh,
        support_host_error_timeout_seconds=self._support_host_error_timeout_seconds,
        support_numa_node_count=self._support_numa_node_count,
        support_visible_core_count=self._support_visible_core_count,
        support_max_run_duration=self._support_max_run_duration,
        support_region_instance_template=self._support_region_instance_template,
        support_subnet_region=self._support_subnet_region,
        support_confidential_compute_type=self._support_confidential_compute_type,
        support_confidential_compute_type_tdx=self._support_confidential_compute_type_tdx,
        support_replica_zones=self._support_replica_zones,
        support_local_ssd_recovery_timeout=self._support_local_ssd_recovery_timeout,
        support_performance_monitoring_unit=self._support_performance_monitoring_unit,
        support_internal_ipv6_reservation=self._support_internal_ipv6_reservation,
        support_storage_pool=self._support_storage_pool,
        support_partner_metadata=self._support_partner_metadata,
        support_maintenance_interval=self._support_maintenance_interval,
        support_specific_then_x_affinity=self._support_specific_then_x_affinity,
        support_graceful_shutdown=self._support_graceful_shutdown,
    )


DETAILED_HELP = {
    'brief': 'Create a Compute Engine virtual machine instance template.',
    'DESCRIPTION': (
        '*{command}* facilitates the creation of Compute Engine '
        'virtual machine instance templates. Instance '
        'templates are global resources, and can be used to create '
        'instances in any zone.'
    ),
    'EXAMPLES': """\
        To create an instance template named 'INSTANCE-TEMPLATE' with the 'n2'
        vm type, '9GB' memory, and 2 CPU cores, run:

          $ {command} INSTANCE-TEMPLATE --custom-vm-type=n2 --custom-cpu=2 --custom-memory=9GB
        """,
}

Create.detailed_help = DETAILED_HELP
