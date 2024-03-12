# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Declarative Hooks for BQ surface arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import time
import uuid

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.args import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import times


_BQ_API = 'bigquery'
_BQ_API_VERSION = 'v2'
_BQ_JOB_ID_PREFIX = 'gcloud-bq'
_INVALID_SCHEMA_UPDATE_MESSAGE = """\
  Invalid Schema change. Only adding additional columns or relaxing `required`
  fields on existing columns is supported:

  For more details on BigQuery schemas see:
  https://cloud.google.com/bigquery/docs/schemas."""


class PermissionsFileError(exceptions.Error):
  """Error if a permissions file is improperly formatted."""


class SchemaFileError(exceptions.Error):
  """Error if a schema file is improperly formatted."""


class TableDataFileError(exceptions.Error):
  """Error if a tabel data file is improperly formatted."""


class SchemaUpdateError(exceptions.Error):
  """Error if a schema update fails."""


# Misc Util Functions
def GetApiMessage(message_name):
  """Return apitools message object for give message name."""
  messages = apis.GetMessagesModule(_BQ_API, _BQ_API_VERSION)
  return getattr(messages, message_name)


def GetApiClient():
  return apis.GetClientInstance(_BQ_API, _BQ_API_VERSION)


# Argument Processors
def JobListProjectionProcessor(show_config):
  projection_enum = (
      GetApiMessage('BigqueryJobsListRequest').ProjectionValueValuesEnum)
  if show_config:
    return projection_enum.full

  return projection_enum.minimal


def JobIdProcessor(job_id_arg):
  if job_id_arg:
    return job_id_arg

  job_id = '{}-{}'.format(_BQ_JOB_ID_PREFIX, uuid.uuid4().hex)
  return job_id


def PermissionsFileProcessor(input_file):
  """Builds a bigquery AccessValueListEntry array from input file.

  Expects YAML or JSON formatted file.

  Args:
    input_file: input file contents from argparse namespace.

  Raises:
    PermissionsFileError: if the file contents are not a valid JSON or YAML
      file.

  Returns:
    [AccessValueListEntry]: Array of AccessValueListEntry messages specifying
      access permissions defined input file.
  """
  access_value_msg = GetApiMessage('Dataset').AccessValueListEntry
  try:
    permissions_array = []
    permissions_from_file = yaml.load(input_file[0])
    permissions_from_file = permissions_from_file.get('access', None)
    if not permissions_from_file or not isinstance(permissions_from_file, list):
      raise PermissionsFileError(
          'Error parsing permissions file: no access list defined in file')
    for access_yaml in permissions_from_file:
      permission = encoding.PyValueToMessage(access_value_msg, access_yaml)
      if _ValidatePermission(permission):
        permissions_array.append(permission)
      else:
        raise PermissionsFileError(('Error parsing permissions file:'
                                    ' invalid permission definition'
                                    ' [{}]'.format(permission)))

    return sorted(permissions_array, key=lambda x: x.role)
  except yaml.YAMLParseError as ype:
    raise PermissionsFileError('Error parsing permissions file [{}]'.format(
        ype))


def _ValidatePermission(permission_obj):
  is_valid = (permission_obj.domain or
              permission_obj.userByEmail or
              permission_obj.specialGroup or
              permission_obj.view or
              permission_obj.groupByEmail) and permission_obj.role
  return is_valid


def ProcessTableExpiration(expire_duration):
  """Convert commandline duration into epoch timeoffset (in ms)."""
  t = times.GetDateTimePlusDuration(datetime.datetime.now(), expire_duration)
  return int(time.mktime(t.timetuple())) * 1000


