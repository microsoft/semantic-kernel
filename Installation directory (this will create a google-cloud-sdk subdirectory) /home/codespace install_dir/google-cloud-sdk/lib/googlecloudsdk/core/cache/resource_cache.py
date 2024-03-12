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

"""The Cloud SDK resource cache.

A resource is an object maintained by a service. Each resource has a
corresponding URI. A URI is composed of one or more parameters. A
service-specific resource parser extracts the parameter tuple from a URI. A
corresponding resource formatter reconstructs the URI from the parameter tuple.

Each service has an API List request that returns the list of resource URIs
visible to the caller. Some APIs are aggregated and return the list of all URIs
for all parameter values. Other APIs are not aggregated and require one or more
of the parsed parameter tuple values to be specified in the list request. This
means that getting the list of all URIs for a non-aggregated resource requires
multiple List requests, ranging over the combination of all values for all
aggregate parameters.

A collection is list of resource URIs in a service visible to the caller. The
collection name uniqely identifies the collection and the service.

A resource cache is a persistent cache that stores parsed resource parameter
tuples for multiple collections. The data for a collection is in one or more
tables.

    +---------------------------+
    | resource cache            |
    | +-----------------------+ |
    | | collection            | |
    | | +-------------------+ | |
    | | | table             | | |
    | | | (key,...,col,...) | | |
    | | |       ...         | | |
    | | +-------------------+ | |
    | |         ...           | |
    | +-----------------------+ |
    |           ...             |
    +---------------------------+

A resource cache is implemented as a ResourceCache object that contains
Collection objects. A Collection is a virtual table that contains one or more
persistent cache tables. Each Collection is also an Updater that handles
resource parsing and updates. Updates are typically done by service List or
Query requests that populate the tables.

The Updater objects make this module resource agnostic. For example, there
could be updater objects that are not associated with a URI. The ResourceCache
doesn't care.

If the List request API for a collection aggregates then its parsed parameter
tuples are contained in one table. Otherwise the collection is stored in
multiple tables. The total number of tables is determined by the number of
aggregate parameters for the List API, and the number of values each aggregate
parameter can take on.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import os

from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import module_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.cache import exceptions
from googlecloudsdk.core.cache import file_cache
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files

import six

# Rollout hedge just in case a cache implementation causes problems.
try:
  from googlecloudsdk.core.cache import sqlite_cache  # pylint: disable=g-import-not-at-top, sqlite3 is not ubiquitous
except ImportError:
  sqlite_cache = None
if (sqlite_cache and
    'sql' in encoding.GetEncodedValue(
        os.environ, 'CLOUDSDK_CACHE_IMPLEMENTATION', 'sqlite')):
  PERSISTENT_CACHE_IMPLEMENTATION = sqlite_cache
else:
  PERSISTENT_CACHE_IMPLEMENTATION = file_cache

DEFAULT_TIMEOUT = 1*60*60
VERSION = 'googlecloudsdk.resource-1.0'


class ParameterInfo(object):
  """An object for accessing parameter values in the program state.

  "program state" is defined by this class.  It could include parsed command
  line arguments and properties.  The class also can also map between resource
  and program parameter names.

  Attributes:
    _additional_params: The list of parameter names not in the parsed resource.
    _updaters: A parameter_name => (Updater, aggregator) dict.
  """

  def __init__(self, additional_params=None, updaters=None):
    self._additional_params = additional_params or []
    self._updaters = updaters or {}

  def GetValue(self, parameter_name, check_properties=True):
    """Returns the program state string value for parameter_name.

    Args:
      parameter_name: The Parameter name.
      check_properties: Check the property value if True.

    Returns:
      The parameter value from the program state.
    """
    del parameter_name, check_properties
    return None

  def GetAdditionalParams(self):
    """Return the list of parameter names not in the parsed resource.

    These names are associated with the resource but not a specific parameter
    in the resource.  For example a global resource might not have a global
    Boolean parameter in the parsed resource, but its command line specification
    might require a --global flag to completly qualify the resource.

    Returns:
      The list of parameter names not in the parsed resource.
    """
    return self._additional_params

  def GetUpdater(self, parameter_name):
    """Returns the updater and aggregator property for parameter_name.

    Args:
      parameter_name: The Parameter name.

    Returns:
      An (updater, aggregator) tuple where updater is the Updater class and
      aggregator is True if this updater must be used to aggregate all resource
      values.
    """
    return self._updaters.get(parameter_name, (None, None))


class Parameter(object):
  """A parsed resource tuple parameter descriptor.

  A parameter tuple has one or more columns. Each has a Parameter descriptor.

  Attributes:
    column: The parameter tuple column index.
    name: The parameter name.
  """

  def __init__(self, column=0, name=None):
    self.column = column
    self.name = name


class _RuntimeParameter(Parameter):
  """A runtime Parameter.

  Attributes:
    aggregator: True if parameter is an aggregator (not aggregated by updater).
    generate: True if values must be generated for this parameter.
    updater_class: The updater class.
    value: A default value from the program state.
  """

  def __init__(self, parameter, updater_class, value, aggregator):
    super(_RuntimeParameter, self).__init__(
        parameter.column, name=parameter.name)
    self.generate = False
    self.updater_class = updater_class
    self.value = value
    self.aggregator = aggregator


class BaseUpdater(object):
  """A base object for thin updater wrappers."""


@six.add_metaclass(abc.ABCMeta)
class Updater(BaseUpdater):
  """A resource cache table updater.

  An updater returns a list of parsed parameter tuples that replaces the rows in
  one cache table. It can also adjust the table timeout.

  The parameters may have their own updaters. These objects are organized as a
  tree with one resource at the root.

  Attributes:
    cache: The persistent cache object.
    collection: The resource collection name.
    columns: The number of columns in the parsed resource parameter tuple.
    parameters: A list of Parameter objects.
    timeout: The resource table timeout in seconds, 0 for no timeout (0 is easy
      to represent in a persistent cache tuple which holds strings and numbers).
  """

  def __init__(self,
               cache=None,
               collection=None,
               columns=0,
               column=0,
               parameters=None,
               timeout=DEFAULT_TIMEOUT):
    """Updater constructor.

    Args:
      cache: The persistent cache object.
      collection: The resource collection name that (1) uniquely names the
        table(s) for the parsed resource parameters (2) is the lookup name of
        the resource URI parser. Resource collection names are unique by
        definition. Non-resource collection names must not clash with resource
        collections names. Prepending a '.' to non-resource collections names
        will avoid the clash.
      columns: The number of columns in the parsed resource parameter tuple.
        Must be >= 1.
      column: If this is an updater for an aggregate parameter then the updater
        produces a table of aggregate_resource tuples. The parent collection
        copies aggregate_resource[column] to a column in its own resource
        parameter tuple.
      parameters: A list of Parameter objects.
      timeout: The resource table timeout in seconds, 0 for no timeout.
    """
    super(Updater, self).__init__()
    self.cache = cache
    self.collection = collection
    self.columns = columns if collection else 1
    self.column = column
    self.parameters = parameters or []
    self.timeout = timeout or 0

  def _GetTableName(self, suffix_list=None):
    """Returns the table name; the module path if no collection.

    Args:
      suffix_list: a list of values to attach to the end of the table name.
        Typically, these will be aggregator values, like project ID.
    Returns: a name to use for the table in the cache DB.
    """
    if self.collection:
      name = [self.collection]
    else:
      name = [module_util.GetModulePath(self)]
    if suffix_list:
      name.extend(suffix_list)
    return '.'.join(name)

  def _GetRuntimeParameters(self, parameter_info):
    """Constructs and returns the _RuntimeParameter list.

    This method constructs a muable shadow of self.parameters with updater_class
    and table instantiations. Each runtime parameter can be:

    (1) A static value derived from parameter_info.
    (2) A parameter with it's own updater_class.  The updater is used to list
        all of the possible values for the parameter.
    (3) An unknown value (None).  The possible values are contained in the
        resource cache for self.

    The Select method combines the caller supplied row template and the runtime
    parameters to filter the list of parsed resources in the resource cache.

    Args:
      parameter_info: A ParamaterInfo object for accessing parameter values in
        the program state.

    Returns:
      The runtime parameters shadow of the immutable self.parameters.
    """
    runtime_parameters = []
    for parameter in self.parameters:
      updater_class, aggregator = parameter_info.GetUpdater(parameter.name)
      value = parameter_info.GetValue(
          parameter.name, check_properties=aggregator)
      runtime_parameter = _RuntimeParameter(
          parameter, updater_class, value, aggregator)
      runtime_parameters.append(runtime_parameter)
    return runtime_parameters

  def ParameterInfo(self):
    """Returns the parameter info object."""
    return ParameterInfo()

  def SelectTable(self, table, row_template, parameter_info, aggregations=None):
    """Returns the list of rows matching row_template in table.

    Refreshes expired tables by calling the updater.

    Args:
      table: The persistent table object.
      row_template: A row template to match in Select().
      parameter_info: A ParamaterInfo object for accessing parameter values in
        the program state.
      aggregations: A list of aggregation Parameter objects.

    Returns:
      The list of rows matching row_template in table.
    """
    if not aggregations:
      aggregations = []
    log.info('cache table=%s aggregations=[%s]',
             table.name,
             ' '.join(['{}={}'.format(x.name, x.value) for x in aggregations]))
    try:
      return table.Select(row_template)
    except exceptions.CacheTableExpired:
      rows = self.Update(parameter_info, aggregations)
      if rows is not None:
        table.DeleteRows()
        table.AddRows(rows)
        table.Validate()
      return table.Select(row_template, ignore_expiration=True)

  def Select(self, row_template, parameter_info=None):
    """Returns the list of rows matching row_template in the collection.

    All tables in the collection are in play. The row matching done by the
    cache layer conveniently prunes the number of tables accessed.

    Args:
      row_template: A row template tuple. The number of columns in the template
        must match the number of columns in the collection. A column with value
        None means match all values for the column. Each column may contain
        these wildcard characters:
          * - match any string of zero or more characters
          ? - match any character
        The matching is anchored on the left.
      parameter_info: A ParamaterInfo object for accessing parameter values in
        the program state.

    Returns:
      The list of rows that match the template row.
    """
    template = list(row_template)
    if self.columns > len(template):
      template += [None] * (self.columns - len(template))
    log.info(
        'cache template=[%s]', ', '.join(["'{}'".format(t) for t in template]))
    # Values keeps track of all valid permutations of values to select from
    # cache tables. The nth item in each permutation corresponds to the nth
    # parameter for which generate is True. The list of aggregations (which is
    # a list of runtime parameters that are aggregators) must also be the same
    # length as these permutations.
    values = [[]]
    aggregations = []
    parameters = self._GetRuntimeParameters(parameter_info)
    for i, parameter in enumerate(parameters):
      parameter.generate = False
      if parameter.value and template[parameter.column] in (None, '*'):
        template[parameter.column] = parameter.value
        log.info('cache parameter=%s column=%s value=%s aggregate=%s',
                 parameter.name, parameter.column, parameter.value,
                 parameter.aggregator)
        if parameter.aggregator:
          aggregations.append(parameter)
          parameter.generate = True
          for v in values:
            v.append(parameter.value)
      elif parameter.aggregator:
        aggregations.append(parameter)
        parameter.generate = True
        log.info('cache parameter=%s column=%s value=%s aggregate=%s',
                 parameter.name, parameter.column, parameter.value,
                 parameter.aggregator)
        # Updater object instantiation is on demand so they don't have to be
        # instantiated at import time in the static CLI tree. It also makes it
        # easier to serialize in the static CLI tree JSON object.
        updater = parameter.updater_class(cache=self.cache)
        sub_template = [None] * updater.columns
        sub_template[updater.column] = template[parameter.column]
        log.info('cache parameter=%s column=%s aggregate=%s',
                 parameter.name, parameter.column, parameter.aggregator)
        new_values = []
        for perm, selected in updater.YieldSelectTableFromPermutations(
            parameters[:i], values, sub_template, parameter_info):
          updater.ExtendValues(new_values, perm, selected)
        values = new_values
    if not values:
      aggregation_values = [x.value for x in aggregations]
      # Given that values is essentially a reduced crossproduct of all results
      # from the parameter updaters, it collapses to [] if any intermediate
      # update finds no results. We only want to keep going here if no
      # aggregators needed to be updated in the first place.
      if None in aggregation_values:
        return []
      table_name = self._GetTableName(suffix_list=aggregation_values)
      table = self.cache.Table(
          table_name,
          columns=self.columns,
          keys=self.columns,
          timeout=self.timeout)
      return self.SelectTable(table, template, parameter_info, aggregations)
    rows = []
    for _, selected in self.YieldSelectTableFromPermutations(
        parameters, values, template, parameter_info):
      rows.extend(selected)
    log.info('cache rows=%s' % rows)
    return rows

  def _GetParameterColumn(self, parameter_info, parameter_name):
    """Get this updater's column number for a certain parameter."""
    updater_parameters = self._GetRuntimeParameters(parameter_info)
    for parameter in updater_parameters:
      if parameter.name == parameter_name:
        return parameter.column
    return None

  def ExtendValues(self, values, perm, selected):
    """Add selected values to a template and extend the selected rows."""
    vals = [row[self.column] for row in selected]
    log.info('cache collection={} adding values={}'.format(
        self.collection, vals))
    v = [perm + [val] for val in vals]
    values.extend(v)

  def YieldSelectTableFromPermutations(self, parameters, values, template,
                                       parameter_info):
    """Selects completions from tables using multiple permutations of values.

    For each vector in values, e.g. ['my-project', 'my-zone'], this method
    selects rows matching the template from a leaf table corresponding to the
    vector (e.g. 'my.collection.my-project.my-zone') and yields a 2-tuple
    containing that vector and the selected rows.

    Args:
      parameters: [Parameter], the list of parameters up through the
        current updater belonging to the parent. These will be used to iterate
        through each permutation contained in values.
      values: list(list()), a list of lists of valid values. Each item in values
        corresponds to a single permutation of values for which item[n] is a
        possible value for the nth generator in parent_parameters.
      template: list(str), the template to use to select new values.
      parameter_info: ParameterInfo, the object that is used to get runtime
        values.

    Yields:
      (perm, list(list)): a 2-tuple where the first value is the permutation
        currently being used to select values and the second value is the result
        of selecting to match the permutation.
    """
    for perm in values:
      temp_perm = [val for val in perm]
      table = self.cache.Table(
          self._GetTableName(suffix_list=perm),
          columns=self.columns,
          keys=self.columns,
          timeout=self.timeout)
      aggregations = []
      for parameter in parameters:
        if parameter.generate:
          # Find the matching parameter from current updater. If the parameter
          # isn't found, the value is discarded.
          column = self._GetParameterColumn(parameter_info, parameter.name)
          if column is None:
            continue
          template[column] = temp_perm.pop(0)
          parameter.value = template[column]
        if parameter.value:
          aggregations.append(parameter)
      selected = self.SelectTable(table, template, parameter_info, aggregations)
      yield perm, selected

  def GetTableForRow(self, row, parameter_info=None, create=True):
    """Returns the table for row.

    Args:
      row: The fully populated resource row.
      parameter_info: A ParamaterInfo object for accessing parameter values in
        the program state.
      create: Create the table if it doesn't exist if True.

    Returns:
      The table for row.
    """
    parameters = self._GetRuntimeParameters(parameter_info)
    values = [row[p.column] for p in parameters if p.aggregator]
    return self.cache.Table(
        self._GetTableName(suffix_list=values),
        columns=self.columns,
        keys=self.columns,
        timeout=self.timeout,
        create=create)

  @abc.abstractmethod
  def Update(self, parameter_info=None, aggregations=None):
    """Returns the list of all current parsed resource parameters."""
    del parameter_info, aggregations


