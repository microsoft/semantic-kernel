# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command for creating or updating application resources from YAML specification."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run.integrations import flags
from googlecloudsdk.command_lib.run.integrations import run_apps_operations
from googlecloudsdk.command_lib.runapps import exceptions


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Deploy(base.Command):
  """Create or update application resources from a YAML specification."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To create application resources from specification

              $ {command} stack.yaml

         """,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddFileArg(parser)
    flags.AddServiceAccountArg(parser)

  def _ValidateAppConfigFile(self, file_content):
    if 'name' not in file_content and 'resources' not in file_content:
      raise exceptions.FieldMismatchError("'name' or 'resources' is missing.")
    if '/t' in file_content:
      raise exceptions.ConfigurationError('tabs found in manifest content.')

  def Run(self, args):
    """Create or Update application from YAML."""

    file_content = args.FILE
    self._ValidateAppConfigFile(file_content)

    release_track = self.ReleaseTrack()
    with run_apps_operations.Connect(args, release_track) as client:
      client.VerifyLocation()

      return client.ApplyYaml(file_content)
