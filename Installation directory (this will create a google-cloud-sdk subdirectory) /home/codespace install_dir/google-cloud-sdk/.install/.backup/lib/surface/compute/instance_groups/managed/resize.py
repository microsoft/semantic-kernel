# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command for setting size of managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


def _AddArgs(parser, creation_retries, suspended_stopped_sizes):
  """Adds args."""
  parser.add_argument(
      '--size',
      required=not suspended_stopped_sizes,
      type=arg_parsers.BoundedInt(0, sys.maxsize, unlimited=True),
      help='Target number of running instances in managed instance group.')

  if creation_retries:
    parser.add_argument(
        '--creation-retries',
        action='store_true',
        default=True,
        help='When instance creation fails retry it.')

  if suspended_stopped_sizes:
    parser.add_argument(
        '--suspended-size',
        type=arg_parsers.BoundedInt(0, sys.maxsize, unlimited=True),
        help='Target number of suspended instances in managed instance group.')
    parser.add_argument(
        '--stopped-size',
        type=arg_parsers.BoundedInt(0, sys.maxsize, unlimited=True),
        help='Target number of stopped instances in managed instance group.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Resize(base.Command):
  """Set managed instance group size."""

  @staticmethod
  def Args(parser):
    _AddArgs(
        parser=parser, creation_retries=False, suspended_stopped_sizes=False)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def CreateGroupReference(self, client, resources, args):
    return (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.
            ResolveAsResource(
                args, resources,
                default_scope=compute_scope.ScopeEnum.ZONE,
                scope_lister=flags.GetDefaultScopeLister(client)))

  @staticmethod
  def _MakeIgmResizeRequest(client, igm_ref, args):
    service = client.apitools_client.instanceGroupManagers
    request = client.messages.ComputeInstanceGroupManagersResizeRequest(
        instanceGroupManager=igm_ref.Name(),
        size=args.size,
        project=igm_ref.project,
        zone=igm_ref.zone)
    return client.MakeRequests([(service, 'Resize', request)])

  @staticmethod
  def _MakeRmigResizeRequest(client, igm_ref, args):
    service = client.apitools_client.regionInstanceGroupManagers
    request = client.messages.ComputeRegionInstanceGroupManagersResizeRequest(
        instanceGroupManager=igm_ref.Name(),
        size=args.size,
        project=igm_ref.project,
        region=igm_ref.region)
    return client.MakeRequests([(service, 'Resize', request)])

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    igm_ref = self.CreateGroupReference(client, holder.resources, args)
    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      return self._MakeIgmResizeRequest(client, igm_ref, args)

    if igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      return self._MakeRmigResizeRequest(client, igm_ref, args)

    raise ValueError('Unknown reference type {0}'.format(igm_ref.Collection()))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ResizeBeta(Resize):
  """Set managed instance group size."""

  @staticmethod
  def Args(parser):
    _AddArgs(
        parser=parser, creation_retries=True, suspended_stopped_sizes=False)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  @staticmethod
  def _MakeIgmResizeAdvancedRequest(client, igm_ref, args):
    service = client.apitools_client.instanceGroupManagers
    request = (
        client.messages.ComputeInstanceGroupManagersResizeAdvancedRequest(
            instanceGroupManager=igm_ref.Name(),
            instanceGroupManagersResizeAdvancedRequest=(
                client.messages.InstanceGroupManagersResizeAdvancedRequest(
                    targetSize=args.size,
                    noCreationRetries=not args.creation_retries,
                )),
            project=igm_ref.project,
            zone=igm_ref.zone))
    return client.MakeRequests([(service, 'ResizeAdvanced', request)])

  @staticmethod
  def _MakeRmigResizeAdvancedRequest(client, igm_ref, args):
    service = client.apitools_client.regionInstanceGroupManagers
    request = (
        client.messages
        .ComputeRegionInstanceGroupManagersResizeAdvancedRequest(
            instanceGroupManager=igm_ref.Name(),
            regionInstanceGroupManagersResizeAdvancedRequest=(
                client.messages
                .RegionInstanceGroupManagersResizeAdvancedRequest(
                    targetSize=args.size,
                    noCreationRetries=not args.creation_retries,
                )),
            project=igm_ref.project,
            region=igm_ref.region))
    return client.MakeRequests([(service, 'ResizeAdvanced', request)])

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    igm_ref = self.CreateGroupReference(client, holder.resources, args)
    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      return self._MakeIgmResizeAdvancedRequest(client, igm_ref, args)

    if igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      # user specifies --no-creation-retries flag explicitly
      if not args.creation_retries:
        return self._MakeRmigResizeAdvancedRequest(client, igm_ref, args)
      return self._MakeRmigResizeRequest(client, igm_ref, args)

    raise ValueError('Unknown reference type {0}'.format(igm_ref.Collection()))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ResizeAlpha(ResizeBeta):
  """Set managed instance group sizes."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, creation_retries=True, suspended_stopped_sizes=True)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  @staticmethod
  def _ValidateArgs(args):
    if (args.size is None and args.suspended_size is None and
        args.stopped_size is None):
      raise exceptions.OneOfArgumentsRequiredException(
          ['--size', '--suspended-size', '--stopped-size'],
          'At least one of the sizes must be specified')
    if not args.creation_retries:
      if args.size is None:
        raise exceptions.RequiredArgumentException(
            '--size',
            'Size must be specified when --no-creation-retries flag is used.')
      if args.suspended_size is not None:
        raise exceptions.ConflictingArgumentsException('--suspended-size',
                                                       '--no-creation-retries')
      if args.stopped_size is not None:
        raise exceptions.ConflictingArgumentsException('--stopped-size',
                                                       '--no-creation-retries')

  @staticmethod
  def _MakeIgmPatchResource(client, args):
    igm_patch_resource = client.messages.InstanceGroupManager()
    if args.size is not None:
      igm_patch_resource.targetSize = args.size
    if args.suspended_size is not None:
      igm_patch_resource.targetSuspendedSize = args.suspended_size
    if args.stopped_size is not None:
      igm_patch_resource.targetStoppedSize = args.stopped_size
    return igm_patch_resource

  @staticmethod
  def _MakeIgmPatchRequest(client, igm_ref, args):
    service = client.apitools_client.instanceGroupManagers
    request = client.messages.ComputeInstanceGroupManagersPatchRequest(
        instanceGroupManager=igm_ref.Name(),
        instanceGroupManagerResource=ResizeAlpha._MakeIgmPatchResource(
            client, args),
        project=igm_ref.project,
        zone=igm_ref.zone)
    return client.MakeRequests([(service, 'Patch', request)])

  @staticmethod
  def _MakeRmigPatchRequest(client, igm_ref, args):
    service = client.apitools_client.regionInstanceGroupManagers
    request = client.messages.ComputeRegionInstanceGroupManagersPatchRequest(
        instanceGroupManager=igm_ref.Name(),
        instanceGroupManagerResource=ResizeAlpha._MakeIgmPatchResource(
            client, args),
        project=igm_ref.project,
        region=igm_ref.region)
    return client.MakeRequests([(service, 'Patch', request)])

  # pylint: disable=line-too-long
  # |  scope   | creation_retries arg | suspended or stopped _size arg |            method             |
  # |----------|----------------------|--------------------------------|-------------------------------|
  # | zonal    | True                 | True                           | Patch                         |
  # | zonal    | True                 | False                          | ResizeAdvanced                |
  # | zonal    | False                | True                           | ConflictingArgumentsException |
  # | zonal    | False                | False                          | ResizeAdvanced                |
  # | regional | True                 | True                           | Patch                         |
  # | regional | True                 | False                          | Resize      TODO(b/178852691) |
  # | regional | False                | True                           | ConflictingArgumentsException |
  # | regional | False                | False                          | ResizeAdvanced                |
  # pylint: enable=line-too-long
  def Run(self, args):
    self._ValidateArgs(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    igm_ref = self.CreateGroupReference(client, holder.resources, args)
    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      # user specifies --no-creation-retries flag explicitly
      if not args.creation_retries:
        return self._MakeIgmResizeAdvancedRequest(client, igm_ref, args)

      return self._MakeIgmPatchRequest(client, igm_ref, args)

    if igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      # user specifies --no-creation-retries flag explicitly
      if not args.creation_retries:
        return self._MakeRmigResizeAdvancedRequest(client, igm_ref, args)

      if args.suspended_size is not None or args.stopped_size is not None:
        return self._MakeRmigPatchRequest(client, igm_ref, args)

      # TODO(b/178852691): Redirect whole alpha traffic to ResizeAdvanced,
      # even if the "no-creation-retries" flag is not set. This would be the
      # intended shape of this code, and this is would be also consistent with
      # zonal version. Instead of doing it immediately, this TODO is added to
      # get the desired gradual launch behavior.
      return self._MakeRmigResizeRequest(client, igm_ref, args)

    raise ValueError('Unknown reference type {0}'.format(igm_ref.Collection()))


Resize.detailed_help = {
    'brief': 'Set managed instance group size.',
    'DESCRIPTION': """
        *{command}* resize a managed instance group to a provided size.

If you resize down, the Instance Group Manager service deletes instances from
the group until the group reaches the desired size. Instances are deleted
in arbitrary order but the Instance Group Manager takes into account some
considerations before it chooses which instance to delete. For more information,
see https://cloud.google.com/compute/docs/reference/rest/v1/instanceGroupManagers/resize.

If you resize up, the service adds instances to the group using the current
instance template until the group reaches the desired size.
""",
}
ResizeBeta.detailed_help = Resize.detailed_help
ResizeAlpha.detailed_help = Resize.detailed_help
