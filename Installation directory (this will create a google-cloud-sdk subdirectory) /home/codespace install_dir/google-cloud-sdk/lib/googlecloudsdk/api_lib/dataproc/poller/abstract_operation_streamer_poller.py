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

"""Abstract waiter utility for api_lib.util.waiter.py.

Abstract waiter utility class for api_lib.util.waiter.WaitFor.
This class is the base class for poller that need to stream output and poll on
dataproc's operation.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import storage_helpers
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_attr


# TODO(b/191187715): Migrate current job poller to extend this class.
class AbstractOperationStreamerPoller(waiter.OperationPoller):
  """Base abstract poller class for dataproc operation.

  Base abstract poller class for dataproc operation. Sub classes should
  override IsDone, Poll, _GetResult and _GetOutputUri functions to provide
  command specific logic. Noticed that it is _GetResult not GetResult. The
  function name is precedes with an underscore.
  Pass TrackerUpdateFunction to waiter.WaitFor's tracker_update_func parameter
  to stream remote output.
  """

  def __init__(self, dataproc):
    """Poller for batch workload.

    Args:
      dataproc: A api_lib.dataproc.Dataproc instance.
    """
    self.saved_stream_uri = None
    self.driver_log_streamer = None
    self.dataproc = dataproc

  def IsDone(self, poll_result):
    """Determines if the poll result is done.

    Determines if the poll result is done. This is a null implementation that
    simply returns False. Sub class should override this and provide concrete
    checking logic.

    Overrides.

    Args:
      poll_result: Poll result returned from Poll function.

    Returns:
      True if the remote resource is done, or False otherwise.
    """
    return False

  def Poll(self, ref):
    """Fetches remote resource.

    Fetches remote resource. This is a null implementation that simply returns
    None. Sub class should override this and provide concrete fetching logic.

    Overrides.

    Args:
      ref: Resource reference. The same argument passed to waiter.WaitFor.

    Returns:
      None. Sub class should override this and return the actual fetched
      resource.
    """
    return None

  def _GetOutputUri(self, poll_result):
    """Gets output uri from poll result.

    Gets output uri from poll result. This is a null implementation that
    returns None. Sub class should override this and return actual output uri
    for output streamer, or returns None if something goes wrong and there is
    no output uri in the poll result.

    Args:
      poll_result: Poll result returned by Poll.

    Returns:
      None. Sub class should override this and returns actual output uri, or
      None when something goes wrong.
    """
    return None

  def _GetResult(self, poll_result):
    """Returns operation result to caller.

    This function is called after GetResult streams remote output.
    This is a null implementation that simply returns None. Sub class should
    override this and provide actual _GetResult logic.

    Args:
      poll_result: Poll result returned from Poll.

    Returns:
      None. Sub class should override this and return actual result.
    """
    return None

  def GetResult(self, poll_result):
    """Returns result for remote resource.

    This function first stream remote output to user, then returns operation
    result by calling _GetResult.

    Overrides.

    Args:
      poll_result: Poll result returned by Poll.

    Returns:
      Wahtever returned from _GetResult.
    """
    # Stream the remaining outputs.
    # There won't be new remote output, so no need to poll on it.
    # Let the streamer stream utill it ends.
    self.TrackerUpdateFunction(None, poll_result, None)
    return self._GetResult(poll_result)

  def TrackerUpdateFunction(self, tracker, poll_result, status):
    """Custom tracker function which gets called after every tick.

    This gets called whenever progress tracker gets a tick. However we want to
    stream remote output to users instead of showing a progress tracker.

    Args:
      tracker: Progress tracker instance. Not being used.
      poll_result: Result from Poll function.
      status: Status argument that is supposed to pass to the progress tracker
      instance. Not being used here as well.
    """
    self._CheckStreamer(poll_result)
    self._StreamOutput()

  def _StreamOutput(self):
    if self.driver_log_streamer and self.driver_log_streamer.open:
      self.driver_log_streamer.ReadIntoWritable(log.err)

  def _CheckStreamer(self, poll_result):
    """Checks if need to init a new output streamer.

    Checks if need to init a new output streamer.
    Remote may fail; switch to new output uri.
    Invalidate the streamer instance and init a new one if necessary.

    Args:
      poll_result: Poll result returned from Poll.
    """
    # Mimic current job waiting behavior to print equal signs across the screen.
    def _PrintEqualsLineAccrossScreen():
      attr = console_attr.GetConsoleAttr()
      log.err.Print('=' * attr.GetTermSize()[0])

    # pylint: disable=assignment-from-none
    uri = self._GetOutputUri(poll_result)
    # pylint: enable=assignment-from-none

    if not uri:
      # Remote resource not ready, nothing to check.
      return

    # Invalidate current streamer if remote output uri changed.
    if self.saved_stream_uri and self.saved_stream_uri != uri:
      self.driver_log_streamer = None
      self.saved_stream_uri = None
      _PrintEqualsLineAccrossScreen()
      log.warning("Attempt failed. Streaming new attempt's output.")
      _PrintEqualsLineAccrossScreen()

    # Init a new streamer if there is no active streamer.
    if not self.driver_log_streamer:
      self.saved_stream_uri = uri
      self.driver_log_streamer = storage_helpers.StorageObjectSeriesStream(uri)
