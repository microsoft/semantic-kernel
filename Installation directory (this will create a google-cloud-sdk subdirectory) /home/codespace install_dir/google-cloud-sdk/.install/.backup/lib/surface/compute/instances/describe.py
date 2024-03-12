# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for describing instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.command_lib.util.apis import arg_utils

DETAILED_HELP = {
    'brief': 'Describe a virtual machine instance.',
    'DESCRIPTION':
        """\
        *{command}* displays all data associated with a Compute
        Engine virtual machine instance.

        It's possible to limit the the scope of the description by using the
        '--format' flag. For details, see
        [Filtering and formatting fun with gcloud](https://cloud.google.com/blog/products/gcp/filtering-and-formatting-fun-with).
        """,
    'EXAMPLES':
        """\
        To describe an instance named ``{0}'', run:

          $ {1} {0}

        To output only a set of fields from the available information, specify
        it  using the '--format' flag:

          $ {1} {0} --format="yaml(name,status,disks)"
        """.format('test-instance', '{command}'),
}


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe a virtual machine instance."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser, operation_type='describe')

  def _GetInstanceRef(self, holder, args):
    return flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(holder.client))

  def _GetInstance(self, holder, instance_ref):
    request = holder.client.messages.ComputeInstancesGetRequest(
        **instance_ref.AsDict())
    return holder.client.MakeRequests([
        (holder.client.apitools_client.instances, 'Get', request)])[0]

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    instance_ref = self._GetInstanceRef(holder, args)
    return self._GetInstance(holder, instance_ref)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(Describe):
  """Describe a virtual machine instance."""

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser, operation_type='describe')
    parser.add_argument(
        '--guest-attributes',
        metavar='GUEST_ATTRIBUTE_KEY',
        type=arg_parsers.ArgList(),
        default=[],
        help=('Instead of instance resource display guest attributes of the '
              'instance stored with the given keys.'))
    parser.add_argument(
        '--view',
        choices={
            'FULL': 'Include everything in instance',
            'BASIC': (
                'Default view of instance, Including everything except Partner'
                ' Metadata.'
            ),
        },
        type=arg_utils.ChoiceToEnumName,
        help='specify Instance view',
    )

  def _GetGuestAttributes(self, holder, instance_ref, variable_keys):
    def _GetGuestAttributeRequest(holder, instance_ref, variable_key):
      req = holder.client.messages.ComputeInstancesGetGuestAttributesRequest(
          instance=instance_ref.Name(),
          project=instance_ref.project,
          variableKey=variable_key,
          zone=instance_ref.zone)
      return (
          holder.client.apitools_client.instances, 'GetGuestAttributes', req)

    requests = [
        _GetGuestAttributeRequest(holder, instance_ref, variable_key)
        for variable_key in variable_keys]
    return holder.client.MakeRequests(requests)

  def _GetInstanceView(self, view, request_message):
    if view == 'FULL':
      return request_message.ViewValueValuesEnum.FULL
    elif view == 'BASIC':
      return request_message.ViewValueValuesEnum.BASIC
    return None

  def _GetInstance(self, holder, instance_ref, view=None):
    request = holder.client.messages.ComputeInstancesGetRequest(
        **instance_ref.AsDict(), view=view)
    return holder.client.MakeRequests([
        (holder.client.apitools_client.instances, 'Get', request)])[0]

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    instance_ref = self._GetInstanceRef(holder, args)
    if args.guest_attributes:
      return self._GetGuestAttributes(
          holder, instance_ref, args.guest_attributes
      )
    if args.view:
      args.view = self._GetInstanceView(
          args.view, holder.client.messages.ComputeInstancesGetRequest
      )
    return self._GetInstance(holder, instance_ref, args.view)


Describe.detailed_help = DETAILED_HELP
DescribeAlpha.detailed_help = DETAILED_HELP
