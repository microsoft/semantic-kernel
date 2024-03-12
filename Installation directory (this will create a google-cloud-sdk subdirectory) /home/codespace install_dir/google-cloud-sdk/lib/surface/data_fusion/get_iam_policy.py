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
"""Command to describe a Data Fusion instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_fusion import datafusion as df
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_fusion import resource_args


class Get(base.ListCommand):
  r"""Gets the IAM policy for a Cloud Data Fusion instance.

  ## EXAMPLES

  To get IAM policy for instance 'my-instance' in project 'my-project' and
  location 'my-location', run:

    $ {command} my-instance --project=my-project --location=my-location

  To run the same command for a specific namespace on the instance, run:

    $ {command} my-instance --project=my-project --location=my-location \
      --namespace=my-namespace
  """

  @staticmethod
  def Args(parser):
    resource_args.AddInstanceResourceArg(parser, 'Instance to describe.')
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--namespace',
        help='CDAP Namespace whose IAM policy we wish to fetch. '
        'For example: `--namespace=my-namespace`.')

  def Run(self, args):
    datafusion = df.Datafusion()
    instance_ref = args.CONCEPTS.instance.Parse()

    if not args.namespace:
      request = datafusion.messages.DatafusionProjectsLocationsInstancesGetIamPolicyRequest(
          resource=instance_ref.RelativeName())

      iam_policy = datafusion.client.projects_locations_instances.GetIamPolicy(
          request)
      return iam_policy
    else:
      request = datafusion.messages.DatafusionProjectsLocationsInstancesNamespacesGetIamPolicyRequest(
          resource='%s/namespaces/%s' %
          (instance_ref.RelativeName(), args.namespace))

      iam_policy = datafusion.client.projects_locations_instances_namespaces.GetIamPolicy(
          request)
      return iam_policy
