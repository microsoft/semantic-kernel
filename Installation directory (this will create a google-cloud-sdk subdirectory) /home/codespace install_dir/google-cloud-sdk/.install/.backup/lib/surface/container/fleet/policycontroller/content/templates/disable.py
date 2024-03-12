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
"""Disables content template library for Policy Controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import command
from googlecloudsdk.command_lib.container.fleet.policycontroller import content


class Disable(base.UpdateCommand, command.PocoCommand):
  """Disable template installation for Policy Controller content.

  The Google-defined template library can be installed onto Policy Controller
  installations. This command removes that template library.

  ## EXAMPLES

  To remove the template library:

    $ {command}
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    cmd_flags = content.Flags(parser, 'enable')
    cmd_flags.add_memberships()

  def Run(self, args):
    parser = content.FlagParser(args, self.messages)
    specs = self.path_specs(args, True)
    updated_specs = {
        path: parser.uninstall_template_library(poco_cfg)
        for path, poco_cfg in specs.items()
    }
    return self.update_specs(updated_specs)
