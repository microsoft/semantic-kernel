# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Deletes a Filestore instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.filestore import filestore_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.filestore import flags
from googlecloudsdk.command_lib.filestore.instances import flags as instances_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Filestore instance."""

  _API_VERSION = filestore_client.V1_API_VERSION

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([flags.GetInstancePresentationSpec(
        'The instance to delete.')]).AddToParser(parser)
    instances_flags.AddLocationArg(parser)
    instances_flags.AddRegionArg(parser)
    instances_flags.AddAsyncFlag(parser)
    instances_flags.AddForceArg(parser)

  def Run(self, args):
    """Deletes a Filestore instance."""
    instance_ref = args.CONCEPTS.instance.Parse()
    delete_warning = ('You are about to delete Filestore instance {}.\n'
                      'Are you sure?'.format(instance_ref.RelativeName()))

    if not console_io.PromptContinue(message=delete_warning):
      return None
    client = filestore_client.FilestoreClient(version=self._API_VERSION)

    result = client.DeleteInstance(instance_ref, args.async_, args.force)

    if args.async_:
      command = properties.VALUES.metrics.command_name.Get().split('.')
      if command:
        command[-1] = 'list'
      log.status.Print(
          'Check the status of the deletion by listing all instances:\n  '
          '$ {} '.format(' '.join(command)))
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(Delete):
  """Delete a Filestore instance."""

  _API_VERSION = filestore_client.BETA_API_VERSION

  def Run(self, args):
    """Deletes a Filestore instance."""
    instance_ref = args.CONCEPTS.instance.Parse()
    delete_warning = ('You are about to delete Filestore instance {}.\n'
                      'Are you sure?'.format(instance_ref.RelativeName()))

    if not console_io.PromptContinue(message=delete_warning):
      return None
    client = filestore_client.FilestoreClient(version=self._API_VERSION)

    result = client.DeleteInstance(instance_ref, args.async_, args.force)

    if args.async_:
      command = properties.VALUES.metrics.command_name.Get().split('.')
      if command:
        command[-1] = 'list'
      log.status.Print(
          'Check the status of the deletion by listing all instances:\n  '
          '$ {} '.format(' '.join(command)))
    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteAlpha(base.DeleteCommand):
  """Delete a Filestore instance."""

  _API_VERSION = filestore_client.ALPHA_API_VERSION

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([
        flags.GetInstancePresentationSpec('The instance to delete.')
    ]).AddToParser(parser)
    instances_flags.AddLocationArg(parser)
    instances_flags.AddRegionArg(parser)
    instances_flags.AddAsyncFlag(parser)

  def Run(self, args):
    """Delete a Filestore instance."""
    instance_ref = args.CONCEPTS.instance.Parse()
    delete_warning = ('You are about to delete Filestore instance {}.\n'
                      'Are you sure?'.format(instance_ref.RelativeName()))

    if not console_io.PromptContinue(message=delete_warning):
      return None
    client = filestore_client.FilestoreClient(version=self._API_VERSION)

    result = client.DeleteInstanceAlpha(instance_ref, args.async_)

    if args.async_:
      command = properties.VALUES.metrics.command_name.Get().split('.')
      if command:
        command[-1] = 'list'
      log.status.Print(
          'Check the status of the deletion by listing all instances:\n  '
          '$ {} '.format(' '.join(command)))
    return result


help_ = {
    'DESCRIPTION':
        'Delete a Filestore instance.',
    'EXAMPLES':
        """\
To delete a Filestore instance named NAME in us-central1-c:

  $ {command} NAME --zone=us-central1-c
"""
}
Delete.detailed_help = help_
DeleteAlpha.detailed_help = help_
