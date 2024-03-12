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
"""Contacts utilties for Cloud Domains commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from apitools.base.protorpclite import messages as _messages

from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.command_lib.domains import flags
from googlecloudsdk.command_lib.domains import util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_printer


def ParseContactData(api_version, path):
  """Parses contact data from a yaml file."""
  domains_messages = registrations.GetMessagesModule(api_version)

  class ContactData(_messages.Message):
    """Message that should be present in YAML file with contacts data."""

    # pylint: disable=invalid-name
    allContacts = _messages.MessageField(domains_messages.Contact, 1)
    registrantContact = _messages.MessageField(domains_messages.Contact, 2)
    adminContact = _messages.MessageField(domains_messages.Contact, 3)
    technicalContact = _messages.MessageField(domains_messages.Contact, 4)

  contacts = util.ParseMessageFromYamlFile(
      path, ContactData,
      'Contact data file \'{}\' does not contain valid contact messages'.format(
          path))
  if not contacts:
    return None

  parsed_contact = None
  if contacts.allContacts:
    for field in ['registrantContact', 'adminContact', 'technicalContact']:
      if contacts.get_assigned_value(field):
        raise exceptions.Error(
            ('Contact data file \'{}\' cannot contain both '
             'allContacts and {} fields.').format(path, field))
    parsed_contact = domains_messages.ContactSettings(
        registrantContact=contacts.allContacts,
        adminContact=contacts.allContacts,
        technicalContact=contacts.allContacts)
  else:
    parsed_contact = domains_messages.ContactSettings(
        registrantContact=contacts.registrantContact,
        adminContact=contacts.adminContact,
        technicalContact=contacts.technicalContact)

  return parsed_contact


def PromptForContacts(api_version, current_contacts=None):
  """Interactively prompts for Whois Contact information."""
  domains_messages = registrations.GetMessagesModule(api_version)

  create_call = (current_contacts is None)
  if not console_io.PromptContinue(
      'Contact data not provided using the --contact-data-from-file flag.',
      prompt_string='Do you want to enter it interactively',
      default=create_call):
    return None

  if create_call:
    contact = _PromptForSingleContact(domains_messages)
    return domains_messages.ContactSettings(
        registrantContact=contact,
        adminContact=contact,
        technicalContact=contact)

  choices = [
      'all the contacts to the same value', 'registrant contact',
      'admin contact', 'technical contact'
  ]
  # TODO(b/166210862): Make it a loop.
  index = console_io.PromptChoice(
      options=choices,
      cancel_option=True,
      default=0,
      message='Which contact do you want to change?')

  if index == 0:
    contact = _PromptForSingleContact(domains_messages,
                                      current_contacts.registrantContact)
    return domains_messages.ContactSettings(
        registrantContact=contact,
        adminContact=contact,
        technicalContact=contact)
  if index == 1:
    contact = _PromptForSingleContact(domains_messages,
                                      current_contacts.registrantContact)
    return domains_messages.ContactSettings(registrantContact=contact)
  if index == 2:
    contact = _PromptForSingleContact(domains_messages,
                                      current_contacts.adminContact)
    return domains_messages.ContactSettings(adminContact=contact)
  if index == 3:
    contact = _PromptForSingleContact(domains_messages,
                                      current_contacts.technicalContact)
    return domains_messages.ContactSettings(technicalContact=contact)
  return None


def _PromptForSingleContact(domains_messages, unused_current_contact=None):
  """Asks a user for a single contact data."""
  contact = domains_messages.Contact()
  contact.postalAddress = domains_messages.PostalAddress()

  # TODO(b/166210862): Use defaults from current_contact.
  #                      But then: How to clear a value?
  # TODO(b/166210862): Better validation: Call validate_only after each prompt.
  contact.postalAddress.recipients.append(
      util.PromptWithValidator(
          validator=util.ValidateNonEmpty,
          error_message=' Name must not be empty.',
          prompt_string='Full name:  '))
  contact.postalAddress.organization = console_io.PromptResponse(
      'Organization (if applicable):  ')
  contact.email = util.PromptWithValidator(
      validator=util.ValidateEmail,
      error_message=' Invalid email address.',
      prompt_string='Email',
      default=properties.VALUES.core.account.Get())
  contact.phoneNumber = util.PromptWithValidator(
      validator=util.ValidateNonEmpty,
      error_message=' Phone number must not be empty.',
      prompt_string='Phone number:  ',
      message='Enter phone number with country code, e.g. "+1.8005550123".')
  contact.faxNumber = util.Prompt(
      prompt_string='Fax number (if applicable):  ',
      message='Enter fax number with country code, e.g. "+1.8005550123".')
  contact.postalAddress.regionCode = util.PromptWithValidator(
      validator=util.ValidateRegionCode,
      error_message=(
          ' Country / Region code must be in ISO 3166-1 format, e.g. "US" or '
          '"PL".\n See https://support.google.com/business/answer/6270107 for a'
          ' list of valid choices.'),
      prompt_string='Country / Region code:  ',
      message='Enter two-letter Country / Region code, e.g. "US" or "PL".')
  if contact.postalAddress.regionCode != 'US':
    log.status.Print('Refer to the guidelines for entering address field '
                     'information at '
                     'https://support.google.com/business/answer/6397478.')
  contact.postalAddress.postalCode = console_io.PromptResponse(
      'Postal / ZIP code:  ')
  contact.postalAddress.administrativeArea = console_io.PromptResponse(
      'State / Administrative area (if applicable):  ')
  contact.postalAddress.locality = console_io.PromptResponse(
      'City / Locality:  ')
  contact.postalAddress.addressLines.append(
      util.PromptWithValidator(
          validator=util.ValidateNonEmpty,
          error_message=' Address Line 1 must not be empty.',
          prompt_string='Address Line 1:  '))

  optional_address_lines = []
  address_line_num = 2
  while len(optional_address_lines) < 4:
    address_line_num = 2 + len(optional_address_lines)
    address_line = console_io.PromptResponse(
        'Address Line {} (if applicable):  '.format(address_line_num))
    if not address_line:
      break
    optional_address_lines += [address_line]

  if optional_address_lines:
    contact.postalAddress.addressLines.extend(optional_address_lines)
  return contact


def ParseContactPrivacy(api_version, contact_privacy):
  domains_messages = registrations.GetMessagesModule(api_version)
  if contact_privacy is None:
    return None
  return flags.ContactPrivacyEnumMapper(domains_messages).GetEnumForChoice(
      contact_privacy)


def PromptForContactPrivacy(api_version, choices, current_privacy=None):
  """Asks a user for Contacts Privacy.

  Args:
    api_version: Cloud Domains API version to call.
    choices: List of privacy choices.
    current_privacy: Current privacy. Should be nonempty in update calls.

  Returns:
    Privacy enum or None if the user cancelled.
  """
  if not choices:
    raise exceptions.Error('Could not find supported contact privacy.')

  domains_messages = registrations.GetMessagesModule(api_version)
  # Sort the choices according to the privacy strength.
  choices.sort(key=flags.PrivacyChoiceStrength, reverse=True)

  if current_privacy:
    if len(choices) == 1:
      log.status.Print(
          'Your current contact privacy is {}. It cannot be changed.'.format(
              current_privacy))
      return None
    else:
      update = console_io.PromptContinue(
          'Your current contact privacy is {}.'.format(current_privacy),
          'Do you want to change it',
          default=False)
      if not update:
        return None

    current_choice = 0
    for ix, privacy in enumerate(choices):
      if privacy == flags.ContactPrivacyEnumMapper(
          domains_messages).GetChoiceForEnum(current_privacy):
        current_choice = ix
  else:
    current_choice = 0  # The strongest available privacy
  if len(choices) == 1:
    ack = console_io.PromptContinue(
        'The only supported contact privacy is {}.'.format(choices[0]),
        default=True)
    if not ack:
      return None
    return ParseContactPrivacy(api_version, choices[0])
  else:
    index = console_io.PromptChoice(
        options=choices,
        default=current_choice,
        message='Specify contact privacy')
    return ParseContactPrivacy(api_version, choices[index])


def ParsePublicContactsAck(api_version, notices):
  """Parses Contact Notices. Returns public_contact_ack enum or None."""
  domains_messages = registrations.GetMessagesModule(api_version)

  if notices is None:
    return False
  for notice in notices:
    enum = flags.ContactNoticeEnumMapper(domains_messages).GetEnumForChoice(
        notice)
    # pylint: disable=line-too-long
    if enum == domains_messages.ConfigureContactSettingsRequest.ContactNoticesValueListEntryValuesEnum.PUBLIC_CONTACT_DATA_ACKNOWLEDGEMENT:
      return enum

  return None


def MergeContacts(api_version, prev_contacts, new_contacts):
  domains_messages = registrations.GetMessagesModule(api_version)
  if new_contacts is None:
    new_contacts = domains_messages.ContactSettings()

  return domains_messages.ContactSettings(
      registrantContact=(new_contacts.registrantContact or
                         prev_contacts.registrantContact),
      adminContact=(new_contacts.adminContact or prev_contacts.adminContact),
      technicalContact=(new_contacts.technicalContact or
                        prev_contacts.technicalContact))


def _SimplifyContacts(contacts):
  """Returns one contact if all 3 contacts are equal, and all 3 contacts otherwise."""
  if contacts.registrantContact == contacts.adminContact and contacts.registrantContact == contacts.technicalContact:
    return contacts.registrantContact
  return contacts


def PromptForPublicContactsAck(domain, contacts, print_format='default'):
  """Asks a user for Public Contacts Ack.

  Args:
    domain: Domain name.
    contacts: Current Contacts. All 3 contacts should be present.
    print_format: Print format, e.g. 'default' or 'yaml'.

  Returns:
    Boolean: whether the user accepted the notice or not.
  """
  log.status.Print(
      'You choose to make contact data of domain {} public.\n'
      'Anyone who looks it up in the WHOIS directory will be able to see info\n'
      'for the domain owner and administrative and technical contacts.\n'
      'Make sure it\'s ok with them that their contact data is public.\n'
      'This info will be publicly available:'.format(domain))
  contacts = _SimplifyContacts(contacts)
  resource_printer.Print(contacts, print_format, out=sys.stderr)

  return console_io.PromptContinue(
      message=None, default=False, throw_if_unattended=True, cancel_on_no=True)
  # TODO(b/110398579): Integrate with ARI.
