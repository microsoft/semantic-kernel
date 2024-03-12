# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Module with logging related functionality for calliope."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from collections import OrderedDict
import contextlib
import copy
import datetime
import json
import logging
import os
import sys
import time

from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console.style import parser as style_parser
from googlecloudsdk.core.console.style import text
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times

import six


LOG_FILE_ENCODING = 'utf-8'

DEFAULT_VERBOSITY = logging.WARNING
DEFAULT_VERBOSITY_STRING = 'warning'
DEFAULT_USER_OUTPUT_ENABLED = True

_VERBOSITY_LEVELS = [
    ('debug', logging.DEBUG),
    ('info', logging.INFO),
    ('warning', logging.WARNING),
    ('error', logging.ERROR),
    ('critical', logging.CRITICAL),
    ('none', logging.CRITICAL + 10)]
VALID_VERBOSITY_STRINGS = dict(_VERBOSITY_LEVELS)
LOG_FILE_EXTENSION = '.log'
# datastore upload and download creates temporary sql3 files in the log dir.
_KNOWN_LOG_FILE_EXTENSIONS = [LOG_FILE_EXTENSION, '.sql3']

# This is a regular expression pattern that matches the format of the date
# marker that marks the beginning of a new log line in a log file. It can be
# used in parsing log files.
LOG_PREFIX_PATTERN = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}'
# Regex used to extract used surfaces from user logs.
USED_SURFACE_PATTERN = r'Running \[gcloud\.([-\w\.]+)\.[-\w]+\]'

# These are the formats for the log directories and files.
# For example, `logs/1970.01.01/12.00.00.000000.log`.
DAY_DIR_FORMAT = '%Y.%m.%d'
FILENAME_FORMAT = '%H.%M.%S.%f'

# These are for Structured (JSON) Log Records
STRUCTURED_RECORD_VERSION = '0.0.1'
STRUCTURED_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%3f%Ez'

# These fields are ordered by how they will appear in the log file
# for consistency. All values are strings.
# (Output Field, LogRecord Field, Description)
STRUCTURED_RECORD_FIELDS = [
    ('version', 'version',
     'Semantic version of the message format. E.g. v0.0.1'),
    ('verbosity', 'levelname',
     'Logging Level: e.g. debug, info, warn, error, critical, exception.'),
    ('timestamp', 'asctime', 'UTC time event logged'),
    ('message', 'message', 'Log/Error message.'),
    ('error', 'error',
     'Actual exception or error raised, if message contains exception data.'),
]
REQUIRED_STRUCTURED_RECORD_FIELDS = OrderedDict((x[:2] for x in
                                                 STRUCTURED_RECORD_FIELDS))


class _NullHandler(logging.Handler, object):
  """A replication of python2.7's logging.NullHandler.

  We recreate this class here to ease python2.6 compatibility.
  """

  def handle(self, record):
    pass

  def emit(self, record):
    pass

  def createLock(self):
    self.lock = None


class _UserOutputFilter(object):
  """A filter to turn on and off user output.

  This filter is used by the ConsoleWriter to determine if output messages
  should be printed or not.
  """

  def __init__(self, enabled):
    """Creates the filter.

    Args:
      enabled: bool, True to enable output, false to suppress.
    """
    self.enabled = enabled


class _StreamWrapper(object):
  """A class to hold an output stream that we can manipulate."""

  def __init__(self, stream):
    """Creates the stream wrapper.

    Args:
      stream: The stream to hold on to.
    """
    self.stream = stream


