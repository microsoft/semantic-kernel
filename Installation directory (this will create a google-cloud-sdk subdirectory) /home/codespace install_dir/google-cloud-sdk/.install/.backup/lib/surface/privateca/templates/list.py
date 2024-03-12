# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""List certificate templates within a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import resource_utils
from googlecloudsdk.api_lib.util import common_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import response_utils
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List certificate templates within a project."""

  detailed_help = {
      'DESCRIPTION':
          'List certificate templates.',
      'EXAMPLES':
          """\
      To list all certificate templates in a project across all locations, run:

        $ {command}

      To list all certificate templates in a project and location 'us-central1',
      run:

        $ {command} --location=us-central1""",
  }

  @staticmethod
  def Args(parser):
    base.Argument(
        '--location',
        help=('The location you want to list the certificate templates for. '
              'Set this to "-" to list certificate templates across all '
              'locations.'),
        default='-').AddToParser(parser)
    base.PAGE_SIZE_FLAG.SetDefault(parser, 100)
    base.SORT_BY_FLAG.SetDefault(parser, 'name')

    parser.display_info.AddFormat("""
      table(
        name.scope("certificateTemplates"):label=NAME,
        name.scope("locations").segment(0):label=LOCATION,
        description
      )""")
    parser.display_info.AddUriFunc(
        resource_utils.MakeGetUriFunc(
            'privateca.projects.locations.certificateTemplates'))

  def Run(self, args):
    """Runs the command."""
    client = privateca_base.GetClientInstance(api_version='v1')
    messages = privateca_base.GetMessagesModule(api_version='v1')

    parent = 'projects/{}/locations/{}'.format(
        properties.VALUES.core.project.GetOrFail(), args.location)
    request = messages.PrivatecaProjectsLocationsCertificateTemplatesListRequest(
        parent=parent,
        orderBy=common_args.ParseSortByArg(args.sort_by),
        filter=args.filter)
    return list_pager.YieldFromList(
        client.projects_locations_certificateTemplates,
        request,
        field='certificateTemplates',
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        get_field_func=response_utils.GetFieldAndLogUnreachable)