def BqTableSchemaFileProcessor(file_arg):
  """Convert Input JSON file into TableSchema message."""
  table_schema_type = GetApiMessage('TableSchema')
  schema_field_type = GetApiMessage('TableFieldSchema')

  try:
    schema_json = yaml.load(file_arg)
    schema_json = schema_json.get('schema', None)

    if not schema_json or not isinstance(schema_json, list):
      raise SchemaFileError(
          'Error parsing schema file: no schema field list defined in file')

    all_fields = []
    for field in schema_json:
      new_field = schema_field_type(name=field['name'],
                                    type=field['type'],
                                    mode=field.get('mode', 'NULLABLE'))
      all_fields.append(new_field)

    return table_schema_type(fields=sorted(all_fields, key=lambda x: x.name))
  except yaml.YAMLParseError as ype:
    raise SchemaFileError('Error parsing schema file [{}]'.format(ype))
  except (AttributeError, KeyError) as e:
    raise SchemaFileError(
        'Error parsing schema file, invalid field definition [{}]'.format(e))


def BqTableDataFileProcessor(file_arg):
  """Convert Input JSON file into TableSchema message."""
  data_insert_request_type = GetApiMessage('TableDataInsertAllRequest')
  insert_row_type = data_insert_request_type.RowsValueListEntry
  data_row_type = GetApiMessage('JsonObject')

  try:
    data_json = yaml.load(file_arg)

    if not data_json or not isinstance(data_json, list):
      raise TableDataFileError(
          'Error parsing data file: no data records defined in file')

    rows = []
    for row in data_json:
      rows.append(insert_row_type(json=encoding.DictToMessage(
          row, data_row_type)))

    return rows
  except yaml.YAMLParseError as ype:
    raise TableDataFileError('Error parsing data file [{}]'.format(ype))


# Request modifiers
def SetProjectId(ref, args, request):
  """Set projectId value for a BigQueryXXXRequests."""
  del ref
  project = args.project or properties.VALUES.core.project.Get(required=True)
  project_ref = resources.REGISTRY.Parse(project,
                                         collection='bigquery.projects')
  request.projectId = project_ref.Name()
  return request


def  SetViewParameters(ref, args, request):
  """Ensure that view parameters are set properly tables create request."""
  del ref  # unused

  if not args.view:
    request.table.view = None

  return request


def  ProcessDatasetOverwrite(ref, args, request):
  """Process the overwrite flag on datasets create."""
  del ref
  dataset_id = request.dataset.datasetReference.datasetId
  project_id = request.projectId

  if args.overwrite:
    if _DatasetExists(dataset_id, project_id):
      _TryDeleteDataset(dataset_id, project_id)

  return request


def  ProcessTableOverwrite(ref, args, request):
  """Process the overwrite flag on tables create."""
  dataset_id = ref.datasetId
  table_id = ref.Name()
  project_id = ref.projectId

  if args.overwrite:
    if _TableExists(dataset_id, table_id, project_id):
      _TryDeleteTable(dataset_id, table_id, project_id)

  return request


def  ProcessTableCopyOverwrite(ref, args, request):
  """Process the overwrite flag on tables copy."""
  del ref  # Unused
  if args.overwrite:
    request.job.configuration.copy.writeDisposition = 'WRITE_TRUNCATE'
  return request


def  ProcessTableCopyConfiguration(ref, args, request):
  """Build JobConfigurationTableCopy from request resource args."""
  del ref  # Unused
  source_ref = args.CONCEPTS.source.Parse()
  destination_ref = args.CONCEPTS.destination.Parse()
  arg_utils.SetFieldInMessage(
      request, 'job.configuration.copy.destinationTable.datasetId',
      destination_ref.Parent().Name())
  arg_utils.SetFieldInMessage(
      request, 'job.configuration.copy.destinationTable.projectId',
      destination_ref.projectId)
  arg_utils.SetFieldInMessage(request,
                              'job.configuration.copy.destinationTable.tableId',
                              destination_ref.Name())
  arg_utils.SetFieldInMessage(request,
                              'job.configuration.copy.sourceTable.datasetId',
                              source_ref.Parent().Name())
  arg_utils.SetFieldInMessage(request,
                              'job.configuration.copy.sourceTable.projectId',
                              source_ref.projectId)
  arg_utils.SetFieldInMessage(request,
                              'job.configuration.copy.sourceTable.tableId',
                              source_ref.Name())
  return request