class _ConsoleWriter(object):
  """A class that wraps stdout or stderr so we can control how it gets logged.

  This class is a stripped down file-like object that provides the basic
  writing methods.  When you write to this stream, if it is enabled, it will be
  written to stdout.  All strings will also be logged at DEBUG level so they
  can be captured by the log file.
  """

  def __init__(self, logger, output_filter, stream_wrapper, always_flush=False):
    """Creates a new _ConsoleWriter wrapper.

    Args:
      logger: logging.Logger, The logger to log to.
      output_filter: _UserOutputFilter, Used to determine whether to write
        output or not.
      stream_wrapper: _StreamWrapper, The wrapper for the output stream,
        stdout or stderr.
      always_flush: bool, always flush stream_wrapper, default to False.
    """
    self.__logger = logger
    self.__filter = output_filter
    self.__stream_wrapper = stream_wrapper
    self.__always_flush = always_flush

  def ParseMsg(self, msg):
    """Converts msg to a console safe pair of plain and ANSI-annotated strings.

    Args:
      msg: str or text.TypedText, the message to parse into plain and
        ANSI-annotated strings.
    Returns:
      str, str: A plain text string and a string that may also contain ANSI
        constrol sequences. If ANSI is not supported or color is disabled,
        then the second string will be identical to the first.
    """
    plain_text, styled_text = msg, msg
    if isinstance(msg, text.TypedText):
      typed_text_parser = style_parser.GetTypedTextParser()
      plain_text = typed_text_parser.ParseTypedTextToString(msg, stylize=False)
      styled_text = typed_text_parser.ParseTypedTextToString(
          msg, stylize=self.isatty())
    plain_text = console_attr.SafeText(
        plain_text, encoding=LOG_FILE_ENCODING, escape=False)
    styled_text = console_attr.SafeText(
        styled_text, encoding=LOG_FILE_ENCODING, escape=False)
    return plain_text, styled_text

  def Print(self, *tokens):
    """Writes the given tokens to the output stream, and adds a newline.

    This method has the same output behavior as the builtin print method but
    respects the configured verbosity.

    Args:
      *tokens: str or text.TypedTextor any object with a str() or unicode()
        method, The messages to print, which are joined with ' '.
    """
    plain_tokens, styled_tokens = [], []
    for token in tokens:
      plain_text, styled_text = self.ParseMsg(token)
      plain_tokens.append(plain_text)
      styled_tokens.append(styled_text)

    plain_text = ' '.join(plain_tokens) + '\n'
    styled_text = ' '.join(styled_tokens) + '\n'
    self._Write(plain_text, styled_text)

  def GetConsoleWriterStream(self):
    """Returns the console writer output stream."""
    return self.__stream_wrapper.stream

  def _Write(self, msg, styled_msg):
    """Just a helper so we don't have to double encode from Print and write.

    Args:
      msg: A text string that only has characters that are safe to encode with
        utf-8.
      styled_msg: A text string with the same properties as msg but also
        contains ANSI control sequences.
    """
    # The log file always uses utf-8 encoding, just give it the string.
    self.__logger.info(msg)

    if self.__filter.enabled:
      # Make sure the string is safe to print in the console. The console might
      # have a more restrictive encoding than utf-8.
      stream_encoding = console_attr.GetConsoleAttr().GetEncoding()
      stream_msg = console_attr.SafeText(
          styled_msg, encoding=stream_encoding, escape=False)
      if six.PY2:
        # Encode to byte strings for output only on Python 2.
        stream_msg = styled_msg.encode(stream_encoding or 'utf-8', 'replace')
      self.__stream_wrapper.stream.write(stream_msg)
      if self.__always_flush:
        self.flush()

  # pylint: disable=g-bad-name, This must match file-like objects
  def write(self, msg):
    plain_text, styled_text = self.ParseMsg(msg)
    self._Write(plain_text, styled_text)

  # pylint: disable=g-bad-name, This must match file-like objects
  def writelines(self, lines):
    for line in lines:
      self.write(line)

  # pylint: disable=g-bad-name, This must match file-like objects
  def flush(self):
    if self.__filter.enabled:
      self.__stream_wrapper.stream.flush()

  def isatty(self):
    isatty = getattr(self.__stream_wrapper.stream, 'isatty', None)
    return isatty() if isatty else False


def _FmtString(fmt):
  """Gets the correct format string to use based on the Python version.

  Args:
    fmt: text string, The format string to convert.

  Returns:
    A byte string on Python 2 or the original string on Python 3.
  """
  # On Py2, log messages come in as both text and byte strings so the format
  # strings needs to be bytes so it doesn't coerce byte messages to unicode.
  # On Py3, only text strings come in and if the format is bytes it can't
  # combine with the log message.
  if six.PY2:
    return fmt.encode('utf-8')
  return fmt


@contextlib.contextmanager
def _SafeDecodedLogRecord(record, encoding):
  """Temporarily modifies a log record to make the message safe to print.

  Python logging creates a single log record for each log event. Each handler
  is given that record and asked format it. To avoid unicode issues, we decode
  all the messages in case they are byte strings. Doing this we also want to
  ensure the resulting string is able to be printed to the given output target.

  Some handlers target the console (which can have many different encodings) and
  some target the log file (which we always write as utf-8. If we modify the
  record, depending on the order of handlers, the log message could lose
  information along the way.

  For example, if the user has an ascii console, we replace non-ascii characters
  in the string with '?' to print. Then if the log file handler is called, the
  original unicode data is gone, even though it could successfully be printed
  to the log file. This context manager changes the log record briefly so it can
  be formatted without changing it for later handlers.

  Args:
    record: The log record.
    encoding: The name of the encoding to SafeDecode with.
  Yields:
    None, yield is necessary as this is a context manager.
  """
  original_msg = record.msg
  try:
    record.msg = console_attr.SafeText(
        record.msg, encoding=encoding, escape=False)
    yield
  finally:
    record.msg = original_msg


class _LogFileFormatter(logging.Formatter):
  """A formatter for log file contents."""
  # TODO(b/116495229): Add a test to ensure consitency.
  # Note: if this ever changes, please update LOG_PREFIX_PATTERN
  FORMAT = _FmtString('%(asctime)s %(levelname)-8s %(name)-15s %(message)s')

  def __init__(self):
    super(_LogFileFormatter, self).__init__(fmt=_LogFileFormatter.FORMAT)

  def format(self, record):
    record = copy.copy(record)

    if isinstance(record.msg, text.TypedText):
      record.msg = style_parser.GetTypedTextParser().ParseTypedTextToString(
          record.msg, stylize=False)

    # There are some cases where record.args ends up being a dict.
    if isinstance(record.args, tuple):
      new_args = []
      for arg in record.args:
        if isinstance(arg, text.TypedText):
          arg = style_parser.GetTypedTextParser().ParseTypedTextToString(
              arg, stylize=False)
        new_args.append(arg)
      record.args = tuple(new_args)
    # The log file handler expects text strings always, and encodes them to
    # utf-8 before writing to the file.
    with _SafeDecodedLogRecord(record, LOG_FILE_ENCODING):
      msg = super(_LogFileFormatter, self).format(record)
    return msg


