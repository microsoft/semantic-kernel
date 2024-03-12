# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Common flags for some of the Service Directory commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


def AddAddressFlag(parser):
  """Adds an address flag for service-directory commands."""
  return base.Argument(
      '--address',
      help="""\
        IPv4 or IPv6 address of the endpoint. The default is
        empty string.""").AddToParser(parser)


def AddPortFlag(parser):
  """Adds a port flag for service-directory commands."""
  return base.Argument(
      '--port',
      help="""\
        Port that the endpoint is running on, must be in the range of
        [0, 65535]. The default is 0.""",
      type=int).AddToParser(parser)


def AddNetworkFlag(parser):
  """Adds a network flag for service-directory commands."""
  return base.Argument(
      '--network',
      help="""\
        Specifies the Google Compute Engine Network (VPC) of the Endpoint.
        Network and Project existence is not checked.
        Example: `projects/<PROJECT_NUM>/locations/global/networks/<NETWORK_NAME>`
        The default is empty string.""").AddToParser(parser)


def AddAnnotationsFlag(parser, resource_type, dictionary_size_limit):
  """Adds annotations flags for service-directory commands."""
  return base.Argument(
      '--annotations',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help="""\
           Annotations for the {}.

           Annotations take the form of key/value string pairs. Keys are
           composed of an optional prefix and a name segment, separated by a
           slash(/). Prefixes and names must be composed of alphanumeric
           characters, dashes, and dots. Names may also use underscores. There
           are no character restrictions on what may go into the value of an
           annotation. The entire dictionary is limited to {} characters, spread
           across all key-value pairs.
           """.format(resource_type, dictionary_size_limit)).AddToParser(parser)


def AddMetadataFlag(parser, resource_type, dictionary_size_limit):
  """Adds metadata flags for service-directory commands."""
  return base.Argument(
      '--metadata',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help="""\
           Metadata for the {}.

           Metadata takes the form of key/value string pairs. Keys are
           composed of an optional prefix and a name segment, separated by a
           slash(/). Prefixes and names must be composed of alphanumeric
           characters, dashes, and dots. Names may also use underscores. There
           are no character restrictions on what may go into the value of a
           metadata. The entire dictionary is limited to {} characters, spread
           across all key-value pairs.
           """.format(resource_type, dictionary_size_limit)).AddToParser(parser)


def AddLabelsFlag(parser, resource_type):
  """Adds labels flags for service-directory commands."""
  return base.Argument(
      '--labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help="""\
           Resource labels associated with the {}.
           """.format(resource_type)).AddToParser(parser)


def AddMaxEndpointsFlag(parser):
  """Adds max_endpoints flags for service-directory commands."""
  return base.Argument(
      '--max-endpoints',
      type=int,
      help="""\
           Maximum number of endpoints to return.
           """).AddToParser(parser)


def AddEndpointFilterFlag(parser):
  """Adds endpoint filter flags for service-directory commands."""
  return base.Argument(
      '--endpoint-filter',
      help="""\
        Apply a Boolean filter EXPRESSION to each endpoint in the service.
        If the expression evaluates True, then that endpoint is listed.
        """,
  ).AddToParser(parser)
