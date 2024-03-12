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

"""Wrapper module for ensuring consistent usage of yaml parsing.

This module forces parsing to use version 1.1 of the YAML spec if not
otherwise specified by the loading method arguments.
However, dumping uses version 1.2.
It also prevents use of unsafe loading and dumping.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml_location_value
from googlecloudsdk.core.util import files

from ruamel import yaml
import six

try:
  # Python 3.3 and above.
  collections_abc = collections.abc
except AttributeError:
  collections_abc = collections


VERSION_1_1 = '1.1'
VERSION_1_2 = '1.2'


# YAML unfortunately uses a bunch of global class state for this kind of stuff.
# We don't have to do it at import but the other option would be to do it every
# time we try to dump something (which is worse for performance that just
# doing it once). This allows OrderedDicts to be serialized as if they were
# normal dicts.
yaml.add_representer(
    collections.OrderedDict,
    yaml.dumper.SafeRepresenter.represent_dict,
    Dumper=yaml.dumper.SafeDumper)
yaml.add_representer(
    collections.OrderedDict,
    yaml.dumper.RoundTripRepresenter.represent_dict,
    Dumper=yaml.dumper.RoundTripDumper)


# Always output None as "null", instead of just empty.
yaml.add_representer(
    type(None),
    lambda self, _: self.represent_scalar('tag:yaml.org,2002:null', 'null'),
    Dumper=yaml.dumper.RoundTripDumper)


class Error(exceptions.Error):
  """Top level error for this module.

  Attributes:
    inner_error: Exception, The original exception that is being wrapped. This
      will always be populated.
    file: str, The path to the thing being loaded (if applicable). This is not
      necessarily a literal file (it could be a URL or any hint the calling
      code passes in). It should only be used for more descriptive error
      messages.
  """

  def __init__(self, e, verb, f=None):
    file_text = ' from [{}]'.format(f) if f else ''
    super(Error, self).__init__(
        'Failed to {} YAML{}: {}'.format(verb, file_text, e))
    self.inner_error = e
    self.file = f


class YAMLParseError(Error):
  """An error that wraps all YAML parsing errors."""

  def __init__(self, e, f=None):
    super(YAMLParseError, self).__init__(e, verb='parse', f=f)


class FileLoadError(Error):
  """An error that wraps errors when loading/reading files."""

  def __init__(self, e, f):
    super(FileLoadError, self).__init__(e, verb='load', f=f)


def load(
    stream,
    file_hint=None,
    round_trip=False,
    location_value=False,
    version=VERSION_1_1,
    preserve_quotes=None,
):
  """Loads YAML from the given steam.

  Args:
    stream: A file like object or string that can be read from.
    file_hint: str, The name of a file or url that the stream data is coming
      from. This is used for better error handling. If you have the actual file,
      you should use load_file() instead. Sometimes the file cannot be read
      directly so you can use a stream here and hint as to where the data is
      coming from.
    round_trip: bool, True to use the RoundTripLoader which preserves ordering
      and line numbers.
    location_value: bool, True to use a loader that preserves ordering and line
      numbers for all values. Each YAML data item is an object with value and lc
      attributes, where lc.line and lc.col are the line and column location for
      the item in the YAML source file.
    version: str, YAML version to use when parsing.
    preserve_quotes: bool, True preserve all the quotes.

  Raises:
    YAMLParseError: If the data could not be parsed.

  Returns:
    The parsed YAML data.
  """
  try:
    if location_value:
      return yaml_location_value.LocationValueLoad(stream)
    loader = yaml.RoundTripLoader if round_trip else yaml.SafeLoader
    return yaml.load(
        stream, loader, version=version, preserve_quotes=preserve_quotes
    )
  except yaml.YAMLError as e:
    raise YAMLParseError(e, f=file_hint)


def load_all(stream, file_hint=None, version=VERSION_1_1, round_trip=False):
  """Loads multiple YAML documents from the given steam.

  Args:
    stream: A file like object or string that can be read from.
    file_hint: str, The name of a file or url that the stream data is coming
      from. See load() for more information.
    version: str, YAML version to use when parsing.
    round_trip: bool, True to use the RoundTripLoader which preserves ordering
      and line numbers.

  Raises:
    YAMLParseError: If the data could not be parsed.

  Yields:
    The parsed YAML data.
  """
  loader = yaml.RoundTripLoader if round_trip else yaml.SafeLoader
  try:
    for x in yaml.load_all(stream, loader, version=version):
      yield x
  except yaml.YAMLError as e:
    raise YAMLParseError(e, f=file_hint)


def load_path(
    path,
    round_trip=False,
    location_value=False,
    version=VERSION_1_1,
    preserve_quotes=None,
):
  """Loads YAML from the given file path.

  Args:
    path: str, A file path to open and read from.
    round_trip: bool, True to use the RoundTripLoader which preserves ordering
      and line numbers.
    location_value: bool, True to use a loader that preserves ordering and line
      numbers for all values. Each YAML data item is an object with value and lc
      attributes, where lc.line and lc.col are the line and column location for
      the item in the YAML source file.
    version: str, YAML version to use when parsing.
    preserve_quotes: bool, True preserve all the quotes.

  Raises:
    YAMLParseError: If the data could not be parsed.
    FileLoadError: If the file could not be opened or read.

  Returns:
    The parsed YAML data.
  """
  try:
    with files.FileReader(path) as fp:
      return load(
          fp,
          file_hint=path,
          round_trip=round_trip,
          location_value=location_value,
          version=version,
          preserve_quotes=preserve_quotes,
      )
  except files.Error as e:
    raise FileLoadError(e, f=path)


def load_all_path(path, version=VERSION_1_1, round_trip=False):
  """Loads multiple YAML documents from the given file path.

  Args:
    path: str, A file path to open and read from.
    version: str, YAML version to use when parsing.
    round_trip: bool, True to use the RoundTripLoader which preserves ordering
      and line numbers.

  Raises:
    YAMLParseError: If the data could not be parsed.
    FileLoadError: If the file could not be opened or read.

  Yields:
    The parsed YAML data.
  """
  try:
    with files.FileReader(path) as fp:
      for x in load_all(fp,
                        file_hint=path,
                        version=version,
                        round_trip=round_trip):
        yield x
  except files.Error as e:
    # EnvironmentError is parent of IOError, OSError and WindowsError.
    # Raised when file does not exist or can't be opened/read.
    raise FileLoadError(e, f=path)


def dump(data, stream=None, round_trip=False, **kwargs):
  """Dumps the given YAML data to the stream.

  Args:
    data: The YAML serializable Python object to dump.
    stream: The stream to write the data to or None to return it as a string.
    round_trip: bool, True to use the RoundTripDumper which preserves ordering
      and line numbers if the yaml was loaded in round trip mode.
    **kwargs: Other arguments to the dump method.

  Returns:
    The string representation of the YAML data if stream is None.
  """
  method = yaml.round_trip_dump if round_trip else yaml.safe_dump
  return method(data, stream=stream, default_flow_style=False, indent=2,
                **kwargs)


def dump_all(documents, stream=None, **kwargs):
  """Dumps multiple YAML documents to the stream.

  Args:
    documents: An iterable of YAML serializable Python objects to dump.
    stream: The stream to write the data to or None to return it as a string.
    **kwargs: Other arguments to the dump method.

  Returns:
    The string representation of the YAML data if stream is None.
  """
  return yaml.safe_dump_all(
      documents, stream=stream, default_flow_style=False, indent=2, **kwargs)


def dump_all_round_trip(documents, stream=None, **kwargs):
  """Dumps multiple YAML documents to the stream using the RoundTripDumper.

  Args:
    documents: An iterable of YAML serializable Python objects to dump.
    stream: The stream to write the data to or None to return it as a string.
    **kwargs: Other arguments to the dump method.

  Returns:
    The string representation of the YAML data if stream is None.
  """
  return yaml.dump_all(
      documents, stream=stream, default_flow_style=False, indent=2,
      Dumper=yaml.RoundTripDumper, **kwargs)


def convert_to_block_text(data):
  r"""This processes the given dict or list so it will render as block text.

  By default, the yaml dumper will write multiline strings out as a double
  quoted string that just includes '\n'. Calling this on the data strucuture
  will make it use the '|-' notation.

  Args:
    data: {} or [], The data structure to process.
  """
  yaml.scalarstring.walk_tree(data)


def list_like(item):
  """Return True if the item is like a list: a MutableSequence."""
  return isinstance(item, collections_abc.MutableSequence)


def dict_like(item):
  """Return True if the item is like a dict: a MutableMapping."""
  return isinstance(item, collections_abc.MutableMapping)


def strip_locations(obj):
  if list_like(obj):
    return [strip_locations(item) for item in obj]
  if dict_like(obj):
    return {key: strip_locations(value) for key, value in six.iteritems(obj)}
  return obj.value
