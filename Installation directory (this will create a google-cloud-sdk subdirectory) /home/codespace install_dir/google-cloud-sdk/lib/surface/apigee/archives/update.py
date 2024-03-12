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
"""Command to update an archive deployment in an Apigee organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args
from googlecloudsdk.command_lib.util.args import labels_util


# DEVELOPER NOTE: This command inherits from the base.DescribeCommand (as
# opposed to the base.UpdateCommand) to get the print functionality of the
# return value (the base.UpdateCommand is silent) in order to print the updated
# archive deployment after the command is run.
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Update(base.DescribeCommand):
  """Update an existing Apigee archive deployment."""

  detailed_help = {
      "DESCRIPTION":
          """\
  {description}

  `{command}` updates an Apigee archive deployment.""",
      "EXAMPLES":
          """\
  To update the ``tag'' and ``rev'' labels of an archive deployment with the id
  ``abcdef01234'' in the Apigee environment called ``my-env'' using the active
  Cloud Platform project, run:

      $ {command} abcdef01234 --environment=my-env --update-labels=tag=my-tag,rev=1234

  To remove the ``dev'' label on an archive deployment with the id
  ``uvwxyz56789'', in the Apigee environment called ``my-env'', in an
  organization called ``my-org'', run:

      $ {command} uvwxyz56789 --environment=my-env --organization=my-org --remove-labels=dev

  To clear all labels on an archive deployment with the id ``mnop4321'', in
  the Apigee environment called ``my-env'', in an organization called
  ``my-org'', and return the updated archive deployment as a JSON object, run:

      $ {command} mnop4321 --environment=my-env --organization=my-org --clear-labels --format=json
  """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.environment.archive_deployment",
        help_text="Archive deployment to update. To get a list of "
        "existing archive deployments, run `{parent_command} list`.",
        argument_name="archive_deployment",
        positional=True,
        required=True,
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])
    # This adds the --update-labels, --remove-labels and --clear-labels flags.
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    """Run the update command."""
    labels_util.GetAndValidateOpsFromArgs(args)
    identifiers = args.CONCEPTS.archive_deployment.Parse().AsDict()
    # First get the existing lables by calling describe on the current archive.
    existing_archive = apigee.ArchivesClient.Describe(identifiers)
    # Modify the label set based on provided flag values.
    if "labels" in existing_archive and not args.clear_labels:
      new_labels = existing_archive["labels"]
    else:
      new_labels = {}
    if args.update_labels:
      new_labels.update(args.update_labels)
    if args.remove_labels:
      for label in args.remove_labels:
        if label in new_labels:
          del new_labels[label]
    labels_proto = {"labels": new_labels}
    return apigee.ArchivesClient.Update(identifiers, labels_proto)
