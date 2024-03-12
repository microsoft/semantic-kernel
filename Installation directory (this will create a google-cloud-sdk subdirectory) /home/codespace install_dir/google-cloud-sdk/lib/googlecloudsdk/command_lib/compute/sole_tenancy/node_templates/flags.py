# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute node templates commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core.util import scaled_integer
import six


def MakeNodeTemplateArg():
  return compute_flags.ResourceArgument(
      resource_name='node templates',
      regional_collection='compute.nodeTemplates',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def _BinarySizeOrAny(default_unit):
  """Parses the value 'any' or a binary size converted to the default unit."""
  # pylint: disable=protected-access
  bytes_per_unit = scaled_integer.GetBinaryUnitSize(default_unit)
  def _Parse(value):
    value = value.lower()
    if value == 'any':
      return value
    size = arg_parsers.BinarySize(default_unit=default_unit)(value)
    converted_size = size // bytes_per_unit
    return six.text_type(converted_size)
  return _Parse


def _IntOrAny():
  def _Parse(value):
    value = value.lower()
    if value == 'any':
      return value
    # Validate that an integer is passed.
    value = int(value)
    return six.text_type(value)
  return _Parse


def _BinarySize(default_unit, lower_bound=None, upper_bound=None):
  """Parses the value as a binary size converted to the default unit."""
  # pylint: disable=protected-access
  bytes_per_unit = scaled_integer.GetBinaryUnitSize(default_unit)
  def _Parse(value):
    value = value.lower()
    size = arg_parsers.BinarySize(
        lower_bound=lower_bound, upper_bound=upper_bound,
        default_unit=default_unit)(value)
    converted_size = size // bytes_per_unit
    return converted_size
  return _Parse


def _Choice(valid_choices):
  def _Parse(value):
    value = six.text_type(value.lower())
    if value not in valid_choices:
      raise arg_parsers.ArgumentTypeError(
          '[type] must be one of [{0}]'.format(
              ','.join(valid_choices)))
    return value
  return _Parse


def AddCreateArgsToParser(parser):
  """Add flags for creating a node template to the argument parser."""
  parser.add_argument(
      '--description',
      help='An optional description of this resource.')
  parser.add_argument(
      '--node-affinity-labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(
          key_type=labels_util.KEY_FORMAT_VALIDATOR,
          value_type=labels_util.VALUE_FORMAT_VALIDATOR),
      action=arg_parsers.UpdateAction,
      help='Labels to use for node affinity, which will be used in instance '
           'scheduling. This corresponds to the `--node-affinity` flag on '
           '`compute instances create` and `compute instance-templates '
           'create`.')
  node_type_group = parser.add_group(mutex=True, required=True)
  node_type_group.add_argument(
      '--node-type',
      help="""\
          The node type to use for nodes in node groups using this template.
          The type of a node determines what resources are available to
          instances running on the node.

          See the following for more information:

              $ {grandparent_command} node-types list""")
  node_type_group.add_argument(
      '--node-requirements',
      type=arg_parsers.ArgDict(
          spec={
              'vCPU': _IntOrAny(),
              'memory': _BinarySizeOrAny('MB'),
              'localSSD': _BinarySizeOrAny('GB'),
          }),
      help="""\
The requirements for nodes. Google Compute Engine will automatically
choose a node type that fits the requirements on Node Group creation.
If multiple node types match your defined criteria, the NodeType with
the least amount of each resource will be selected. You can specify 'any'
to indicate any non-zero value for a certain resource.

The following keys are allowed:

*vCPU*:::: The number of committed cores available to the node.

*memory*:::: The amount of memory available to the node. This value
should include unit (eg. 3072MB or 9GB). If no units are specified,
*MB is assumed*.

*localSSD*:::: Optional. The amount of SSD space available on the
node. This value should include unit (eg. 3072MB or 9GB). If no
units are specified, *GB is assumed*. If this key is not specified, local SSD is
unconstrained.
      """)


def AddAcceleratorArgs(parser):
  """Adds Accelerator-related args."""
  parser.add_argument(
      '--accelerator',
      type=arg_parsers.ArgDict(spec={
          'type': str,
          'count': int,
      }),
      help="""\
      Attaches accelerators (e.g. GPUs) to the node template.

      *type*::: The specific type (e.g. nvidia-tesla-k80 for nVidia Tesla K80)
      of accelerator to attach to the node template. Use 'gcloud compute
      accelerator-types list' to learn about all available accelerator types.

      *count*::: Number of accelerators to attach to each
      node template. The default value is 1.
      """)


def AddDiskArgToParser(parser):
  """Add flag for specifying disk information."""
  parser.add_argument(
      '--disk',
      type=arg_parsers.ArgDict(
          spec={
              'type': _Choice(['local-ssd']),
              'size': _BinarySize(
                  'GB', lower_bound='375GB', upper_bound='375GB'),
              'count': int,
          },
          required_keys=[
              'type',
              'count',
          ]),
      help="""\
Option to specify disk properties. It is mutually exclusive with
'--node-requirements=[localSSD=LOCALSSD]' but
'--node-requirements=[memory=MEMORY],[vCPU=VCPU],any' are still available.

*type*::: Specifies the desired disk type on the node. This disk type must be a
local storage type. This should be the name of the disk type. Currently
only `local-ssd` is allowed.

*size*::: The size of the disk in GiB. Currently you can specify only 375 GiB
or no value at all.

*count*::: Specifies the number of such disks. Set to `16` or `24`.

""")


def GetServerBindingMapperFlag(messages):
  """Helper to get a choice flag from server binding type enum."""
  return arg_utils.ChoiceEnumMapper(
      '--server-binding',
      messages.ServerBinding.TypeValueValuesEnum,
      custom_mappings={
          'RESTART_NODE_ON_ANY_SERVER': (
              'restart-node-on-any-server',
              ('Nodes using this template will restart on any physical server '
               'following a maintenance event.')),
          'RESTART_NODE_ON_MINIMAL_SERVERS': (
              'restart-node-on-minimal-servers', """\
Nodes using this template will restart on the same physical server following a
maintenance event, instead of being live migrated to or restarted on a new
physical server. This means that VMs on such nodes will experience outages while
maintenance is applied. This option may be useful if you are using software
licenses tied to the underlying server characteristics such as physical sockets
or cores, to avoid the need for additional licenses when maintenance occurs.

Note that in some cases, Google Compute Engine may need to move your VMs to a
new underlying server. During these situations your VMs will be restarted on a
new physical server and assigned a new sole tenant physical server ID.""")},
      help_str=(
          'The server binding policy for nodes using this template, which '
          'determines where the nodes should restart following a maintenance '
          'event.'),
      default='restart-node-on-any-server')


def AddCpuOvercommitTypeFlag(parser):
  parser.add_argument(
      '--cpu-overcommit-type',
      choices=['enabled', 'none'],
      help=('CPU overcommit type for nodes created based on this template. To '
            'overcommit CPUs on a VM, set --cpu-overcommit-type equal to '
            'either standard or none, and then when creating a VM, specify a '
            'value for the --min-node-cpu flag. Lower values for '
            '--min-node-cpu specify a higher overcommit ratio, that is, '
            'proportionally more vCPUs in relation to physical CPUs. You can '
            'only overcommit CPUs on VMs that are scheduled on nodes that '
            'support it.')
  )
