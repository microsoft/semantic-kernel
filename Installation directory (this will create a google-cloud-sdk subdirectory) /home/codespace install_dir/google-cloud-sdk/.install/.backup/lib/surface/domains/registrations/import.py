# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""`gcloud domains registrations import` command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import flags
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util
from googlecloudsdk.command_lib.util.args import labels_util
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
class Import(base.CreateCommand):
  # pylint: disable=line-too-long
  """Import a domain from Google Domains registrar to Cloud Domains.

  Create a new Cloud Domains registration resource by importing an existing
  domain from Google Domains registrar.
  The new resource's ID will be equal to the domain name.

  After this command executes, a resource is created with state ACTIVE,
  indicating that the import was successful. Cloud Domains will automatically
  renew your domain as long as your Cloud Billing account is active. If this
  command fails, no resource is created.

  Other users may lose access to the domain and will need IAM permissions on the
  Cloud project containing the registration resource to regain access.

  ## EXAMPLES

  To import ``example.com'', run:

    $ {command} example.com
  """

  @staticmethod
  def Args(parser):
    resource_args.AddRegistrationResourceArg(
        parser, noun='The domain name', verb='to import')
    labels_util.AddCreateLabelsFlags(parser)
    flags.AddAsyncFlagToParser(parser)

  def Run(self, args):
    api_version = registrations.GetApiVersionFromArgs(args)
    client = registrations.RegistrationsClient(api_version)

    client.PrintSQSPAck()

    normalized = util.NormalizeResourceName(args.registration)
    if normalized != args.registration:
      console_io.PromptContinue(
          u'Domain name \'{}\' has been normalized to equivalent \'{}\'.'.format(
              args.registration, normalized),
          throw_if_unattended=False,
          cancel_on_no=True,
          default=True)
      args.registration = normalized

    registration_ref = args.CONCEPTS.registration.Parse()
    location_ref = registration_ref.Parent()
    labels = labels_util.ParseCreateArgs(
        args, client.messages.ImportDomainRequest.LabelsValue)

    response = client.Import(
        location_ref, registration_ref.registrationsId, labels=labels)

    response = util.WaitForOperation(api_version, response, args.async_)
    log.CreatedResource(
        registration_ref.Name(),
        'registration',
        args.async_)

    return response
