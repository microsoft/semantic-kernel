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
"""Get the Cloud Deploy config for the provided region."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import config
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import exceptions as deploy_exceptions
from googlecloudsdk.command_lib.deploy import resource_args


_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
    To get the config for project `test-project` in region `us-central1`:

       $ {command} --project=test-project --region=us-central1

  """,
}


def _CommonArgs(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  resource_args.AddLocationResourceArg(parser)


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class GetConfig(base.DescribeCommand):
  """Get the Cloud Deploy config for the provided region and project.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      deploy_exceptions.HTTP_ERROR_FORMAT
  )
  def Run(self, args):
    location_ref = args.CONCEPTS.region.Parse()
    project = location_ref.AsDict()['projectsId']
    region = location_ref.AsDict()['locationsId']
    config_client = config.ConfigClient()
    conf = config_client.GetConfig(project, region)
    return conf
