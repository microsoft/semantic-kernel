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
"""completers for resource library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from apitools.base.protorpclite import messages

from googlecloudsdk.api_lib.util import resource as resource_lib  # pylint: disable=unused-import
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.concepts import resource_parameter_info
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

import six

DEFAULT_ID_FIELD = 'name'
_PROJECTS_COLLECTION = 'cloudresourcemanager.projects'
_PROJECT_ID_FIELD = 'projectId'


class Error(exceptions.Error):
  """Base error class for this module."""


class ParentTranslator(object):
  """Translates parent collections for completers.

  Attributes:
    collection: str, the collection name.
    param_translation: {str: str}, lookup from the params of the child
      collection to the params of the special parent collection. If None,
      then the collections match and translate methods are a no-op.
  """

  def __init__(self, collection, param_translation=None):
    self.collection = collection
    self.param_translation = param_translation or {}

  def ToChildParams(self, params):
    """Translate from original parent params to params that match the child."""
    if self.param_translation:
      for orig_param, new_param in six.iteritems(self.param_translation):
        params[orig_param] = params.get(new_param)
        del params[new_param]
    return params

  def MessageResourceMap(self, message, ref):
    """Get dict for translating parent params into the given message type."""
    message_resource_map = {}
    # Parse resource with any params in the translator that are needed for the
    # request.
    for orig_param, special_param in six.iteritems(self.param_translation):
      try:
        message.field_by_name(orig_param)
      # The field is not found, meaning that the original param isn't in the
      # message.
      except KeyError:
        continue
      message_resource_map[orig_param] = getattr(ref, special_param, None)
    return message_resource_map

  def Parse(self, parent_params, parameter_info, aggregations_dict):
    """Parse the parent resource from parameter info and aggregations.

    Args:
      parent_params: [str], a list of params in the current collection's parent
        collection.
      parameter_info: the runtime ResourceParameterInfo object.
      aggregations_dict: {str: str}, a dict of params to values that are
        being aggregated from earlier updates.

    Returns:
      resources.Resource | None, the parsed parent reference or None if there
        is not enough information to parse.
    """
    param_values = {
        self.param_translation.get(p, p): parameter_info.GetValue(p)
        for p in parent_params}
    for p, value in six.iteritems(aggregations_dict):
      translated_name = self.param_translation.get(p, p)
      if value and not param_values.get(translated_name, None):
        param_values[translated_name] = value
    try:
      return resources.Resource(
          resources.REGISTRY,
          collection_info=resources.REGISTRY.GetCollectionInfo(self.collection),
          subcollection='',
          param_values=param_values,
          endpoint_url=None)
    # Not all completion list calls may need to have a parent, so even if we
    # can't parse a parent, we log the error and attempt to send an update call
    # without one. (Any error returned by the API will be raised.)
    except resources.Error as e:
      log.info(six.text_type(e).rstrip())
      return None


# A map from parent params (in original resource parser order, joined with '.')
# to special collections. If the original params are different from the special
# collection, the param_translator is used to translate back and forth between
# the original params and the special collection.
_PARENT_TRANSLATORS = {
    'projectsId': ParentTranslator(_PROJECTS_COLLECTION,
                                   {'projectsId': _PROJECT_ID_FIELD}),
    'projectId': ParentTranslator(_PROJECTS_COLLECTION)}


class CollectionConfig(collections.namedtuple(
    'CollectionConfig',
    [
        # static params are used to build the List request when updating
        # the cache (equivalent to completion_request_params in AttributeConfig
        # objects)
        'static_params',
        # Configures the ID field that is used to parse the results of a List
        # request when updating the cache. Equivalent to completion_id_field
        # in AttributeConfig objects.
        'id_field',
        # Configures the param name for the completer.
        'param_name']
    )):
  """Stores data about special collections for configuring completion."""


# This maps special collections to configuration for CompleterInfo objects
# rather than using configuration from the parent resource's collection.
# Currently only covers projects.
_SPECIAL_COLLECTIONS_MAP = {
    _PROJECTS_COLLECTION: CollectionConfig({'filter': 'lifecycleState:ACTIVE'},
                                           _PROJECT_ID_FIELD,
                                           _PROJECT_ID_FIELD)}


class ResourceArgumentCompleter(completers.ResourceCompleter):
  """A completer for an argument that's part of a resource argument."""

  def __init__(self, resource_spec, collection_info, method,
               static_params=None, id_field=None, param=None, **kwargs):
    """Initializes."""
    self.resource_spec = resource_spec
    self._method = method
    self._static_params = static_params or {}
    self.id_field = id_field or DEFAULT_ID_FIELD
    collection_name = collection_info.full_name
    api_version = collection_info.api_version
    super(ResourceArgumentCompleter, self).__init__(
        collection=collection_name,
        api_version=api_version,
        param=param,
        parse_all=True,
        **kwargs)

  @property
  def method(self):
    """Gets the list method for the collection.

    Returns:
      googlecloudsdk.command_lib.util.apis.registry.APIMethod, the method.
    """
    return self._method

  def _ParentParams(self):
    """Get the parent params of the collection."""
    return self.collection_info.GetParams('')[:-1]

  def _GetUpdaters(self):
    """Helper function to build dict of updaters."""
    # Find the attribute that matches the final param of the collection for this
    # completer.
    final_param = self.collection_info.GetParams('')[-1]
    for i, attribute in enumerate(self.resource_spec.attributes):
      if self.resource_spec.ParamName(attribute.name) == final_param:
        attribute_idx = i
        break
    else:
      attribute_idx = 0

    updaters = {}
    for i, attribute in enumerate(
        self.resource_spec.attributes[:attribute_idx]):
      completer = CompleterForAttribute(self.resource_spec, attribute.name)
      if completer:
        updaters[self.resource_spec.ParamName(attribute.name)] = (completer,
                                                                  True)
      else:
        updaters[self.resource_spec.ParamName(attribute.name)] = (None,
                                                                  False)
    return updaters

  def ParameterInfo(self, parsed_args, argument):
    """Builds a ResourceParameterInfo object.

    Args:
      parsed_args: the namespace.
      argument: unused.

    Returns:
      ResourceParameterInfo, the parameter info for runtime information.
    """
    resource_info = parsed_args.CONCEPTS.ArgNameToConceptInfo(argument.dest)

    updaters = self._GetUpdaters()

    return resource_parameter_info.ResourceParameterInfo(
        resource_info, parsed_args, argument, updaters=updaters,
        collection=self.collection)

  def ValidateAttributeSources(self, aggregations):
    """Validates that parent attributes values exitst before making request."""
    parameters_needing_resolution = set([p.name for p in self.parameters[:-1]])
    resolved_parameters = set([a.name for a in aggregations])
    # attributes can also be resolved by completers
    for attribute in self.resource_spec.attributes:
      if CompleterForAttribute(self.resource_spec, attribute.name):
        resolved_parameters.add(
            self.resource_spec.attribute_to_params_map[attribute.name])
    return parameters_needing_resolution.issubset(resolved_parameters)

  def Update(self, parameter_info, aggregations):
    if self.method is None:
      return None

    if not self.ValidateAttributeSources(aggregations):
      return None

    log.info(
        'Cache query parameters={} aggregations={}'
        'resource info={}'.format(
            [(p, parameter_info.GetValue(p))
             for p in self.collection_info.GetParams('')],
            [(p.name, p.value) for p in aggregations],
            parameter_info.resource_info.attribute_to_args_map))
    parent_translator = self._GetParentTranslator(parameter_info, aggregations)
    try:
      query = self.BuildListQuery(parameter_info, aggregations,
                                  parent_translator=parent_translator)
    except Exception as e:  # pylint: disable=broad-except
      if properties.VALUES.core.print_completion_tracebacks.GetBool():
        raise
      log.info(six.text_type(e).rstrip())
      raise Error('Could not build query to list completions: {} {}'.format(
          type(e), six.text_type(e).rstrip()))
    try:
      response = self.method.Call(query)
      response_collection = self.method.collection
      items = [self._ParseResponse(r, response_collection,
                                   parameter_info=parameter_info,
                                   aggregations=aggregations,
                                   parent_translator=parent_translator)
               for r in response]
      log.info('cache items={}'.format(
          [i.RelativeName() for i in items]))
    except Exception as e:  # pylint: disable=broad-except
      if properties.VALUES.core.print_completion_tracebacks.GetBool():
        raise
      log.info(six.text_type(e).rstrip())
      # Give user more information if they hit an apitools validation error,
      # which probably means that they haven't provided enough information
      # for us to complete.
      if isinstance(e, messages.ValidationError):
        raise Error('Update query failed, may not have enough information to '
                    'list existing resources: {} {}'.format(
                        type(e), six.text_type(e).rstrip()))
      raise Error('Update query [{}]: {} {}'.format(
          query, type(e), six.text_type(e).rstrip()))
    return [self.StringToRow(item.RelativeName()) for item in items]

  def _ParseResponse(self, response, response_collection,
                     parameter_info=None, aggregations=None,
                     parent_translator=None):
    """Gets a resource ref from a single item in a list response."""
    param_values = self._GetParamValuesFromParent(
        parameter_info, aggregations=aggregations,
        parent_translator=parent_translator)
    param_names = response_collection.detailed_params
    for param in param_names:
      val = getattr(response, param, None)
      if val is not None:
        param_values[param] = val

    line = getattr(response, self.id_field, '')
    return resources.REGISTRY.Parse(
        line, collection=response_collection.full_name, params=param_values)

  def _GetParamValuesFromParent(self, parameter_info, aggregations=None,
                                parent_translator=None):
    parent_ref = self.GetParent(parameter_info, aggregations=aggregations,
                                parent_translator=parent_translator)
    if not parent_ref:
      return {}
    params = parent_ref.AsDict()
    if parent_translator:
      return parent_translator.ToChildParams(params)
    return params

  def _GetAggregationsValuesDict(self, aggregations):
    """Build a {str: str} dict of name to value for aggregations."""
    aggregations_dict = {}
    aggregations = [] if aggregations is None else aggregations
    for aggregation in aggregations:
      if aggregation.value:
        aggregations_dict[aggregation.name] = aggregation.value
    return aggregations_dict

  def BuildListQuery(self, parameter_info, aggregations=None,
                     parent_translator=None):
    """Builds a list request to list values for the given argument.

    Args:
      parameter_info: the runtime ResourceParameterInfo object.
      aggregations: a list of _RuntimeParameter objects.
      parent_translator: a ParentTranslator object if needed.

    Returns:
      The apitools request.
    """
    method = self.method
    if method is None:
      return None
    message = method.GetRequestType()()
    for field, value in six.iteritems(self._static_params):
      arg_utils.SetFieldInMessage(message, field, value)
    parent = self.GetParent(parameter_info, aggregations=aggregations,
                            parent_translator=parent_translator)
    if not parent:
      return message
    message_resource_map = {}

    if parent_translator:
      message_resource_map = parent_translator.MessageResourceMap(
          message, parent)

    arg_utils.ParseResourceIntoMessage(
        parent, method, message,
        message_resource_map=message_resource_map, is_primary_resource=True)
    return message

  def _GetParentTranslator(self, parameter_info, aggregations=None):
    """Get a special parent translator if needed and available."""
    aggregations_dict = self._GetAggregationsValuesDict(aggregations)
    param_values = self._GetRawParamValuesForParent(
        parameter_info, aggregations_dict=aggregations_dict)
    try:
      self._ParseDefaultParent(param_values)
      # If there's no error, we don't need a translator.
      return None
    except resources.ParentCollectionResolutionException:
      # Check the parent params against the _PARENT_TRANSLATORS dict, using the
      # parent params (joined by '.' in original resource parser order) as a
      # key.
      key = '.'.join(self._ParentParams())
      if key in _PARENT_TRANSLATORS:
        return _PARENT_TRANSLATORS.get(key)
    # Errors will be raised and logged later when actually parsing the parent.
    except resources.Error:
      return None

  def _GetRawParamValuesForParent(self, parameter_info, aggregations_dict=None):
    """Get raw param values for the resource in prep for parsing parent."""
    param_values = {p: parameter_info.GetValue(p) for p in self._ParentParams()}
    for name, value in six.iteritems(aggregations_dict or {}):
      if value and not param_values.get(name, None):
        param_values[name] = value
    final_param = self.collection_info.GetParams('')[-1]
    if param_values.get(final_param, None) is None:
      param_values[final_param] = 'fake'  # Stripped when we get the parent.
    return param_values

  def _ParseDefaultParent(self, param_values):
    """Parse the parent for a resource using default collection."""
    resource = resources.Resource(
        resources.REGISTRY,
        collection_info=self.collection_info,
        subcollection='',
        param_values=param_values,
        endpoint_url=None)
    return resource.Parent()

  def GetParent(self, parameter_info, aggregations=None,
                parent_translator=None):
    """Gets the parent reference of the parsed parameters.

    Args:
      parameter_info: the runtime ResourceParameterInfo object.
      aggregations: a list of _RuntimeParameter objects.
      parent_translator: a ParentTranslator for translating to a special
        parent collection, if needed.

    Returns:
      googlecloudsdk.core.resources.Resource | None, the parent resource or None
        if no parent was found.
    """
    aggregations_dict = self._GetAggregationsValuesDict(aggregations)
    param_values = self._GetRawParamValuesForParent(
        parameter_info, aggregations_dict=aggregations_dict)
    try:
      if not parent_translator:
        return self._ParseDefaultParent(param_values)
      return parent_translator.Parse(self._ParentParams(), parameter_info,
                                     aggregations_dict)
    except resources.ParentCollectionResolutionException as e:
      # We don't know the parent collection.
      log.info(six.text_type(e).rstrip())
      return None
    # No resource could be parsed.
    except resources.Error as e:
      log.info(six.text_type(e).rstrip())
      return None

  def __eq__(self, other):
    """Overrides."""
    # Not using type(self) because the class is created programmatically.
    if not isinstance(other, ResourceArgumentCompleter):
      return False
    return (self.resource_spec == other.resource_spec and
            self.collection == other.collection and
            self.method == other.method)


