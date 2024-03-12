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
"""Run the web UI assistant for schema migrations."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.command_lib.spanner import migration_backend


class Web(base.BinaryBackedCommand):
  """Run the web UI assistant for schema migrations."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To run the web UI assistant:

          $ {command}
      """),
  }

  @staticmethod
  def Args(parser):
    """Register the flags for this command."""
    flags.GetSpannerMigrationWebPortFlag().AddToParser(parser)
    flags.GetSpannerMigrationWebOpenFlag().AddToParser(parser)

  def Run(self, args):
    """Run the web UI assistant."""
    command_executor = migration_backend.SpannerMigrationWrapper()
    env_vars = migration_backend.GetEnvArgsForCommand(
        extra_vars={'GCLOUD_HB_PLUGIN': 'true'})
    response = command_executor(
        command='web',
        open_flag=args.open,
        port=args.port,
        env=env_vars,
    )
    self.exit_code = response.exit_code
    return self._DefaultOperationResponseHandler(response)
