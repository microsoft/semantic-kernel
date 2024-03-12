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
"""The gcloud datastore indexes cleanup command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.datastore import index_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.app import output_helpers
from googlecloudsdk.command_lib.datastore import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class Cleanup(base.Command):
  """Cleanup Cloud Datastore indexes."""

  detailed_help = {
      'brief':
          'Remove unused datastore indexes based on your local index '
          'configuration.',
      'DESCRIPTION':
          """
This command removes unused datastore indexes based on your local index
configuration. Any indexes that exist that are not in the index file will be
removed.
      """,
      'EXAMPLES':
          """\
          To remove unused indexes based on your local configuration, run:

            $ {command} ~/myapp/index.yaml
          """,
  }

  @staticmethod
  def Args(parser):
    """Get arguments for this command.

    Args:
      parser: argparse.ArgumentParser, the parser for this command.
    """
    flags.AddIndexFileFlag(parser)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    info = yaml_parsing.ConfigYamlInfo.FromFile(args.index_file)
    if not info or info.name != yaml_parsing.ConfigYamlInfo.INDEX:
      raise exceptions.InvalidArgumentException(
          'index_file', 'You must provide the path to a valid index.yaml file.')
    output_helpers.DisplayProposedConfigDeployments(
        project=project, configs=[info]
    )
    console_io.PromptContinue(
        default=True, throw_if_unattended=False, cancel_on_no=True)
    received_indexes = index_api.NormalizeIndexes(info.parsed.indexes or [])
    indexes_to_delete_ids = set()
    current_indexes = index_api.ListIndexes(project)
    for index_id, index in current_indexes:
      if index in received_indexes:
        continue
      msg = ('This index is no longer defined in your index.yaml file.\n{0}'
             .format(index.ToYAML()))
      prompt = 'Do you want to delete this index'
      if console_io.PromptContinue(msg, prompt, default=True):
        indexes_to_delete_ids.add(index_id)
    index_api.DeleteIndexes(project, indexes_to_delete_ids)
