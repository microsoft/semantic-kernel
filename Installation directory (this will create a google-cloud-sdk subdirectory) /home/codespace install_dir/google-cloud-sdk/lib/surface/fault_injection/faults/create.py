# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Create Command for fault."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.fault_injection import faults
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.fault_injection import flags


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To create a fault with the id `my-fault` and file path `my/path/to/yaml`, run:

          $ {command} my-fault --file=my/path/to/yaml
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Command to create a fault in the Project/Location."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddCreateFaultFlags(parser)

  def Run(self, args):
    """Run the create command."""
    client = faults.FaultsClient()
    fault_ref = args.CONCEPTS.fault.Parse()
    parent_ref = fault_ref.Parent()
    if not fault_ref.Name():
      raise exceptions.InvalidArgumentException(
          'fault', 'fault id must be non-empty.'
      )
    if not args.file:
      raise exceptions.InvalidArgumentException(
          'fault', 'file must be non-empty.'
      )
    return client.Create(
        fault=fault_ref.Name(),
        faultconfig=args.file,
        parent=parent_ref.RelativeName(),
    )
