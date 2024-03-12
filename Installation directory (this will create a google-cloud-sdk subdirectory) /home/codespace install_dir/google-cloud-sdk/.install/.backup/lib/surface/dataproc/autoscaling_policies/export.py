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
"""Export autoscaling policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files


class Export(base.Command):
  """Export an autoscaling policy.

  Exporting an autoscaling policy is similar to describing one, except that
  export omits output only fields, such as the policy id and resource name. This
  is to allow piping the output of export directly into import, which requires
  that output only fields are omitted.

  ## EXAMPLES

  The following command saves the contents of autoscaling policy
  `example-autoscaling-policy` to a file so that it can be imported later:

    $ {command} example-autoscaling-policy --destination=saved-policy.yaml
  """

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddAutoscalingPolicyResourceArg(parser, 'export',
                                          dataproc.api_version)
    export_util.AddExportFlags(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    messages = dataproc.messages

    policy_ref = args.CONCEPTS.autoscaling_policy.Parse()

    request = messages.DataprocProjectsRegionsAutoscalingPoliciesGetRequest(
        name=policy_ref.RelativeName())
    policy = dataproc.client.projects_regions_autoscalingPolicies.Get(request)

    # Filter out OUTPUT_ONLY fields and resource identifying fields. Note this
    # needs to be kept in sync with v1 autoscaling_policies.proto.
    policy.id = None
    policy.name = None

    if args.destination:
      with files.FileWriter(args.destination) as stream:
        export_util.Export(message=policy, stream=stream)
    else:
      # Print to stdout
      export_util.Export(message=policy, stream=sys.stdout)
