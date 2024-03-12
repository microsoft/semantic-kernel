# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command to delete Airflow data for a Cloud Composer environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import flags
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import storage_util
from googlecloudsdk.core.console import console_io


DETAILED_HELP = {
    'EXAMPLES':
        '''\
          To delete the data from the path ``path/to/data'', for the
          environment named ``environmnet-1'' in the location ``us-east1'', run:

            $ {command} path/to/data --environment=environment-1 --location=us-east1
        '''
}


class Delete(base.Command):
  """Delete data from an Cloud Composer environment's Cloud Storage bucket.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(
        parser, 'whose data to delete.', positional=False)
    flags.AddDeleteTargetPositional(parser, 'data')

  def Run(self, args):
    env_ref = args.CONCEPTS.environment.Parse()
    subtarget = '[{}] in '.format(args.target) if args.target else ''
    console_io.PromptContinue(
        'Recursively deleting all contents from {}the \'data/\' '
        'subdirectory of environment [{}]'.format(subtarget,
                                                  env_ref.RelativeName()),
        cancel_on_no=True)
    return storage_util.Delete(
        env_ref, args.target or '*', 'data', release_track=self.ReleaseTrack())