class _ConsoleFormatter(logging.Formatter):
  """A formatter for the console logger, handles colorizing messages."""

  TIMESTAMP = _FmtString('%(asctime)s ')
  LEVEL = _FmtString('%(levelname)s:')
  MESSAGE = _FmtString(' %(message)s')

  RED = _FmtString('\033[1;31m')
  YELLOW = _FmtString('\033[1;33m')
  END = _FmtString('\033[0m')

  DEFAULT_FORMAT = LEVEL + MESSAGE
  DEFAULT_FORMATS = {
      'detailed': TIMESTAMP + LEVEL + MESSAGE,
  }

  COLOR_FORMATS = {
      'standard': {
          logging.WARNING: YELLOW + LEVEL + END + MESSAGE,
          logging.ERROR: RED + LEVEL + END + MESSAGE,
          logging.FATAL: RED + LEVEL + MESSAGE + END,
      },
      'detailed': {
          logging.WARNING: TIMESTAMP + YELLOW + LEVEL + END + MESSAGE,
          logging.ERROR: TIMESTAMP + RED + LEVEL + END + MESSAGE,
          logging.FATAL: RED + TIMESTAMP + LEVEL + MESSAGE + END,
      }
  }

  def __init__(self, out_stream):
    super(_ConsoleFormatter, self).__init__()

    console_log_format = properties.VALUES.core.console_log_format.Get()
    use_color = not properties.VALUES.core.disable_color.GetBool(
        validate=False)
    use_color &= out_stream.isatty()
    use_color &= console_attr.GetConsoleAttr().SupportsAnsi()

    self._formats = (
        _ConsoleFormatter.COLOR_FORMATS.get(console_log_format)
        if use_color else {})
    self._default_format = _ConsoleFormatter.DEFAULT_FORMATS.get(
        console_log_format, _ConsoleFormatter.DEFAULT_FORMAT)

  def format(self, record):
    fmt = self._formats.get(record.levelno, self._default_format)
    # We are doing some hackery here to change the log format on the fly. In
    # Python 3, they changed the internal workings of the formatter class so we
    # need to do something a little different to maintain the behavior.
    self._fmt = fmt
    if six.PY3:
      # pylint: disable=protected-access
      self._style._fmt = fmt
    # Convert either bytes or text into a text string that is safe for printing.
    # This is the first time we are able to intercept messages that come
    # directly from the log methods (as opposed to the out.write() methods
    # above).
    stream_encoding = console_attr.GetConsoleAttr().GetEncoding()
    with _SafeDecodedLogRecord(record, stream_encoding):
      msg = super(_ConsoleFormatter, self).format(record)
    if six.PY2:
      msg = msg.encode(stream_encoding or 'utf-8', 'replace')
    return msg


class _JsonFormatter(logging.Formatter):
  """A formatter that handles formatting log messages as JSON."""

  def __init__(self,
               required_fields,
               json_serializer=None,
               json_encoder=None):

    super(_JsonFormatter, self).__init__()
    self.required_fields = required_fields
    self.json_encoder = json_encoder
    self.json_serializer = json_serializer or json.dumps
    self.default_time_format = STRUCTURED_TIME_FORMAT

  def GetErrorDict(self, log_record):
    """Extract exception info from a logging.LogRecord as an OrderedDict."""
    error_dict = OrderedDict()
    if log_record.exc_info:
      if not log_record.exc_text:
        log_record.exc_text = self.formatException(log_record.exc_info)

      if issubclass(type(log_record.msg), BaseException):
        error_dict['type'] = type(log_record.msg).__name__
        error_dict['details'] = six.text_type(log_record.msg)
        error_dict['stacktrace'] = getattr(log_record.msg,
                                           '__traceback__', None)
      elif issubclass(type(log_record.exc_info[0]), BaseException):
        error_dict['type'] = log_record.exc_info[0]
        error_dict['details'] = log_record.exc_text
        error_dict['stacktrace'] = log_record.exc_info[2]
      else:
        error_dict['type'] = log_record.exc_text
        error_dict['details'] = log_record.exc_text
        error_dict['stacktrace'] = log_record.exc_text
      return error_dict
    return None

  def BuildLogMsg(self, log_record):
    """Converts a logging.LogRecord object to a JSON serializable OrderedDict.

    Utilizes supplied set of required_fields to determine output fields.

    Args:
      log_record: logging.LogRecord, log record to be converted

    Returns:
      OrderedDict of required_field values.
    """
    message_dict = OrderedDict()
    # This perserves the order in the output for each JSON message
    for outfield, logfield in six.iteritems(self.required_fields):
      if outfield == 'version':
        message_dict[outfield] = STRUCTURED_RECORD_VERSION
      else:
        message_dict[outfield] = log_record.__dict__.get(logfield)
    return message_dict

  def LogRecordToJson(self, log_record):
    """Returns a json string of the log message."""
    log_message = self.BuildLogMsg(log_record)
    if not log_message.get('error'):
      log_message.pop('error')

    return self.json_serializer(log_message,
                                cls=self.json_encoder)

  def formatTime(self, record, datefmt=None):
    return times.FormatDateTime(
        times.GetDateTimeFromTimeStamp(record.created),
        fmt=datefmt,
        tzinfo=times.UTC)

  def format(self, record):
    """Formats a log record and serializes to json."""
    record.__dict__['error'] = self.GetErrorDict(record)
    record.message = record.getMessage()
    record.asctime = self.formatTime(record, self.default_time_format)
    return self.LogRecordToJson(record)


