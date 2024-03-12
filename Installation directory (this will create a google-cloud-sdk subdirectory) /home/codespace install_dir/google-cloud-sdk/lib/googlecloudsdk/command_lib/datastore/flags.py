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
"""Flags and helpers for the datastore related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers


def AddEntityFilterFlags(parser):
  """Adds flags for entity filters to the given parser."""
  parser.add_argument(
      '--kinds',
      metavar='KIND',
      type=arg_parsers.ArgList(),
      help="""
      A list specifying what kinds will be included in the operation. When
      omitted, all Kinds are included. For example, to operate on only the
      'Customer' and 'Order' Kinds:

        $ {command} --kinds='Customer','Order'
      """)

  parser.add_argument(
      '--namespaces',
      metavar='NAMESPACE',
      type=arg_parsers.ArgList(),
      help="""
      A list specifying what namespaces will be included in the operation.
      When omitted, all namespaces are included in the operation,
      including the default namespace. To specify that *only* the default
      namespace should be operated on, use the special symbol '(default)'.
      For example, to operate on entities from both the 'customers' and default
      namespaces:

        $ {command} --namespaces='(default)','customers'
      """)


def AddLabelsFlag(parser):
  """Adds a --operation-labels flag to the given parser."""
  parser.add_argument(
      '--operation-labels',
      metavar='OPERATION_LABEL',
      type=arg_parsers.ArgDict(),
      help="""
      A string:string map of custom labels to associate with this operation.
      For example:

        $ {command} --operation-labels=comment='customer orders','sales rep'=pending
      """)


def AddIndexFileFlag(parser):
  """Adds a index_file flag to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      'index_file',
      help="""
        The path to your `index.yaml` file. For a detailed look into defining
        your `index.yaml` file, refer to this configuration guide:
        https://cloud.google.com/datastore/docs/tools/indexconfig#Datastore_About_index_yaml
        """,
  )


def AddOperationNameFlag(parser, operation_type):
  """Adds a name flag to the given parser.

  Args:
    parser: The argparse parser.
    operation_type: The operate type displayed in help text, a str.
  """
  parser.add_argument(
      'name',
      type=str,
      default=None,
      help="""
        The unique name of the Operation to {}, formatted as either the full
        or relative resource path:

          projects/my-app-id/operations/foo

        or:

          foo
        """.format(operation_type),
  )
