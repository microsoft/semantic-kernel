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
"""Flag Utilities for cloud tpu commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


def GetTPUNameArg():
  return base.Argument(
      'tpu_id',
      help='Name of the TPU.')


def GetDescriptionFlag():
  return base.Argument(
      '--description',
      help='Specifies a text description of the TPU.')


def GetAcceleratorTypeFlag():
  """Set argument for choosing the TPU Accelerator type."""
  return base.Argument(
      '--accelerator-type',
      default='v2-8',
      type=lambda x: x.lower(),
      required=False,
      help="""\
      TPU accelerator type for the TPU.
       If not specified, this defaults to `v2-8`.
      """)


def GetVersionFlag():
  """Set argument for choosing the TPU Tensor Flow version."""
  return base.Argument(
      '--version',
      required=True,
      help="""\
      TensorFlow version for the TPU, such as `1.6`. For a list of available
      TensorFlow versions please see https://www.tensorflow.org/versions/.
      """)


def GetRangeFlag():
  """Set Cidr Range for Cloud TPU."""
  return base.Argument(
      '--range',
      required=False,
      help="""\
      CIDR Range for the TPU.
       The IP range that the TPU will select an IP address from.
       Must be in CIDR notation and a `/29` range, for example `192.168.0.0/29`.
       Errors will occur if the CIDR range has already been used for a
       currently existing TPU, the CIDR range conflicts with any networks
       in the user's provided network, or the provided network is peered with
       another network that is using that CIDR range.
      """)


def AddPreemptibleFlag(parser):
  return parser.add_argument(
      '--preemptible',
      required=False,
      action='store_true',
      default=False,
      help="""\
      Create a preemptible Cloud TPU, instead of a normal (non-preemptible) Cloud TPU. A
        preemptible Cloud TPU costs less per hour, but the Cloud TPU service can stop/terminate
        the node at any time.
      """)


def AddTpuNameArg(parser):
  return parser.add_argument(
      'execution_group_name',
      help="""\
      The execution group name to delete. """
      )


def AddTpuNameOverrideArg(parser):
  return parser.add_argument(
      '--name',
      help="""\
      Override the name to use for VMs and TPUs (defaults to your username). """,
      )


def AddPreemptibleVmFlag(parser):
  return parser.add_argument(
      '--preemptible-vm',
      required=False,
      action='store_true',
      default=False,
      help="""\
      Create a preemptible Compute Engine VM, instead of a normal (non-preemptible) VM.
        A preemptible VM costs less per hour, but the Compute Engine service can terminate the
        instance at any time.
      """)


def AddTfVersionFlag(parser, help_text_override=None):
  help_text = """\
      Set the version of TensorFlow to use when creating the Compute Engine VM and the Cloud TPU.
        (It defaults to auto-selecting the latest stable release.)
      """
  return parser.add_argument(
      '--tf-version',
      required=False,
      help=help_text_override or help_text
      )


def AddTfVersionFlagForResume(parser):
  help_text_override = """\
      Set the version of TensorFlow to the version originally set when creating the suspended Cloud TPU and Compute Engine VM .
        (It defaults to auto-selecting the latest stable release.)
      """
  AddTfVersionFlag(parser, help_text_override)


def AddVmOnlyFlag(parser):
  return parser.add_argument(
      '--vm-only',
      action='store_true',
      required=False,
      default=False,
      help="""\
      Do not allocate a TPU, only allocate a VM (useful if you're not ready to run on a TPU yet).
      """)


def AddTpuOnlyFlag(parser, help_text_override=None):
  help_text = """\
      Do not allocate a VM, only allocate a TPU. To be used after the command has been run with a --vm-only flag
      and the user is ready to run on a TPU. Ensure that the name matches the name passed in when creating with the --vm-only flag.
      """
  return parser.add_argument(
      '--tpu-only',
      action='store_true',
      required=False,
      default=False,
      help=help_text_override or help_text)


def AddTpuOnlyFlagForDelete(parser):
  help_text_override = """\
    Do not delete VM, only delete the TPU.
  """
  return AddTpuOnlyFlag(parser, help_text_override)


def AddDeepLearningImagesFlag(parser):
  return parser.add_argument(
      '--use-dl-images',
      action='store_true',
      required=False,
      default=False,
      help="""\
      Use Deep Learning VM Images (see docs - https://cloud.google.com/deep-learning-vm/) instead
      of TPU-specific machine images. Defaults to TPU-specific images. This
      value is set to true automatically if the --use-with-notebook flag is
      set to true.
      """)


def AddDryRunFlag(parser):
  return parser.add_argument(
      '--dry-run',
      required=False,
      action='store_true',
      default=False,
      help="""\
      Do not make changes; print only what would have happened.
      """)


def AddPortForwardingFlag(parser):
  return parser.add_argument(
      '--forward-ports',
      action='store_false',
      required=False,
      help="""\
      Automatically forward useful ports from the Compute Engine VM to your local
        machine. The ports forwarded are: 6006 (tensorboard), 8888 (jupyter notebooks),
        8470 (TPU port), 8466 (TPU profiler port).
      """)


def AddGceImageFlag(parser):
  return parser.add_argument(
      '--gce-image',
      help="""\
      Override the automatically chosen Compute Engine Image. Use this flag when you're using
        your own custom images instead of the provided ones with TensorFlow pre-installed.
      """)


def AddDiskSizeFlag(parser):
  return parser.add_argument(
      '--disk-size',
      default='250GB',
      type=arg_parsers.BinarySize(
          lower_bound='20GB',
          upper_bound='2000GB',
          suggested_binary_size_scales=['GB']),
      help="""\
      Configures the root volume size of your Compute Engine VM (in GB). The
      minimum size is 20GB and the maximum is 2000GB. Specified value must be an
      integer multiple of Gigabytes.
      """)


def AddMachineTypeArgs(parser):
  return parser.add_argument(
      '--machine-type',
      default='n1-standard-1',
      help="""\
      Specifies the machine type used for the Compute Engine VM. To get a
      list of available machine types, run 'gcloud compute
      machine-types list'. If unspecified, the default type is n1-standard-1.
      """)


def AddUseWithNotebook(parser):
  return parser.add_argument(
      '--use-with-notebook',
      action='store_true',
      required=False,
      default=False,
      help="""\
      Allow Compute Engine VM to be recognized by Cloud AI Notebooks. This
      automatically sets the content of the flag --use-dl-images flag to be
      true.
      """
      )


def AddNetworkArgs(parser, help_text_override=None):
  help_text = """\
    Specifies the network the Cloud TPU and associated VM should be created in.
    If unspecified, the network "default" is picked.
    """
  return parser.add_argument(
      '--network',
      default='default',
      help=help_text_override or help_text)


def AddNetworkArgsForResume(parser):
  help_text_override = """\
    Set to the network that was originally used creating the suspended Cloud TPU
    and Compute Engine VM. (It defaults to using the 'default' network.)
    """
  return AddNetworkArgs(parser, help_text_override)
