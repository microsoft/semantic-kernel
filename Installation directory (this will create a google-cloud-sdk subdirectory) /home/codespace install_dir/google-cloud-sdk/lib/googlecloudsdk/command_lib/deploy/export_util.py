# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for the cloud deploy export commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import files


def Export(manifest_dict, args):
  """Writes a message as YAML to a stream.

  Args:
    manifest_dict: parsed yaml definition.
    args: arguments from command line.
  """
  if args.destination:
    with files.FileWriter(args.destination) as stream:
      resource_printer.Print(manifest_dict, print_format='yaml', out=stream)
  else:
    resource_printer.Print(manifest_dict, print_format='yaml')
