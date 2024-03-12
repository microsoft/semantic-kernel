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

"""Deletes a specific instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import instances_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a specified instance."""

  detailed_help = {
      'EXAMPLES': """\
          To delete instance i1 of service s1 and version v1, run:

            $ {command} i1 --service=s1 --version=v1
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'instance', help='The instance ID.')
    parser.add_argument(
        '--version', '-v', required=True, help='The version ID.')
    parser.add_argument(
        '--service', '-s', required=True, help='The service ID.')

  def Run(self, args):
    client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())
    instance = instances_util.Instance(args.service,
                                       args.version, args.instance)

    log.status.Print('Deleting the instance [{0}].'.format(instance))
    console_io.PromptContinue(cancel_on_no=True)
    res = resources.REGISTRY.Parse(
        args.instance,
        params={
            'appsId': properties.VALUES.core.project.GetOrFail,
            'servicesId': args.service,
            'versionsId': args.version,
            'instancesId': args.instance,
        },
        collection='appengine.apps.services.versions.instances')
    client.DeleteInstance(res)
    log.DeletedResource(res)
