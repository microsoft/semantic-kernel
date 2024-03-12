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

"""`gcloud app repair` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.core.console import progress_tracker


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Repair(base.Command):
  """Restores required App Engine features to the current application.

  For example, this command will restore the App Engine staging bucket if it
  has been deleted. It will no longer restore the service account, instead, the
  IAM service account undelete API must be used for the purpose.
  """

  detailed_help = {
      'EXAMPLES': """\
          To repair the application, run

              $ {command}
          """,
  }

  def Run(self, args):
    api_client = appengine_api_client.AppengineApiClient.GetApiClient('v1beta')

    with progress_tracker.ProgressTracker(
        'Repairing the app [{0}]'.format(api_client.project)):
      api_client.RepairApplication()



