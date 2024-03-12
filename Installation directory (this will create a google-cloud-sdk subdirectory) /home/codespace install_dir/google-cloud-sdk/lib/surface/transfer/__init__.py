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
"""Cloud Transfer Service commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


DETAILED_HELP = {
    'DESCRIPTION':
        """\
        The gcloud transfer command group lets you create and manage
        Transfer Service jobs, operations, and agents.

        To get started, run:
        `gcloud transfer jobs create --help`

        More info on prerequisite IAM permissions:
        https://cloud.google.com/storage-transfer/docs/on-prem-set-up
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Transfer(base.Group):
  """Manage Transfer Service jobs, operations, and agents."""

  category = base.TRANSFER_CATEGORY

  detailed_help = DETAILED_HELP

  def Filter(self, context, args):
    # TODO(b/190541554):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
