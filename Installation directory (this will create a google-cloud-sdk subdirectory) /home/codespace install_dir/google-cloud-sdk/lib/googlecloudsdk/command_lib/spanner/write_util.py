# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Provides helper methods for dealing with Cloud Spanner Writes API.

  The main reasons for adding the util functions for Writes API are as below:
    - API expects column values to be extra_types.JsonValue, apitool cannot
      handle it by default.
    - for different data types the API expects different formats, for example:
      for INT64, API expects a string value; for FLOAT64, it expects a number.
      As the values user input are strings by default, the type conversion is
      necessary.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
from collections import OrderedDict
import re
from apitools.base.py import extra_types
from googlecloudsdk.core.exceptions import Error
import six
from six.moves import zip


class BadColumnNameError(Error):
  """Raised when a column name entered by user is not found in the table."""


class BadTableNameError(Error):
  """Raised when a table name entered by user is not found in the database."""


class InvalidKeysError(Error):
  """Raised when the number of keys user input does not match the DDL."""


class InvalidArrayInputError(Error):
  """Raised when the user tries to input a list as a value in the data flag."""


class _TableColumn(object):
  """A wrapper that stores the column information.

  Attributes:
    name: String, the name of the table column.
    col_type: _ScalarColumnType or _ArrayColumnType.
  """
  _COLUMN_DDL_PATTERN = re.compile(
      r"""
            # A column definition has a name and a type, with some additional
            # properties.
            # Some examples:
            #    Foo INT64 NOT NULL
            #    Bar STRING(1024)
            #    Baz ARRAY<FLOAT32>
            [`]?(?P<name>\w+)[`]?\s+
            (?P<type>[\w<>]+)
            # We don't care about "NOT NULL", and the length number after STRING
            # or BYTES (e.g.STRING(MAX), BYTES(1024)).
        """, re.DOTALL | re.VERBOSE)

  def __init__(self, name, col_type):
    self.name = name
    self.col_type = col_type

  def __eq__(self, other):
    return self.name == other.name and self.col_type == other.col_type

  @classmethod
  def FromDdl(cls, column_ddl):
    """Constructs an instance of _TableColumn from a column_def DDL statement.

    Args:
      column_ddl: string, the parsed string contains the column name and type
        information. Example: SingerId INT64 NOT NULL.

    Returns:
      A _TableColumn object.

    Raises:
      ValueError: invalid DDL, this error shouldn't happen in theory, as the API
        is expected to return valid DDL statement strings.
    """
    column_match = cls._COLUMN_DDL_PATTERN.search(column_ddl)
    if not column_match:
      raise ValueError('Invalid DDL: [{}].'.format(column_ddl))
    column_name = column_match.group('name')
    col_type = _ColumnType.FromDdl(column_match.group('type'))

    return _TableColumn(column_name, col_type)

  def GetJsonValues(self, value):
    """Convert the user input values to JSON value or JSON array value.

    Args:
      value: String or string list, the user input values of the column.

    Returns:
      extra_types.JsonArray or extra_types.JsonValue, the json value of a single
          column in the format that API accepts.
    """
    return self.col_type.GetJsonValue(value)


class _ColumnType(six.with_metaclass(abc.ABCMeta, object)):
  """A wrapper that stores the column type information.

  A column type can be one of the scalar types such as integers, as well as
      array. An array type is an ordered list of zero or more elements of
      scalar type.

  Attributes:
    scalar_type: String, the type of the column or the element of the column
        (if the column is an array).
  """
  # For Scalar types: there are 8 scalar types in Cloud Spanner considered as
  # valid key and column types. 'JSON', 'TOKENLIST' however, are not valid key
  # types.
  _SCALAR_TYPES = ('BOOL', 'BYTES', 'DATE', 'FLOAT64', 'INT64', 'STRING',
                   'TIMESTAMP', 'NUMERIC', 'JSON', 'TOKENLIST')

  def __init__(self, scalar_type):
    self.scalar_type = scalar_type

  @classmethod
  def FromDdl(cls, column_type_ddl):
    """Constructs a _ColumnType object from a partial DDL statement.

    Args:
      column_type_ddl: string, the parsed string only contains the column type
        information. Example: INT64 NOT NULL, ARRAY<STRING(MAX)> or BYTES(200).

    Returns:
      A _ArrayColumnType or a _ScalarColumnType object.

    Raises:
      ValueError: invalid DDL, this error shouldn't happen in theory, as the API
        is expected to return valid DDL statement strings.
    """
    scalar_match = None
    for data_type in cls._SCALAR_TYPES:
      if data_type in column_type_ddl:
        scalar_match = data_type
        break

    if not scalar_match:
      raise ValueError(
          'Invalid DDL: unrecognized type [{}].'.format(column_type_ddl))

    if column_type_ddl.startswith('ARRAY'):
      return _ArrayColumnType(scalar_match)
    else:
      return _ScalarColumnType(scalar_match)

  @abc.abstractmethod
  def GetJsonValue(self, value):
    raise NotImplementedError()


