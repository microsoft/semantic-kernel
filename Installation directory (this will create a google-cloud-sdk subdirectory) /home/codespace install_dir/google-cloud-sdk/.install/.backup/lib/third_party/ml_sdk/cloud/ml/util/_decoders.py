# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Dataflow-related utilities.
"""

import csv
import json
import logging


class DecodeError(Exception):
  """Base decode error."""
  pass


class PassthroughDecoder(object):

  def decode(self, x):
    return x


class JsonDecoder(object):
  """A decoder for JSON formatted data."""

  def decode(self, x):
    return json.loads(x)


class CsvDecoder(object):
  """A decoder for CSV formatted data.
  """

  # TODO(user) Revisit using cStringIO for design compatibility with
  # coders.CsvCoder.
  class _LineGenerator(object):
    """A csv line generator that allows feeding lines to a csv.DictReader."""

    def __init__(self):
      self._lines = []

    def push_line(self, line):
      # This API currently supports only one line at a time.
      assert not self._lines
      self._lines.append(line)

    def __iter__(self):
      return self

    def next(self):
      # This API currently supports only one line at a time.
      # If this ever supports more than one row be aware that DictReader might
      # attempt to read more than one record if one of the records is empty line
      line_length = len(self._lines)
      if line_length == 0:
        raise DecodeError(
            'Columns do not match specified csv headers: empty line was found')
      assert line_length == 1, 'Unexpected number of lines %s' % line_length
      # This doesn't maintain insertion order to the list, which is fine
      # because the list has only 1 element. If there were more and we wanted
      # to maintain order and timecomplexity we would switch to deque.popleft.
      return self._lines.pop()

  class _ReaderWrapper(object):
    """A wrapper for csv.reader / csv.DictReader to make it picklable."""

    def __init__(self, line_generator, column_names, delimiter, decode_to_dict,
                 skip_initial_space):
      self._state = (line_generator, column_names, delimiter, decode_to_dict,
                     skip_initial_space)
      self._line_generator = line_generator
      if decode_to_dict:
        self._reader = csv.DictReader(
            line_generator, column_names, delimiter=str(delimiter),
            skipinitialspace=skip_initial_space)
      else:
        self._reader = csv.reader(line_generator, delimiter=str(delimiter),
                                  skipinitialspace=skip_initial_space)

    def read_record(self, x):
      self._line_generator.push_line(x)
      return self._reader.next()

    def __getstate__(self):
      return self._state

    def __setstate__(self, state):
      self.__init__(*state)

  def __init__(
      self, column_names, numeric_column_names, delimiter, decode_to_dict,
      fail_on_error, skip_initial_space):
    """Initializer.

    Args:
      column_names: Tuple of strings. Order must match the order in the file.
      numeric_column_names: Tuple of strings. Contains column names that are
          numeric. Every name in numeric_column_names must also be in
          column_names.
      delimiter:  String used to separate fields.
      decode_to_dict: Boolean indicating whether the docoder should generate a
          dictionary instead of a raw sequence. True by default.
      fail_on_error: Whether to fail if a corrupt row is found.
      skip_initial_space: When True, whitespace immediately following the
          delimiter is ignored.
    """
    self._column_names = column_names
    self._numeric_column_names = set(numeric_column_names)
    self._reader = self._ReaderWrapper(
        self._LineGenerator(), column_names, delimiter, decode_to_dict,
        skip_initial_space)
    self._decode_to_dict = decode_to_dict
    self._fail_on_error = fail_on_error

  def _handle_corrupt_row(self, message):
    """Handle corrupt rows.

    Depending on whether the decoder is configured to fail on error it will
    raise a DecodeError or return None.

    Args:
      message: String, the error message to raise.
    Returns:
      None, when the decoder is not configured to fail on error.
    Raises:
      DecodeError: when the decoder is configured to fail on error.
    """
    if self._fail_on_error:
      raise DecodeError(message)
    else:
      # TODO(user) Don't log every time but only every N invalid lines.
      logging.warning('Discarding invalid row: %s', message)
      return None

  def _get_value(self, column_name, value):
    # TODO(user) remove this logic from the decoders and let it be
    # part of prepreocessing. CSV is a schema-less container we shouldn't be
    # performing these conversions here.
    if not value or not value.strip():
      return None
    if column_name in self._numeric_column_names:
      return float(value)
    return value

  # Please run //third_party/py/google/cloud/ml:benchmark_coders_test
  # if you make any changes on these methods.
  def decode(self, record):
    """Decodes the given string.

    Args:
      record: String to be decoded.

    Returns:
      Serialized object corresponding to decoded string. Or None if there's an
      error and the decoder is configured not to fail on error.

    Raises:
      DecodeError: If columns do not match specified csv headers.
      ValueError: If some numeric column has non-numeric data.
    """
    try:
      record = self._reader.read_record(record)
    except Exception as e:  # pylint: disable=broad-except
      return self._handle_corrupt_row('%s: %s' % (e, record))
    # Check record length mismatches.
    if len(record) != len(self._column_names):
      return self._handle_corrupt_row(
          'Columns do not match specified csv headers: %s -> %s' % (
              self._column_names, record))

    if self._decode_to_dict:
      # DictReader fills missing colums with None. Thus, if the last value
      # as defined by the schema is None, there was at least one "missing"
      # column.
      if record[self._column_names[-1]] is None:
        return self._handle_corrupt_row(
            'Columns do not match specified csv headers: %s -> %s' % (
                self._column_names, record))
      for name, value in record.iteritems():
        record[name] = self._get_value(name, value)
    else:
      for index, name in enumerate(self._column_names):
        value = record[index]
        record[index] = self._get_value(name, value)
    return record
