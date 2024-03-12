# -*- coding: utf-8 -*-
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Base classes for gsutil UI controller, UIThread and MainThreadUIQueue."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from collections import deque
import sys
import threading
import time

from six.moves import queue as Queue

from gslib.metrics import LogPerformanceSummaryParams
from gslib.metrics import LogRetryableError
from gslib.thread_message import FileMessage
from gslib.thread_message import FinalMessage
from gslib.thread_message import MetadataMessage
from gslib.thread_message import PerformanceSummaryMessage
from gslib.thread_message import ProducerThreadMessage
from gslib.thread_message import ProgressMessage
from gslib.thread_message import RetryableErrorMessage
from gslib.thread_message import SeekAheadMessage
from gslib.thread_message import StatusMessage
from gslib.utils import parallelism_framework_util
from gslib.utils.unit_util import DecimalShort
from gslib.utils.unit_util import HumanReadableWithDecimalPlaces
from gslib.utils.unit_util import MakeHumanReadable
from gslib.utils.unit_util import PrettyTime

_ZERO_TASKS_TO_DO_ARGUMENT = (
    parallelism_framework_util.ZERO_TASKS_TO_DO_ARGUMENT)


class EstimationSource(object):
  """enum for total size source."""
  # Integer to indicate total size came from the final ProducerThreadMessage.
  # It has priority over all other total_size sources.
  PRODUCER_THREAD_FINAL = 1
  # Integer to indicate total size came from SeekAheadThread.
  # It has priority over self.SEEK_AHEAD_THREAD and over
  # self.INDIVIDUAL_MESSAGES.
  SEEK_AHEAD_THREAD = 2
  # Integer to indicate total size came from a ProducerThread estimation.
  # It has priority over self.INDIVIDUAL_MESSAGES.
  PRODUCER_THREAD_ESTIMATE = 3
  # Stores the actual source from total_size. We start from FileMessages or
  # MetadataMessages.
  INDIVIDUAL_MESSAGES = 4
  # Note: this priority based model was used in case we add new sources for
  # total_size in the future. It also allows us to search for smaller numbers
  # (larger priorities) rather than having to list those with higher priority.


def BytesToFixedWidthString(num_bytes, decimal_places=1):
  """Adjusts proper width for printing num_bytes in readable format.

  Args:
    num_bytes: The number of bytes we must display.
    decimal_places: The standard number of decimal places.
  Returns:
    String of fixed width representing num_bytes.
  """
  human_readable = HumanReadableWithDecimalPlaces(num_bytes,
                                                  decimal_places=decimal_places)
  number_format = human_readable.split()
  if int(round(float(number_format[0]))) >= 1000:
    # If we are in the [1000:1024) range for the whole part of the number,
    # we must remove the decimal part.
    last_character = len(number_format[0]) - decimal_places - 1
    number_format[0] = number_format[0][:last_character]
  return '%9s' % (' '.join(number_format))


