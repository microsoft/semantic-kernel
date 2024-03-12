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
"""Implementation of objects describe command for getting info on objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import request_config_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import full_resource_formatter
from googlecloudsdk.command_lib.storage.resources import gsutil_json_printer
from googlecloudsdk.command_lib.storage.resources import resource_util


class Describe(base.DescribeCommand):
  """Describe a Cloud Storage object."""

  detailed_help = {
      'DESCRIPTION':
          """
      Describe a Cloud Storage object.
      """,
      'EXAMPLES':
          """

      Describe a Google Cloud Storage object with the url
      "gs://bucket/my-object":

        $ {command} gs://bucket/my-object

      Describe object with JSON formatting, only returning the "name" key:

        $ {command} gs://bucket/my-object --format="json(name)"
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument('url', help='Specifies URL of object to describe.')
    flags.add_additional_headers_flag(parser)
    flags.add_encryption_flags(parser, command_only_reads_data=True)
    flags.add_fetch_encrypted_object_hashes_flag(parser, is_list=False)
    flags.add_raw_display_flag(parser)
    flags.add_soft_deleted_flag(parser)
    gsutil_json_printer.GsutilJsonPrinter.Register()

  def Run(self, args):
    encryption_util.initialize_key_store(args)
    if wildcard_iterator.contains_wildcard(args.url):
      raise errors.InvalidUrlError(
          'Describe does not accept wildcards because it returns a single'
          ' resource. Please use the `ls` or `objects list` command for'
          ' retrieving multiple resources.')

    url = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_cloud_object(args.command_path, url)

    client = api_factory.get_api(url.scheme)
    resource = client.get_object_metadata(
        url.bucket_name,
        url.object_name,
        generation=url.generation,
        fields_scope=cloud_api.FieldsScope.FULL,
        soft_deleted=args.soft_deleted,
    )

    if (args.fetch_encrypted_object_hashes and
        cloud_api.Capability.ENCRYPTION in client.capabilities and
        not (resource.md5_hash and resource.crc32c_hash) and
        resource.decryption_key_hash_sha256):
      request_config = request_config_factory.get_request_config(
          resource.storage_url,
          decryption_key_hash_sha256=resource.decryption_key_hash_sha256,
          error_on_missing_key=True)
      final_resource = client.get_object_metadata(
          resource.bucket,
          resource.name,
          fields_scope=cloud_api.FieldsScope.FULL,
          generation=resource.generation,
          request_config=request_config,
          soft_deleted=args.soft_deleted,
      )
    else:
      final_resource = resource

    return resource_util.get_display_dict_for_resource(
        final_resource,
        full_resource_formatter.ObjectDisplayTitlesAndDefaults,
        display_raw_keys=args.raw,
    )
