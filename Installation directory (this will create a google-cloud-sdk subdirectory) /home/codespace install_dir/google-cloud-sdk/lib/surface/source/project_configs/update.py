# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""`gcloud source project-configs update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.source import project_configs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source import flags
from googlecloudsdk.command_lib.source import util


class Update(base.Command):
  r"""Update the Cloud Source Repositories configuration of the current project.

  ## EXAMPLES

  To enable PushBlock for all repositories under current project, run:

    $ {command} --enable-pushblock

  To associate a Cloud Pub/Sub topic to receive repository update notifications,
  run:

    $ {command} --add-topic=TOPIC_NAME --service-account=SERVICE_ACCOUNT_EMAIL \
        --message-format=json
  """

  _ENABLE_KEY_UPDATE_MASK = 'enablePrivateKeyCheck'
  _PUBSUB_CONFIGS_UPDATE_MASK = 'pubsubConfigs'

  @staticmethod
  def Args(parser):
    flags.AddProjectConfigUpdateArgs(parser)

  def Run(self, args):
    client = project_configs.ProjectConfig()
    if args.enable_pushblock or args.disable_pushblock:
      updated_project_config = util.ParseProjectConfigWithPushblock(args)
      return client.Update(updated_project_config, self._ENABLE_KEY_UPDATE_MASK)

    project_ref = util.CreateProjectResource(args)
    project_config = client.Get(project_ref)
    updated_project_config = util.ParseProjectConfigWithModifiedTopic(
        args, project_config)
    return client.Update(updated_project_config,
                         self._PUBSUB_CONFIGS_UPDATE_MASK)