class StatusMessageManager(object):
  """General manager for common functions shared by data and metadata managers.

  This subclass has the responsibility of having a common constructor and the
  same handler for SeekAheadMessages and ProducerThreadMessages.
  """

  class _ThroughputInformation(object):
    """Class that contains all information needed for throughput calculation.

    This _ThroughputInformation is used to track progress and time at several
    points of our operation.
    """

    def __init__(self, progress, report_time):
      """Constructor of _ThroughputInformation.

      Args:
        progress: The current progress, in bytes/second or objects/second.
        report_time: Float representing when progress was reported (seconds
            since Epoch).
      """
      self.progress = progress
      self.time = report_time

  def __init__(self,
               update_message_period=1,
               update_spinner_period=0.6,
               sliding_throughput_period=5,
               first_throughput_latency=10,
               quiet_mode=False,
               custom_time=None,
               verbose=False,
               console_width=80):
    """Instantiates a StatusMessageManager.

    Args:
      update_message_period: Minimum period for refreshing and  displaying
                             new information. A non-positive value will ignore
                             any time restrictions imposed by this field, but
                             it will affect throughput and time remaining
                             estimations.
      update_spinner_period: Minimum period for refreshing and displaying the
                             spinner. A non-positive value will ignore
                             any time restrictions imposed by this field.
      sliding_throughput_period: Sliding period for throughput calculation. A
                                 non-positive value will make it impossible to
                                 calculate the throughput.
      first_throughput_latency: Minimum waiting time before actually displaying
                                throughput info. A non-positive value will
                                ignore any time restrictions imposed by this
                                field.
      quiet_mode: If True, do not print status messages (but still process
                  them for analytics reporting as necessary).
      custom_time: If a custom start_time is desired. Used for testing.
      verbose: Tells whether or not the operation is on verbose mode.
      console_width: Width to display on console. This should not adjust the
                     visual output, just the space padding. For proper
                     visualization, we recommend setting this field to at least
                     80.
    """
    self.update_message_period = update_message_period
    self.update_spinner_period = update_spinner_period
    self.sliding_throughput_period = sliding_throughput_period
    self.first_throughput_latency = first_throughput_latency
    self.quiet_mode = quiet_mode
    self.custom_time = custom_time
    self.verbose = verbose
    self.console_width = console_width

    # Initial estimation source for number of objects and total size
    # is through individual FileMessages or individual MetadataMessages,
    # depending on the StatusMessageManager superclass.
    self.num_objects_source = EstimationSource.INDIVIDUAL_MESSAGES
    self.total_size_source = EstimationSource.INDIVIDUAL_MESSAGES
    self.num_objects = 0
    # Only used on data operations. Will remain 0 for metadata operations.
    self.total_size = 0

    # Time at last info update displayed.
    self.refresh_message_time = (self.custom_time
                                 if self.custom_time else time.time())
    self.start_time = self.refresh_message_time
    # Time at last spinner update.
    self.refresh_spinner_time = self.refresh_message_time

    # Measured in objects/second or bytes/second, depending on the superclass.
    self.throughput = 0.0
    # Deque of _ThroughputInformation to help with throughput calculation.
    self.old_progress = deque()
    self.last_progress_time = 0

    self.spinner_char_list = ['/', '-', '\\', '|']
    self.current_spinner_index = 0

    self.objects_finished = 0
    self.num_objects = 0  # Number of objects being processed

    # This overrides time constraints for updating and displaying
    # important information, such as having finished to process an object.
    self.object_report_change = False
    self.final_message = False

  def GetSpinner(self):
    """Returns the current spinner character.

    Returns:
      char_to_print: Char to be printed as the spinner
    """
    return self.spinner_char_list[self.current_spinner_index]

  def UpdateSpinner(self):
    """Updates the current spinner character."""
    self.current_spinner_index = ((self.current_spinner_index + 1) %
                                  len(self.spinner_char_list))

  def _HandleProducerThreadMessage(self, status_message):
    """Handles a ProducerThreadMessage.

    Args:
      status_message: The ProducerThreadMessage to be processed.
    """
    if status_message.finished:
      # This means this was a final ProducerThreadMessage.
      if self.num_objects_source >= EstimationSource.PRODUCER_THREAD_FINAL:
        self.num_objects_source = EstimationSource.PRODUCER_THREAD_FINAL
        self.num_objects = status_message.num_objects
      if (self.total_size_source >= EstimationSource.PRODUCER_THREAD_FINAL and
          status_message.size):
        self.total_size_source = EstimationSource.PRODUCER_THREAD_FINAL
        self.total_size = status_message.size
      return
    if self.num_objects_source >= EstimationSource.PRODUCER_THREAD_ESTIMATE:
      self.num_objects_source = EstimationSource.PRODUCER_THREAD_ESTIMATE
      self.num_objects = status_message.num_objects
    if (self.total_size_source >= EstimationSource.PRODUCER_THREAD_ESTIMATE and
        status_message.size):
      self.total_size_source = EstimationSource.PRODUCER_THREAD_ESTIMATE
      self.total_size = status_message.size

  def _HandleSeekAheadMessage(self, status_message, stream):
    """Handles a SeekAheadMessage.

    Args:
      status_message: The SeekAheadMessage to be processed.
      stream: Stream to print messages.
    """
    estimate_message = ('Estimated work for this command: objects: %s' %
                        status_message.num_objects)
    if status_message.size:
      estimate_message += (', total size: %s' %
                           MakeHumanReadable(status_message.size))
      if self.total_size_source >= EstimationSource.SEEK_AHEAD_THREAD:
        self.total_size_source = EstimationSource.SEEK_AHEAD_THREAD
        self.total_size = status_message.size

    if self.num_objects_source >= EstimationSource.SEEK_AHEAD_THREAD:
      self.num_objects_source = EstimationSource.SEEK_AHEAD_THREAD
      self.num_objects = status_message.num_objects

    estimate_message += '\n'
    if not self.quiet_mode:
      stream.write(estimate_message)

  def _HandlePerformanceSummaryMessage(self, status_message):
    """Handles a PerformanceSummaryMessage.

    Args:
      status_message: The PerformanceSummaryMessage to be processed.
    """
    LogPerformanceSummaryParams(uses_slice=status_message.uses_slice)

  def ShouldTrackThroughput(self, cur_time):
    """Decides whether enough time has passed to start tracking throughput.

    Args:
      cur_time: current time.
    Returns:
      Whether or not we should track the throughput.
    """
    return cur_time - self.start_time >= self.first_throughput_latency

  def ShouldPrintProgress(self, cur_time):
    """Decides whether or not it is time for printing a new progress.

    Args:
      cur_time: current time.
    Returns:
      Whether or not we should print the progress.
    """
    sufficient_time_elapsed = (cur_time - self.refresh_message_time
                               >= self.update_message_period)
    # Don't report if we aren't actually going to do anything (for example,
    # an rsync that will sync 0 objects).
    nonzero_report = self.num_objects
    return (sufficient_time_elapsed or
            self.object_report_change) and (nonzero_report)

  def ShouldPrintSpinner(self, cur_time):
    """Decides whether or not it is time for updating the spinner character.

    Args:
      cur_time: Current time.
    Returns:
      Whether or not we should update and print the spinner.
    """
    return (cur_time - self.refresh_spinner_time > self.update_spinner_period
            and self.total_size)

  def PrintSpinner(self, stream=sys.stderr):
    """Prints a spinner character.

    Args:
      stream: Stream to print messages. Usually sys.stderr, but customizable
              for testing.
    """
    self.UpdateSpinner()
    if not self.quiet_mode:
      stream.write(self.GetSpinner() + '\r')

  def UpdateThroughput(self, cur_time, cur_progress):
    """Updates throughput if the required period for calculation has passed.

    The throughput is calculated by taking all the progress (objects or bytes)
    processed within the last sliding_throughput_period seconds, and dividing
    that by the time period between the oldest progress time within that range
    and the last progress measurement, which are defined by oldest_progress[1]
    and last_progress_time, respectively. Among the pros of this approach,
    a connection break or a sudden change in throughput is quickly noticeable.
    Furthermore, using the last throughput measurement rather than the current
    time allows us to have a better estimation of the actual throughput.

    Args:
      cur_time: Current time to check whether or not it is time for a new
                throughput measurement.
      cur_progress: The current progress, in number of objects finished or in
                    bytes.
    """
    while (len(self.old_progress) > 1 and cur_time - self.old_progress[0].time
           > self.sliding_throughput_period):
      self.old_progress.popleft()

    if not self.old_progress:
      return
    oldest_progress = self.old_progress[0]
    if self.last_progress_time == oldest_progress.time:
      self.throughput = 0
      return
    # If old-progress is not empty and the time of oldest_progress does not
    # match the last_progress_time, we can safely calculate the throughput.
    self.throughput = ((cur_progress - oldest_progress.progress) /
                       (self.last_progress_time - oldest_progress.time))
    # Just to avoid -0.00 B/s.
    self.throughput = max(0, self.throughput)

  def PrintFinalSummaryMessage(self, stream=sys.stderr):
    """Prints a final message to indicate operation succeeded.

    Args:
      stream: Stream to print messages. Usually sys.stderr, but customizable
              for testing.
    """
    string_to_print = ('Operation completed over %s objects' %
                       DecimalShort(self.num_objects))
    if self.total_size:
      string_to_print += ('/%s' %
                          HumanReadableWithDecimalPlaces(self.total_size))
    remaining_width = self.console_width - len(string_to_print)
    if not self.quiet_mode:
      stream.write(('\n' + string_to_print + '.' +
                    (max(remaining_width, 0) * ' ') + '\n'))


