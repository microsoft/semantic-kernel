# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command utilities for `gcloud dns dns-keys`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.dns import dns_keys
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
import six


ALGORITHM_NUMBERS = {
    'rsamd5': 1,
    'dh': 2,
    'dsa': 3,
    'rsasha1': 5,
    'dsansec3sha1': 6,
    'rsasha1nsec3sha1': 7,
    'rsasha256': 8,
    'rsasha512': 10,
    'eccgost': 12,
    'ecdsap256sha256': 13,
    'ecdsap384sha384': 14,
}


DIGEST_TYPE_NUMBERS = {
    'sha1': 1,
    'sha256': 2,
    'sha384': 4,
}


def _GenerateDSRecord(key):
  key_tag = six.text_type(key.keyTag)
  key_algorithm = six.text_type(ALGORITHM_NUMBERS[key.algorithm.name])
  digest_algorithm = six.text_type(
      DIGEST_TYPE_NUMBERS[key.digests[0].type.name])
  digest = key.digests[0].digest
  return ' '.join([key_tag, key_algorithm, digest_algorithm, digest])


def TransformDSRecord(r, undefined=''):
  messages = apis.GetMessagesModule('dns', 'v1')
  key = encoding.DictToMessage(r, messages.DnsKey)
  try:
    return _GenerateDSRecord(key)
  except AttributeError:
    return undefined

_TRANSFORMS = {'ds_record': TransformDSRecord}


def GetTransforms():
  return _TRANSFORMS


DESCRIBE_HELP = {
    'brief': 'Show details about a DNS key resource.',
    'DESCRIPTION': ('This command displays the details of a single DNS key '
                    'resource.'),
    'EXAMPLES': """\
        To show details about a DNS key resource with ID 3 in a managed zone
        `my_zone`, run:

          $ {command} --zone=my_zone 3

        To get the DS record corresponding for the DNSKEY record from the
        previous example, run (the DNSKEY record must be for a key-signing key):

          $ {command} --zone=my_zone 3 --format='value(ds_record())'
        """
}


def AddDescribeFlags(parser, hide_short_zone_flag=False, is_beta=False):
  flags.GetZoneArg(
      'The name of the managed-zone the DNSKEY record belongs to',
      hide_short_zone_flag=hide_short_zone_flag).AddToParser(parser)
  flags.GetKeyArg(is_beta=is_beta).AddToParser(parser)
  parser.display_info.AddTransforms(GetTransforms())


LIST_HELP = {
    'brief': 'List DNS key resources.',
    'DESCRIPTION': 'List DNS key resources in a managed zone.',
    'EXAMPLES': """\
        To see the list of all DNS key resources for a managed zone `my_zone`,
        run:

          $ {command} --zone=my_zone

        To see the DS records for every key-signing DnsKey in a managed zone,
        run:

          $ {command} --zone=my_zone --filter='type=keySigning' \
              --format='value(ds_record())'
        """
}


def AddListFlags(parser, hide_short_zone_flag=False):
  parser.display_info.AddFormat('table(id,keyTag,type,isActive,description)')
  base.URI_FLAG.RemoveFromParser(parser)
  base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
  flags.GetZoneArg(
      'The name of the managed-zone you want to list DNSKEY records for.',
      hide_short_zone_flag=hide_short_zone_flag).AddToParser(parser)
  parser.display_info.AddCacheUpdater(None)
  parser.display_info.AddTransforms(GetTransforms())


class Keys(object):
  """Wrapper object for DNS DNSKEYs commands."""

  def __init__(self, keys_client, version):
    self._keys_client = keys_client
    self._version = version

  def _GetRegistry(self):
    return util.GetRegistry(self._version)

  def _ParseDnsKey(self, key_id, zone, project):
    return self._GetRegistry().Parse(
        key_id,
        params={
            'project': project,
            'managedZone': zone
        },
        collection='dns.dnsKeys')

  def _ParseZone(self, zone_id, project):
    return self._GetRegistry().Parse(
        zone_id,
        params={
            'project': project,
        },
        collection='dns.managedZones')

  def Describe(self, key_id, zone, project):
    """Calls Get on the DNS DnsKeys API with the given parameters."""
    key_ref = self._ParseDnsKey(key_id, zone, project)
    return self._keys_client.Get(key_ref)

  def List(self, zone_id, project):
    zone_ref = self._ParseZone(zone_id, project)
    return self._keys_client.List(zone_ref)

  @classmethod
  def FromApiVersion(cls, version):
    return cls(dns_keys.Client.FromApiVersion(version), version)
