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
"""Command to deploy an Apigee API proxy to an environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args
from googlecloudsdk.core import log


class Deploy(base.DescribeCommand):
  """Deploy an API proxy to an environment."""

  detailed_help = {
      "DESCRIPTION":
          """\
   {description}

  `{command}` installs an API proxy revision in an Apigee runtime environment.

  By default, the API proxy's base path must not already be in use by a deployed
  proxy in the target environment. To allow Apigee to undeploy any conflicting
  API proxy as part of the deployment, use the `--override` command.

  Once a particular revision of an API proxy has been deployed, that revision
  can no longer be modified. Any updates to the API proxy must be saved as a new
  revision.
  """,
      "EXAMPLES":
          """\
  To deploy the latest revision of the API proxy named ``demo'' to the ``test''
  environment, given that the API proxy and environment's matching Cloud
  Platform project has been set in gcloud settings, run:

    $ {command} --environment=test --api=demo

  To deploy revision 3 of that proxy, owned by an organization named ``my-org'',
  run, and replace any conflicting deployment that might already exist, run:

    $ {command} 3 --organization=my-org --environment=test --api=demo --override

  To deploy that proxy and print the resulting deployment as a JSON object, run:

    $ {command} 3 --organization=my-org --environment=test --api=demo --format=json
  """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        "--override",
        action="store_true",
        help=("Force the deployment of the new revision, overriding any " +
              "currently deployed revision that would conflict with it.\n\n" +
              "If an existing API proxy revision is deployed, set this flag " +
              "to ensure seamless deployment with zero downtime. In this " +
              "case, the existing revision remains deployed until the new " +
              "revision is fully deployed.\n\n" +
              "If unset, `{command}` will fail unless all conflicting API " +
              "proxies are first undeployed from the environment. To do " +
              "this, run `{parent_command} undeploy` on the conflicting " +
              "deployment."))

    help_text = {
        "api": ("API proxy to be deployed. To get a list of available API " +
                "proxies, run `{{parent_command}} list`."),
        "environment": ("Environment in which to deploy the API proxy. To " +
                        "get a list of available environments, run " +
                        "`{{grandparent_command}} environments list`."),
        "organization": ("Apigee organization of the proxy and environment. " +
                         "If unspecified, the Cloud Platform project's "
                         "associated organization will be used."),
    }
    fallthroughs = [defaults.GCPProductOrganizationFallthrough(),
                    defaults.StaticFallthrough("revision", "latest")]
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.environment.api.revision",
        "API proxy revision to be deployed and environment in which to deploy "
        "it. Revisions can either be a positive revision number, or the "
        "special value ``latest'', which will deploy the latest revision of "
        "the API proxy. If revision is unspecified, the default is ``latest''.",
        fallthroughs=fallthroughs,
        help_texts=help_text)

  def Run(self, args):
    """Run the deploy command."""
    identifiers = args.CONCEPTS.revision.Parse().AsDict()
    if identifiers["revisionsId"] == "latest":
      latest_revision = apigee.APIsClient.Describe(identifiers)["revision"][-1]
      log.status.Print("Using current latest revision `%s`"%latest_revision)
      identifiers["revisionsId"] = latest_revision

    result = apigee.APIsClient.Deploy(identifiers, args.override)
    return result
