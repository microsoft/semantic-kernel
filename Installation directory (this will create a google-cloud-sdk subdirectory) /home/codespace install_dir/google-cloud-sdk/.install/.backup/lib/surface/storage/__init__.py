# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Cloud Storage commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import metrics_util


DETAILED_HELP = {
    'DESCRIPTION': """\
        The gcloud storage command group lets you create and manage
        Cloud Storage resources such as buckets and objects.

        More information on Cloud Storage can be found here:
        https://cloud.google.com/storage, and detailed documentation can be
        found here: https://cloud.google.com/storage/docs/
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Storage(base.Group):
  """Create and manage Cloud Storage buckets and objects."""

  category = base.STORAGE_CATEGORY

  detailed_help = DETAILED_HELP

  def __init__(self):
    super(Storage, self).__init__()
    metrics_util.fix_user_agent_for_gsutil_shim()

  def Filter(self, context, args):
    # TODO(b/190541521):  Determine if command group works with project number
    base.RequireProjectID(args)
    # gsutil does not keep the user project quota enabled by default. Hence
    # we will be keeping it disabled in gcloud storage as well to ensure parity.
    # See b/258687686#comment5 for more information.
    base.DisableUserProjectQuota()
    del context, args

    # Enable self signed jwt for alpha track
    self.EnableSelfSignedJwtForTracks([base.ReleaseTrack.ALPHA])
