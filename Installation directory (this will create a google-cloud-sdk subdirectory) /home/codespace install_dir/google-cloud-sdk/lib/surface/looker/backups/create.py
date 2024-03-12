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
"""Create a backup of a Looker instance."""

from googlecloudsdk.api_lib.looker import backups
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.looker import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

_DETAILED_HELP = {
    'DESCRIPTION':
        'Create a backup of a Looker instance.',
    'EXAMPLES':
        """ \
        To create a backup of an instance with the name my-looker-instance, in
        region us-central1 run:

          $ {command} --instance='my-looker-instance' --region='us-central1'
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateInstanceBackup(base.CreateCommand):
  """Create a backup of a Looker instance."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddInstance(parser)
    parser.add_argument(
        '--region',
        required=True,
        help=(
            """ \
            The name of the Looker region of the instance. Overrides the
            default looker/region property value for this command invocation.
            """
        ))

  def Run(self, args):
    parent = resources.REGISTRY.Parse(
        args.instance,
        params={
            'projectsId': properties.VALUES.core.project.GetOrFail,
            'locationsId': args.region
        },
        api_version=backups.API_VERSION_DEFAULT,
        collection='looker.projects.locations.instances').RelativeName()

    return backups.CreateBackup(parent)
