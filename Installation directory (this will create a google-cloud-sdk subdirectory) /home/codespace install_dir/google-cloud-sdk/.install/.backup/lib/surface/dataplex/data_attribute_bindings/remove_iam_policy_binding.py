# -*- coding: utf-8 -*- #
# Copyright 2022 Google Inc. All Rights Reserved.
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
"""`gcloud dataplex data-attribute-bindings remove-iam-policy-binding` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import data_taxonomy
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class RemoveIamPolicyBinding(base.Command):
  """Removes IAM policy binding from a Dataplex Data Attribute Binding."""

  detailed_help = {
      'EXAMPLES':
          """\

          To remove an IAM policy binding for the role `roles/dataplex.viewer`
          for the user `testuser@gmail.com` from an Data Attribute Binding `test-attribute-binding` within projet
          `test-project` in location `us-central1`, run:

            $ {command} test-attribute-binding --project=test-project --location=us-central1 --role=roles/dataplex.viewer --member=user:testuser@gmail.com


          See https://cloud.google.com/dataplex/docs/iam-roles for details of
          policy role and member types.

          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddDataAttributeBindingResourceArg(
        parser, 'to remove IAM policy binding from ')

    iam_util.AddArgsForRemoveIamPolicyBinding(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.')
  def Run(self, args):
    attribute_binding_ref = args.CONCEPTS.data_attribute_binding.Parse()
    result = data_taxonomy.DataAttributeBindingRemoveIamPolicyBinding(
        attribute_binding_ref, args.member, args.role)
    return result