class _ConsoleLoggingFormatterMuxer(logging.Formatter):
  """Logging Formatter Composed of other formatters."""

  def __init__(self,
               structured_formatter,
               stream_writter,
               default_formatter=None):
    logging.Formatter.__init__(self)
    self.default_formatter = default_formatter or logging.Formatter
    self.structured_formatter = structured_formatter
    self.terminal = stream_writter.isatty()

  def ShowStructuredOutput(self):
    """Returns True if output should be Structured, False otherwise."""
    show_messages = properties.VALUES.core.show_structured_logs.Get()
    if any([show_messages == 'terminal' and self.terminal,
            show_messages == 'log' and not self.terminal,
            show_messages == 'always']):
      return True

    return False

  def format(self, record):
    """Formats the record using the proper formatter."""
    show_structured_output = self.ShowStructuredOutput()

    # The logged msg was a TypedText so convert msg to a normal str.
    stylize = self.terminal and not show_structured_output
    record = copy.copy(record)
    if isinstance(record.msg, text.TypedText):
      record.msg = style_parser.GetTypedTextParser().ParseTypedTextToString(
          record.msg, stylize=stylize)

    # There are some cases where record.args ends up being a dict.
    if isinstance(record.args, tuple):
      new_args = []
      for arg in record.args:
        if isinstance(arg, text.TypedText):
          arg = style_parser.GetTypedTextParser().ParseTypedTextToString(
              arg, stylize=stylize)
        new_args.append(arg)
      record.args = tuple(new_args)

    if show_structured_output:
      return self.structured_formatter.format(record)
    return self.default_formatter.format(record)


class NoHeaderErrorFilter(logging.Filter):
  """Filter out urllib3 Header Parsing Errors due to a urllib3 bug.

  See https://bugs.python.org/issue36226
  """

  def filter(self, record):
    """Filter out Header Parsing Errors."""
    return 'Failed to parse headers' not in record.getMessage()


