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
"""`gcloud service-directory namespaces add-iam-policy-binding` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.service_directory import namespaces
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.service_directory import resource_args

_RESOURCE_TYPE = 'namespace'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AddIamPolicyBinding(base.Command):
  """Adds IAM policy binding to a namespace."""

  detailed_help = {
      'EXAMPLES':
          """\
          To add an IAM policy binding to a Service Directory namespace, run:

            $ {command} my-namespace --location=us-east1 --role=roles/owner --member=user:foo@gmail.com
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddNamespaceResourceArg(parser,
                                          'to add IAM policy binding to.')

    iam_util.AddArgsForAddIamPolicyBinding(parser)

  def Run(self, args):
    client = namespaces.NamespacesClient(self.GetReleaseTrack())
    namespace_ref = args.CONCEPTS.namespace.Parse()

    result = client.AddIamPolicyBinding(namespace_ref, args.member, args.role)
    iam_util.LogSetIamPolicy(namespace_ref.Name(), _RESOURCE_TYPE)

    return result

  def GetReleaseTrack(self):
    return base.ReleaseTrack.GA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class AddIamPolicyBindingBeta(AddIamPolicyBinding):
  """Adds IAM policy binding to a namespace."""

  def GetReleaseTrack(self):
    return base.ReleaseTrack.BETA
