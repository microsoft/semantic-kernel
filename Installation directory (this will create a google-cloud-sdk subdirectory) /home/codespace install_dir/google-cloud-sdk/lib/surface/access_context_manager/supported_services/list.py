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

"""services list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import supported_services
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(base.ListCommand):
  """Lists all [VPC Service Controls supported services].

  Lists the services that VPC Service Controls supports. The services that are
  in this list either fully support VPC Service Controls or the
  integration of this service with VPC Service Controls is in
  [Preview stage](https://cloud.google.com/products#product-launch-stages).
  Services that aren't in this list don't support VPC Service Controls and
  aren't guaranteed to function properly in a VPC Service Controls
  environment.
  """

  _API_VERSION = 'v1'
  detailed_help = {
      'brief': 'Lists all VPC Service Controls supported services',
      'DESCRIPTION': (
          'Lists the services that VPC Service Controls supports. The services'
          ' that are in this list either fully support VPC Service Controls or'
          ' the integration of this service with VPC Service Controls is in'
          ' [Preview'
          ' stage](https://cloud.google.com/products#product-launch-stages).'
          " Services that aren't in this list don't support VPC Service"
          " Controls and aren't guaranteed to function properly in a VPC"
          ' Service Controls environment.'
      ),
      'EXAMPLES': """\
  To list VPC Service Controls supported services, run:

    $ {command}

  This command prints out a list of all supported services in a tabular form:

    NAME                    TITLE                SUPPORT_STAGE  AVAILABLE_ON_RESTRICTED_VIP KNOWN_LIMITATIONS
    vpcsc_supported_service VPC-SC Supported API GA             True                        False
  """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """

    # Remove unneeded list-related flags from parser
    base.URI_FLAG.RemoveFromParser(parser)

    parser.display_info.AddFormat("""
          table(
            name:label=NAME:sort=1,
            title:label=TITLE,
            supportStage:label=SUPPORT_STAGE,
            availableOnRestrictedVip.yesno(no=False):label=AVAILABLE_ON_RESTRICTED_VIP,
            known_limitations.yesno(no=False):label=KNOWN_LIMITATIONS
          )
        """)

  def Run(self, args):
    """Run 'access-context-manager supported-services list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The list of VPC Service Controls supportes services.
    """

    client = supported_services.Client(version=self._API_VERSION)

    return client.List(args.page_size, args.limit)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  _API_VERSION = 'v1alpha'
