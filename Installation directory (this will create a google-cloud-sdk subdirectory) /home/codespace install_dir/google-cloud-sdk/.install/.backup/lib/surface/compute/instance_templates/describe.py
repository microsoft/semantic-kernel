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
"""Command for describing instance templates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_templates import flags
from googlecloudsdk.command_lib.util.apis import arg_utils


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class DescribeGA(base.DescribeCommand):
  """Describe a virtual machine instance template."""
  support_region_flag = True
  view_flag = False

  @classmethod
  def Args(cls, parser):
    DescribeGA.InstanceTemplateArg = flags.MakeInstanceTemplateArg(
        include_regional=cls.support_region_flag)
    DescribeGA.InstanceTemplateArg.AddArgument(
        parser, operation_type='describe'
    )
    if cls.view_flag:
      parser.add_argument(
          '--view',
          choices={
              'FULL': 'Include everything in instance',
              'BASIC': (
                  'Default view of instance, Including everything except'
                  ' Partner Metadata.'
              ),
          },
          type=arg_utils.ChoiceToEnumName,
          help='specify Instance view',
      )

  @staticmethod
  def GetServiceClient(client, ref):
    if ref.Collection() == 'compute.instanceTemplates':
      return client.apitools_client.instanceTemplates
    else:
      return client.apitools_client.regionInstanceTemplates

  @staticmethod
  def GetRequestMessage(client, ref):
    if ref.Collection() == 'compute.instanceTemplates':
      return client.messages.ComputeInstanceTemplatesGetRequest
    else:
      return client.messages.ComputeRegionInstanceTemplatesGetRequest

  @staticmethod
  def GetViewEnumValue(view, request_message):
    if view == 'FULL':
      return request_message.ViewValueValuesEnum.FULL
    elif view == 'BASIC':
      return request_message.ViewValueValuesEnum.BASIC
    return None

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_template_ref = DescribeGA.InstanceTemplateArg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
        default_scope=compute_scope.ScopeEnum.GLOBAL,
    )

    service_client = self.GetServiceClient(client, instance_template_ref)
    request_message = self.GetRequestMessage(client, instance_template_ref)
    if self.view_flag:
      return client.MakeRequests([(
          service_client,
          'Get',
          request_message(
              **instance_template_ref.AsDict(),
              view=self.GetViewEnumValue(
                  args.view, request_message
              )
          ),
      )])[0]

    return client.MakeRequests([(
        service_client,
        'Get',
        request_message(**instance_template_ref.AsDict()),
    )])[0]


DescribeGA.detailed_help = {
    'brief': 'Describe a virtual machine instance template',
    'DESCRIPTION': """\
        *{command}* displays all data associated with a Google Compute
        Engine virtual machine instance template.
        """,
    'EXAMPLES': """\
        To describe the instance template named 'INSTANCE-TEMPLATE', run:

          $ {command} INSTANCE-TEMPLATE
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(DescribeGA):
  view_flag = True
