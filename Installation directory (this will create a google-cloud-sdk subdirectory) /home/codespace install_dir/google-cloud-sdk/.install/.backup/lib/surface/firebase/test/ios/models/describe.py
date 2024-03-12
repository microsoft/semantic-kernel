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
"""The 'gcloud firebase test ios models describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test import util
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand):
  """Describe an iOS model."""

  detailed_help = {
      'DESCRIPTION': 'Describe an iOS model.',
      'EXAMPLES': """
To describe an iOS model, run:

  {command} iphone7

To describe an iOS model in JSON format, run:

  {command} iphone7 --format=json
"""
  }

  @staticmethod
  def Args(parser):
    """Method called by Calliope to register flags for this command.

    Args:
      parser: An argparse parser used to add arguments that follow this
          command in the CLI. Positional arguments are allowed.
    """
    # Positional arg
    parser.add_argument(
        'model_id',
        help='ID of the model to describe, found using $ {parent_command} list.'
    )

  def Run(self, args):
    """Run the 'gcloud firebase test ios models describe' command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation (i.e. group and command arguments combined).

    Returns:
      The iOS model we want to show a description of.
    """
    catalog = util.GetIosCatalog(self.context)
    for model in catalog.models:
      if model.id == args.model_id:
        return model
    raise exceptions.ModelNotFoundError(args.model_id)
