# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Manage parsing resource arguments for the cloud platform.

The Parse() function and Registry.Parse() method are to be used whenever a
Google Cloud API resource is indicated in a command-line argument.
URLs, bare names with hints, and any other acceptable spelling for a resource
will be accepted, and a consistent python object will be returned for use in
code.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import re

from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.api_lib.util import apis_util
from googlecloudsdk.api_lib.util import resource as resource_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties

import six
from six.moves import map  # pylint: disable=redefined-builtin
from six.moves import urllib
from six.moves import zip  # pylint: disable=redefined-builtin
import uritemplate

_COLLECTION_SUB_RE = r'[a-zA-Z_]+(?:\.[a-zA-Z0-9_]+)+'

# The first two wildcards in this are the API and the API's version. The rest
# are parameters into a specific collection in that API/version.
_URL_RE = re.compile(r'(https?://[^/]+/[^/]+/[^/]+/)(.+)')
_METHOD_ID_RE = re.compile(r'(?P<collection>{collection})\.get'.format(
    collection=_COLLECTION_SUB_RE))
_GCS_URL_RE = re.compile('^gs://([^/]*)(?:/(.*))?$')
_GCS_URL = 'https://www.googleapis.com/storage/v1/'
_GCS_ALT_URL = 'https://storage.googleapis.com/storage/v1/'
_GCS_ALT_URL_SHORT = 'https://storage.googleapis.com/'


class Error(Exception):
  """Exceptions for this module."""


class _ResourceWithoutGetException(Error):
  """Exception for resources with no Get method."""


class BadResolverException(Error):
  """Exception to signal that a resource has no Get method."""

  def __init__(self, param):
    super(BadResolverException, self).__init__(
        'bad resolver for [{param}]'.format(param=param))


class AmbiguousAPIException(Error):
  """Exception for when two APIs try to define a resource."""

  def __init__(self, collection, base_urls):
    super(AmbiguousAPIException, self).__init__(
        'collection [{collection}] defined in multiple APIs: {apis}'.format(
            collection=collection,
            apis=repr(base_urls)))


class AmbiguousResourcePath(Error):
  """Exception for when API path maps to two different resources."""

  def __init__(self, parser1, parser2):
    super(AmbiguousResourcePath, self).__init__(
        'There already exists parser {0} for same path, '
        'can not register another one {1}'.format(parser1, parser2))


class ParentCollectionResolutionException(Error):
  """Exception for when the parent collection cannot be computed automatically.
  """

  def __init__(self, collection, params):
    super(ParentCollectionResolutionException, self).__init__(
        'Could not resolve the parent collection of collection [{collection}]. '
        'No collections found with parameters [{params}]'.format(
            collection=collection, params=', '.join(params)))


class ParentCollectionMismatchException(Error):
  """Exception when the parent collection does not have the expected params."""

  def __init__(self, collection, parent_collection, expected_params,
               actual_params):
    super(ParentCollectionMismatchException, self).__init__(
        'The parent collection [{parent_collection}] of collection '
        '[{collection}] does have have the expected parameters. Expected '
        '[{expected_params}], found [{actual_params}].'.format(
            parent_collection=parent_collection, collection=collection,
            expected_params=', '.join(expected_params),
            actual_params=', '.join(actual_params)))


class UserError(exceptions.Error, Error):
  """Exceptions that are caused by user input."""


class InvalidResourceException(UserError):
  """A collection-path that was given could not be parsed."""

  def __init__(self, line, reason=None):
    message = 'could not parse resource [{line}]'.format(line=line)
    if reason:
      message += ': ' + reason
    super(InvalidResourceException, self).__init__(message)


class WrongResourceCollectionException(UserError):
  """A command line that was given had the wrong collection."""

  def __init__(self, expected, got, path):
    super(WrongResourceCollectionException, self).__init__(
        'wrong collection: expected [{expected}], got [{got}], for '
        'path [{path}]'.format(
            expected=expected, got=got, path=path))
    self.got = got
    self.path = path


class RequiredFieldOmittedException(UserError):
  """A command line that was given did not specify a field."""

  def __init__(self, collection_name, expected):
    super(RequiredFieldOmittedException, self).__init__(
        'value for field [{expected}] in collection [{collection_name}] is '
        'required but was not provided'.format(
            expected=expected, collection_name=collection_name))


class UnknownCollectionException(UserError):
  """A command line that was given did not specify a collection."""

  def __init__(self, line):
    super(UnknownCollectionException, self).__init__(
        'unknown collection for [{line}]'.format(line=line))


class InvalidCollectionException(UserError):
  """A command line that was given did not specify a collection."""

  def __init__(self, collection, api_version=None):
    message = 'unknown collection [{collection}]'.format(collection=collection)
    if api_version:
      message += ' for API version [{version}]'.format(version=api_version)
    super(InvalidCollectionException, self).__init__(message)


