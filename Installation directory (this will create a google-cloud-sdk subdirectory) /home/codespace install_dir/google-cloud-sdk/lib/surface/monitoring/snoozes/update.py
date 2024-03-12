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
"""`gcloud monitoring snoozes update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import snoozes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import flags
from googlecloudsdk.command_lib.monitoring import resource_args
from googlecloudsdk.command_lib.monitoring import util
from googlecloudsdk.core import log


class Update(base.UpdateCommand):
  """Updates a snooze."""

  detailed_help = {
      'DESCRIPTION': """\
          Update a snooze.

          If `--snooze-from-file` is specified, then the update rules depend on
          the value of the (optional) `--fields` flag:

            * If `--fields` is specified, then only the specified fields of the
              snooze are updated.
            * Else, all fields of the snooze are replaced. The updated snooze
              can be modified further using the flags from the Snooze
              Settings group below.

          Otherwise, the snooze will be updated with the values specified in
          the flags from the Snooze Settings group.

          For information about the JSON/YAML format of a snooze:
          https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.snoozes
       """,
      'EXAMPLES': """\
          To update a snooze time interval with command-line options, run:

            $ {command} MY-SNOOZE --start-time=START_TIME --end-time=END_TIME

          To update a snooze display name with a file, run:

            $ {command} --snooze-from-file=MY-FILE --fields=display_name

          Sample contents of MY-FILE:

            criteria:
              policies:
              - projects/MY-PROJECT/alertPolicies/MY-POLICY
            interval:
              startTime: '2024-03-01T08:00:00Z'
              endTime: '2024-03-08T04:59:59.500Z'
            displayName: New Snooze with New Display Name
       """
  }

  @staticmethod
  def Args(parser):
    resources = [
        resource_args.CreateSnoozeResourceArg('to be updated.')]
    resource_args.AddResourceArgs(parser, resources)
    flags.AddFileMessageFlag(parser, 'snooze')
    flags.AddFieldsFlagsWithMutuallyExclusiveSettings(
        parser,
        fields_help=('The list of fields to update. Must specify '
                     '`--snooze-from-file` if using this flag.'),
        add_settings_func=flags.AddSnoozeSettingsFlags,
        update=True)

  def Run(self, args):
    util.ValidateUpdateArgsSpecified(
        args,
        ['snooze_from_file', 'display_name',
         'start_time', 'end_time', 'fields'],
        'snooze')
    flags.ValidateSnoozeUpdateArgs(args)

    client = snoozes.SnoozeClient()
    messages = client.messages

    passed_yaml_snooze = False
    snooze_ref = args.CONCEPTS.snooze.Parse()
    if args.snooze_from_file:
      passed_yaml_snooze = True
      snooze = util.GetBaseSnoozeMessageFromArgs(
          args, messages.Snooze, update=True
      )
    else:
      # If a full snooze isn't given, we want to do Read-Modify-Write.
      # TODO(b/271427290): Replace 500 with 404 in api
      snooze = client.Get(snooze_ref)
      # And validate that the snooze reference is not Past/Canceled.
      flags.ValidateSnoozeInterval(
          snooze,
          display_name=args.display_name,
          start_time=args.start_time,
          end_time=args.end_time,
      )

    if not args.fields:
      fields = []
      util.ModifySnooze(
          snooze,
          messages,
          display_name=args.display_name,
          start_time=args.start_time,
          end_time=args.end_time,
          field_masks=fields)

      # For more robust concurrent updates, use update masks if we're not
      # trying to replace the snooze using --snooze-from-file.
      fields = None if passed_yaml_snooze else ','.join(sorted(fields))
    else:
      fields = ','.join(args.fields)

    result = client.Update(snooze_ref, snooze, fields)
    log.UpdatedResource(result.name, 'snooze')
    return result
