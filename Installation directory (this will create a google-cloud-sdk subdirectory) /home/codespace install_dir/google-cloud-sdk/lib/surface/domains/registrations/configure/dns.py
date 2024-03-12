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
"""`gcloud domains registrations configure dns` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.domains import dns_util
from googlecloudsdk.command_lib.domains import flags
from googlecloudsdk.command_lib.domains import resource_args
from googlecloudsdk.command_lib.domains import util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class ConfigureDNS(base.UpdateCommand):
  """Configure DNS settings of a Cloud Domains registration.

  Configure DNS settings of a Cloud Domains registration.

  In most cases, this command is used for changing the authoritative name
  servers and DNSSEC options for the given domain. However, advanced options
  like glue records are available.

  When using Cloud DNS Zone or Google Domains name servers, DNSSEC will be
  enabled by default where possible. You can disable it using the
  --disable-dnssec flag.

  ## EXAMPLES

  To start an interactive flow to configure DNS settings for ``example.com'',
  run:

    $ {command} example.com

  To use Cloud DNS managed-zone ``example-zone'' for ``example.com'', run:

    $ {command} example.com --cloud-dns-zone=example-zone

  If the managed-zone is signed, DNSSEC will be enabled for the domain.

  To change DNS settings for ``example.com'' according to information from a
  YAML file ``dns_settings.yaml'', run:

    $ {command} example.com --dns-settings-from-file=dns_settings.yaml

  To disable DNSSEC, run:

    $ {command} example.com --disable-dnssec

  """

  @staticmethod
  def Args(parser):
    resource_args.AddRegistrationResourceArg(parser,
                                             'to configure DNS settings for')
    flags.AddConfigureDNSSettingsFlagsToParser(parser)
    flags.AddValidateOnlyFlagToParser(parser, 'configure DNS settings of the')
    flags.AddAsyncFlagToParser(parser)

  def Run(self, args):
    api_version = registrations.GetApiVersionFromArgs(args)
    client = registrations.RegistrationsClient(api_version)
    args.registration = util.NormalizeResourceName(args.registration)
    registration_ref = args.CONCEPTS.registration.Parse()
    if args.disable_dnssec and args.dns_settings_from_file:
      raise exceptions.Error(
          'argument --disable-dnssec: At most one of '
          '--dns-settings-from-file | --disable-dnssec can be specified.')

    registration = client.Get(registration_ref)
    util.AssertRegistrationOperational(api_version, registration)

    dns_settings, update_mask = dns_util.ParseDNSSettings(
        api_version,
        args.name_servers,
        args.cloud_dns_zone,
        args.use_google_domains_dns,
        args.dns_settings_from_file,
        registration_ref.registrationsId,
        enable_dnssec=not args.disable_dnssec,
        dns_settings=registration.dnsSettings)

    if dns_settings is None:
      dns_settings, update_mask = dns_util.PromptForNameServers(
          api_version,
          registration_ref.registrationsId,
          enable_dnssec=not args.disable_dnssec,
          dns_settings=registration.dnsSettings)
      if dns_settings is None:
        return None

    if registration.dnsSettings.glueRecords and not update_mask.glue_records:
      # It's ok to leave Glue records while changing name servers.
      log.status.Print('Glue records will not be cleared. If you want to clear '
                       'them, use --dns-settings-from-file flag.')

    ds_records_present = dns_util.DnssecEnabled(registration.dnsSettings)
    name_servers_changed = update_mask.name_servers and not dns_util.NameServersEquivalent(
        registration.dnsSettings, dns_settings)
    if ds_records_present and name_servers_changed:
      log.warning('Name servers should not be changed if DS '
                  'records are present. Disable DNSSEC first and wait '
                  '24 hours before you change name servers. Otherwise '
                  'your domain may stop serving.')
      if not args.unsafe_dns_update:
        dns_util.PromptForUnsafeDnsUpdate()

    response = client.ConfigureDNS(
        registration_ref,
        dns_settings,
        update_mask,
        validate_only=args.validate_only)

    if args.validate_only:
      log.status.Print('The command will not have any effect because '
                       'validate-only flag is present.')
    else:
      response = util.WaitForOperation(api_version, response, args.async_)
      log.UpdatedResource(registration_ref.Name(), 'registration', args.async_)
    return response
