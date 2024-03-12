# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""utilities function for partner metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.protorpclite import protojson
from apitools.base.py import encoding
from apitools.base.py import extra_types
from googlecloudsdk.api_lib.compute import exceptions
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import arg_parsers

messages = core_apis.GetMessagesModule('compute', 'alpha')


class NullValueInAddPartnerMetadataException(exceptions.Error):
  """Null values not allowed in add-partner-metadata."""


def AddPartnerMetadataArgs(parser):
  """Adds --metadata and --metadata-from-file flags."""
  parser.add_argument(
      '--partner-metadata',
      type=arg_parsers.ArgDict(),
      help=(
          'Partner Metadata assigned to the instance. A map from a'
          ' subdomain(namespace) to entries map.'
      ),
      default={},
      metavar='KEY=VALUE',
      action=arg_parsers.UpdateAction,
  )
  parser.add_argument(
      '--partner-metadata-from-file',
      type=arg_parsers.FileContents(),
      help=(
          'path to json local file which including the definintion of partner'
          ' metadata.'
      ),
      metavar='LOCAL_FILE_PATH',
  )


def CreatePartnerMetadataDict(args):
  """create partner metadata from the given args.

  Args:
    args: args containing partner-metadata or partner-metadata-from-file flags

  Returns:
    python dict contains partner metadata from given args.
  """
  return _CreatePartnerMetadataDict(
      args.partner_metadata, args.partner_metadata_from_file
  )


def _CreatePartnerMetadataDict(
    partner_metadata, partner_metadata_from_file=None
):
  """create partner metadata from the given args.

  Args:
    partner_metadata: partner metadata dictionary.
    partner_metadata_from_file: partner metadata file content.

  Returns:
    python dict contains partner metadata from given args.
  """
  partner_metadata_file = {}
  if partner_metadata_from_file:
    partner_metadata_file = json.loads(partner_metadata_from_file)
  partner_metadata_dict = {}
  for key in partner_metadata_file.keys():
    if 'entries' in partner_metadata_file[key]:
      partner_metadata_dict[key] = partner_metadata_file[key]
    else:
      partner_metadata_dict[key] = {'entries': partner_metadata_file[key]}
  for key, value in partner_metadata.items():
    namespace, entry = key.split('/')
    if namespace not in partner_metadata_dict:
      partner_metadata_dict[namespace] = {'entries': {}}
    partner_metadata_dict[namespace]['entries'][entry] = json.loads(value)
  return partner_metadata_dict


def ValidatePartnerMetadata(partner_metadata):
  for key in partner_metadata.keys():
    if partner_metadata[key] is None:
      raise NullValueInAddPartnerMetadataException(
          'Null values are not allowed in partner metadata.'
      )
    if isinstance(partner_metadata[key], dict):
      ValidatePartnerMetadata(partner_metadata[key])


def ConvertStructuredEntries(structured_entries):
  structured_entries_message = messages.StructuredEntries()
  if structured_entries is None:
    return structured_entries_message
  structured_entries_message.entries = messages.StructuredEntries.EntriesValue()
  for key, value in structured_entries['entries'].items():
    structured_entries_message.entries.additionalProperties.append(
        messages.StructuredEntries.EntriesValue.AdditionalProperty(
            key=key, value=encoding.DictToMessage(value, extra_types.JsonValue)
        )
    )
  return structured_entries_message


def ConvertPartnerMetadataDictToMessage(partner_metadata_dict):
  partner_metadata_message = messages.PartnerMetadata.PartnerMetadataValue()
  for namespace, structured_entries in partner_metadata_dict.items():
    partner_metadata_message.additionalProperties.append(
        messages.PartnerMetadata.PartnerMetadataValue.AdditionalProperty(
            key=namespace, value=ConvertStructuredEntries(structured_entries)
        )
    )
  return partner_metadata_message


def ConvertStructuredEntriesToJson(structured_entries_message):
  structured_entries_dict = {'entries': {}}
  for (
      structured_entry
  ) in structured_entries_message.entries.additionalProperties:
    structured_entries_dict['entries'][structured_entry.key] = (
        encoding.MessageToDict(structured_entry.value)
    )
  return json.dumps(structured_entries_dict)


def EncodeStructuredEntries(structured_entries_message):
  if structured_entries_message.entries is None:
    return 'null'
  return ConvertStructuredEntriesToJson(structured_entries_message)


def DecodeStructuredEntries(structured_entries):
  return protojson.ProtoJson().decode_message(
      messages.StructuredEntries, structured_entries
  )

if hasattr(messages, 'StructuredEntries'):
  encoding.RegisterCustomMessageCodec(
      encoder=EncodeStructuredEntries, decoder=DecodeStructuredEntries
  )(messages.StructuredEntries)