def _MatchCollection(resource_spec, attribute):
  """Gets the collection for an attribute in a resource."""
  resource_collection_info = resource_spec._collection_info  # pylint: disable=protected-access
  resource_collection = registry.APICollection(
      resource_collection_info)
  if resource_collection is None:
    return None
  if attribute == resource_spec.attributes[-1]:
    return resource_collection.name
  attribute_idx = resource_spec.attributes.index(attribute)
  api_name = resource_collection_info.api_name
  resource_collections = registry.GetAPICollections(
      api_name,
      resource_collection_info.api_version)
  params = resource_collection.detailed_params[:attribute_idx + 1]
  for c in resource_collections:
    if c.detailed_params == params:
      return c.name


def _GetCompleterCollectionInfo(resource_spec, attribute):
  """Gets collection info for an attribute in a resource."""
  api_version = None
  collection = _MatchCollection(resource_spec, attribute)
  if collection:
    # pylint: disable=protected-access
    full_collection_name = (
        resource_spec._collection_info.api_name + '.' + collection)
    api_version = resource_spec._collection_info.api_version
  # The CloudResourceManager projects collection can be used for "synthetic"
  # project resources that don't have their own method.
  elif attribute.name == 'project':
    full_collection_name = 'cloudresourcemanager.projects'
  else:
    return None
  return resources.REGISTRY.GetCollectionInfo(full_collection_name,
                                              api_version=api_version)


