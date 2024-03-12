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
"""The gcloud run group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


DETAILED_HELP = {
    'brief': 'Manage your Cloud Run applications.',
    'DESCRIPTION': """
        The gcloud run command group lets you deploy container images
        to Google Cloud Run.
        """,
    'EXAMPLES': """
        To deploy your container, use the `gcloud run deploy` command:

          $ gcloud run deploy <service-name> --image <image_name>

        For more information, run:
          $ gcloud run deploy --help
        """
}


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA)
class Serverless(base.Group):
  """Manage your Cloud Run resources."""
  category = base.COMPUTE_CATEGORY
  detailed_help = DETAILED_HELP

  def Filter(self, context, args):
    """Runs before any commands in this group."""
    # TODO(b/190539410):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
