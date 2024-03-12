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

"""Utilities related to adding flags for the gcloud meta api commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.util.apis import arg_marshalling
from googlecloudsdk.command_lib.util.apis import registry


def APICompleter(**_):
  return [a.name for a in registry.GetAllAPIs()]


def CollectionCompleter(**_):
  return [c.full_name for c in registry.GetAPICollections()]


def MethodCompleter(prefix, parsed_args, **_):
  del prefix
  collection = getattr(parsed_args, 'collection', None)
  if not collection:
    return []
  return [m.name for m in registry.GetMethods(collection)]


API_VERSION_FLAG = base.Argument(
    '--api-version',
    help='The version of the given API to use. If not provided, the default '
         'version of the API will be used.')

COLLECTION_FLAG = base.Argument(
    '--collection',
    required=True,
    completer=CollectionCompleter,
    help='The name of the collection to specify the method for.')

RAW_FLAG = base.Argument(
    '--raw',
    action='store_true',
    default=False,
    help='For list commands, the response is flattened to return the items as '
         'a list rather than returning the list response verbatim. Use this '
         'flag to disable this behavior and return the raw response.'
)

API_REQUIRED_FLAG = base.Argument(
    '--api',
    required=True,
    completer=APICompleter,
    help='The name of the API to get the attributes for.')


class MethodDynamicPositionalAction(parser_extensions.DynamicPositionalAction):
  """A DynamicPositionalAction that adds flags for a given method to the parser.

  Based on the value given for method, it looks up the valid fields for that
  method call and adds those flags to the parser.
  """

  def __init__(self, *args, **kwargs):
    # Pop the dest so that the superclass doesn't try to automatically save the
    # value of the arg to the namespace. We explicitly save the method ref
    # instead.
    self._dest = kwargs.pop('dest')
    super(MethodDynamicPositionalAction, self).__init__(*args, **kwargs)

  def GenerateArgs(self, namespace, method_name):
    # Get the collection from the existing parsed args.
    full_collection_name = getattr(namespace, 'collection', None)
    api_version = getattr(namespace, 'api_version', None)
    if not full_collection_name:
      raise c_exc.RequiredArgumentException(
          '--collection',
          'The collection name must be specified before the API method.')

    # Look up the method and get all the args for it.
    method = registry.GetMethod(full_collection_name, method_name,
                                api_version=api_version)

    arg_generator = arg_marshalling.AutoArgumentGenerator(method,
                                                          raw=namespace.raw)
    method_ref = MethodRef(namespace, method, arg_generator)
    setattr(namespace, self._dest, method_ref)

    return arg_generator.GenerateArgs()

  def Completions(self, prefix, parsed_args, **kwargs):
    return MethodCompleter(prefix, parsed_args, **kwargs)


class MethodRef(object):
  """Encapsulates a method specified on the command line with all its flags.

  This makes use of an ArgumentGenerator to generate and parse all the flags
  that correspond to a method. It provides a simple interface to the command so
  the implementor doesn't need to be aware of which flags were added and
  manually extract them. This knows which flags exist and what method fields
  they correspond to.
  """

  def __init__(self, namespace, method, arg_generator):
    """Creates the MethodRef.

    Args:
      namespace: The argparse namespace that holds the parsed args.
      method: APIMethod, The method.
      arg_generator: arg_marshalling.AutoArgumentGenerator, The generator for
        this method.
    """
    self.namespace = namespace
    self.method = method
    self.arg_generator = arg_generator

  def Call(self):
    """Execute the method.

    Returns:
      The result of the method call.
    """
    raw = self.arg_generator.raw
    request = self.arg_generator.CreateRequest(self.namespace)
    limit = self.arg_generator.Limit(self.namespace)
    page_size = self.arg_generator.PageSize(self.namespace)
    return self.method.Call(request, raw=raw, limit=limit, page_size=page_size)