class _ResourceParser(object):
  """Class that turns command-line arguments into a cloud resource message."""

  def __init__(self, registry, collection_info):
    """Create a _ResourceParser for a given collection.

    Args:
      registry: Registry, The resource registry this parser belongs to.
      collection_info: resource_util.CollectionInfo, description for collection.
    """
    self.registry = registry
    self.collection_info = collection_info

  def ParseRelativeName(
      self, relative_name, base_url=None, subcollection='', url_unescape=False):
    """Parse relative name into a Resource object.

    Args:
      relative_name: str, resource relative name.
      base_url: str, base url part of the api which manages this resource.
      subcollection: str, id of subcollection. See the api resource module
          (googlecloudsdk/generated_clients/apis/API_NAME/API_VERSION/resources.py).
      url_unescape: bool, if true relative name parameters will be unescaped.

    Returns:
      Resource representing this name.

    Raises:
      InvalidResourceException: if relative name doesn't match collection
          template.
    """
    base_url = apis_internal.UniversifyAddress(base_url)
    path_template = self.collection_info.GetPathRegEx(subcollection)
    match = re.match(path_template, relative_name)
    if not match:
      raise InvalidResourceException(
          relative_name,
          'It is not in {0} collection as it does not match path template {1}'
          .format(self.collection_info.full_name, path_template))
    params = self.collection_info.GetParams(subcollection)
    fields = match.groups()
    if url_unescape:
      fields = map(urllib.parse.unquote, fields)
    return Resource(self.registry, self.collection_info, subcollection,
                    param_values=dict(zip(params, fields)),
                    endpoint_url=base_url)

  def ParseResourceId(self, resource_id, kwargs,
                      base_url=None, subcollection='', validate=True,
                      default_resolver=None):
    """Given a command line and some keyword args, get the resource.

    Args:
      resource_id: str, Some identifier for the resource.
          Can be None to indicate all params should be taken from kwargs.
      kwargs: {str:(str or func()->str)}, flags (available from context) or
          resolvers that can help parse this resource. If the fields in
          collection-path do not provide all the necessary information,
          kwargs will be searched for what remains.
      base_url: use this base url (endpoint) for the resource, if not provided
          default corresponding api version base url will be used.
      subcollection: str, name of subcollection to use when parsing this path.
      validate: bool, Validate syntax. Use validate=False to handle IDs under
        construction. An ID can be:
          fully qualified - All parameters are specified and have valid syntax.
          partially qualified - Some parameters are specified, all have valid
            syntax.
          under construction - Some parameters may be missing or too short and
            not meet the syntax constraints. With additional characters they
            would have valid syntax. Used by completers that build IDs from
            strings character by character. Completers need to do the
            string => parameters => string round trip with validate=False to
            handle the "add character TAB" cycle.
      default_resolver: func(str) => str, a default param resolver function
        called if kwargs doesn't resolve a param.

    Returns:
      protorpc.messages.Message, The object containing info about this resource.

    Raises:
      InvalidResourceException: If the provided collection-path is malformed.
      WrongResourceCollectionException: If the collection-path specified the
          wrong collection.
      RequiredFieldOmittedException: If the collection-path's path did not
          provide enough fields.
      GRIPathMismatchException: If the number of path segments in the GRI does
          not match the expected format of the URL for the given resource
          collection.
      ValueError: if parameter set in kwargs is not subset of the resource
          parameters.
    """
    base_url = apis_internal.UniversifyAddress(base_url)
    if resource_id is not None:
      try:
        return self.ParseRelativeName(
            resource_id, base_url=base_url, subcollection=subcollection)
      except InvalidResourceException:
        path = self.collection_info.GetPath(subcollection)
        path_prefixes = self.GetFieldNamesFromPath(path)

        contains_all_fields = all(
            prefix + '/' in resource_id for prefix in path_prefixes)

        if contains_all_fields:
          raise UserError('Invalid value: {}'.format(resource_id))
        else:
          pass

    params = self.collection_info.GetParams(subcollection)

    # Sanity check that Parse was called with right backup parameters.
    if not set(kwargs.keys()).issubset(params):
      raise ValueError(
          'Provided params {} is not subset of the resource parameters {} for '
          'collection {}'
          .format(sorted(kwargs.keys()), sorted(params),
                  self.collection_info.full_name))

    if _GRIsAreEnabled():
      # Also ensures that the collection specified in the GRI matches ours.
      gri = GRI.FromString(resource_id,
                           collection=self.collection_info.full_name,
                           validate=validate)
      fields = gri.path_fields
      if len(fields) > len(params):
        raise GRIPathMismatchException(
            resource_id, params,
            collection=gri.collection if gri.is_fully_qualified else None)
      elif len(fields) < len(params):
        fields += [None] * (len(params) - len(fields))
      fields = reversed(fields)
    else:
      fields = [None] * len(params)
      fields[-1] = resource_id

    param_values = dict(zip(params, fields))

    for param, value in param_values.items():
      if value is not None:
        continue

      # First try the resolvers given to this resource explicitly.
      resolver = kwargs.get(param)
      if resolver:
        param_values[param] = resolver() if callable(resolver) else resolver
      elif default_resolver:
        param_values[param] = default_resolver(param)

    ref = Resource(self.registry, self.collection_info, subcollection,
                   param_values, base_url)
    return ref

  def GetFieldNamesFromPath(self, path):
    """Extract field names from uri template path.

    Args:
      path: str, uri template path.

    Returns:
      list(str), list of field names in the template path.
    """
    return [
        prefix for idx, prefix in enumerate(
            path.split('/'))
        if idx % 2 == 0 and prefix
    ]

  def __str__(self):
    path_str = ''
    for param in self.collection_info.params:
      path_str = '[{path}]/{param}'.format(path=path_str, param=param)
    return '[{collection}::]{path}'.format(
        collection=self.collection_info.full_name, path=path_str)


