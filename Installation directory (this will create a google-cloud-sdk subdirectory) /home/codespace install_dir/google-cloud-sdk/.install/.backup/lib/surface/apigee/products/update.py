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
"""Command to modify an Apigee API product."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.apigee import argument_groups
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


class Update(base.DescribeCommand):
  """Update an existing Apigee API product."""

  detailed_help = {
      "DESCRIPTION":
          """
          {description}

          `{command}` applies a set of modifications to an existing API product.

          To create a new API product, run:

              $ {parent_command} create
          """,
      "EXAMPLES":
          """
          To update the display name of the API product with the internal name ``my-prod'', run:

              $ {command} my-prod --display-name="Example Project"

          To update the description of the API product, run:

              $ {command} my-prod --description="This API is famous for appearing in a YouTube video."

          To remove the API product's description, run:

              $ {command} my-prod --clear-description

          To remove manual approval requirements from the API and change its access level to public, run:

              $ {command} my-prod --public-access --automatic-approval

          To impose a quota of 45 calls per minute per application on the API product, run:

              $ {command} my-prod --quota=45 --quota-interval=1 --quota-unit=minute

          To remove a quota on the API product and switch it to unlisted access with manual approval, run:

              $ {command} my-prod --manual-approval --private-access --clear-quota

          To set the API product's custom attribute ``foo'' to the value ``bar'', updating that attribute if it exists and creating it if it doesn't, and remove the attribute ``baz'' if it exists, run:

              $ {command} my-prod --add-attribute="foo=bar"  --remove-attribute=baz

          To update the list of API proxies included in the API product, run:

              $ {command} my-prod --add-api=NEW_ONE,NEW_TWO --remove-api=OLD_ONE,OLD_TWO

          To switch the API product to including all ``test'' environment APIs no matter what API proxy or resource they expose, run:

              $ {command} my-prod --add-environment=test --all-apis --all-resources

          To update the list of API resources included in the API product, and
          output the updated API product as a JSON object, run:

              $ {command} my-prod --add-resource="NEW_ONE#NEW_TWO" --remove-resource="OLD_ONE#OLD_TWO" --format=json
          """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.product",
        "API product to be updated. To get a list of available API products, "
        "run:\n\n\n"
        "    $ {parent_command} list\n\n",
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])

    argument_groups.AddEditableListArgument(
        parser,
        "environment",
        "environments",
        "Environments to which the API product is bound. Requests to "
        "environments that are not listed are rejected, preventing developers "
        "from accessing those resources even if they can access the same API "
        "proxies in another environment.\n\n"
        "For example, this can be used to prevent applications with access to "
        "production APIs from accessing the alpha or beta versions of those "
        "APIs.\n\n"
        "To get a list of available environments, run:\n\n"
        "    $ {grandparent_command} environments list",
        clear_arg="--all-environments",
        clear_help="Make all environments accessible through this API product.",
        dest="environments")

    parser.add_argument(
        "--display-name",
        dest="set_displayName",
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

    argument_groups.AddEditableListArgument(
        parser,
        "API",
        "APIs",
        """API proxies to which this API product is bound. Only those API
proxies will be accessible through the API product.

The API proxy names must already be deployed to the bound environments, or
creation of the API product will fail. To get a list of deployed API proxies,
run:

    $ {grandparent_command} deployments list

To deploy an API proxy, run:

    $ {grandparent_command} apis deploy.""",
        dest="proxies",
        clear_arg="--all-apis",
        clear_help="Include all deployed API proxies in the product, so long "
        "as they match the other parameters.")
    argument_groups.AddEditableListArgument(
        parser,
        "resource",
        "resources",
        """API resources to be bundled in the API product.

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

The API proxy resources must already be deployed to the bound environments, or
creation of the API product will fail.""",
        dest="apiResources",
        collector_type=argument_groups.HashDelimitedArgList(),
        clear_arg="--all-resources",
        clear_help="Include all deployed API resources in the product, so long "
        "as they match the other parameters.")

    quota_mutex = parser.add_mutually_exclusive_group()
    quota_group = quota_mutex.add_argument_group(
        ("To impose a quota limit on calls to the API product, specify all of "
         "the following:"))

    quota_group.add_argument(
        "--quota",
        type=int,
        help="""Number of request messages permitted per app by this API
product for the specified `--quota-interval` and `--quota-unit`.