class CompleterInfo(object):
  """Holds data that can be used to instantiate a resource completer."""

  def __init__(self, static_params=None, id_field=None, collection_info=None,
               method=None, param_name=None):
    self.static_params = static_params
    self.id_field = id_field
    self.collection_info = collection_info
    self.method = method
    self.param_name = param_name

  @classmethod
  def FromResource(cls, resource_spec, attribute_name):
    """Gets the method, param_name, and other configuration for a completer.

    Args:
      resource_spec: concepts.ResourceSpec, the overall resource.
      attribute_name: str, the name of the attribute whose argument will use
        this completer.

    Raises:
      AttributeError: if the attribute doesn't belong to the resource.

    Returns:
      CompleterInfo, the instantiated object.
    """
    for a in resource_spec.attributes:
      if a.name == attribute_name:
        attribute = a
        break
    else:
      raise AttributeError(
          'Attribute [{}] not found in resource.'.format(attribute_name))
    param_name = resource_spec.ParamName(attribute_name)
    static_params = attribute.completion_request_params
    id_field = attribute.completion_id_field
    collection_info = _GetCompleterCollectionInfo(resource_spec, attribute)
    if collection_info.full_name in _SPECIAL_COLLECTIONS_MAP:
      special_info = _SPECIAL_COLLECTIONS_MAP.get(collection_info.full_name)
      method = registry.GetMethod(collection_info.full_name, 'list')
      static_params = special_info.static_params
      id_field = special_info.id_field
      param_name = special_info.param_name
    if not collection_info:
      return CompleterInfo(static_params, id_field, None, None, param_name)
    # If there is no appropriate list method for the collection, we can't auto-
    # create a completer.
    try:
      method = registry.GetMethod(
          collection_info.full_name, 'list',
          api_version=collection_info.api_version)
    except registry.UnknownMethodError:
      if (collection_info.full_name != _PROJECTS_COLLECTION
          and collection_info.full_name.split('.')[-1] == 'projects'):
        # The CloudResourceManager projects methods can be used for "synthetic"
        # project resources that don't have their own method.
        # This is a bit of a hack, so if any resource arguments come up for
        # which this doesn't work, a toggle should be added to the
        # ResourceSpec class to disable this.
        # Does not use param_name from the special collections map because
        # the collection exists with the current params, it's just the list
        # method that we're borrowing.
        special_info = _SPECIAL_COLLECTIONS_MAP.get(_PROJECTS_COLLECTION)
        method = registry.GetMethod(_PROJECTS_COLLECTION, 'list')
        static_params = special_info.static_params
        id_field = special_info.id_field
      else:
        method = None
    except registry.Error:
      method = None
    return CompleterInfo(static_params, id_field, collection_info, method,
                         param_name)

  def GetMethod(self):
    """Get the APIMethod for an attribute in a resource."""
    return self.method


def CompleterForAttribute(resource_spec, attribute_name):
  """Gets a resource argument completer for a specific attribute."""

  class Completer(ResourceArgumentCompleter):
    """A specific completer for this attribute and resource."""

    def __init__(self, resource_spec=resource_spec,
                 attribute_name=attribute_name, **kwargs):
      completer_info = CompleterInfo.FromResource(resource_spec, attribute_name)

      super(Completer, self).__init__(
          resource_spec,
          completer_info.collection_info,
          completer_info.method,
          static_params=completer_info.static_params,
          id_field=completer_info.id_field,
          param=completer_info.param_name,
          **kwargs)

    @classmethod
    def validate(cls):
      """Checks whether the completer is valid (has a list method)."""
      return bool(
          CompleterInfo.FromResource(resource_spec, attribute_name).GetMethod())

  if not Completer.validate():
    return None

  return Completer
