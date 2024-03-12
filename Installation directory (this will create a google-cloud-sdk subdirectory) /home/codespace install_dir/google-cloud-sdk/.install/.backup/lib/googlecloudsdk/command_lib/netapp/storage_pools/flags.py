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
"""Flags and helpers for the Cloud NetApp Files Storage Pools commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp import util as netapp_api_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp import util as netapp_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers


STORAGE_POOLS_LIST_FORMAT = """\
    table(
        name.basename():label=STORAGE_POOL_NAME:sort=1,
        name.segment(3):label=LOCATION,
        serviceLevel,
        capacityGib,
        network,
        state,
        volumeCapacityGib
    )"""

## Helper functions to add args / flags for Storage Pools gcloud commands ##


def GetStoragePoolServiceLevelArg(messages, required=True):
  """Adds a --service-level arg to the given parser.

  Args:
    messages: The messages module.
    required: bool, whether choice arg is required or not

  Returns:
    the choice arg.
  """
  custom_mappings = {
      'PREMIUM': (
          'premium',
          """
                          Premium Service Level for Cloud NetApp Storage Pool.
                          The Premium Service Level has a throughput per TiB of
                          allocated volume size of 64 MiB/s.""",
      ),
      'EXTREME': (
          'extreme',
          """
                          Extreme Service Level for Cloud NetApp Storage Pool.
                          The Extreme Service Level has a throughput per TiB of
                          allocated volume size of 128 MiB/s.""",
      ),
      'STANDARD': (
          'standard',
          """
                          Standard Service Level for Cloud NetApp Storage Pool.
                          The Standard Service Level has a throughput per TiB of
                          allocated volume size of 128 MiB/s.""",
      )
  }
  service_level_arg = arg_utils.ChoiceEnumMapper(
      '--service-level',
      messages.StoragePool.ServiceLevelValueValuesEnum,
      help_str="""The service level for the Cloud NetApp Storage Pool.
       For more details, see:
       https://cloud.google.com/netapp/volumes/docs/configure-and-use/storage-pools/overview#service_levels
        """,
      custom_mappings=custom_mappings,
      required=required,
  )
  return service_level_arg


def AddStoragePoolServiceLevelArg(
    parser, messages, required=False
):
  GetStoragePoolServiceLevelArg(
      messages, required=required
  ).choice_arg.AddToParser(parser)


def AddStoragePoolAsyncFlag(parser):
  help_text = """Return immediately, without waiting for the operation
  in progress to complete."""
  concepts.ResourceParameterAttributeConfig(name='async', help_text=help_text)
  base.ASYNC_FLAG.AddToParser(parser)


def AddStoragePoolNetworkArg(parser, required=True):
  """Adds a --network arg to the given parser.

  Args:
    parser: argparse parser.
    required: bool whether arg is required or not
  """

  network_arg_spec = {
      'name': str,
      'psa-range': str,
  }

  network_help = """\
        Network configuration for a Cloud NetApp Files Storage Pool. Specifying
        `psa-range` is optional.
        *name*::: The name of the Google Compute Engine
        [VPC network](/compute/docs/networks-and-firewalls#networks) to which
        the volume is connected. Short-form (VPC network ID) or long-form
        (full VPC network name: projects/PROJECT/locations/LOCATION/networks/NETWORK) are both
        accepted, but please use the long-form when attempting to create a Storage Pool using a shared VPC.
        *psa-range*::: The `psa-range` is the name of the allocated range of the
        Private Service Access connection. The range you specify can't
        overlap with either existing subnets or assigned IP address ranges for
        other Cloud NetApp Files Storage Pools in the selected VPC network.
  """

  parser.add_argument(
      '--network',
      type=arg_parsers.ArgDict(spec=network_arg_spec, required_keys=['name']),
      required=required,
      help=network_help)


def AddStoragePoolActiveDirectoryArg(parser):
  """Adds a --active-directory arg to the given parser."""
  concept_parsers.ConceptParser.ForResource(
      '--active-directory',
      flags.GetActiveDirectoryResourceSpec(),
      'The Active Directory to attach to the Storage Pool.',
      flag_name_overrides={'location': ''}).AddToParser(parser)


def AddStoragePoolKmsConfigArg(parser):
  """Adds a --kms-config arg to the given parser."""
  concept_parsers.ConceptParser.ForResource(
      '--kms-config',
      flags.GetKmsConfigResourceSpec(),
      'The KMS config to attach to the Storage Pool.',
      flag_name_overrides={'location': ''}).AddToParser(parser)


def AddStoragePoolEnableLdapArg(parser):
  """Adds the --enable-ladp arg to the given parser."""
  parser.add_argument(
      '--enable-ldap',
      type=arg_parsers.ArgBoolean(
          truthy_strings=netapp_util.truthy, falsey_strings=netapp_util.falsey),
      help="""Boolean flag indicating whether Storage Pool is a NFS LDAP Storage Pool or not"""
  )

## Helper functions to combine Storage Pools args / flags for gcloud commands ##


def AddStoragePoolCreateArgs(parser, release_track):
  """Add args for creating a Storage Pool."""
  concept_parsers.ConceptParser([
      flags.GetStoragePoolPresentationSpec('The Storage Pool to create.')
  ]).AddToParser(parser)
  flags.AddResourceDescriptionArg(parser, 'Storage Pool')
  flags.AddResourceCapacityArg(parser, 'Storage Pool')
  flags.AddResourceAsyncFlag(parser)
  labels_util.AddCreateLabelsFlags(parser)
  messages = netapp_api_util.GetMessagesModule(release_track=release_track)
  AddStoragePoolServiceLevelArg(
      parser, messages=messages, required=True
  )
  AddStoragePoolNetworkArg(parser)
  AddStoragePoolActiveDirectoryArg(parser)
  AddStoragePoolKmsConfigArg(parser)
  AddStoragePoolEnableLdapArg(parser)


def AddStoragePoolDeleteArgs(parser):
  """Add args for deleting a Storage Pool."""
  concept_parsers.ConceptParser([
      flags.GetStoragePoolPresentationSpec('The Storage Pool to delete.')
  ]).AddToParser(parser)
  flags.AddResourceAsyncFlag(parser)


def AddStoragePoolUpdateArgs(parser):
  """Add args for updating a Storage Pool."""
  concept_parsers.ConceptParser([
      flags.GetStoragePoolPresentationSpec('The Storage Pool to update.')
  ]).AddToParser(parser)
  flags.AddResourceDescriptionArg(parser, 'Storage Pool')
  flags.AddResourceAsyncFlag(parser)
  flags.AddResourceCapacityArg(parser, 'Storage Pool', required=False)
  labels_util.AddUpdateLabelsFlags(parser)
  AddStoragePoolActiveDirectoryArg(parser)
