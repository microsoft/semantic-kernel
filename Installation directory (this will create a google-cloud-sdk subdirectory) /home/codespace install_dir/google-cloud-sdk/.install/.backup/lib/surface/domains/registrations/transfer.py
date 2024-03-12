# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""`gcloud domains registrations transfer` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import contacts_util
from googlecloudsdk.command_lib.domains import dns_util
from googlecloudsdk.command_lib.domains import flags
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions
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
class Transfer(base.CreateCommand):
  # pylint: disable=line-too-long
  """Transfer a domain from another registrar.

  Create a new Cloud Domains registration resource by transferring an existing
  domain from another registrar.
  The new resource's ID will be equal to the domain name.

  After this command executes, the resource will be in state
  TRANSFER_PENDING. To complete the transfer, the registrant may need to approve
  the transfer through an email sent by the current registrar. Domain transfers
  can take 5-7 days to complete. After the transfer is completed, the resource
  transitions to state ACTIVE, indicating that the transfer was successful. If
  the transfer is rejected or the request expires without being approved, the
  resource ends up in state TRANSFER_FAILED. If the transfer fails, you can
  safely delete the resource and retry the transfer. Transfers in state
  TRANSFER_PENDING can also be cancelled with the delete command.

  ## EXAMPLES

  To transfer ``example.com'' interactively, run:

    $ {command} example.com

  To transfer ``example.com'' using contact data from a YAML file
  ``contacts.yaml'', run:

    $ {command} example.com --contact-data-from-file=contacts.yaml

  To transfer ``example.com'' with interactive prompts disabled, provide
  --authorization-code-from-file, --contact-data-from-file, --contact-privacy,
  --yearly-price flags and one of the flags for setting authoritative name
  servers. Sometimes also --notices flag is required.
  """

  @staticmethod
  def Args(parser):
    resource_args.AddRegistrationResourceArg(
        parser, noun='The domain name', verb='to transfer')
    flags.AddTransferFlagsToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)
    flags.AddValidateOnlyFlagToParser(parser, verb='transfer', noun='domain')
    flags.AddAsyncFlagToParser(parser)

  def _ValidateContacts(self, contacts):
    if contacts is None:
      raise exceptions.Error('Providing contacts is required.')
    for field in ['registrantContact', 'adminContact', 'technicalContact']:
      if not contacts.get_assigned_value(field):
        raise exceptions.Error('Providing {} is required.'.format(field))
    # TODO(b/166210862): Call Transfer with validate_only to check contacts.

  def Run(self, args):
    api_version = registrations.GetApiVersionFromArgs(args)
    client = registrations.RegistrationsClient(api_version)

    client.PrintSQSPAck()

    normalized = util.NormalizeResourceName(args.registration)
    if normalized != args.registration:
      console_io.PromptContinue(
          'Domain name \'{}\' has been normalized to equivalent \'{}\'.'.format(
              args.registration, normalized),
          throw_if_unattended=False,
          cancel_on_no=True,
          default=True)
      args.registration = normalized

    registration_ref = args.CONCEPTS.registration.Parse()
    location_ref = registration_ref.Parent()

    # First check if the domain is available for transfer, then parse all the
    # parameters, ask for price and only then ask for additional data.
    transfer_params = client.RetrieveTransferParameters(
        location_ref, registration_ref.registrationsId)

    locked_enum = client.messages.TransferParameters.TransferLockStateValueValuesEnum.LOCKED
    if transfer_params.transferLockState == locked_enum:
      raise exceptions.Error(
          'Domains must be unlocked before transferring. Transfer lock state: {}'
          .format(transfer_params.transferLockState))

    auth_code = util.ReadFileContents(args.authorization_code_from_file)

    labels = labels_util.ParseCreateArgs(
        args, client.messages.Registration.LabelsValue)

    dns_settings = None
    if not args.keep_dns_settings:
      # Assume DNSSEC is off following transfer when changing name servers.
      dns_settings, _ = dns_util.ParseDNSSettings(
          api_version,
          None,
          args.cloud_dns_zone,
          args.use_google_domains_dns,
          None,
          registration_ref.registrationsId,
          enable_dnssec=False)

    contacts = contacts_util.ParseContactData(api_version,
                                              args.contact_data_from_file)
    if contacts:
      self._ValidateContacts(contacts)

    contact_privacy = contacts_util.ParseContactPrivacy(api_version,
                                                        args.contact_privacy)
    yearly_price = util.ParseYearlyPrice(api_version, args.yearly_price)

    # Ignore HSTS notices for transfer.
    public_contacts_ack, _ = util.ParseRegisterNotices(args.notices)

    if auth_code is None:
      # TODO(b/186472865): Handle transfers without auth codes e.g. co.uk.
      auth_code = util.PromptForAuthCode()

    if yearly_price is None:
      yearly_price = util.PromptForYearlyPriceAck(transfer_params.yearlyPrice)
      if yearly_price is None:
        raise exceptions.Error('Accepting yearly price is required.')
    if not util.EqualPrice(yearly_price, transfer_params.yearlyPrice):
      raise exceptions.Error(
          'Incorrect yearly_price: \'{}\', expected: {}.'.format(
              util.TransformMoneyType(yearly_price),
              util.TransformMoneyType(transfer_params.yearlyPrice)))

    keep_dns_settings = args.keep_dns_settings
    if dns_settings is None and not keep_dns_settings:
      # Assume DNSSEC is off following transfer when changing name servers.
      dns_settings, _, keep_dns_settings = dns_util.PromptForNameServersTransfer(
          api_version, registration_ref.registrationsId)
      if dns_settings is None and not keep_dns_settings:
        raise exceptions.Error('Providing DNS settings is required.')

    if contacts is None:
      contacts = contacts_util.PromptForContacts(api_version)
      self._ValidateContacts(contacts)

    if contact_privacy is None:
      choices = [
          flags.ContactPrivacyEnumMapper(client.messages).GetChoiceForEnum(enum)
          for enum in transfer_params.supportedPrivacy
      ]
      contact_privacy = contacts_util.PromptForContactPrivacy(
          api_version, choices)
      if contact_privacy is None:
        raise exceptions.Error('Providing Contact Privacy is required.')
    contacts.privacy = contact_privacy

    public_privacy_enum = client.messages.ContactSettings.PrivacyValueValuesEnum.PUBLIC_CONTACT_DATA
    if not public_contacts_ack and contact_privacy == public_privacy_enum:
      public_contacts_ack = contacts_util.PromptForPublicContactsAck(
          transfer_params.domainName, contacts)
      if public_contacts_ack is None:
        raise exceptions.Error('Acceptance is required.')

    response = client.Transfer(
        location_ref,
        registration_ref.registrationsId,
        dns_settings=dns_settings,
        contact_settings=contacts,
        authorization_code=auth_code.strip(),
        yearly_price=yearly_price,
        public_privacy_accepted=public_contacts_ack,
        labels=labels,
        validate_only=args.validate_only)

    if args.validate_only:
      log.status.Print('The command will not have any effect because '
                       'validate-only flag is present.')
    else:
      response = util.WaitForOperation(api_version, response, args.async_)
      log.CreatedResource(
          registration_ref.Name(),
          'registration',
          args.async_,
          details=(
              'Note:\nThe domain transfer has been initiated, but is not yet '
              'complete. The registrant may need to follow instructions in a '
              'transfer confirmation email sent by the current registrar in '
              'order for the transfer to proceed. Even after confirmation, '
              'transfers can sometimes take several days to complete. The '
              'transfer will be complete when the registration resource changes'
              ' state to ACTIVE.'))

    return response
