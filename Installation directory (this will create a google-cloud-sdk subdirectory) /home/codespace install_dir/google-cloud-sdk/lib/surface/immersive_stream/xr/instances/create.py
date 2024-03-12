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
"""Command to create an Immersive Stream for XR service instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.immersive_stream.xr import api_util
from googlecloudsdk.api_lib.immersive_stream.xr import instances
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.immersive_stream.xr import flags
from googlecloudsdk.command_lib.immersive_stream.xr import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create an Immersive Stream for XR service instance."""

  detailed_help = {
      'DESCRIPTION': 'Create an Immersive Stream for XR service instance.',
      'EXAMPLES': """
          To create a service instance called `my-instance` serving content
          `my-content` with version `my-version` that has availablilty for 2
          concurent sessions in us-west1 region and 3 concurrent sessions in
          us-east4 region, run:

            $ {command} my-instance --content=my-content --version=my-version --add-region=region=us-west1,capacity=2 --add-region=region=us-east4,capacity=3

          Optionally, a fallback url may be specified. Users will be redirected
          to this fallback url when the service instance is unable to provide
          the streaming experience.
          To create a service instance called `my-instance` serving content
          `my-content` with version `my-version` that has availablilty for 2
          concurent sessions in us-west1 and uses fallback url
          `https://www.google.com` run:

            $ {command} my-instance --content=my-content --version=my-version --add-region=region=us-west1,capacity=2 --fallback-url="https://www.google.com"

           By default, the instance is created with mode=ar, which supports both
           3D and AR experiences. Instances can also be configured to use
           3D-only mode. This configuration cannot be updated later.
           To use 3D-only mode, include:

            --mode=3d

           By default, the instance is created with gpu-class=t4. This uses the
           NVIDIA T4 GPU for the instance. Instances can also be configured to
           use NVIDIA L4 GPUs at creation. Note that only certain regions are
           available for L4, and only 3D-only mode is supported. This
           configuration cannot be updated later.
           To use NVIDIA L4 GPU for the instance, include:

            --gpu-class=l4
      """,
  }

  @staticmethod
  def __ValidateArgs(args):
    return flags.ValidateRegionConfigArgs(args.add_region, 'add')

  @staticmethod
  def Args(parser):
    resource_args.AddContentResourceArg(
        parser, verb='served by the instance', positional=False
    )
    parser.add_argument('instance', help='Name of the instance to be created')
    parser.add_argument(
        '--version',
        required=True,
        help='Build version tag of the content served by this instance',
    )
    parser.add_argument(
        '--fallback-url',
        help=(
            'Fallback url to redirect users to when this service instance is'
            ' unable to provide the streaming experience'
        ),
        required=False,
    )
    parser.add_argument(
        '--mode',
        help='The rendering mode that is supported by this service instance',
        required=False,
    )
    parser.add_argument(
        '--gpu-class',
        help='The class of GPU that is used by this service instance',
        required=False,
    )
    flags.AddRegionConfigArg('--add-region', parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    if not Create.__ValidateArgs(args):
      return

    region_configs = args.add_region
    content_ref = args.CONCEPTS.content.Parse()
    content_name = content_ref.RelativeName()
    location = content_ref.locationsId
    instance_name = args.instance
    version = args.version
    fallback_url = args.fallback_url
    mode = args.mode
    gpu_class = args.gpu_class

    if fallback_url and not flags.ValidateUrl(fallback_url):
      return

    if mode and not flags.ValidateMode(mode):
      return

    if gpu_class and not flags.ValidateGpuClass(gpu_class, mode):
      return

    client = api_util.GetClient(self.ReleaseTrack())
    target_location_configs = instances.GenerateTargetLocationConfigs(
        self.ReleaseTrack(),
        add_region_configs=region_configs,
        update_region_configs=None,
        remove_regions=None,
        current_instance=None,
    )
    result_operation = instances.Create(
        self.ReleaseTrack(),
        instance_name,
        content_name,
        location,
        version,
        target_location_configs,
        fallback_url,
        mode,
        gpu_class,
    )
    log.status.Print('Create request issued for: [{}]'.format(instance_name))
    if args.async_:
      log.status.Print(
          'Check operation [{}] for status.\n'.format(result_operation.name)
      )
      return result_operation

    operation_resource = resources.REGISTRY.Parse(
        result_operation.name,
        api_version=api_util.GetApiVersion(self.ReleaseTrack()),
        collection='stream.projects.locations.operations',
    )
    created_instance = waiter.WaitFor(
        waiter.CloudOperationPoller(
            client.projects_locations_streamInstances,
            client.projects_locations_operations,
        ),
        operation_resource,
        'Waiting for operation [{}] to complete'.format(result_operation.name),
    )

    instance_resource = resources.REGISTRY.Parse(
        None,
        collection='stream.projects.locations.streamInstances',
        api_version=api_util.GetApiVersion(self.ReleaseTrack()),
        params={
            'projectsId': properties.VALUES.core.project.Get(required=True),
            'locationsId': 'global',
            'streamInstancesId': instance_name,
        },
    )

    log.CreatedResource(instance_resource)

    return created_instance
