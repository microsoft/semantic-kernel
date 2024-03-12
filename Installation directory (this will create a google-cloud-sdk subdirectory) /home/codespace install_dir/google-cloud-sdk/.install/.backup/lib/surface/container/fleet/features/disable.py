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
"""Generic command to disable any fleet feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.container.fleet.features import base


@calliope_base.Hidden
class Disable(base.DisableCommand):
  """Disable a fleet feature.

  ## EXAMPLES

  To disable the `servicemesh` feature, run:

    $ {command} servicemesh
  """

  @staticmethod
  def Args(parser):
    base.DisableCommand.Args(parser)
    parser.add_argument(
        'feature',
        help='Short name of the feature to disable.',
    )

  def Run(self, args):
    self.feature_name = args.feature
    self.Disable(args.force)
