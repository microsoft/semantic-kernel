# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Command to describe an Apigee API product."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


class Describe(base.DescribeCommand):
  """Describe an Apigee API product."""

  detailed_help = {
      "EXAMPLES":
          """
          To describe an API product called ``product-name'' in the active Cloud
          Platform project, run:

              $ {command} product-name

          To describe an API product called ``other-product'' in an Apigee
          organization called ``org-name'', run:

              $ {command} other-product --organization=org-name

          To describe an API product called ``product-name'' as a JSON object,
          run:

              $ {command} product-name --format=json
          """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser, "organization.product",
        "API product to be described. To get a list of available API products, "
        "run:\n\n\n"
        "    $ {parent_command} list\n\n",
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])

  def Run(self, args):
    """Run the describe command."""
    identifiers = args.CONCEPTS.product.Parse().AsDict()
    return apigee.ProductsClient.Describe(identifiers)
