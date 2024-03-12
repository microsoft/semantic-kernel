# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Resource display taps.

A tapper is an object that converts an iterable into another iterable. It
applies the Tap method as each item is iterated on, and applies the Done method
just before the iteration stops. A Tapper may delete items from an iterable
and/or inject new items into an iterable. Tappers are useful for monitoring or
modifying an iterable without consuming it all at once.

For example one could always:

  items = list(iterable_items)
  for item in items:
    do_something(item)
  # pass items to the next consumer

However, if an iterable consumed a lot of resources (say a generator with a
zillion items) then the list() statement would instantiate all of the items and
strain memory. A tapper avoids this by dealing with each item as it is
generated.

There is a tapper for each of the --filter, --flatten, --limit, and --page
flags.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_filter
from googlecloudsdk.core.resource import resource_printer_base
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.util import peek_iterable


class Filterer(peek_iterable.Tap):
  """A Tapper class that filters out resources not matching an expression.

  Attributes:
    _match: The resource filter method.
  """

  def __init__(self, expression, defaults):
    """Constructor.

    Args:
      expression: The resource filter expression string.
      defaults: The resource format and filter default projection.
    """
    self._compiled_expression = resource_filter.Compile(
        expression, defaults=defaults)
    self._missing_keys = resource_filter.GetAllKeys(self._compiled_expression)

  def Tap(self, resource):
    """Returns True if resource matches the filter expression.

    Args:
      resource: The resource to filter.

    Returns:
      True if resource matches the filter expression.
    """
    serialized_resource = resource_projector.MakeSerializable(resource)
    self._missing_keys -= set(
        key
        for key in self._missing_keys
        if resource_property.ResourceContainsKey(serialized_resource, key)
    )
    if resource_printer_base.IsResourceMarker(resource):
      return True
    return self._compiled_expression.Evaluate(serialized_resource)

  def Done(self):
    def WarnMissingKeys(missing_keys):
      missing_keys_str = ', '.join(
          ['.'.join(map(str, key)) for key in sorted(missing_keys)]
      )
      log.warning(
          'The following filter keys were not present in any resource : '
          + missing_keys_str
      )

    if self._missing_keys:
      WarnMissingKeys(self._missing_keys)


class Flattener(peek_iterable.Tap):
  """A Tapper class that flattens a resource key slice to separate records.

  A serialized copy of the resource is modified in place. This means the same
  resource object is returned for each flattened slice item. This is OK because
  the downstream is not guaranteed uniqueness.

  Attributes:
    _child_name: The flattened value to set is _parent_key[_child_name].
    _key: The parsed resource key of the slice to flatten.
    _parent_key: The parent of _key, None for the resource itself.
    _items: The items to flatten in the current resource.
    _resource: The serialized copy of the current resource.
  """

  def __init__(self, key):
    """Constructor.

    Args:
      key: The resource key of the slice to flatten.
    """
    # Save a copy of the key.
    self._key = key[:]
    self._child_name = self._key[-1] if self._key else None
    self._parent_key = self._key[:-1] if self._key else None
    self._items = None
    self._resource = None

  def Tap(self, resource):
    """Returns the next slice item in resource.

    Args:
      resource: The resource to flatten.

    Returns:
      True if the next slice is not a list, False if there are no more items,
      or Injector(resource) which is the resource with the next slice flattened.
    """
    if self._items is None:
      # Modify a serialized copy of resource.
      self._resource = resource_projector.MakeSerializable(resource)
      self._items = resource_property.Get(self._resource, self._key)
      if not isinstance(self._items, list):
        item = self._items
        self._items = None
        return peek_iterable.TapInjector(item, replace=True)
    if not self._items:
      self._items = None
      return False
    item = self._items.pop(0)
    if self._parent_key:
      parent = resource_property.Get(self._resource, self._parent_key)
    else:
      parent = self._resource
    parent[self._child_name] = item
    return peek_iterable.TapInjector(
        resource_projector.MakeSerializable(self._resource))


class Limiter(peek_iterable.Tap):
  """A Tapper class that filters out resources after a limit is reached.

  Attributes:
    _limit: The resource count limit.
    _count: The resource count.
  """

  def __init__(self, limit):
    self._limit = limit
    self._count = 0

  def Tap(self, resource):
    """Returns True if the limit has not been reached yet, None otherwise.

    Args:
      resource: The resource to limit.

    Returns:
      True if the limit has not been reached yet, None otherwise to stop
      iterations.
    """
    if resource_printer_base.IsResourceMarker(resource):
      return True
    self._count += 1
    return self._count <= self._limit or None


class Pager(peek_iterable.Tap):
  """A Tapper class that injects a PageMarker after each page of resources.

  Attributes:
    _page_size: The number of resources per page.
    _count: The current page resource count.
  """

  def __init__(self, page_size):
    self._page_size = page_size
    self._count = 0

  def Tap(self, resource):
    """Injects a PageMarker if the current page limit has been reached.

    Args:
      resource: The resource to limit.

    Returns:
      TapInjector(PageMarker) if the page current page limit has been reached,
      otherwise True to retain the current resource.
    """
    if resource_printer_base.IsResourceMarker(resource):
      return True
    self._count += 1
    if self._count > self._page_size:
      self._count = 0
      return peek_iterable.TapInjector(resource_printer_base.PageMarker())
    return True


class UriCacher(peek_iterable.Tap):
  """A Tapper class that caches URIs based on the cache update op.

  Attributes:
    _transform_uri: The uri() transform function.
    _update_cache_op: The non-None return value from UpdateUriCache().
    _uris: The list of changed URIs, None if it is corrupt.
  """

  def __init__(self, update_cache_op, transform_uri):
    self._transform_uri = transform_uri
    self._update_cache_op = update_cache_op
    self._uris = []

  def Tap(self, resource):
    """Appends the URI for resource to the list of cache changes.

    Sets self._uris to None if a URI could not be retrieved for any resource.

    Args:
      resource: The resource from which the URI is extracted.

    Returns:
      True - all resources are seen downstream.
    """
    if resource_printer_base.IsResourceMarker(resource):
      return True
    if self._uris is not None:
      uri = self._transform_uri(resource, undefined=None)
      if uri:
        self._uris.append(uri)
      else:
        self._uris = None
    return True

  def Done(self):
    if self._uris is not None:
      self._update_cache_op.Update(self._uris)


class UriReplacer(peek_iterable.Tap):
  """A Tapper class that replaces each resource item with its URI.

  Attributes:
    _transform_uri: The uri() transform function.
  """

  def __init__(self, transform_uri):
    self._transform_uri = transform_uri

  def Tap(self, resource):
    """Replaces resource with its URI or skips the resource if it has no URI.

    Args:
      resource: The resource to replace with its URI.

    Returns:
      TapInjector(URI, replace=True) if the resource has a URI or False to skip
      the resource.
    """
    if resource_printer_base.IsResourceMarker(resource):
      return True
    uri = self._transform_uri(resource, undefined=None)
    if not uri:
      return False
    return peek_iterable.TapInjector(uri, replace=True)