class ResourceCache(PERSISTENT_CACHE_IMPLEMENTATION.Cache):
  """A resource cache object."""

  def __init__(self, name=None, create=True):
    """ResourceCache constructor.

    Args:
      name: The persistent cache object name. If None then a default name
        conditioned on the account name is used.
          <GLOBAL_CONFIG_DIR>/cache/<ACCOUNT>/resource.cache
      create: Create the cache if it doesn't exist if True.
    """
    if not name:
      name = self.GetDefaultName()
    super(ResourceCache, self).__init__(
        name=name, create=create, version=VERSION)

  @staticmethod
  def GetDefaultName():
    """Returns the default resource cache name."""
    path = [config.Paths().cache_dir]
    account = properties.VALUES.core.account.Get(required=False)
    if account:
      path.append(account)
    files.MakeDir(os.path.join(*path))
    path.append('resource.cache')
    return os.path.join(*path)


def Delete(name=None):
  """Deletes the current persistent resource cache however it's implemented."""
  if not name:
    name = ResourceCache.GetDefaultName()

  # Keep trying implementation until cache not found or a matching cache found.
  for implementation in (sqlite_cache, file_cache):
    if not implementation:
      continue
    try:
      implementation.Cache(name=name, create=False, version=VERSION).Delete()
      return
    except exceptions.CacheInvalid:
      continue
