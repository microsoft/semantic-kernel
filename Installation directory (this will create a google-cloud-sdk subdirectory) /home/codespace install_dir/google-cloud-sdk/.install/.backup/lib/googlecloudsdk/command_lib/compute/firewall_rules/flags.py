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
"""Flags and helpers for the compute firewall-rules commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util.apis import arg_utils

# Needs to be indented to show up correctly in help text
LIST_WITH_ALL_FIELDS_FORMAT = """\
table(
                    name,
                    network,
                    direction,
                    priority,
                    sourceRanges.list():label=SRC_RANGES,
                    destinationRanges.list():label=DEST_RANGES,
                    allowed[].map().firewall_rule().list():label=ALLOW,
                    denied[].map().firewall_rule().list():label=DENY,
                    sourceTags.list():label=SRC_TAGS,
                    sourceServiceAccounts.list():label=SRC_SVC_ACCT,
                    targetTags.list():label=TARGET_TAGS,
                    targetServiceAccounts.list():label=TARGET_SVC_ACCT,
                    disabled
                )"""

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      network.basename(),
      direction,
      priority,
      allowed[].map().firewall_rule().list():label=ALLOW,
      denied[].map().firewall_rule().list():label=DENY,
      disabled
    )"""

LIST_NOTICE = """\
To show all fields of the firewall, please show in JSON format: --format=json
To show all fields in table format, please see the examples in --help.
"""


class FirewallsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(FirewallsCompleter, self).__init__(
        collection='compute.firewalls',
        list_command='compute firewall-rules list --uri',
        **kwargs)


def FirewallRuleArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='firewall rule',
      completer=FirewallsCompleter,
      plural=plural,
      required=required,
      global_collection='compute.firewalls')


def AddEnableLogging(parser):
  parser.add_argument(
      '--enable-logging',
      action=arg_parsers.StoreTrueFalseAction,
      help="""\
      Enable logging for the firewall rule. Logs will be exported to
      StackDriver. Firewall logging is disabled by default. To enable logging
      for an existing rule, run:

        $ {command} MY-RULE --enable-logging

      To disable logging on an existing rule, run:

        $ {command} MY-RULE --no-enable-logging
      """)


def GetLoggingMetadataArg(messages):
  return arg_utils.ChoiceEnumMapper(
      '--logging-metadata',
      messages.FirewallLogConfig.MetadataValueValuesEnum,
      custom_mappings={
          'INCLUDE_ALL_METADATA': 'include-all',
          'EXCLUDE_ALL_METADATA': 'exclude-all'
      },
      help_str=('Adds or removes metadata fields to or from the reported '
                'firewall logs. Can only be specified if --enable-logging is '
                'true.'))


def AddLoggingMetadata(parser, messages):
  GetLoggingMetadataArg(messages).choice_arg.AddToParser(parser)
