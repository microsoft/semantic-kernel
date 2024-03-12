# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Declarative Resource Map Update Utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.declarative.clients import kcc_client
from googlecloudsdk.command_lib.util.resource_map import base
from googlecloudsdk.command_lib.util.resource_map import resource_map_update_util
from googlecloudsdk.command_lib.util.resource_map.declarative import declarative_map
from googlecloudsdk.core import name_parsing


class KrmToApitoolsResourceNameError(base.ResourceMapError):
  """General Purpose Exception for the Update Utility."""


def build_collection_map():
  collection_map = {}
  api_names, api_versions = get_apitools_collections()
  for api_name in api_names:
    collection_map[api_name] = get_collection_names(api_name,
                                                    api_versions[api_name])
  return collection_map


def get_apitools_collections():
  """Returns all apitools collections and associated versions."""
  collection_api_names = set()
  collection_api_versions = {}
  for api in registry.GetAllAPIs():
    collection_api_names.add(api.name)
    if api.name not in collection_api_versions:
      collection_api_versions[api.name] = []
    collection_api_versions[api.name].append(api.version)

  return collection_api_names, collection_api_versions


# TODO(b/197004182) Refactor for common use between maps
def get_collection_names(api_name, api_versions):
  """Gets collection names for all collections in each specified version.

  Args:
    api_name: Name of the API to return collection names for.
    api_versions: Desired api versions to return collections for.

  Returns:
    collection_names: Names of every registered apitools collection.
  """
  collection_names = set()
  for version in api_versions:
    resource_collections = [
        registry.APICollection(c)
        for c in apis_internal._GetApiCollections(api_name, version)  # pylint:disable=protected-access
    ]
    for resource_collection in resource_collections:
      collection_names.add(resource_collection.name)
  return collection_names


# Config Connector resources with no corresponding apitools collections.
_ALLOWED_MISMATCHES = frozenset({('bigtable', 'BigtableGCPolicy'),
                                 ('compute', 'ComputeNetworkPeering'),
                                 ('compute', 'ComputeProjectMetadata'),
                                 ('compute', 'ComputeRouterInterface'),
                                 ('compute', 'ComputeRouterNAT'),
                                 ('compute', 'ComputeRouterPeer'),
                                 ('sql', 'SQLUser'),
                                 ('resourcemanager', 'ResourceManagerPolicy'),
                                 ('servicenetworking',
                                  'ServiceNetworkingConnection')})


def generate_cc_update_map():
  """Generates the map used to update the resource map with cc metadata.

  The returned update map will have an analogous structure to the resource map.
  Each resource will contain the associated metadata values to be applied to the
  resource map.

  Raises:
    KrmToApitoolsResourceNameError: Raised if mismatches occur that are not
      present in _ALLOWED_MISMATCHES.

  Returns:
    Update map containing the config connector support metadata.
  """
  config_connector_data = kcc_client.KccClient().ListResources()
  apitools_resource_map = build_collection_map()
  update_map = {}
  resources_already_seen = set()
  unmatched_resources = set()

  for resource_spec in config_connector_data:
    krm_group = resource_spec['GVK']['Group'].split('.')[0]
    krm_kind = resource_spec['GVK']['Kind']

    apitools_api_name = krm_group_to_apitools_api_name(
        krm_group, (apitools_resource_map.keys()))
    try:
      apitools_collection_name = krm_kind_to_apitools_collection_name(
          krm_kind, krm_group,
          set(apitools_resource_map[apitools_api_name]))
    except KrmToApitoolsResourceNameError:
      if (krm_group, krm_kind) not in _ALLOWED_MISMATCHES:
        unmatched_resources.add((krm_group, krm_kind))
      continue

    if (apitools_api_name, apitools_collection_name) in resources_already_seen:
      if not resource_spec['ResourceNameFormat']:
        continue
    resources_already_seen.add((apitools_api_name, apitools_collection_name))

    asset_inventory_api_name = apitools_api_name
    asset_inventory_resource_name = krm_kind
    if krm_group in asset_inventory_resource_name.lower():
      asset_inventory_resource_name = asset_inventory_resource_name[
          len(krm_group):]
    asset_inventory_type = '{}.googleapis.com/{}'.format(
        asset_inventory_api_name, asset_inventory_resource_name)

    bulk_support = resource_spec['SupportsBulkExport']
    single_export_support = resource_spec['SupportsExport']
    iam_support = resource_spec['SupportsIAM']

    if apitools_api_name not in update_map:
      update_map[apitools_api_name] = {}
    if apitools_collection_name not in update_map[apitools_api_name]:
      update_map[apitools_api_name][apitools_collection_name] = {
          'support_bulk_export': False,
          'support_single_export': False,
          'support_iam': False
      }

    update_map[apitools_api_name][apitools_collection_name][
        'krm_kind'] = krm_kind
    update_map[apitools_api_name][apitools_collection_name][
        'krm_group'] = krm_group
    update_map[apitools_api_name][apitools_collection_name][
        'asset_inventory_type'] = asset_inventory_type
    # If the resource does not have ResourceNameFormat then these will be False.
    update_map[apitools_api_name][apitools_collection_name][
        'support_bulk_export'] = bool(bulk_support)
    update_map[apitools_api_name][apitools_collection_name][
        'support_single_export'] = bool(single_export_support)
    update_map[apitools_api_name][apitools_collection_name][
        'support_iam'] = bool(iam_support)

  if unmatched_resources:
    raise KrmToApitoolsResourceNameError(
        'The KRM resources were unable to be matched to apitools collections: {}'
        .format(unmatched_resources))

  return update_map


