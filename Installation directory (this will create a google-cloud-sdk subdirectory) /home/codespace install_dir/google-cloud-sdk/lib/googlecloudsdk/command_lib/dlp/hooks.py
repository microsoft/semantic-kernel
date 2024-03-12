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
"""Argument processors for DLP surface arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times
import six

_DLP_API = 'dlp'
_DLP_API_VERSION = 'v2'

_COLOR_SPEC_ERROR_SUFFIX = """\
Colors should be specified as a string of `r,g,b` float values in the interval
[0,1] representing the amount of red, green, and blue in the color,
respectively. For example, `black = 0,0,0`, `red = 1.0,0,0`,
`white = 1.0,1.0,1.0`, and so on.
"""

VALID_IMAGE_EXTENSIONS = {
    'n_a': 'IMAGE',
    '.png': 'IMAGE_PNG',
    '.jpeg': 'IMAGE_JPEG',
    '.jpg': 'IMAGE_JPEG',
    '.svg': 'IMAGE_SVG',
    '.bmp': 'IMAGE_BMP'
}


class ImageFileError(exceptions.Error):
  """Error if an image file is improperly formatted or missing."""


class RedactColorError(exceptions.Error):
  """Error if a redact color is improperly formatted or missing."""


class BigQueryTableNameError(exceptions.Error):
  """Error if a BigQuery table name is improperly formatted."""


# Misc/Helper Functions
def _GetMessageClass(msg_type_name):
  """Get API message object for given message type name."""
  msg = apis.GetMessagesModule(_DLP_API, _DLP_API_VERSION)
  return getattr(msg, msg_type_name)


def _ValidateExtension(extension):
  """Validate image file name extension."""
  if not extension:  # No extension is ok.
    return True
  # But if provided it should match expected values
  return extension and (extension in VALID_IMAGE_EXTENSIONS)


def _ConvertColorValue(color):
  """Convert color value(color) to a float or raise value error."""
  j = float(color)
  if j > 1.0 or j < 0.0:
    raise ValueError('Invalid Color.')

  return j


def _ValidateAndParseColors(value):
  """Validates that values has proper format and returns parsed components."""
  values = value.split(',')

  if len(values) == 3:
    try:
      return [_ConvertColorValue(x) for x in values]
    except ValueError:
      raise RedactColorError('Invalid Color Value(s) [{}]. '
                             '{}'.format(value, _COLOR_SPEC_ERROR_SUFFIX))
  else:
    raise RedactColorError('You must specify exactly 3 color values [{}]. '
                           '{}'.format(value, _COLOR_SPEC_ERROR_SUFFIX))


def _ValidateAndParseInputTableName(table_name):
  """Validate BigQuery table name format and returned parsed components."""
  name_parts = table_name.split('.')
  if len(name_parts) != 3:
    raise BigQueryTableNameError(
        'Invalid BigQuery table name [{}]. BigQuery tables are uniquely '
        'identified by their project_id, dataset_id, and table_id in the '
        'format `<project_id>.<dataset_id>.<table_id>`.'.format(table_name))

  return name_parts


def _ValidateAndParseOutputTableName(table_name):
  """Validate BigQuery table name format and returned parsed components."""
  # Table id is optional for output tables.
  name_parts = table_name.split('.')
  if len(name_parts) != 3 and len(name_parts) != 2:
    raise BigQueryTableNameError(
        'Invalid BigQuery output table name [{}]. BigQuery tables are uniquely '
        'identified by their project_id, dataset_id, and or table_id in the '
        'format `<project_id>.<dataset_id>.<table_id>` or '
        '`<project_id>.<dataset_id>.'.format(table_name))

  return name_parts


# Types
def InfoType(value):  # Defines elment type for infoTypes collection on request
  """Return GooglePrivacyDlpV2InfoType message for a parsed value."""
  infotype = _GetMessageClass('GooglePrivacyDlpV2InfoType')
  return infotype(name=value)


def PrivacyField(value):
  """Create a GooglePrivacyDlpV2FieldId for value."""
  field_id = _GetMessageClass('GooglePrivacyDlpV2FieldId')
  return field_id(name=value)


def BigQueryInputOptions(table_name):
  """Convert BigQuery table name into GooglePrivacyDlpV2BigQueryOptions.

  Creates BigQuery input options for a job trigger.

  Args:
    table_name: str, BigQuery table name to create input options from in the
      form `<project_id>.<dataset_id>.<table_id>`.

  Returns:
    GooglePrivacyDlpV2BigQueryOptions, input options for job trigger.

  Raises:
    BigQueryTableNameError if table_name is improperly formatted.
  """
  project_id, data_set_id, table_id = _ValidateAndParseInputTableName(
      table_name)
  big_query_options = _GetMessageClass('GooglePrivacyDlpV2BigQueryOptions')
  big_query_table = _GetMessageClass('GooglePrivacyDlpV2BigQueryTable')
  table = big_query_table(
      datasetId=data_set_id, projectId=project_id, tableId=table_id)
  options = big_query_options(tableReference=table)
  return options


def GcsInputOptions(url):
  """Return CloudStorageOptions for given GCS url."""
  cloud_storage_options = _GetMessageClass(
      'GooglePrivacyDlpV2CloudStorageOptions')
  file_set = _GetMessageClass('GooglePrivacyDlpV2FileSet')
  return cloud_storage_options(fileSet=file_set(url=url))


def DatastoreInputOptions(table_name):
  """Convert Datastore arg value into GooglePrivacyDlpV2DatastoreOptions.

  Creates Datastore input options for a job trigger from datastore table name.

  Args:
    table_name: str, Datastore table name to create options from in the form
    `namespace:example-kind` or simply `example-kind`.

  Returns:
    GooglePrivacyDlpV2Action, output action for job trigger.
  """
  data_store_options = _GetMessageClass('GooglePrivacyDlpV2DatastoreOptions')
  kind = _GetMessageClass('GooglePrivacyDlpV2KindExpression')
  partition_id = _GetMessageClass('GooglePrivacyDlpV2PartitionId')
  project = properties.VALUES.core.project.Get(required=True)
  split_name = table_name.split(':')
  if len(split_name) == 2:
    namespace, table = split_name
    kind_exp = kind(name=table)
    partition = partition_id(namespaceId=namespace, projectId=project)
  else:
    kind_exp = kind(name=table_name)
    partition = partition_id(projectId=project)
  return data_store_options(kind=kind_exp, partitionId=partition)


def PubSubTopicAction(topic):
  """Return PubSub DlpV2Action for given PubSub topic."""
  action_msg = _GetMessageClass('GooglePrivacyDlpV2Action')
  pubsub_action = _GetMessageClass('GooglePrivacyDlpV2PublishToPubSub')
  return action_msg(pubSub=pubsub_action(topic=topic))


def BigQueryTableAction(table_name):
  """Convert BigQuery formatted table name into GooglePrivacyDlpV2Action.

  Creates a BigQuery output action for a job trigger.

  Args:
    table_name: str, BigQuery table name to create action from in the form
      `<project_id>.<dataset_id>.<table_id>` or `<project_id>.<dataset_id>`.

  Returns:
    GooglePrivacyDlpV2Action, output action for job trigger.

  Raises:
    BigQueryTableNameError if table_name is improperly formatted.
  """
  name_parts = _ValidateAndParseOutputTableName(table_name)

  project_id = name_parts[0]
  data_set_id = name_parts[1]
  table_id = ''
  if len(name_parts) == 3:
    table_id = name_parts[2]
  action_msg = _GetMessageClass('GooglePrivacyDlpV2Action')
  save_findings_config = _GetMessageClass('GooglePrivacyDlpV2SaveFindings')
  output_config = _GetMessageClass('GooglePrivacyDlpV2OutputStorageConfig')
  big_query_table = _GetMessageClass('GooglePrivacyDlpV2BigQueryTable')
  table = big_query_table(
      datasetId=data_set_id, projectId=project_id, tableId=table_id)

  return action_msg(
      saveFindings=save_findings_config(
          outputConfig=output_config(table=table)))


def DlpTimeStamp(value):
  return times.FormatDateTime(value, tzinfo=times.UTC)


# Request Hooks
def SetRequestParent(ref, args, request):
  """Set parent value for a DlpXXXRequest."""
  del ref
  parent = args.project or properties.VALUES.core.project.Get(required=True)
  project_ref = resources.REGISTRY.Parse(parent, collection='dlp.projects')
  request.parent = project_ref.RelativeName()
  return request


def SetCancelRequestHook(ref, args, request):
  """Set cancel message on DlpProjectsDlpJobsCancelRequest."""
  del ref
  del args
  cancel_request = _GetMessageClass('GooglePrivacyDlpV2CancelDlpJobRequest')
  request.googlePrivacyDlpV2CancelDlpJobRequest = cancel_request()
  return request


def UpdateDataStoreOptions(ref, args, request):
  """Update partitionId.projectId on DatastoreOptions."""
  del ref
  data_store_options = (
      request.googlePrivacyDlpV2CreateJobTriggerRequest.jobTrigger.inspectJob
      .storageConfig.datastoreOptions)
  if args.project and data_store_options:
    data_store_options.partitionId.projectId = args.project

  return request


# Required since bigQueryOptions are create by a separate flag so
# identifyingFields can't be set until before requests is sent.
def UpdateIdentifyingFields(ref, args, request):
  """Update bigQueryOptions.identifyingFields with parsed fields."""
  del ref
  big_query_options = (
      request.googlePrivacyDlpV2CreateDlpJobRequest.inspectJob.storageConfig
      .bigQueryOptions)
  if big_query_options and args.identifying_fields:
    field_id = _GetMessageClass('GooglePrivacyDlpV2FieldId')
    big_query_options.identifyingFields = [
        field_id(name=field) for field in args.identifying_fields
    ]
  return request


def SetOrderByFromSortBy(ref, args, request):
  """Set orderBy attribute on message from common --sort-by flag."""
  del ref
  if args.sort_by:
    order_by_fields = []
    for field in args.sort_by:
      # ~field ==> field desc
      if field.startswith('~'):
        field = field.lstrip('~') + ' desc'
      else:
        field += ' asc'
      order_by_fields.append(field)
    request.orderBy = ','.join(order_by_fields)
  return request


# Argument Processors
def ExtractBqTableFromInputConfig(value):
  """Extracts and returns BigQueryTable from parsed BigQueryOptions message."""
  return value.tableReference


def GetReplaceTextTransform(value):
  replace_config = _GetMessageClass('GooglePrivacyDlpV2ReplaceValueConfig')
  value_holder = _GetMessageClass('GooglePrivacyDlpV2Value')
  return replace_config(newValue=value_holder(stringValue=value))


def GetInfoTypeTransform(value):
  del value
  infotype_config = _GetMessageClass(
      'GooglePrivacyDlpV2ReplaceWithInfoTypeConfig')
  return infotype_config()


def GetRedactTransform(value):
  del value
  redact_config = _GetMessageClass('GooglePrivacyDlpV2RedactConfig')
  return redact_config()


def GetImageFromFile(path):
  """Builds a GooglePrivacyDlpV2ByteContentItem message from a path.

  Will attempt to set message.type from file extension (if present).

  Args:
    path: the path arg given to the command.

  Raises:
    ImageFileError: if the image path does not exist and does not have a valid
    extension.

  Returns:
    GooglePrivacyDlpV2ByteContentItem: an message containing image data for
    the API on the image to analyze.
  """
  extension = os.path.splitext(path)[-1].lower()
  extension = extension or 'n_a'
  image_item = _GetMessageClass('GooglePrivacyDlpV2ByteContentItem')
  if os.path.isfile(path) and _ValidateExtension(extension):
    enum_val = arg_utils.ChoiceToEnum(VALID_IMAGE_EXTENSIONS[extension],
                                      image_item.TypeValueValuesEnum)
    image = image_item(data=files.ReadBinaryFileContents(path), type=enum_val)
  else:
    raise ImageFileError(
        'The image path [{}] does not exist or has an invalid extension. '
        'Must be one of [jpg, jpeg, png, bmp or svg]. '
        'Please double-check your input and try again.'.format(path))
  return image


def GetRedactColorFromString(color_string):
  """Convert color_string into GooglePrivacyDlpV2Color.

  Creates a GooglePrivacyDlpV2Color message from input string to use for image
  redaction.

  Args:
    color_string: str, string representing red, green and blue color saturation
      percentages as float values between 0.0 and 1.0. For example, `black =
      0,0,0`, `red = 1.0,0,0`, `white = 1.0,1.0,1.0` etc.

  Returns:
    GooglePrivacyDlpV2Color, color message.

  Raises:
    RedactColorError if color_string is improperly formatted.
  """
  color_msg = _GetMessageClass('GooglePrivacyDlpV2Color')
  red, green, blue = _ValidateAndParseColors(color_string)
  return color_msg(red=red, blue=blue, green=green)


def GetJobScheduleDurationString(value):
  """Return API required format for duration specified by value."""
  return '{}s'.format(six.text_type(value))


# Additional Arguments Hook
def GetIdentifyingFieldsArg():
  """Capture identifying fields for BigQuery table."""
  help_text = ('Comma separated list of references to field names uniquely '
               'identifying rows within the BigQuery table. Nested fields in '
               'the format `person.birthdate.year` are allowed.')
  return [
      base.Argument(
          '--identifying-fields',
          metavar='IDENTIFYING_FIELDS',
          type=arg_parsers.ArgList(),
          help=help_text)
  ]


def _PossiblyWriteRedactedResponseToOutputFile(value, parsed_args):
  """Helper function for writing redacted contents to an output file."""
  if not parsed_args.output_file:
    return
  with files.BinaryFileWriter(parsed_args.output_file) as outfile:
    outfile.write(value)
  log.status.Print('The redacted contents can be viewed in [{}]'.format(
      parsed_args.output_file))


def PossiblyWriteRedactedTextResponseToOutputFile(response, parsed_args):
  """Write the contents of the redacted text file to parsed_args.output_file."""
  _PossiblyWriteRedactedResponseToOutputFile(response.item.value, parsed_args)
  return response


def PossiblyWriteRedactedImageResponseToOutputFile(response, parsed_args):
  """Write the redacted image to parsed_args.output_file."""
  _PossiblyWriteRedactedResponseToOutputFile(response.redactedImage,
                                             parsed_args)
  return response


def AddOutputFileFlag():
  """Add --output-file to a redact command."""
  return [
      base.Argument(
          '--output-file',
          help='Path to the file to write redacted contents to.')
  ]
