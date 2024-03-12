# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for importing instances in OVF format into GCE."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute.images import os_choices
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.compute.sole_tenancy import flags as sole_tenancy_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

_OUTPUT_FILTER = ['[Daisy', '[import-', 'starting build', '  import', 'ERROR']


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Import(base.CreateCommand):
  """Import an instance into Compute Engine from OVF."""

  _OS_CHOICES = os_choices.OS_CHOICES_INSTANCE_IMPORT_GA

  @classmethod
  def Args(cls, parser):
    compute_holder = cls._GetComputeApiHolder(no_http=True)
    messages = compute_holder.client.messages

    instances_flags.AddCanIpForwardArgs(parser)
    instances_flags.AddMachineTypeArgs(parser)
    instances_flags.AddNoRestartOnFailureArgs(parser)
    instances_flags.AddTagsArgs(parser)
    instances_flags.AddCustomMachineTypeArgs(parser)
    instances_flags.AddNetworkArgs(parser)
    instances_flags.AddPrivateNetworkIpArgs(parser)
    instances_flags.AddDeletionProtectionFlag(parser)
    instances_flags.AddNetworkTierArgs(parser, instance=True)
    instances_flags.AddNoAddressArg(parser)
    labels_util.AddCreateLabelsFlags(parser)
    daisy_utils.AddCommonDaisyArgs(parser, operation='an import')
    daisy_utils.AddExtraCommonDaisyArgs(parser)
    instances_flags.INSTANCES_ARG_FOR_IMPORT.AddArgument(
        parser, operation_type='import')
    daisy_utils.AddOVFSourceUriArg(parser)
    parser.add_argument(
        '--os',
        required=False,
        choices=sorted(cls._OS_CHOICES),
        help='Specifies the OS of the image being imported.')
    daisy_utils.AddByolArg(parser)

    image_utils.AddGuestOsFeaturesArgForImport(parser, messages)

    parser.add_argument(
        '--description',
        help='Specifies a textual description of the VM instances.')
    daisy_utils.AddGuestEnvironmentArg(parser)
    parser.display_info.AddCacheUpdater(completers.InstancesCompleter)
    sole_tenancy_flags.AddNodeAffinityFlagToParser(parser)
    parser.add_argument(
        '--hostname',
        help="""\
      Specify the hostname of the VM instance to be imported. The specified
      hostname must be RFC1035 compliant. If hostname is not specified, the
      default hostname is [INSTANCE_NAME].c.[PROJECT_ID].internal when using
      the global DNS, and [INSTANCE_NAME].[ZONE].c.[PROJECT_ID].internal
      when using zonal DNS.
      """)
    daisy_utils.AddComputeServiceAccountArg(
        parser, 'instance import',
        daisy_utils.IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT)
    instances_flags.AddServiceAccountAndScopeArgs(
        parser,
        False,
        extra_scopes_help=(
            'However, if neither `--scopes` nor `--no-scopes` are '
            'specified and the project has no default service '
            'account, then the VM instance is imported with no '
            'scopes. Note that the level of access that a service '
            'account has is determined by a combination of access '
            'scopes and IAM roles so you must configure both '
            'access scopes and IAM roles for the service account '
            'to work properly.'),
        operation='Import')

    daisy_utils.AddCloudBuildServiceAccountArg(
        parser,
        'instance import',
        daisy_utils.IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT,
    )

  @classmethod
  def _GetComputeApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def _ValidateInstanceName(self, args):
    """Raise an exception if requested instance name is invalid."""
    instance_name_pattern = re.compile('^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$')
    if not instance_name_pattern.match(args.instance_name):
      raise exceptions.InvalidArgumentException(
          'INSTANCE_NAME',
          'Name must start with a lowercase letter followed by up to '
          '63 lowercase letters, numbers, or hyphens, and cannot end '
          'with a hyphen.')

  def _CheckForExistingInstances(self, instance_name, client):
    """Check that the destination instances do not already exist."""

    zone = properties.VALUES.compute.zone.GetOrFail()
    request = (client.apitools_client.instances, 'Get',
               client.messages.ComputeInstancesGetRequest(
                   instance=instance_name,
                   project=properties.VALUES.core.project.GetOrFail(),
                   zone=zone))
    errors = []
    instances = client.MakeRequests([request], errors_to_collect=errors)
    if not errors and instances:
      message = ('The VM instance [{instance_name}] already exists in zone '
                 '[{zone}].').format(
                     instance_name=instance_name, zone=zone)
      raise exceptions.InvalidArgumentException('INSTANCE_NAME', message)

  def _ValidateArgs(self, args, compute_client):
    self._ValidateInstanceName(args)
    self._CheckForExistingInstances(args.instance_name, compute_client)

    instances_flags.ValidateNicFlags(args)
    instances_flags.ValidateNetworkTierArgs(args)
    daisy_utils.ValidateZone(args, compute_client)
    instances_flags.ValidateServiceAccountAndScopeArgs(args)

  def Run(self, args):
    compute_holder = self._GetComputeApiHolder()
    compute_client = compute_holder.client
    messages = compute_client.messages

    self._ValidateArgs(args, compute_client)

    log.warning('Importing OVF. This may take 40 minutes for smaller OVFs '
                'and up to a couple of hours for larger OVFs.')

    machine_type = None
    if args.machine_type or args.custom_cpu or args.custom_memory:
      machine_type = instance_utils.InterpretMachineType(
          machine_type=args.machine_type,
          custom_cpu=args.custom_cpu,
          custom_memory=args.custom_memory,
          ext=getattr(args, 'custom_extensions', None),
          vm_type=getattr(args, 'custom_vm_type', None))

    try:
      source_uri = daisy_utils.MakeGcsUri(args.source_uri)
    except resources.UnknownCollectionException:
      raise exceptions.InvalidArgumentException(
          'source-uri',
          'must be a path to an object or a directory in Cloud Storage')

    # The value of the attribute 'guest_os_features' can be can be a list, None,
    # or the attribute may not be present at all.
    # We treat the case when it is None or when it is not present as if the list
    # of features is empty. We need to use the trailing `or ()` rather than
    # give () as a default value to getattr() to handle the case where
    # args.guest_os_features is present, but it is None.
    guest_os_features = getattr(args, 'guest_os_features', None) or ()
    uefi_compatible = (
        messages.GuestOsFeature.TypeValueValuesEnum.UEFI_COMPATIBLE.name
        in guest_os_features)

    return daisy_utils.RunInstanceOVFImportBuild(
        args=args,
        compute_client=compute_client,
        instance_name=args.instance_name,
        source_uri=source_uri,
        no_guest_environment=not args.guest_environment,
        can_ip_forward=args.can_ip_forward,
        deletion_protection=args.deletion_protection,
        description=args.description,
        labels=args.labels,
        machine_type=machine_type,
        network=args.network,
        network_tier=args.network_tier,
        subnet=args.subnet,
        private_network_ip=args.private_network_ip,
        no_restart_on_failure=not args.restart_on_failure,
        os=args.os,
        byol=getattr(args, 'byol', False),
        uefi_compatible=uefi_compatible,
        tags=args.tags,
        zone=properties.VALUES.compute.zone.Get(),
        project=args.project,
        output_filter=_OUTPUT_FILTER,
        release_track=(
            self.ReleaseTrack().id.lower() if self.ReleaseTrack() else None
        ),
        hostname=getattr(args, 'hostname', None),
        no_address=getattr(args, 'no_address', False),
        compute_service_account=getattr(args, 'compute_service_account', ''),
        cloudbuild_service_account=getattr(
            args, 'cloudbuild_service_account', ''
        ),
        scopes=getattr(args, 'scopes', None),
        no_scopes=getattr(args, 'no_scopes', False),
        service_account=getattr(args, 'service_account', None),
        no_service_account=getattr(args, 'no_service_account', False),
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ImportBeta(Import):
  """Import an instance into Compute Engine from OVF."""

  _OS_CHOICES = os_choices.OS_CHOICES_INSTANCE_IMPORT_BETA

  @classmethod
  def Args(cls, parser):
    super(ImportBeta, cls).Args(parser)

  # pylint: disable=useless-super-delegation
  def _ValidateArgs(self, args, compute_client):
    super(ImportBeta, self)._ValidateArgs(args, compute_client)


Import.detailed_help = {
    'brief': (
        'Create Compute Engine virtual machine instances from virtual '
        'appliance in OVA/OVF format.'),
    'DESCRIPTION':
        """\
        *{command}* creates Compute Engine virtual machine instances from
        virtual appliance in OVA/OVF format.

        Importing OVF involves:
        *  Unpacking OVF package (if in OVA format) to Cloud Storage.
        *  Import disks from OVF to Compute Engine.
        *  Translate the boot disk to make it bootable in Compute Engine.
        *  Create a VM instance using OVF metadata and imported disks and boot it.

        OVF import tool requires Cloud Build to be enabled. See [](https://cloud.google.com/compute/docs/import/import-ovf-files#enable-cloud-build)
        Virtual machine instances, images and disks in Compute engine and files
        stored on Cloud Storage incur charges. See [](https://cloud.google.com/compute/docs/images/importing-virtual-disks#resource_cleanup).
        """,
    'EXAMPLES':
        """\
        To import an OVF package from Cloud Storage into a VM named
        `my-instance`, run:

          $ {command} my-instance --source-uri=gs://my-bucket/my-dir
        """,
}
