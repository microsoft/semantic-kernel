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
"""Command to describe an Apigee API deployment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import errors
from googlecloudsdk.command_lib.apigee import resource_args


class Describe(base.DescribeCommand):
  """Describe an Apigee API proxy deployment."""

  detailed_help = {
      "DESCRIPTION":
          """\
  {description}

  `{command}` retrieves the status of a specific API proxy's deployment to a
  specific environment.
          """,
      "EXAMPLES":
          """\
  To get the status of a deployment in the active Cloud Platform project, which
  deploys ``my-proxy'' into the ``prod'' environment, run:

      $ {command} --api=my-proxy --environment=prod

  To get the status of that deployment as a JSON object, run:

      $ {command} --api=my-proxy --environment=prod --format=json

  To get the status of a deployment in an organization called ``my-org'', which
  deploys version 3 of the proxy ``my-proxy'' into the ``test'' environment,
  run:

      $ {command} 3 --organization=my-org --environment=test --api=my-proxy
          """
  }

  @staticmethod
  def Args(parser):
    help_text = {
        "api": "Deployed API proxy.",
        "environment": "Environment in which the proxy was deployed.",
        "organization": ("Apigee Organization of the proxy and environment. If "
                         "unspecified, the Cloud Platform project's associated "
                         "organization will be used."),
    }
    fallthroughs = [
        defaults.GCPProductOrganizationFallthrough(),
        defaults.StaticFallthrough("revision", "auto")
    ]
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.environment.api.revision",
        """\
API proxy revision and environment of the deployment to be described.


To get a list of deployed proxies and their environments, run:

    $ {parent_command} list

REVISION can either be a positive revision number, or the special value
``auto'', which will choose whichever revision of API is currently deployed in
ENVIRONMENT, or return an error if more than one revision is deployed.


If REVISION is unspecified, the default is ``auto''.

""",
        fallthroughs=fallthroughs,
        help_texts=help_text)

  def Run(self, args):
    """Run the describe command."""
    identifiers = args.CONCEPTS.revision.Parse().AsDict()
    if identifiers["revisionsId"] == "auto":
      del identifiers["revisionsId"]
      defaults.FallBackToDeployedProxyRevision(identifiers)

    # Deployments have no identifier of their own, so the API to get deployment
    # details looks like a List call with all possible parents specified.
    deployments = apigee.DeploymentsClient.List(identifiers)
    if not deployments:
      raise errors.EntityNotFoundError("deployment", identifiers, "GET")
    return deployments[0]
