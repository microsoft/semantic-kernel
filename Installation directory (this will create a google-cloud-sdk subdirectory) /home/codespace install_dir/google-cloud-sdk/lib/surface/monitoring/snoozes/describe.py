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
"""`gcloud monitoring snoozes describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.monitoring import snoozes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.monitoring import resource_args


class Describe(base.DescribeCommand):
  """Describe a snooze."""

  detailed_help = {
      'EXAMPLES': """\
          To describe a snooze, run:

            $ {command} MY-SNOOZE

          To describe a snooze in JSON, run:

            $ {command} MY-SNOOZE --format=json

          To describe a snooze contained within a specific project, run:

            $ {command} MY-SNOOZE --project=MY-PROJECT

          To describe a snooze with a fully qualified snooze ID, run:

            $ {command} projects/MY-PROJECT/snoozes/MY-SNOOZE
       """
  }

  @staticmethod
  def Args(parser):
    resources = [
        resource_args.CreateSnoozeResourceArg('to be described.')]
    resource_args.AddResourceArgs(parser, resources)

  def Run(self, args):
    client = snoozes.SnoozeClient()
    snooze_ref = args.CONCEPTS.snooze.Parse()

  # TODO(b/271427290): Replace 500 with 404 in api
    result = client.Get(snooze_ref)
    return result
