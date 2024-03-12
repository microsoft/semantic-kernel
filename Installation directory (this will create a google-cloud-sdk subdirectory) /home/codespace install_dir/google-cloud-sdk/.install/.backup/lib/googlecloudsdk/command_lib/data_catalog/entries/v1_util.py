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

from os import path
from apitools.base.protorpclite import messages as _messages
from apitools.base.py import encoding
from googlecloudsdk.api_lib.data_catalog import entries_v1
from googlecloudsdk.api_lib.data_catalog import util as api_util
from googlecloudsdk.command_lib.concepts import exceptions as concept_exceptions
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times
import six


class InvalidSchemaError(exceptions.Error):
  """Error if a schema is improperly specified."""


class InvalidSchemaFileError(exceptions.Error):
  """Error if a schema file is not valid JSON or YAML."""


class UnderSpecifiedEntryError(exceptions.Error):
  """Error if an entry resource argument is not fully specified."""


class InvalidPhysicalSchemaError(exceptions.Error):
  """Error if physical schema is improperly specified."""


def ParseFilesetRequirements(ref, args, request):
  """Fileset types need a file pattern."""
  del ref
  if args.type == 'fileset' and args.gcs_file_patterns is None:
    # if type is fileset and gcs-file-patterns not specified
    raise concept_exceptions.ModalGroupError('gcs-file-patterns',
                                             'type=FILESET',
                                             '--gcs-file-patterns')
  return request


def GetJsonTimeString(dt):
  return times.FormatDateTime(times.ParseDateTime(dt))


def CorrectUpdateMask(ref, args, request):
  """Returns the update request with the corrected mask.

  The API expects a request with an update mask of 'schema', whereas the inline
  schema argument generates an update mask of 'schema.columns'. So if --schema
  was specified, we have to correct the update mask. As for the physical schema,
  the mask must be added.

  Args:
    ref: The entry resource reference.
    args: The parsed args namespace.
    request: The update entry request.

  Returns:
    Request with corrected update mask.
  """
  del ref
  if args.IsSpecified('physical_schema_type'):
    request.updateMask += ',schema'
  if args.IsSpecified('schema'):
    request.updateMask = request.updateMask.replace('schema.columns', 'schema')
  return request


def DetectType(ref, args, request):
  """Detect Entry type.

  Args:
    ref: The entry resource reference.
    args: The parsed args namespace.
    request: The update entry request.

  Returns:
    Request with proper type
  """

  del ref
  client = entries_v1.EntriesClient()
  messages = client.messages

  if args.IsSpecified('kafka_cluster_bootstrap_servers'):
    arg_utils.SetFieldInMessage(
        request, 'googleCloudDatacatalogV1Entry.type',
        messages.GoogleCloudDatacatalogV1Entry.TypeValueValuesEnum.CLUSTER)
  if args.IsSpecified('kafka_topic'):
    arg_utils.SetFieldInMessage(
        request, 'googleCloudDatacatalogV1Entry.type',
        messages.GoogleCloudDatacatalogV1Entry.TypeValueValuesEnum.DATA_STREAM)
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

  file_patterns = entries_v1.EntriesClient().Get(
      entry_ref).gcsFilesetSpec.filePatterns or []
  if args.IsSpecified('clear_file_patterns'):
    file_patterns = []
  if args.IsSpecified('remove_file_patterns'):
    to_remove = set(args.remove_file_patterns)
    file_patterns = [b for b in file_patterns if b not in to_remove]
  if args.IsSpecified('add_file_patterns'):
    file_patterns += args.add_file_patterns

  arg_utils.SetFieldInMessage(
      request, 'googleCloudDatacatalogV1Entry.gcsFilesetSpec.filePatterns',
      file_patterns)

  request.updateMask += ',gcsFilesetSpec.filePatterns'
  return request


def ParsePhysicalSchema(ref, args, request):
  """Parses physical schema from file after obtaining information about its type.

  Args:
    ref: The entry resource reference.
    args: The parsed args namespace.
    request: The update entry request.

  Returns:
    Request with merged GCS file pattern.

  Raises:
    InvalidPhysicalSchemaError: if physical schema type is unknown
  """
  if not args.IsSpecified('physical_schema_type'):
    return request

  del ref
  client = entries_v1.EntriesClient()
  messages = client.messages

  if args.IsSpecified('physical_schema_file'):
    schema_abs_path = path.expanduser(args.physical_schema_file)
    schema_text = files.ReadFileContents(schema_abs_path)
  else:
    schema_text = ''

  schema_type = args.physical_schema_type

  if schema_type == 'avro':
    schema = messages.GoogleCloudDatacatalogV1PhysicalSchemaAvroSchema()
    schema.text = schema_text
  elif schema_type == 'thrift':
    schema = messages.GoogleCloudDatacatalogV1PhysicalSchemaThriftSchema()
    schema.text = schema_text
  elif schema_type == 'protobuf':
    schema = messages.GoogleCloudDatacatalogV1PhysicalSchemaProtobufSchema()
    schema.text = schema_text
  elif schema_type == 'parquet':
    schema = messages.GoogleCloudDatacatalogV1PhysicalSchemaParquetSchema()
  elif schema_type == 'orc':
    schema = messages.GoogleCloudDatacatalogV1PhysicalSchemaOrcSchema()
  else:
    raise InvalidPhysicalSchemaError(
        'Unknown physical schema type. Must be one of: avro, thrift, protobuf,'
        'parquet, orc')

  arg_utils.SetFieldInMessage(
      request,
      'googleCloudDatacatalogV1Entry.schema.physicalSchema.' + schema_type,
      schema)

  return request


def ParseResourceIntoLookupRequest(ref, args, request):
  del ref
  return entries_v1.ParseResourceIntoLookupRequest(args.resource, request)


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
    client = entries_v1.EntriesClient()
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
  messages = api_util.GetMessagesModule('v1')

  try:
    schema_message = encoding.DictToMessage(
        {'columns': schema}, messages.GoogleCloudDatacatalogV1Schema)
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
