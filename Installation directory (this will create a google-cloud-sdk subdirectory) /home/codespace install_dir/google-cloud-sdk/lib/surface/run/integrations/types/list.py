# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command for listing Cloud Run Integration types."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run.integrations import run_apps_operations


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """Lists Cloud Run Integration Types."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To list all integration types

              $ {command}

         """,
  }

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    parser.display_info.AddFormat(
        'table('
        'integration_type:label="TYPE",'
        'description:label=DESCRIPTION)')

  def Run(self, args):
    """List integration types."""
    release_track = self.ReleaseTrack()
    with run_apps_operations.Connect(args, release_track) as client:
      # Output is sorted by the integration name to guarantee the same ordering
      # for scenario tests.
      result = sorted(client.ListIntegrationTypes(),
                      key=lambda t: t.integration_type)
      return list(result)
