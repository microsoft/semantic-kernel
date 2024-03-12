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
"""Factory class for BatchesCreateRequest message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc.batches import batch_message_factory


class BatchesCreateRequestFactory(object):
  """Factory class handling BatchesCreateRequest message.

  Factory class for configure argument parser and create
  BatchesCreateRequest message from parsed argument.
  """

  def __init__(self, dataproc, batch_message_factory_override=None):
    """Factory for BatchesCreateRequest message.

    Only handles general submit flags added by this class. User needs to
    provide job specific message when creating the request message.

    Args:
      dataproc: A api_lib.dataproc.Dataproc instance.
      batch_message_factory_override: Override BatchMessageFactory instance.
    """
    self.dataproc = dataproc

    self.batch_message_factory = batch_message_factory_override
    if not self.batch_message_factory:
      self.batch_message_factory = (
          batch_message_factory.BatchMessageFactory(self.dataproc))

  def GetRequest(self, args, batch_job):
    """Creates a BatchesCreateRequest message.

    Creates a BatchesCreateRequest message. The factory only handles the
    arguments added in AddArguments function. User needs to provide job
    specific message instance.

    Args:
      args: Parsed arguments.
      batch_job: A batch job typed message instance.

    Returns:
      BatchesCreateRequest: A configured BatchesCreateRequest.
    """
    kwargs = {}

    kwargs['parent'] = args.CONCEPTS.region.Parse().RelativeName()

    # Recommendation: Always set a request ID for a create batch request.
    kwargs['requestId'] = args.request_id
    if not kwargs['requestId']:
      kwargs['requestId'] = util.GetUniqueId()

    # This behavior conflicts with protobuf definition.
    # Remove this if auto assign batch ID on control plane is enabled.
    kwargs['batchId'] = args.batch
    if not kwargs['batchId']:
      kwargs['batchId'] = kwargs['requestId']

    kwargs['batch'] = self.batch_message_factory.GetMessage(args, batch_job)

    return self.dataproc.messages.DataprocProjectsLocationsBatchesCreateRequest(
        **kwargs)


def AddArguments(parser, api_version):
  """Add arguments related to BatchesCreateRequest message.

  Add BatchesCreateRequest arguments to parser. This only includes general
  arguments for all `batches submit` commands. Batch job type specific
  arguments are not included, and those messages need to be passed in during
  message construction (when calling GetMessage).

  Args:
    parser: A argument parser instance.
    api_version: Api version to use.
  """
  flags.AddProjectsLocationsResourceArg(parser, api_version)

  batch_id_pattern = re.compile(r'^[a-z0-9][-a-z0-9]{2,61}[a-z0-9]$')
  parser.add_argument(
      '--batch',
      type=arg_parsers.CustomFunctionValidator(batch_id_pattern.match, (
          'Only lowercase letters (a-z), numbers (0-9), and '
          'hyphens (-) are allowed. The length must be between 4 and 63 characters.'
      )),
      help=(
          'The ID of the batch job to submit. '
          'The ID must contain only lowercase letters (a-z), numbers (0-9) and '
          'hyphens (-). The length of the name must be between 4 and 63 characters. '
          'If this argument is not provided, a random generated UUID '
          'will be used.'))

  request_id_pattern = re.compile(r'^[a-zA-Z0-9_-]{1,40}$')
  parser.add_argument(
      '--request-id',
      type=arg_parsers.CustomFunctionValidator(request_id_pattern.match, (
          'Only letters (a-z, A-Z), numbers (0-9), underscores (_), and hyphens '
          '(-) are allowed. The length must not exceed 40 characters.')),
      help=('A unique ID that identifies the request. If the service '
            'receives two batch create requests with the same request_id, '
            'the second request is ignored and the operation that '
            'corresponds to the first Batch created and stored in the '
            'backend is returned. '
            'Recommendation:  Always set this value to a UUID. '
            'The value must contain only letters (a-z, A-Z), numbers (0-9), '
            'underscores (_), and hyphens (-). The maximum length is 40 '
            'characters.'))

  _AddDependency(parser)


def _AddDependency(parser):
  batch_message_factory.AddArguments(parser)
