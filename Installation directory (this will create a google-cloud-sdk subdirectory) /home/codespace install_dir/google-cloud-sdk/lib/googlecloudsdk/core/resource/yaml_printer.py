# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""YAML format printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import io

from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer_base
from googlecloudsdk.core.resource import resource_transform
from googlecloudsdk.core.yaml import dict_like
from googlecloudsdk.core.yaml import list_like

import six
from six.moves import range  # pylint: disable=redefined-builtin


class YamlPrinter(resource_printer_base.ResourcePrinter):
  """Prints the YAML representations of JSON-serializable objects.

  [YAML](http://www.yaml.org), YAML ain't markup language.

  Printer attributes:
    null="string": Display string instead of `null` for null/None values.
    no-undefined: Does not display resource data items with null values.
    version=VERSION: Prints using the specified YAML version, default 1.2.

  For example:

    printer = YamlPrinter(log.out)
    printer.AddRecord({'a': ['hello', 'world'], 'b': {'x': 'bye'}})

  produces:

    ---
    a:
      - hello
      - world
    b:
      - x: bye

  Attributes:
    _yaml: Reference to the `yaml` module. Imported locally to improve startup
        performance.
  """

  def __init__(self, *args, **kwargs):
    super(YamlPrinter, self).__init__(*args, retain_none_values=True, **kwargs)
    # pylint:disable=g-import-not-at-top, Delay import for performance.
    from ruamel import yaml
    # Use pure=True to only use python implementations. Otherwise, it can load
    # the the _ruamel_yaml C extension from site packages if
    # CLOUDSDK_PYTHON_SITEPACKAGES=1 is set. There is no guarantee that the C
    # extension is compatible with our vendored ruamel.yaml and the python
    # runtime.
    self._yaml = yaml.YAML(typ='safe', pure=True)
    self._yaml.default_flow_style = False
    self._yaml.old_indent = resource_printer_base.STRUCTURED_INDENTATION
    self._yaml.allow_unicode = True
    self._yaml.encoding = log.LOG_FILE_ENCODING

    null = self.attributes.get('null')
    version = self.attributes.get('version')
    # If no version specified, uses ruamel's default (1.2)
    if version:
      self._yaml.version = str(version)

    def _FloatPresenter(unused_dumper, data):
      return yaml.nodes.ScalarNode(
          'tag:yaml.org,2002:float', resource_transform.TransformFloat(data))

    def _LiteralLinesPresenter(dumper, data):
      return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

    def _NullPresenter(dumper, unused_data):
      if null in ('null', None):
        return dumper.represent_scalar('tag:yaml.org,2002:null', 'null')
      return dumper.represent_scalar('tag:yaml.org,2002:str', null)

    def _OrderedDictPresenter(dumper, data):
      return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

    def _UndefinedPresenter(dumper, data):
      r = repr(data)
      if r == '[]':
        return dumper.represent_list([])
      if r == '{}':
        return dumper.represent_dict({})
      dumper.represent_undefined(data)

    self._yaml.representer.add_representer(float,
                                           _FloatPresenter)
    self._yaml.representer.add_representer(YamlPrinter._LiteralLines,
                                           _LiteralLinesPresenter)
    self._yaml.representer.add_representer(None,
                                           _UndefinedPresenter)
    self._yaml.representer.add_representer(type(None),
                                           _NullPresenter)
    self._yaml.representer.add_representer(collections.OrderedDict,
                                           _OrderedDictPresenter)

  class _LiteralLines(six.text_type):
    """A yaml representer hook for literal strings containing newlines."""

  def _UpdateTypesForOutput(self, val):
    """Dig through a dict of list of primitives to help yaml output.

    Args:
      val: A dict, list, or primitive object.

    Returns:
      An updated version of val.
    """
    if isinstance(val, six.string_types) and '\n' in val:
      return YamlPrinter._LiteralLines(val)
    if list_like(val):
      for i in range(len(val)):
        val[i] = self._UpdateTypesForOutput(val[i])
      return val
    if dict_like(val):
      for key in val:
        val[key] = self._UpdateTypesForOutput(val[key])
      return val
    return val

  def _AddRecord(self, record, delimit=True):
    """Immediately prints the given record as YAML.

    Args:
      record: A YAML-serializable Python object.
      delimit: Prints resource delimiters if True.
    """
    stream = self._out
    # In python 2, to dump unicode in ruamel, we need to use a byte stream,
    # and handle the decoding ourselves. python 3 can handle it correctly.
    if six.PY2 and  isinstance(self._out, io.StringIO):
      stream = io.BytesIO()
    record = self._UpdateTypesForOutput(record)
    self._yaml.explicit_start = delimit
    self._yaml.dump(
        record,
        stream=stream)
    if stream is not self._out:
      self._out.write(stream.getvalue().decode(log.LOG_FILE_ENCODING))
