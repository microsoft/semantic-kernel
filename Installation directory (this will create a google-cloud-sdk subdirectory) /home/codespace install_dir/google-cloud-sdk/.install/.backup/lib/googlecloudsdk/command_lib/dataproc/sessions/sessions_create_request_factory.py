# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Factory class for SessionCreateRequest message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.dataproc.sessions import session_message_factory


class SessionsCreateRequestFactory(object):
  """Factory class handling SessionsCreateRequest message.

  Factory class for configure argument parser and create
  SessionsCreateRequest message from parsed argument.
  """

  def __init__(self, dataproc, session_message_factory_override=None):
    """Factory for SessionsCreateRequest message.

    Only handles general create flags added by this class. User needs to
    provide session specific message when creating the request message.

    Args:
      dataproc: A api_lib.dataproc.Dataproc instance.
      session_message_factory_override: Override SessionMessageFactory instance.
    """
    self.dataproc = dataproc

    self.session_message_factory = session_message_factory_override
    if not self.session_message_factory:
      self.session_message_factory = (
          session_message_factory.SessionMessageFactory(self.dataproc))

  def GetRequest(self, args):
    """Creates a SessionsCreateRequest message.

    Creates a SessionsCreateRequest message. The factory only handles the
    arguments added in AddArguments function. User needs to provide session
    specific message instance.

    Args:
      args: Parsed arguments.

    Returns:
      SessionsCreateRequest: A configured SessionsCreateRequest.
    """
    kwargs = {}
    kwargs['parent'] = args.CONCEPTS.session.Parse().Parent().RelativeName()

    kwargs['requestId'] = args.request_id
    if not kwargs['requestId']:
      kwargs['requestId'] = util.GetUniqueId()

    kwargs['sessionId'] = args.session

    kwargs['session'] = self.session_message_factory.GetMessage(args)

    return (
        self.dataproc.messages.DataprocProjectsLocationsSessionsCreateRequest(
            **kwargs
        )
    )


def AddArguments(parser):
  """Add arguments related to SessionsCreateRequest message.

  Add SessionsCreateRequest arguments to parser. This only includes general
  arguments for all `sessions create` commands. Session type specific
  arguments are not included, and those messages need to be passed in during
  message construction (when calling GetMessage).

  Args:
    parser: A argument parser instance.
  """
  request_id_pattern = re.compile(r'^[a-zA-Z0-9_-]{1,40}$')
  parser.add_argument(
      '--request-id',
      type=arg_parsers.CustomFunctionValidator(request_id_pattern.match, (
          'Only letters (a-z, A-Z), numbers (0-9), underscores (_), and hyphens'
          ' (-) are allowed. The length must not exceed 40 characters.')),
      help=('A unique ID that identifies the request. If the service '
            'receives two session create requests with the same request_id, '
            'the second request is ignored and the operation that '
            'corresponds to the first session created and stored in the '
            'backend is returned. '
            'Recommendation:  Always set this value to a UUID. '
            'The value must contain only letters (a-z, A-Z), numbers (0-9), '
            'underscores (_), and hyphens (-). The maximum length is 40 '
            'characters.'))

  parser.add_argument(
      '--max-idle',
      type=arg_parsers.Duration(),
      help="""
          The duration after which an idle session will be automatically
          terminated, for example, "20m" or "2h". A session is considered idle
          if it has no active Spark applications and no active Jupyter kernels.
          Run [gcloud topic datetimes](https://cloud.google.com/sdk/gcloud/reference/topic/datetimes)
          for information on duration formats.""")

  _AddDependency(parser)


def _AddDependency(parser):
  session_message_factory.AddArguments(parser)
