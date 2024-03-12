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
"""Utilities for Data Catalog entries commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import messages as _messages
from apitools.base.py import encoding
from googlecloudsdk.api_lib.data_catalog import entries
from googlecloudsdk.api_lib.data_catalog import util as api_util
from googlecloudsdk.command_lib.concepts import exceptions as concept_exceptions
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
import six


class InvalidSchemaError(exceptions.Error):
  """Error if a schema is improperly specified."""


class InvalidSchemaFileError(exceptions.Error):
  """Error if a schema file is not valid JSON or YAML."""


class UnderSpecifiedEntryError(exceptions.Error):
  """Error if an entry resource argument is not fully specified."""


def CorrectUpdateMask(ref, args, request):
  """Returns the update request with the corrected mask.

  The API expects a request with an update mask of 'schema', whereas the inline
  schema argument generates an update mask of 'schema.columns'. So if --schema
  was specified, we have to correct the update mask.

  Args:
    ref: The entry resource reference.
    args: The parsed args namespace.
    request: The update entry request.

  Returns:
    Request with corrected update mask.
  """
  del ref
  if args.IsSpecified('schema'):
    request.updateMask = request.updateMask.replace('schema.columns', 'schema')
  return request


def _IsChangeFilePatternSpecified(args):
  return (args.IsSpecified('add_file_patterns') or
          args.IsSpecified('remove_file_patterns') or
          args.IsSpecified('clear_file_patterns'))


def MergeGcsFilePatterns(ref, args, request):
  """Merges user-provided GCS file patterns with existing patterns.

  Args:
    ref: The entry resource reference.
    args: The parsed args namespace.
    request: The update entry request.

  Returns:
    Request with merged GCS file pattern.
  """
  if not _IsChangeFilePatternSpecified(args):
    return request

  del ref
  entry_ref = args.CONCEPTS.entry.Parse()

  file_patterns = entries.EntriesClient().Get(
      entry_ref).gcsFilesetSpec.filePatterns or []
  if args.IsSpecified('clear_file_patterns'):
    file_patterns = []
  if args.IsSpecified('remove_file_patterns'):
    to_remove = set(args.remove_file_patterns)
    file_patterns = [b for b in file_patterns if b not in to_remove]
  if args.IsSpecified('add_file_patterns'):
    file_patterns += args.add_file_patterns

  arg_utils.SetFieldInMessage(
      request, 'googleCloudDatacatalogV1beta1Entry.gcsFilesetSpec.filePatterns',
      file_patterns)

  request.updateMask += ',gcsFilesetSpec.filePatterns'
  return request


def ParseResourceIntoLookupRequest(ref, args, request):
  del ref
  return entries.ParseResourceIntoLookupRequest(args.resource, request)


def LookupAndParseEntry(ref, args, request):
  """Parses the entry into the request, performing a lookup first if necessary.

  Args:
    ref: None.
    args: The parsed args namespace.
    request: The update entry request.

  Returns:
    Request containing the parsed entry.
  Raises:
    UnderSpecifiedEntryError: if ENTRY was only partially specified.
    RequiredMutexGroupError: if both or neither ENTRY, --lookup-entry specified.
  """
  del ref
  entry_ref = args.CONCEPTS.entry.Parse()

  # Parse() will raise an error if the entry flags are specified without the
  # anchor, so we don't need to handle that case. However no error is returned
  # if a positional is specified but parsing fails, so we check for that here.
  if args.IsSpecified('entry') and not entry_ref:
    raise UnderSpecifiedEntryError(
        'Argument [ENTRY : --entry-group=ENTRY_GROUP --location=LOCATION] was '
        'not fully specified.')

  if ((entry_ref and args.IsSpecified('lookup_entry')) or
      (not entry_ref and not args.IsSpecified('lookup_entry'))):
    raise concept_exceptions.RequiredMutexGroupError(
        'entry', '([ENTRY : --entry-group=ENTRY_GROUP --location=LOCATION] '
        '| --lookup-entry)')

  if entry_ref:
    request.name = entry_ref.RelativeName()
  else:
    client = entries.EntriesClient()
    request.name = client.Lookup(args.lookup_entry).name
  return request


def ProcessSchemaFromFile(schema_file):
  try:
    schema = yaml.load(schema_file)
  except yaml.YAMLParseError as e:
    raise InvalidSchemaFileError('Error parsing schema file: [{}]'.format(e))
  return _SchemaToMessage(schema)


# TODO(b/127861769): Improve schema validation.
def _SchemaToMessage(schema):
  """Converts the given schema dict to the corresponding schema message.

  Args:
    schema: dict, The schema that has been processed.

  Returns:
    googleCloudDatacatalogV1betaSchema
  Raises:
    InvalidSchemaError: If the schema is invalid.
  """
  messages = api_util.GetMessagesModule()

  try:
    schema_message = encoding.DictToMessage(
        {'columns': schema}, messages.GoogleCloudDatacatalogV1beta1Schema)
  except AttributeError:
    # TODO(b/77547931): Fix apitools bug related to unchecked iteritems() call.
    raise InvalidSchemaError(
        'Invalid schema: expected list of column names along with their types, '
        'modes, descriptions, and/or nested subcolumns.')
  except _messages.ValidationError as e:
    # Unfortunately apitools doesn't provide a way to get the path to the
    # invalid field here.
    raise InvalidSchemaError('Invalid schema: [{}]'.format(e))
  unrecognized_field_paths = _GetUnrecognizedFieldPaths(schema_message)
  if unrecognized_field_paths:
    error_msg_lines = ['Invalid schema, the following fields are unrecognized:']
    error_msg_lines += unrecognized_field_paths
    raise InvalidSchemaError('\n'.join(error_msg_lines))

  return schema_message


def _GetUnrecognizedFieldPaths(message):
  """Returns the field paths for unrecognized fields in the message."""
  errors = encoding.UnrecognizedFieldIter(message)
  unrecognized_field_paths = []
  for edges_to_message, field_names in errors:
    message_field_path = '.'.join(six.text_type(e) for e in edges_to_message)
    # Don't print the top level columns field since the user didn't specify it
    message_field_path = message_field_path.replace('columns', '', 1)
    for field_name in field_names:
      unrecognized_field_paths.append('{}.{}'.format(message_field_path,
                                                     field_name))
  return sorted(unrecognized_field_paths)


def LogStarSuccess(_, args):
  log.out.Print('Starred entry [{}].'.format(args.entry))


def LogUnstarSuccess(_, args):
  log.out.Print('Unstarred entry [{}].'.format(args.entry))
