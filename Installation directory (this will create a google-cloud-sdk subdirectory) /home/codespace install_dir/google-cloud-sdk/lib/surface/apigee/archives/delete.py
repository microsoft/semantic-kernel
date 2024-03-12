# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Command to delete an archive deployment in an Apigee organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Delete an Apigee archive deployment."""

  detailed_help = {
      "DESCRIPTION":
          """\
  {description}

  `{command}` deletes an Apigee archive deployment.""",
      "EXAMPLES":
          """\
  To delete an archive deployment with the ID ``abcdefghijkl123456'' in the
  environment called ``my-env'' using the active Cloud Platform project, run:

      $ {command} abcdefghijkl123456 --environment=my-env

  To delete an archive deployment with the ID ``mnopqurstuvw654321'', in an
  environment called ``my-env'', in an organization called ``my-org'', run:

      $ {command} mnopqurstuvw654321 --environment=my-env --organization=my-org
  """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.environment.archive_deployment",
        "Apigee archive deployment to delete.",
        argument_name="archive_deployment",
        positional=True,
        required=True,
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])

  def Run(self, args):
    """Run the describe command."""
    identifiers = args.CONCEPTS.archive_deployment.Parse().AsDict()
    archive_id = identifiers["archiveDeploymentsId"]
    msg = "Archive deployment [{}] will be deleted.".format(archive_id)
    if console_io.PromptContinue(message=msg):
      apigee.ArchivesClient.Delete(identifiers)
      log.status.Print("Archive deployment [{}] deleted.".format(archive_id))
