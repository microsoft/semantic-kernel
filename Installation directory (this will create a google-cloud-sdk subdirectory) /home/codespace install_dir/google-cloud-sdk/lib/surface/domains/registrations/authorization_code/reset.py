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
"""`gcloud domains registrations authorization-code reset` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util


class ResetAuthorizationCode(base.DescribeCommand):
  """Resets authorization code of a specific Cloud Domains registration.

  Resets authorization code of a specific registration.

  You can call this API only after 60 days have elapsed since initial
  registration.

  ## EXAMPLES

  To reset authorization code of ``example.com'', run:

    $ {command} example.com
  """

  @staticmethod
  def Args(parser):
    resource_args.AddRegistrationResourceArg(parser,
                                             'to reset authorization code for')

  def Run(self, args):
    """Run reset authorization code command."""
    api_version = registrations.GetApiVersionFromArgs(args)
    client = registrations.RegistrationsClient(api_version)
    args.registration = util.NormalizeResourceName(args.registration)
    registration_ref = args.CONCEPTS.registration.Parse()

    registration = client.Get(registration_ref)
    util.AssertRegistrationOperational(api_version, registration)

    return client.ResetAuthorizationCode(registration_ref)
