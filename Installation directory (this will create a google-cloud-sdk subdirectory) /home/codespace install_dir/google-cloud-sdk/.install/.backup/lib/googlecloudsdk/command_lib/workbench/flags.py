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
"""Utilities for flags for `gcloud tasks` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.compute.networks import flags as compute_network_flags
from googlecloudsdk.command_lib.compute.networks.subnets import flags as compute_subnet_flags
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.workbench import completers
from googlecloudsdk.core import properties


def GetLocationResourceArg(help_text):
  """Constructs and returns the Location Resource Argument."""

  def GetLocationResourceSpec():
    """Constructs and returns the Location Resource Argument."""
    def LocationAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='location',
          help_text=(
              'Google Cloud location'
              'https://cloud.google.com/compute/docs/regions-zones/#locations.'
          ),
          fallthroughs=[
              deps.PropertyFallthrough(properties.VALUES.notebooks.location),
          ],
      )

    return concepts.ResourceSpec(
        'notebooks.projects.locations',
        resource_name='location',
        api_version='v2',
        projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        locationsId=LocationAttributeConfig())

  return concept_parsers.ConceptParser.ForResource(
      '--location', GetLocationResourceSpec(), help_text, required=True)


def GetInstanceResourceArg(help_text):
  """Constructs and returns the Instance Resource Argument."""

  def GetInstanceResourceSpec():
    """Constructs and returns the Resource specification for Instance."""

    def InstanceAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='instance', help_text=help_text)

    def LocationAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='location',
          help_text=(
              'Google Cloud location of this environment '
              'https://cloud.google.com/compute/docs/regions-zones/#locations.'
          ),
          fallthroughs=[
              deps.PropertyFallthrough(properties.VALUES.notebooks.location),
          ],
      )

    return concepts.ResourceSpec(
        'notebooks.projects.locations.instances',
        resource_name='instance',
        api_version='v2',
        instancesId=InstanceAttributeConfig(),
        locationsId=LocationAttributeConfig(),
        projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        disable_auto_completers=False)

  return concept_parsers.ConceptParser.ForResource(
      'instance', GetInstanceResourceSpec(), help_text, required=True)


def AddNetworkArgument(help_text, parser):
  """Adds Resource arg for network to the parser."""

  def GetNetworkResourceSpec():
    """Constructs and returns the Resource specification for Subnet."""

    def NetworkAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='network',
          help_text=help_text,
          completer=compute_network_flags.NetworksCompleter)

    return concepts.ResourceSpec(
        'compute.networks',
        resource_name='network',
        network=NetworkAttributeConfig(),
        project=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        disable_auto_completers=False)

  concept_parsers.ConceptParser.ForResource('--network',
                                            GetNetworkResourceSpec(),
                                            help_text).AddToParser(parser)


def AddSubnetArgument(help_text, parser):
  """Adds Resource arg for subnetwork to the parser."""

  def GetSubnetResourceSpec():
    """Constructs and returns the Resource specification for Subnet."""

    def SubnetAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='subnet',
          help_text=help_text,
          completer=compute_subnet_flags.SubnetworksCompleter)

    def RegionAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='subnet-region',
          help_text=(
              'Google Cloud region of this subnetwork '
              'https://cloud.google.com/compute/docs/regions-zones/#locations.'
          ),
          completer=completers.RegionCompleter)

    return concepts.ResourceSpec(
        'compute.subnetworks',
        resource_name='subnetwork',
        subnetwork=SubnetAttributeConfig(),
        region=RegionAttributeConfig(),
        project=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        disable_auto_completers=False)

  concept_parsers.ConceptParser.ForResource('--subnet', GetSubnetResourceSpec(),
                                            help_text).AddToParser(parser)


def AddInstanceResource(parser, add_async_flag=True):
  GetInstanceResourceArg(
      ('User-defined unique name of this instance. The instance name must be '
       '1 to 63 characters long and contain only lowercase letters, numeric '
       'characters, and dashes. The first character must be a lowercase letter '
       'and the last character cannot be a dash.')).AddToParser(parser)
  if add_async_flag:
    base.ASYNC_FLAG.AddToParser(parser)


def AddDiagnosticConfigFlags(parser, vm_type):
  """Adds Diagnostic config flags to parser."""
  parser.add_argument(
      '--gcs-bucket',
      dest='gcs_bucket',
      help=('The Cloud Storage bucket where the log files generated from the '
            'diagnose command will be stored. storage.buckets.writer '
            'permissions must be given to project\'s service account or '
            'user credential. Format: gs://`{gcs_bucket}` '),
      required=True)
  parser.add_argument(
      '--relative-path',
      dest='relative_path',
      help=('Defines the relative storage path in the Cloud Storage bucket '
            'where the diagnostic logs will be written. Default path will be '
            'the root directory of the Cloud Storage bucket'
            'Format of full path: gs://`{gcs_bucket}`/`{relative_path}`/ '),
      required=False)
  parser.add_argument(
      '--enable-repair',
      action='store_true',
      dest='enable_repair',
      default=False,
      help=('Enables flag to repair service for {}'.format(vm_type)),
      required=False)
  parser.add_argument(
      '--enable-packet-capture',
      action='store_true',
      dest='enable_packet_capture',
      default=False,
      help=('Enables flag to capture packets from '
            'the {} for 30 seconds'.format(vm_type)),
      required=False)
  parser.add_argument(
      '--enable-copy-home-files',
      action='store_true',
      dest='enable_copy_home_files',
      default=False,
      help=('Enables flag to copy all `/home/jupyter` folder contents'),
      required=False)


def AddCreateInstanceFlags(parser):
  """Construct groups and arguments specific to the instance creation."""
  accelerator_choices = [
      'NVIDIA_TESLA_K80', 'NVIDIA_TESLA_P100',
      'NVIDIA_TESLA_V100', 'NVIDIA_TESLA_P4', 'NVIDIA_TESLA_T4',
      'NVIDIA_TESLA_A100', 'NVIDIA_TESLA_A100_80GB',
      'NVIDIA_TESLA_T4_VWS', 'NVIDIA_TESLA_P100_VWS', 'NVIDIA_TESLA_P4_VWS'
  ]
  disk_choices = ['PD_STANDARD', 'PD_SSD', 'PD_BALANCED', 'PD_EXTREME']
  encryption_choices = ['GMEK', 'CMEK']
  nic_type_choices = ['VIRTIGO_NET', 'GVNIC']

  AddInstanceResource(parser)
  gce_setup_group = parser.add_group(
      help=(
          'Gce Setup for the instance'))
  gce_setup_group.add_argument(
      '--machine-type',
      help=(
          'The '
          '[Compute Engine machine type](https://cloud.google.com/sdk/gcloud/reference/compute/machine-types) '  # pylint: disable=line-too-long
          'of this instance.'),
      default='n1-standard-4')
  accelerator_group = gce_setup_group.add_group(
      help=(
          'The hardware accelerator used on this instance. If you use '
          'accelerators, make sure that your configuration has [enough vCPUs '
          'and memory to support the `machine_type` you have selected]'
          '(/compute/docs/gpus/#gpus-list).'))
  accelerator_group.add_argument(
      '--accelerator-type',
      help='Type of this accelerator.',
      choices=accelerator_choices,
      default=None)
  accelerator_group.add_argument(
      '--accelerator-core-count',
      help='Count of cores of this accelerator.',
      type=int)
  service_account_group = gce_setup_group.add_group(
      help=(
          'The service account on this instance, giving access to other '
          'Google Cloud services. You can use any service account within the '
          'same project, but you must grant the service account user permission '
          'to use the instance. If not specified, the [Compute Engine default '
          'service account](/compute/docs/access/service-accounts#default_'
          'service_account) is used.'
      ),
  )
  service_account_group.add_argument(
      '--service-account-email',
      help=(
          'The service account on this instance, giving access to other '
          'Google Cloud services. You can use any service account within the '
          'same project, but you must grant the service account user permission '
          'to use the instance. If not specified, the [Compute Engine default '
          'service account](/compute/docs/access/service-accounts#default_'
          'service_account) is used.'
      ),
  )
  image_group = gce_setup_group.add_group(mutex=True)
  vm_source_group = image_group.add_group()
  vm_source_group.add_argument(
      '--vm-image-project',
      help=(
          'The ID of the Google Cloud project that this VM image belongs to. '
          'Format: projects/`{project_id}`.'
      ),
      default='deeplearning-platform-release',
  )
  vm_mutex_group = vm_source_group.add_group(mutex=True, required=True)
  vm_mutex_group.add_argument(
      '--vm-image-name', help='Use this VM image name to find the image.'
  )
  vm_mutex_group.add_argument(
      '--vm-image-family',
      help=(
          'Use this VM image family to find the image; the newest image in '
          'this family will be used.'
      )
  )
  container_group = image_group.add_group()
  container_group.add_argument(
      '--container-repository',
      help=(
          'The path to the container image repository. '
          'For example: gcr.io/`{project_id}`/`{image_name}`.'
      ),
      required=True,
  )
  container_group.add_argument(
      '--container-tag',
      help=(
          'The tag of the container image. If not specified, '
          'this defaults to the latest tag.'
      ),
  )

  boot_group = gce_setup_group.add_group(help='Boot disk configurations.')
  boot_group.add_argument(
      '--boot-disk-type',
      choices=disk_choices,
      default=None,
      help=(
          'Type of boot disk attached to this instance, defaults to '
          'standard persistent disk (`PD_STANDARD`).'
      ),
  )
  boot_group.add_argument(
      '--boot-disk-size',
      type=int,
      help=(
          'Size of boot disk in GB attached to this instance, up to '
          'a maximum of 64000 GB (64 TB). The minimum recommended value '
          'is 100 GB. If not specified, this defaults to 100.'
      ),
  )
  boot_group.add_argument(
      '--boot-disk-encryption',
      choices=encryption_choices,
      default=None,
      help='Disk encryption method used on the boot disk, defaults to GMEK.',
  )
  boot_kms_flag_overrides = {
      'kms-keyring': '--boot-disk-encryption-key-keyring',
      'kms-location': '--boot-disk-encryption-key-location',
      'kms-project': '--boot-disk-encryption-key-project'
  }
  kms_resource_args.AddKmsKeyResourceArg(
      parser=boot_group,
      resource='boot_disk',
      name='--boot-disk-kms-key',
      flag_overrides=boot_kms_flag_overrides,
  )

  data_group = gce_setup_group.add_group(help='Data disk configurations.')
  data_group.add_argument(
      '--data-disk-type',
      choices=disk_choices,
      default=None,
      help=(
          'Type of data disk attached to this instance, defaults to '
          'standard persistent disk (`PD_STANDARD`).'
      ),
  )
  data_group.add_argument(
      '--data-disk-size',
      type=int,
      help=(
          'Size of data disk in GB attached to this instance, up to '
          'a maximum of 64000 GB (64 TB). The minimum recommended value '
          'is 100 GB. If not specified, this defaults to 100.'
      ),
  )
  data_group.add_argument(
      '--data-disk-encryption',
      choices=encryption_choices,
      default=None,
      help='Disk encryption method used on the data disk, defaults to GMEK.',
  )
  data_kms_flag_overrides = {
      'kms-keyring': '--data-disk-encryption-key-keyring',
      'kms-location': '--data-disk-encryption-key-location',
      'kms-project': '--data-disk-encryption-key-project',
  }
  kms_resource_args.AddKmsKeyResourceArg(
      parser=data_group,
      resource='data_disk',
      name='--data-disk-kms-key',
      flag_overrides=data_kms_flag_overrides,
  )

  shielded_vm_group = gce_setup_group.add_group(
      help='Shielded VM configurations.'
  )
  shielded_vm_group.add_argument(
      '--shielded-secure-boot',
      help='Boot instance with secure boot enabled',
      type=str,
  )
  shielded_vm_group.add_argument(
      '--shielded-vtpm',
      help='Boot instance with TPM (Trusted Platform Module) enabled',
      type=str,
  )
  shielded_vm_group.add_argument(
      '--shielded-integrity-monitoring',
      help='Enable monitoring of the boot integrity of the instance',
      type=str,
  )

  gpu_group = gce_setup_group.add_group(help='GPU driver configurations.')
  gpu_group.add_argument(
      '--install-gpu-driver',
      action='store_true',
      dest='install_gpu_driver',
      help=(
          'Whether the end user authorizes Google Cloud to install a GPU driver'
          ' on this instance. If this field is empty or set to false, the GPU'
          " driver won't be installed. Only applicable to instances with GPUs."
      ),
  )
  gpu_group.add_argument(
      '--custom-gpu-driver-path',
      help=(
          'Specify a custom Cloud Storage path where the GPU driver is '
          "stored. If not specified, we'll automatically choose from official "
          'GPU drivers.'
      ),
  )

  network_group = gce_setup_group.add_group(help='Network configs.')
  AddNetworkArgument(
      ('The name of the VPC that this instance is in. Format: '
       'projects/`{project_id}`/global/networks/`{network_id}`.'),
      network_group)
  AddSubnetArgument(
      ('The name of the subnet that this instance is in. Format: projects/'
       '`{project_id}`/regions/`{region}`/subnetworks/`{subnetwork_id}`.'),
      network_group)

  network_group.add_argument(
      '--nic-type',
      help='Type of the network interface card.',
      choices=nic_type_choices,
      default=None)

  gce_setup_group.add_argument(
      '--disable-public-ip',
      action='store_true',
      dest='disable_public_ip',
      help="""\
  If specified, no public IP will be assigned to this instance.""")
  gce_setup_group.add_argument(
      '--enable-ip-forwarding',
      action='store_true',
      dest='enable_ip_forwarding',
      help="""\
  If specified, IP forwarding will be enabled for this instance.""")
  parser.add_argument(
      '--disable-proxy-access',
      action='store_true',
      dest='disable_proxy_access',
      help="""\
  If true, the notebook instance will not register with the proxy.""")

  gce_setup_group.add_argument(
      '--metadata',
      help='Custom metadata to apply to this instance.',
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE')

  gce_setup_group.add_argument(
      '--tags',
      metavar='TAGS',
      help=('Tags to apply to this instance.'),
      type=arg_parsers.ArgList())

  parser.add_argument(
      '--labels',
      help=('Labels to apply to this instance. These can be later modified '
            'by the setLabels method.'),
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE')

  parser.add_argument(
      '--instance-owners',
      help=(
          'The owners of this instance after creation. Format:'
          ' `alias@example.com`. Currently supports one owner only. If not'
          " specified, all of the service account users of the VM instance's"
          ' service account can use the instance.'
      ),
  )


def AddDescribeInstanceFlags(parser):
  AddInstanceResource(parser, add_async_flag=False)


def AddDeleteInstanceFlags(parser):
  AddInstanceResource(parser)


def AddListInstanceFlags(parser):
  parser.add_argument(
      '--location',
      completer=completers.LocationCompleter,
      help=('Google Cloud location of this environment '
            'https://cloud.google.com/compute/docs/regions-zones/#locations.'))


def AddRegisterInstanceFlags(parser):
  AddInstanceResource(parser)


def AddResetInstanceFlags(parser):
  AddInstanceResource(parser)


def AddStartInstanceFlags(parser):
  AddInstanceResource(parser)


def AddStopInstanceFlags(parser):
  AddInstanceResource(parser)


def AddGetHealthInstanceFlags(parser):
  AddInstanceResource(parser, add_async_flag=False)


def AddIsUpgradeableInstanceFlags(parser):
  AddInstanceResource(parser, add_async_flag=False)


def AddUpgradeInstanceFlags(parser):
  AddInstanceResource(parser)


def AddRollbackInstanceFlags(parser):
  AddInstanceResource(parser)
  parser.add_argument(
      '--target-snapshot',
      help='The saved snapshot to rollback to.',
      required=True)


def AddUpdateInstanceFlags(parser):
  """Adds accelerator, labels and machine type flags to the parser for update."""
  accelerator_choices = [
      'NVIDIA_TESLA_K80', 'NVIDIA_TESLA_P100',
      'NVIDIA_TESLA_V100', 'NVIDIA_TESLA_P4', 'NVIDIA_TESLA_T4',
      'NVIDIA_TESLA_A100', 'NVIDIA_TESLA_A100_80GB',
      'NVIDIA_TESLA_T4_VWS', 'NVIDIA_TESLA_P100_VWS', 'NVIDIA_TESLA_P4_VWS'
  ]
  AddInstanceResource(parser)
  gce_setup_group = parser.add_group(
      help=(
          'Gce Setup for the instance'))
  accelerator_group = gce_setup_group.add_group(
      help='Accelerator configurations.'
      )
  accelerator_group.add_argument(
      '--accelerator-type',
      help='Type of this accelerator.',
      choices=accelerator_choices,
      default=None)
  accelerator_group.add_argument(
      '--accelerator-core-count',
      help='Count of cores of this accelerator.',
      type=int)
  gpu_group = gce_setup_group.add_group(help='GPU driver configurations.')
  gpu_group.add_argument(
      '--install-gpu-driver',
      help='Install gpu driver',
      type=bool)
  gpu_group.add_argument(
      '--custom-gpu-driver-path',
      help='custom gpu driver path',
      type=str)
  shielded_vm_group = gce_setup_group.add_group(
      help='Shielded VM configurations.'
      )
  shielded_vm_group.add_argument(
      '--shielded-secure-boot',
      help='Boot instance with secure boot enabled',
      type=str)
  shielded_vm_group.add_argument(
      '--shielded-vtpm',
      help='Boot instance with TPM (Trusted Platform Module) enabled',
      type=str)
  shielded_vm_group.add_argument(
      '--shielded-integrity-monitoring',
      help='Enable monitoring of the boot integrity of the instance',
      type=str)
  parser.add_argument(
      '--labels',
      help=('Labels to apply to this instance. These can be later modified '
            'by the setLabels method.'),
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE')
  gce_setup_group.add_argument(
      '--metadata',
      help='Custom metadata to apply to this instance.',
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE')
  gce_setup_group.add_argument(
      '--machine-type',
      help=(
          'The '
          '[Compute Engine machine type](https://cloud.google.com/sdk/gcloud/reference/compute/machine-types) '  # pylint: disable=line-too-long
          'of this instance.'))


def AddDiagnoseInstanceFlags(parser):
  """Construct groups and arguments specific to the instance diagnosing."""
  AddInstanceResource(parser)
  AddDiagnosticConfigFlags(parser, 'instance')


def AddResizeDiskFlags(parser):
  """Construct groups and arguments specific to the disk resizing."""
  AddInstanceResource(parser)
  disk_group = parser.add_group(
      help=(
          'Disk resizing configurations Amount needs to be greater than the'
          ' existing size.'
      ),
      mutex=True,
      required=True,
  )
  disk_group.add_argument(
      '--boot-disk-size',
      type=int,
      help=(
          'Size of boot disk in GB attached to this instance, up to '
          'a maximum of 64000 GB (64 TB).'
      ),
  )
  disk_group.add_argument(
      '--data-disk-size',
      type=int,
      help=(
          'Size of data disk in GB attached to this instance, up to '
          'a maximum of 64000 GB (64 TB). '
      ),
  )
