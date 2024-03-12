# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for creating VM instances running Docker images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import containers_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateContainer(base.UpdateCommand):
  """Command for updating VM instances running container images."""

  @staticmethod
  def Args(parser):
    """Register parser args."""
    instances_flags.AddUpdateContainerArgs(parser,
                                           container_mount_disk_enabled=True)

  def Run(self, args):
    """Issues requests necessary to update Container."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = instances_flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=instances_flags.GetInstanceZoneScopeLister(client))

    instance = client.apitools_client.instances.Get(
        client.messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))

    container_mount_disk = instances_flags.GetValidatedContainerMountDisk(
        holder, args.container_mount_disk, instance.disks, [], for_update=True,
        client=client.apitools_client)

    containers_utils.UpdateInstance(holder, client, instance_ref, instance,
                                    args, container_mount_disk_enabled=True,
                                    container_mount_disk=container_mount_disk)


UpdateContainer.detailed_help = {
    'brief':
        """\
    Updates Compute Engine virtual machine instances running container
    images.
    """,
    'DESCRIPTION':
        """\
    *{command}* updates Compute Engine virtual
    machines that runs a Docker image. For example:

      $ {command} instance-1 --zone us-central1-a \
        --container-image=gcr.io/google-containers/busybox

    updates an instance called instance-1, in the us-central1-a zone,
    to run the 'busybox' image.

    For more examples, refer to the *EXAMPLES* section below.
    """,
    'EXAMPLES':
        """\
    To run the gcr.io/google-containers/busybox image on an instance named
    'instance-1' that executes 'echo "Hello world"' as a run command, run:

      $ {command} instance-1 \
        --container-image=gcr.io/google-containers/busybox \
        --container-command='echo "Hello world"'

    To run the gcr.io/google-containers/busybox image in privileged mode, run:

      $ {command} instance-1 \
        --container-image=gcr.io/google-containers/busybox \
        --container-privileged
    """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class UpdateContainerAlpha(UpdateContainer):
  """Command for updating VM instances running container images."""

  @staticmethod
  def Args(parser):
    instances_flags.AddUpdateContainerArgs(parser,
                                           container_mount_disk_enabled=True)

  def Run(self, args):
    """Issues requests necessary to update Container."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = instances_flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=instances_flags.GetInstanceZoneScopeLister(client))
    instance = client.apitools_client.instances.Get(
        client.messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))
    container_mount_disk = instances_flags.GetValidatedContainerMountDisk(
        holder, args.container_mount_disk, instance.disks, [], for_update=True,
        client=client.apitools_client)
    containers_utils.UpdateInstance(holder, client, instance_ref, instance,
                                    args, container_mount_disk_enabled=True,
                                    container_mount_disk=container_mount_disk)