class Resource(object):
  """Information about a Cloud resource."""

  def __init__(self, registry, collection_info, subcollection, param_values,
               endpoint_url):
    """Create a Resource object that may be partially resolved.

    To allow resolving of unknown params to happen after parse-time, the
    param resolution code is in this class rather than the _ResourceParser
    class.

    Args:
      registry: Registry, The resource registry this parser belongs to.
      collection_info: resource_util.CollectionInfo, The collection description
          for this resource.
      subcollection: str, id for subcollection of this collection.
      param_values: {param->value}, A list of values for parameters.
      endpoint_url: str, override service endpoint url for this resource. If
           None default base url of collection api will be used.
    Raises:
      RequiredFieldOmittedException: if param_values have None value.
    """
    self._registry = registry
    self._collection_info = collection_info

    if endpoint_url:
      self._endpoint_url = endpoint_url
    else:
      self._endpoint_url = apis_internal.UniversifyAddress(
          collection_info.base_url
      )
    self._subcollection = subcollection
    self._path = collection_info.GetPath(subcollection)
    self._params = collection_info.GetParams(subcollection)
    for param, value in six.iteritems(param_values):
      if value is None:
        raise RequiredFieldOmittedException(collection_info.full_name, param)
      setattr(self, param, value)

    self._self_link = '{0}{1}'.format(
        self._endpoint_url, uritemplate.expand(self._path, self.AsDict()))
    if self._collection_info.api_name in ('compute', 'storage',
                                          'certificatemanager'):
      # TODO(b/15425944): Unquote URLs for now for these apis.
      self._self_link = urllib.parse.unquote(self._self_link)
    self._initialized = True

  def __setattr__(self, key, value):
    if getattr(self, '_initialized', None) is not None:
      raise NotImplementedError(
          'Cannot set attribute {0}. '
          'Resource references are immutable.'.format(key))
    super(Resource, self).__setattr__(key, value)

  def __delattr__(self, key):
    raise NotImplementedError(
        'Cannot delete attribute {0}. '
        'Resource references are immutable.'.format(key))

  def Collection(self):
    collection = self._collection_info.full_name
    if self._subcollection:
      return collection + '.' + self._subcollection
    return collection

  def GetCollectionInfo(self):
    return self._collection_info

  def Name(self):
    if self._params:
      # The last param is defined to be the resource's "name".
      return getattr(self, self._params[-1])
    return None

  def RelativeName(self, url_escape=False):
    """Relative resource name.

    A URI path ([path-noscheme](http://tools.ietf.org/html/rfc3986#appendix-A))
    without the leading "/". It identifies a resource within the API service.
    For example:
      "shelves/shelf1/books/book2"

    Args:
      url_escape: bool, if true would url escape each parameter.
    Returns:
       Unescaped part of SelfLink which is essentially base_url + relative_name.
       For example if SelfLink is
         https://pubsub.googleapis.com/v1/projects/myprj/topics/mytopic
       then relative name is
         projects/myprj/topics/mytopic.
    """
    escape_func = urllib.parse.quote if url_escape else lambda x, safe: x

    effective_params = dict(
        [(k, escape_func(getattr(self, k), safe=''))
         for k in self._params])

    return urllib.parse.unquote(
        uritemplate.expand(self._path, effective_params))

  def AsDict(self):
    """Returns resource reference parameters and its values."""
    return collections.OrderedDict(
        [
            [param, getattr(self, param)] for param in self._params
        ]
    )

  def AsList(self):
    """Returns resource reference values."""
    return [getattr(self, param) for param in self._params]

  # TODO(b/130649099): add support for domain-splitting style URI.
  def SelfLink(self):
    """Returns URI for this resource."""
    return self._self_link

  def Parent(self, parent_collection=None):
    """Gets a reference to the parent of this resource.

    If parent_collection is not given, we attempt to automatically determine it
    by finding the collection within the same API that has the correct set of
    URI parameters for what we expect. If the parent collection cannot be
    automatically determined, it can be specified manually.

    Args:
      parent_collection: str, The full collection name of the parent resource.
        Only required if it cannot be automatically determined.

    Raises:
      ParentCollectionResolutionException: If the parent collection cannot be
        determined or doesn't exist.
      ParentCollectionMismatchException: If the given or auto-resolved parent
       collection does not have the expected URI parameters.

    Returns:
      Resource, The reference to the parent resource.
    """
    parent_params = self._params[:-1]
    all_collections = self._registry.parsers_by_collection[
        self._collection_info.api_name][self._collection_info.api_version]

    if parent_collection:
      # Parent explicitly provided. Make sure it exists and that the params
      # match what we would expect the parent to have.
      try:
        parent_parser = all_collections[parent_collection]
      except KeyError:
        raise UnknownCollectionException(parent_collection)
      actual_parent_params = parent_parser.collection_info.GetParams('')
      if actual_parent_params != parent_params:
        raise ParentCollectionMismatchException(
            self.Collection(), parent_collection, parent_params,
            actual_parent_params)
    else:
      # Auto resolve the parent collection by finding the collection with
      # matching parameters.
      for collection, parser in six.iteritems(all_collections):
        if parser.collection_info.GetParams('') == parent_params:
          parent_collection = collection
          break
      if not parent_collection:
        raise ParentCollectionResolutionException(
            self.Collection(), parent_params)

    parent_param_values = {k: getattr(self, k) for k in parent_params}
    ref = self._registry.Parse(None, parent_param_values,
                               collection=parent_collection)
    return ref

  def __str__(self):
    return self._self_link

  def __eq__(self, other):
    if isinstance(other, Resource):
      return self.SelfLink() == other.SelfLink()
    return False

  def __lt__(self, other):
    return self.SelfLink() < other.SelfLink()

  def __hash__(self):
    return hash(self._self_link)

  def __repr__(self):
    return self._self_link


