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
"""`gcloud domains registrations list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util

_FORMAT = """\
table(
    name.scope("registrations"):label=DOMAIN,
    state:label=STATE,
    managementSettings.renewalMethod:label=RENEWAL_METHOD,
    expireTime:label=EXPIRE_TIME
)
"""


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List Cloud Domains registrations.

  List Cloud Domains registrations in the project.

  ## EXAMPLES

  To list all registrations in the project, run:

    $ {command}
  """

  @staticmethod
  def ArgsPerVersion(api_version, parser):
    resource_args.AddLocationResourceArg(parser, 'to list registrations for')
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(util.RegistrationsUriFunc(api_version))

  @staticmethod
  def Args(parser):
    List.ArgsPerVersion(registrations.BETA_API_VERSION, parser)

  def Run(self, args):
    """Run the list command."""
    api_version = registrations.GetApiVersionFromArgs(args)
    client = registrations.RegistrationsClient(api_version)

    location_ref = args.CONCEPTS.location.Parse()

    return client.List(location_ref, args.limit, args.page_size)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(List):
  """List Cloud Domains registrations.

  List Cloud Domains registrations in the project.

  ## EXAMPLES

  To list all registrations in the project, run:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    List.ArgsPerVersion(registrations.ALPHA_API_VERSION, parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListGa(List):
  """List Cloud Domains registrations.

  List Cloud Domains registrations in the project.

  ## EXAMPLES

  To list all registrations in the project, run:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    List.ArgsPerVersion(registrations.GA_API_VERSION, parser)
