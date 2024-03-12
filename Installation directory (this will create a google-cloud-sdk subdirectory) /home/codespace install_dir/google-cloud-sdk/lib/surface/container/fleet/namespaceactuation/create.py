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
"""The command to create Namespace Actuation Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet.features import base


def ModeEnumTranslation(mode) -> str:
  if mode == 'unspecified':
    return 'ACTUATION_MODE_UNSPECIFIED'
  if mode == 'create-and-delete-if-created':
    return 'ACTUATION_MODE_CREATE_AND_DELETE_IF_CREATED'
  if mode == 'add-and-remove-fleet-labels':
    return 'ACTUATION_MODE_ADD_AND_REMOVE_FLEET_LABELS'


@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class Create(base.EnableCommand):
  """Create Namespace Actuation Feature.

  This command creates Namespace Actuation Feature in a fleet.

  ## EXAMPLES

  To create the Namespace Actuation Feature, run:

    $ {command}
  """

  feature_name = 'namespaceactuation'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--actuation-mode',
        type=str,
        default='unspecified',
        choices=[
            'unspecified',
            'create-and-delete-if-created',
            'add-and-remove-fleet-labels',
        ],
        help="""The actuation mode that can the feature will use.""",
    )

  def Run(self, args):
    feature = self.messages.Feature(
        spec=self.messages.CommonFeatureSpec(
            namespaceactuation=self.messages.NamespaceActuationFeatureSpec(
                actuationMode=self.messages.NamespaceActuationFeatureSpec.ActuationModeValueValuesEnum(
                    ModeEnumTranslation(args.actuation_mode)
                ),
            )
        )
    )
    self.Enable(feature)
