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
"""Command to set an IAM policy binding on a Data Fusion instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_fusion import datafusion as df
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_fusion import data_fusion_iam_util
from googlecloudsdk.command_lib.data_fusion import resource_args
from googlecloudsdk.command_lib.iam import iam_util


class AddIamPolicyBinding(base.Command):
  r"""Adds an IAM policy bindng to a Cloud Data Fusion instance.

  ## EXAMPLES

  To set someone@example.com to have roles/datafusion.admin permission for
  instance 'my-instance', in project 'my-project', location in 'my-location',
  run:

  $ {command} add-iam-policy-binding my-instance --location=my-location \
    --member=user:someone@example.com --role=roles/datafusion.admin

  To run the same command for a specific namespace on the instance, run:

  $ {command} add-iam-policy-binding my-instance --location=my-location \
    --member=user:someone@example.com --role=roles/datafusion.admin \
    --namespace=my-namespace
  """

  @staticmethod
  def Args(parser):
    resource_args.AddInstanceResourceArg(parser, 'Instance to add IAM binding.')
    base.URI_FLAG.RemoveFromParser(parser)

    iam_util.AddArgsForAddIamPolicyBinding(parser)
    parser.add_argument(
        '--namespace',
        help='CDAP Namespace whose IAM policy we wish to append. '
        'For example: `--namespace=my-namespace`.')

  def Run(self, args):
    datafusion = df.Datafusion()
    instance_ref = args.CONCEPTS.instance.Parse()

    if not args.namespace:
      get_request = datafusion.messages.DatafusionProjectsLocationsInstancesGetIamPolicyRequest(
          resource=instance_ref.RelativeName())
      iam_policy = datafusion.client.projects_locations_instances.GetIamPolicy(
          get_request)
    else:
      get_request = datafusion.messages.DatafusionProjectsLocationsInstancesNamespacesGetIamPolicyRequest(
          resource='%s/namespaces/%s' %
          (instance_ref.RelativeName(), args.namespace))
      iam_policy = datafusion.client.projects_locations_instances_namespaces.GetIamPolicy(
          get_request)

    iam_util.AddBindingToIamPolicy(datafusion.messages.Binding,
                                   iam_policy,
                                   args.member,
                                   args.role)

    results = data_fusion_iam_util.DoSetIamPolicy(instance_ref, args.namespace,
                                                  iam_policy,
                                                  datafusion.messages,
                                                  datafusion.client)
    return results
