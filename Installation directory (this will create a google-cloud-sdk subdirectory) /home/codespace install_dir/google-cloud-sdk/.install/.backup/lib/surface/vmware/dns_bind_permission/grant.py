# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""'vmware dns-bind-permission grant' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware import dnsbindpermission
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
          Grants the bind permission to the customer provided user/service account to bind their DNS zone with the intranet VPC associated with the project.
        """,
    'EXAMPLES': """
          To grant the bind permission to the customer provided user `user@abc.com` to bind their DNS zone with the intranet VPC associated with project `my-project`, run:

            $ {command} --user=user@abc.com --project=my-project

          Or:

            $ {command} --user=user@abc.com

          In the second example, the project is taken from gcloud properties core/project.

          To grant the bind permission to the customer provided service account `service-account@gserviceaccount.com` to bind their DNS zone with the intranet VPC associated with project `my-project`, run:

          $ {command} --service-account=service-account@gserviceaccount.com --project=my-project

          Or:

            $ {command} --service-account=service-account@gserviceaccount.com

          In the second example, the project is taken from gcloud properties core/project.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Grant(base.Command):
  """Grants a DNS Bind Permission."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddProjectArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--user',
        required=False,
        help="""\
        The consumer provided user which needs to be granted permission to bind with the intranet VPC corresponding to the consumer project. If this field is not provided then the service-account should be provided.
        """,
    )
    group.add_argument(
        '--service-account',
        required=False,
        help="""\
        The consumer provided service account which needs to be granted permission to bind with the intranet VPC corresponding to the consumer project. If this field is not provided then the user should be provided.
        """,
    )

  def Run(self, args):
    project = args.CONCEPTS.project.Parse()
    client = dnsbindpermission.DNSBindPermissionClient()
    is_async = args.async_
    operation = client.Grant(
        project, user=args.user, service_account=args.service_account
    )
    if is_async:
      log.UpdatedResource(
          operation.name, kind='DNS Bind Permission', is_async=True
      )
      return

    dns_bind_permission = '{project}/locations/global/dnsBindPermission'.format(
        project=project.RelativeName()
    )
    client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=('waiting for DNS Bind Permission [{}] to be granted').format(
            dns_bind_permission
        ),
        has_result=False,
    )
    resource = client.Get(project)
    log.UpdatedResource(
        dns_bind_permission, kind='DNS Bind Permission'
    )
    return resource