def ConvertJsonValueForScalarTypes(scalar_type, scalar_value):
  """Convert the user input scalar value to JSON value.

  Args:
    scalar_type: String, the scalar type of the column, e.g INT64, DATE.
    scalar_value: String, the value of the column that user inputs.

  Returns:
    An API accepts JSON value of a column or an element of an array column.
  """
  if scalar_value == 'NULL':
    return extra_types.JsonValue(is_null=True)
  elif scalar_type == 'BOOL':
    # True and true are valid boolean values.
    bool_value = scalar_value.upper() == 'TRUE'
    return extra_types.JsonValue(boolean_value=bool_value)
  elif scalar_type == 'FLOAT64':
    # NaN, +/-inf are valid float values.
    if scalar_value in ('NaN', 'Infinity', '-Infinity'):
      return extra_types.JsonValue(string_value=scalar_value)
    else:
      return extra_types.JsonValue(double_value=float(scalar_value))
  else:
    # TODO(b/73077622): add bytes conversion.
    # For other data types (INT, STRING, TIMESTAMP, DATE, NUMERIC, JSON), the
    # json format would be string.
    return extra_types.JsonValue(string_value=scalar_value)


class _ScalarColumnType(_ColumnType):

  def __init__(self, scalar_type):
    super(_ScalarColumnType, self).__init__(scalar_type)

  def __eq__(self, other):
    return self.scalar_type == other.scalar_type and isinstance(
        other, _ScalarColumnType)

  def GetJsonValue(self, value):
    return ConvertJsonValueForScalarTypes(self.scalar_type, value)


class _ArrayColumnType(_ColumnType):

  def __init__(self, scalar_type):
    super(_ArrayColumnType, self).__init__(scalar_type)

  def __eq__(self, other):
    return self.scalar_type == other.scalar_type and isinstance(
        other, _ArrayColumnType)

  def GetJsonValue(self, values):
    return extra_types.JsonValue(
        array_value=extra_types.JsonArray(entries=[
            ConvertJsonValueForScalarTypes(self.scalar_type, v) for v in values
        ]))


class ColumnJsonData(object):
  """Container for the column name and value to be written in a table.

  Attributes:
    col_name: String, the name of the column to be written.
    col_value: extra_types.JsonArray(array column) or
      extra_types.JsonValue(scalar column), the value to be written.
  """

  def __init__(self, col_name, col_value):
    self.col_name = col_name
    self.col_value = col_value


