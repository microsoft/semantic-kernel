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

"""Shared flags definitions for finding commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from apitools.base.py import encoding
from googlecloudsdk.api_lib.scc import securitycenter_client as sc_client
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import errors
from googlecloudsdk.command_lib.util.args import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties

# TODO: b/312478509 - Add Deprecation warning for compare-duration.
COMPARE_DURATION_FLAG = base.Argument(
    '--compare-duration',
    help="""
      When compare_duration is set, the result's "state_change" attribute is
      updated to indicate whether the finding had its state changed, the
      finding's state remained unchanged, or if the finding was added during
      the compare_duration period of time that precedes the read_time. This
      is the time between (read_time - compare_duration) and read_time. The
      state_change value is derived based on the presence and state of the
      finding at the two points in time. Intermediate state changes between
      the two times don't affect the result. For example, the results aren't
      affected if the finding is made inactive and then active again.
      Possible "state_change" values when compare_duration is specified:

      * 'CHANGED': indicates that the finding was present at the start of
        compare_duration, but changed its state at read_time.

      * 'UNCHANGED': indicates that the finding was present at the start of
        compare_duration and did not change state at read_time.

      * 'ADDED': indicates that the finding was not present at the start of
        compare_duration, but was present at read_time.

      * 'REMOVED': indicates that the finding was present at the start of
        compare_duration, but was not present at read_time.

      If compare_duration is not specified, then the only possible
      state_change is 'UNUSED', which will be the state_change set for all
      findings present at read_time. If this field is set then 'state_change'
      must be a specified field in 'group_by'. See $ gcloud topic datetimes
      for information on supported duration formats.""",
)

EVENT_TIME_FLAG_NOT_REQUIRED = base.Argument(
    '--event-time',
    help="""Time at which the event took place. For example, if the finding
  represents an open firewall it would capture the time the open firewall
  was detected. If event-time is not provided, it will default to UTC
  version of NOW. See `$ gcloud topic datetimes` for information on
  supported time formats.""",
    required=False,
)


EVENT_TIME_FLAG_REQUIRED = base.Argument(
    '--event-time',
    help="""Time at which the event took place. For example, if the finding
  represents an open firewall it would capture the time the open firewall
  was detected. If event-time is not provided, it will default to UTC
  version of NOW. See `$ gcloud topic datetimes` for information on
  supported time formats.""",
    required=True,
)


EXTERNAL_URI_FLAG = base.Argument(
    '--external-uri',
    help="""URI that, if available, points to a web page outside of Cloud SCC (Security Command Center)
    where additional information about the finding can be found. This field is guaranteed to be
    either empty or a well formed URL.""",
)


SOURCE_FLAG = base.Argument(
    '--source', help='Source id. Defaults to all sources.', default='-'
)


SOURCE_PROPERTIES_FLAG = base.Argument(
    '--source-properties',
    help="""Source specific properties. These properties are managed by the
      source that writes the finding. The key names in the source_properties map
      must be between 1 and 255 characters, and must start with a letter and
      contain alphanumeric characters or underscores only. For example
      "key1=val1,key2=val2" """,
    metavar='KEY=VALUE',
    type=arg_parsers.ArgDict(),
)


STATE_FLAG = base.ChoiceArgument(
    '--state',
    help_str='State is one of: [ACTIVE, INACTIVE].',
    choices=['active', 'inactive', 'state-unspecified'],
)


def CreateFindingArg():
  """Create finding as positional resource."""
  finding_spec_data = {
      'name': 'finding',
      'collection': 'securitycenter.organizations.sources.findings',
      'attributes': [
          {
              'parameter_name': 'organizationsId',
              'attribute_name': 'organization',
              'help': """(Optional) If the full resource name isn't provided e.g. organizations/123, then provide the
              organization id which is the suffix of the organization. Example: organizations/123, the id is
              123.""",
              'fallthroughs': [{
                  'hook': 'googlecloudsdk.command_lib.scc.findings.flags:GetDefaultOrganization',
                  'hint': """Set the organization property in configuration using `gcloud config set scc/organization`
                  if it is not specified in command line.""",
              }],
          },
          {
              'parameter_name': 'sourcesId',
              'attribute_name': 'source',
              'help': """(Optional) If the full resource name isn't provided e.g. organizations/123/sources/456, then
              provide the source id which is the suffix of the source.
              Example: organizations/123/sources/456, the id is 456.""",
          },
          {
              'parameter_name': 'findingId',
              'attribute_name': 'finding',
              'help': """Optional) If the full resource name isn't provided e.g.
              organizations/123/sources/456/findings/789, then provide the finding id which is the suffix of
              the finding. Example: organizations/123/sources/456/findings/789, the id is 789.""",
          },
      ],
      'disable_auto_completers': 'false',
  }
  arg_specs = [
      resource_args.GetResourcePresentationSpec(
          verb='to be used for the SCC (Security Command Center) command',
          name='finding',
          required=True,
          prefixes=False,
          positional=True,
          resource_data=finding_spec_data,
      ),
  ]
  return concept_parsers.ConceptParser(arg_specs, [])


def GetDefaultOrganization():
  """Prepend organizations/ to org if necessary."""
  resource_pattern = re.compile('organizations/[0-9]+')
  id_pattern = re.compile('[0-9]+')
  organization = properties.VALUES.scc.organization.Get()
  if not resource_pattern.match(organization) and not id_pattern.match(
      organization
  ):
    raise errors.InvalidSCCInputError(
        'Organization must match either organizations/[0-9]+ or [0-9]+.'
    )
  if resource_pattern.match(organization):
    return organization
  return 'organizations/' + organization


def ConvertSourceProperties(source_properties_dict):
  """Hook to capture "key1=val1,key2=val2" as SourceProperties object."""
  messages = sc_client.GetMessages()
  return encoding.DictToMessage(
      source_properties_dict, messages.Finding.SourcePropertiesValue
  )
