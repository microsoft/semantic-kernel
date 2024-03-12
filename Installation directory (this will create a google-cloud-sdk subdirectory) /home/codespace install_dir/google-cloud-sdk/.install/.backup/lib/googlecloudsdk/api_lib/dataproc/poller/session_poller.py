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

"""Waiter utility for api_lib.util.waiter.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.api_lib.dataproc.poller import (
    abstract_operation_streamer_poller as dataproc_poller_base)
from googlecloudsdk.core import log


class SessionPoller(dataproc_poller_base.AbstractOperationStreamerPoller):
  """Poller for session workload."""

  def IsDone(self, session):
    """See base class."""
    return session and session.state in (
        self.dataproc.messages.Session.StateValueValuesEnum.ACTIVE,
        self.dataproc.messages.Session.StateValueValuesEnum.FAILED)

  def Poll(self, session_ref):
    """See base class."""
    request = (
        self.dataproc.messages.DataprocProjectsLocationsSessionsGetRequest(
            name=session_ref))
    try:
      return self.dataproc.client.projects_locations_sessions.Get(request)
    except apitools_exceptions.HttpError as error:
      log.warning('Get session failed:\n{}'.format(error))
      if util.IsClientHttpException(error):
        # Stop polling if encounter client Http error (4xx).
        raise

  def _GetResult(self, session):
    """Handles errors.

    Error handling for sessions. This happen after the session reaches one of
    the complete states.

    Overrides.

    Args:
      session: The session resource.

    Returns:
      None. The result is directly output to log.err.

    Raises:
      OperationTimeoutError: When waiter timed out.
      OperationError: When remote session creation is failed.
    """
    if not session:
      # Session resource is None but polling is considered done.
      # This only happens when the waiter timed out.
      raise exceptions.OperationTimeoutError(
          'Timed out while waiting for session creation.')

    if (session.state ==
        self.dataproc.messages.Session.StateValueValuesEnum.FAILED):
      err_message = 'Session creation is FAILED.'
      if session.stateMessage:
        err_message = '{} Detail: {}'.format(err_message, session.stateMessage)
        if err_message[-1] != '.':
          err_message += '.'
      raise exceptions.OperationError(err_message)

    # Nothing to return.
    return None

  def _CheckStreamer(self, poll_result):
    pass