def  ProcessSchemaUpdate(ref, args, request):
  """Process schema Updates (additions/mode changes) for the request.

  Retrieves the current table schema for ref and attempts to merge in the schema
  provided in the requests. This is necessary since the API backend does not
  handle PATCH semantics for schema updates (e.g. process the deltas) so we must
  always send the fully updated schema in the requests.

  Args:
    ref: resource reference for table.
    args: argparse namespace for requests
    request: BigqueryTablesPatchRequest object


  Returns:
    request: updated requests

  Raises:
    SchemaUpdateError: table not found or invalid an schema change.
  """
  table = request.table
  relaxed_columns = args.relax_columns
  if not table.schema and not relaxed_columns:  # if not updating schema,
    return request                              # then just return.

  original_schema = _TryGetCurrentSchema(ref.Parent().Name(),
                                         ref.Name(),
                                         ref.projectId)

  new_schema_columns = table.schema
  updated_fields = _GetUpdatedSchema(original_schema,
                                     new_schema_columns,
                                     relaxed_columns)

  table_schema_type = GetApiMessage('TableSchema')
  request.table.schema = table_schema_type(fields=updated_fields)

  return request


def _TryGetCurrentSchema(dataset_id, table_id, project_id):
  """Try to retrieve the current BigQuery TableSchema for a table_ref.

    Tries to fetch the schema of an existing table. Raises SchemaUpdateError if
    table is not found or if table is not of type 'TABLE'.

  Args:
    dataset_id: the dataset id containing the table.
    table_id: the table id for the table.
    project_id: the project id containing the dataset and table.


  Returns:
    schema: the table schema object

  Raises:
    SchemaUpdateError: table not found or invalid table type.
  """
  client = GetApiClient()
  service = client.tables
  get_request_type = GetApiMessage('BigqueryTablesGetRequest')
  get_request = get_request_type(datasetId=dataset_id,
                                 tableId=table_id,
                                 projectId=project_id)
  try:
    table = service.Get(get_request)
    if not table or table.type != 'TABLE':
      raise SchemaUpdateError('Schema modifications only supported '
                              'on TABLE objects received [{}]'.format(
                                  table))
  except apitools_exceptions.HttpNotFoundError:
    raise SchemaUpdateError('Table with id [{}:{}:{}] not found.'.format(
        project_id, dataset_id, table_id))

  return table.schema


def _GetUpdatedSchema(
    original_schema,
    new_columns=None,
    relaxed_columns=None):
  """Update original_schema by adding and/or relaxing mode on columns."""
  orig_field_map = (
      {f.name: f for f in original_schema.fields} if original_schema else {})

  if relaxed_columns:
    orig_field_map = _GetRelaxedCols(relaxed_columns, orig_field_map)

  if new_columns:
    orig_field_map = _AddNewColsToSchema(new_columns.fields, orig_field_map)

  return sorted(orig_field_map.values(), key=lambda x: x.name)


def _GetRelaxedCols(relaxed_columns, orig_schema_map):
  """Change mode to `NULLABLE` for columns in existing schema.

    Tries set mode on existing columns in orig_schema_map to `NULLABLE`. Raises
    SchemaUpdateError if column is not found in orig_schema_map.

  Args:
    relaxed_columns: [string] the list columns to relax required mode for.
    orig_schema_map: {string: TableSchemaField} map of field name to
      TableSchemaField objects representing the original schema.

  Returns:
    updated_schema_map: {string: TableSchemaField} map of field name to
      TableSchemaField objects representing the updated schema.

  Raises:
    SchemaUpdateError: if any of the fields to be relaxed are not in the
      original schema.
  """
  updated_schema_map = orig_schema_map.copy()
  for col in relaxed_columns:
    if col in orig_schema_map:
      updated_schema_map[col].mode = 'NULLABLE'
    else:
      raise SchemaUpdateError(_INVALID_SCHEMA_UPDATE_MESSAGE)
  return updated_schema_map


