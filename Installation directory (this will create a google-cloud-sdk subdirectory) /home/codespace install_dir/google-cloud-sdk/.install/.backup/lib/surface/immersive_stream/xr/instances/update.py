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
"""Command to update an Immersive Stream for XR service instance."""

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
class Update(base.Command):
  """Update an Immersive Stream for XR service instance."""

  detailed_help = {
      'DESCRIPTION': ("""
          Update an Immersive Stream for XR service instance.
          This command can be used to update one of the following:
            - the capacity for an existing region of the service instance
            - the content build version served by the instance
            - the fallback url to redirect users to when the service instance is
              unable to provide the streaming experience

          If updating the capacity, only one region may be updated for each
          command execution, and the new capacity may not be 0 or exceed the
          quota limit.
      """),
      'EXAMPLES': ("""
          To update the service instance `my-instance` to have capacity 2 for an
          existing region us-west1, run:

            $ {command} my-instance --update-region=region=us-west1,capacity=2

          To update the service instance `my-instance` to have capacity 1 for a
          new region us-east4, run:

            $ {command} my-instance --add-region=region=us-east4,capacity=1

          To update the service instance `my-instance` to remove the existing
          region us-east4, run:

            $ {command} my-instance --remove-region=us-east4

          To update the service instance `my-instance` to serve content version
          `my-version`, run:

            $ {command} my-instance --version=my-version

          To update the service instance `my-instance` to use fallback url
          `https://www.google.com`, run:

            $ {command} my-instance --fallback-url="https://www.google.com"
      """)
  }

  @staticmethod
  def __ValidateArgs(args):
    if args.add_region:
      return flags.ValidateRegionConfigArgs(args.add_region, 'add')

    if args.remove_region:
      if len(set(args.remove_region)) < len(args.remove_region):
        log.error('Duplicate regions in --remove-region arguments.')
        return False

    if args.update_region:
      return flags.ValidateRegionConfigArgs(args.update_region, 'update')

    return True

  @staticmethod
  def Args(parser):
    resource_args.AddInstanceResourceArg(parser, verb='to update')
    group = parser.add_group(mutex=True, required=True, help='Update options')
    group.add_argument(
        '--version',
        help='Build version tag of the content served by this instance')
    group.add_argument(
        '--fallback-url',
        help='Fallback url to redirect users to when this service instance is unable to provide the streaming experience'
    )
    flags.AddRegionConfigArg(
        '--add-region', group, repeatable=False, required=False)
    flags.AddRegionConfigArg(
        '--update-region', group, repeatable=False, required=False)
    group.add_argument(
        '--remove-region', help='Region to remove', action='append')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    if not Update.__ValidateArgs(args):
      return

    version = args.version
    fallback_url = args.fallback_url
    add_region_configs = args.add_region
    remove_regions = args.remove_region
    update_region_configs = args.update_region
    instance_name = args.instance

    instance_ref = resources.REGISTRY.Parse(
        None,
        collection='stream.projects.locations.streamInstances',
        api_version=api_util.GetApiVersion(self.ReleaseTrack()),
        params={
            'projectsId': properties.VALUES.core.project.Get(required=True),
            'locationsId': 'global',
            'streamInstancesId': instance_name
        })

    if version:
      result_operation = instances.UpdateContentBuildVersion(
          self.ReleaseTrack(), instance_ref, version)
    elif fallback_url:
      if not flags.ValidateUrl(fallback_url):
        return
      result_operation = instances.UpdateFallbackUrl(self.ReleaseTrack(),
                                                     instance_ref, fallback_url)
    else:
      # We limit to one update per call.
      if add_region_configs:
        if len(add_region_configs) > 1:
          log.error(('Only one region may be added at a time. Please try again '
                     'with only one --add-region argument.'))
          return
      elif remove_regions:
        if len(remove_regions) > 1:
          log.error(('Only one region may be removed at a time. Please try '
                     'again with only one --remove-region argument.'))
          return
      elif update_region_configs:
        if len(update_region_configs) > 1:
          log.error(('Only one region may be updated at a time. Please try '
                     'again with only one --update-region argument.'))
          return

      current_instance = instances.Get(self.ReleaseTrack(),
                                       instance_ref.RelativeName())
      target_location_configs = instances.GenerateTargetLocationConfigs(
          self.ReleaseTrack(),
          add_region_configs=add_region_configs,
          update_region_configs=update_region_configs,
          remove_regions=remove_regions,
          current_instance=current_instance)
      if target_location_configs is None:
        return
      result_operation = instances.UpdateLocationConfigs(
          self.ReleaseTrack(), instance_ref, target_location_configs)

    client = api_util.GetClient(self.ReleaseTrack())

    log.status.Print('Update request issued for: [{}]'.format(instance_name))
    if args.async_:
      log.status.Print('Check operation [{}] for status.\n'.format(
          result_operation.name))
      return result_operation

    operation_resource = resources.REGISTRY.Parse(
        result_operation.name,
        collection='stream.projects.locations.operations',
        api_version=api_util.GetApiVersion(self.ReleaseTrack()))
    updated_instance = waiter.WaitFor(
        waiter.CloudOperationPoller(client.projects_locations_streamInstances,
                                    client.projects_locations_operations),
        operation_resource,
        'Waiting for operation [{}] to complete'.format(result_operation.name))

    instance_resource = resources.REGISTRY.Parse(
        None,
        collection='stream.projects.locations.streamInstances',
        api_version=api_util.GetApiVersion(self.ReleaseTrack()),
        params={
            'projectsId': properties.VALUES.core.project.Get(required=True),
            'locationsId': 'global',
            'streamInstancesId': instance_name
        })

    log.UpdatedResource(instance_resource)
    return updated_instance
