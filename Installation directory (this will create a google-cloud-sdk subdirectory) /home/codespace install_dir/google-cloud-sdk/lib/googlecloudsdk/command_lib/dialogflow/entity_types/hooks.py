# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Declarative hooks for `gcloud dialogflow entity-types`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
import six


def EntitiesType(entities):
  """Validates entities input and turns it into an entities dict.

  Valid entities inputs are:
    str of comma separated entities
    list of entities
    map from entities to synonyms

  Args:
    entities: entities input
  Returns:
    dict mapping from entities to synonyms
  Raises:
    InvalidArgumentException: If the entities input is invalid.
  """
  if isinstance(entities, six.text_type):
    entities = arg_parsers.ArgList()(entities)
  if isinstance(entities, list):
    for entity in entities:
      if not isinstance(entity, six.text_type):
        break
    else:
      return [{'value': entity, 'synonyms': [entity]} for entity in entities]
  if isinstance(entities, dict):
    for entity, synonyms in entities.items():
      if not isinstance(synonyms, list):
        break
    else:
      return [{'value': entity, 'synonyms': synonyms}
              for entity, synonyms in entities.items()]
  raise exceptions.InvalidArgumentException(
      'Entities must be a list of entities or a map from entities to a list of'
      'synonyms.')


def PatchEntityType(unused_instance_ref, args, update_request):
  """Update entities based on clear/remove/add-entities flags."""
  entities = update_request.googleCloudDialogflowV2EntityType.entities
  if args.IsSpecified('clear_entities'):
    entities = []
  if args.IsSpecified('remove_entities'):
    to_remove = set(args.remove_entities or [])
    entities = [e for e in entities if e.value not in to_remove]
  if args.IsSpecified('add_entities'):
    entities += args.add_entities
  update_request.googleCloudDialogflowV2EntityType.entities = entities
  return update_request


def SetUpdateMask(unused_instance_ref, args, update_request):
  """Set the update mask on the update request based on the args.

  Args:
    unused_instance_ref: unused.
    args: The argparse namespace.
    update_request: The update request to modify.
  Returns:
    The update request.
  Raises:
    InvalidArgumentException: If no fields are specified to update.
  """
  update_mask = []

  if (args.IsSpecified('add_entities') or args.IsSpecified('remove_entities')
      or args.IsSpecified('clear_entities')):
    update_mask.append('entities')

  if args.IsSpecified('add_entities'):
    update_mask.append('kind')

  if args.IsSpecified('display_name'):
    update_mask.append('displayName')

  if args.IsSpecified('auto_expand'):
    update_mask.append('autoExpansionMode')

  if not update_mask:
    raise exceptions.InvalidArgumentException(
        'Must specify at least one valid entity type parameter to update.')

  update_request.updateMask = ','.join(update_mask)

  return update_request


def AddEntityTypeKind(unused_instance_ref, unused_args, request):
  entities = request.googleCloudDialogflowV2EntityType.entities
  enum = request.googleCloudDialogflowV2EntityType.KindValueValuesEnum
  kind = enum.KIND_LIST
  for entity in entities:
    if entity.synonyms != [entity.value]:
      kind = enum.KIND_MAP
  request.googleCloudDialogflowV2EntityType.kind = kind
  return request
