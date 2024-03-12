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
"""`gcloud dataplex data-taxonomies attributes add-iam-policy-binding` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.dataplex import data_taxonomy
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddIamPolicyBinding(base.Command):
  """Add IAM policy binding to a Dataplex Data Attribute."""

  detailed_help = {
      'EXAMPLES':
          """\
          To add an IAM policy binding for the role of `roles/dataplex.viewer`
          for the user `test-user@gmail.com` to Data Attribute `test-attribute` in location
          `us-central`, in Data Taxonomy 'test-taxonomy', run:

            $ {command} test-attribute --project=test-project  --location=us-central1 --data_taxonomy=test-datataxonomy --role=roles/dataplex.viewer --member=user:foo@gmail.com

          See https://cloud.google.com/dataplex/docs/iam-roles for details of
          policy role and member types.
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddAttributeResourceArg(parser,
                                          'to add IAM policy binding to.')

    iam_util.AddArgsForAddIamPolicyBinding(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.')
  def Run(self, args):
    data_attribute_ref = args.CONCEPTS.data_attribute.Parse()
    result = data_taxonomy.DataAttributeAddIamPolicyBinding(
        data_attribute_ref, args.member, args.role)
    return result
