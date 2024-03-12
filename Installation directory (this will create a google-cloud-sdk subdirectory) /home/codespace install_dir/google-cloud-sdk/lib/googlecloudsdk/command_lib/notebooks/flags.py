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
from googlecloudsdk.command_lib.notebooks import completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def GetEnvironmentResourceArg(
    api_version, help_text, positional=True, required=True
):
  """Constructs and returns the Environment Resource Argument."""

  def GetEnvironmentResourceSpec():
    """Constructs and returns the Resource specification for Environment."""

    def EnvironmentAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='environment', help_text=help_text)

    def LocationAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='{}location'.format('' if positional else 'environment-'),
          help_text=(
              'Google Cloud location of this environment '
              'https://cloud.google.com/compute/docs/regions-zones/#locations.'
          ),
          completer=completers.LocationCompleter,
          fallthroughs=[
              deps.ArgFallthrough('--location'),
              deps.PropertyFallthrough(properties.VALUES.notebooks.location)
          ],
      )

    return concepts.ResourceSpec(
        'notebooks.projects.locations.environments',
        resource_name='environment',
        api_version=api_version,
        environmentsId=EnvironmentAttributeConfig(),
        locationsId=LocationAttributeConfig(),
        projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        disable_auto_completers=False,
    )

  return concept_parsers.ConceptParser.ForResource(
      '{}environment'.format('' if positional else '--'),
      GetEnvironmentResourceSpec(),
      help_text,
      required=required,
  )


def AddListEnvironmentFlags(parser):
  parser.add_argument(
      '--location',
      completer=completers.LocationCompleter,
      help=(
          'Google Cloud location of this environment: '
          'https://cloud.google.com/compute/docs/regions-zones/#locations.'
      ),
  )


def AddCreateEnvironmentFlags(api_version, parser):
  """Construct groups and arguments specific to the environment create."""
  source_group = parser.add_group(mutex=True, required=True)
  vm_source_group = source_group.add_group()
  vm_mutex_group = vm_source_group.add_group(mutex=True, required=True)
  container_group = source_group.add_group()
  GetEnvironmentResourceArg(
      api_version,
      (
          'User-defined unique name of this environment. The environment name'
          ' must be 1 to 63 characters long and contain only lowercase letters,'
          ' numeric characters, and dashes. The first character must be a'
          ' lowercaseletter and the last character cannot be a dash.'
      ),
  ).AddToParser(parser)
  parser.add_argument(
      '--description', help='A brief description of this environment.'
  )
  parser.add_argument('--display-name', help='Name to display on the UI.')
  parser.add_argument(
      '--post-startup-script',
      help=(
          'Path to a Bash script that automatically runs after a notebook'
          ' instance fully boots up. The path must be a URL or Cloud Storage'
          ' path(gs://`path-to-file/`file-name`).'
      ),
  )
  base.ASYNC_FLAG.AddToParser(parser)
  vm_source_group.add_argument(
      '--vm-image-project',
      help=(
          'The ID of the Google Cloud project that this VM image belongs to.'
          'Format: projects/`{project_id}`.'
      ),
      default='deeplearning-platform-release',
  )
  vm_mutex_group.add_argument(
      '--vm-image-family',
      help=(
          'Use this VM image family to find the image; the newest image in '
          'this family will be used.'
      ),
      default='common-cpu',
  )
  vm_mutex_group.add_argument(
      '--vm-image-name', help='Use this VM image name to find the image.'
  )
  container_group.add_argument(
      '--container-repository',
      help=(
          'The path to the container image repository. For example: '
          'gcr.io/`{project_id}`/`{image_name}`.'
      ),
      required=True,
  )
  container_group.add_argument(
      '--container-tag',
      help=(
          'The tag of the container image. If not specified, this defaults to'
          ' the latest tag.'
      ),
  )


def AddDeleteEnvironmentFlags(api_version, parser):
  GetEnvironmentResourceArg(
      api_version,
      (
          'User-defined unique name of this environment. The environment name'
          ' must be 1 to 63 characters long and contain only lowercase letters,'
          ' numeric characters, and dashes. The first character must be a'
          ' lowercaseletter and the last character cannot be a dash.'
      ),
  ).AddToParser(parser)
  base.ASYNC_FLAG.AddToParser(parser)