def _GRIsAreEnabled():
  """Returns True if GRIs are enabled."""
  return (properties.VALUES.core.enable_gri.GetBool() or
          properties.VALUES.core.resource_completion_style.Get() == 'gri')


def _APINameFromCollection(collection):
  """Get the API name from a collection name like 'api.parents.children'.

  Args:
    collection: str, The collection name.

  Returns:
    str: The API name.
  """
  return collection.split('.')[0]


class GRIException(UserError):
  """Base class for all GRI related exceptions."""
  pass


class InvalidGRIFormatException(GRIException):
  """Exception for when a GRI is syntactically invalid."""

  def __init__(self, gri):
    super(InvalidGRIFormatException, self).__init__(
        'The given GRI [{gri}] is invalid and could not be parsed.\n'
        'Valid GRIs take the form of: a:b:c::api.collection'.format(gri=gri)
    )


class InvalidGRICollectionSyntaxException(GRIException):
  """Exception for when the collection part of a GRI is syntactically invalid.
  """

  def __init__(self, gri, collection):
    super(InvalidGRICollectionSyntaxException, self).__init__(
        'The given GRI [{gri}] could not be parsed because the collection '
        '[{collection}] is invalid'.format(gri=gri, collection=collection)
    )


class GRICollectionMismatchException(GRIException):
  """Exception for when the parsed GRI collection does not match the expected.
  """

  def __init__(self, gri, expected_collection, parsed_collection):
    super(GRICollectionMismatchException, self).__init__(
        'The given GRI [{gri}] could not be parsed because collection '
        '[{expected_collection}] was expected but [{parsed_collection}] was '
        'provided. Provide a GRI with the correct collection or drop the '
        'specified collection.'.format(gri=gri,
                                       expected_collection=expected_collection,
                                       parsed_collection=parsed_collection)
    )


class InvalidGRIPathSyntaxException(GRIException):
  """Exception for when a part of the path of the GRI is syntactically invalid.
  """

  def __init__(self, gri, message):
    super(InvalidGRIPathSyntaxException, self).__init__(
        'The given GRI [{gri}] could not be parsed because the path is invalid:'
        ' {message}'.format(gri=gri, message=message)
    )


class GRIPathMismatchException(GRIException):
  """Exception for when the path has the wrong number of segments."""

  def __init__(self, gri, params, collection=None):
    super(GRIPathMismatchException, self).__init__(
        'The given GRI [{gri}] does not match the required structure for this '
        'resource type. It must match the format: [{format}]'
        .format(gri=gri, format=(':'.join(reversed(params)) +
                                 ('::' + collection if collection else '')))
    )