class _LogManager(object):
  """A class to manage the logging handlers based on how calliope is being used.

  We want to always log to a file, in addition to logging to stdout if in CLI
  mode.  This sets up the required handlers to do this.
  """
  FILE_ONLY_LOGGER_NAME = '___FILE_ONLY___'

  def __init__(self):
    self._file_formatter = _LogFileFormatter()

    # Set up the root logger, it accepts all levels.
    self._root_logger = logging.getLogger()
    self._root_logger.setLevel(logging.NOTSET)

    # This logger will get handlers for each output file, but will not propagate
    # to the root logger.  This allows us to log exceptions and errors to the
    # files without it showing up in the terminal.
    self.file_only_logger = logging.getLogger(_LogManager.FILE_ONLY_LOGGER_NAME)
    # Accept all log levels for files.
    self.file_only_logger.setLevel(logging.NOTSET)
    self.file_only_logger.propagate = False

    self._logs_dirs = []

    self._console_formatter = None
    self._user_output_filter = _UserOutputFilter(DEFAULT_USER_OUTPUT_ENABLED)
    self.stdout_stream_wrapper = _StreamWrapper(None)
    self.stderr_stream_wrapper = _StreamWrapper(None)

    self.stdout_writer = _ConsoleWriter(self.file_only_logger,
                                        self._user_output_filter,
                                        self.stdout_stream_wrapper)
    self.stderr_writer = _ConsoleWriter(self.file_only_logger,
                                        self._user_output_filter,
                                        self.stderr_stream_wrapper,
                                        always_flush=True)

    self.verbosity = None
    self.user_output_enabled = None
    self.current_log_file = None
    self.Reset(sys.stdout, sys.stderr)

  def Reset(self, stdout, stderr):
    """Resets all logging functionality to its default state."""
    # Clears any existing logging handlers.
    self._root_logger.handlers[:] = []

    # Refresh the streams for the console writers.
    self.stdout_stream_wrapper.stream = stdout
    self.stderr_stream_wrapper.stream = stderr

    # Configure Formatters
    json_formatter = _JsonFormatter(REQUIRED_STRUCTURED_RECORD_FIELDS)
    std_console_formatter = _ConsoleFormatter(stderr)
    console_formatter = _ConsoleLoggingFormatterMuxer(
        json_formatter,
        self.stderr_writer,
        default_formatter=std_console_formatter)
    # Reset the color and structured output handling.
    self._console_formatter = console_formatter
    # A handler to redirect logs to stderr, this one is standard.
    self.stderr_handler = logging.StreamHandler(stderr)
    self.stderr_handler.setFormatter(self._console_formatter)
    self.stderr_handler.setLevel(DEFAULT_VERBOSITY)
    self._root_logger.addHandler(self.stderr_handler)

    # Reset all the log file handlers.
    for f in self.file_only_logger.handlers:
      f.close()
    self.file_only_logger.handlers[:] = []
    self.file_only_logger.addHandler(_NullHandler())
    self.file_only_logger.setLevel(logging.NOTSET)

    # Reset verbosity and output settings.
    self.SetVerbosity(None)
    self.SetUserOutputEnabled(None)
    self.current_log_file = None

    logging.getLogger('urllib3.connectionpool').addFilter(
        NoHeaderErrorFilter())

  def SetVerbosity(self, verbosity):
    """Sets the active verbosity for the logger.

    Args:
      verbosity: int, A verbosity constant from the logging module that
        determines what level of logs will show in the console. If None, the
        value from properties or the default will be used.

    Returns:
      int, The current verbosity.
    """
    if verbosity is None:
      # Try to load from properties if set.
      verbosity_string = properties.VALUES.core.verbosity.Get()
      if verbosity_string is not None:
        verbosity = VALID_VERBOSITY_STRINGS.get(verbosity_string.lower())
    if verbosity is None:
      # Final fall back to default verbosity.
      verbosity = DEFAULT_VERBOSITY

    if self.verbosity == verbosity:
      return self.verbosity

    self.stderr_handler.setLevel(verbosity)

    old_verbosity = self.verbosity
    self.verbosity = verbosity
    return old_verbosity

  def SetUserOutputEnabled(self, enabled):
    """Sets whether user output should go to the console.

    Args:
      enabled: bool, True to enable output, False to suppress.  If None, the
        value from properties or the default will be used.

    Returns:
      bool, The old value of enabled.
    """
    if enabled is None:
      enabled = properties.VALUES.core.user_output_enabled.GetBool(
          validate=False)
    if enabled is None:
      enabled = DEFAULT_USER_OUTPUT_ENABLED

    self._user_output_filter.enabled = enabled

    old_enabled = self.user_output_enabled
    self.user_output_enabled = enabled
    return old_enabled

  def _GetMaxLogDays(self):
    """Gets the max log days for the logger.

    Returns:
      max_log_days: int, the maximum days for log file retention
    """
    # Fetch from properties. Defaults to 30 if unset.
    return properties.VALUES.core.max_log_days.GetInt()

  def _GetMaxAge(self):
    """Gets max_log_day's worth of seconds."""
    return 60 * 60 * 24 * self._GetMaxLogDays()

  def _GetMaxAgeTimeDelta(self):
    return datetime.timedelta(days=self._GetMaxLogDays())

  def _GetFileDatetime(self, path):
    return datetime.datetime.strptime(os.path.basename(path),
                                      DAY_DIR_FORMAT)

  def AddLogsDir(self, logs_dir):
    """Adds a new logging directory and configures file logging.

    Args:
      logs_dir: str, Path to a directory to store log files under.  This method
        has no effect if this is None, or if this directory has already been
        registered.
    """
    if not logs_dir or logs_dir in self._logs_dirs:
      return

    self._logs_dirs.append(logs_dir)
    # If logs cleanup has been enabled, try to delete old log files
    # in the given directory. Continue normally if we try to delete log files
    # that do not exist. This can happen when two gcloud instances are cleaning
    # up logs in parallel.
    self._CleanUpLogs(logs_dir)

    # If the user has disabled file logging, return early here to avoid setting
    # up the file handler. Note that this should happen after cleaning up the
    # logs directory so that log retention settings are still respected.
    if properties.VALUES.core.disable_file_logging.GetBool():
      return

    # A handler to write DEBUG and above to log files in the given directory
    try:
      log_file = self._SetupLogsDir(logs_dir)
      file_handler = logging.FileHandler(
          log_file, encoding=LOG_FILE_ENCODING)
    except (OSError, IOError, files.Error) as exp:
      warning('Could not setup log file in {0}, ({1}: {2}.\n'
              'The configuration directory may not be writable. '
              'To learn more, see '
              'https://cloud.google.com/sdk/docs/configurations#'
              'creating_a_configuration'.format(
                  logs_dir, type(exp).__name__, exp))
      return

    self.current_log_file = log_file
    file_handler.setLevel(logging.NOTSET)
    file_handler.setFormatter(self._file_formatter)
    self._root_logger.addHandler(file_handler)
    self.file_only_logger.addHandler(file_handler)

  def _CleanUpLogs(self, logs_dir):
    """Clean up old log files if log cleanup has been enabled."""
    if self._GetMaxLogDays():
      try:
        self._CleanLogsDir(logs_dir)
      except OSError:
        pass

  def _CleanLogsDir(self, logs_dir):
    """Cleans up old log files form the given logs directory.

    Args:
      logs_dir: str, The path to the logs directory.
    """
    now = datetime.datetime.now()
    now_seconds = time.time()

    try:
      dirnames = os.listdir(logs_dir)
    except (OSError, UnicodeError):
      # In event of a non-existing or non-readable directory, we don't want to
      # cause an error
      return
    for dirname in dirnames:
      dir_path = os.path.join(logs_dir, dirname)
      if self._ShouldDeleteDir(now, dir_path):
        for filename in os.listdir(dir_path):
          log_file_path = os.path.join(dir_path, filename)
          if self._ShouldDeleteFile(now_seconds, log_file_path):
            os.remove(log_file_path)
        try:
          os.rmdir(dir_path)
        except OSError:
          # If the directory isn't empty, or isn't removable for some other
          # reason. This is okay.
          pass

  def _ShouldDeleteDir(self, now, path):
    """Determines if the directory should be deleted.

    True iff:
    * path is a directory
    * path name is formatted according to DAY_DIR_FORMAT
    * age of path (according to DAY_DIR_FORMAT) is slightly older than the
      MAX_AGE of a log file

    Args:
      now: datetime.datetime object indicating the current date/time.
      path: the full path to the directory in question.

    Returns:
      bool, whether the path is a valid directory that should be deleted
    """
    if not os.path.isdir(path):
      return False
    try:
      dir_date = self._GetFileDatetime(path)
    except ValueError:
      # Not in a format we're expecting; we probably shouldn't mess with it
      return False
    dir_age = now - dir_date
    # Add an additional day to this. It's better to delete a whole directory at
    # once and leave some extra files on disk than to loop through on each run
    # (some customers have pathologically large numbers of log files).
    return dir_age > self._GetMaxAgeTimeDelta() + datetime.timedelta(1)

  def _ShouldDeleteFile(self, now_seconds, path):
    """Determines if the file is old enough to be deleted.

    If the file is not a file that we recognize, return False.

    Args:
      now_seconds: int, The current time in seconds.
      path: str, The file or directory path to check.

    Returns:
      bool, True if it should be deleted, False otherwise.
    """
    if os.path.splitext(path)[1] not in _KNOWN_LOG_FILE_EXTENSIONS:
      # If we don't recognize this file, don't delete it
      return False
    stat_info = os.stat(path)
    return now_seconds - stat_info.st_mtime > self._GetMaxAge()

  def _SetupLogsDir(self, logs_dir):
    """Creates the necessary log directories and get the file name to log to.

    Logs are created under the given directory.  There is a sub-directory for
    each day, and logs for individual invocations are created under that.

    Deletes files in this directory that are older than MAX_AGE.

    Args:
      logs_dir: str, Path to a directory to store log files under

    Returns:
      str, The path to the file to log to
    """
    now = datetime.datetime.now()
    day_dir_name = now.strftime(DAY_DIR_FORMAT)
    day_dir_path = os.path.join(logs_dir, day_dir_name)
    files.MakeDir(day_dir_path)

    filename = '{timestamp}{ext}'.format(
        timestamp=now.strftime(FILENAME_FORMAT), ext=LOG_FILE_EXTENSION)
    log_file = os.path.join(day_dir_path, filename)
    return log_file


