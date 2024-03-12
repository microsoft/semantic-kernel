# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""The gcloud code services group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.code import flags


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Code(base.Group):
  """Create and manage a local development environment for Cloud Run.

  This set of commands can be used create or change a local development
  setup.
  """
  category = base.SERVERLESS_CATEGORY

  detailed_help = {
      'EXAMPLES':
          """\
          To set up a local development environment, run:

            $ {command} dev
      """,
  }

  def Filter(self, context, args):
    # TODO(b/190528427):  Determine if command group works with project number
    base.RequireProjectID(args)
    flags.Validate(args)
    return context
