# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to query activities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.policy_intelligence import policy_troubleshooter
from googlecloudsdk.calliope import base

_DETAILED_HELP = {
    'brief': """Troubleshoot the IAM Policy.
        """,
    'DESCRIPTION': """\
      Performs a check on whether a principal is granted a
      permission on a resource and how that access is determined according to
      the resource's effective IAM policy interpretation.
        """,
    'EXAMPLES': """\
    To troubleshoot a permission of a principal on a resource, run:

      $ {command} //cloudresourcemanager.googleapis.com/projects/project-id \
      --principal-email=my-iam-account@somedomain.com \
      --permission=resourcemanager.projects.get

    See https://cloud.google.com/iam/help/allow-policies/overview for more
    information about IAM policies.
      """,
}

_DETAILED_HELP = {
    'brief': """Troubleshoot IAM allow and deny policies.
        """,
    'DESCRIPTION': """\
      Uses a resource's effective IAM allow policy and IAM deny policy to
      check whether a principal has a specific permission on the resource.
        """,
    'EXAMPLES': """\
      The following command checks whether the principal ``my-user@example.com''
      has the permission ``resourcemanager.projects.get'' on the project
      ``my-project'':

        $ {command} //cloudresourcemanager.googleapis.com/projects/my-project
        --principal-email=my-user@example.com
        --permission=resourcemanager.projects.get

      The following command checks whether the principal ``my-user@example.com''
      has the ``compute.images.get'' permission on the project
      ``my-project''. The command also provides additional context that lets
      Troubleshooter evaluate conditional role bindings:

        $ {command} //cloudresourcemanager.googleapis.com/projects/my-project \
        --principal-email=my-user@example.com \
        --permission=compute.images.get \
        --resource-name=//compute.googleapis.com/projects/my-project/zones/images/my-image'\
        --resource-service='compute.googleapis.com' \
        --resource-type='compute.googleapis.com/Image' \
        --destination-ip='192.2.2.2'--destination-port=8080 --request-time='2023-01-01T00:00:00Z'
      """,
}


def _Args(parser):
  """Parses arguments for the commands."""
  parser.add_argument(
      'resource',
      metavar='RESOURCE',
      type=str,
      help="""Full resource name that access is checked against.
      For a list of full resource name formats, see: https://cloud.google.com/iam/docs/resource-names.
      """,
  )
  parser.add_argument(
      '--principal-email',
      required=True,
      metavar='EMAIL',
      type=str,
      help="""Email address that identifies the principal to check. Only Google Accounts and
      service accounts are supported.
      """,
  )
  parser.add_argument(
      '--permission',
      required=True,
      metavar='PERMISSION',
      type=str,
      help="""IAM permission to check. The permssion can be in the `v1` or `v2`
      format. For example, `resourcemanager.projects.get` or
      `cloudresourcemanager.googleapis.com/projects.get`.
      For a list of permissions, see https://cloud.google.com/iam/docs/permissions-reference and https://cloud.google.com/iam/docs/deny-permissions-support
      """,
  )
  parser.add_argument(
      '--resource-service',
      required=False,
      type=str,
      help="""The resource service value to use when checking conditional bindings.
      For accepted values, see: https://cloud.google.com/iam/docs/conditions-resource-attributes#resource-service
      """,
  )
  parser.add_argument(
      '--resource-type',
      required=False,
      type=str,
      help="""The resource type value to use when checking conditional bindings.
      For accepted values, see: https://cloud.google.com/iam/docs/conditions-resource-attributes#resource-type
      """,
  )
  parser.add_argument(
      '--resource-name',
      required=False,
      type=str,
      help="""The resource name value to use when checking conditional bindings.
      For accepted values, see: https://cloud.google.com/iam/docs/conditions-resource-attributes#resource-name.
      """,
  )
  parser.add_argument(
      '--request-time',
      required=False,
      type=str,
      help="""The request timestamp to use when checking conditional bindings. This string must adhere to UTC format
      (RFC 3339). For example,2021-01-01T00:00:00Z. For more information, see:
      https://tools.ietf.org/html/rfc3339
      """,
  )
  parser.add_argument(
      '--destination-ip',
      required=False,
      type=str,
      help="""The request destination IP address to use when checking conditional bindings. For example, `198.1.1.1`.
      """,
  )
  parser.add_argument(
      '--destination-port',
      required=False,
      type=int,
      help="""The request destination port to use when checking conditional bindings. For example, 8080.
      """,
  )


def _Run(policy_troubleshooter_api, args):
  """Troubleshoot the IAM Policies."""
  destination_context = policy_troubleshooter_api.GetPolicyTroubleshooterPeer(
      destination_ip=args.destination_ip,
      destination_port=args.destination_port,
  )
  request_context = policy_troubleshooter_api.GetPolicyTroubleshooterRequest(
      request_time=args.request_time
  )
  resource_context = policy_troubleshooter_api.GetPolicyTroubleshooterResource(
      resource_name=args.resource_name,
      resource_service=args.resource_service,
      resource_type=args.resource_type,
  )
  condition_context = (
      policy_troubleshooter_api.GetPolicyTroubleshooterConditionContext(
          destination=destination_context,
          request=request_context,
          resource=resource_context,
      )
  )
  access_tuple = policy_troubleshooter_api.GetPolicyTroubleshooterAccessTuple(
      condition_context=condition_context,
      full_resource_name=args.resource,
      principal_email=args.principal_email,
      permission=args.permission,
  )
  return policy_troubleshooter_api.TroubleshootIAMPolicies(access_tuple)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class TroubleshootAlpha(base.Command):
  """Troubleshoot the IAM Policies."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Parses arguments for the commands."""
    _Args(parser)

  def Run(self, args):
    return _Run(
        policy_troubleshooter.PolicyTroubleshooterApi(self.ReleaseTrack()), args
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.Hidden
class TroubleshootBeta(base.Command):
  """Troubleshoot IAM allow and deny policies."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Parses arguments for the commands."""
    _Args(parser)

  def Run(self, args):
    return _Run(
        policy_troubleshooter.PolicyTroubleshooterApi(self.ReleaseTrack()), args
    )


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Troubleshoot(base.Command):
  """Troubleshoot IAM allow and deny policies."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Parses arguments for the commands."""
    _Args(parser)

  def Run(self, args):
    return _Run(
        policy_troubleshooter.PolicyTroubleshooterApi(self.ReleaseTrack()), args
    )
