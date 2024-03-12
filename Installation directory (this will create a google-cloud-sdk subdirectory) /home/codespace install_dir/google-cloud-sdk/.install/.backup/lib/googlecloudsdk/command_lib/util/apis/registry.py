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

"""Utilities for the gcloud meta apis surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import messages
from apitools.base.py import  exceptions as apitools_exc
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.api_lib.util import resource
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis import apis_map
import six

NAME_SEPARATOR = '.'


class Error(exceptions.Error):
  pass


class UnknownAPIError(Error):

  def __init__(self, api_name):
    super(UnknownAPIError, self).__init__(
        'API [{api}] does not exist or is not registered.'
        .format(api=api_name)
    )


class UnknownAPIVersionError(Error):

  def __init__(self, api_name, version):
    super(UnknownAPIVersionError, self).__init__(
        'Version [{version}] does not exist for API [{api}].'
        .format(version=version, api=api_name)
    )


class NoDefaultVersionError(Error):

  def __init__(self, api_name):
    super(NoDefaultVersionError, self).__init__(
        'API [{api}] does not have a default version. You must specify which '
        'version to use.'.format(api=api_name)
    )


class UnknownCollectionError(Error):

  def __init__(self, api_name, api_version, collection):
    super(UnknownCollectionError, self).__init__(
        'Collection [{collection}] does not exist for [{api}] [{version}].'
        .format(collection=collection, api=api_name, version=api_version)
    )


class UnknownMethodError(Error):

  def __init__(self, method, collection):
    super(UnknownMethodError, self).__init__(
        'Method [{method}] does not exist for collection [{collection}].'
        .format(method=method, collection=collection)
    )


class APICallError(Error):
  pass


class API(object):
  """A data holder for returning API data for display."""

  def __init__(self, name, version, is_default, client, base_url):
    self.name = name
    self.version = version
    self.is_default = is_default
    self._client = client
    self.base_url = base_url

  def GetMessagesModule(self):
    return self._client.MESSAGES_MODULE


class APICollection(object):
  """A data holder for collection information for an API."""

  def __init__(self, collection_info):
    self.api_name = collection_info.api_name
    self.api_version = collection_info.api_version
    self.base_url = collection_info.base_url
    self.docs_url = collection_info.docs_url
    self.name = collection_info.name
    self.full_name = collection_info.full_name
    self.detailed_path = collection_info.GetPath('')
    self.detailed_params = collection_info.GetParams('')
    self.path = collection_info.path
    self.params = collection_info.params
    self.enable_uri_parsing = collection_info.enable_uri_parsing


class APIMethod(object):
  """A data holder for method information for an API collection."""

  def __init__(self, service, name, api_collection, method_config,
               disable_pagination=False):
    self._service = service
    self._method_name = name
    self._disable_pagination = disable_pagination

    self.collection = api_collection

    self.name = method_config.method_id
    dotted_path = self.collection.full_name + NAME_SEPARATOR
    if self.name.startswith(dotted_path):
      self.name = self.name[len(dotted_path):]

    self.path = _RemoveVersionPrefix(
        self.collection.api_version, method_config.relative_path)
    self.params = method_config.ordered_params
    if method_config.flat_path:
      self.detailed_path = _RemoveVersionPrefix(
          self.collection.api_version, method_config.flat_path)
      self.detailed_params = resource.GetParamsFromPath(method_config.flat_path)
    else:
      self.detailed_path = self.path
      self.detailed_params = self.params

    self.http_method = method_config.http_method
    self.request_field = method_config.request_field
    self.request_type = method_config.request_type_name
    self.response_type = method_config.response_type_name

    self._request_collection = self._RequestCollection()
    # Keep track of method query parameters
    self.query_params = method_config.query_params

  @property
  def resource_argument_collection(self):
    """Gets the collection that should be used to represent the resource.

    Most of the time this is the same as request_collection because all methods
    in a collection operate on the same resource and so the API method takes
    the same parameters that make up the resource.

    One exception is List methods where the API parameters are for the parent
    collection. Because people don't specify the resource directly for list
    commands this also returns the parent collection for parsing purposes.

    The other exception is Create methods. They reference the parent collection
    list Like, but the difference is that we *do* want to specify the actual
    resource on the command line, so the original resource collection is
    returned here instead of the one that matches the API methods. When
    generating the request, you must figure out how to generate the message
    correctly from the parsed resource (as you cannot simply pass the reference
    to the API).

    Returns:
      APICollection: The collection.
    """
    if self.IsList():
      return self._request_collection
    return self.collection

  @property
  def request_collection(self):
    """Gets the API collection that matches the parameters of the API method."""
    return self._request_collection

  def GetRequestType(self):
    """Gets the apitools request class for this method."""
    return self._service.GetRequestType(self._method_name)

  def GetResponseType(self):
    """Gets the apitools response class for this method."""
    return self._service.GetResponseType(self._method_name)

  def GetEffectiveResponseType(self):
    """Gets the effective apitools response class for this method.

    This will be different from GetResponseType for List methods if we are
    extracting the list of response items from the overall response. This will
    always match the type of response that Call() returns.

    Returns:
      The apitools Message object.
    """
    if (item_field := self.ListItemField()) and self.HasTokenizedRequest():
      return arg_utils.GetFieldFromMessage(
          self.GetResponseType(), item_field).type
    else:
      return self.GetResponseType()

  def GetMessageByName(self, name):
    """Gets a arbitrary apitools message class by name.

    This method can be used to get arbitrary apitools messages from the
    underlying service. Examples:

    policy_type = method.GetMessageByName('Policy')
    status_type = method.GetMessageByName('Status')

    Args:
      name: str, the name of the message to return.
    Returns:
      The apitools Message object.
    """
    msgs = self._service.client.MESSAGES_MODULE
    return getattr(msgs, name, None)

  def IsList(self):
    """Determines whether this is a List method."""
    return self._method_name == 'List'

  def HasTokenizedRequest(self):
    """Determines whether this is a method that supports paging."""
    return (not self._disable_pagination
            and 'pageToken' in self._RequestFieldNames()
            and 'nextPageToken' in self._ResponseFieldNames())

  def BatchPageSizeField(self):
    """Gets the name of the page size field in the request if it exists."""
    request_fields = self._RequestFieldNames()
    if 'maxResults' in request_fields:
      return 'maxResults'
    if 'pageSize' in request_fields:
      return 'pageSize'
    return None

  def ListItemField(self):
    """Gets the name of the field that contains the items in paginated response.

    This will return None if the method is not a paginated or if a single
    repeated field of items could not be found in the response type.

    Returns:
      str, The name of the field or None.
    """
    if self._disable_pagination:
      return None

    response = self.GetResponseType()
    found = [f for f in response.all_fields()
             if f.variant == messages.Variant.MESSAGE and f.repeated]
    if len(found) == 1:
      return found[0].name
    else:
      return None

  def _RequestCollection(self):
    """Gets the collection that matches the API parameters of this method.

    Methods apply to elements of a collection. The resource argument is always
    of the type of that collection.  List is an exception where you are listing
    items of that collection so the argument to be provided is that of the
    parent collection. This method returns the collection that should be used
    to parse the resource for this specific method.

    Returns:
      APICollection, The collection to use or None if no parent collection could
      be found.
    """
    if self.detailed_params == self.collection.detailed_params:
      return self.collection
    collections = GetAPICollections(
        self.collection.api_name, self.collection.api_version)
    for c in collections:
      if self.detailed_params == c.detailed_params:
        return c
    return None

  def _RequestFieldNames(self):
    """Gets the fields that are actually a part of the request message.

    For APIs that use atomic names, this will only be the single name parameter
    (and any other message fields) but not the detailed parameters.

    Returns:
      [str], The field names.
    """
    return [f.name for f in self.GetRequestType().all_fields()]

  def _ResponseFieldNames(self):
    """Gets the fields that are actually a part of the response message.

    Returns:
      [str], The field names.
    """
    return [f.name for f in self.GetResponseType().all_fields()]

  def Call(self, request, client=None, global_params=None, raw=False,
           limit=None, page_size=None):
    """Executes this method with the given arguments.

    Args:
      request: The apitools request object to send.
      client: base_api.BaseApiClient, An API client to use for making requests.
      global_params: {str: str}, A dictionary of global parameters to send with
        the request.
      raw: bool, True to not do any processing of the response, False to maybe
        do processing for List results.
      limit: int, The max number of items to return if this is a List method.
      page_size: int, The max number of items to return in a page if this API
        supports paging.

    Returns:
      The response from the API.
    """
    if client is None:
      client = apis.GetClientInstance(
          self.collection.api_name, self.collection.api_version)
    service = _GetService(client, self.collection.name)
    request_func = self._GetRequestFunc(
        service, request, raw=raw, limit=limit, page_size=page_size)
    try:
      return request_func(global_params=global_params)
    except apitools_exc.InvalidUserInputError as e:
      log.debug('', exc_info=True)
      raise APICallError(str(e))

  def _GetRequestFunc(self, service, request, raw=False,
                      limit=None, page_size=None):
    """Gets a request function to call and process the results.

    If this is a method with paginated response, it may flatten the response
    depending on if the List Pager can be used.

    Args:
      service: The apitools service that will be making the request.
      request: The apitools request object to send.
      raw: bool, True to not do any processing of the response, False to maybe
        do processing for List results.
      limit: int, The max number of items to return if this is a List method.
      page_size: int, The max number of items to return in a page if this API
        supports paging.

    Returns:
      A function to make the request.
    """
    if raw or self._disable_pagination:
      return self._NormalRequest(service, request)

    item_field = self.ListItemField()
    if not item_field:
      if self.IsList():
        log.debug(
            'Unable to flatten list response, raw results being returned.')
      return self._NormalRequest(service, request)

    if not self.HasTokenizedRequest():
      # API doesn't do paging.
      if self.IsList():
        return self._FlatNonPagedRequest(service, request, item_field)
      else:
        return self._NormalRequest(service, request)

    def RequestFunc(global_params=None):
      return list_pager.YieldFromList(
          service, request, method=self._method_name, field=item_field,
          global_params=global_params, limit=limit,
          current_token_attribute='pageToken',
          next_token_attribute='nextPageToken',
          batch_size_attribute=self.BatchPageSizeField(),
          batch_size=page_size)
    return RequestFunc

  def _NormalRequest(self, service, request):
    """Generates a basic request function for the method.

    Args:
      service: The apitools service that will be making the request.
      request: The apitools request object to send.

    Returns:
      A function to make the request.
    """
    def RequestFunc(global_params=None):
      method = getattr(service, self._method_name)
      return method(request, global_params=global_params)
    return RequestFunc

  def _FlatNonPagedRequest(self, service, request, item_field):
    """Generates a request function for the method that extracts an item list.

    List responses usually have a single repeated field that represents the
    actual items being listed. This request function returns only those items
    not the entire response.

    Args:
      service: The apitools service that will be making the request.
      request: The apitools request object to send.
      item_field: str, The name of the field that the list of items can be found
       in.

    Returns:
      A function to make the request.
    """
    def RequestFunc(global_params=None):
      response = self._NormalRequest(service, request)(
          global_params=global_params)
      return getattr(response, item_field)
    return RequestFunc


def _RemoveVersionPrefix(api_version, path):
  """Trims the version number off the front of a URL path if present."""
  if not path:
    return None
  if path.startswith(api_version):
    return path[len(api_version) + 1:]
  return path


def _ValidateAndGetDefaultVersion(api_name, api_version):
  """Validates the API exists and gets the default version if not given."""
  # pylint:disable=protected-access
  api_name, _ = apis_internal._GetApiNameAndAlias(api_name)
  api_vers = apis_map.MAP.get(api_name, {})
  if not api_vers:
    # No versions, this API is not registered.
    raise UnknownAPIError(api_name)
  if api_version:
    if api_version not in api_vers:
      raise UnknownAPIVersionError(api_name, api_version)
    return api_version

  for version, api_def in six.iteritems(api_vers):
    if api_def.default_version:
      return version
  raise NoDefaultVersionError(api_name)


def GetAPI(api_name, api_version=None):
  """Get a specific API definition.

  Args:
    api_name: str, The name of the API.
    api_version: str, The version string of the API.

  Returns:
    API, The API definition.
  """
  api_version = _ValidateAndGetDefaultVersion(api_name, api_version)
  # pylint: disable=protected-access
  api_def = apis_internal.GetApiDef(api_name, api_version)
  if api_def.apitools:
    api_client = apis_internal._GetClientClassFromDef(api_def)
  else:
    api_client = apis_internal._GetGapicClientClass(api_name, api_version)

  if hasattr(api_client, 'BASE_URL'):
    base_url = api_client.BASE_URL
  else:
    try:
      base_url = apis_internal._GetResourceModule(
          api_name, api_version
      ).BASE_URL
    except ImportError:
      base_url = 'https://{}.googleapis.com/{}'.format(api_name, api_version)
  return API(
      api_name, api_version, api_def.default_version, api_client, base_url
  )


def GetAllAPIs():
  """Gets all registered APIs.

  Returns:
    [API], A list of API definitions.
  """
  all_apis = []
  for api_name, versions in six.iteritems(apis_map.MAP):
    for api_version, _ in six.iteritems(versions):
      all_apis.append(GetAPI(api_name, api_version))
  return all_apis


def _SplitFullCollectionName(collection):
  return tuple(collection.split(NAME_SEPARATOR, 1))


def GetAPICollections(api_name=None, api_version=None):
  """Gets the registered collections for the given API version.

  Args:
    api_name: str, The name of the API or None for all apis.
    api_version: str, The version string of the API or None to use the default
      version.

  Returns:
    [APICollection], A list of the registered collections.
  """
  if api_name:
    all_apis = {api_name: _ValidateAndGetDefaultVersion(api_name, api_version)}
  else:
    all_apis = {x.name: x.version for x in GetAllAPIs() if x.is_default}

  collections = []
  for n, v in six.iteritems(all_apis):
    # pylint:disable=protected-access
    collections.extend(
        [APICollection(c) for c in apis_internal._GetApiCollections(n, v)])
  return collections


def GetAPICollection(full_collection_name, api_version=None):
  """Gets the given collection for the given API version.

  Args:
    full_collection_name: str, The collection to get including the api name.
    api_version: str, The version string of the API or None to use the default
      for this API.

  Returns:
    APICollection, The requested API collection.

  Raises:
    UnknownCollectionError: If the collection does not exist for the given API
    and version.
  """
  api_name, collection = _SplitFullCollectionName(full_collection_name)
  api_version = _ValidateAndGetDefaultVersion(api_name, api_version)
  collections = GetAPICollections(api_name, api_version)
  for c in collections:
    if c.name == collection:
      return c
  raise UnknownCollectionError(api_name, api_version, collection)


def GetMethod(full_collection_name, method, api_version=None,
              disable_pagination=False):
  """Gets the specification for the given API method.

  Args:
    full_collection_name: str, The collection including the api name.
    method: str, The name of the method.
    api_version: str, The version string of the API or None to use the default
      for this API.
    disable_pagination: bool, Boolean for whether pagination should be disabled

  Returns:
    APIMethod, The method specification.

  Raises:
    UnknownMethodError: If the method does not exist on the collection.
  """
  methods = GetMethods(
      full_collection_name, api_version=api_version,
      disable_pagination=disable_pagination)
  for m in methods:
    if m.name == method:
      return m
  raise UnknownMethodError(method, full_collection_name)


def _GetService(client, collection_name):
  return getattr(client, collection_name.replace(NAME_SEPARATOR, '_'), None)


def _GetApiClient(api_name, api_version):
  """Gets the repesctive api client for the api."""
  api_def = apis_internal.GetApiDef(api_name, api_version)
  if api_def.apitools:
    client = apis.GetClientInstance(api_name, api_version, no_http=True)
  else:
    client = apis.GetGapicClientInstance(api_name, api_version)
  return client


def GetMethods(
    full_collection_name, api_version=None, disable_pagination=False):
  """Gets all the methods available on the given collection.

  Args:
    full_collection_name: str, The collection including the api name.
    api_version: str, The version string of the API or None to use the default
      for this API.
    disable_pagination: bool, Boolean for whether pagination should be disabled

  Returns:
    [APIMethod], The method specifications.
  """
  api_collection = GetAPICollection(full_collection_name,
                                    api_version=api_version)

  client = _GetApiClient(api_collection.api_name, api_collection.api_version)
  service = _GetService(client, api_collection.name)
  if not service:
    # This is a synthetic collection that does not actually have a backing API.
    return []

  method_names = service.GetMethodsList()
  method_configs = [(name, service.GetMethodConfig(name))
                    for name in method_names]
  return [APIMethod(service, name, api_collection, config, disable_pagination)
          for name, config in method_configs]
