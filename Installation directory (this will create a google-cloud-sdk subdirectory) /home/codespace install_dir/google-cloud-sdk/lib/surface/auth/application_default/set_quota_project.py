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
"""Update or add a quota project in application default credentials json."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.auth import auth_util
from googlecloudsdk.command_lib.resource_manager import completers


class SetQuotaProject(base.SilentCommand):
  """Update or add a quota project in application default credentials (ADC).

  A quota project is a Google Cloud Project that will be used for billing
  and quota limits.

  Before running this command, an ADC must already be generated using
  $ gcloud auth application-default login.
  The quota project defined in the ADC will be used by the Google client
  libraries.
  The existing application default credentials must have the
  `serviceusage.services.use` permission on the given project.

  ## EXAMPLES

  To update the quota project in application default credentials to
  `my-quota-project`, run:

    $ {command} my-quota-project
  """

  @staticmethod
  def Args(parser):
    base.Argument(
        'quota_project_id',
        metavar='QUOTA_PROJECT_ID',
        completer=completers.ProjectCompleter,
        help='Quota project ID to add to application default credentials. If '
        'a quota project already exists, it will be updated.').AddToParser(
            parser)

  def Run(self, args):
    return auth_util.AddQuotaProjectToADC(args.quota_project_id)
