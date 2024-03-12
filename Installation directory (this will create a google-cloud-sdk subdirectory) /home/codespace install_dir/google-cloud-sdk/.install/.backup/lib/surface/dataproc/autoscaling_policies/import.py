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
"""Import autoscaling policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io


class Import(base.Command):
  """Import an autoscaling policy.

  If the specified autoscaling policy already exists, it will be overwritten.
  Otherwise, a new autoscaling policy will be created.
  To edit an existing autoscaling policy, you can export the autoscaling policy
  to a file, edit its configuration, and then import the new configuration.

  This command does not allow output only fields, such as policy id and resource
  name. It populates the id field based on the resource name specified as the
  first command line argument.

  ## EXAMPLES

  The following command creates or updates the contents of autoscaling policy
  `example-autoscaling-policy` based on a yaml file:

    $ {command} example-autoscaling-policy --source=saved-policy.yaml
  """

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())

    flags.AddAutoscalingPolicyResourceArg(parser, 'import',
                                          dataproc.api_version)
    export_util.AddImportFlags(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    policy_ref = args.CONCEPTS.autoscaling_policy.Parse()
    policy = util.ReadAutoscalingPolicy(
        dataproc=dataproc,
        policy_id=policy_ref.Name(),
        policy_file_name=args.source)

    try:
      return util.CreateAutoscalingPolicy(dataproc, policy_ref.RelativeName(),
                                          policy)
    except apitools_exceptions.HttpError as error:
      # Catch ALREADY_EXISTS
      if error.status_code != 409:
        raise error
      # Warn the user that they're going to overwrite an existing policy
      console_io.PromptContinue(
          message=('Autoscaling policy [{0}] will be overwritten.').format(
              policy.id),
          cancel_on_no=True)
      return util.UpdateAutoscalingPolicy(dataproc, policy_ref.RelativeName(),
                                          policy)
