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
"""DNS utilties for Cloud Domains commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.dns import util as dns_api_util
from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.domains import util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_printer
import six


class DnsUpdateMask(object):
  """Class with information which parts of dns_settings should be updated."""

  def __init__(self,
               name_servers=False,
               glue_records=False,
               google_domains_dnssec=False,
               custom_dnssec=False):
    self.name_servers = name_servers
    self.glue_records = glue_records
    self.google_domains_dnssec = google_domains_dnssec
    self.custom_dnssec = custom_dnssec


def ParseDNSSettings(api_version,
                     name_servers,
                     cloud_dns_zone,
                     use_google_domains_dns,
                     dns_settings_from_file,
                     domain,
                     enable_dnssec=True,
                     dns_settings=None):
  """Parses DNS settings from a flag.

  At most one of the arguments (except domain) should be non-empty.

  Args:
    api_version: Cloud Domains API version to call.
    name_servers: List of name servers
    cloud_dns_zone: Cloud DNS Zone name
    use_google_domains_dns: Information that Google Domains name servers should
      be used.
    dns_settings_from_file: Path to a yaml file with dns_settings.
    domain: Domain name corresponding to the DNS settings.
    enable_dnssec: Enable DNSSEC for Google Domains name servers or Cloud DNS
      Zone.
    dns_settings: Current DNS settings. Used during Configure DNS only.

  Returns:
    A pair: (messages.DnsSettings, DnsUpdateMask) to be updated, or (None, None)
    if all the arguments are empty.
  """
  domains_messages = registrations.GetMessagesModule(api_version)
  if name_servers is not None:
    return _CustomNameServers(domains_messages, name_servers)
  if cloud_dns_zone is not None:
    nameservers, ds_records = _GetCloudDnsDetails(domains_messages,
                                                  cloud_dns_zone, domain,
                                                  enable_dnssec)
    return _CustomNameServers(domains_messages, nameservers, ds_records)
  if use_google_domains_dns:
    return _GoogleDomainsNameServers(domains_messages, enable_dnssec)
  if dns_settings_from_file is not None:
    return _ParseDnsSettingsFromFile(domains_messages, dns_settings_from_file)
  if dns_settings is not None and not enable_dnssec:
    return _DisableDnssec(domains_messages, dns_settings)
  return None, None


def _CustomNameServers(domains_messages, name_servers, ds_records=None):
  """Validates name servers and returns (dns_settings, update_mask)."""
  if not ds_records:
    ds_records = []
  normalized_name_servers = list(map(util.NormalizeDomainName, name_servers))
  for ns, normalized in zip(name_servers, normalized_name_servers):
    if not util.ValidateDomainName(normalized):
      raise exceptions.Error('Invalid name server: \'{}\'.'.format(ns))
  update_mask = DnsUpdateMask(name_servers=True, custom_dnssec=True)
  dns_settings = domains_messages.DnsSettings(
      customDns=domains_messages.CustomDns(
          nameServers=normalized_name_servers, dsRecords=ds_records))
  return dns_settings, update_mask


def _GoogleDomainsNameServers(domains_messages, enable_dnssec):
  """Enable Google Domains name servers and returns (dns_settings, update_mask)."""
  update_mask = DnsUpdateMask(name_servers=True, google_domains_dnssec=True)
  ds_state = domains_messages.GoogleDomainsDns.DsStateValueValuesEnum.DS_RECORDS_PUBLISHED
  if not enable_dnssec:
    ds_state = domains_messages.GoogleDomainsDns.DsStateValueValuesEnum.DS_RECORDS_UNPUBLISHED
  dns_settings = domains_messages.DnsSettings(
      googleDomainsDns=domains_messages.GoogleDomainsDns(dsState=ds_state))
  return dns_settings, update_mask


def _ParseDnsSettingsFromFile(domains_messages, path):
  """Parses dns_settings from a yaml file.

  Args:
    domains_messages: Cloud Domains messages module.
    path: YAML file path.

  Returns:
    Pair (DnsSettings, DnsUpdateMask) or (None, None) if path is None.
  """
  dns_settings = util.ParseMessageFromYamlFile(
      path, domains_messages.DnsSettings,
      'DNS settings file \'{}\' does not contain valid dns_settings message'
      .format(path))
  if not dns_settings:
    return None, None

  update_mask = None
  if dns_settings.googleDomainsDns is not None:
    update_mask = DnsUpdateMask(
        name_servers=True, google_domains_dnssec=True, glue_records=True)
  elif dns_settings.customDns is not None:
    update_mask = DnsUpdateMask(
        name_servers=True, custom_dnssec=True, glue_records=True)
  else:
    raise exceptions.Error(
        'dnsProvider is not present in DNS settings file \'{}\'.'.format(path))

  return dns_settings, update_mask


def _GetCloudDnsDetails(domains_messages, cloud_dns_zone, domain,
                        enable_dnssec):
  """Fetches list of name servers from provided Cloud DNS Managed Zone.

  Args:
    domains_messages: Cloud Domains messages module.
    cloud_dns_zone: Cloud DNS Zone resource reference.
    domain: Domain name.
    enable_dnssec: If true, try to read DNSSEC information from the Zone.

  Returns:
    A pair: List of name servers and a list of Ds records (or [] if e.g. the
    Zone is not signed).
  """
  # Get the managed-zone.
  dns_api_version = 'v1'
  dns = apis.GetClientInstance('dns', dns_api_version)
  dns_messages = dns.MESSAGES_MODULE
  zone_ref = dns_api_util.GetRegistry(dns_api_version).Parse(
      cloud_dns_zone,
      params={
          'project': properties.VALUES.core.project.GetOrFail,
      },
      collection='dns.managedZones')

  try:
    zone = dns.managedZones.Get(
        dns_messages.DnsManagedZonesGetRequest(
            project=zone_ref.project, managedZone=zone_ref.managedZone))
  except apitools_exceptions.HttpError as error:
    raise calliope_exceptions.HttpException(error)
  domain_with_dot = domain + '.'
  if zone.dnsName != domain_with_dot:
    raise exceptions.Error(
        'The dnsName \'{}\' of specified Cloud DNS zone \'{}\' does not match the '
        'registration domain \'{}\''.format(zone.dnsName, cloud_dns_zone,
                                            domain_with_dot))
  if zone.visibility != dns_messages.ManagedZone.VisibilityValueValuesEnum.public:
    raise exceptions.Error(
        'Cloud DNS Zone \'{}\' is not public.'.format(cloud_dns_zone))

  if not enable_dnssec:
    return zone.nameServers, []

  signed = dns_messages.ManagedZoneDnsSecConfig.StateValueValuesEnum.on
  if not zone.dnssecConfig or zone.dnssecConfig.state != signed:
    log.status.Print(
        'Cloud DNS Zone \'{}\' is not signed. DNSSEC won\'t be enabled.'.format(
            cloud_dns_zone))
    return zone.nameServers, []
  try:
    dns_keys = []
    req = dns_messages.DnsDnsKeysListRequest(
        project=zone_ref.project,
        managedZone=zone_ref.managedZone)
    while True:
      resp = dns.dnsKeys.List(req)
      dns_keys += resp.dnsKeys
      req.pageToken = resp.nextPageToken
      if not resp.nextPageToken:
        break
  except apitools_exceptions.HttpError as error:
    log.status.Print('Cannot read DS records from Cloud DNS Zone \'{}\': {}. '
                     'DNSSEC won\'t be enabled.'.format(cloud_dns_zone, error))
  ds_records = _ConvertDnsKeys(domains_messages, dns_messages, dns_keys)
  if not ds_records:
    log.status.Print('No supported DS records found in Cloud DNS Zone \'{}\'. '
                     'DNSSEC won\'t be enabled.'.format(cloud_dns_zone))
    return zone.nameServers, []
  return zone.nameServers, ds_records


def _ConvertDnsKeys(domains_messages, dns_messages, dns_keys):
  """Converts DnsKeys to DsRecords."""
  ds_records = []
  for key in dns_keys:
    if key.type != dns_messages.DnsKey.TypeValueValuesEnum.keySigning:
      continue
    if not key.isActive:
      continue
    try:
      algorithm = domains_messages.DsRecord.AlgorithmValueValuesEnum(
          six.text_type(key.algorithm).upper())
      for d in key.digests:
        digest_type = domains_messages.DsRecord.DigestTypeValueValuesEnum(
            six.text_type(d.type).upper())
        ds_records.append(
            domains_messages.DsRecord(
                keyTag=key.keyTag,
                digest=d.digest,
                algorithm=algorithm,
                digestType=digest_type))
    except TypeError:
      continue  # Ignore unsupported algorithms and digest types.
  return ds_records


def _DisableDnssec(domains_messages, dns_settings):
  """Returns DNS settings (and update mask) with DNSSEC disabled."""
  if dns_settings is None:
    return None, None
  if dns_settings.googleDomainsDns is not None:
    updated_dns_settings = domains_messages.DnsSettings(
        googleDomainsDns=domains_messages.GoogleDomainsDns(
            dsState=domains_messages.GoogleDomainsDns.DsStateValueValuesEnum
            .DS_RECORDS_UNPUBLISHED))
    update_mask = DnsUpdateMask(google_domains_dnssec=True)
  elif dns_settings.customDns is not None:
    updated_dns_settings = domains_messages.DnsSettings(
        customDns=domains_messages.CustomDns(dsRecords=[]))
    update_mask = DnsUpdateMask(custom_dnssec=True)
  else:
    return None, None
  return updated_dns_settings, update_mask


def PromptForNameServers(api_version,
                         domain,
                         enable_dnssec=None,
                         dns_settings=None,
                         print_format='default'):
  """Asks the user to provide DNS settings interactively.

  Args:
    api_version: Cloud Domains API version to call.
    domain: Domain name corresponding to the DNS settings.
    enable_dnssec: Should the DNSSEC be enabled.
    dns_settings: Current DNS configuration (or None if resource is not yet
      created).
    print_format: Print format to use when showing current dns_settings.

  Returns:
    A pair: (messages.DnsSettings, DnsUpdateMask) to be updated, or (None, None)
    if the user cancelled.
  """
  domains_messages = registrations.GetMessagesModule(api_version)
  options = [
      'Provide name servers list', 'Provide Cloud DNS Managed Zone name',
      'Use free name servers provided by Google Domains'
  ]
  if dns_settings is not None:  # Update
    log.status.Print('Your current DNS settings are:')
    resource_printer.Print(dns_settings, print_format, out=sys.stderr)

    message = (
        'You can provide your DNS settings by specifying name servers, '
        'a Cloud DNS Managed Zone name or by choosing '
        'free name servers provided by Google Domains'
    )
    cancel_option = True
    default = len(options)  # Additional 'cancel' option.
  else:
    options = options[:2]
    message = (
        'You can provide your DNS settings by specifying name servers '
        'or a Cloud DNS Managed Zone name'
    )
    cancel_option = False
    default = 1  # Cloud DNS Zone.

  index = console_io.PromptChoice(
      message=message,
      options=options,
      cancel_option=cancel_option,
      default=default)
  name_servers = []
  if index == 0:  # name servers.
    while len(name_servers) < 2:
      while True:
        ns = console_io.PromptResponse('Name server (empty line to finish):  ')
        if not ns:
          break
        if not util.ValidateDomainName(ns):
          log.status.Print('Invalid name server: \'{}\'.'.format(ns))
        else:
          name_servers += [ns]
      if len(name_servers) < 2:
        log.status.Print('You have to provide at least 2 name servers.')
    return _CustomNameServers(domains_messages, name_servers)
  elif index == 1:  # Cloud DNS.
    while True:
      zone = util.PromptWithValidator(
          validator=util.ValidateNonEmpty,
          error_message=' Cloud DNS Managed Zone name must not be empty.',
          prompt_string='Cloud DNS Managed Zone name:  ')
      try:
        name_servers, ds_records = _GetCloudDnsDetails(domains_messages, zone,
                                                       domain, enable_dnssec)
      except (exceptions.Error, calliope_exceptions.HttpException) as e:
        log.status.Print(six.text_type(e))
      else:
        break
    return _CustomNameServers(domains_messages, name_servers, ds_records)
  elif index == 2:  # Google Domains name servers.
    return _GoogleDomainsNameServers(domains_messages, enable_dnssec)
  else:
    return None, None  # Cancel.


def PromptForNameServersTransfer(api_version, domain):
  """Asks the user to provide DNS settings interactively for Transfers.

  Args:
    api_version: Cloud Domains API version to call.
    domain: Domain name corresponding to the DNS settings.

  Returns:
    A triple: (messages.DnsSettings, DnsUpdateMask, _) to be updated, or
    (None, None, _) if the user cancelled. The third value returns true when
    keeping the current DNS settings during Transfer.
  """
  domains_messages = registrations.GetMessagesModule(api_version)
  options = [
      'Provide Cloud DNS Managed Zone name',
      'Use free name servers provided by Google Domains',
      'Keep current DNS settings from current registrar'
  ]
  message = ('You can provide your DNS settings in one of several ways:\n'
             'You can specify a Cloud DNS Managed Zone name. To avoid '
             'downtime following transfer, make sure the zone is configured '
             'correctly before proceeding.\n'
             'You can select free name servers provided by Google Domains. '
             'This blank-slate option cannot be configured before transfer.\n'
             'You can also choose to keep the domain\'s DNS settings '
             'from its current registrar. Use this option only if you are '
             'sure that the domain\'s current DNS service will not cease upon '
             'transfer, as is often the case for DNS services provided for '
             'free by the registrar.')

  cancel_option = False
  default = 2  # Keep current DNS settings.
  enable_dnssec = False

  index = console_io.PromptChoice(
      message=message,
      options=options,
      cancel_option=cancel_option,
      default=default)
  if index == 0:  # Cloud DNS.
    while True:
      zone = util.PromptWithValidator(
          validator=util.ValidateNonEmpty,
          error_message=' Cloud DNS Managed Zone name must not be empty.',
          prompt_string='Cloud DNS Managed Zone name:  ')
      try:
        name_servers, ds_records = _GetCloudDnsDetails(domains_messages, zone,
                                                       domain, enable_dnssec)
      except (exceptions.Error, calliope_exceptions.HttpException) as e:
        log.status.Print(six.text_type(e))
      else:
        break
    dns_settings, update_mask = _CustomNameServers(domains_messages,
                                                   name_servers, ds_records)
    return dns_settings, update_mask, False
  elif index == 1:  # Google Domains name servers.
    dns_settings, update_mask = _GoogleDomainsNameServers(
        domains_messages, enable_dnssec)
    return dns_settings, update_mask, False
  else:  # Keep current DNS settings (Transfer).
    return None, None, True


def NameServersEquivalent(prev_dns_settings, new_dns_settings):
  """Checks if dns settings have equivalent name servers."""
  if prev_dns_settings.googleDomainsDns:
    return bool(new_dns_settings.googleDomainsDns)
  if prev_dns_settings.customDns:
    if not new_dns_settings.customDns:
      return False
    prev_ns = sorted(
        map(util.NormalizeDomainName, prev_dns_settings.customDns.nameServers))
    new_ns = sorted(
        map(util.NormalizeDomainName, new_dns_settings.customDns.nameServers))
    return prev_ns == new_ns

  return False


def PromptForUnsafeDnsUpdate():
  console_io.PromptContinue(
      'This operation is not safe.',
      default=False,
      throw_if_unattended=True,
      cancel_on_no=True)


def DnssecEnabled(dns_settings):
  ds_records = []
  if dns_settings.googleDomainsDns is not None:
    ds_records = dns_settings.googleDomainsDns.dsRecords
  if dns_settings.customDns is not None:
    ds_records = dns_settings.customDns.dsRecords
  return bool(ds_records)
