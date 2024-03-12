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
"""Surface for deleting a firewall rule."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app.api import appengine_firewall_api_client as api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.app import firewall_rules_util
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Deletes a specified firewall rule."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To delete an App Engine firewall rule, run:

            $ {command} 1234
          """,
  }

  @staticmethod
  def Args(parser):
    flags.FIREWALL_PRIORITY_FLAG.AddToParser(parser)

  def Run(self, args):
    priority = firewall_rules_util.ParsePriority(args.priority)
    if priority == firewall_rules_util.DEFAULT_RULE_PRIORITY:
      raise exceptions.InvalidArgumentException(
          'priority', 'The `default` can not be deleted, only updated.')

    console_io.PromptContinue(
        prompt_string='You are about to delete rule [{0}].'.format(priority),
        cancel_on_no=True)

    client = api_client.GetApiClientForTrack(self.ReleaseTrack())
    resource = firewall_rules_util.ParseFirewallRule(client, priority)
    client.Delete(resource)

    log.DeletedResource(priority)
