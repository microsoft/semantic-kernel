# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Command to create an Apigee API product."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.apigee import argument_groups
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import prompts
from googlecloudsdk.command_lib.apigee import resource_args
from googlecloudsdk.core.console import console_io


class Deploy(base.DescribeCommand):
  """Create an Apigee API product."""

  detailed_help = {
      "DESCRIPTION":
          """
          Create an Apigee API product.

          `{command}` publishes a collection of API proxy resources as an API
          product.

          API products combine their underlying API proxies with quota settings
          and metadata, to deliver customized and productized API bundles to
          the developer community.

          API products enable the repackaging of APIs on-the-fly, without having
          to do any additional coding or configuration. Apigee recommends
          starting with a simple API product including only required elements,
          and then provisioning credentials to apps to enable them to start
          testing those APIs.

          At minimum, a new API product requires an internal name, access
          policy, and declaration of what environments and API proxies to
          include in the product. If these aren't provided, interactive calls
          will prompt for the missing values, and non-interactive calls will
          fail.
          """,
      "EXAMPLES":
          """
          To create a basic API product in the active Cloud Platform project by
          answering interactive prompts, run:

              $ {command}

          To create an API product that publicly exposes all API proxies
          deployed to the ``prod'' environment, run:

              $ {command} kitchen-sink --environments=prod --all-proxies --public-access

          To require manual approval of developers before they can access the
          new API product, run:

              $ {command} kitchen-sink --environments=prod --all-proxies --public-access --manual-approval

          To hide the new API product while still making it accessible to
          developers, run:

              $ {command} kitchen-sink --environments=prod --all-proxies --private-access

          To restrict the new API product to internal users only, run:

              $ {command} kitchen-sink --environments=prod --all-proxies --internal-access

          To expose all API proxies that are deployed to a URI fragment
          beginning with ``/v1'' or ``/v0'', run:

              $ {command} legacy --all-environments --resources="/v0/**#/v1/**" --public-access

          To expose a few specific API proxies on all URI paths where they're
          deployed, run:

              $ {command} consumer --environments=prod --apis=menu,cart,delivery-tracker --public-access

          To expose only those API calls that match both a set of API proxies
          and a set of API resources, run:

              $ {command} legacy-consumer --environments=prod --apis=menu,cart,delivery-tracker --resources="/v0/**#/v1/**" --public-access

          To impose a quota of 50 calls per half-hour on a new all-inclusive API
          product, and output the new API product as a JSON object, run:

              $ {command} kitchen-sink --environments=prod --all-proxies --public-access --quota=50 --quota-interval=30 --quota-unit=minute --format=json

          To specify a human-friendly display name and description for the
          product, run:

              $ {command} consumer --environments=prod --apis=menu,cart,delivery-tracker --public-access --display-name="Consumer APIs" --description="APIs for the consumer side of the delivery network: ordering food and tracking deliveries."
          """
  }

  @staticmethod
  def Args(parser):
    # Can't use fallthroughs for optional resource arguments, as they won't run
    # unless at least one argument from the set is provided.
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.product",
        "API product to be created. Characters in a product's internal name "
        "are restricted to: ```A-Za-z0-9._-$ %```.",
        validate=True,
        argument_name="INTERNAL_NAME",
        required=False)

    environment_group = parser.add_mutually_exclusive_group()

    environment_group.add_argument(
        "--environments",
        metavar="ENVIRONMENT",
        type=arg_parsers.ArgList(min_length=1),
        help=("Environments to which the API product is bound. Requests to "
              "environments that are not listed are rejected, preventing "
              "developers from accessing those resources through API Proxies "
              "deployed in another environment.\n\n"
              "For example, this can prevent resources associated with API "
              "proxies in a ``prod'' environment from also granting access to "
              "matching API proxies deployed in a ``test'' environment.\n\n"
              "To get a list of available environments, run:\n\n"
              "    $ {grandparent_command} environments list"))

    environment_group.add_argument(
        "--all-environments",
        dest="environments",
        action="store_const",
        const=[],
        help="Make all environments accessible through this API product.")

    parser.add_argument(
        "--display-name",
        help=("Name to be displayed in the UI or developer portal to "
              "developers registering for API access."))

    access_group = parser.add_mutually_exclusive_group()
    access_group.add_argument(
        "--public-access",
        dest="access",
        action="store_const",
        const="public",
        help=("Make this API product visible to developers in the Apigee "
              "developer portal."))
    access_group.add_argument(
        "--private-access",
        dest="access",
        action="store_const",
        const="private",
        help=("Hide this API product in the developer portal but make it "
              "accessible by external developers."))
    access_group.add_argument(
        "--internal-access",
        dest="access",
        action="store_const",
        const="internal",
        help="Prevent external access to this API product.")

    proxies_mutex_group = parser.add_mutually_exclusive_group(
        "Arguments specifying which API proxies and resources to expose.")

    proxies_mutex_group.add_argument(
        "--all-proxies",
        action="store_true",
        help=("Expose all available API proxies and their resources. Must be "
              "explicitly specified if neither `--apis` nor `--resources` is "
              "provided."))

    proxies_group = proxies_mutex_group.add_argument_group(
        "Arguments that restrict exposed API proxies. One or both of these may "
        "be specified if `--all-proxies` is not:")

    proxies_group.add_argument(
        "--apis",
        metavar="API",
        type=arg_parsers.ArgList(),
        help="""\
Comma-separated names of API proxies to which this API product is bound. Only
those API proxies will be accessible through the new API product.

If not provided, all deployed API proxies will be included in the product, so
long as they match the other parameters.

The API proxy names must already be deployed to the bound environments, or
creation of the API product will fail. To get a list of deployed API proxies,
run:

    $ {grandparent_command} deployments list

To deploy an API proxy, run:

    $ {grandparent_command} apis deploy""")

    # Resource paths conform to RFC 2396's segment format, so a "," may appear
    # in one, but a "#" will not. " " or "|" would also have worked, but would
    # have been harder to read in help text; spaces and pipes have special
    # meaning in usage strings.
    proxies_group.add_argument(
        "--resources",
        metavar="RESOURCE",
        type=argument_groups.HashDelimitedArgList(min_length=1),
        help="""\
API resources to be bundled in the API product, separated by `#` signs.

By default, the resource paths are mapped from the `proxy.pathsuffix` variable.

The proxy path suffix is defined as the URI fragment following the
ProxyEndpoint base path. For example, if ``/forecastrss'' is given as an element
of this list, and the base path defined for the API proxy is `/weather`, then
only requests to `/weather/forecastrss` are permitted by the API product.

Proxy paths can use asterisks as wildcards; `/**` indicates that all sub-URIs
are included, whereas a single asterisk indicates that only URIs one level
down are included.

By default, `/` supports the same resources as `/**` as well as the base path
defined by the API proxy.

For example, if the base path of the API proxy is `/v1/weatherapikey`, then
the API product supports requests to `/v1/weatherapikey` and to any sub-URIs,
such as `/v1/weatherapikey/forecastrss`, `/v1/weatherapikey/region/CA`, and so
on.

If not provided, all deployed API resources will be included in the product, so
long as they match the other parameters.

The API proxy resources must already be deployed to the bound environments, or
creation of the API product will fail.""")

    quota_group = parser.add_argument_group(
        ("To impose a quota limit on calls to the API product, specify all of "
         "the following:"))

    quota_group.add_argument(
        "--quota",
        type=int,
        help="""Number of request messages permitted per app by this API product
for the specified `--quota-interval` and `--quota-unit`.

For example, to create an API product that allows 50 requests every twelve hours
to every deployed API proxy, run:

    $ {command} PRODUCT --all-environments --all-proxies --public-access --quota=50 --quota-interval=12 --quota-unit=hour

If specified, `--quota-interval` and `--quota-unit` must be specified too.""")
    quota_group.add_argument(
        "--quota-interval",
        type=int,
        help=("Time interval over which the number of request messages is "
              "calculated.\n\n"
              "If specified, `--quota` and `--quota-unit` must be specified "
              "too."))
    quota_group.add_argument(
        "--quota-unit",
        choices=["minute", "hour", "day", "month"],
        help=("Time unit for `--quota-interval`.\n\n"
              "If specified, `--quota` and `--quota-interval` must be "
              "specified too."))

    parser.add_argument(
        "--description",
        help=("Overview of the API product. Include key information about the "
              "API product that is not captured by other fields."))

    parser.add_argument(
        "--manual-approval",
        action="store_true",
        help=("Require manual approval of developer requests to access this "
              "API product before their consumer keys can be used. If unset, "
              "the consumer key is generated in an \"approved\" state and can "
              "be used immediately."))

    parser.add_argument(
        "--oauth-scopes",
        metavar="SCOPE",
        type=arg_parsers.ArgList(),
        help=("Comma-separated list of OAuth scopes that are validated at "
              "runtime. Apigee validates that the scopes in any access token "
              "presented match the scopes defined in the OAuth policy "
              "assoicated with the API product."))

    parser.add_argument(
        "--attributes",
        metavar="NAME=VALUE",
        type=arg_parsers.ArgDict(max_length=17),
        help=("Key-value attribute pairs that may be used to extend the "
              "default API product profile with customer-specific metadata. Up "
              "to 17 attributes can be specified."))

  def Run(self, args):
    """Run the deploy command."""
    if args.organization is None:
      args.organization = defaults.OrganizationFromGCPProduct()

    if console_io.CanPrompt():
      if args.organization is None:

        def _ListOrgs():
          response = apigee.OrganizationsClient.List()
          if "organizations" in response:
            return [item["organization"] for item in response["organizations"]]
          else:
            return []

        args.organization = prompts.ResourceFromFreeformPrompt(
            "organization",
            "the organization in which to create the API product", _ListOrgs)

      if args.INTERNAL_NAME is None:
        product_matcher = resource_args.ValidPatternForEntity("product")
        valid_product = lambda name: product_matcher.search(name) is not None
        args.INTERNAL_NAME = console_io.PromptWithValidator(
            valid_product, "Empty or invalid API product name.",
            "Enter an internal name for the new API product: ")

      org_identifier = {"organizationsId": args.organization}
      if args.environments is None:
        list_envs = lambda: apigee.EnvironmentsClient.List(org_identifier)
        choice = console_io.PromptChoice(
            ["Include all environments", "Choose environments to include"],
            prompt_string=("What environments should be accessible in the API "
                           "product?"))
        if choice == 0:
          args.environments = []
        else:
          args.environments = prompts.ResourceListFromPrompt(
              "environment", list_envs)

      if not args.apis and not args.resources and not args.all_proxies:
        choice = console_io.PromptChoice(
            [
                "Include all API proxies",
                "Choose API proxies and/or basepaths to include"
            ],
            prompt_string=("What API proxies should be accessible in the API "
                           "product?"))
        if choice == 0:
          args.all_proxies = True
        else:

          def _ListDeployedProxies():
            response = apigee.DeploymentsClient.List(org_identifier)
            return sorted(list(set(item["apiProxy"] for item in response)))

          args.apis = prompts.ResourceListFromPrompt(
              "api", _ListDeployedProxies, "Include all deployed API proxies")

          resource_options = [
              "Restrict proxy access by resource path",
              "Include all resource paths of the product's API proxies"
          ]
          if console_io.PromptChoice(resource_options) == 0:
            args.resources = prompts.ListFromFreeformPrompt(
                "Enter a resource path that should be included: ",
                "Include another resource path",
                "Include all resource paths of the product's API proxies")
          else:
            args.resources = []

          if not args.resources and not args.apis:
            # User explicitly chose to include all proxies and resources.
            args.all_proxies = True

      if args.access is None:
        option = console_io.PromptChoice([
            "Public - visible in the Apigee developer portal",
            ("Private - callable by external developers but not visible in the "
             "Apigee developer portal"),
            "Internal - not callable by external developers"
        ],
                                         message="Choose an access policy.")
        args.access = ["public", "private", "internal"][option]

    if args.environments is None:
      raise exceptions.OneOfArgumentsRequiredException(
          ["--environments", "--all-environments"],
          "All API products must include at least one environment.")

    if args.access is None:
      raise exceptions.OneOfArgumentsRequiredException([
          "--public-access", "--private-access", "--internal-access"
      ], "All API products must specify whether they can be publicly accessed.")

    if not args.apis and not args.resources and not args.all_proxies:
      raise exceptions.OneOfArgumentsRequiredException(
          ["--apis", "--resources", "--all-proxies"],
          "All API products must include at least one API proxy or resource.")

    quota_args_missing = [
        arg for arg in vars(args) if "quota" in arg and vars(args)[arg] is None
    ]
    if quota_args_missing:
      if len(quota_args_missing) < 3:
        raise exceptions.RequiredArgumentException(
            "--" + quota_args_missing[0].replace("_", "-"),
            "Must specify all quota arguments to use quotas.")
    else:
      args.quota = "%d" % args.quota
      args.quota_interval = "%d" % args.quota_interval

    attributes = [{"name": "access", "value": args.access}]
    if args.attributes:
      for key in args.attributes:
        attributes.append({"name": key, "value": args.attributes[key]})

    identifiers = args.CONCEPTS.internal_name.Parse().AsDict()

    if args.display_name is None:
      args.display_name = identifiers["apiproductsId"]

    product = apigee.ProductsInfo(
        name=identifiers["apiproductsId"],
        displayName=args.display_name,
        approvalType="manual" if args.manual_approval else "auto",
        attributes=attributes,
        description=args.description,
        apiResources=args.resources if args.resources else None,
        environments=args.environments if args.environments else None,
        proxies=args.apis if args.apis else None,
        quota=args.quota,
        quotaInterval=args.quota_interval,
        quotaTimeUnit=args.quota_unit,
        scopes=args.oauth_scopes)
    return apigee.ProductsClient.Create(identifiers, product)
