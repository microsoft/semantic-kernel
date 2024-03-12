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

"""findings list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.web_security_scanner import wss_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.web_security_scanner import resource_args

HTTP_ERROR_FORMAT = (
    'ResponseError: code={status_code}, message={status_message}')


@wss_base.UseWebSecurityScannerApi(wss_base.WebSecurityScannerApiVersion.V1BETA)
class List(base.ListCommand, wss_base.WebSecurityScannerCommand):
  """List all the findings for a given scan run."""

  detailed_help = {
      'EXAMPLES':
          """\
          To list all the findings for a given scan run, run:

            $ {command} SCAN_RUN

          """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddScanRunResourceArg(parser)

  def Run(self, args):
    """Run 'list findings'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      All the scan findings for a given scan run

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    scan_run_ref = args.CONCEPTS.scan_run.Parse()
    try:
      # get all existing finding types via ListFindingTypeStats.
      list_finding_type_stats_response = \
        self.client.projects_scanConfigs_scanRuns_findingTypeStats.List(
            request=self.messages.
            WebsecurityscannerProjectsScanConfigsScanRunsFindingTypeStatsListRequest(
                parent=scan_run_ref.RelativeName()))

      finding_types = []
      for finding_type_stats in \
          list_finding_type_stats_response.findingTypeStats:
        finding_types.append(finding_type_stats.findingType)

      # get paged findings for each type
      all_findings = []
      for finding_type in finding_types:
        request = (
            self.messages
            .WebsecurityscannerProjectsScanConfigsScanRunsFindingsListRequest(
                parent=scan_run_ref.RelativeName(),
                filter='finding_type=' + finding_type))

        all_findings.append(
            list_pager.YieldFromList(
                self.client.projects_scanConfigs_scanRuns_findings,
                request,
                field='findings',
                batch_size_attribute=None))

      return [
          finding for finding in itertools.chain.from_iterable(all_findings)
      ]
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, HTTP_ERROR_FORMAT)
