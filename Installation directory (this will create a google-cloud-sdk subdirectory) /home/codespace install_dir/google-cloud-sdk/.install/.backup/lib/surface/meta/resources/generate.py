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

"""A command that generates resource URIs given collection and api version."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
import six
from six.moves import range


class Parse(base.Command):
  """Cloud SDK resource test URI generator.

  *{command}* is an handy way to generate test URIs for the resource parser.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--collection',
        metavar='NAME',
        required=True,
        help='The resource collection name of the resource to parse.')
    parser.add_argument(
        '--api-version',
        metavar='VERSION',
        help=('The resource collection API version. The collection default '
              'is used if not specified.'))
    parser.add_argument(
        '--count',
        default=1,
        type=arg_parsers.BoundedInt(lower_bound=1),
        help='The number of test resource URIs to generate.')

  def Run(self, args):
    """Returns the list of generated resources."""
    collection_info = resources.REGISTRY.GetCollectionInfo(
        args.collection, api_version=args.api_version)
    templates = {}
    params = collection_info.GetParams('')
    if not params:
      # There are some collections that don't operate on resources but are
      # manually created in regen_apis_config.yaml. If there are no template
      # params, don't try to generate resources for them.
      return []
    for param in params:
      templates[param] = 'my-' + param.lower() + '-{}'
    uris = []
    for i in range(1, args.count + 1):
      params = {}
      for param, template in six.iteritems(templates):
        params[param] = template.format(i)
      uri = resources.Resource(
          None, collection_info, '', params, None).SelfLink()
      uris.append(uri)
    return uris
