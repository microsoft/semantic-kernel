# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""List the subordinate certificate authorities within a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import resource_utils
from googlecloudsdk.api_lib.util import common_args
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import response_utils
from googlecloudsdk.command_lib.privateca import text_utils
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List subordinate certificate authorities.

  List the subordinate certificate authorities within a project.

  ## EXAMPLES

  To list all subordinate certificate authorities in a project:

  $ {command}

  To list all subordinate certificate authorities within a project and location
  'us-central1':

  $ {command} --location=us-central1

  To list all subordinate certificate authorities within a CA Pool in location
  'us-central1':

  $ {command} --pool=my-pool --location=us-central1
  """

  @staticmethod
  def Args(parser):
    base.Argument(
        '--location',
        help=(
            'Location of the certificate authorities. If omitted, subordinate '
            'CAs across all regions will be listed. Note that, if it is '
            'populated, the privateca/location property will be used if this '
            'flag is not specified. To ignore this property, specify "-" as '
            'the location.')).AddToParser(parser)
    base.Argument(
        '--pool',
        help=('ID of the CA Pool where the certificate authorities reside. If '
              'omitted, subordinate CAs across all CA pools will be listed.'
             )).AddToParser(parser)
    base.PAGE_SIZE_FLAG.SetDefault(parser, 100)
    base.FILTER_FLAG.RemoveFromParser(parser)

    parser.display_info.AddFormat("""
        table(
          name.basename(),
          name.scope().segment(-5):label=LOCATION,
          name.scope().segment(-3):label=POOL,
          state,
          state.regex("ENABLED","YES","NO"):label=INCLUDED_IN_POOL_ISSUANCE,
          ca_certificate_descriptions[0].subject_description.not_before_time():label=NOT_BEFORE,
          ca_certificate_descriptions[0].subject_description.not_after_time():label=NOT_AFTER)
        """)
    parser.display_info.AddTransforms({
        'not_before_time': text_utils.TransformNotBeforeTime,
        'not_after_time': text_utils.TransformNotAfterTime
    })
    parser.display_info.AddUriFunc(
        resource_utils.MakeGetUriFunc(
            'privateca.projects.locations.caPools.certificateAuthorities'))

  def Run(self, args):
    client = privateca_base.GetClientInstance(api_version='v1')
    messages = privateca_base.GetMessagesModule(api_version='v1')

    location_property_fallback = properties.VALUES.privateca.location.Get()
    if args.IsSpecified('location'):
      location = args.location
    elif location_property_fallback and args.IsSpecified('pool'):
      location = location_property_fallback
    else:
      location = '-'

    ca_pool_id = args.pool if args.IsSpecified('pool') else '-'

    if location == '-' and args.IsSpecified('pool'):
      raise exceptions.InvalidArgumentException(
          '--location',
          'If a pool id is specified, you must also specify the location of that pool.'
      )

    parent_resource = 'projects/{}/locations/{}/caPools/{}'.format(
        properties.VALUES.core.project.GetOrFail(), location, ca_pool_id)

    request = messages.PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesListRequest(
        parent=parent_resource,
        filter='type:SUBORDINATE',
        orderBy=common_args.ParseSortByArg(args.sort_by))

    return list_pager.YieldFromList(
        client.projects_locations_caPools_certificateAuthorities,
        request,
        field='certificateAuthorities',
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        get_field_func=response_utils.GetFieldAndLogUnreachable)
