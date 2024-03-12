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

"""Cloud Transcoder job templates create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.transcoder import templates
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transcoder import flags
from googlecloudsdk.command_lib.transcoder import resource_args
from googlecloudsdk.command_lib.util.args import labels_util


class Create(base.CreateCommand):
  """Create Transcoder job templates."""

  detailed_help = {
      'EXAMPLES':
          """
        To create a job template with json format configuration:

          $ {command} TEMPLATE_ID --json="config: json-format" --location=us-central1

        To create a job template with json format configuration file:

          $ {command} TEMPLATE_ID --file="config.json" --location=us-central1

        To create a job template with json format configuration and labels

          $ {command} TEMPLATE_ID --file="config.json" --location=us-central1 --labels=key=value
        """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddTemplateResourceArg(parser)
    flags.AddCreateTemplateFlags(parser)
    parser.display_info.AddFormat('json')
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    """Create a job template."""
    client = templates.TemplatesClient(self.ReleaseTrack())

    template_ref = args.CONCEPTS.template_id.Parse()

    parent_ref = template_ref.Parent()
    template_id = template_ref.jobTemplatesId

    return client.Create(parent_ref=parent_ref, template_id=template_id,
                         args=args)
