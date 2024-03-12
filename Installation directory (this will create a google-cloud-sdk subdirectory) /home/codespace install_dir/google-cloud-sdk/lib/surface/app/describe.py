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

"""The `app services describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import exceptions
from googlecloudsdk.core import log


_DETAILED_HELP = {
    'EXAMPLES': """\
        To show all the data about the current application, run

            $ {command}
        """,
}


def Describe(api_client):
  try:
    return api_client.GetApplication()
  except apitools_exceptions.HttpNotFoundError:
    log.debug('No app found:', exc_info=True)
    project = api_client.project
    raise exceptions.MissingApplicationError(project)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DescribeGA(base.Command):
  """Display all data about an existing service."""

  def Run(self, args):
    return Describe(appengine_api_client.GetApiClientForTrack(
        self.ReleaseTrack()))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(base.Command):
  """Display all data about an existing service using the beta API."""

  def Run(self, args):
    return Describe(appengine_api_client.GetApiClientForTrack(
        self.ReleaseTrack()))


DescribeGA.detailed_help = _DETAILED_HELP
DescribeBeta.detailed_help = _DETAILED_HELP
