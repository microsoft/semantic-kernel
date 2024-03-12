# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""The `app instances enable-debug` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import env
from googlecloudsdk.api_lib.app import instances_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker


class EnableDebug(base.Command):
  """Enable debug mode for an instance (only works on the flexible environment).

  When in debug mode, SSH will be enabled on the VMs, and you can use
  `gcloud compute ssh` to login to them. They will be removed from the health
  checking pools, but they still receive requests.

  Note that any local changes to an instance will be *lost* if debug mode is
  disabled on the instance. New instance(s) may spawn depending on the app's
  scaling settings.

  Additionally, debug mode doesn't work for applications using the
  App Engine standard environment.
  """

  detailed_help = {
      'EXAMPLES': """\
          To enable debug mode for a particular instance, run:

              $ {command} --service=s1 --version=v1 i1

          To enable debug mode for an instance chosen interactively, run:

              $ {command}
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'instance', nargs='?',
        help="""\
        Instance ID to enable debug mode on. If not specified,
        select instance interactively. Must uniquely specify (with other
        flags) exactly one instance""")

    parser.add_argument(
        '--service', '-s',
        help="""\
        If specified, only match instances belonging to the given service.
        This affects both interactive and non-interactive selection.""")

    parser.add_argument(
        '--version', '-v',
        help="""\
        If specified, only match instances belonging to the given version.
        This affects both interactive and non-interactive selection.""")

  def Run(self, args):
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())
    all_instances = list(api_client.GetAllInstances(
        args.service, args.version,
        version_filter=lambda v: v.environment in [env.FLEX, env.MANAGED_VMS]))
    try:
      res = resources.REGISTRY.Parse(args.instance)
    except Exception:  # pylint:disable=broad-except
      # If parsing fails, use interactive selection or provided instance ID.
      instance = instances_util.GetMatchingInstance(
          all_instances, service=args.service, version=args.version,
          instance=args.instance)
    else:
      instance = instances_util.GetMatchingInstance(
          all_instances, service=res.servicesId, version=res.versionsId,
          instance=res.instancesId)

    console_io.PromptContinue(
        'About to enable debug mode for instance [{0}].'.format(instance),
        cancel_on_no=True)
    message = 'Enabling debug mode for instance [{0}]'.format(instance)
    res = resources.REGISTRY.Parse(
        instance.id,
        params={
            'appsId': properties.VALUES.core.project.GetOrFail,
            'versionsId': instance.version,
            'instancesId': instance.id,
            'servicesId': instance.service,
        },
        collection='appengine.apps.services.versions.instances')
    with progress_tracker.ProgressTracker(message):
      api_client.DebugInstance(res)