class MetadataManager(StatusMessageManager):
  """Manages shared state for metadata operations.

  This manager is specific for metadata operations. Among its main functions,
  it receives incoming StatusMessages, storing all necessary data
  about the current and past states of the system necessary to display to the
  UI. It also provides methods for calculating metrics such as throughput and
  estimated time remaining. Finally, it provides methods for displaying messages
  to the UI.
  """

  def __init__(self,
               update_message_period=1,
               update_spinner_period=0.6,
               sliding_throughput_period=5,
               first_throughput_latency=10,
               quiet_mode=False,
               custom_time=None,
               verbose=False,
               console_width=80):
    # pylint: disable=g-doc-args
    """Instantiates a MetadataManager.

    See argument documentation in StatusMessageManager base class.
    """
    # pylint: enable=g-doc-args
    super(MetadataManager,
          self).__init__(update_message_period=update_message_period,
                         update_spinner_period=update_spinner_period,
                         sliding_throughput_period=sliding_throughput_period,
                         first_throughput_latency=first_throughput_latency,
                         quiet_mode=quiet_mode,
                         custom_time=custom_time,
                         verbose=verbose,
                         console_width=console_width)

  def GetProgress(self):
    """Gets the progress for a MetadataManager.

    Returns:
      The number of finished objects.
    """
    return self.objects_finished

  def _HandleMetadataMessage(self, status_message):
    """Handles a MetadataMessage.

    Args:
      status_message: The MetadataMessage to be processed.
    """
    self.objects_finished += 1
    if self.num_objects_source >= EstimationSource.INDIVIDUAL_MESSAGES:
      self.num_objects_source = EstimationSource.INDIVIDUAL_MESSAGES
      self.num_objects += 1
    # Ensures we print periodic progress, and that we send a final message.
    self.object_report_change = True
    self.last_progress_time = status_message.time
    if (self.objects_finished == self.num_objects and
        self.num_objects_source == EstimationSource.PRODUCER_THREAD_FINAL):
      self.final_message = True

  def ProcessMessage(self, status_message, stream):
    """Processes a message from _MainThreadUIQueue or _UIThread.

    Args:
      status_message: The StatusMessage item to be processed.
      stream: Stream to print messages.
    """
    self.object_report_change = False
    if isinstance(status_message, SeekAheadMessage):
      self._HandleSeekAheadMessage(status_message, stream)
    elif isinstance(status_message, ProducerThreadMessage):
      self._HandleProducerThreadMessage(status_message)
    elif isinstance(status_message, MetadataMessage):
      self._HandleMetadataMessage(status_message)
    elif isinstance(status_message, RetryableErrorMessage):
      LogRetryableError(status_message)
    elif isinstance(status_message, PerformanceSummaryMessage):
      self._HandlePerformanceSummaryMessage(status_message)
    self.old_progress.append(
        self._ThroughputInformation(self.objects_finished, status_message.time))

  def PrintProgress(self, stream=sys.stderr):
    """Prints progress and throughput/time estimation.

    Prints total number of objects and number of finished objects with the
    percentage of work done, potentially including the throughput
    (in objects/second) and estimated time remaining.

    Args:
      stream: Stream to print messages. Usually sys.stderr, but customizable
              for testing.
    """
    # Time to update all information
    total_remaining = self.num_objects - self.objects_finished
    if self.throughput:
      time_remaining = total_remaining / self.throughput
    else:
      time_remaining = None

    char_to_print = self.GetSpinner()
    if self.num_objects_source <= EstimationSource.SEEK_AHEAD_THREAD:
      # An example of objects_completed here would be ' [2/3 objects]'.
      objects_completed = ('[' + DecimalShort(self.objects_finished) + '/' +
                           DecimalShort(self.num_objects) + ' objects]')
      if self.num_objects == self.objects_finished:
        percentage = '100'
      else:
        percentage = (
            '%3d' %
            min(99, int(100 * float(self.objects_finished) / self.num_objects)))
      percentage_completed = percentage + '% Done'
    else:
      # An example of objects_completed here would be ' [2 objects]'.
      objects_completed = ('[' + DecimalShort(self.objects_finished) +
                           ' objects]')
      percentage_completed = ''

    if (self.refresh_message_time - self.start_time
        > self.first_throughput_latency):
      # Should also include throughput.
      # An example of throughput here would be '2 objects/s'
      throughput = '%.2f objects/s' % self.throughput
      if (self.num_objects_source <= EstimationSource.PRODUCER_THREAD_ESTIMATE
          and self.throughput):
        # Should also include time remaining.
        # An example of time remaining would be ' ETA 00:00:11'.
        time_remaining_str = 'ETA ' + PrettyTime(time_remaining)
      else:
        time_remaining_str = ''
    else:
      throughput = ''
      time_remaining_str = ''

    format_str = ('{char_to_print} {objects_completed} {percentage_completed}'
                  ' {throughput} {time_remaining_str}')
    string_to_print = format_str.format(
        char_to_print=char_to_print,
        objects_completed=objects_completed,
        percentage_completed=percentage_completed,
        throughput=throughput,
        time_remaining_str=time_remaining_str)
    remaining_width = self.console_width - len(string_to_print)
    if not self.quiet_mode:
      stream.write(string_to_print + (max(remaining_width, 0) * ' ') + '\r')

  def CanHandleMessage(self, status_message):
    """Determines whether this manager is suitable for handling status_message.

    Args:
      status_message: The StatusMessage object to be analyzed.
    Returns:
      True if this message can be properly handled by this manager,
      False otherwise.
    """
    if isinstance(
        status_message,
        (SeekAheadMessage, ProducerThreadMessage, MetadataMessage, FinalMessage,
         RetryableErrorMessage, PerformanceSummaryMessage)):
      return True
    return False