_log_manager = _LogManager()

# The configured stdout writer.  This writer is a stripped down file-like
# object that provides the basic writing methods.  When you write to this
# stream, it will be written to stdout only if user output is enabled.  All
# strings will also be logged at INFO level to any registered log files.
out = _log_manager.stdout_writer


# The configured stderr writer.  This writer is a stripped down file-like
# object that provides the basic writing methods.  When you write to this
# stream, it will be written to stderr only if user output is enabled.  All
# strings will also be logged at INFO level to any registered log files.
err = _log_manager.stderr_writer

# Status output writer. For things that are useful to know for someone watching
# a command run, but aren't normally scraped.
status = err


# Gets a logger object that logs only to a file and never to the console.
# You usually don't want to use this logger directly.  All normal logging will
# also go to files.  This logger specifically prevents the messages from going
# to the console under any verbosity setting.
file_only_logger = _log_manager.file_only_logger


def Print(*msg):
  """Writes the given message to the output stream, and adds a newline.

  This method has the same output behavior as the builtin print method but
  respects the configured user output setting.

  Args:
    *msg: str, The messages to print.
  """
  out.Print(*msg)


def WriteToFileOrStdout(path, content, overwrite=True, binary=False,
                        private=False, create_path=False):
  """Writes content to the specified file or stdout if path is '-'.

  Args:
    path: str, The path of the file to write.
    content: str, The content to write to the file.
    overwrite: bool, Whether or not to overwrite the file if it exists.
    binary: bool, True to open the file in binary mode.
    private: bool, Whether to write the file in private mode.
    create_path: bool, True to create intermediate directories, if needed.

  Raises:
    Error: If the file cannot be written.
  """
  if path == '-':
    if binary:
      files.WriteStreamBytes(sys.stdout, content)
    else:
      out.write(content)
  elif binary:
    files.WriteBinaryFileContents(path, content, overwrite=overwrite,
                                  private=private, create_path=create_path)
  else:
    files.WriteFileContents(
        path,
        content,
        overwrite=overwrite,
        private=private,
        create_path=create_path)


