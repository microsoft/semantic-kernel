# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""The gcloud kuberun group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class KubeRun(base.Group):
  """Top level command to interact with KubeRun.

  Use this set of commands to create and manage KubeRun resources
  and some related project settings.
  """
  category = base.COMPUTE_CATEGORY

  detailed_help = {
      'EXAMPLES':
          """\
          To list your KubeRun services, run:

            $ {command} core services list
      """,
  }

  def Filter(self, context, args):
    """Runs before any commands in this group."""
    # TODO(b/190535898):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
