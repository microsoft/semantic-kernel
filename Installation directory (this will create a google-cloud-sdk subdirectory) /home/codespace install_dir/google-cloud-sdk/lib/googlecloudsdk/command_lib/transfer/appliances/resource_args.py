# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Shared resource flags for Transfer Appliance commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.transfer.appliances import regions
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


APPLIANCES_COLLECTION = 'transferappliance.projects.locations.appliances'
ORDERS_COLLECTION = 'transferappliance.projects.locations.orders'


class ResourceVerb(enum.Enum):
  DELETE = 'delete'
  DESCRIBE = 'describe'
  LIST = 'list'
  UPDATE = 'update'


def appliance_attribute_config(name='appliance'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The appliance affiliated with the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='name')


def order_attribute_config(name='order'):
  return concepts.ResourceParameterAttributeConfig(
      name=name,
      help_text='The order affiliated with the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='name')


def region_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text='The region affiliated with the {resource}.',
      fallthroughs=[deps.ArgFallthrough('--region')])


def get_appliance_resource_spec(resource_name='appliance'):
  return concepts.ResourceSpec(
      APPLIANCES_COLLECTION,
      resource_name=resource_name,
      appliancesId=appliance_attribute_config(name=resource_name),
      locationsId=region_attribute_config(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def get_order_resource_spec(resource_name='order'):
  return concepts.ResourceSpec(
      ORDERS_COLLECTION,
      resource_name=resource_name,
      ordersId=order_attribute_config(name=resource_name),
      locationsId=region_attribute_config(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def _add_region_flag(parser, verb):
  """Add region flag for appliances/orders.

  Normally we'd rely on the argument output by region_attribute_config() but
  we can set "choices" and convert the value to lower if we add it this way.

  Args:
    parser (arg_parse.Parser): The parser for the command.
    verb (ResourceVerb): The action taken on the resource, such as 'update'.
  """
  parser.add_argument(
      '--region',
      choices=regions.CLOUD_REGIONS,
      type=str.lower,
      help='The location affiliated with the appliance order to {}.'.format(
          verb.value))


def add_appliance_resource_arg(parser, verb):
  """Add a resource argument for a transfer appliance.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser (arg_parse.Parser): The parser for the command.
    verb (ResourceVerb): The action taken on the resource, such as 'update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'appliance',
      get_appliance_resource_spec(),
      'The appliance to {}.'.format(verb.value),
      flag_name_overrides={'region': ''},
      prefixes=True,
      required=True).AddToParser(parser)
  _add_region_flag(parser, verb)


def add_order_resource_arg(parser, verb):
  """Add a resource argument for a transfer appliance order.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser (arg_parse.Parser): The parser for the command.
    verb (ResourceVerb): The action taken on the resource, such as 'update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'order',
      get_order_resource_spec(),
      'The order to {}.'.format(verb.value),
      flag_name_overrides={'region': ''},
      prefixes=True,
      required=True).AddToParser(parser)
  _add_region_flag(parser, verb)


def add_clone_resource_arg(parser):
  """Add a resource argument for cloning a transfer appliance.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser (arg_parse.Parser): The parser for the command.
  """
  concept_parsers.ConceptParser.ForResource(
      '--clone',
      get_order_resource_spec(),
      'The order to clone.',
      prefixes=True,
      required=False).AddToParser(parser)


def _get_appliance_uri(appliance):
  return resources.REGISTRY.Parse(
      appliance.name,
      params={'projectsId': properties.VALUES.core.project.Get()},
      collection=APPLIANCES_COLLECTION).SelfLink()


def _get_order_uri(order):
  return resources.REGISTRY.Parse(
      order.name,
      params={'projectsId': properties.VALUES.core.project.Get()},
      collection=ORDERS_COLLECTION).SelfLink()


def add_list_resource_args(parser, listing_orders=True):
  """Add both order and appliance resource arguments for list commands.

  Args:
    parser (arg_parse.Parser): The parser for the command.
    listing_orders (bool): Toggles the help text phrasing to match either orders
      or appliances being the resource being listed.
  """
  verb = ResourceVerb.LIST
  primary_help = 'The {} to {}.'
  secondary_help = 'The {} associated with the {} to {}.'
  if listing_orders:
    orders_help = primary_help.format('orders', verb.value)
    appliances_help = secondary_help.format('appliances', 'orders', verb.value)
    parser.display_info.AddUriFunc(_get_order_uri)
  else:
    appliances_help = primary_help.format('appliances', verb.value)
    orders_help = secondary_help.format('orders', 'appliances', verb.value)
    parser.display_info.AddUriFunc(_get_appliance_uri)

  arg_specs = [
      presentation_specs.ResourcePresentationSpec(
          '--appliances',
          get_appliance_resource_spec('appliances'),
          appliances_help,
          flag_name_overrides={'region': ''},
          plural=True,
          prefixes=False),
      presentation_specs.ResourcePresentationSpec(
          '--orders',
          get_order_resource_spec('orders'),
          orders_help,
          flag_name_overrides={'region': ''},
          plural=True,
          prefixes=True)
  ]

  concept_parsers.ConceptParser(arg_specs).AddToParser(parser)
  _add_region_flag(parser, verb)


def _get_filter_clause_from_resources(filter_key, resource_refs):
  if not resource_refs:
    return ''
  filter_list = [
      '{}:{}'.format(filter_key, ref.RelativeName()) for ref in resource_refs
  ]
  resource_list = ' OR '.join(filter_list)
  return '({})'.format(resource_list)


def parse_list_resource_args_as_filter_string(args, listing_orders=True):
  """Parses list resource args as a filter string.

  Args:
    args (parser_extensions.Namespace): the parsed arguments for the command.
    listing_orders (bool): Toggles the appropriate keys for order and appliance
      depending on which resource is primarily being listed.

  Returns:
    A filter string.
  """
  filter_list = [args.filter] if args.filter else []
  if args.IsSpecified('orders'):
    order_refs = args.CONCEPTS.orders.Parse()
    if order_refs:
      filter_key = 'name' if listing_orders else 'order'
      filter_list.append(_get_filter_clause_from_resources(
          filter_key, order_refs))
  if args.IsSpecified('appliances'):
    appliance_refs = args.CONCEPTS.appliances.Parse()
    if appliance_refs:
      filter_key = 'appliances' if listing_orders else 'name'
      filter_list.append(_get_filter_clause_from_resources(
          filter_key, appliance_refs))
  return ' AND '.join(filter_list)


def get_parent_string(region):
  """Returns a presentation string for list and create calls, given a region."""
  project = properties.VALUES.core.project.Get()
  return 'projects/{}/locations/{}'.format(project, region or '-')


def get_appliance_name(locations_id, appliances_id):
  """Returns an appliance name to locations and appliances ID."""
  return resources.Resource.RelativeName(
      resources.REGISTRY.Create(
          APPLIANCES_COLLECTION,
          appliancesId=appliances_id,
          locationsId=locations_id,
          projectsId=properties.VALUES.core.project.Get()))


def get_order_name(locations_id, orders_id):
  """Returns an appliance name to locations and orders ID."""
  return resources.Resource.RelativeName(
      resources.REGISTRY.Create(
          ORDERS_COLLECTION,
          ordersId=orders_id,
          locationsId=locations_id,
          projectsId=properties.VALUES.core.project.Get()))
