# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Apply an Anthos configuration package."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.anthos import anthoscli_backend
from googlecloudsdk.command_lib.anthos import flags
from googlecloudsdk.command_lib.util.args import common_args
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Apply(base.BinaryBackedCommand):
  """Apply configuration changes for Anthos infrastructure."""

  detailed_help = {
      'EXAMPLES': """
      To apply Anthos package to a Google Kubernetes Engine cluster in
      project `my-project`:

          $ {command} my-config --project=my-project
      """,
  }

  @staticmethod
  def Args(parser):
    flags.GetLocalDirFlag(
        help_override='Directory of package to apply.').AddToParser(parser)
    common_args.ProjectArgument(
        help_text_to_overwrite='Project ID.').AddToParser(parser)

  def Run(self, args):
    command_executor = anthoscli_backend.AnthosCliWrapper()
    apply_project = properties.VALUES.core.project.Get()
    auth_cred = anthoscli_backend.GetAuthToken(
        account=properties.VALUES.core.account.Get(), operation='apply')
    log.status.Print('Starting apply of package [{}] using '
                     'project [{}]'.format(args.LOCAL_DIR, apply_project))
    response = command_executor(command='apply',
                                apply_dir=args.LOCAL_DIR,
                                project=apply_project,
                                show_exec_error=args.show_exec_error,
                                env=anthoscli_backend.GetEnvArgsForCommand(
                                    extra_vars={'GCLOUD_AUTH_PLUGIN': 'true'}),
                                stdin=auth_cred)
    return self._DefaultOperationResponseHandler(response)
