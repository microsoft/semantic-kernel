# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Cancels a Cloud Deploy AutomationRun."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.clouddeploy import automation_run
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import exceptions as deploy_exceptions
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': textwrap.dedent("""\
     To cancel an AutomationRun `test-run` for delivery pipeline `test-pipeline`
     in region `us-central1`, run:

      $ {command} test-run --delivery-pipeline=test-pipeline
      --region=us-central1
      """),
}


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Cancel(base.CreateCommand):
  """Cancels a Cloud Deploy Automation Run."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddAutomationRunResourceArg(parser, positional=True)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      deploy_exceptions.HTTP_ERROR_FORMAT
  )
  def Run(self, args):
    automation_run_ref = args.CONCEPTS.automation_run.Parse()
    log.status.Print(
        'Cancelling automation run {}.\n'.format(
            automation_run_ref.RelativeName()
        )
    )

    return automation_run.AutomationRunsClient().Cancel(
        automation_run_ref.RelativeName()
    )
