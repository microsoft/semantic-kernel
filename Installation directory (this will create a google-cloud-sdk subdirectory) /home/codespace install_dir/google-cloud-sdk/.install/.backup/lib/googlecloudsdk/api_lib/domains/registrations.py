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
"""API client library for Cloud Domains Registrations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log

ALPHA_API_VERSION = 'v1alpha2'
BETA_API_VERSION = 'v1beta1'
GA_API_VERSION = 'v1'


def GetApiVersionFromArgs(args):
  """Return API version based on args."""
  release_track = args.calliope_command.ReleaseTrack()
  if release_track == base.ReleaseTrack.ALPHA:
    return ALPHA_API_VERSION
  if release_track == base.ReleaseTrack.BETA:
    return BETA_API_VERSION
  if release_track == base.ReleaseTrack.GA:
    return GA_API_VERSION
  raise exceptions.UnsupportedReleaseTrackError(release_track)


def GetClientInstance(api_version):
  return apis.GetClientInstance('domains', api_version)


def GetMessagesModule(api_version, client=None):
  client = client or GetClientInstance(api_version)
  return client.MESSAGES_MODULE


class RegistrationsClient(object):
  """Client for registrations service in the Cloud Domains API."""

  def __init__(self, api_version, client=None, messages=None):
    self.client = client or GetClientInstance(api_version)
    self.messages = messages or GetMessagesModule(api_version, client)
    self._service = self.client.projects_locations_registrations

  def PrintSQSPAck(self):
    """Prints FYI acknowledgement about the Google Domains - Squarespace deal.
    """
    ack_message = (
        'Domain name registration services are provided by Squarespace '
        '(https://domains.squarespace.com),\n'
        'pursuant to the Squarespace Terms of Service '
        '(https://www.squarespace.com/terms-of-service)\n'
        'and Squarespace Domain Registration Agreement '
        '(https://www.squarespace.com/domain-registration-agreement),\n'
        'which Google resells pursuant to an agreement with Squarespace.\n'
        'Initially, Google will manage your domain(s) on Squarespace\'s behalf.'
        ' Once your domain is transitioned to Squarespace,\n'
        'Google will share your name, contact information, and other '
        'domain-related information with Squarespace.\n'
        'You can review Squarespace\'s Privacy Policy '
        '(https://www.squarespace.com/privacy) for details on how they '
        'process your information.\n'
        'Google\'s Privacy Policy (https://policies.google.com/privacy) '
        'describes how Google handles this information as a reseller.\n'
        'By choosing to continue, you (1) acknowledge receipt of Google\'s '
        'Privacy Policy and direct us to share this information\n'
        'with Squarespace; and (2) agree to the Squarespace Terms of Service '
        '(https://www.squarespace.com/terms-of-service) and\n'
        'Squarespace Domain Registration Agreement '
        '(https://www.squarespace.com/domain-registration-agreement), and\n'
        'acknowledge receipt of Squarespace\'s Privacy Policy '
        '(https://www.squarespace.com/privacy).\n'
    )

    log.status.Print(ack_message)

  def Register(
      self,
      parent_ref,
      domain,
      dns_settings,
      contact_settings,
      yearly_price,
      labels=None,
      hsts_notice_accepted=False,
      public_privacy_accepted=False,
      validate_only=False,
  ):
    """Creates a Registration.

    Args:
      parent_ref: a Resource reference to a domains.projects.locations resource
        for the parent of this registration.
      domain: str, the name of the domain to register. Used as resource name.
      dns_settings: DnsSettings to be used.
      contact_settings: ContactSettings to be used.
      yearly_price: price for the domain registration and its cost for the
        following years.
      labels: Unified GCP Labels for the resource.
      hsts_notice_accepted: bool, Whether HSTS notice was presented & accepted.
      public_privacy_accepted: bool, Whether public privacy notice was presented
        & accepted.
      validate_only: If set to true, performs only validation, without creating.

    Returns:
      Operation: the long running operation to register a domain.
    """
    domain_notices = []
    if hsts_notice_accepted:
      domain_notices = [
          self.messages.RegisterDomainRequest
          .DomainNoticesValueListEntryValuesEnum.HSTS_PRELOADED
      ]
    contact_notices = []
    if public_privacy_accepted:
      contact_notices = [
          self.messages.RegisterDomainRequest
          .ContactNoticesValueListEntryValuesEnum
          .PUBLIC_CONTACT_DATA_ACKNOWLEDGEMENT
      ]
    req = self.messages.DomainsProjectsLocationsRegistrationsRegisterRequest(
        parent=parent_ref.RelativeName(),
        registerDomainRequest=self.messages.RegisterDomainRequest(
            registration=self.messages.Registration(
                domainName=domain,
                dnsSettings=dns_settings,
                contactSettings=contact_settings,
                labels=labels),
            domainNotices=domain_notices,
            contactNotices=contact_notices,
            yearlyPrice=yearly_price,
            validateOnly=validate_only))

    return self._service.Register(req)

  def Transfer(self,
               parent_ref,
               domain,
               dns_settings,
               contact_settings,
               authorization_code,
               yearly_price,
               labels=None,
               public_privacy_accepted=False,
               validate_only=False):
    """Transfers a domain and creates a new Registration.

    Args:
      parent_ref: a Resource reference to a domains.projects.locations resource
        for the parent of this registration.
      domain: str, the name of the domain to transfer. Used as resource name.
      dns_settings: DnsSettings to be used.
      contact_settings: ContactSettings to be used.
      authorization_code: The authorization code needed to transfer the domain.
      yearly_price: price for the domain transfer and its cost for the following
        years.
      labels: Unified GCP Labels for the resource.
      public_privacy_accepted: bool, Whether public privacy notice was presented
        & accepted.
      validate_only: If set to true, performs only validation, without
        transferring.

    Returns:
      Operation: the long running operation to transfer a domain.
    """
    contact_notices = []
    if public_privacy_accepted:
      contact_notices = [
          self.messages.TransferDomainRequest
          .ContactNoticesValueListEntryValuesEnum
          .PUBLIC_CONTACT_DATA_ACKNOWLEDGEMENT
      ]

    registration = self.messages.Registration(
        domainName=domain,
        dnsSettings=dns_settings,
        contactSettings=contact_settings,
        labels=labels)

    req = self.messages.DomainsProjectsLocationsRegistrationsTransferRequest(
        parent=parent_ref.RelativeName(),
        transferDomainRequest=self.messages.TransferDomainRequest(
            registration=registration,
            contactNotices=contact_notices,
            authorizationCode=self.messages.AuthorizationCode(
                code=authorization_code),
            yearlyPrice=yearly_price,
            validateOnly=validate_only))

    return self._service.Transfer(req)

  def Import(self, parent_ref, domain, labels):
    """Imports a domain and creates a new Registration.

    Args:
      parent_ref: a Resource reference to a domains.projects.locations resource
        for the parent of this registration.
      domain: str, the name of the domain to import. Used as resource name.
      labels: Unified GCP Labels for the resource.

    Returns:
      Operation: the long running operation to import a domain.
    """
    req = self.messages.DomainsProjectsLocationsRegistrationsImportRequest(
        parent=parent_ref.RelativeName(),
        importDomainRequest=self.messages.ImportDomainRequest(
            domainName=domain, labels=labels))
    return self._service.Import(req)

  def Export(self, registration_ref):
    req = self.messages.DomainsProjectsLocationsRegistrationsExportRequest(
        name=registration_ref.RelativeName())
    return self._service.Export(req)

  def Delete(self, registration_ref):
    req = self.messages.DomainsProjectsLocationsRegistrationsDeleteRequest(
        name=registration_ref.RelativeName())
    return self._service.Delete(req)

  def Get(self, registration_ref):
    get_req = self.messages.DomainsProjectsLocationsRegistrationsGetRequest(
        name=registration_ref.RelativeName())
    return self._service.Get(get_req)

  def RetrieveAuthorizationCode(self, registration_ref):
    # pylint: disable=line-too-long
    req = self.messages.DomainsProjectsLocationsRegistrationsRetrieveAuthorizationCodeRequest(
        registration=registration_ref.RelativeName())
    return self._service.RetrieveAuthorizationCode(req)

  def ResetAuthorizationCode(self, registration_ref):
    # pylint: disable=line-too-long
    req = self.messages.DomainsProjectsLocationsRegistrationsResetAuthorizationCodeRequest(
        registration=registration_ref.RelativeName())
    return self._service.ResetAuthorizationCode(req)

  def RetrieveImportableDomains(self,
                                parent_ref,
                                limit=None,
                                page_size=None,
                                batch_size=None):
    request = self.messages.DomainsProjectsLocationsRegistrationsRetrieveImportableDomainsRequest(
        location=parent_ref.RelativeName(), pageSize=page_size)

    return list_pager.YieldFromList(
        self._service,
        request,
        method='RetrieveImportableDomains',
        field='domains',
        limit=limit,
        batch_size=batch_size,
        batch_size_attribute='pageSize',
    )

  def List(self, parent_ref, limit=None, page_size=None, list_filter=None):
    """List the domain registrations in a given project.

    Args:
      parent_ref: a Resource reference to a domains.projects.locations resource
        to list registrations for.
      limit: int, the total number of results to return from the API.
      page_size: int, the number of results in each batch from the API.
      list_filter: str, filter to apply in the list request.

    Returns:
      A generator of the domain registrations in the project.
    """
    list_req = self.messages.DomainsProjectsLocationsRegistrationsListRequest(
        parent=parent_ref.RelativeName(), filter=list_filter)
    return list_pager.YieldFromList(
        self._service,
        list_req,
        batch_size=page_size,
        limit=limit,
        field='registrations',
        batch_size_attribute='pageSize')

  def Patch(self, registration_ref, labels=None):
    """Updates a Registration.

    Used for updating labels.

    Args:
      registration_ref: a Resource reference to a
        domains.projects.locations.registrations resource.
      labels: Unified GCP Labels for the resource.

    Returns:
      Operation: the long running operation to patch registration.
    """
    registration = self.messages.Registration()
    registration.labels = labels
    update_mask = 'labels'

    patch_req = self.messages.DomainsProjectsLocationsRegistrationsPatchRequest(
        registration=registration,
        name=registration_ref.RelativeName(),
        updateMask=update_mask)

    return self._service.Patch(patch_req)

  def ConfigureManagement(
      self, registration_ref, transfer_lock, preferred_renewal_method
  ):
    """Updates management settings.

    Args:
      registration_ref: a Resource reference to a
        domains.projects.locations.registrations resource.
      transfer_lock: The transfer lock state.
      preferred_renewal_method: The preferred Renewal Method.

    Returns:
      Operation: the long running operation to configure management
        registration.
    """
    management_settings = self.messages.ManagementSettings(
        transferLockState=transfer_lock,
        preferredRenewalMethod=preferred_renewal_method,
    )

    updated_list = []
    if transfer_lock:
      updated_list += ['transfer_lock_state']
    if preferred_renewal_method:
      updated_list += ['preferred_renewal_method']
    update_mask = ','.join(updated_list)
    # pylint: disable=line-too-long
    req = self.messages.DomainsProjectsLocationsRegistrationsConfigureManagementSettingsRequest(
        registration=registration_ref.RelativeName(),
        configureManagementSettingsRequest=self.messages.ConfigureManagementSettingsRequest(
            managementSettings=management_settings, updateMask=update_mask
        ),
    )

    return self._service.ConfigureManagementSettings(req)

  def ConfigureDNS(self, registration_ref, dns_settings, updated,
                   validate_only):
    """Calls ConfigureDNSSettings method.

    Args:
      registration_ref: Registration resource reference.
      dns_settings: New DNS Settings.
      updated: dns_util.DnsUpdateMask object representing an update mask.
      validate_only: validate_only flag.

    Returns:
      Long Running Operation reference.
    """

    updated_list = []
    if updated.glue_records:
      updated_list += ['glue_records']
    if updated.google_domains_dnssec:
      if updated.name_servers:
        updated_list += ['google_domains_dns']
      else:
        updated_list += ['google_domains_dns.ds_state']
    if updated.custom_dnssec:
      if updated.name_servers:
        updated_list += ['custom_dns']
      else:
        updated_list += ['custom_dns.ds_records']
    update_mask = ','.join(updated_list)

    # pylint: disable=line-too-long
    req = self.messages.DomainsProjectsLocationsRegistrationsConfigureDnsSettingsRequest(
        registration=registration_ref.RelativeName(),
        configureDnsSettingsRequest=self.messages.ConfigureDnsSettingsRequest(
            dnsSettings=dns_settings,
            updateMask=update_mask,
            validateOnly=validate_only))

    return self._service.ConfigureDnsSettings(req)

  def ConfigureContacts(self, registration_ref, contacts, contact_privacy,
                        public_contacts_ack, validate_only):
    """Calls ConfigureContactSettings method.

    Args:
      registration_ref: Registration resource reference.
      contacts: New Contacts.
      contact_privacy: New Contact privacy.
      public_contacts_ack: Whether the user accepted public privacy.
      validate_only: validate_only flag.

    Returns:
      Long Running Operation reference.
    """
    updated_list = []
    if contact_privacy:
      updated_list += ['privacy']

    if contacts is None:
      contact_settings = self.messages.ContactSettings(privacy=contact_privacy)
    else:
      contact_settings = self.messages.ContactSettings(
          privacy=contact_privacy,
          registrantContact=contacts.registrantContact,
          adminContact=contacts.adminContact,
          technicalContact=contacts.technicalContact)

      if contacts.registrantContact:
        updated_list += ['registrant_contact']
      if contacts.adminContact:
        updated_list += ['admin_contact']
      if contacts.technicalContact:
        updated_list += ['technical_contact']

    update_mask = ','.join(updated_list)

    notices = []
    if public_contacts_ack:
      notices = [
          self.messages.ConfigureContactSettingsRequest
          .ContactNoticesValueListEntryValuesEnum
          .PUBLIC_CONTACT_DATA_ACKNOWLEDGEMENT
      ]

    # pylint: disable=line-too-long
    req = self.messages.DomainsProjectsLocationsRegistrationsConfigureContactSettingsRequest(
        registration=registration_ref.RelativeName(),
        configureContactSettingsRequest=self.messages
        .ConfigureContactSettingsRequest(
            contactSettings=contact_settings,
            updateMask=update_mask,
            contactNotices=notices,
            validateOnly=validate_only))

    return self._service.ConfigureContactSettings(req)

  def ConfigureRegistrantEmail(self, registration_ref, registrant_email):
    """Sets a registrant contact.

    This resends registrant email confirmation.
    It's done by updating registrant email to the current value.

    Args:
      registration_ref: a Resource reference to a
        domains.projects.locations.registrations resource.
      registrant_email: The registrant email.

    Returns:
      Operation: the long running operation to configure contacts registration.
    """
    contact_settings = self.messages.ContactSettings(
        registrantContact=self.messages.Contact(email=registrant_email))

    # pylint: disable=line-too-long
    req = self.messages.DomainsProjectsLocationsRegistrationsConfigureContactSettingsRequest(
        registration=registration_ref.RelativeName(),
        configureContactSettingsRequest=self.messages
        .ConfigureContactSettingsRequest(
            contactSettings=contact_settings,
            updateMask='registrant_contact.email'))

    return self._service.ConfigureContactSettings(req)

  def RetrieveRegisterParameters(self, parent_ref, domain):
    # pylint: disable=line-too-long
    request = self.messages.DomainsProjectsLocationsRegistrationsRetrieveRegisterParametersRequest(
        location=parent_ref.RelativeName(), domainName=domain)
    return self._service.RetrieveRegisterParameters(request).registerParameters

  def RetrieveTransferParameters(self, parent_ref, domain):
    # pylint: disable=line-too-long
    request = self.messages.DomainsProjectsLocationsRegistrationsRetrieveTransferParametersRequest(
        location=parent_ref.RelativeName(), domainName=domain)
    return self._service.RetrieveTransferParameters(request).transferParameters

  def SearchDomains(self, parent_ref, query):
    # pylint: disable=line-too-long
    request = self.messages.DomainsProjectsLocationsRegistrationsSearchDomainsRequest(
        location=parent_ref.RelativeName(), query=query)
    return self._service.SearchDomains(request).registerParameters
