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
"""'vmware private-clouds identity-sources create' command."""

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
        Create a new identity source resource in a given private cloud.
      """,
    'EXAMPLES': """
        To create an identity source called `my-is` in a private cloud `my-pc` located in project `my-project` and zone `us-west1-a`:

          $ {command} my-is --private-cloud my-pc --project my-project --location us-west1-a --domain example.com
            --base-users-dn dc=example,dc=com --base-groups-dn dc=example,dc=com --domain-user user@example.com
            --domain-password secretPassword123 --protocol LDAP --primary-server ldap://example.com

          Or:

          $ {command} my-is --private-cloud my-pc --domain example.com --base-users-dn dc=example,dc=com
            --base-groups-dn dc=example,dc=com --domain-user user@example.com --domain-password secretPassword123
            --protocol LDAP --primary-server ldap://example.com

          In the second example, the project and location are taken from gcloud properties `core/project` and `compute/zone` respectively.
  """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Google Cloud VMware Engine identity source."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddIdentitySourceArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--domain',
        required=True,
        help='The domain name of the identity source.',
    )
    parser.add_argument(
        '--domain-alias',
        required=False,
        help='The domain alias of the identity source.',
    )
    parser.add_argument(
        '--base-users-dn',
        required=True,
        help='The base distinguished name for users.',
    )
    parser.add_argument(
        '--base-groups-dn',
        required=True,
        help='The base distinguished name for groups.',
    )
    parser.add_argument(
        '--domain-user',
        required=True,
        help=(
            'ID of a user in the domain who has a minimum of read-only access'
            ' to the base distinguished names of users and groups.'
        ),
    )
    parser.add_argument(
        '--domain-password',
        required=True,
        help=(
            'Password of the user in the domain who has a minimum of read-only'
            ' access to the base distinguished names of users and groups.'
        ),
    )
    parser.add_argument(
        '--protocol',
        required=True,
        choices=['LDAP', 'LDAPS'],
        help='The LDAP server connection protocol.',
    )
    parser.add_argument(
        '--primary-server',
        required=True,
        help="""
        Primary domain controller LDAP server for the domain.
        Format `ldap://hostname:port` or `ldaps://hostname:port`
        """,
    )
    parser.add_argument(
        '--secondary-server',
        help="""
        Secondary domain controller LDAP server for the domain.
        Format `ldap://hostname:port` or `ldaps://hostname:port`
        """,
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
    is_async = args.async_

    certificates = [
        files.ReadFileContents(path) for path in args.ssl_certificate_from_file
    ]

    operation = client.Create(
        source,
        domain=args.domain,
        domain_alias=args.domain_alias,
        base_users_dn=args.base_users_dn,
        base_groups_dn=args.base_groups_dn,
        domain_user=args.domain_user,
        domain_password=args.domain_password,
        protocol=args.protocol,
        primary_server=args.primary_server,
        secondary_server=args.secondary_server,
        ssl_certificates=certificates,
    )
    if is_async:
      log.CreatedResource(operation.name, kind='identity source', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for identity source [{}] to be created'.format(
            source.RelativeName()
        ),
    )
    log.CreatedResource(source.RelativeName(), kind='identity source')
    return resource
