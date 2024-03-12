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
"""Command to list Apigee API proxy deployments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


class List(base.ListCommand):
  """List Apigee API proxy deployments."""

  detailed_help = {
      "DESCRIPTION":
          """\
          {description}

          `{command}` lists deployments of API proxies, optionally filtered by
          environment, proxy name, proxy revision, or a combination of these.
          """,
      "EXAMPLES":
          """
          To list all deployments for the active Cloud Platform project, run:

              $ {command}

          To list all deployments in an Apigee organization called ``my-org'',
          run:

              $ {command} --organization=my-org

          To list all deployments of an API proxy called ``my-proxy'' in the
          active Cloud Platform project, run:

              $ {command} --api=my-proxy

          To list all deployments to the ``test'' environment of the active
          Cloud Platform project, formatted as a JSON array, run:

              $ {command} --environment=test --format=json

          To list all deployments of ``my-proxy'' to the ``test'' environment in
          an Apigee organization called ``my-org'', run:

              $ {command} --organization=my-org --api=my-proxy --environment=test
          """
  }

  @staticmethod
  def Args(parser):
    help_text = {
        "api": ("The API proxy whose deployments should be listed. If not "
                "provided, all proxies will be listed. To get a list of "
                "existing API proxies, run "
                "`{{grandparent_command}} apis list`."),
        "environment": ("The environment whose deployments should be listed. "
                        "If not provided, all environments will be listed. "
                        "To get a list of available environments, run "
                        "`{{grandparent_command}} environments list`."),
        "organization": ("The organization whose deployments should be listed."
                         "If unspecified, the Cloud Platform project's "
                         "associated organization will be used."),
    }

    # When Calliope parses a resource's resource arguments, it interprets them
    # as an all-or-nothing whole; if any of them are not provided the whole
    # resource defaults to None.
    #
    # Thus, to make individual parts of the search path optional for the user
    # while accepting others, fallthrough logic for those arguments must be
    # present to return a placeholder value that can be recognized after parsing
    # and interpreted as "no value provided".
    #
    # Unfortunately, `None` won't work as the placeholder, because a fallthrough
    # class returning "None" means it was unable to provide a value at all.
    # Thus, some other value must be chosen.
    fallthroughs = [
        defaults.GCPProductOrganizationFallthrough(),
        # For `revision`, the placeholder MUST be a string, because gcloud
        # concepts will try to parse it as a URL or fully qualified path, and
        # will choke on non-string values. This should be safe as all legitimate
        # revisions are numeric.
        defaults.StaticFallthrough("revision", "all"),
        # For other arguments, the placeholder must not be a string; any string
        # provided here might collide with a real environment or API name. Use
        # the Python builtin function all() as a convenient, idiomatic
        # alternative.
        defaults.StaticFallthrough("environment", all),
        defaults.StaticFallthrough("api", all),
    ]
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.environment.api.revision",
        "API proxy revision and environment whose deployments should be "
        "listed. Providing a REVISION is only valid if API is also specified. "
        "If no REVISION is provided, all deployed revisions that match the "
        "other arguments will be included.",
        positional=False,
        required=True,
        fallthroughs=fallthroughs,
        help_texts=help_text)
    parser.display_info.AddFormat("table(environment,apiProxy,revision)")

  def Run(self, args):
    """Run the list command."""
    identifiers = args.CONCEPTS.revision.Parse().AsDict()
    if identifiers["apisId"] is all:
      if identifiers["revisionsId"] != "all":
        raise exceptions.RequiredArgumentException(
            "--api", "Filtering by revision requires specifying its API.")
      del identifiers["apisId"]
    if identifiers["environmentsId"] is all:
      del identifiers["environmentsId"]
    if identifiers["revisionsId"] == "all":
      del identifiers["revisionsId"]

    return apigee.DeploymentsClient.List(identifiers)
