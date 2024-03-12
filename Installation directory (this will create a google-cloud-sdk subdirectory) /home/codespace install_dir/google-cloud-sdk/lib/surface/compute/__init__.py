# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""The super-group for the compute CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import transforms
from googlecloudsdk.calliope import base


DETAILED_HELP = {
    'DESCRIPTION': """
        The gcloud compute command group lets you create, configure, and
        manipulate Compute Engine virtual machine (VM) instances.

        With Compute Engine, you can create and run VMs
        on Google's infrastructure. Compute Engine offers scale, performance,
        and value that lets you launch large compute clusters on
        Google's infrastructure.

        For more information about Compute Engine, see the
        [Compute Engine overview](https://cloud.google.com/compute/)
        and the
        [Compute Engine user documentation](https://cloud.google.com/compute/docs/).
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Compute(base.Group):
  """Create and manipulate Compute Engine resources."""
  detailed_help = DETAILED_HELP

  category = base.COMPUTE_CATEGORY

  @staticmethod
  def Args(parser):
    parser.display_info.AddTransforms(transforms.GetTransforms())

  def Filter(self, context, args):
    # TODO(b/190528962):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
    base.DisableUserProjectQuota()

    self.EnableSelfSignedJwtForTracks(
        [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]
    )
