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
"""Command for importing machine images in OVF format into GCE."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import daisy_utils
from googlecloudsdk.api_lib.compute import image_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.images import os_choices
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.compute.machine_images import flags as machine_image_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

_OUTPUT_FILTER = ['[Daisy', '[import-', 'starting build', '  import', 'ERROR']


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Import(base.CreateCommand):
  """Import a machine image into Compute Engine from OVF."""

  @classmethod
  def Args(cls, parser):
    compute_holder = cls._GetComputeApiHolder(no_http=True)
    messages = compute_holder.client.messages

    parser.display_info.AddFormat(machine_image_flags.DEFAULT_LIST_FORMAT)
    Import.MACHINE_IMAGE_ARG = machine_image_flags.MakeMachineImageArg()
    Import.MACHINE_IMAGE_ARG.AddArgument(parser, operation_type='import')
    parser.add_argument(
        '--description',
        help='Specifies a text description of the machine image.')
    flags.AddStorageLocationFlag(parser, "machine image's")
    flags.AddGuestFlushFlag(parser, 'machine image')

    machine_image_flags.AddNoRestartOnFailureArgs(parser)
    machine_image_flags.AddTagsArgs(parser)
    machine_image_flags.AddCanIpForwardArgs(parser)
    machine_image_flags.AddNetworkArgs(parser)
    machine_image_flags.AddNetworkTierArgs(parser)

    instances_flags.AddMachineTypeArgs(parser)
    instances_flags.AddCustomMachineTypeArgs(parser)
    labels_util.AddCreateLabelsFlags(parser)
    daisy_utils.AddCommonDaisyArgs(parser, operation='an import')
    daisy_utils.AddOVFSourceUriArg(parser)

    image_utils.AddGuestOsFeaturesArgForImport(parser, messages)

    parser.add_argument(
        '--os',
        required=False,
        choices=sorted(os_choices.OS_CHOICES_INSTANCE_IMPORT_BETA),
        help='Specifies the OS of the machine image being imported.')
    daisy_utils.AddByolArg(parser)
    flags.AddZoneFlag(
        parser,
        'machine image',
        'import',
        explanation='The zone in which to perform the import of the machine image. '
        + flags.ZONE_PROPERTY_EXPLANATION)
    daisy_utils.AddGuestEnvironmentArg(parser, 'machine image')
    parser.display_info.AddCacheUpdater(completers.InstancesCompleter)
    daisy_utils.AddNoAddressArg(
        parser,
        'machine image import',
        docs_url=(
            'https://cloud.google.com/nat/docs/gce-example#create-nat '
            'and https://cloud.google.com/vpc/docs/private-access-options#pga'))
    daisy_utils.AddComputeServiceAccountArg(
        parser, 'machine image import',
        daisy_utils.IMPORT_ROLES_FOR_COMPUTE_SERVICE_ACCOUNT)
    daisy_utils.AddCloudBuildServiceAccountArg(
        parser,
        'machine image import',
        daisy_utils.IMPORT_ROLES_FOR_CLOUDBUILD_SERVICE_ACCOUNT,
    )
    instances_flags.AddServiceAccountAndScopeArgs(
        parser,
        False,
        extra_scopes_help=(
            'However, if neither `--scopes` nor `--no-scopes` are '
            'specified and the project has no default service '
            'account, then the machine image is imported with no '
            'scopes. Note that the level of access that a service '
            'account has is determined by a combination of access '
            'scopes and IAM roles so you must configure both '
            'access scopes and IAM roles for the service account '
            'to work properly.'),
        operation='Import',
        resource='machine image')

  @classmethod
  def _GetComputeApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def _ValidateArgs(self, args, compute_client):
    instances_flags.ValidateNicFlags(args)
    instances_flags.ValidateNetworkTierArgs(args)
    daisy_utils.ValidateZone(args, compute_client)
    instances_flags.ValidateServiceAccountAndScopeArgs(args)
    try:
      args.source_uri = daisy_utils.MakeGcsUri(args.source_uri)
    except resources.UnknownCollectionException:
      raise exceptions.InvalidArgumentException(
          'source-uri',
          'must be a path to an object or a directory in Cloud Storage')

  def Run(self, args):
    compute_holder = self._GetComputeApiHolder()
    compute_client = compute_holder.client

    self._ValidateArgs(args, compute_client)

    log.warning('Importing OVF. This may take 40 minutes for smaller OVFs '
                'and up to a couple of hours for larger OVFs.')

    return daisy_utils.RunMachineImageOVFImportBuild(
        args=args,
        output_filter=_OUTPUT_FILTER,
        release_track=(self.ReleaseTrack().id.lower()
                       if self.ReleaseTrack() else None),
        messages=compute_client.messages)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ImportBeta(Import):
  """Import a machine image into Compute Engine from OVF for Beta."""

  @classmethod
  def Args(cls, parser):
    super(ImportBeta, cls).Args(parser)
    daisy_utils.AddExtraCommonDaisyArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ImportAlpha(Import):
  """Import a machine image into Compute Engine from OVF for Alpha."""

  @classmethod
  def Args(cls, parser):
    super(ImportAlpha, cls).Args(parser)
    daisy_utils.AddExtraCommonDaisyArgs(parser)

Import.detailed_help = {
    'brief': (
        'Create a Compute Engine machine image from virtual appliance '
        'in OVA/OVF format.'),
    'DESCRIPTION':
        """\
        *{command}* creates Compute Engine machine image from virtual appliance
        in OVA/OVF format.

        Importing OVF involves:
        *  Unpacking OVF package (if in OVA format) to Cloud Storage.
        *  Import disks from OVF to Compute Engine.
        *  Translate the boot disk to make it bootable in Compute Engine.
        *  Create a machine image using OVF metadata and imported disks.

        Virtual instances, images, machine images, and disks in Compute engine
        and files stored on Cloud Storage incur charges. See [](https://cloud.google.com/compute/docs/images/importing-virtual-disks#resource_cleanup).
        """,
    'EXAMPLES':
        """\
        To import an OVF package from Cloud Storage into a machine image named
        `my-machine-image`, run:

          $ {command} my-machine-image --source-uri=gs://my-bucket/my-dir
        """,
}
