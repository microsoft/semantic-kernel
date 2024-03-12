# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""The super-group for the AlloyDB CLI.

The fact that this is a directory with
an __init__.py in it makes it a command group. The methods written below will
all be called by calliope (though they are all optional).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'DESCRIPTION': """
        The gcloud alloydb command group lets you create and manage Google Cloud AlloyDB
        databases.

        AlloyDB is a fully-managed database service that makes it easy to set
        up, maintain, manage, and administer your Alloydb databases in
        the cloud.

        More information on AlloyDB can be found at https://cloud.google.com/alloydb
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class AlloyDB(base.Group):
  """Create and manage AlloyDB databases."""

  category = base.DATABASES_CATEGORY

  detailed_help = DETAILED_HELP

  def Filter(self, context, args):
    # TODO(b/190524014):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
    base.DisableUserProjectQuota()
