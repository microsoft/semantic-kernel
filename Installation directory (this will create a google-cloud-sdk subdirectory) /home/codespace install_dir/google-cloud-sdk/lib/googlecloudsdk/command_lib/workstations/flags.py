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
"""Flags for Workstation Config related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def AddAsyncFlag(parser):
  """Adds --async flag."""
  base.ASYNC_FLAG.AddToParser(parser)


def LocationsAttributeConfig(
    location_fallthrough=False, global_fallthrough=False
):
  """Create a location attribute in resource argument.

  Args:
    location_fallthrough: If set, enables fallthroughs for the location
      attribute.
    global_fallthrough: If set, enables global fallthroughs for the location
      attribute.

  Returns:
    Location resource argument parameter config
  """
  fallthroughs = []
  if location_fallthrough:
    fallthroughs.append(
        deps.PropertyFallthrough(properties.VALUES.workstations.region)
    )
  if global_fallthrough:
    fallthroughs.append(
        deps.Fallthrough(
            lambda: '-', hint='default is all regions'
        )
    )
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      fallthroughs=fallthroughs,
      help_text='The region for the {resource}.',
  )


def ClustersAttributeConfig(
    cluster_fallthrough=False, global_fallthrough=False
):
  """Create a cluster attribute in resource argument.

  Args:
    cluster_fallthrough: If set, enables fallthroughs for the cluster attribute.
    global_fallthrough: If set, enables global fallthroughs for the cluster
      attribute.

  Returns:
    Cluster resource argument parameter config
  """
  fallthroughs = []
  if cluster_fallthrough:
    fallthroughs.append(
        deps.PropertyFallthrough(properties.VALUES.workstations.cluster)
    )
  if global_fallthrough:
    fallthroughs.append(
        deps.Fallthrough(
            lambda: '-',
            hint='default is all clusters',
        )
    )
  return concepts.ResourceParameterAttributeConfig(
      name='cluster',
      fallthroughs=fallthroughs,
      help_text='The cluster for the {resource}.',
  )


def ConfigsAttributeConfig(config_fallthrough=False, global_fallthrough=False):
  """Create a config attribute in resource argument.

  Args:
    config_fallthrough: If set, enables fallthroughs for the config attribute
      using the value set in workstations/config.
    global_fallthrough: If set, enables global fallthroughs for the config
      attribute.

  Returns:
    Config resource argument parameter config
  """
  fallthroughs = []
  if config_fallthrough:
    fallthroughs.append(
        deps.PropertyFallthrough(properties.VALUES.workstations.config)
    )
  if global_fallthrough:
    fallthroughs.append(
        deps.Fallthrough(
            lambda: '-',
            hint='default is all configs',
        )
    )
  return concepts.ResourceParameterAttributeConfig(
      name='config',
      fallthroughs=fallthroughs,
      help_text='The config for the {resource}.',
  )


def WorkstationsAttributeConfig():
  """Create a workstation attribute in resource argument.

  Returns:
    Workstation resource argument parameter config
  """
  return concepts.ResourceParameterAttributeConfig(
      name='workstation',
      help_text='The workstation.',
  )


def AddConfigResourceArg(
    parser, api_version='v1beta', flag_anchor=False, global_fallthrough=False
):
  """Create a config resource argument."""
  spec = concepts.ResourceSpec(
      'workstations.projects.locations.workstationClusters.workstationConfigs',
      resource_name='config',
      api_version=api_version,
      workstationConfigsId=ConfigsAttributeConfig(
          global_fallthrough=global_fallthrough
      ),
      workstationClustersId=ClustersAttributeConfig(
          cluster_fallthrough=True, global_fallthrough=global_fallthrough
      ),
      locationsId=LocationsAttributeConfig(
          location_fallthrough=True, global_fallthrough=global_fallthrough
      ),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )
  concept_parsers.ConceptParser.ForResource(
      '--config' if flag_anchor else 'config',
      spec,
      'The group of arguments defining a config',
      required=True,
  ).AddToParser(parser)


def AddWorkstationResourceArg(parser, api_version='v1beta'):
  """Create a workstation resource argument."""
  spec = concepts.ResourceSpec(
      'workstations.projects.locations.workstationClusters.workstationConfigs.workstations',
      resource_name='workstation',
      api_version=api_version,
      workstationsId=WorkstationsAttributeConfig(),
      workstationConfigsId=ConfigsAttributeConfig(config_fallthrough=True),
      workstationClustersId=ClustersAttributeConfig(cluster_fallthrough=True),
      locationsId=LocationsAttributeConfig(location_fallthrough=True),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )
  concept_parsers.ConceptParser.ForResource(
      'workstation',
      spec,
      'The group of arguments defining a workstation',
      required=True,
  ).AddToParser(parser)


def AddIdleTimeoutFlag(parser, use_default=True):
  """Adds an --idle-timeout flag to the given parser."""
  help_text = """\
  How long (in seconds) to wait before automatically stopping an instance that
  hasn't received any user traffic. A value of 0 indicates that this instance
  should never time out due to idleness.
  """
  parser.add_argument(
      '--idle-timeout',
      default=7200 if use_default else None,
      type=int,
      help=help_text,
  )


def AddRunningTimeoutFlag(parser, use_default=True):
  """Adds an --running-timeout flag to the given parser."""
  help_text = """\
  How long (in seconds) to wait before automatically stopping a workstation
  after it started. A value of 0 indicates that workstations using this config
  should never time out.
  """
  parser.add_argument(
      '--running-timeout',
      default=7200 if use_default else None,
      type=int,
      help=help_text,
  )


def AddMachineTypeFlag(parser, use_default=True):
  """Adds a --machine-type flag to the given parser."""
  help_text = """\
  Machine type determines the specifications of the Compute Engine machines
  that the workstations created under this configuration will run on."""
  parser.add_argument(
      '--machine-type',
      type=str,
      default='e2-standard-4' if use_default else None,
      help=help_text,
  )


def AddServiceAccountFlag(parser):
  """Adds a --service-account flag to the given parser."""
  help_text = """\
  Email address of the service account that will be used on VM instances used to
  support this config. This service account must have permission to pull the
  specified container image. If not set, VMs will run without a service account,
  in which case the image must be publicly accessible."""
  parser.add_argument('--service-account', help=help_text)


def AddServiceAccountScopes(parser):
  """Adds a --service-account-scopes flag to the given parser."""
  help_text = """\
  Scopes to grant to the service_account. Various scopes are
  automatically added based on feature usage. When specified, users of
  workstations under this configuration must have
  iam.serviceAccounts.actAs` on the service account.
  """
  parser.add_argument(
      '--service-account-scopes',
      metavar='SERVICE_ACCOUNT_SCOPES',
      type=arg_parsers.ArgList(),
      help=help_text)


def AddNetworkTags(parser):
  """Adds a --network-tags flag to the given parser."""
  help_text = """\
  Network tags to add to the Google Compute Engine machines backing the
  Workstations.

  Example:

    $ {command} --network-tags=tag_1,tag_2
  """
  parser.add_argument(
      '--network-tags',
      metavar='NETWORK_TAGS',
      type=arg_parsers.ArgList(),
      help=help_text)


def AddPoolSize(parser, use_default=True):
  """Adds a --pool-size flag to the given parser."""
  help_text = """\
  Number of instances to pool for faster Workstation starup."""
  parser.add_argument(
      '--pool-size',
      default=0 if use_default else None,
      type=int,
      help=help_text,
  )


def AddDisablePublicIpAddresses(parser, use_default=True):
  """Adds a --disable-public-ip-addresses flag to the given parser."""
  help_text = """\
  Default value is false.
  If set, instances will have no public IP address."""
  parser.add_argument(
      '--disable-public-ip-addresses',
      action='store_true',
      default=False if use_default else None,
      help=help_text,
  )


def AddDisableTcpConnections(parser, use_default=True):
  """Adds a --disable-tcp-connections flag to the given parser."""
  help_text = """\
  Default value is false.
  If set, workstations don't allow plain TCP connections."""
  parser.add_argument(
      '--disable-tcp-connections',
      action='store_true',
      default=False if use_default else None,
      help=help_text,
  )


def AddEnableTcpConnections(parser):
  """Adds a --enable-tcp-connections flag to the given parser."""
  help_text = """\
  If set, workstations allow plain TCP connections."""

  group = parser.add_mutually_exclusive_group()
  group.add_argument(
      '--enable-tcp-connections',
      action='store_true',
      help=help_text,
  )

  help_text = """\
  If set, workstations don't allow plain TCP connections."""
  group.add_argument(
      '--disable-tcp-connections',
      action='store_true',
      help=help_text,
  )


def AddShieldedSecureBoot(parser, use_default=True):
  """Adds --shielded-secure-boot flag to the given parser."""
  help_text = """\
  Default value is false.
  If set, instances will have Secure Boot enabled."""
  parser.add_argument(
      '--shielded-secure-boot',
      action='store_true',
      default=False if use_default else None,
      help=help_text,
  )


def AddShieldedVtpm(parser, use_default=True):
  """Adds a --shielded-vtpm flag to the given parser."""
  help_text = """\
  Default value is false.
  If set, instances will have vTPM enabled."""
  parser.add_argument(
      '--shielded-vtpm',
      action='store_true',
      default=False if use_default else None,
      help=help_text,
  )


def AddShieldedIntegrityMonitoring(parser, use_default=True):
  """Adds a --shielded-integrity-monitoring flag to the given parser."""
  help_text = """\
  Default value is false.
  If set, instances will have integrity monitoring enabled."""
  parser.add_argument(
      '--shielded-integrity-monitoring',
      action='store_true',
      default=False if use_default else None,
      help=help_text,
  )


def AddEnableAuditAgent(parser, use_default=True):
  """Adds an --enable-audit-agent flag to the given parser."""
  help_text = """\
  Whether to enable Linux `auditd` logging on the workstation. When enabled,
  a service account must also be specified that has `logging.buckets.write`
  permission on the project."""
  parser.add_argument(
      '--enable-audit-agent',
      action='store_true',
      default=False if use_default else None,
      help=help_text,
  )


def AddEnableConfidentialCompute(parser, use_default=True):
  """Adds an --enable-confidential-compute flag to the given parser."""
  help_text = """\
  Default value is false.
  If set, instances will have confidential compute enabled."""
  parser.add_argument(
      '--enable-confidential-compute',
      action='store_true',
      default=False if use_default else None,
      help=help_text,
  )


def AddEnableNestedVirtualization(parser, use_default=True):
  """Adds an --enable-nested-virtualization flag to the given parser."""
  help_text = """\
  Default value is false.
  If set, instances will have nested virtualization enabled."""
  parser.add_argument(
      '--enable-nested-virtualization',
      action='store_true',
      default=False if use_default else None,
      help=help_text,
  )


def AddBootDiskSize(parser, use_default=True):
  """Adds a --boot-disk-size flag to the given parser."""
  help_text = """\
  Size of the boot disk in GB."""
  parser.add_argument(
      '--boot-disk-size',
      default=50 if use_default else None,
      type=int,
      help=help_text,
  )


def AddPdDiskType(parser):
  """Adds a --pd-disk-type flag to the given parser."""
  help_text = """\
  Type of the persistent directory."""
  parser.add_argument(
      '--pd-disk-type',
      choices=['pd-standard', 'pd-balanced', 'pd-ssd'],
      default='pd-standard',
      help=help_text)


def AddPdDiskSize(parser):
  """Adds a --pd-disk-size flag to the given parser."""
  help_text = """\
  Size of the persistent directory in GB."""
  parser.add_argument(
      '--pd-disk-size',
      choices=[10, 50, 100, 200, 500, 1000],
      default=200,
      type=int,
      help=help_text)


def AddPdReclaimPolicy(parser):
  """Adds a --pd-reclaim-policy flag to the given parser."""
  help_text = """\
  What should happen to the disk after the Workstation is deleted."""
  parser.add_argument(
      '--pd-reclaim-policy',
      choices={
          'delete':
              'The persistent disk will be deleted with the Workstation.',
          'retain':
              'The persistent disk will be remain after the workstation is deleted and the administrator must manually delete the disk.'
      },
      default='delete',
      help=help_text)


def AddEphemeralDirectory(parser):
  spec = {
      'mount-path': str,
      'disk-type': str,
      'source-snapshot': str,
      'source-image': str,
      'read-only': bool
  }
  help_text = """\
  Ephemeral directory which won't persist across workstation sessions."""
  parser.add_argument(
      '--ephemeral-directory',
      type=arg_parsers.ArgDict(spec=spec),
      action='append',
      metavar='PROPERTY=VALUE',
      help=help_text
  )


def AddContainerImageField(parser, use_default=True):
  """Adds the --container-predefined-image and --container-custom-image flags to the given parser.
  """
  predefined_image_help_text = """\
  Code editor on base images."""
  custom_image_help_text = """\
  A docker image for the workstation. This image must be accessible by the
  service account configured in this configuration (--service-account). If no
  service account is defined, this image must be public.
  """
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
      '--container-predefined-image',
      choices={
          'codeoss': 'Code OSS',
          'intellij': 'IntelliJ IDEA Ultimate',
          'pycharm': 'PyCharm Professional',
          'rider': 'Rider',
          'webstorm': 'WebStorm',
          'phpstorm': 'PhpStorm',
          'rubymine': 'RubyMine',
          'goland': 'GoLand',
          'clion': 'CLion',
          'base-image': 'Base image - no IDE',
      },
      default='codeoss' if use_default else None,
      help=predefined_image_help_text,
  )

  group.add_argument(
      '--container-custom-image', type=str, help=custom_image_help_text)


def AddContainerCommandField(parser):
  """Adds a --container-command flag to the given parser."""
  help_text = """\
  If set, overrides the default ENTRYPOINT specified by the image.

  Example:

    $ {command} --container-command=executable,parameter_1,parameter_2"""
  parser.add_argument(
      '--container-command',
      metavar='CONTAINER_COMMAND',
      type=arg_parsers.ArgList(),
      help=help_text)


def AddContainerArgsField(parser):
  """Adds a --container-args flag to the given parser."""
  help_text = """\
  Arguments passed to the entrypoint.

  Example:

    $ {command} --container-args=arg_1,arg_2"""
  parser.add_argument(
      '--container-args',
      metavar='CONTAINER_ARGS',
      type=arg_parsers.ArgList(),
      help=help_text)


def AddContainerEnvField(parser):
  """Adds a --container-env flag to the given parser."""
  help_text = """\
  Environment variables passed to the container.

  Example:

    $ {command} --container-env=key1=value1,key2=value2"""
  parser.add_argument(
      '--container-env',
      metavar='CONTAINER_ENV',
      type=arg_parsers.ArgDict(key_type=str, value_type=str),
      help=help_text)


def AddContainerWorkingDirField(parser):
  """Adds a --container-working-dir flag to the given parser."""
  help_text = """\
  If set, overrides the default DIR specified by the image."""
  parser.add_argument('--container-working-dir', help=help_text)


def AddContainerRunAsUserField(parser):
  """Adds a --container-run-as-user flag to the given parser."""
  help_text = """\
  If set, overrides the USER specified in the image with the given
  uid."""
  parser.add_argument('--container-run-as-user', type=int, help=help_text)


def AddWorkstationPortField(parser):
  """Adds a workstation-port flag to the given parser."""
  help_text = """\
  The port on the workstation to which traffic should be sent."""
  parser.add_argument('workstation_port', type=int, help=help_text)


def AddPortField(parser):
  """Adds a --port flag to the given parser."""
  help_text = """\
  The port on the workstation to which traffic should be sent."""
  parser.add_argument('--port', type=int, default=22, help=help_text)


def AddLocalHostPortField(parser):
  """Adds a --local-host-port flag to the given parser."""
  help_text = """\
  `LOCAL_HOST:LOCAL_PORT` on which gcloud should bind and listen for connections
  that should be tunneled.

  `LOCAL_PORT` may be omitted, in which case it is treated as 0 and an arbitrary
  unused local port is chosen. The colon also may be omitted in that case.

  If `LOCAL_PORT` is 0, an arbitrary unused local port is chosen."""
  parser.add_argument(
      '--local-host-port',
      type=arg_parsers.HostPort.Parse,
      default='localhost:0',
      help=help_text)


def AddCommandField(parser):
  """Adds a --command flag to the given parser."""
  help_text = """\
      A command to run on the workstation.

      Runs the command on the target workstation and then exits.
      """
  parser.add_argument('--command', type=str, help=help_text)


def AddSshArgsAndUserField(parser):
  """Adds a --user flag to the given parser."""
  help_text = """\
  The username with which to SSH.
  """
  parser.add_argument('--user', type=str, default='user', help=help_text)

  help_text = """\
  Flags and positionals passed to the underlying ssh implementation."""
  parser.add_argument('ssh_args', nargs=argparse.REMAINDER, help=help_text)


def AddEncryptionKeyFields(parser):
  """Adds the --kms-key and --kms-key-service-account flags to the given parser."""
  group = parser.add_group(help='Encryption key settings')

  help_text = """\
  The customer-managed encryption key to use for this config. If not specified,
  a Google-managed encryption key is used.
  """
  group.add_argument('--kms-key', type=str, help=help_text, required=True)

  help_text = """\
  The service account associated with the provided customer-managed encryption
  key.
  """
  group.add_argument('--kms-key-service-account', type=str, help=help_text)


def AddLabelsField(parser):
  """Adds a --labels flag to the given parser."""
  help_text = """\
  Labels that are applied to the configuration and propagated to the underlying
  Compute Engine resources.

  Example:

    $ {command} --labels=label1=value1,label2=value2"""
  parser.add_argument(
      '--labels',
      metavar='LABELS',
      type=arg_parsers.ArgDict(key_type=str, value_type=str),
      help=help_text,
  )


def AddAcceleratorFields(parser):
  """Adds the --accelerator-type and --accelerator-count flags to the given parser."""
  group = parser.add_group(help='Accelerator settings')

  help_text = """\
  The type of accelerator resource to attach to the instance, for example,
  "nvidia-tesla-p100".
  """
  group.add_argument(
      '--accelerator-type', type=str, help=help_text
  )

  help_text = """\
  The number of accelerator cards exposed to the instance.
  """
  group.add_argument(
      '--accelerator-count', type=int, help=help_text, required=True
  )


def AddReplicaZones(parser):
  """Adds a --replica-zones flag to the given parser."""
  help_text = """\
  Specifies the zones the VM and disk resources will be
  replicated within the region. If set, exactly two zones within the
  workstation cluster's region must be specified.

  Example:

    $ {command} --replica-zones=us-central1-a,us-central1-f
  """
  parser.add_argument(
      '--replica-zones',
      metavar='REPLICA_ZONES',
      type=arg_parsers.ArgList(),
      help=help_text)


def AddDisableSSHToVM(parser, use_default=True):
  """Adds a --disable-ssh-to-vm flag to the given parser."""
  help_text = """\
  Default value is False.
  If set, workstations disable SSH connections to the root VM."""
  parser.add_argument(
      '--disable-ssh-to-vm',
      action='store_true',
      default=False if use_default else False,
      help=help_text,
  )


def AddEnableSSHToVM(parser):
  """Adds a --enable-ssh-to-vm flag to the given parser."""
  help_text = """\
  If set, workstations disable SSH connections to the root VM."""
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
      '--disable-ssh-to-vm',
      action='store_true',
      help=help_text,
  )
  help_text = """\
  If set, workstations enable SSH connections to the root VM."""
  group.add_argument(
      '--enable-ssh-to-vm',
      action='store_true',
      help=help_text,
  )
