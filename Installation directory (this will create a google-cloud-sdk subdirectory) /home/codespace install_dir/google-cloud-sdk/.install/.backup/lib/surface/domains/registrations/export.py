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
"""`gcloud domains registrations export` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import flags
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.Deprecate(
    is_removed=True,
    warning=(
        'This command is deprecated. See'
        ' https://cloud.google.com/domains/docs/deprecations/feature-deprecations.'
    ),
    error=(
        'This command has been removed. See'
        ' https://cloud.google.com/domains/docs/deprecations/feature-deprecations.'
    ),
)
class Export(base.DeleteCommand):
  """Export a Cloud Domains registration.

  Export the domain to direct management by Google Domains. The domain remains
  valid until expiry.

  After you export a registered domain, the auto-renewal will be disabled, but
  you will continue to incur billing charges until the next yearly renewal date.
  You will also become the sole owner of the domain in Google Domains, and Cloud
  IAM is not used anymore.

  To manage your domain after exporting, visit Google Domains at
  https://domains.google.com/registrar, or see
  https://support.google.com/domains/answer/3251174 for more information.

  ## EXAMPLES

  To export a registration for ``example.com'', run:

    $ {command} example.com
  """

  @staticmethod
  def Args(parser):
    resource_args.AddRegistrationResourceArg(parser, 'to export')
    flags.AddAsyncFlagToParser(parser)

  def Run(self, args):
    api_version = registrations.GetApiVersionFromArgs(args)
    client = registrations.RegistrationsClient(api_version)
    args.registration = util.NormalizeResourceName(args.registration)
    registration_ref = args.CONCEPTS.registration.Parse()

    console_io.PromptContinue(
        'You are about to export registration \'{}\''.format(
            registration_ref.registrationsId),
        throw_if_unattended=True,
        cancel_on_no=True)

    response = client.Export(registration_ref)

    response = util.WaitForOperation(api_version, response, args.async_)
    log.ExportResource(
        registration_ref.Name(),
        'registration',
        is_async=args.async_,
        details=('Note:\nRegistration remains valid until expiry. Manage it in '
                 'Google Domains at https://domains.google.com/registrar, or '
                 'see https://support.google.com/domains/answer/3251174 for '
                 'more information.'))
    return response