def AddDescribeEnvironmentFlags(api_version, parser):
  GetEnvironmentResourceArg(
      api_version,
      (
          'User-defined unique name of this environment. The environment name'
          ' must be 1 to 63 characters long and contain only lowercase letters,'
          ' numeric characters, and dashes. The first character must be a'
          ' lowercaseletter and the last character cannot be a dash.'
      ),
  ).AddToParser(parser)


def GetLocationResourceArg(api_version, help_text):
  """Constructs and returns the Location Resource Argument."""

  def GetLocationResourceSpec():
    """Constructs and returns the Location Resource Argument."""
    def LocationAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='location',
          help_text=(
              'Google Cloud location of this runtime '
              'https://cloud.google.com/compute/docs/regions-zones/#locations.'
          ),
          fallthroughs=[
              deps.PropertyFallthrough(properties.VALUES.notebooks.location),
          ],
      )

    return concepts.ResourceSpec(
        'notebooks.projects.locations',
        resource_name='location',
        api_version=api_version,
        projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        locationsId=LocationAttributeConfig())

  return concept_parsers.ConceptParser.ForResource(
      '--location', GetLocationResourceSpec(), help_text, required=True)


def GetRuntimeResourceArg(api_version, help_text):
  """Constructs and returns the Runtime Resource Argument."""

  def GetRuntimeResourceSpec():
    """Constructs and returns the Resource specification for Runtime."""

    def RuntimeAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='runtime', help_text=help_text)

    def LocationAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name='location',
          help_text=(
              'Google Cloud location of this runtime '
              'https://cloud.google.com/compute/docs/regions-zones/#locations.'
          ),
          fallthroughs=[
              deps.PropertyFallthrough(properties.VALUES.notebooks.location),
          ],
      )

    return concepts.ResourceSpec(
        'notebooks.projects.locations.runtimes',
        resource_name='runtime',
        api_version=api_version,
        projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        locationsId=LocationAttributeConfig(),
        runtimesId=RuntimeAttributeConfig(),
        disable_auto_completers=False)

  return concept_parsers.ConceptParser.ForResource(
      'runtime', GetRuntimeResourceSpec(), help_text, required=True)


def GetInstanceResourceArg(api_version, help_text):
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
        api_version=api_version,
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
        disable_auto_completers=False,
    )

  concept_parsers.ConceptParser.ForResource(
      '--subnet', GetSubnetResourceSpec(), help_text
  ).AddToParser(parser)


def AddRuntimeResource(api_version, parser, add_async_flag=True):
  GetRuntimeResourceArg(
      api_version,
      (
          'User-defined unique name of this runtime. The runtime name must be 1'
          ' to 63 characters long and contain only lowercase letters, numeric'
          ' characters, and dashes. The first character must be a lowercase'
          ' letter and the last character cannot be a dash.'
      ),
  ).AddToParser(parser)
  if add_async_flag:
    base.ASYNC_FLAG.AddToParser(parser)


def AddInstanceResource(api_version, parser, add_async_flag=True):
  GetInstanceResourceArg(
      api_version,
      (
          'User-defined unique name of this instance. The instance name must be'
          ' 1 to 63 characters long and contain only lowercase letters, numeric'
          ' characters, and dashes. The first character must be a lowercase'
          ' letter and the last character cannot be a dash.'
      ),
  ).AddToParser(parser)
  if add_async_flag:
    base.ASYNC_FLAG.AddToParser(parser)


def AddDiagnosticConfigFlags(parser, vm_type):
  """Adds Diagnostic config flags to parser."""
  parser.add_argument(
      '--gcs-bucket',
      help=('The Cloud Storage bucket where the log files generated from the '
            'diagnose command will be stored. storage.buckets.writer '
            'permissions must be given to project\'s service account or '
            'user credential. Format: gs://`{gcs_bucket}` '),
      required=True)
  parser.add_argument(
      '--relative-path',
      help=('Defines the relative storage path in the Cloud Storage bucket '
            'where the diagnostic logs will be written. Default path will be '
            'the root directory of the Cloud Storage bucket'
            'Format of full path: gs://`{gcs_bucket}`/`{relative_path}`/ '),
      required=False)
  parser.add_argument(
      '--enable-repair',
      action='store_true',
      dest='enable-repair',
      default=False,
      help=('Enables flag to repair service for {}'.format(vm_type)),
      required=False)
  parser.add_argument(
      '--enable-packet-capture',
      action='store_true',
      dest='enable-packet-capture',
      default=False,
      help=('Enables flag to capture packets from '
            'the {} for 30 seconds'.format(vm_type)),
      required=False)
  parser.add_argument(
      '--enable-copy-home-files',
      action='store_true',
      dest='enable-copy-home-files',
      default=False,
      help=('Enables flag to copy all `/home/jupyter` folder contents'),
      required=False)
  parser.add_argument(
      '--timeout-minutes',
      help=('Maximum amount of time in minutes before the operation times out'),
      required=False)


