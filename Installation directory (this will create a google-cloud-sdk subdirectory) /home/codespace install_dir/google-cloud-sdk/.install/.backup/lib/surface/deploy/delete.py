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
"""Deletes(n >= 0) Delivery Pipeline(s), Target(s), Custom Target Type(s), and Automation(s) with current project's Cloud Deploy service.."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import deploy
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import exceptions as deploy_exceptions
from googlecloudsdk.command_lib.deploy import flags
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.core import yaml

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
    To delete the resources in a Cloud Deploy YAML file `deploy.yaml`:

       $ {command} --file=deploy.yaml --region=us-central1

  """,
}


def _CommonArgs(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  flags.AddConfigFile(parser)
  flags.AddForce(
      parser, 'If true, the delivery pipeline and '
      'its sub-resources (releases and rollouts) are deleted.')
  resource_args.AddLocationResourceArg(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.UpdateCommand):
  """Deletes Delivery Pipeline(s), Target(s), Custom Target Type(s), and Automation(s) in a yaml configuration."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      deploy_exceptions.HTTP_ERROR_FORMAT
  )
  def Run(self, args):
    """This is what gets called when the user runs this command."""
    loaded_yaml = list(yaml.load_all_path(args.file))
    deploy_client = deploy.DeployClient()
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']

    deploy_client.DeleteResources(loaded_yaml, region, args.force)
