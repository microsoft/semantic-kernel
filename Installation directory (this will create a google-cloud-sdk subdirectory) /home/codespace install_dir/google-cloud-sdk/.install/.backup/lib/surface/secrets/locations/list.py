# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""List all available locations in which secrets can be replicated."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.secrets import args as secrets_args
from googlecloudsdk.command_lib.secrets import fmt as secrets_fmt


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(base.ListCommand):
  r"""List all available locations.

  List all available locations in which secrets can be replicated.

  ## EXAMPLES

  List available secrets locations:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddProject(parser)
    secrets_fmt.UseLocationTable(parser)

  def Run(self, args):
    project_ref = args.CONCEPTS.project.Parse()
    if not project_ref:
      raise exceptions.RequiredArgumentException(
          'project',
          'Please set a project with "--project" flag or "gcloud config set project <project_id>".'
      )
    return secrets_api.Locations().ListWithPager(
        project_ref=project_ref, limit=args.limit)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  r"""List all available locations.

  List all available locations in which secrets can be replicated.

  ## EXAMPLES

  List available secrets locations:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddProject(parser)
    secrets_fmt.UseLocationTable(parser)

  def Run(self, args):
    project_ref = args.CONCEPTS.project.Parse()
    if not project_ref:
      raise exceptions.RequiredArgumentException(
          'project',
          'Please set a project with "--project" flag or "gcloud config set project <project_id>".'
      )
    return secrets_api.Locations().ListWithPager(
        project_ref=project_ref, limit=args.limit)