def Reset(stdout=None, stderr=None):
  """Reinitialize the logging system.

  This clears all loggers registered in the logging module, and reinitializes
  it with the specific loggers we want for calliope.

  This will set the initial values for verbosity or user_output_enabled to their
  values saved in the properties.

  Since we are using the python logging module, and that is all statically
  initialized, this method does not actually turn off all the loggers.  If you
  hold references to loggers or writers after calling this method, it is
  possible they will continue to work, but their behavior might change when the
  logging framework is reinitialized.  This is useful mainly for clearing the
  loggers between tests so stubs can get reset.

  Args:
    stdout: the file-like object to restore to stdout. If not given, sys.stdout
      is used
    stderr: the file-like object to restore to stderr. If not given, sys.stderr
      is used
  """
  _log_manager.Reset(stdout or sys.stdout, stderr or sys.stderr)


def SetVerbosity(verbosity):
  """Sets the active verbosity for the logger.

  Args:
    verbosity: int, A verbosity constant from the logging module that
      determines what level of logs will show in the console. If None, the
      value from properties or the default will be used.

  Returns:
    int, The current verbosity.
  """
  return _log_manager.SetVerbosity(verbosity)


def GetVerbosity():
  """Gets the current verbosity setting.

  Returns:
    int, The current verbosity.
  """
  return _log_manager.verbosity


def GetVerbosityName(verbosity=None):
  """Gets the name for the current verbosity setting or verbosity if not None.

  Args:
    verbosity: int, Returns the name for this verbosity if not None.

  Returns:
    str, The verbosity name or None if the verbosity is unknown.
  """
  if verbosity is None:
    verbosity = GetVerbosity()
  for name, num in six.iteritems(VALID_VERBOSITY_STRINGS):
    if verbosity == num:
      return name
  return None


def OrderedVerbosityNames():
  """Gets all the valid verbosity names from most verbose to least verbose."""
  return [name for name, _ in _VERBOSITY_LEVELS]


def _GetEffectiveVerbosity(verbosity):
  """Returns the effective verbosity for verbosity. Handles None => NOTSET."""
  return verbosity or logging.NOTSET


def SetLogFileVerbosity(verbosity):
  """Sets the log file verbosity.

  Args:
    verbosity: int, A verbosity constant from the logging module that
      determines what level of logs will be written to the log file. If None,
      the default will be used.

  Returns:
    int, The current verbosity.
  """
  return _GetEffectiveVerbosity(
      _log_manager.file_only_logger.setLevel(verbosity))


def GetLogFileVerbosity():
  """Gets the current log file verbosity setting.

  Returns:
    int, The log file current verbosity.
  """
  return _GetEffectiveVerbosity(
      _log_manager.file_only_logger.getEffectiveLevel())


class LogFileVerbosity(object):
  """A log file verbosity context manager.

  Attributes:
    _context_verbosity: int, The log file verbosity during the context.
    _original_verbosity: int, The original log file verbosity before the
      context was entered.

  Returns:
    The original verbosity is returned in the "as" clause.
  """

  def __init__(self, verbosity):
    self._context_verbosity = verbosity

  def __enter__(self):
    self._original_verbosity = SetLogFileVerbosity(self._context_verbosity)
    return self._original_verbosity

  def __exit__(self, exc_type, exc_value, traceback):
    SetLogFileVerbosity(self._original_verbosity)
    return False


def SetUserOutputEnabled(enabled):
  """Sets whether user output should go to the console.

  Args:
    enabled: bool, True to enable output, false to suppress.

  Returns:
    bool, The old value of enabled.
  """
  return _log_manager.SetUserOutputEnabled(enabled)


def IsUserOutputEnabled():
  """Gets whether user output is enabled or not.

  Returns:
    bool, True if user output is enabled, False otherwise.
  """
  return _log_manager.user_output_enabled


def AddFileLogging(logs_dir):
  """Adds a new logging file handler to the root logger.

  Args:
    logs_dir: str, The root directory to store logs in.
  """
  _log_manager.AddLogsDir(logs_dir=logs_dir)


def GetLogDir():
  """Gets the path to the currently in use log directory.

  Returns:
    str, The logging directory path.
  """
  log_file = _log_manager.current_log_file
  if not log_file:
    return None
  return os.path.dirname(log_file)


def GetLogFileName(suffix):
  """Returns a new log file name based on the currently active log file.

  Args:
    suffix: str, A suffix to add to the current log file name.

  Returns:
    str, The name of a log file, or None if file logging is not on.
  """
  log_file = _log_manager.current_log_file
  if not log_file:
    return None
  log_filename = os.path.basename(log_file)
  log_file_root_name = log_filename[:-len(LOG_FILE_EXTENSION)]
  return log_file_root_name + suffix


def GetLogFilePath():
  """Return the path to the currently active log file.

  Returns:
    str, The name of a log file, or None if file logging is not on.
  """
  return _log_manager.current_log_file


