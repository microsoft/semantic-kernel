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
"""`gcloud monitoring uptime create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import uptime
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import flags
from googlecloudsdk.command_lib.monitoring import resource_args
from googlecloudsdk.command_lib.monitoring import util
from googlecloudsdk.command_lib.util.args import repeated
from googlecloudsdk.core import log


class Update(base.UpdateCommand):
  """Update an existing uptime check or synthetic monitor."""

  detailed_help = {
      'DESCRIPTION': """\
          Updates an existing uptime check or synthetic monitor.

          Flags only apply to uptime checks unless noted that they apply to
          synthetic monitors.

          For information about the JSON/YAML format of an uptime check:
          https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.uptimeCheckConfigs
       """,
      'EXAMPLES': """\
          To update an uptime check or synthetic monitor, run:

          $ {command} CHECK_ID --period=5 --timeout=30
       """,}

  @staticmethod
  def Args(parser):
    resources = [resource_args.CreateUptimeResourceArg('to be updated.')]
    resource_args.AddResourceArgs(parser, resources)
    flags.AddUptimeSettingsFlags(parser, update=True)

  def Run(self, args):
    client = uptime.UptimeClient()
    uptime_check_ref = args.CONCEPTS.check_id.Parse()
    uptime_check = client.Get(uptime_check_ref)

    new_user_labels = util.ProcessUpdateLabels(
        args,
        'user_labels',
        client.messages.UptimeCheckConfig.UserLabelsValue,
        uptime_check.userLabels,
    )

    new_headers = None
    regions = ParseSelectedRegions(uptime_check.selectedRegions)
    new_regions = repeated.ParsePrimitiveArgs(args, 'regions', lambda: regions)
    status_codes = []
    new_status_codes = []
    status_classes = []
    new_status_classes = []
    if uptime_check.httpCheck is not None:
      new_headers = util.ProcessUpdateLabels(
          args,
          'headers',
          client.messages.HttpCheck.HeadersValue,
          uptime_check.httpCheck.headers,
      )
      for status in uptime_check.httpCheck.acceptedResponseStatusCodes:
        if status.statusClass is not None:
          status_classes.append(status.statusClass)
        else:
          status_codes.append(status.statusValue)
      new_status_codes = repeated.ParsePrimitiveArgs(
          args, 'status_codes', lambda: status_codes
      )
      status_classes = ParseStatusClasses(status_classes)
      new_status_classes = repeated.ParsePrimitiveArgs(
          args, 'status_classes', lambda: status_classes
      )

    util.ModifyUptimeCheck(
        uptime_check,
        client.messages,
        args,
        regions=new_regions,
        user_labels=new_user_labels,
        headers=new_headers,
        status_classes=new_status_classes,
        status_codes=new_status_codes,
        update=True
    )
    # Full replace, no fields_mask
    result = client.Update(uptime_check_ref, uptime_check, fields=None)
    log.UpdatedResource(result.name, 'uptime')
    return result


def ParseSelectedRegions(selected_regions):
  """Convert previously selected regions from enum to flag for update logic."""
  client = uptime.UptimeClient()
  messages = client.messages
  region_mapping = {
      messages.UptimeCheckConfig.SelectedRegionsValueListEntryValuesEnum.USA_OREGON: (
          'usa-oregon'
      ),
      messages.UptimeCheckConfig.SelectedRegionsValueListEntryValuesEnum.USA_IOWA: (
          'usa-iowa'
      ),
      messages.UptimeCheckConfig.SelectedRegionsValueListEntryValuesEnum.USA_VIRGINIA: (
          'usa-virginia'
      ),
      messages.UptimeCheckConfig.SelectedRegionsValueListEntryValuesEnum.EUROPE: (
          'europe'
      ),
      messages.UptimeCheckConfig.SelectedRegionsValueListEntryValuesEnum.SOUTH_AMERICA: (
          'south-america'
      ),
      messages.UptimeCheckConfig.SelectedRegionsValueListEntryValuesEnum.ASIA_PACIFIC: (
          'asia-pacific'
      ),
  }
  return [region_mapping.get(region) for region in selected_regions]


def ParseStatusClasses(status_classes):
  """Convert previously status classes from enum to flag for update logic."""
  client = uptime.UptimeClient()
  messages = client.messages
  status_mapping = {
      messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_1XX: (
          '1xx'
      ),
      messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_2XX: (
          '2xx'
      ),
      messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_3XX: (
          '3xx'
      ),
      messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_4XX: (
          '4xx'
      ),
      messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_5XX: (
          '5xx'
      ),
      messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_ANY: (
          'any'
      ),
  }
  return [status_mapping.get(status_class) for status_class in status_classes]