def _AddNewColsToSchema(new_fields, orig_schema_map):
  """Add new columns to an existing schema.

    Tries add new fields to an existing schema. Raises SchemaUpdateError
    if column already exists in the orig_schema_map.

  Args:
    new_fields: [TableSchemaField] the list columns add to schema.
    orig_schema_map: {string: TableSchemaField} map of field name to
      TableSchemaField objects representing the original schema.

  Returns:
    updated_schema_map: {string: TableSchemaField} map of field name to
      TableSchemaField objects representing the updated schema.

  Raises:
    SchemaUpdateError: if any of the fields to be relaxed are not in the
      original schema.
  """
  updated_schema_map = orig_schema_map.copy()
  for new_field in new_fields:
    if new_field.name in orig_schema_map:
      raise SchemaUpdateError(_INVALID_SCHEMA_UPDATE_MESSAGE)
    updated_schema_map[new_field.name] = new_field
  return updated_schema_map


def _DatasetExists(dataset_id, project_id):
  """Validate a resource of the given type with specified ID already exists."""
  client = GetApiClient()
  service = client.datasets
  get_request_type = GetApiMessage('BigqueryDatasetsGetRequest')
  get_request = get_request_type(datasetId=dataset_id, projectId=project_id)
  try:
    service.Get(get_request)
    return True
  except apitools_exceptions.HttpNotFoundError:
    log.info('Dataset with id [{}:{}] not found.'.format(
        project_id, dataset_id))

  return False


def _TableExists(dataset_id, table_id, project_id):
  """Validate a resource of the given type with specified ID already exists."""
  client = GetApiClient()
  service = client.tables
  get_request_type = GetApiMessage('BigqueryTablesGetRequest')
  get_request = get_request_type(datasetId=dataset_id, tableId=table_id,
                                 projectId=project_id)
  try:
    service.Get(get_request)
    return True
  except apitools_exceptions.HttpNotFoundError:
    log.info('Table with id [{}:{}:{}] not found.'.format(
        project_id, dataset_id, table_id))

  return False


def _TryDeleteDataset(dataset_id, project_id):
  """Try to delete a dataset, propagating error on failure."""
  client = GetApiClient()
  service = client.datasets
  delete_request_type = GetApiMessage('BigqueryDatasetsDeleteRequest')
  delete_request = delete_request_type(datasetId=dataset_id,
                                       projectId=project_id,
                                       deleteContents=True)
  service.Delete(delete_request)
  log.info('Deleted dataset [{}:{}]'.format(project_id, dataset_id))


def _TryDeleteTable(dataset_id, table_id, project_id):
  """Try to delete a dataset, propagating error on failure."""
  client = GetApiClient()
  service = client.tables
  delete_request_type = GetApiMessage('BigqueryTablesDeleteRequest')
  delete_request = delete_request_type(datasetId=dataset_id, tableId=table_id,
                                       projectId=project_id)
  service.Delete(delete_request)
  log.info('Deleted table [{}:{}:{}]'.format(project_id, dataset_id, table_id))


# Argument Types
def BqViewType(query_string):
  view_def_type = GetApiMessage('ViewDefinition')
  return view_def_type(query=query_string, useLegacySql=True)


# Resource Argument Hooks
def GetTableCopyResourceArgs():
  """Get Table resource args (source, destination) for copy command."""
  table_spec_data = yaml_data.ResourceYAMLData.FromPath('bq.table')
  arg_specs = [
      resource_args.GetResourcePresentationSpec(
          verb='to copy from', name='source', required=True, prefixes=True,
          attribute_overrides={'table': 'source'}, positional=False,
          resource_data=table_spec_data.GetData()),
      resource_args.GetResourcePresentationSpec(
          verb='to copy to', name='destination',
          required=True, prefixes=True,
          attribute_overrides={'table': 'destination'}, positional=False,
          resource_data=table_spec_data.GetData())]
  fallthroughs = {
      '--source.dataset': ['--destination.dataset'],
      '--destination.dataset': ['--source.dataset']
  }
  return [concept_parsers.ConceptParser(arg_specs, fallthroughs)]