def _PrintResourceChange(operation,
                         resource,
                         kind,
                         is_async,
                         details,
                         failed,
                         operation_past_tense=None):
  """Prints a status message for operation on resource.

  The non-failure status messages are disabled when user output is disabled.

  Args:
    operation: str, The completed operation name.
    resource: str, The resource name.
    kind: str, The resource kind (instance, cluster, project, etc.).
    is_async: bool, True if the operation is in progress.
    details: str, Extra details appended to the message. Keep it succinct.
    failed: str, Failure message. For commands that operate on multiple
      resources and report all successes and failures before exiting. Failure
      messages use log.error. This will display the message on the standard
      error even when user output is disabled.
    operation_past_tense: str, The past tense version of the operation verb.
      If None assumes operation + 'd'
  """
  msg = []
  if failed:
    msg.append('Failed to ')
    msg.append(operation)
  elif is_async:
    msg.append(operation.capitalize())
    msg.append(' in progress for')
  else:
    verb = operation_past_tense or '{0}d'.format(operation)
    msg.append('{0}'.format(verb.capitalize()))

  if kind:
    msg.append(' ')
    msg.append(kind)
  if resource:
    msg.append(' ')
    msg.append(text.TextTypes.RESOURCE_NAME(six.text_type(resource)))
  if details:
    msg.append(' ')
    msg.append(details)

  if failed:
    msg.append(': ')
    msg.append(failed)
  period = '' if str(msg[-1]).endswith('.') else '.'
  msg.append(period)
  msg = text.TypedText(msg)
  writer = error if failed else status.Print
  writer(msg)


def CreatedResource(resource, kind=None, is_async=False, details=None,
                    failed=None):
  """Prints a status message indicating that a resource was created.

  Args:
    resource: str, The resource name.
    kind: str, The resource kind (instance, cluster, project, etc.).
    is_async: bool, True if the operation is in progress.
    details: str, Extra details appended to the message. Keep it succinct.
    failed: str, Failure message.
  """
  _PrintResourceChange('create', resource, kind, is_async, details, failed)


def DeletedResource(resource, kind=None, is_async=False, details=None,
                    failed=None):
  """Prints a status message indicating that a resource was deleted.

  Args:
    resource: str, The resource name.
    kind: str, The resource kind (instance, cluster, project, etc.).
    is_async: bool, True if the operation is in progress.
    details: str, Extra details appended to the message. Keep it succinct.
    failed: str, Failure message.
  """
  _PrintResourceChange('delete', resource, kind, is_async, details, failed)


def DetachedResource(resource,
                     kind=None,
                     is_async=False,
                     details=None,
                     failed=None):
  """Prints a status message indicating that a resource was detached.

  Args:
    resource: str, The resource name.
    kind: str, The resource kind (instance, cluster, project, etc.).
    is_async: bool, True if the operation is in progress.
    details: str, Extra details appended to the message. Keep it succinct.
    failed: str, Failure message.
  """
  _PrintResourceChange(
      'detach',
      resource,
      kind,
      is_async,
      details,
      failed,
      operation_past_tense='detached')


def RestoredResource(resource, kind=None, is_async=False, details=None,
                     failed=None):
  """Prints a status message indicating that a resource was restored.

  Args:
    resource: str, The resource name.
    kind: str, The resource kind (instance, cluster, project, etc.).
    is_async: bool, True if the operation is in progress.
    details: str, Extra details appended to the message. Keep it succinct.
    failed: str, Failure message.
  """
  _PrintResourceChange('restore', resource, kind, is_async, details, failed)


def UpdatedResource(resource, kind=None, is_async=False, details=None,
                    failed=None):
  """Prints a status message indicating that a resource was updated.

  Args:
    resource: str, The resource name.
    kind: str, The resource kind (instance, cluster, project, etc.).
    is_async: bool, True if the operation is in progress.
    details: str, Extra details appended to the message. Keep it succinct.
    failed: str, Failure message.
  """
  _PrintResourceChange('update', resource, kind, is_async, details, failed)


def ResetResource(resource, kind=None, is_async=False, details=None,
                  failed=None):
  """Prints a status message indicating that a resource was reset.

  Args:
    resource: str, The resource name.
    kind: str, The resource kind (instance, cluster, project, etc.).
    is_async: bool, True if the operation is in progress.
    details: str, Extra details appended to the message. Keep it succinct.
    failed: str, Failure message.
  """
  _PrintResourceChange('reset', resource, kind, is_async, details, failed,
                       operation_past_tense='reset')


def ImportResource(resource,
                   kind=None,
                   is_async=False,
                   details=None,
                   failed=None):
  """Prints a status message indicating that a resource was imported.

  Args:
    resource: str, The resource name.
    kind: str, The resource kind (instance, cluster, project, etc.).
    is_async: bool, True if the operation is in progress.
    details: str, Extra details appended to the message. Keep it succinct.
    failed: str, Failure message.
  """
  _PrintResourceChange(
      'import',
      resource,
      kind,
      is_async,
      details,
      failed,
      operation_past_tense='imported')


def ExportResource(resource,
                   kind=None,
                   is_async=False,
                   details=None,
                   failed=None):
  """Prints a status message indicating that a resource was exported.

  Args:
    resource: str, The resource name.
    kind: str, The resource kind (instance, cluster, project, etc.).
    is_async: bool, True if the operation is in progress.
    details: str, Extra details appended to the message. Keep it succinct.
    failed: str, Failure message.
  """
  _PrintResourceChange(
      'export',
      resource,
      kind,
      is_async,
      details,
      failed,
      operation_past_tense='exported')


# pylint: disable=invalid-name
# There are simple redirects to the logging module as a convenience.
getLogger = logging.getLogger
log = logging.log
debug = logging.debug
info = logging.info
warning = logging.warning
error = logging.error
critical = logging.critical
fatal = logging.fatal
exception = logging.exception
