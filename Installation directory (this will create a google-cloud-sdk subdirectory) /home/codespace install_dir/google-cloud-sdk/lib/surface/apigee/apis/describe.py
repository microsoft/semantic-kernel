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
"""Command to describe an Apigee API proxy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


class Describe(base.DescribeCommand):
  """Describe an Apigee API proxy."""

  detailed_help = {
      "DESCRIPTION":
          """\
  {description}

  `{command}` shows metadata about an API proxy and its revisions.""",
      "EXAMPLES":
          """\
  To describe an API proxy called ``proxy-name'' given that its matching Cloud
  Platform project has been set in gcloud settings, run:

      $ {command} proxy-name

  To describe an API proxy called ``other-proxy-name'' in another project whose
  Apigee organization is named ``org-name'', run:

      $ {command} other-proxy-name --organization=org-name

  To describe an API proxy called ``proxy-name'' and include details on its
  revisions, run:

      $ {command} proxy-name --verbose

  To describe an API proxy called ``proxy-name'' as a JSON object, run:

      $ {command} proxy-name --format=json
  """
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument("--verbose", action="store_true",
                        help="Include proxy revision info in the description.")
    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      parser.add_argument("--revision",
                          help="Include proxy revision info for a specific "
                          "revision ID in the description.")
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.api",
        "API proxy to be described. To get a list of available API proxies, "
        "run `{parent_command} list`.",
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])

  def Run(self, args):
    """Run the describe command."""
    identifiers = args.CONCEPTS.api.Parse().AsDict()

    result = apigee.APIsClient.Describe(identifiers)

    # Must use vars(args) to check whether there's even a revision field in the
    # parsed args namespace. It's only present for ALPHA track.
    requested_revision = None
    if "revision" in vars(args):
      requested_revision = args.revision

    # If the user didn't ask for revision data, the response from
    # APIsClient.Describe() is good enough.
    if requested_revision is None and not args.verbose:
      return result

    rev_nums = result["revision"]
    if requested_revision is not None:
      if requested_revision not in rev_nums:
        message = "No revision %r among API %s's revisions: %s"%(
            requested_revision, identifiers["apisId"], rev_nums)
        raise exceptions.InvalidArgumentException("--revision", message)
      # No need to check whether this revision exists within the original list;
      # if there's no such revision, RevisionsClient will raise an appropriate
      # error.
      rev_nums = [requested_revision]

    revisions = []
    for revision in rev_nums:
      identifiers["revisionsId"] = revision
      revision_result = apigee.RevisionsClient.Describe(identifiers)
      del revision_result["name"]
      revisions.append(revision_result)
    del result["revision"]
    result["revisions"] = revisions

    return result