class DataManager(StatusMessageManager):
  """Manages shared state for data operations.

  This manager is specific for data operations. Among its main functions,
  it receives incoming StatusMessages, storing all necessary data
  about the current and past states of the system necessary to display to the
  UI. It also provides methods for calculating metrics such as throughput and
  estimated time remaining. Finally, it provides methods for displaying messages
  to the UI.
  """

  class _ProgressInformation(object):
    """Class that contains all progress information needed for a given file.

    This _ProgressInformation is used as the value associated with a file_name
    in the dict that stores the information about all processed files.
    """

    def __init__(self, size):
      """Constructor of _ProgressInformation.

      Args:
        size: The total size of the file.
      """
      # Sum of all progress obtained in this operation.
      self.new_progress_sum = 0
      # Sum of all progress from previous operations (mainly for resuming
      # uploads or resuming downloads).
      self.existing_progress_sum = 0
      # Dict for tracking the progress for each individual component. Key is
      # of the form (component_num, dst_url) and correspondent element is a
      # tuple which stores the current progress obtained from this operation,
      # and the progress obtained from previous operations.
      self.dict = {}
      # The total size for the file
      self.size = size

  def __init__(self,
               update_message_period=1,
               update_spinner_period=0.6,
               sliding_throughput_period=5,
               first_throughput_latency=10,
               quiet_mode=False,
               custom_time=None,
               verbose=False,
               console_width=None):
    # pylint: disable=g-doc-args
    """Instantiates a DataManager.

    See argument documentation in StatusMessageManager base class.
    """
    # pylint: disable=g-doc-args
    super(DataManager,
          self).__init__(update_message_period=update_message_period,
                         update_spinner_period=update_spinner_period,
                         sliding_throughput_period=sliding_throughput_period,
                         first_throughput_latency=first_throughput_latency,
                         quiet_mode=quiet_mode,
                         custom_time=custom_time,
                         verbose=verbose,
                         console_width=console_width)

    self.first_item = True

    self.total_progress = 0  # Sum of progress for all threads.
    self.new_progress = 0
    self.existing_progress = 0

    # Dict containing individual progress for each file. Key is filename
    # (from src_url). It maps to a _ProgressInformation object.
    self.individual_file_progress = {}

    self.component_total = 0
    self.finished_components = 0
    self.existing_components = 0

  def GetProgress(self):
    """Gets the progress for a DataManager.

    Returns:
      The number of processed bytes in this operation.
    """
    return self.new_progress

  def _HandleFileDescription(self, status_message):
    """Handles a FileMessage that describes a file.

    Args:
      status_message: the FileMessage to be processed.
    """
    if not status_message.finished:
      # File started.
      if self.first_item and not self.custom_time:
        # Set initial time.
        self.refresh_message_time = status_message.time
        self.start_time = self.refresh_message_time
        self.last_throughput_time = self.refresh_message_time
        self.first_item = False

      # Gets file name (from src_url).
      file_name = status_message.src_url.url_string
      status_message.size = status_message.size if status_message.size else 0
      # Creates a new entry on individual_file_progress.
      self.individual_file_progress[file_name] = self._ProgressInformation(
          status_message.size)

      if self.num_objects_source >= EstimationSource.INDIVIDUAL_MESSAGES:
        # This ensures the file has not been counted on SeekAheadThread or
        # in ProducerThread.
        self.num_objects_source = EstimationSource.INDIVIDUAL_MESSAGES
        self.num_objects += 1
      if self.total_size_source >= EstimationSource.INDIVIDUAL_MESSAGES:
        # This ensures the file size has not been counted on SeekAheadThread or
        # in ProducerThread.
        self.total_size_source = EstimationSource.INDIVIDUAL_MESSAGES
        self.total_size += status_message.size

      self.object_report_change = True

    else:
      # File finished.
      self.objects_finished += 1
      file_name = status_message.src_url.url_string
      file_progress = self.individual_file_progress[file_name]
      total_bytes_transferred = (file_progress.new_progress_sum +
                                 file_progress.existing_progress_sum)
      # Ensures total_progress has the right value.
      self.total_progress += file_progress.size - total_bytes_transferred
      self.new_progress += file_progress.size - total_bytes_transferred
      self.last_progress_time = status_message.time
      # Deleting _ProgressInformation object to save memory.
      del self.individual_file_progress[file_name]
      self.object_report_change = True
      if (self.objects_finished == self.num_objects and
          self.num_objects_source == EstimationSource.PRODUCER_THREAD_FINAL):
        self.final_message = True

  def _IsFile(self, file_message):
    """Tells whether or not this FileMessage represent a file.

    This is needed because FileMessage is used by both files and components.

    Args:
      file_message: The FileMessage to be analyzed.
    Returns:
      Whether or not this represents a file.
    """
    message_type = file_message.message_type
    return (message_type == FileMessage.FILE_DOWNLOAD or
            message_type == FileMessage.FILE_UPLOAD or
            message_type == FileMessage.FILE_CLOUD_COPY or
            message_type == FileMessage.FILE_DAISY_COPY or
            message_type == FileMessage.FILE_LOCAL_COPY or
            message_type == FileMessage.FILE_REWRITE or
            message_type == FileMessage.FILE_HASH)

  def _HandleComponentDescription(self, status_message):
    """Handles a FileMessage that describes a component.

    Args:
      status_message: The FileMessage to be processed.
    """
    if (status_message.message_type == FileMessage.EXISTING_COMPONENT and
        not status_message.finished):
      # Existing component: have to ensure total_progress accounts for it.
      self.existing_components += 1

      file_name = status_message.src_url.url_string
      file_progress = self.individual_file_progress[file_name]

      key = (status_message.component_num, status_message.dst_url)
      file_progress.dict[key] = (0, status_message.size)
      file_progress.existing_progress_sum += status_message.size

      self.total_progress += status_message.size
      self.existing_progress += status_message.size

    elif ((status_message.message_type == FileMessage.COMPONENT_TO_UPLOAD or
           status_message.message_type == FileMessage.COMPONENT_TO_DOWNLOAD)):
      if not status_message.finished:
        # Component started.
        self.component_total += 1
        if status_message.message_type == FileMessage.COMPONENT_TO_DOWNLOAD:
          file_name = status_message.src_url.url_string
          file_progress = self.individual_file_progress[file_name]

          file_progress.existing_progress_sum += (
              status_message.bytes_already_downloaded)

          key = (status_message.component_num, status_message.dst_url)
          file_progress.dict[key] = (0, status_message.bytes_already_downloaded)

          self.total_progress += status_message.bytes_already_downloaded
          self.existing_progress += status_message.bytes_already_downloaded

      else:
        # Component finished.
        self.finished_components += 1
        file_name = status_message.src_url.url_string
        file_progress = self.individual_file_progress[file_name]

        key = (status_message.component_num, status_message.dst_url)
        last_update = (file_progress.dict[key] if key in file_progress.dict else
                       (0, 0))
        self.total_progress += status_message.size - sum(last_update)
        self.new_progress += status_message.size - sum(last_update)
        self.last_progress_time = status_message.time
        file_progress.new_progress_sum += (status_message.size -
                                           sum(last_update))
        file_progress.dict[key] = (status_message.size - last_update[1],
                                   last_update[1])

  def _HandleProgressMessage(self, status_message):
    """Handles a ProgressMessage that tracks progress of a file or component.

    Args:
      status_message: The ProgressMessage to be processed.
    """
    # Retrieving index and dict for this file.
    file_name = status_message.src_url.url_string
    file_progress = self.individual_file_progress[file_name]

    # Retrieves last update ((0,0) if no previous update) for this file or
    # component. To ensure uniqueness (among components),
    # we use a (component_num, dst_url) tuple as our key.
    key = (status_message.component_num, status_message.dst_url)
    last_update = (file_progress.dict[key] if key in file_progress.dict else
                   (0, 0))
    status_message.processed_bytes -= last_update[1]
    file_progress.new_progress_sum += (status_message.processed_bytes -
                                       last_update[0])
    # Updates total progress with new update from component.
    self.total_progress += status_message.processed_bytes - last_update[0]
    self.new_progress += status_message.processed_bytes - last_update[0]
    # Updates file_progress.dict on component's key.
    file_progress.dict[key] = (status_message.processed_bytes, last_update[1])
    self.last_progress_time = status_message.time

  def ProcessMessage(self, status_message, stream):
    """Processes a message from _MainThreadUIQueue or _UIThread.

    Args:
      status_message: The StatusMessage item to be processed.
      stream: Stream to print messages. Here only for SeekAheadThread
    """
    self.object_report_change = False
    if isinstance(status_message, ProducerThreadMessage):
      # ProducerThread info.
      self._HandleProducerThreadMessage(status_message)

    elif isinstance(status_message, SeekAheadMessage):
      # SeekAheadThread info.
      self._HandleSeekAheadMessage(status_message, stream)

    elif isinstance(status_message, FileMessage):
      if self._IsFile(status_message):
        # File info.
        self._HandleFileDescription(status_message)
      else:
        # Component info.
        self._HandleComponentDescription(status_message)
      LogPerformanceSummaryParams(file_message=status_message)

    elif isinstance(status_message, ProgressMessage):
      # Progress info.
      self._HandleProgressMessage(status_message)

    elif isinstance(status_message, RetryableErrorMessage):
      LogRetryableError(status_message)

    elif isinstance(status_message, PerformanceSummaryMessage):
      self._HandlePerformanceSummaryMessage(status_message)

    self.old_progress.append(
        self._ThroughputInformation(self.new_progress, status_message.time))

  def PrintProgress(self, stream=sys.stderr):
    """Prints progress and throughput/time estimation.

    If a ProducerThreadMessage or SeekAheadMessage has been provided,
    it outputs the number of files completed, number of total files,
    the current progress, the total size, and the percentage it
    represents.
    If none of those have been provided, it only includes the number of files
    completed, the current progress and total size (which might be updated),
    with no percentage as we do not know if more files are coming.
    It may also include time estimation (available only given
    ProducerThreadMessage or SeekAheadMessage provided) and throughput. For that
    to happen, there is an extra condition of at least first_throughput_latency
    seconds having been passed since the UIController started, and that
    either the ProducerThread or the SeekAheadThread have estimated total
    number of files and total size.

    Args:
      stream: Stream to print messages. Usually sys.stderr, but customizable
              for testing.
    """
    # Time to update all information.
    total_remaining = self.total_size - self.total_progress

    if self.throughput:
      time_remaining = total_remaining / self.throughput
    else:
      time_remaining = None

    char_to_print = self.GetSpinner()

    if self.num_objects_source <= EstimationSource.SEEK_AHEAD_THREAD:
      # An example of objects_completed here would be ' [2/3 files]'.
      objects_completed = ('[' + DecimalShort(self.objects_finished) + '/' +
                           DecimalShort(self.num_objects) + ' files]')
    else:
      # An example of objects_completed here would be ' [2 files]'.
      objects_completed = '[' + DecimalShort(self.objects_finished) + ' files]'

    # An example of bytes_progress would be '[101.0 MiB/1.0 GiB]'.
    bytes_progress = ('[%s/%s]' % (BytesToFixedWidthString(
        self.total_progress), BytesToFixedWidthString(self.total_size)))

    if self.total_size_source <= EstimationSource.SEEK_AHEAD_THREAD:
      if self.num_objects == self.objects_finished:
        percentage = '100'
      else:
        percentage = (
            '%3d' %
            min(99, int(100 * float(self.total_progress) / self.total_size)))
      percentage_completed = percentage + '% Done'
    else:
      percentage_completed = ''

    if (self.refresh_message_time - self.start_time
        > self.first_throughput_latency):
      # Should also include throughput.
      # An example of throughput here would be ' 82.3 MiB/s'
      throughput = BytesToFixedWidthString(self.throughput) + '/s'

      if (self.total_size_source <= EstimationSource.PRODUCER_THREAD_ESTIMATE
          and self.throughput):
        # Should also include time remaining.
        # An example of time remaining would be ' ETA 00:00:11'.
        time_remaining_str = 'ETA ' + PrettyTime(time_remaining)
      else:
        time_remaining_str = ''
    else:
      throughput = ''
      time_remaining_str = ''

    format_str = ('{char_to_print} {objects_completed}{bytes_progress}'
                  ' {percentage_completed} {throughput} {time_remaining_str}')
    string_to_print = format_str.format(
        char_to_print=char_to_print,
        objects_completed=objects_completed,
        bytes_progress=bytes_progress,
        percentage_completed=percentage_completed,
        throughput=throughput,
        time_remaining_str=time_remaining_str)
    remaining_width = self.console_width - len(string_to_print)
    if not self.quiet_mode:
      stream.write(string_to_print + (max(remaining_width, 0) * ' ') + '\r')

  def CanHandleMessage(self, status_message):
    """Determines whether this manager is suitable for handling status_message.

    Args:
      status_message: The StatusMessage object to be analyzed.
    Returns:
      True if this message can be properly handled by this manager,
      False otherwise.
    """
    if isinstance(status_message, (
        SeekAheadMessage,
        ProducerThreadMessage,
        FileMessage,
        ProgressMessage,
        FinalMessage,
        RetryableErrorMessage,
        PerformanceSummaryMessage,
    )):
      return True
    return False