class GRI(object):
  """Encapsulates a parsed GRI string.

  Attributes:
    path_fields: [str], The individual fields of the path portion of the GRI.
    collection: str, The collection portion of the GRI.
    is_fully_qualified: bool, True if the original GRI included the collection.
      This could be false if the collection is not defined, or if it was passed
      in explicitly during parsing.
  """

  def __init__(self, path_fields, collection=None, is_fully_qualified=False):
    """Use FromString() to construct a GRI."""
    self.path_fields = path_fields
    self.collection = collection
    self.is_fully_qualified = is_fully_qualified and collection is not None

  def __str__(self):
    gri = ':'.join([self._EscapePathSegment(s)
                    for s in self.path_fields]).rstrip(':')
    if self.is_fully_qualified:
      gri += '::' + self.collection
    return gri

  @classmethod
  def FromString(cls, gri, collection=None, validate=True):
    """Parses a GRI from a string.

    Args:
      gri: str, The GRI to parse.
      collection: str, The collection this GRI is for. If provided and the GRI
        contains a collection, they must match. If not provided, the collection
        in the GRI will be used, or None if it is not specified.
      validate: bool, Validate syntax. Use validate=False to handle GRIs under
        construction.

    Returns:
      A parsed GRI object.

    Raises:
      GRICollectionMismatchException: If the given collection does not match the
        collection specified in the GRI.
    """
    path, parsed_collection = cls._SplitCollection(gri, validate=validate)

    if not collection:
      # No collection was provided, use the one the was parsed from the GRI.
      # Could be None at this point.
      collection = parsed_collection
    elif validate:
      # A collection was provided, validate it for syntax.
      cls._ValidateCollection(gri, collection)
      if parsed_collection and parsed_collection != collection:
        # There was also a collection in the GRI, ensure it matches.
        raise GRICollectionMismatchException(
            gri, expected_collection=collection,
            parsed_collection=parsed_collection)

    path_fields = cls._SplitPath(path)

    return GRI(
        path_fields, collection, is_fully_qualified=bool(parsed_collection))

  @classmethod
  def _SplitCollection(cls, gri, validate=True):
    """Splits a GRI into its path and collection segments.

    Args:
      gri: str, The GRI string to parse.
      validate: bool, Validate syntax. Use validate=False to handle GRIs under
        construction.

    Returns:
      (str, str), The path and collection parts of the string. The
      collection may be None if not specified in the GRI.

    Raises:
      InvalidGRIFormatException: If the GRI cannot be parsed.
      InvalidGRIPathSyntaxException: If the GRI path cannot be parsed.
    """
    if not gri:
      return None, None
    # This is a very complicated regex for what is otherwise a simple concept.
    # It is basically trying to split the string on double colon separators
    # which are :: not surrounded by {}.  You cannot do a negation in regex, so
    # it does this by doing a positive match of {..[^}] [^{]::} and [^{]::[^}].
    # Because we want to split only on the colons, we use look aheads and
    # behinds in order to not consume characters (so split does not consider
    # them as part of the match.
    parts = re.split(r'(?=(?<={)::+[^:}]|(?<=[^:{])::+}|(?<=[^:{])::+[^:}])::',
                     gri)
    if len(parts) > 2:
      raise InvalidGRIFormatException(gri)
    elif len(parts) == 2:
      path, parsed_collection = parts[0], parts[1]
      if validate:
        cls._ValidateCollection(gri, parsed_collection)
    else:
      path, parsed_collection = parts[0], None

    # The regex can't correctly match ':' at the beginning or the end, but in
    # either case, they are invalid.
    if validate and (path.startswith(':') or path.endswith(':')):
      raise InvalidGRIPathSyntaxException(
          gri, 'GRIs cannot have empty path segments.')

    return path, parsed_collection

  @classmethod
  def _ValidateCollection(cls, gri, collection):
    # Matches: api.collection or api.collection.subcollection (with any level
    # of nesting).
    if not re.match(r'^\w+\.\w+(?:\.\w+)*$', collection):
      raise InvalidGRICollectionSyntaxException(gri, collection)

  @classmethod
  def _SplitPath(cls, path):
    """Splits a GRI into its individual path segments.

    Args:
      path: str, The path segment of the GRI (from _SplitCollection)

    Returns:
      [str], A list of the path segments of the GRI.
    """
    if not path:
      return []
    # See above method for the description of this regex. It is the same except
    # with single colons instead of double.
    parts = re.split(r'(?=(?<={):+[^:}]|(?<=[^:{]):+}|(?<=[^:{]):+[^:}]):',
                     path)

    # Unescape escaped colons by stripping off one layer of braces.
    return [cls._UnescapePathSegment(part) for part in parts]

  @classmethod
  def _UnescapePathSegment(cls, segment):
    return re.sub(r'{(:+)}', r'\1', segment)

  @classmethod
  def _EscapePathSegment(cls, segment):
    return re.sub(r'(:+)', r'{\1}', segment)


def HasOverriddenEndpoint(api_name):
  """Check if a URL is the result of an endpoint override."""
  try:
    endpoint_override = properties.VALUES.api_endpoint_overrides.Property(
        api_name).Get()
  except properties.NoSuchPropertyError:
    return False

  return bool(endpoint_override)


