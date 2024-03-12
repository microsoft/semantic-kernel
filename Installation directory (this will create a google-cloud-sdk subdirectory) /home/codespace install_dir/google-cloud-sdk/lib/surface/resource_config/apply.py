# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Apply a KRM configuration to a Google Cloud Platform resource filename or stdin."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.declarative import flags as declarative_flags
from googlecloudsdk.command_lib.util.declarative.clients import kcc_client
from googlecloudsdk.core.console import progress_tracker

_DETAILED_HELP = {
    'EXAMPLES':
        """
      To create or update the resource in file 'my-resource.yaml' in the current project run:
        $ {command} my-resource.yaml
    """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Apply(base.DeclarativeCommand):
  """Apply a KRM configuration to a Google Cloud Platform resource filename or stdin."""
  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    declarative_flags.AddResolveResourcesArg(parser)
    declarative_flags.AddApplyPathArg(parser)
    parser.display_info.AddFormat('yaml')

  def Run(self, args):
    resource_path = args.PATH
    resolve_refs = args.resolve_references
    client = kcc_client.KccClient()
    output = None
    with progress_tracker.ProgressTracker(
        message='Applying {}'.format(resource_path),
        aborted_message='Apply Cancelled'):
      output = client.ApplyConfig(resource_path, resolve_refs)
    return output

