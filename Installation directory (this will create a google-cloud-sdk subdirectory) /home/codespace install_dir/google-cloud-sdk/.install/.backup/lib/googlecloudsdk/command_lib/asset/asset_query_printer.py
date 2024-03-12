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
"""Custom table printer for CAI team's asset query API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io

from apitools.base.py import extra_types
from googlecloudsdk.core.resource import custom_printer_base as cp
from googlecloudsdk.core.resource import resource_printer

# Defined to match service name (cloudasset.googleapis.com).
ASSET_QUERY_PRINTER_FORMAT = 'cloudasset'


class AssetQueryPrinter(cp.CustomPrinterBase):
  """Prints the asset query response in a custom human readable format."""

  @staticmethod
  def Register(parser):
    """Register this custom printer with the given parser."""
    resource_printer.RegisterFormatter(
        ASSET_QUERY_PRINTER_FORMAT, AssetQueryPrinter, hidden=True)
    parser.display_info.AddFormat(ASSET_QUERY_PRINTER_FORMAT)

  def _FormatMetadata(self, resp):
    # Turn the response into a dict, remove rows and schema, output the rest.
    resp_message = extra_types.encoding.MessageToPyValue(resp)
    if 'queryResult' in resp_message:
      if 'rows' in resp_message['queryResult']:
        del resp_message['queryResult']['rows']
      if 'schema' in resp_message['queryResult']:
        del resp_message['queryResult']['schema']
      if not resp_message['queryResult']:
        # If the queryResult only had a schema, don't print it out.
        del resp_message['queryResult']
    string_buf = io.StringIO()
    resource_printer.Print(resp_message, 'yaml', out=string_buf)
    return string_buf.getvalue()

  # pylint: disable=line-too-long
  def _FormatRowTable(self, resp):
    """Formats rows in a [QueryAssetsResponse]'s queryResults into a table.

    Args:
      resp: The [QueryAssetsResponse] that contains 0 or more rows.

    Returns:
      A 'Lines' custom printer object that corresponds to the formatted table
      when printed out.

    The response.queryResult.rows in response:
    {
      "jobReference":
      "CiBqb2JfdDR2SFgwa3BPNFpQVDFudVJJaW5TdVNfS1N0YxIBAxjH8ZmAo6qckik",
      "done": true,
      "queryResult": {
        "rows": [
          {
            "f": [
              {
                "v":
                "//cloudresourcemanager.googleapis.com/folders/417243649856"
              }
            ]
          }
        ],
        "schema": {
          "fields": [
            {
              "field": "name",
              "type": "STRING",
              "mode": "NULLABLE"
            }
          ]
        },
        "total_rows": 1
      }
    }
    Will return a custom printer Lines object holding the following string:
    ┌────────────────────────────────────────────────────────────┐
    │                            name                            │
    ├────────────────────────────────────────────────────────────┤
    │ //cloudresourcemanager.googleapis.com/folders/417243649856 │
    └────────────────────────────────────────────────────────────┘
    """
    # pylint: enable=line-too-long

    # Used to catch and stop the unexpected secondary call of the
    # Display() function with invalid data.
    if not hasattr(resp, 'queryResult') or not hasattr(resp.queryResult,
                                                       'schema'):
      return None

    schema = resp.queryResult.schema
    rows = resp.queryResult.rows
    row_list = []
    # Create a list of base-level schema keys,
    # and populate the table formatting string used by printer at the same time.
    if not schema.fields:
      # Received an empty schema, nothing to process.
      return None
    schemabuf = io.StringIO()
    schemabuf.write('table[box]({})'.format(', '.join(
        '{}:label={}'.format(field.field, field.field)
        for field in schema.fields)))

    for row in rows:
      # Convert from 'f' 'v' key:value representations to an appropriate struct
      # to pass to ConvertFromFV()
      row_json = extra_types.encoding.MessageToPyValue(row)
      schema_json = extra_types.encoding.MessageToPyValue(schema)
      row_list.append(self._ConvertFromFV(schema_json, row_json, False))
    raw_out = io.StringIO()
    resource_printer.Print(row_list, schemabuf.getvalue(), out=raw_out)
    # cp.Lines simply tells the custom printer to print the provided
    # strings as is with no modification.
    return cp.Lines([raw_out.getvalue()])

  def _ConvertFromFV(self, schema, row, is_record):
    """Converts from FV format to values.

    Args:
      schema: The schema struct within the queryResult struct in the response.
      row: A single row of the response's queryResult.rows message.
      is_record: True if the row object is a record within an actual row.

    Returns:
      A dictionary mapping row keys to the values that may be a simple datatype,
      a record (struct) in the form of a dictionary, or a list of either simple
      data types or records (again, in the form of dictionaries).

    Raises:
      IOError: An error occurred accessing the smalltable.
    """
    if not row:
      return ''

    values = [entry.get('v', '') for entry in row.get('f', [])]
    result = {}
    new_schema = schema
    if not is_record:
      new_schema = schema['fields']

    for field, v in zip(new_schema, values):
      if 'type' not in field:
        raise IOError('Invalid response: missing type property')
      if field['type'].upper() == 'RECORD':
        # Nested field.
        subfields = field.get('fields', [])
        if field.get('mode', 'NULLABLE').upper() == 'REPEATED':
          # Repeated and nested. Convert the array of v's of FV's.
          result[field['field']] = [
              self._ConvertFromFV(subfields, subvalue.get('v', ''), True)
              for subvalue in v
          ]
        else:
          # Nested non-repeated field. Convert the nested f from FV.
          cur_val = self._ConvertFromFV(subfields, v, True)
          if cur_val:
            result[field['field']] = cur_val
          else:
            result[field['field']] = ''
      elif field.get('mode', 'NULLABLE').upper() == 'REPEATED':
        # Repeated but not nested: an array of v's.
        cur_val = [subvalue.get('v', '') for subvalue in v]
        result[field['field']] = cur_val if cur_val is not None else ''
      else:
        # Normal flat field.
        result[field['field']] = v if v else ''
    return result

  def Transform(self, resp):
    """Transforms a CAI [QueryAssetsResponse] into human-readable format."""
    # The response should have either an error field or a jobReference field.
    # Otherwise, the response is considered malformed and disregarded.
    if not hasattr(resp, 'jobReference') and not hasattr(resp, 'error'):
      return None
    metadata = self._FormatMetadata(resp)
    rows = self._FormatRowTable(resp)
    sections_list = []
    if metadata:
      sections_list.append(metadata)
    if rows:
      sections_list.append(rows)

    return cp.Section(sections_list, max_column_width=60)
