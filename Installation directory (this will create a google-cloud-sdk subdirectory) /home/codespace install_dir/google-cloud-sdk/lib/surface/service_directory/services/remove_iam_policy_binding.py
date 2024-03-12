# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""`gcloud service-directory services remove-iam-policy-binding` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.service_directory import services
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.service_directory import resource_args

_RESOURCE_TYPE = 'service'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class RemoveIamPolicyBinding(base.Command):
  """Removes IAM policy binding from a service."""

  detailed_help = {
      'EXAMPLES':
          """\
          To remove an IAM policy binding to a Service Directory service, run:

            $ {command} my-service --namespace=my-namespace --location=us-east1 --role=roles/owner --member=user:foo@gmail.com
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddServiceResourceArg(
        parser,
        """to remove IAM policy binding from.""")

    iam_util.AddArgsForRemoveIamPolicyBinding(parser)

  def Run(self, args):
    client = services.ServicesClient(self.GetReleaseTrack())
    service_ref = args.CONCEPTS.service.Parse()

    result = client.RemoveIamPolicyBinding(service_ref, args.member, args.role)
    iam_util.LogSetIamPolicy(service_ref.Name(), _RESOURCE_TYPE)

    return result

  def GetReleaseTrack(self):
    return base.ReleaseTrack.GA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class RemoveIamPolicyBindingBeta(RemoveIamPolicyBinding):
  """Removes IAM policy binding from a service."""

  def GetReleaseTrack(self):
    return base.ReleaseTrack.BETA
