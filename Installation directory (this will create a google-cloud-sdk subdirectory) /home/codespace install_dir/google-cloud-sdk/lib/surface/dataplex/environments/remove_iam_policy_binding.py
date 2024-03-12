# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""`gcloud dataplex environment remove-iam-policy-binding` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import environment
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class RemoveIamPolicyBinding(base.Command):
  """Removes IAM policy binding from a Dataplex Environment."""

  detailed_help = {
      'EXAMPLES':
          """\

          To remove an IAM policy binding for the role `roles/dataplex.viewer`
          for the user `testuser@gmail.com` from an environment `test-environment` within lake
          `test-lake` in location `us-central1`, run:

            $ {command} test-environment --project=test-project --location=us-central1 --lake=test-lake --role=roles/dataplex.viewer --member=user:testuser@gmail.com


          See https://cloud.google.com/dataplex/docs/iam-roles for details of
          policy role and member types.

          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(
        parser, 'to remove IAM policy binding from ')

    iam_util.AddArgsForRemoveIamPolicyBinding(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.')
  def Run(self, args):
    environment_ref = args.CONCEPTS.environment.Parse()
    result = environment.RemoveIamPolicyBinding(environment_ref, args.member,
                                                args.role)
    return result
