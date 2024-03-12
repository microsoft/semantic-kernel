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
"""'vmware  private-clouds identity-sources update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.identitysources import IdentitySourcesClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

_DETAILED_HELP = {
    'DESCRIPTION': """
        Update an identity source. Only base-users-dn, base-groups-dn, domain-user, domain-password and ssl-certificates can be updated.
      """,
    'EXAMPLES': """
        To update an identity source called `my-identity-source` in private cloud `my-private-cloud` and zone `us-west2-a`
        by changing base-users-dn to `dc=example,dc=com`, domain-user to `user@example.com`, and domain-password to `secretPassword123` run:

          $ {command} my-identity-source --project=my-project --location=us-west2-a --private-cloud=my-private-cloud
            --base-users-dn dc=example,dc=com --domain-user user@example.com --domain-password secretPassword123

          Or:

          $ {command} my-identity-source --private-cloud=my-private-cloud --base-users-dn dc=example,dc=com
            --domain-user user@example.com --domain-password secretPassword123

         In the second example, the project and location are taken from gcloud properties `core/project` and `compute/zone` respectively.
  """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Google Cloud VMware Engine identity source."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddIdentitySourceArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--base-users-dn',
        help='The base distinguished name for users.',
    )
    parser.add_argument(
        '--base-groups-dn',
        help='The base distinguished name for groups.',
    )
    parser.add_argument(
        '--domain-user',
        help=(
            'ID of a user in the domain who has a minimum of read-only access'
            ' to the base distinguished names of users and groups.'
        ),
    )
    parser.add_argument(
        '--domain-password',
        help=(
            'Password of the user in the domain who has a  minimum of read-only'
            ' access to the base distinguished names of users and groups.'
        ),
    )
    parser.add_argument(
        '--ssl-certificate-from-file',
        action='append',
        default=[],
        help=(
            'Path to the root CA certificate files in CER format for the LDAPS'
            ' server. Can be passed multiple times.'
        ),
    )

  def Run(self, args):
    source = args.CONCEPTS.identity_source.Parse()
    client = IdentitySourcesClient()

    certificates = [
        files.ReadFileContents(path) for path in args.ssl_certificate_from_file
    ]

    operation = client.Update(
        source,
        base_users_dn=args.base_users_dn,
        base_groups_dn=args.base_groups_dn,
        domain_user=args.domain_user,
        domain_password=args.domain_password,
        ssl_certificates=certificates,
    )
    is_async = args.async_

    if is_async:
      log.UpdatedResource(operation.name, kind='identity source', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for identity source [{}] to be updated'.format(
            source.RelativeName()
        ),
    )
    log.UpdatedResource(source.RelativeName(), kind='identity source')
    return resource
