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
"""`gcloud domains registrations register` command."""

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


class Register(base.CreateCommand):
  # pylint: disable=line-too-long
  """Register a new domain.

  Create a new Cloud Domains registration resource by registering a new domain.
  The new resource's ID will be equal to the domain name.

  After this command executes, the resource will be in state
  REGISTRATION_PENDING. The registration process should complete in less than 5
  minutes. After that the resource will be in state ACTIVE. In rare
  cases this process can take much longer due, for example, to a downtime of the
  domain registry.

  Also in rare cases, the domain may end up in state REGISTRATION_FAILED. In
  that case, delete the registration resource and try again.

  When using Cloud DNS Zone or Google Domains name servers, DNSSEC will be
  enabled by default where possible. You can choose to not enable DNSSEC by
  using the --disable-dnssec flag.

  ## EXAMPLES

  To register ``example.com'' interactively, run:

    $ {command} example.com

  To register ``example.com'' using contact data from a YAML file
  ``contacts.yaml'', run:

    $ {command} example.com --contact-data-from-file=contacts.yaml

  To register ``example.com'' with interactive prompts disabled, provide
  --contact-data-from-file, --contact-privacy, --yearly-price flags and one of
  the flags for setting authoritative name servers. Sometimes also --notices
  flag is required. For example, run:

    $ {command} example.com --contact-data-from-file=contacts.yaml --contact-privacy=private-contact-data --yearly-price="12.00 USD" --cloud-dns-zone=example-com --quiet
  """

  @staticmethod
  def Args(parser):
    resource_args.AddRegistrationResourceArg(
        parser, noun='The domain name', verb='to register')
    flags.AddRegisterFlagsToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)
    flags.AddValidateOnlyFlagToParser(parser, 'create')
    flags.AddAsyncFlagToParser(parser)

  def _ValidateContacts(self, contacts):
    if contacts is None:
      raise exceptions.Error('Providing contacts is required.')
    for field in ['registrantContact', 'adminContact', 'technicalContact']:
      if not contacts.get_assigned_value(field):
        raise exceptions.Error('Providing {} is required.'.format(field))
    # TODO(b/166210862): Call Register with validate_only to check contacts.

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

    # First check if the domain is available, then parse all the parameters,
    # ask for price and only then ask for additional data.
    register_params = client.RetrieveRegisterParameters(
        location_ref, registration_ref.registrationsId)

    available_enum = client.messages.RegisterParameters.AvailabilityValueValuesEnum.AVAILABLE
    if register_params.availability != available_enum:
      raise exceptions.Error(
          'Domain \'{}\' is not available for registration: \'{}\''.format(
              registration_ref.registrationsId, register_params.availability))

    labels = labels_util.ParseCreateArgs(
        args, client.messages.Registration.LabelsValue)

    dns_settings, _ = dns_util.ParseDNSSettings(
        api_version,
        args.name_servers,
        args.cloud_dns_zone,
        args.use_google_domains_dns,
        None,
        registration_ref.registrationsId,
        enable_dnssec=not args.disable_dnssec)

    contacts = contacts_util.ParseContactData(api_version,
                                              args.contact_data_from_file)
    if contacts:
      self._ValidateContacts(contacts)

    contact_privacy = contacts_util.ParseContactPrivacy(api_version,
                                                        args.contact_privacy)
    yearly_price = util.ParseYearlyPrice(api_version, args.yearly_price)
    public_contacts_ack, hsts_ack = util.ParseRegisterNotices(args.notices)

    if yearly_price is None:
      yearly_price = util.PromptForYearlyPriceAck(register_params.yearlyPrice)
      if yearly_price is None:
        raise exceptions.Error('Accepting yearly price is required.')
    if not util.EqualPrice(yearly_price, register_params.yearlyPrice):
      raise exceptions.Error(
          'Incorrect yearly_price: \'{}\', expected: {}.'.format(
              util.TransformMoneyType(yearly_price),
              util.TransformMoneyType(register_params.yearlyPrice)))

    hsts_enum = client.messages.RegisterParameters.DomainNoticesValueListEntryValuesEnum.HSTS_PRELOADED
    if hsts_enum in register_params.domainNotices and not hsts_ack:
      hsts_ack = util.PromptForHSTSAck(register_params.domainName)
      if hsts_ack is None:
        raise exceptions.Error('Acceptance is required.')

    if dns_settings is None:
      dns_settings, _ = dns_util.PromptForNameServers(
          api_version,
          registration_ref.registrationsId,
          enable_dnssec=not args.disable_dnssec)
      if dns_settings is None:
        raise exceptions.Error('Providing DNS settings is required.')

    if contacts is None:
      contacts = contacts_util.PromptForContacts(api_version)
      self._ValidateContacts(contacts)

    if contact_privacy is None:
      choices = [
          flags.ContactPrivacyEnumMapper(client.messages).GetChoiceForEnum(enum)
          for enum in register_params.supportedPrivacy
      ]
      contact_privacy = contacts_util.PromptForContactPrivacy(
          api_version, choices)
      if contact_privacy is None:
        raise exceptions.Error('Providing Contact Privacy is required.')
    contacts.privacy = contact_privacy

    public_privacy_enum = client.messages.ContactSettings.PrivacyValueValuesEnum.PUBLIC_CONTACT_DATA
    if not public_contacts_ack and contact_privacy == public_privacy_enum:
      public_contacts_ack = contacts_util.PromptForPublicContactsAck(
          register_params.domainName, contacts)
      if public_contacts_ack is None:
        raise exceptions.Error('Acceptance is required.')

    response = client.Register(
        location_ref,
        registration_ref.registrationsId,
        dns_settings=dns_settings,
        contact_settings=contacts,
        yearly_price=yearly_price,
        hsts_notice_accepted=hsts_ack,
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
              'Note:\nThe domain is not yet registered.\n'
              'Wait until the registration resource changes state to ACTIVE.'))

    return response
