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
"""Implementation of objects compose command for Cloud Storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


import textwrap

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks import compose_objects_task


class Compose(base.Command):
  """Concatenate a sequence of objects into a new composite object."""

  detailed_help = {
      'DESCRIPTION':
          """
      {command} creates a new object whose content is the concatenation
      of a given sequence of source objects in the same bucket.
      For more information, please see:
      [composite objects documentation](https://cloud.google.com/storage/docs/composite-objects).

      There is a limit (currently 32) to the number of components
      that can be composed in a single operation.
      """,
      'EXAMPLES':
          """
      The following command creates a new object `target.txt` by concatenating
      `a.txt` and `b.txt`:

        $ {command} gs://bucket/a.txt gs://bucket/b.txt gs://bucket/target.txt
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'source',
        nargs='+',
        help=textwrap.dedent("""\
            The list of source objects that will be concatenated into a
            single object."""))
    parser.add_argument('destination', help='The destination object.')

    flags.add_additional_headers_flag(parser)
    flags.add_encryption_flags(parser, hidden=True)
    flags.add_per_object_retention_flags(parser)
    flags.add_precondition_flags(parser)

  def Run(self, args):
    encryption_util.initialize_key_store(args)
    if args.source:
      destination_resource = resource_reference.UnknownResource(
          storage_url.storage_url_from_string(args.destination))
      for url_string in args.source:
        source_url = storage_url.storage_url_from_string(url_string)
        errors_util.raise_error_if_not_cloud_object(args.command_path,
                                                    source_url)
        if source_url.scheme is not destination_resource.storage_url.scheme:
          raise errors.Error('Composing across providers is not supported.')
    if (args.destination !=
        destination_resource.storage_url.versionless_url_string):
      raise errors.Error(
          'Verison-specific URLs are not valid destinations because'
          ' composing always results in creating an object with the'
          ' latest generation.')

    source_expansion_iterator = name_expansion.NameExpansionIterator(
        args.source,
        fields_scope=cloud_api.FieldsScope.NO_ACL,
        recursion_requested=name_expansion.RecursionSetting.NO)

    objects_to_compose = [
        source.resource for source in source_expansion_iterator
    ]

    user_request_args = (
        user_request_args_factory.get_user_request_args_from_command_args(
            args, metadata_type=user_request_args_factory.MetadataType.OBJECT))

    compose_objects_task.ComposeObjectsTask(
        objects_to_compose,
        destination_resource,
        print_status_message=True,
        user_request_args=user_request_args,
    ).execute()