class UIController(object):
  """Controller UI class to integrate _MainThreadUIQueue and _UIThread.

  This class receives messages from _MainThreadUIQueue and _UIThread and send
  them to an appropriate manager, which will then processes and store data about
  them.
  """

  def __init__(self,
               update_message_period=1,
               update_spinner_period=0.6,
               sliding_throughput_period=5,
               first_throughput_latency=10,
               quiet_mode=False,
               custom_time=None,
               verbose=False,
               dump_status_messages_file=None):
    """Instantiates a UIController.

    Args:
      update_message_period: Minimum period for refreshing and  displaying
          new information. A non-positive value will ignore any time
          restrictions imposed by this field.
      update_spinner_period: Minimum period for refreshing and displaying the
          spinner. A non-positive value will ignore any time restrictions
          imposed by this field.
      sliding_throughput_period: Sliding period for throughput calculation. A
          non-positive value will make it impossible to calculate the
          throughput.
      first_throughput_latency: Minimum waiting time before actually displaying
          throughput info. A non-positive value will ignore any time
          restrictions imposed by this field.
      quiet_mode: If True, do not print status messages (but still process
          them for analytics reporting as necessary).
      custom_time: If a custom start_time is desired. Used for testing.
      verbose: Tells whether or not the operation is on verbose mode.
      dump_status_messages_file: File path for logging all received status
          messages, for debugging purposes.
    """
    self.verbose = verbose
    self.update_message_period = update_message_period
    self.update_spinner_period = update_spinner_period
    self.sliding_throughput_period = sliding_throughput_period
    self.first_throughput_latency = first_throughput_latency
    self.manager = None
    self.quiet_mode = quiet_mode
    self.custom_time = custom_time
    self.console_width = 80  # Console width. Passed to manager.
    # List storing all estimation messages from SeekAheadThread or
    # ProducerThread. This is used when we still do not know which manager to
    # use.
    self.early_estimation_messages = []
    self.printed_final_message = False
    self.dump_status_message_fp = None
    if dump_status_messages_file:
      self.dump_status_message_fp = open(dump_status_messages_file, 'ab')

  def _HandleMessage(self, status_message, stream, cur_time=None):
    """Processes a message, updates throughput and prints progress.

    Args:
      status_message: Message to be processed. Could be None if UIThread cannot
                      retrieve message from status_queue.
      stream: stream to print messages. Usually sys.stderr, but customizable
              for testing.
      cur_time: Message time. Used to determine if it is time to refresh
                output, or calculate throughput.
    """
    self.manager.ProcessMessage(status_message, stream)
    if self.manager.ShouldPrintProgress(cur_time):
      if self.manager.ShouldTrackThroughput(cur_time):
        self.manager.UpdateThroughput(cur_time, self.manager.GetProgress())
      self.manager.PrintProgress(stream)
      self.manager.refresh_message_time = cur_time
    if self.manager.ShouldPrintSpinner(cur_time):
      self.manager.PrintSpinner(stream)
      self.manager.refresh_spinner_time = cur_time
    if ((isinstance(status_message, FinalMessage) or self.manager.final_message)
        and self.manager.num_objects and not self.printed_final_message):
      self.printed_final_message = True
      LogPerformanceSummaryParams(
          num_objects_transferred=self.manager.num_objects)
      self.manager.PrintFinalSummaryMessage(stream)

  def Call(self, status_message, stream, cur_time=None):
    """Coordinates UI manager and calls appropriate function to handle message.

    Args:
      status_message: Message to be processed. Could be None if UIThread cannot
                      retrieve message from status_queue.
      stream: Stream to print messages. Usually sys.stderr, but customizable
              for testing.
      cur_time: Message time. Used to determine if it is time to refresh
                output, or calculate throughput.
    """
    if not isinstance(status_message, StatusMessage):
      if status_message == _ZERO_TASKS_TO_DO_ARGUMENT and not self.manager:
        # Create a manager to handle early estimation messages before returning.
        self.manager = (DataManager(
            update_message_period=self.update_message_period,
            update_spinner_period=self.update_spinner_period,
            sliding_throughput_period=self.sliding_throughput_period,
            first_throughput_latency=self.first_throughput_latency,
            quiet_mode=self.quiet_mode,
            custom_time=self.custom_time,
            verbose=self.verbose,
            console_width=self.console_width))
        for estimation_message in self.early_estimation_messages:
          self._HandleMessage(estimation_message,
                              stream,
                              cur_time=estimation_message.time)
      return
    if self.dump_status_message_fp:
      # TODO: Add Unicode support to string methods on message classes.
      # Currently, dump will fail with a UnicodeEncodeErorr if the message
      # class contains a Unicode attribute.
      self.dump_status_message_fp.write(str(status_message))
      self.dump_status_message_fp.write('\n')
    if not cur_time:
      cur_time = status_message.time
    if not self.manager:
      if (isinstance(status_message, SeekAheadMessage) or
          isinstance(status_message, ProducerThreadMessage)):
        self.early_estimation_messages.append(status_message)
        return
      elif isinstance(status_message, MetadataMessage):
        self.manager = (MetadataManager(
            update_message_period=self.update_message_period,
            update_spinner_period=self.update_spinner_period,
            sliding_throughput_period=self.sliding_throughput_period,
            first_throughput_latency=self.first_throughput_latency,
            quiet_mode=self.quiet_mode,
            custom_time=self.custom_time,
            verbose=self.verbose,
            console_width=self.console_width))
        for estimation_message in self.early_estimation_messages:
          self._HandleMessage(estimation_message, stream, cur_time)
      else:
        self.manager = (DataManager(
            update_message_period=self.update_message_period,
            update_spinner_period=self.update_spinner_period,
            sliding_throughput_period=self.sliding_throughput_period,
            first_throughput_latency=self.first_throughput_latency,
            quiet_mode=self.quiet_mode,
            custom_time=self.custom_time,
            verbose=self.verbose,
            console_width=self.console_width))

        for estimation_message in self.early_estimation_messages:
          self._HandleMessage(estimation_message, stream, cur_time)
    if not self.manager.CanHandleMessage(status_message):
      if (isinstance(status_message, FileMessage) or
          isinstance(status_message, ProgressMessage)):
        # We have to create a DataManager to handle this data message. This is
        # to avoid a possible race condition where MetadataMessages are sent
        # before data messages. As such, this means that the DataManager has
        # priority, and whenever a data message is received, we ignore the
        # MetadataManager if one exists, and start a DataManager from scratch.
        # This can be done because we do not need any MetadataMessages to
        # properly handle a data operation. It could be useful to send the
        # early estimation messages, if those are available.
        self.manager = (DataManager(
            update_message_period=self.update_message_period,
            update_spinner_period=self.update_spinner_period,
            sliding_throughput_period=self.sliding_throughput_period,
            first_throughput_latency=self.first_throughput_latency,
            custom_time=self.custom_time,
            verbose=self.verbose,
            console_width=self.console_width))
        for estimation_message in self.early_estimation_messages:
          self._HandleMessage(estimation_message, stream, cur_time)
      else:
        # No need to handle this message.
        return
    self._HandleMessage(status_message, stream, cur_time)


