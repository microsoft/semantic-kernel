# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""The main command group for cloud dataproc."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base

# TODO(b/62883827): Move this into the docstring along with other places
# where this pattern currently occurs.
DETAILED_HELP = {
    'DESCRIPTION': """\
        The gcloud dataproc command group lets you create and manage Dataproc
        clusters and jobs.

        Dataproc is an Apache Hadoop, Apache Spark, Apache Pig, and Apache
        Hive service. It easily processes big datasets at low cost, creating
        managed clusters of any size that scale down once processing is
        complete.

        More information on Dataproc can be found here:
        https://cloud.google.com/dataproc and detailed documentation can be
        found here: https://cloud.google.com/dataproc/docs/

        ## EXAMPLES

        To see how to create and manage clusters, run:

            $ {command} clusters

        To see how to submit and manage jobs, run:

            $ {command} jobs
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Dataproc(base.Group):
  """Create and manage Google Cloud Dataproc clusters and jobs."""

  category = base.DATA_ANALYTICS_CATEGORY

  detailed_help = DETAILED_HELP

  def Filter(self, context, args):
    # TODO(b/190530371):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
    base.DisableUserProjectQuota()

    self.EnableSelfSignedJwtForTracks(
        [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]
    )
