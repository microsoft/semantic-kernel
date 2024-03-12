# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Command to wait for Cloud Life Sciences operation to complete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.lifesciences import lifesciences_client
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.lifesciences import operation_poller
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers


class Wait(base.SilentCommand):
  r"""Wait for Cloud Life Sciences operation to complete.

  ## EXAMPLES
  To wait for the completion of the operation called `my-operation`, run:

    $ {command} my-operation
  """

  WAIT_CEILING_MS = 60 * 20 * 1000

  @staticmethod
  def Args(parser):
    operation_spec = concepts.ResourceSpec.FromYaml(
        yaml_data.ResourceYAMLData.FromPath('lifesciences.operation')
        .GetData())
    concept_parsers.ConceptParser.ForResource(
        'operation', operation_spec, 'The Cloud Life Sciences operation to wait for.',
        required=True).AddToParser(parser)

  def Run(self, args):
    client = lifesciences_client.LifeSciencesClient()
    operation_ref = args.CONCEPTS.operation.Parse()

    req = client.messages.LifesciencesProjectsLocationsOperationsGetRequest(
        name=operation_ref.RelativeName())

    operation = client.client.projects_locations_operations.Get(req)

    waiter.WaitFor(
        operation_poller.OperationPoller(),
        operation.name,
        'Waiting for [{}] to complete.'.format(operation.name),
        wait_ceiling_ms=self.WAIT_CEILING_MS)