def krm_kind_to_apitools_collection_name(krm_kind, krm_group,
                                         apitools_collection_names):
  """Converts the config-connector resource name to apitools collection name.

  Applies several heuristics based on commonalities between KRM Group and Kind
  values and apitools collection names toto map the KRM Group and Kind to the
  apitools collection name.

  Args:
    krm_kind: The KRM Kind provided by the config connector binary.
    krm_group: The KRM group provided by the config-connector binary.
    apitools_collection_names: Set of all collections for the relevant service.

  Raises:
    KrmToApitoolsResourceNameError: Raised if no apitools collection name
      could be derived for the given krm_kind and krm_group.

  Returns:
    The converted resource name.
  """

  apitools_collection_guess = krm_kind

  # Remove prepended krm_group from collection name if exists.
  apitools_collection_guess = remove_krm_group(apitools_collection_guess,
                                               krm_group)
  # Poluralize the collection name
  apitools_collection_guess = name_parsing.pluralize(
      apitools_collection_guess)

  # Convert first segment of collection name to lowercase.
  apitools_collection_guess = lowercase_first_segment(apitools_collection_guess)

  # Convert interior occurrences of acronyms to lowercase (e.g. SSH -> Ssh)
  apitools_collection_guess = capitalize_interior_acronyms(
      apitools_collection_guess)

  # Return guess if it's a perfect match.
  if apitools_collection_guess in apitools_collection_names:
    return apitools_collection_guess

  # Find possible matches for our guess.
  possible_matches = find_possible_matches(apitools_collection_guess,
                                           apitools_collection_names)

  # Pick and return best match based on some heuristics.
  best_match = pick_best_match(possible_matches)
  if best_match:
    return best_match

  # Raise error if no match found. Parent function will handle if no match
  # is acceptable for this resource.
  else:
    raise KrmToApitoolsResourceNameError('Cant match: {}: {}'.format(
        krm_group, krm_kind))


def krm_group_to_apitools_api_name(krm_group, apitools_api_names):
  if krm_group in apitools_api_names:
    return krm_group
  else:
    for api_name in apitools_api_names:
      if krm_group in api_name:
        if api_name.startswith(krm_group) or api_name.endswith(krm_group):
          return api_name


def remove_krm_group(apitools_collection_guess, krm_group):
  """Remove krm_group prefix from krm_kind."""
  if krm_group.lower() in apitools_collection_guess.lower():
    apitools_collection_guess = apitools_collection_guess[len(krm_group):]
  return apitools_collection_guess


def lowercase_first_segment(apitools_collection_guess):
  """First segment of collection should be lowercased, handle acronyms."""
  acronyms = ['HTTPS', 'HTTP', 'SSL', 'URL', 'VPN', 'TCP']
  found_acronym = False
  for acronym in acronyms:
    if apitools_collection_guess.startswith(acronym):
      apitools_collection_guess = apitools_collection_guess.replace(
          acronym, acronym.lower())
      found_acronym = True
  if not found_acronym:
    apitools_collection_guess = apitools_collection_guess[0].lower(
    ) + apitools_collection_guess[1:]
  return apitools_collection_guess


def capitalize_interior_acronyms(apitools_collection_guess):
  """Interior instances of acronyms should have only first letter capitalized."""
  acronyms = ['HTTPS', 'HTTP', 'SSL', 'URL', 'VPN', 'TCP']
  for acronym in acronyms:
    if acronym in apitools_collection_guess:
      apitools_collection_guess = apitools_collection_guess.replace(
          acronym, acronym.capitalize())
  return apitools_collection_guess


def find_possible_matches(apitools_collection_guess, apitools_collection_names):
  """Find any apitools collections that reasonably match our guess."""
  possible_matches = []
  for apitools_collection_name in apitools_collection_names:
    split_collection_name = apitools_collection_name.split('.')
    if apitools_collection_guess.lower() in split_collection_name[-1].lower(
    ) or split_collection_name[-1].lower() in apitools_collection_guess.lower():
      possible_matches.append(apitools_collection_name)
  return possible_matches


def pick_best_match(possible_matches):
  """Pick best match to our guess for apitools collection."""
  # If only one possible match, return it.
  if len(possible_matches) == 1:
    return possible_matches[0]
  # If more than one possible match...
  elif len(possible_matches) > 1:
    # Sort by count of segments i.e. `projects.location.resource` == 3.
    possible_matches = sorted(possible_matches, key=lambda x: len(x.split('.')))
    # If there a single shortest segment, that's our best bet, return it.
    if len(possible_matches[0].split('.')) < len(
        possible_matches[1].split('.')):
      return possible_matches[0]
    else:
      # If there are ties, prioritize locations > regions > zones.
      for priority_scope in ['locations', 'regions', 'zones']:
        for possible_match in possible_matches:
          if priority_scope in possible_match:
            return possible_match
  # If no matches, return None.
  else:
    return None


def update():
  """Primary declarative resource map update function."""
  declarative_map_instance = declarative_map.DeclarativeMap()
  updater = resource_map_update_util.MapUpdateUtil(declarative_map_instance)
  config_connector_update_map = generate_cc_update_map()
  updater.register_update_map(config_connector_update_map)
  updater.update()