class Table(object):
  """Container for the properties of a table in Cloud Spanner database.

  Attributes:
    name: String, the name of table.
    _columns: OrderedDict, with keys are the column names and values are the
      _TableColumn objects.
    _primary_keys: String list, the names of the primary key columns in the
      order defined in the DDL statement
  """
  _TABLE_DDL_PATTERN = re.compile(
      r"""
          # Every table starts with "CREATE TABLE" followed by name and column
          # definitions, in a big set of parenthesis.
          # For example:
          #    CREATE TABLE Foos (
          #        Bar INT64 NOT NULL,
          #        Baz INT64 NOT NULL,
          #        Qux STRING(MAX),
          #    )
          CREATE\s+TABLE\s+
          (?P<name>[\w\.]+)\s+\(\s+
          (?P<columns>.*)\)\s+
          # Then, it has "PRIMARY KEY" and a list of primary keys, in parens:
          # PRIMARY KEY ( Bar, Qux )
          PRIMARY\s+KEY\s*\(
          (?P<primary_keys>.*)\)
          # It may have extra instructions on the end (e.g. INTERLEAVE) to
          # tell Spanner how to store the data, but we don't really care.
      """, re.DOTALL | re.VERBOSE)

  def __init__(self, table_name, _columns, _primary_keys=None):
    self.name = table_name
    self._columns = _columns
    self._primary_keys = _primary_keys or []

  def GetJsonData(self, data_dict):
    """Get the column names and values to be written from data input.

    Args:
      data_dict: Dictionary where keys are the column names and values are user
          input data value, which is parsed from --data argument in the command.

    Returns:
      List of ColumnJsonData, which includes the column names and values to be
        written.
    """
    column_list = []

    for col_name, col_value in six.iteritems(data_dict):
      col_in_table = self._FindColumnByName(col_name)
      col_json_value = col_in_table.GetJsonValues(col_value)
      column_list.append(ColumnJsonData(col_name, col_json_value))

    return column_list

  def GetJsonKeys(self, keys_list):
    """Get the primary key values to be written from keys input.

    Args:
      keys_list: String list, the primary key values of the row to be deleted.

    Returns:
      List of extra_types.JsonValue.

    Raises:
      InvalidKeysError: the keys are invalid.
    """

    # Raise an exception when the number of keys entered by user does not
    # match the number of the primary key columns in the current table.
    if len(keys_list) != len(self._primary_keys):
      raise InvalidKeysError(
          'Invalid keys. There are {} primary key columns in the table [{}]. '
          '{} are given.'.format(
              len(self._primary_keys), self.name, len(keys_list)))

    keys_json_list = []

    for key_name, key_value in zip(self._primary_keys, keys_list):
      col_in_table = self._FindColumnByName(key_name)
      col_json_value = col_in_table.GetJsonValues(key_value)
      keys_json_list.append(col_json_value)

    return keys_json_list

  @classmethod
  def FromDdl(cls, database_ddl, table_name):
    """Constructs a Table from ddl statements.

    Args:
      database_ddl: String list, the ddl statements of the current table from
          server.
      table_name: String, the table name user inputs.

    Returns:
      Table.

    Raises:
      BadTableNameError: the table name is invalid.
      ValueError: Invalid Ddl.
    """
    # A list of all the table names in the current database.
    table_name_list = []

    for ddl in database_ddl:
      # If the ddl statement is a create table statement and matches the given
      # table name, parse the string and return the table object.
      table_match = cls._TABLE_DDL_PATTERN.search(ddl)
      if not table_match:
        continue

      name = table_match.group('name')
      if name != table_name:
        # Store all valid table names of the database.
        table_name_list.append(name)
        continue

      column_defs = table_match.group('columns')
      column_dict = OrderedDict()

      for column_ddl in column_defs.split(','):
        # It can be an empty string at the end of the list.
        if column_ddl and not column_ddl.isspace():
          column = _TableColumn.FromDdl(column_ddl)
          column_dict[column.name] = column
      # Set the primary key list in the table.
      # Example: PRIMARY KEY ( Bar, Qux ) -> [Bar,Qux].
      raw_primary_keys = table_match.groupdict()['primary_keys']
      primary_keys_list = [k.strip() for k in raw_primary_keys.split(',')]

      return Table(table_name, column_dict, primary_keys_list)

    raise BadTableNameError(
        'Table name [{}] is invalid. Valid table names: [{}].'.format(
            table_name, ', '.join(table_name_list)))

  def GetColumnTypes(self):
    """Maps the column name to the column type.

    Returns:
      OrderedDict of column names to types.
    """
    col_to_type = OrderedDict()
    for name, column in six.iteritems(self._columns):
      col_to_type[name] = column.col_type
    return col_to_type

  def _FindColumnByName(self, col_name):
    """Find the _TableColumn object with the given column name.

    Args:
      col_name: String, the name of the column.

    Returns:
      _TableColumn.

    Raises:
      BadColumnNameError: the column name is invalid.
    """
    try:
      return self._columns[col_name]
    except KeyError:
      valid_column_names = ', '.join(list(self._columns.keys()))
      raise BadColumnNameError(
          'Column name [{}] is invalid. Valid column names: [{}].'.format(
              col_name, valid_column_names))


def ValidateArrayInput(table, data):
  """Checks array input is valid.

  Args:
    table: Table, the table which data is being modified.
    data: OrderedDict, the data entered by the user.

  Returns:
    data (OrderedDict) the validated data.

  Raises:
    InvalidArrayInputError: if the input contains an array which is invalid.
  """
  col_to_type = table.GetColumnTypes()
  for column, value in six.iteritems(data):
    col_type = col_to_type[column]
    if isinstance(col_type,
                  _ArrayColumnType) and isinstance(value, list) is False:
      raise InvalidArrayInputError(
          'Column name [{}] has an invalid array input: {}. `--flags-file` '
          'should be used to specify array values.'.format(column, value))
  return data