class Registry(object):
  """Keep a list of all the resource collections and their parsing functions.

  Attributes:
    parsers_by_collection: {str: {str: {str: _ResourceParser}}}, All the
        resource parsers indexed by their api name, api version
        and collection name.
    parsers_by_url: Deeply-nested dict. The first key is the API's URL root,
        and each key after that is one of the remaining tokens which can be
        either a constant or a parameter name. At the end, a key of None
        indicates the value is a _ResourceParser.
    registered_apis: {str: str}, The most recently registered API version for
        each API. For instance, {'dns': 'v1', 'compute': 'alpha'}.
  """

  def __init__(self, parsers_by_collection=None, parsers_by_url=None,
               registered_apis=None):
    self.parsers_by_collection = parsers_by_collection or {}
    self.parsers_by_url = parsers_by_url or {}
    self.registered_apis = registered_apis or {}

  def Clone(self):
    """Clones this registry.

    Clones share the same underlying parser data and differ only in which API
    versions were most recently registered.

    Returns:
      Registry, The cloned registry.
    """
    return Registry(
        parsers_by_collection=self.parsers_by_collection,
        parsers_by_url=self.parsers_by_url,
        registered_apis=self.registered_apis.copy())

  def RegisterApiByName(self, api_name, api_version=None):
    """Register the given API if it has not been registered already.

    Args:
      api_name: str, The API name.
      api_version: str, The API version, None for the default version.
    Returns:
      api version which was registered.
    """
    registered_version = self.registered_apis.get(api_name, None)
    if api_version is None:
      if registered_version:
        # Use last registered api version as default.
        api_version = registered_version
      else:
        api_version = apis_internal._GetDefaultVersion(api_name)  # pylint:disable=protected-access

    # Populate the collection info if we haven't already.
    if api_version not in self.parsers_by_collection.get(api_name, {}):
      # pylint:disable=protected-access
      for collection in apis_internal._GetApiCollections(api_name, api_version):
        self._RegisterCollection(collection)

    self.registered_apis[api_name] = api_version
    return api_version

  def _RegisterCollection(self, collection_info):
    """Registers given collection with registry.

    Args:
      collection_info: CollectionInfo, description of resource collection.
    Raises:
      AmbiguousAPIException: If the API defines a collection that has already
          been added.
      AmbiguousResourcePath: If api uses same path for multiple resources.
    """
    api_name = collection_info.api_name
    api_version = collection_info.api_version
    parser = _ResourceParser(self, collection_info)

    collection_parsers = (self.parsers_by_collection.setdefault(api_name, {})
                          .setdefault(api_version, {}))
    collection_subpaths = collection_info.flat_paths
    if not collection_subpaths:
      collection_subpaths = {'': collection_info.path}

    for subname, path in six.iteritems(collection_subpaths):
      collection_name = collection_info.full_name + (
          '.' + subname if subname else '')
      existing_parser = collection_parsers.get(collection_name)
      if existing_parser is not None:
        raise AmbiguousAPIException(collection_name,
                                    [collection_info.base_url,
                                     existing_parser.collection_info.base_url])
      collection_parsers[collection_name] = parser

      if collection_info.enable_uri_parsing:
        self._AddParserForUriPath(api_name, api_version, subname, parser, path)

  def _AddParserForUriPath(self, api_name, api_version,
                           subcollection, parser, path):
    """Registers parser for given path."""
    tokens = [api_name, api_version] + path.split('/')

    # Build up a search tree to match URLs against URL templates.
    # The tree will branch at each URL segment, where the first segment
    # is the API's base url, and each subsequent segment is a token in
    # the instance's get method's relative path. At the leaf, a key of
    # None indicates that the URL can finish here, and provides the parser
    # for this resource.
    cur_level = self.parsers_by_url
    while tokens:
      token = tokens.pop(0)
      if token[0] == '{' and token[-1] == '}':
        token = '{}'
      if token not in cur_level:
        cur_level[token] = {}
      cur_level = cur_level[token]
    if None in cur_level:
      raise AmbiguousResourcePath(cur_level[None], parser.collection_info.name)

    cur_level[None] = subcollection, parser

  def GetParserForCollection(self, collection, api_version=None):
    """Returns a parser object for collection.

    Args:
      collection: str, The resource collection name.
      api_version: str, The API version, None for the default version.

    Raises:
      InvalidCollectionException: If there is no parser.

    Returns:
      The parser object for collection.
    """
    # Register relevant API if necessary and possible
    api_name = _APINameFromCollection(collection)
    api_version = self.RegisterApiByName(api_name, api_version=api_version)

    parser = (self.parsers_by_collection
              .get(api_name, {}).get(api_version, {}).get(collection, None))
    if parser is None:
      raise InvalidCollectionException(collection, api_version)
    return parser

  def ParseResourceId(self, collection, resource_id, kwargs, validate=True,
                      api_version=None, default_resolver=None):
    """Parse a resource id string into a Resource.

    Args:
      collection: str, the name/id for the resource from commandline argument.
      resource_id: str, Some resource identifier.
          Can be None to indicate all params should be taken from kwargs.
      kwargs: {str:(str or func()->str)}, flags (available from context) or
          resolvers that can help parse this resource. If the fields in
          collection-path do not provide all the necessary information,
          kwargs will be searched for what remains.
      validate: bool, Validate syntax. Use validate=False to handle IDs under
        construction. An ID can be:
          fully qualified - All parameters are specified and have valid syntax.
          partially qualified - Some parameters are specified, all have valid
            syntax.
          under construction - Some parameters may be missing or too short and
            not meet the syntax constraints. With additional characters they
            would have valid syntax. Used by completers that build IDs from
            strings character by character. Completers need to do the
            string => parameters => string round trip with validate=False to
            handle the "add character TAB" cycle.
      api_version: str, The API version, None for the default version.
      default_resolver: func(str) => str, a default param resolver function
        called if kwargs doesn't resolve a param.

    Returns:
      protorpc.messages.Message, The object containing info about this resource.

    Raises:
      InvalidCollectionException: If the provided collection-path is malformed.
      UnknownCollectionException: If the collection of the resource could not be
          determined.

    """
    if _GRIsAreEnabled():
      # If collection is set already, it will be validated in the split method.
      # If it is unknown, it will come back with the parsed collection or None.
      # Ideally we would pass the parsed GRI to the parser instead of reparsing,
      # but this library would need some refactoring to make that clean.
      collection = GRI.FromString(
          resource_id, collection=collection, validate=validate).collection

    if not collection:
      raise UnknownCollectionException(resource_id)

    parser = self.GetParserForCollection(collection, api_version=api_version)
    base_url = GetApiBaseUrl(parser.collection_info.api_name,
                             parser.collection_info.api_version)

    parser_collection = parser.collection_info.full_name
    subcollection = ''
    if len(parser_collection) != len(collection):
      subcollection = collection[len(parser_collection)+1:]
    return parser.ParseResourceId(resource_id, kwargs, base_url, subcollection,
                                  validate=validate,
                                  default_resolver=default_resolver)

  def GetCollectionInfo(self, collection_name, api_version=None):
    api_name = _APINameFromCollection(collection_name)
    api_version = self.RegisterApiByName(api_name, api_version=api_version)
    parser = (self.parsers_by_collection
              .get(api_name, {}).get(api_version, {})
              .get(collection_name, None))
    if parser is None:
      raise InvalidCollectionException(collection_name, api_version)
    return parser.collection_info

  def ParseURL(self, url):
    """Parse a URL into a Resource.

    This method does not yet handle "api.google.com" in place of
    "www.googleapis.com/api/version".

    Searches self.parsers_by_url to find a _ResourceParser. The parsers_by_url
    attribute is a deeply nested dictionary, where each key corresponds to
    a URL segment. The first segment is an API's base URL (eg.
    "https://www.googleapis.com/compute/v1/"), and after that it's each
    remaining token in the URL, split on '/'. Then a path down the tree is
    followed, keyed by the extracted pieces of the provided URL. If the key in
    the tree is a literal string, like "project" in .../project/{project}/...,
    the token from the URL must match exactly. If it's a parameter, like
    "{project}", then any token can match it, and that token is stored in a
    dict of params to with the associated key ("project" in this case). If there
    are no URL tokens left, and one of the keys at the current level is None,
    the None points to a _ResourceParser that can turn the collected
    params into a Resource.

    Args:
      url: str, The URL of the resource.

    Returns:
      Resource, The resource indicated by the provided URL.

    Raises:
      InvalidResourceException: If the provided URL could not be turned into
          a cloud resource.
    """
    match = _URL_RE.match(url)
    if not match:
      raise InvalidResourceException(url, reason='unknown API host')

    api_name, api_version, resource_path = (
        resource_util.SplitEndpointUrl(url))

    try:
      # pylint:disable=protected-access
      versions = apis_internal._GetVersions(api_name)
    except apis_util.UnknownAPIError:
      raise InvalidResourceException(url, 'unknown api {}'.format(api_name))

    if api_version not in versions:
      if HasOverriddenEndpoint(api_name):
        # Use last registered, or default, api version in case of override.
        api_version = self.registered_apis.get(
            # pylint:disable=protected-access
            api_name, apis_internal._GetDefaultVersion(api_name))

    if api_version not in versions:
      raise InvalidResourceException(
          url, 'unknown api version {}'.format(api_version))

    tokens = [api_name, api_version] + resource_path.split('/')
    endpoint = url[:-len(resource_path)]

    # Register relevant API if necessary and possible
    try:
      self.RegisterApiByName(api_name, api_version=api_version)
    except apis_util.UnknownAPIError:
      raise InvalidResourceException(url, 'unknown api {}'.format(api_name))
    except apis_util.UnknownVersionError:
      raise InvalidResourceException(
          url, 'unknown api version {}'.format(api_version))

    params = []
    cur_level = self.parsers_by_url
    for i, token in enumerate(tokens):
      if token in cur_level:
        # If the literal token is already here, follow it down.
        cur_level = cur_level[token]
        continue

      # If the literal token is not here, see if this can be a parameter.
      param, next_level = '', {}  # Predefine these to silence linter.
      for param, next_level in six.iteritems(cur_level):
        if param == '{}':
          break
      else:
        raise InvalidResourceException(
            url, reason='Could not parse at [{}]'.format(token))

      if len(next_level) == 1 and None in next_level:
        # This is the last parameter so we can combine the remaining tokens.
        token = '/'.join(tokens[i:])
        params.append(urllib.parse.unquote(token))
        cur_level = next_level
        break

      # Clean up the provided value
      params.append(urllib.parse.unquote(token))

      # Keep digging down.
      cur_level = next_level

    # No more tokens, so look for a parser.
    if None not in cur_level:
      raise InvalidResourceException(url, 'Url too short.')
    subcollection, parser = cur_level[None]
    params = dict(zip(parser.collection_info.GetParams(subcollection), params))
    return parser.ParseResourceId(
        None, params, base_url=endpoint,
        subcollection=subcollection)

  def ParseRelativeName(self, relative_name, collection, url_unescape=False,
                        api_version=None):
    """Parser relative names. See Resource.RelativeName() method."""
    parser = self.GetParserForCollection(collection, api_version=api_version)
    base_url = GetApiBaseUrl(parser.collection_info.api_name,
                             parser.collection_info.api_version)
    subcollection = parser.collection_info.GetSubcollection(collection)

    return parser.ParseRelativeName(
        relative_name, base_url, subcollection, url_unescape)

  def ParseStorageURL(self, url, collection=None):
    """Parse gs://bucket/object_path into storage.v1 api resource."""
    match = _GCS_URL_RE.match(url)
    if not match:
      raise InvalidResourceException(url, 'Not a storage url')
    if match.group(2):
      if collection and collection != 'storage.objects':
        raise WrongResourceCollectionException('storage.objects', collection,
                                               url)
      return self.ParseResourceId(
          collection='storage.objects',
          resource_id=None,
          kwargs={'bucket': match.group(1), 'object': match.group(2)})

    if collection and collection != 'storage.buckets':
      raise WrongResourceCollectionException('storage.buckets', collection, url)
    return self.ParseResourceId(
        collection='storage.buckets',
        resource_id=None,
        kwargs={'bucket': match.group(1)})

  def Parse(self, line, params=None, collection=None, enforce_collection=True,
            validate=True, default_resolver=None, api_version=None):
    """Parse a Cloud resource from a command line.

    Args:
      line: str, The argument provided on the command line.
      params: {str:(str or func()->str)}, flags (available from context) or
        resolvers that can help parse this resource. If the fields in
        collection-path do not provide all the necessary information, params
        will be searched for what remains.
      collection: str, The resource's collection, or None if it should be
        inferred from the line.
      enforce_collection: bool, fail unless parsed resource is of this
        specified collection, this is applicable only if line is URL.
      validate: bool, Validate syntax. Use validate=False to handle IDs under
        construction.
      default_resolver: func(str) => str, a default param resolver function
        called if params doesn't resolve a param.
      api_version: str, The API version, None for the default version.

    Returns:
      A resource object.

    Raises:
      InvalidResourceException: If the line is invalid.
      RequiredFieldOmittedException: If resource is underspecified.
      UnknownCollectionException: If no collection is provided or can be
          inferred.
      WrongResourceCollectionException: If the provided URL points into a
          collection other than the one specified.
    """
    if line:
      if line.startswith('https://') or line.startswith('http://'):
        try:
          ref = self.ParseURL(line)
        except InvalidResourceException as e:
          bucket = None

          gcs_url = apis_internal.UniversifyAddress(_GCS_URL)
          gcs_alt_url = apis_internal.UniversifyAddress(_GCS_ALT_URL)
          gcs_alt_url_short = apis_internal.UniversifyAddress(
              _GCS_ALT_URL_SHORT)
          if line.startswith(gcs_url):
            try:
              bucket_prefix, bucket, object_prefix, objectpath = (
                  line[len(gcs_url):].split('/', 3))
            except ValueError:
              raise e
            if (bucket_prefix, object_prefix) != ('b', 'o'):
              raise
          elif line.startswith(gcs_alt_url_short):
            try:
              try:
                bucket_prefix, bucket, object_prefix, objectpath = (
                    line[len(gcs_alt_url):].split('/', 3))
              except ValueError:
                raise e
              if (bucket_prefix, object_prefix) != ('b', 'o'):
                raise
            except InvalidResourceException as e:
              line = line[len(gcs_alt_url_short):]
              if '/' in line:
                bucket, objectpath = line.split('/', 1)
              else:
                return self.ParseResourceId(
                    collection='storage.buckets',
                    resource_id=None,
                    kwargs={'bucket': line})
          if bucket is not None:
            return self.ParseResourceId(
                collection='storage.objects',
                resource_id=None,
                kwargs={'bucket': bucket, 'object': objectpath})
          raise
        # TODO(b/35870652): consider not doing this here.
        # Validation of the argument is a distinct concern.
        if (enforce_collection and collection and
            ref.Collection() != collection):
          raise WrongResourceCollectionException(
              expected=collection,
              got=ref.Collection(),
              path=ref.SelfLink())
        return ref
      elif line.startswith('gs://'):
        return self.ParseStorageURL(line, collection=collection)

    if validate and line is not None and not line:
      raise InvalidResourceException(line)

    return self.ParseResourceId(collection, line, params or {},
                                api_version=api_version,
                                validate=validate,
                                default_resolver=default_resolver)

  def Create(self, collection, **params):
    """Create a Resource from known collection and params.

    Args:
      collection: str, The name of the collection the resource belongs to.
      **params: {str:str}, The values for each of the resource params.

    Returns:
      Resource, The constructed resource.
    """
    return self.Parse(None, collection=collection, params=params)


REGISTRY = Registry()


def GetApiBaseUrl(api_name, api_version):
  """Determine base url to use for resources of given version."""
  # Use current override endpoint for this resource name.
  endpoint_override_property = getattr(
      properties.VALUES.api_endpoint_overrides, api_name, None)
  base_url = None
  if endpoint_override_property is not None:
    base_url = endpoint_override_property.Get()
    if base_url is not None:
      # Check base url style. If it includes api version then override
      # also replaces the version, otherwise it only overrides the domain.
      # pylint:disable=protected-access
      client_base_url = apis_internal._GetBaseUrlFromApi(api_name, api_version)

      _, url_version, _ = resource_util.SplitEndpointUrl(client_base_url)
      if url_version is None:
        base_url += api_version + '/'
  if base_url is not None:
    base_url = apis_internal.UniversifyAddress(base_url)
  return base_url


def GetApiBaseUrlOrThrow(api_name, api_version):
  """Determine base url to use for resources of given version."""
  # Uses current override endpoint for this resource name or throws an exception
  api_base_url = GetApiBaseUrl(api_name, api_version)
  if api_base_url is None:
    raise UserError(
        'gcloud config property {} needs to be set in api_endpoint_overrides '
        'section.'.format(api_name))
  return api_base_url
