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
"""Flags definition for gcloud ai persistent-resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import flags as shared_flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai.persistent_resources import persistent_resource_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers

# TODO(b/262780738): Add link to persistent resource spec once spec is
# published to the public.
_PERSISTENT_RESOURCE_CONFIG = base.Argument(
    '--config',
    help=textwrap.dedent("""\
      Path to the Persistent Resource configuration file. This file should be a
      YAML document containing a list of `ResourcePool`
      If an option is specified both in the configuration file **and** via
      command-line arguments, the command-line arguments override the
      configuration file. Note that keys with underscore are invalid.

      Example(YAML):

        resourcePoolSpecs:
          machineSpec:
            machineType: n1-standard-4
          replicaCount: 1"""))

_RESOURCE_POOL_SPEC = base.Argument(
    '--resource-pool-spec',
    action='append',
    type=arg_parsers.ArgDict(
        spec={
            'replica-count': int,
            'min-replica-count': int,
            'max-replica-count': int,
            'machine-type': str,
            'accelerator-type': str,
            'accelerator-count': int,
            'disk-type': str,
            'disk-size': int,
            'local-ssd-count': int,
        }),
    metavar='RESOURCE_POOL_SPEC',
    help=textwrap.dedent("""\
      Defines a resource pool to be created in the Persistent Resource. You can
      include multiple resource pool specs in order to create a Persistent
      Resource with multiple resource pools.

      The spec can contain the following fields:

      *machine-type*::: (Required): The type of the machine.
        see https://cloud.google.com/vertex-ai/docs/training/configure-compute#machine-types
        for supported types. This field corresponds to the `machineSpec.machineType`
        field in `ResourcePool` API message.
      *replica-count*::: (Required if autoscaling not enabled) The number of
        replicas to use when creating this resource pool. This field
        corresponds to the replicaCount field in 'ResourcePool' API message.
      *min-replica-count*::: (Optional) The minimum number of replicas that
        autoscaling will down-size to for this resource pool. Both
        min-replica-count and max-replica-count are required to enable
        autoscaling on this resource pool. The value for this parameter must be
        at least 1.
      *max-replica-count*::: (Optional) The maximum number of replicas that
        autoscaling will create for this resource pool. Both min-replica-count
        and max-replica-count are required to enable autoscaling on this
        resource pool. The maximum value for this parameter is 1000.
      *accelerator-type*::: (Optional) The type of GPU to attach to the
        machines.
        see https://cloud.google.com/vertex-ai/docs/training/configure-compute#specifying_gpus
        for more requirements. This field corresponds to the `machineSpec.acceleratorType`
        field in `ResourcePool` API message.
      *accelerator-count*::: (Required with accelerator-type) The number of GPUs
        for each VM in the resource pool to use. The default the value if 1.
        This field corresponds to the `machineSpec.acceleratorCount` field in
        `ResourcePool` API message.
      *disk-type*::: (Optional) The type of disk to use for each machine's boot disk in
        the resource pool. The default is `pd-standard`. This field corresponds
        to the `diskSpec.bootDiskType` field in `ResourcePool` API message.
      *disk-size*::: (Optional) The disk size in Gb for each machine's boot disk in the
        resource pool. The default is `100`. This field corresponds to
        the `diskSpec.bootDiskSizeGb` field in `ResourcePool` API message.


      ::::
      Example:
      --worker-pool-spec=replica-count=1,machine-type=n1-highmem-2
      """))

ENABLE_CUSTOM_SERVICE_ACCOUNT = base.Argument(
    '--enable-custom-service-account',
    action='store_true',
    required=False,
    help=textwrap.dedent("""\
      Whether or not to use a custom user-managed service account with this
      Persistent Resource.
      """))


def AddCreatePersistentResourceFlags(parser):
  """Adds flags related to create a Persistent Resource."""
  shared_flags.AddRegionResourceArg(
      parser,
      'to create a Persistent Resource',
      prompt_func=region_util.GetPromptForRegionFunc(
          constants.SUPPORTED_TRAINING_REGIONS))
  shared_flags.NETWORK.AddToParser(parser)
  ENABLE_CUSTOM_SERVICE_ACCOUNT.AddToParser(parser)
  # TODO(b/262780738): Unimplemented
  # shared_flags.TRAINING_SERVICE_ACCOUNT.AddToParser(parser)
  shared_flags.AddKmsKeyResourceArg(parser, 'persistent resource')

  labels_util.AddCreateLabelsFlags(parser)

  shared_flags.GetDisplayNameArg('Persistent Resource',
                                 required=False).AddToParser(parser)

  resource_id_flag = base.Argument(
      '--persistent-resource-id',
      required=True,
      default=None,
      help='User-specified ID of the Persistent Resource.')
  resource_id_flag.AddToParser(parser)

  resource_pool_spec_group = base.ArgumentGroup(
      help='resource pool specification.', required=True
  )
  resource_pool_spec_group.AddArgument(_PERSISTENT_RESOURCE_CONFIG)
  resource_pool_spec_group.AddArgument(_RESOURCE_POOL_SPEC)
  resource_pool_spec_group.AddToParser(parser)


def AddPersistentResourceResourceArg(
    parser, verb, regions=constants.SUPPORTED_TRAINING_REGIONS):
  """Add a resource argument for a Vertex AI Persistent Resource.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    regions: list[str], the list of supported regions.
  """
  resource_spec = concepts.ResourceSpec(
      resource_collection=persistent_resource_util.PERSISTENT_RESOURCE_COLLECTION,
      resource_name='persistent resource',
      locationsId=shared_flags.RegionAttributeConfig(
          prompt_func=region_util.GetPromptForRegionFunc(regions)),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)

  concept_parsers.ConceptParser.ForResource(
      'persistent_resource',
      resource_spec,
      'The persistent resource {}.'.format(verb),
      required=True).AddToParser(parser)
