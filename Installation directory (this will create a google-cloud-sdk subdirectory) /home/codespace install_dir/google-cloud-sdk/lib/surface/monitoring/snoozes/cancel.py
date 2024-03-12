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
"""`gcloud monitoring snoozes cancel` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import snoozes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import resource_args
from googlecloudsdk.command_lib.monitoring import util
from googlecloudsdk.core import log
from googlecloudsdk.core.util import times


class Cancel(base.UpdateCommand):
  """Cancels a snooze."""

  detailed_help = {
      'DESCRIPTION': """\
          Cancel a snooze.

          If the start time is in the future, then
          this command is equivalent to:

            * update --start-time="+PT1S" --end-time="+PT1S

          Otherwise, if the start time is past and the ending time is in the
          future, then this command is equivalent to:

            * update --end-time="+PT1S

          For information about the JSON/YAML format of a snooze:
          https://cloud.google.com/monitoring/api/ref_v3/rest/v3/projects.snoozes
       """,
      'EXAMPLES': """\
          To cancel a snooze, run:

            $ {command} MY-SNOOZE

          To cancel a snooze contained within a specific project, run:

            $ {command} MY-SNOOZE --project=MY-PROJECT

          To cancel a snooze with a fully qualified snooze ID, run:

            $ {command} projects/MY-PROJECT/snoozes/MY-SNOOZE
       """
  }

  @staticmethod
  def Args(parser):
    resources = [
        resource_args.CreateSnoozeResourceArg('to be canceled.')]
    resource_args.AddResourceArgs(parser, resources)

  def Run(self, args):
    client = snoozes.SnoozeClient()
    messages = client.messages

    snooze_ref = args.CONCEPTS.snooze.Parse()

    # TODO(b/271427290): Replace 500 with 404 in api
    snooze = client.Get(snooze_ref)

    start_time = times.ParseDateTime(snooze.interval.startTime)
    end_time = times.ParseDateTime('+PT1S')
    if start_time > times.Now():
      start_time = end_time

    util.ModifySnooze(
        snooze,
        messages,
        start_time=start_time,
        end_time=end_time)

    result = client.Update(snooze_ref, snooze, None)
    log.UpdatedResource(result.name, 'snooze')
    return result
