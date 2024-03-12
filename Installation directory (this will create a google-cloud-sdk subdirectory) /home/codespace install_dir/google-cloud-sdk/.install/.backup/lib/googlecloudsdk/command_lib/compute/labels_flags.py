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
"""Flags for GCE compute add/remove labels support."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


def AddArgsForAddLabels(parser, required=True):
  """Adds the required --labels flags for add-labels command."""
  required_labels_flag = base.Argument(
      '--labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      required=required,
      help='A list of labels to add.')

  required_labels_flag.AddToParser(parser)


def AddArgsForRemoveLabels(parser):
  """Adds the --labels and --all flags for remove-labels command."""

  args_group = parser.add_mutually_exclusive_group(required=True)
  args_group.add_argument(
      '--all',
      action='store_true',
      default=False,
      help='Remove all labels from the resource.')
  args_group.add_argument(
      '--labels',
      type=arg_parsers.ArgList(min_length=1),
      help="""
          A comma-separated list of label keys to remove from the resource.
          """,
      metavar='KEY')