def AddCreateInstanceFlags(api_version, parser):
  """Construct groups and arguments specific to the instance creation."""
  accelerator_choices = [
      'NVIDIA_TESLA_A100', 'NVIDIA_TESLA_K80', 'NVIDIA_TESLA_P100',
      'NVIDIA_TESLA_V100', 'NVIDIA_TESLA_P4', 'NVIDIA_TESLA_T4',
      'NVIDIA_TESLA_T4_VWS', 'NVIDIA_TESLA_P100_VWS', 'NVIDIA_TESLA_P4_VWS',
      'TPU_V2', 'TPU_V3', 'NVIDIA_L4'
  ]
  disk_choices = ['PD_STANDARD', 'PD_SSD', 'PD_BALANCED', 'PD_EXTREME']
  encryption_choices = ['GMEK', 'CMEK']
  reservation_choices = [
      'TYPE_UNSPECIFIED',
      'NO_RESERVATION',
      'ANY_RESERVATION',
      'SPECIFIC_RESERVATION',
  ]
  AddInstanceResource(api_version, parser)
  environment_group = parser.add_group(mutex=True)
  GetEnvironmentResourceArg(api_version, (
      'User-defined unique name of this environment. The environment name '
      'must be 1 to 63 characters long and contain only lowercase letters, '
      'numeric characters, and dashes. The first character must be a lowercase '
      'letter and the last character cannot be a dash.'),
                            positional=False,
                            required=False).AddToParser(environment_group)
  vm_source_group = environment_group.add_group()
  vm_mutex_group = vm_source_group.add_group(mutex=True)
  container_group = environment_group.add_group()
  vm_source_group.add_argument(
      '--vm-image-project',
      help=('The ID of the Google Cloud project that this VM image belongs to. '
            'Format: projects/`{project_id}`.'),
      default='deeplearning-platform-release')
  vm_mutex_group.add_argument(
      '--vm-image-family',
      help=('Use this VM image family to find the image; the newest image in '
            'this family will be used.'),
      default='common-cpu')
  vm_mutex_group.add_argument(
      '--vm-image-name', help='Use this VM image name to find the image.')
  container_group.add_argument(
      '--container-repository',
      help=('The path to the container image repository. '
            'For example: gcr.io/`{project_id}`/`{image_name}`.'),
      required=True)
  container_group.add_argument(
      '--container-tag',
      help=('The tag of the container image. If not specified, '
            'this defaults to the latest tag.'))
  parser.add_argument(
      '--post-startup-script',
      help=(
          'Path to a Bash script that automatically runs after a notebook '
          'instance fully boots up. The path must be a URL or Cloud Storage '
          'path (gs://`path-to-file`/`file-name`).'))
  parser.add_argument(
      '--service-account',
      help=(
          'The service account on this instance, giving access to other '
          'Google Cloud services. You can use any service account within the '
          'same project, but you must have the service account user permission '
          'to use the instance. If not specified, the [Compute Engine default '
          'service account](/compute/docs/access/service-accounts#default_'
          'service_account) is used.'))
  parser.add_argument(
      '--machine-type',
      help=(
          'The '
          '[Compute Engine machine type](https://cloud.google.com/sdk/gcloud/reference/compute/machine-types) '  # pylint: disable=line-too-long
          'of this instance.'),
      default='n1-standard-1')
  parser.add_argument(
      '--instance-owners',
      help=(
          'The owners of this instance after creation. '
          'Format:`alias@example.com`. Currently supports one owner only.'
          'If not specified, all of the service account users of the VM '
          'instance\'s service account can use the instance.'))
  accelerator_group = parser.add_group(
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
  gpu_group = parser.add_group(help='GPU driver configurations.')
  gpu_group.add_argument(
      '--install-gpu-driver',
      action='store_true',
      dest='install_gpu_driver',
      help=(
          'Whether the end user authorizes Google Cloud to install a GPU '
          'driver on this instance. If this field is empty or set to false, '
          'the GPU driver won\'t be installed. Only applicable to instances '
          'with GPUs.'
      ))
  gpu_group.add_argument(
      '--custom-gpu-driver-path',
      help=(
          'Specify a custom Cloud Storage path where the GPU driver is '
          'stored. If not specified, we\'ll automatically choose from official '
          'GPU drivers.'))
  boot_group = parser.add_group(help='Boot disk configurations.')
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
  data_group = parser.add_group(help='Data disk configurations.')
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
      '--no-remove-data-disk',
      action='store_true',
      dest='no_remove_data_disk',
      help=(
          'If true, the data disk will not be auto deleted when deleting '
          'the instance.'
      ),
  )
  encryption_group = parser.add_group(help='Disk encryption configurations.')
  encryption_group.add_argument(
      '--disk-encryption',
      choices=encryption_choices,
      default=None,
      help='Disk encryption method used on the boot disk, defaults to GMEK.')
  kms_resource_args.AddKmsKeyResourceArg(encryption_group, 'instance')
  network_group = parser.add_group(help='Network configs.')
  network_group.add_argument(
      '--no-public-ip',
      action='store_true',
      dest='no_public_ip',
      help="""\
  If specified, no public IP will be assigned to this instance.""")
  network_group.add_argument(
      '--no-proxy-access',
      action='store_true',
      dest='no_proxy_access',
      help="""\
  If true, the notebook instance will not register with the proxy.""")

  AddNetworkArgument(
      ('The name of the VPC that this instance is in. Format: '
       'projects/`{project_id}`/global/networks/`{network_id}`.'),
      network_group)
  AddSubnetArgument(
      ('The name of the subnet that this instance is in. Format: projects/'
       '`{project_id}`/regions/`{region}`/subnetworks/`{subnetwork_id}`.'),
      network_group)
  parser.add_argument(
      '--labels',
      help=('Labels to apply to this instance. These can be later modified '
            'by the setLabels method.'),
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE')
  parser.add_argument(
      '--metadata',
      help=("""\
Custom metadata to apply to this instance.

For example, to specify a Cloud Storage bucket for automatic backup,
you can use the `gcs-data-bucket` metadata tag. Format:
`"--metadata=gcs-data-bucket=``BUCKET''"`.
"""),
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE')
  parser.add_argument(
      '--shielded-secure-boot',
      help=('Boot instance with secure boot enabled. '
            'Disabled by default.'),
      dest='shielded_vm_secure_boot',
      action='store_true',
      default=False,
  )
  parser.add_argument(
      '--shielded-vtpm',
      help=('Boot instance with TPM (Trusted Platform Module) enabled.'),
      dest='shielded_vm_vtpm',
      action='store_true',
      default=True,
  )
  parser.add_argument(
      '--shielded-integrity-monitoring',
      help=('Enable monitoring of the boot integrity of the instance.'),
      dest='shielded_vm_integrity_monitoring',
      action='store_true',
      default=True,
  )
  reservation_group = parser.add_group(
      help='Specifies the reservation for the instance.')
  reservation_group.add_argument(
      '--reservation-affinity',
      choices=reservation_choices,
      default='TYPE_UNSPECIFIED',
      help='The type of reservation for the instance.',
  )
  reservation_group.add_argument(
      '--reservation',
      help=('The name of the reservation, required when '
            '`--reservation-affinity=SPECIFIC_RESERVATION`.'))
  parser.add_argument(
      '--tags',
      metavar='TAGS',
      help=('Tags to apply to this instance.'),
      type=arg_parsers.ArgList())


def AddDescribeInstanceFlags(api_version, parser):
  AddInstanceResource(api_version, parser, add_async_flag=False)


def AddDeleteInstanceFlags(api_version, parser):
  AddInstanceResource(api_version, parser)


def AddListInstanceFlags(parser):
  parser.add_argument(
      '--location',
      completer=completers.LocationCompleter,
      help=('Google Cloud location of this environment '
            'https://cloud.google.com/compute/docs/regions-zones/#locations.'))


def AddRegisterInstanceFlags(api_version, parser):
  AddInstanceResource(api_version, parser)


def AddResetInstanceFlags(api_version, parser):
  AddInstanceResource(api_version, parser)


def AddStartInstanceFlags(api_version, parser):
  AddInstanceResource(api_version, parser)


def AddStopInstanceFlags(api_version, parser):
  AddInstanceResource(api_version, parser)


def AddGetHealthInstanceFlags(api_version, parser):
  AddInstanceResource(api_version, parser, add_async_flag=False)


def AddIsUpgradeableInstanceFlags(api_version, parser):
  AddInstanceResource(api_version, parser, add_async_flag=False)


def AddUpgradeInstanceFlags(api_version, parser):
  AddInstanceResource(api_version, parser)


def AddRollbackInstanceFlags(api_version, parser):
  AddInstanceResource(api_version, parser)
  parser.add_argument(
      '--target-snapshot',
      help='The saved snapshot to rollback to',
      required=True)


def AddUpdateInstanceFlags(api_version, parser):
  """Adds accelerator, labels and machine type flags to the parser for update."""
  accelerator_choices = [
      'NVIDIA_TESLA_A100', 'NVIDIA_TESLA_K80', 'NVIDIA_TESLA_P100',
      'NVIDIA_TESLA_V100', 'NVIDIA_TESLA_P4', 'NVIDIA_TESLA_T4',
      'NVIDIA_TESLA_T4_VWS', 'NVIDIA_TESLA_P100_VWS', 'NVIDIA_TESLA_P4_VWS',
      'TPU_V2', 'TPU_V3', 'NVIDIA_L4'
  ]
  AddInstanceResource(api_version, parser)
  update_group = parser.add_group(required=True)
  update_group.add_argument(
      '--accelerator-type',
      help='Type of this accelerator.',
      choices=accelerator_choices,
      default=None)
  update_group.add_argument(
      '--accelerator-core-count',
      help='Count of cores of this accelerator.',
      type=int)
  update_group.add_argument(
      '--labels',
      help=('Labels to apply to this instance. '
            'These can be later modified by the setLabels method.'),
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE')
  update_group.add_argument(
      '--machine-type',
      help='The [Compute Engine machine type](/compute/docs/machine-types).')


def AddDiagnoseInstanceFlags(api_version, parser):
  """Construct groups and arguments specific to the instance diagnosing."""
  AddInstanceResource(api_version, parser)
  AddDiagnosticConfigFlags(parser, 'instance')


def AddMigrateInstanceFlags(api_version, parser):
  """Construct groups and arguments specific to the instance migration."""
  post_startup_script_option_choices = [
      'POST_STARTUP_SCRIPT_OPTION_UNSPECIFIED',
      'POST_STARTUP_SCRIPT_OPTION_SKIP',
      'POST_STARTUP_SCRIPT_OPTION_RERUN',
      ]
  AddInstanceResource(api_version, parser)
  parser.add_argument(
      '--post-startup-script-option',
      help='// Specifies the behavior of post startup script during migration.',
      choices=post_startup_script_option_choices,
      default='POST_STARTUP_SCRIPT_OPTION_UNSPECIFIED')


def AddDeleteRuntimeFlags(api_version, parser):
  AddRuntimeResource(api_version, parser)


def AddDescribeRuntimeFlags(api_version, parser):
  AddRuntimeResource(api_version, parser, add_async_flag=False)


def AddStartRuntimeFlags(api_version, parser):
  AddRuntimeResource(api_version, parser)


def AddStopRuntimeFlags(api_version, parser):
  AddRuntimeResource(api_version, parser)


def AddSwitchRuntimeFlags(api_version, parser):
  """Adds accelerator and machine type flags to the parser for switch."""
  accelerator_choices = [
      'NVIDIA_TESLA_A100', 'NVIDIA_TESLA_K80', 'NVIDIA_TESLA_P100',
      'NVIDIA_TESLA_V100', 'NVIDIA_TESLA_P4', 'NVIDIA_TESLA_T4',
      'NVIDIA_TESLA_T4_VWS', 'NVIDIA_TESLA_P100_VWS', 'NVIDIA_TESLA_P4_VWS',
      'TPU_V2', 'TPU_V3'
  ]
  AddRuntimeResource(api_version, parser)
  parser.add_argument('--machine-type', help=('machine type'))
  accelerator_config_group = parser.add_group()
  accelerator_config_group.add_argument(
      '--accelerator-type',
      help='Type of this accelerator.',
      choices=accelerator_choices,
      default=None)
  accelerator_config_group.add_argument(
      '--accelerator-core-count',
      help='Count of cores of this accelerator.',
      type=int)


def AddResetRuntimeFlags(api_version, parser):
  AddRuntimeResource(api_version, parser)


def AddCreateRuntimeFlags(api_version, parser):
  """Construct groups and arguments specific to the runtime creation."""

  AddRuntimeResource(api_version, parser)
  runtime_type_group = parser.add_group(mutex=True, required=True)
  runtime_type_group.add_argument('--runtime-type', help='runtime type')
  machine_type_group = runtime_type_group.add_group()
  machine_type_group.add_argument(
      '--machine-type', help='machine type', required=True
  )
  local_disk_group = machine_type_group.add_group()
  local_disk_group.add_argument('--interface', help='runtime interface')
  local_disk_group.add_argument('--source', help='runtime source')
  local_disk_group.add_argument('--mode', help='runtime mode')
  local_disk_group.add_argument('--type', help='runtime type')

  access_config_group = parser.add_group(required=True)
  access_config_group.add_argument('--runtime-access-type', help='access type')
  access_config_group.add_argument('--runtime-owner', help='runtime owner')

  software_config_group = parser.add_group()
  software_config_group.add_argument(
      '--idle-shutdown-timeout', help='idle shutdown timeout'
  )
  software_config_group.add_argument(
      '--install-gpu-driver', help='install gpu driver'
  )
  software_config_group.add_argument(
      '--custom-gpu-driver-path', help='custom gpu driver path'
  )
  software_config_group.add_argument(
      '--post-startup-script', help='post startup script'
  )
  software_config_group.add_argument(
      '--post-startup-script-behavior', help='post startup script behavior'
  )


def AddListRuntimeFlags(api_version, parser):
  GetLocationResourceArg(
      api_version, 'Location of this runtime. For example, us-central1-a'
  ).AddToParser(parser)


def AddDiagnoseRuntimeFlags(api_version, parser):
  """Construct groups and arguments specific to the runtime diagnosing."""
  AddRuntimeResource(api_version, parser)
  AddDiagnosticConfigFlags(parser, 'runtime')


def AddMigrateRuntimeFlags(api_version, parser):
  """Construct groups and arguments specific to the runtime migration."""
  post_startup_script_option_choices = [
      'POST_STARTUP_SCRIPT_OPTION_UNSPECIFIED',
      'POST_STARTUP_SCRIPT_OPTION_SKIP',
      'POST_STARTUP_SCRIPT_OPTION_RERUN',
      ]
  AddRuntimeResource(api_version, parser)
  network_group = parser.add_group(help='Network configs.')
  AddNetworkArgument(
      ('The name of the VPC that this instance is in. Format: '
       'projects/`{project_id}`/global/networks/`{network_id}`.'),
      network_group)
  AddSubnetArgument(
      ('The name of the subnet that this instance is in. Format: projects/'
       '`{project_id}`/regions/`{region}`/subnetworks/`{subnetwork_id}`.'),
      network_group)
  parser.add_argument(
      '--service-account',
      help=(
          'The service account to be included in the Compute Engine instance '
          'of the new Workbench Instance when the Runtime uses single user '
          'only mode for permission. If not specified, the [Compute Engine '
          'default service account](https://cloud.google.com/compute/docs/'
          'access/service-accounts#default_service_account) is used. When the '
          'Runtime uses service account mode for permission, it will reuse the '
          'same service account, and this field must be empty.'
          ))
  parser.add_argument(
      '--post-startup-script-option',
      help='Specifies the behavior of post startup script during migration.',
      choices=post_startup_script_option_choices,
      default='POST_STARTUP_SCRIPT_OPTION_UNSPECIFIED')