For example, `--quota=50`, `--quota-interval=12`, and `--quota-unit=hour` means
50 requests are allowed every 12 hours.""")
    quota_group.add_argument(
        "--quota-interval",
        type=int,
        help=("Time interval over which the number of "
              "request messages is calculated."))
    quota_group.add_argument(
        "--quota-unit",
        choices=["minute", "hour", "day", "month"],
        help=("Time unit for `--quota-interval`."))

    quota_mutex.add_argument(
        "--clear-quota",
        action="store_true",
        help="Remove any quota currently imposed on the API product.")

    argument_groups.AddClearableArgument(
        parser, "description",
        "Overview of the API product. Include key information about the API "
        "product that is not captured by other fields.",
        "Remove the API product's description.")

    approval_group = parser.add_mutually_exclusive_group()
    approval_group.add_argument(
        "--manual-approval",
        action="store_const",
        const="manual",
        dest="set_approvalType",
        help=("Require manual approval of developer requests to access this "
              "API product before their consumer keys can be used."))
    approval_group.add_argument(
        "--automatic-approval",
        action="store_const",
        const="auto",
        dest="set_approvalType",
        help=("Allow developers to generate approved consumer keys without "
              "waiting for approval."))

    argument_groups.AddEditableListArgument(
        parser,
        "OAuth scope",
        "OAuth scopes",
        "Comma-separated list of OAuth scopes that are validated at runtime. "
        "Apigee validates that the scopes in any access token presented match "
        "the scopes defined in the OAuth policy assoicated with the API "
        "product.",
        dest="scopes")

    argument_groups.AddEditableListArgument(
        parser,
        "attribute",
        "attributes",
        "Key-value attribute pairs that may be used to extend the default API "
        "product profile with customer-specific metadata. Up to 17 attributes "
        "can be specified.",
        dict_like=True,
        add_metavar="NAME=VALUE",
        remove_metavar="NAME")

  def Run(self, args):
    """Run the update command."""
    identifiers = args.CONCEPTS.product.Parse().AsDict()

    product = apigee.ProductsClient.Describe(identifiers)

    ## Quota related.
    if args.quota is not None:
      product["quota"] = "%d" % args.quota
    if args.quota_interval is not None:
      product["quotaInterval"] = "%d" % args.quota_interval
    if args.quota_unit:
      product["quotaTimeUnit"] = args.quota_unit
    # Check that AFTER these updates, all three quota settings are present.
    quota_field_names = ["quota", "quotaInterval", "quotaTimeUnit"]
    quota_fields_exist = [field in product for field in quota_field_names]
    if any(quota_fields_exist) and not all(quota_fields_exist):
      if not args.quota_interval:
        missing_arg = "--quota-interval"
      elif not args.quota_unit:
        missing_arg = "--quota-unit"
      else:
        missing_arg = "--quota"
      raise exceptions.RequiredArgumentException(
          missing_arg,
          "Products with quotas must specify all three quota settings.")
    if args.clear_quota:
      del product["quota"]
      del product["quotaInterval"]
      del product["quotaTimeUnit"]
      args.clear_quota = None

    ## Attribute list related
    attribute_list = product["attributes"] if "attributes" in product else []
    attribute_list = [(item["name"], item["value"]) for item in attribute_list]
    attributes = collections.OrderedDict(attribute_list)

    if args.add_attribute is not None:
      add_attributes = args.add_attribute
      if ("access" in add_attributes and
          add_attributes["access"] not in ["public", "private", "internal"]):
        raise exceptions.BadArgumentException(
            "--add-attribute",
            "The `access` attribute must be set to one of \"public\", "
            "\"private\", or \"internal\".")
      attributes.update(add_attributes)
      args.add_attribute = None

    if args.remove_attribute is not None:
      for sublist in args.remove_attribute:
        if "access" in sublist and not args.access:
          raise exceptions.BadArgumentException(
              "--remove-attribute", "The `access` attribute is required.")
        for item in sublist:
          if item in attributes:
            del attributes[item]
      args.remove_attribute = None

    if args.clear_attributes:
      # It doesn't make sense that the server would return an API product
      # without access rules, but the API physically allows it, and an
      # unexpected response mustn't cause gcloud to crash.
      access = attributes["access"] if "access" in attributes else None
      attributes = {"access": access} if access else {}
      args.clear_attributes = None

    if args.access:
      attributes["access"] = args.access

    attribute_dict = lambda item: {"name": item[0], "value": item[1]}
    attributes_dicts = [attribute_dict(item) for item in attributes.items()]
    product["attributes"] = attributes_dicts

    # Python lint rules don't allow direct comparison with the empty string;
    # detect it by process of elimination (not truthy, not None) instead.
    if not args.set_displayName and args.set_displayName is not None:
      raise exceptions.BadArgumentException(
          "--display-name", "An API product's display name cannot be blank.")

    # The rest of the fields can be filled in directly from arguments.
    emptied_lists = set()
    arg_dict = vars(args)
    for key, value in arg_dict.items():
      if value is None or "_" not in key:
        continue
      label, field = key.split("_", 1)
      if label == "add":
        if field not in product:
          product[field] = []
        for sublist in value:
          product[field] += sublist
      elif label == "remove" and field in product:
        for sublist in value:
          for item in sublist:
            if item in product[field]:
              product[field].remove(item)
              if not product[field]:
                # This removed the last item from `field`. None it out so it's
                # not sent to the server in the update call.
                product[field] = None
                emptied_lists.add(field)
      elif label == "set":
        product[field] = value
      elif label == "clear" and value and field in product:
        del product[field]

    # For API proxies, resources, and environments, don't allow the user to
    # empty the list without explicitly stating that they intend to include ALL
    # proxies/resources/environments. Otherwise the user may get results they
    # didn't expect (removing a proxy -> the number of proxies exposed goes up).
    if "proxies" in emptied_lists:
      # User removed the last API proxy but didn't say to clear proxies. The
      # result may not be what the user expected.
      raise exceptions.BadArgumentException(
          "--remove-api",
          "An API product must include at least one API proxy, or else all "
          "API proxies will implicitly be included. If this was intended, use "
          "[--all-apis] instead of removing APIs individually.")

    if "apiResources" in emptied_lists:
      raise exceptions.BadArgumentException(
          "--remove-resource",
          "An API product must include at least one API resource, or else all "
          "resources will implicitly be included. If this was intended, use "
          "[--all-resources] instead of removing resources individually.")

    if "environments" in emptied_lists:
      raise exceptions.BadArgumentException(
          "--remove-environment",
          "An API product must include at least one environment, or else all "
          "environments will implicitly be included. If this was intended, use "
          "[--all-environments] instead of removing environments individually.")

    # Clean up the product structure; remove any irrelevant fields that might
    # have been populated by global gcloud args, and populate any empty fields
    # with None.
    product = {
        key: (product[key] if key in product else None)
        for key in apigee.ProductsInfo._fields
    }

    product["name"] = identifiers["apiproductsId"]

    updated_product = apigee.ProductsInfo(**product)
    return apigee.ProductsClient.Update(identifiers, updated_product)
