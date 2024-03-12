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
"""`gcloud domains registrations delete` command."""

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


class Delete(base.DeleteCommand):
  """Delete a Cloud Domains registration.

  Delete a registration resource.

  Delete can only be called on registrations in state EXPORTED with expire_time
  in the past.
  It also works for registrations in state REGISTRATION_FAILED, TRANSFER_FAILED,
  and TRANSFER_PENDING.

  ## EXAMPLES

  To delete a registration for ``example.com'', run:

    $ {command} example.com
  """

  @staticmethod
  def Args(parser):
    resource_args.AddRegistrationResourceArg(parser, 'to delete')
    flags.AddAsyncFlagToParser(parser)

  def Run(self, args):
    api_version = registrations.GetApiVersionFromArgs(args)
    client = registrations.RegistrationsClient(api_version)
    args.registration = util.NormalizeResourceName(args.registration)
    registration_ref = args.CONCEPTS.registration.Parse()

    console_io.PromptContinue(
        'You are about to delete registration \'{}\''.format(
            registration_ref.registrationsId),
        throw_if_unattended=True,
        cancel_on_no=True)

    response = client.Delete(registration_ref)

    response = util.WaitForOperation(api_version, response, args.async_)
    log.DeletedResource(
        registration_ref.Name(), 'registration', is_async=args.async_)
    return response
