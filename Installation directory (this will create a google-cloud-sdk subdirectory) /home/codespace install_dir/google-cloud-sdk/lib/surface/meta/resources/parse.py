# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""A command that parses resources given collection and api version."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_printer

import six


class Parse(base.ListCommand):
  """Cloud SDK resource parser module tester.

  *{command}* is an handy way to debug the resource parser from the command
  line.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--api-version',
        metavar='VERSION',
        help=('The resource collection API version. The collection default '
              'is used if not specified.'))
    parser.add_argument(
        '--collection',
        metavar='NAME',
        help='The resource collection name of the resource to parse.')
    parser.add_argument(
        '--stack-trace',
        action='store_true',
        default=True,
        help=('Enable all exception stack traces, including Cloud SDK core '
              'exceptions.'))
    parser.add_argument(
        'resources_to_parse',
        nargs='*',
        help=('The list of resource URLs to parse. If not specified then '
              '*{command}* enters an interactive loop, prompting for URLs to '
              'parse.'))

  def Run(self, args):
    """Returns the parsed parameters for one resource."""
    if args.api_version:
      api_name = args.collection.split('.')[0]
      resources.REGISTRY.RegisterApiByName(
          api_name, api_version=args.api_version)

    if args.resources_to_parse:
      parsed_resources = []
      for uri in args.resources_to_parse:
        try:
          resource = resources.REGISTRY.Parse(uri, collection=args.collection)
        except (Exception, SystemExit) as e:  # pylint: disable=broad-except
          if args.stack_trace:
            exceptions.reraise(e)
          log.error(six.text_type(e))
          parsed_resources.append({
              'error': six.text_type(e),
              'uri': uri,
          })
          continue
        collection_info = resource.GetCollectionInfo()
        parsed_resources.append({
            'api_name': collection_info.api_name,
            'api_version': collection_info.api_version,
            'collection': collection_info.full_name,
            'params': resource.AsDict(),
            'uri': resource.SelfLink(),
        })
      return parsed_resources

    while True:
      uri = console_io.PromptResponse('PARSE> ')
      if uri is None:
        break
      if not uri:
        continue
      try:
        params = resources.REGISTRY.Parse(
            uri,
            collection=args.collection).AsDict()
      except (Exception, SystemExit) as e:  # pylint: disable=broad-except
        if args.stack_trace:
          exceptions.reraise(e)
        log.error(six.text_type(e))
        continue
      resource_printer.Print(params, 'json')
    sys.stderr.write('\n')
    return None

  def Epilog(self, items_were_listed=False):
    del items_were_listed
