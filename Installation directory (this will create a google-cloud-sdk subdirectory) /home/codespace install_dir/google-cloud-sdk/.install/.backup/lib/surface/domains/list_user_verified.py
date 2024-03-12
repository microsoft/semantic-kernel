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
"""The `domains list-user-verified` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.app.api import appengine_domains_api_client as api_client
from googlecloudsdk.api_lib.run import global_methods as run_methods
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class ListUserVerified(base.Command):
  """Lists the user's verified domains."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To list domains that have been verified by the current user, run:

            $ {command}

          Use the {parent_command} verify command to verify additional
          domains.
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('table(id:sort=1)')

  def Run(self, args):
    try:
      project = properties.VALUES.core.project.Get()
      client = api_client.GetApiClientForTrack(self.ReleaseTrack())
      return client.ListVerifiedDomains()
    # Note: the domain user-verified listing API is availible through two
    # routes, one App Engine and one Cloud Run. The command should work if the
    # user has *either* API activated. The following falls back to Cloud Run
    # if the user does not have App Engine activated.
    except (apitools_exceptions.HttpNotFoundError,
            apitools_exceptions.HttpForbiddenError) as appengine_err:
      try:
        run_client = run_methods.GetServerlessClientInstance()
        return run_methods.ListVerifiedDomains(run_client)
      except (apitools_exceptions.HttpNotFoundError,
              apitools_exceptions.HttpForbiddenError):
        log.error('To list user-verified domains, you must activate either'
                  ' the App Engine or Cloud Run API and have read permissions '
                  'on one of them.')
        log.error('To activate App Engine, visit:')
        log.error('https://console.cloud.google.com/apis/api/'
                  'appengine.googleapis.com/overview?project={}'.format(
                      project))
        log.error('To activate Cloud Run, visit:')
        log.error('https://console.cloud.google.com/apis/api/'
                  'run.googleapis.com/overview?project={}'.format(project))
        raise appengine_err
