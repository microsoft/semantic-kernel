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
"""Command to delete an Apigee organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DescribeCommand):
  """Delete an Apigee organization."""

  detailed_help = {
      "DESCRIPTION":
          """
          {description}

          `{command}` deletes an organization and all resources inside it. This
          is currently only supported for trial organizations.

          This is a long running operation. Once organization provisioning has
          begun, `{command}` will exit, returning the operation's ID and initial
          status. To continue monitoring the operation, run
          `{grandparent_command} operations describe OPERATION_NAME`.

          """,
      "EXAMPLES":
          """
          To delete an organization called ``my-org'', run:

              $ {command} my-org

          To delete an organization called ``my-org'', and print only the name
          of the launched operation, run:

              $ {command} my-org --format="value(name)"
          """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser, "organization", "The trial organization to be deleted.")

  def Run(self, args):
    """Run the delete command."""
    identifiers = args.CONCEPTS.organization.Parse().AsDict()
    return apigee.OrganizationsClient.Delete(identifiers)
