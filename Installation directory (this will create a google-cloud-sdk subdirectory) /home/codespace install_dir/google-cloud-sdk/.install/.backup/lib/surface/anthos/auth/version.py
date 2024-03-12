# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Authenticate clusters using the Anthos client.."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.anthos import anthoscli_backend


@base.Hidden
class Version(base.BinaryBackedCommand):
  """Get version info for the Anthos Auth client."""

  detailed_help = {
      'EXAMPLES': """
      To display version info:

          $ {command}
            """,
  }

  def Run(self, args):
    command_executor = anthoscli_backend.AnthosAuthWrapper()
    response = command_executor(
        command='version',
        show_exec_error=args.show_exec_error,
        env=anthoscli_backend.GetEnvArgsForCommand())
    return self._DefaultOperationResponseHandler(response)
