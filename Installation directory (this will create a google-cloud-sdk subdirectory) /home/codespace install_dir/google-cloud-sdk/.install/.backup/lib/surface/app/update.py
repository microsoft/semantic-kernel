# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""The `app update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import update_util


_DETAILED_HELP = {
    'brief': ('Updates an App Engine application.'),
    'DESCRIPTION': """
        This command is used to update settings on an app engine application.

        """,
    'EXAMPLES': """
        To enable split health checks on an application:

          $ {command} --split-health-checks

        To update the app-level service account on an application:

          $ {command} --service-account=SERVICE_ACCOUNT
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGa(base.UpdateCommand):
  """Updates an App Engine application(GA version)."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    update_util.AddAppUpdateFlags(parser)

  def Run(self, args):
    update_util.PatchApplication(
        self.ReleaseTrack(),
        split_health_checks=args.split_health_checks,
        service_account=args.service_account)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class UpdateAlphaAndBeta(base.UpdateCommand):
  """Updates an App Engine application(Alpha and Beta version)."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    update_util.AddAppUpdateFlags(parser)

  def Run(self, args):
    update_util.PatchApplication(
        self.ReleaseTrack(),
        split_health_checks=args.split_health_checks,
        service_account=args.service_account)
