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
"""`gcloud domains registrations describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import registration_printer
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core import log


class Describe(base.DescribeCommand):
  """Describe an existing Cloud Domains registration.

  Print information about an existing registration.

  ## EXAMPLES

  To describe a registration for ``example.com'', run:

    $ {command} example.com
  """

  @staticmethod
  def Args(parser):
    resource_args.AddRegistrationResourceArg(parser, 'to describe')

    resource_printer.RegisterFormatter(
        registration_printer.REGISTRATION_PRINTER_FORMAT,
        registration_printer.RegistrationPrinter,
        hidden=True)
    parser.display_info.AddFormat(
        registration_printer.REGISTRATION_PRINTER_FORMAT)

  def Run(self, args):
    api_version = registrations.GetApiVersionFromArgs(args)
    client = registrations.RegistrationsClient(api_version)
    args.registration = util.NormalizeResourceName(args.registration)

    registration = client.Get(args.CONCEPTS.registration.Parse())

    return registration
