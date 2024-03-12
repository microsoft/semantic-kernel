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
"""Implementation of hash command for getting formatted file hashes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import binascii

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import fast_crc32c_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.util import crc32c
from googlecloudsdk.core import log

_DIGEST_FORMAT_KEY = 'digest_format'
_CRC32C_HASH_KEY = 'crc32c_hash'
_MD5_HASH_KEY = 'md5_hash'
_URL_KEY = 'url'


def _convert_base64_to_hex(base64_string):
  """Converts base64 hash digest to hex-formatted hash digest string."""
  if base64_string is None:
    return None
  return binascii.hexlify(
      base64.b64decode(
          base64_string.strip('\n"\'').encode('utf-8'))).decode('utf-8')


def _is_object_or_file_resource(resource):
  return isinstance(resource, (resource_reference.ObjectResource,
                               resource_reference.FileObjectResource))


def _get_resource_iterator(url_strings):
  """Wildcard matches and recurses into top-level of buckets."""
  any_url_matched = False
  for url_string in url_strings:
    wildcard_expanded_iterator = wildcard_iterator.get_wildcard_iterator(
        url_string,
        error_on_missing_key=False,
        fetch_encrypted_object_hashes=True)
    this_url_matched = False
    for wildcard_expanded_resource in wildcard_expanded_iterator:
      if _is_object_or_file_resource(wildcard_expanded_resource):
        any_url_matched = this_url_matched = True
        yield wildcard_expanded_resource
      elif (isinstance(wildcard_expanded_resource.storage_url,
                       storage_url.CloudUrl) and
            wildcard_expanded_resource.storage_url.is_bucket()):
        bucket_expanded_iterator = wildcard_iterator.get_wildcard_iterator(
            wildcard_expanded_resource.storage_url.join('*').url_string,
            error_on_missing_key=False)
        for bucket_expanded_resource in bucket_expanded_iterator:
          if isinstance(bucket_expanded_resource,
                        (resource_reference.ObjectResource)):
            any_url_matched = this_url_matched = True
            yield bucket_expanded_resource
    if not this_url_matched:
      log.warning('No matches found for {}'.format(url_string))
  if not any_url_matched:
    raise errors.InvalidUrlError('No URLS matched.')


class Hash(base.Command):
  """Calculates hashes on local or cloud files."""

  detailed_help = {
      'DESCRIPTION':
          """
      Calculates hashes on local or cloud files that can be used to compare with
      "gcloud storage ls -L" output. If a specific hash option is not provided,
      this command calculates all gcloud storage-supported hashes for the file.

      Note that gcloud storage automatically performs hash validation when
      uploading or downloading files, so this command is only needed if you want
      to write a script that separately checks the hash for some reason.

      If you calculate a CRC32C hash for the file without a precompiled
      google-crc32c installation, hashing will be very slow.
      """,
      'EXAMPLES':
          """

      To get the MD5 and CRC32C hash digest of a cloud object in Base64 format:

        $ {command} gs://bucket/object

      To get just the MD5 hash digest of a local object in hex format:

        $ {command} /dir/object.txt --skip-crc32c --hex
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'urls', nargs='+', help='Local or cloud URLs of objects to hash.')
    parser.add_argument(
        '--hex',
        action='store_true',
        help='Output hash digests in hex format. By default, digests are'
        ' displayed in base64.')
    skip_flags_group = parser.add_group(mutex=True)
    skip_flags_group.add_argument(
        '--skip-crc32c',
        action='store_true',
        help='Skip CRC32C hash calculation. Useful if command is running slow.')
    skip_flags_group.add_argument(
        '--skip-md5',
        action='store_true',
        help='Skip MD5 hash calculation. Useful if command is running slow.')
    flags.add_encryption_flags(parser, command_only_reads_data=True)

    flags.add_additional_headers_flag(parser)

  def Run(self, args):
    encryption_util.initialize_key_store(args)
    if not args.skip_crc32c:
      if fast_crc32c_util.should_use_gcloud_crc32c():
        crc32c_implementation = 'gcloud-crc32c (Go binary)'
      elif crc32c.IS_FAST_GOOGLE_CRC32C_AVAILABLE:
        crc32c_implementation = 'google-crc32c (Python binary)'
      else:
        crc32c_implementation = 'crcmod (slow pure Python implementation)'
      log.info('CRC32C implementation: {}'.format(crc32c_implementation))

    if args.hex:
      hash_format = 'hex'
      format_cloud_digest = _convert_base64_to_hex
      format_file_hash_object = lambda x: x.hexdigest()
    else:
      hash_format = 'base64'
      format_cloud_digest = lambda x: x
      format_file_hash_object = hash_util.get_base64_hash_digest_string

    for resource in _get_resource_iterator(args.urls):
      output_dict = {
          _DIGEST_FORMAT_KEY: hash_format,
      }
      if isinstance(resource, resource_reference.ObjectResource):
        if resource.crc32c_hash is None and resource.md5_hash is None:
          log.warning('No hashes found for {}'.format(resource))
          continue
        output_dict[_URL_KEY] = resource.storage_url.versionless_url_string
        if not args.skip_crc32c:
          output_dict[_CRC32C_HASH_KEY] = format_cloud_digest(
              resource.crc32c_hash)
        if not args.skip_md5:
          output_dict[_MD5_HASH_KEY] = format_cloud_digest(resource.md5_hash)
      else:  # FileObjectResource
        output_dict[_URL_KEY] = resource.storage_url.object_name
        if not args.skip_crc32c:
          output_dict[_CRC32C_HASH_KEY] = format_file_hash_object(
              hash_util.get_hash_from_file(
                  resource.storage_url.object_name,
                  hash_util.HashAlgorithm.CRC32C,
              )
          )
        if not args.skip_md5:
          output_dict[_MD5_HASH_KEY] = format_file_hash_object(
              hash_util.get_hash_from_file(
                  resource.storage_url.object_name, hash_util.HashAlgorithm.MD5
              )
          )
      yield output_dict
