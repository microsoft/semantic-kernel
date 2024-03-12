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

"""The configs variables get-value command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.runtime_config import base_commands
from googlecloudsdk.core import log


class GetValue(base_commands.VariableRetrieverCommand):
  """Output values of variable resources.

  This command prints only the value of the variable resource with the
  specified name, and does not append a trailing newline character.
  It can be used as part of shell expansions.
  """

  detailed_help = {
      'EXAMPLES': """\
          To print the value of a variable named "my-var", run:

            $ {command} --config-name=my-config my-var

          Values will be automatically base64-decoded.
          """,
  }

  def Display(self, args, variable):
    # Server guarantees that only one of those will be set.
    if variable.value:
      log.out.write(variable.value)
    else:
      log.out.write(variable.text)
