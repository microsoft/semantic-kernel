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
"""Command for creating TPU node and GCE VM combination."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.exceptions import HttpConflictError
from apitools.base.py.exceptions import HttpNotFoundError

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.tpus import flags as tpus_flags
from googlecloudsdk.command_lib.compute.tpus.execution_groups import util as tpu_utils
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  r"""Create Google Compute TPUs along with VMs.

  ## EXAMPLES

  To create both TPU and VM, run:

    $ {command} --name=test-execution-group --zone=test-zone
    --project=test-project --accelerator-type=v2-8 --tf-version=2.4.1

  To create both TPU and VM with additional flags, run:

    $ {command} --name=test-execution-group --zone=test-zone \
    --project=test-project --accelerator-type=v2-8 --tf-version=2.4.1 \
    --network=default --preemptible-vm --disk-size=100 \
    --machine-type=n1-standard-2 --use-dl-images

  To create a VM only before creating the TPU, run:

    $ {command} --name=test-execution-group-tpu-only --zone=test-zone \
    --project=test-project --accelerator-type=v2-8 --tf-version=2.4.1 --tpu-only

  To create the TPU only after the VM has been created, run:

    $ {command} --name=test-execution-group-tpu-only --zone=test-zone \
    --project=test-project --accelerator-type=v2-8 --tf-version=2.4.1 --vm-only
  """

  @classmethod
  def Args(cls, parser):
    flags.AddZoneFlag(parser, resource_type='tpu', operation_type='create')
    tpus_flags.AddTpuNameOverrideArg(parser)
    tpus_flags.AddPreemptibleFlag(parser)
    tpus_flags.AddTfVersionFlag(parser)
    tpus_flags.AddVmOnlyFlag(parser)
    tpus_flags.AddTpuOnlyFlag(parser)
    tpus_flags.AddDeepLearningImagesFlag(parser)
    tpus_flags.AddDryRunFlag(parser)
    tpus_flags.GetAcceleratorTypeFlag().AddToParser(parser)
    tpus_flags.AddPreemptibleVmFlag(parser)
    tpus_flags.AddPortForwardingFlag(parser)
    tpus_flags.AddGceImageFlag(parser)
    tpus_flags.AddDiskSizeFlag(parser)
    tpus_flags.AddMachineTypeArgs(parser)
    tpus_flags.AddNetworkArgs(parser)
    tpus_flags.AddUseWithNotebook(parser)

  def Run(self, args):
    tpu_utils.DefaultArgs.ValidateName(args)
    tpu_utils.DefaultArgs.ValidateZone(args)

    responses = []

    if args.dry_run:
      self.DryRun(args)
      return responses

    tpu = tpu_utils.TPUNode(self.ReleaseTrack())
    if not args.tf_version:
      try:
        args.tf_version = tpu.LatestStableTensorflowVersion(args.zone)
      except HttpNotFoundError:
        log.err.Print('Could not find stable Tensorflow version, please '
                      'set tensorflow version flag using --tf-version')
        return responses

    if not args.vm_only:
      try:
        tpu_operation_ref = tpu.Create(args.name,
                                       args.accelerator_type, args.tf_version,
                                       args.zone, args.preemptible,
                                       args.network)
      except HttpConflictError:
        log.err.Print('TPU Node with name:{} already exists, '
                      'try a different name'.format(args.name))
        return responses

    if not args.tpu_only:
      instance = tpu_utils.Instance(self.ReleaseTrack())
      gce_image = args.gce_image
      if not gce_image:
        use_dl_images = args.use_dl_images
        if args.use_with_notebook:
          use_dl_images = True
        gce_image = instance.ResolveImageFromTensorflowVersion(
            args.tf_version, use_dl_images)
      try:
        instance_operation_ref = instance.Create(
            args.name, args.zone, args.machine_type,
            utils.BytesToGb(args.disk_size), args.preemptible_vm, gce_image,
            args.network, args.use_with_notebook)
      except HttpConflictError:
        err_msg = ('VM with name:{} already exists, '
                   'try a different name.').format(args.name)
        if not args.vm_only:
          err_msg += (' TPU Node:{} creation is underway and will '
                      'need to be deleted.'.format(args.name))
        log.err.Print(err_msg)
        return responses

    if not args.vm_only:
      responses.append(
          tpu.WaitForOperation(tpu_operation_ref, 'Creating TPU node:{}'.format(
              args.name)))
      tpu_node = tpu.Get(args.name, args.zone)
      resource_manager = tpu_utils.ResourceManager()
      resource_manager.AddTpuUserAgent(tpu_node.serviceAccount)
    if not args.tpu_only:
      instance_create_response = instance.WaitForOperation(
          instance_operation_ref, 'Creating GCE VM:{}'.format(args.name))
      responses.append(instance_create_response)

      ssh_helper = tpu_utils.SSH(self.ReleaseTrack())
      responses.append(ssh_helper.SSHToInstance(args, instance_create_response))

    return responses

  def DryRun(self, args):
    if not args.vm_only:
      log.status.Print(
          'Creating TPU with Name:{}, Accelerator type:{}, TF version:{}, '
          'Zone:{}, Network:{}'.format(args.name, args.accelerator_type,
                                       args.tf_version, args.zone,
                                       args.network))
      log.status.Print(
          'Adding Storage and Logging access on TPU Service Account')

    if not args.tpu_only:
      log.status.Print('Creating VM with Name:{}, Zone:{}, Machine Type:{},'
                       ' Disk Size(GB):{}, Preemptible:{}, Network:{}'.format(
                           args.name, args.zone, args.machine_type,
                           utils.BytesToGb(args.disk_size), args.preemptible_vm,
                           args.network))

      log.status.Print('SSH to VM:{}'.format(args.name))
