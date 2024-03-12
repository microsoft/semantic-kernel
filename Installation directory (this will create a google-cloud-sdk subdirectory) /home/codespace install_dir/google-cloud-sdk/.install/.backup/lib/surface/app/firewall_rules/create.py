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
"""Surface for creating a firewall rule."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app.api import appengine_firewall_api_client as api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.app import firewall_rules_util
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.core import log


class Create(base.CreateCommand):
  """Creates a firewall rule."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To create a new App Engine firewall rule, run:

              $ {command} 1234
                --source-range='2001:db8::/32'
                --action=deny
                --description='block traffic from the example range.'
          """,
  }

  @staticmethod
  def Args(parser):
    flags.FIREWALL_PRIORITY_FLAG.AddToParser(parser)
    flags.AddFirewallRulesFlags(parser, required=True)

  def Run(self, args):
    client = api_client.GetApiClientForTrack(self.ReleaseTrack())
    priority = firewall_rules_util.ParsePriority(args.priority)

    if priority == firewall_rules_util.DEFAULT_RULE_PRIORITY:
      raise exceptions.InvalidArgumentException(
          'priority', 'The `default` can not be created, only updated.')

    action = firewall_rules_util.ParseAction(client.messages, args.action)

    rule = client.Create(priority, args.source_range, action, args.description)
    log.CreatedResource(args.priority)
    return rule