class MainThreadUIQueue(object):
  """Handles status display and processing in the main thread / master process.

  This class emulates a queue to cover main-thread activity before or after
  Apply, as well as for the single-threaded, single-process case, i.e.,
  _SequentialApply. When multiple threads or processes are used during calls
  to Apply, the main thread is waiting for work to complete, and this queue
  must remain unused until Apply returns. Code producing arguments for
  Apply (such as the NameExpansionIterator) must not post messages to this
  queue to avoid race conditions with the UIThread.

  This class sends the messages it receives to UIController, which
  decides the correct course of action.
  """

  def __init__(self, stream, ui_controller):
    """Instantiates a _MainThreadUIQueue.

    Args:
      stream: Stream for printing messages.
      ui_controller: UIController to manage messages.
    """

    super(MainThreadUIQueue, self).__init__()
    self.ui_controller = ui_controller
    self.stream = stream

  # pylint: disable=invalid-name, unused-argument
  def put(self, status_message, timeout=None):
    self.ui_controller.Call(status_message, self.stream)

  # pylint: enable=invalid-name, unused-argument


class UIThread(threading.Thread):
  """Responsible for centralized printing across multiple processes/threads.

  This class pulls status messages that are posted to the centralized status
  queue and coordinates displaying status and progress to the user. It is
  used only during calls to _ParallelApply, which in turn is called only when
  multiple threads and/or processes are used.

  This class sends the messages it receives to UIController, which
  decides the correct course of action.
  """

  def __init__(self, status_queue, stream, ui_controller, timeout=1):
    """Instantiates a _UIThread.

    Args:
      status_queue: Queue for reporting status updates.
      stream: Stream for printing messages.
      ui_controller: UI controller to manage messages.
      timeout: Timeout for getting a message.
    """

    super(UIThread, self).__init__()
    self.status_queue = status_queue
    self.stream = stream
    self.timeout = timeout
    self.ui_controller = ui_controller
    self.start()

  def run(self):
    try:
      while True:
        try:
          status_message = self.status_queue.get(timeout=self.timeout)
        except Queue.Empty:
          status_message = None
          continue
        self.ui_controller.Call(status_message, self.stream)
        if status_message == _ZERO_TASKS_TO_DO_ARGUMENT:
          # Item from MainThread to indicate we are done.
          break
    except Exception as e:  # pylint:disable=broad-except
      self.stream.write('Exception in UIThread: %s\n' % e)
