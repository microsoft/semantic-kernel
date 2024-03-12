# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Utilities for the `gcloud feedback` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re
import sys

from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_attr_os
import six

from six.moves import range
from six.moves import urllib

ISSUE_TRACKER_BASE_URL = 'https://issuetracker.google.com/'
NEW_ISSUE_URL = 'https://issuetracker.google.com/issues/new'
ISSUE_TRACKER_URL = 'https://issuetracker.google.com/issues?q=componentid:187143%2B'
ISSUE_TRACKER_COMPONENT = 187143

# The new issue URL has a maximum length, so we need to limit the length of
# pre-filled form fields
MAX_URL_LENGTH = 8208


COMMENT_PRE_STACKTRACE_TEMPLATE = """\
WARNING: This is a PUBLIC issue tracker, and as such, anybody can read the
information in the report you file. In order to help diagnose the issue,
we've included some installation information in this report. Please look
through and redact any information you consider personal or sensitive
before submitting this issue.

{formatted_command}What steps will reproduce the problem?


What is the expected output? What do you see instead?


Please provide any additional information below.


"""

COMMENT_TEMPLATE = COMMENT_PRE_STACKTRACE_TEMPLATE + """\
{formatted_traceback}


Installation information:

{gcloud_info}\
"""

TRUNCATED_INFO_MESSAGE = '[output truncated]'

STACKTRACE_LINES_PER_ENTRY = 2

# Pattern for splitting the traceback into stacktrace and exception.
PARTITION_TRACEBACK_PATTERN = (
    r'(?P<stacktrace>'
    r'Traceback \(most recent call last\):\n'
    r'(?: {2}File ".*", line \d+, in .+\n {4}.+\n)+'
    r')'
    r'(?P<exception>\S.+)')

TRACEBACK_ENTRY_REGEXP = (
    r'File "(?P<file>.*)", line (?P<line>\d+), in (?P<function>.+)\n'
    r'(?P<code_snippet>.+)\n')

MAX_CODE_SNIPPET_LENGTH = 80


class CommentHolder(object):

  def __init__(self, body, pre_stacktrace, stacktrace, exception):
    self.body = body
    self.pre_stacktrace = pre_stacktrace
    self.stacktrace = stacktrace
    self.exception = exception


def _FormatNewIssueUrl(comment):
  params = {
      'description': comment,
      'component': six.text_type(ISSUE_TRACKER_COMPONENT)
  }
  return NEW_ISSUE_URL + '?' + urllib.parse.urlencode(params)


def OpenInBrowser(url):
  # pylint: disable=g-import-not-at-top
  # Import in here for performance reasons
  import webbrowser
  # pylint: enable=g-import-not-at-top
  webbrowser.open_new_tab(url)


def _UrlEncodeLen(string):
  """Return the length of string when URL-encoded."""
  # urlencode turns a dict into a string of 'key=value' pairs. We use a blank
  # key and don't want to count the '='.
  encoded = urllib.parse.urlencode({'': string})[1:]
  return len(encoded)


def _FormatStackTrace(first_entry, rest):
  return '\n'.join([first_entry, '  [...]'] + rest) + '\n'


def _ShortenStacktrace(stacktrace, url_encoded_length):
  # pylint: disable=g-docstring-has-escape
  """Cut out the middle entries of the stack trace to a given length.

  For instance:

  >>> stacktrace = '''
  ...   File "foo.py", line 10, in run
  ...     result = bar.run()
  ...   File "bar.py", line 11, in run
  ...     result = baz.run()
  ...   File "baz.py", line 12, in run
  ...     result = qux.run()
  ...   File "qux.py", line 13, in run
  ...     raise Exception(':(')
  ... '''
  >>> _ShortenStacktrace(stacktrace, 300) == '''\
  ...   File "foo.py", line 10, in run
  ...     result = bar.run()
  ...   [...]
  ...   File "baz.py", line 12, in run
  ...      result = qux.run()
  ...   File "qux.py", line 13, in run
  ...      raise Exception(':(')
  ... '''
  True


  Args:
    stacktrace: str, the stacktrace (might be formatted by _FormatTraceback)
        without the leading 'Traceback (most recent call last):' or 'Trace:'
    url_encoded_length: int, the length to shorten the stacktrace to (when
        URL-encoded).

  Returns:
    str, the shortened stacktrace.
  """
  # A stacktrace consists of several entries, each of which is a pair of lines.
  # The first describes the file containing the line of source in the stack
  # trace; the second shows the line of source in the stack trace as it appears
  # in the source.
  stacktrace = stacktrace.strip('\n')
  lines = stacktrace.split('\n')
  entries = ['\n'.join(lines[i:i+STACKTRACE_LINES_PER_ENTRY]) for i in
             range(0, len(lines), STACKTRACE_LINES_PER_ENTRY)]

  if _UrlEncodeLen(stacktrace) <= url_encoded_length:
    return stacktrace + '\n'

  rest = entries[1:]
  while (_UrlEncodeLen(_FormatStackTrace(entries[0], rest)) >
         url_encoded_length) and len(rest) > 1:
    rest = rest[1:]
  # If we've eliminated the entire middle of the stacktrace and it's still
  # longer than the max allowed length, nothing we can do beyond that. We'll
  # return the short-as-possible stacktrace and let the caller deal with it.
  return _FormatStackTrace(entries[0], rest)


def _ShortenIssueBody(comment, url_encoded_length):
  """Shortens the comment to be at most the given length (URL-encoded).

  Does one of two things:

  (1) If the whole stacktrace and everything before it fits within the
      URL-encoded max length, truncates the remainder of the comment (which
      should include e.g. the output of `gcloud info`.
  (2) Otherwise, chop out the middle of the stacktrace until it fits. (See
      _ShortenStacktrace docstring for an example).
  (3) If the stacktrace cannot be shortened to fit in (2), then revert to (1).
      That is, truncate the comment.

  Args:
    comment: CommentHolder, an object containing the formatted comment for
        inclusion before shortening, and its constituent components
    url_encoded_length: the max length of the comment after shortening (when
        comment is URL-encoded).

  Returns:
    (str, str): the shortened comment and a message containing the parts of the
    comment that were omitted by the shortening process.
  """
  # * critical_info contains all of the critical information: the name of the
  # command, the stacktrace, and places for the user to provide additional
  # information.
  # * optional_info is the less essential `gcloud info output`.
  critical_info, middle, optional_info = comment.body.partition(
      'Installation information:\n')
  optional_info = middle + optional_info
  # We need to count the message about truncating the output towards our total
  # character count.
  max_str_len = (url_encoded_length -
                 _UrlEncodeLen(TRUNCATED_INFO_MESSAGE + '\n'))
  truncated_issue_body, remaining = _UrlTruncateLines(comment.body, max_str_len)

  # Case (1) from the docstring
  if _UrlEncodeLen(critical_info) <= max_str_len:
    return truncated_issue_body, remaining
  else:
    # Attempt to shorten stacktrace by cutting out middle
    non_stacktrace_encoded_len = _UrlEncodeLen(
        comment.pre_stacktrace + 'Trace:\n' + comment.exception + '\n' +
        TRUNCATED_INFO_MESSAGE)
    max_stacktrace_len = url_encoded_length - non_stacktrace_encoded_len
    shortened_stacktrace = _ShortenStacktrace(comment.stacktrace,
                                              max_stacktrace_len)
    critical_info_with_shortened_stacktrace = (
        comment.pre_stacktrace + 'Trace:\n' + shortened_stacktrace +
        comment.exception + '\n' + TRUNCATED_INFO_MESSAGE)
    optional_info_with_full_stacktrace = ('Full stack trace (formatted):\n' +
                                          comment.stacktrace +
                                          comment.exception + '\n\n' +
                                          optional_info)

    # Case (2) from the docstring
    if _UrlEncodeLen(critical_info_with_shortened_stacktrace) <= max_str_len:
      return (critical_info_with_shortened_stacktrace,
              optional_info_with_full_stacktrace)
    # Case (3) from the docstring
    else:
      return truncated_issue_body, optional_info_with_full_stacktrace


def _UrlTruncateLines(string, url_encoded_length):
  """Truncates the given string to the given URL-encoded length.

  Always cuts at a newline.

  Args:
    string: str, the string to truncate
    url_encoded_length: str, the length to which to truncate

  Returns:
    tuple of (str, str), where the first str is the truncated version of the
    original string and the second str is the remainder.
  """
  lines = string.split('\n')
  included_lines = []
  excluded_lines = []
  # Adjust the max length for the truncation message in case it is needed
  max_str_len = (url_encoded_length -
                 _UrlEncodeLen(TRUNCATED_INFO_MESSAGE + '\n'))
  while (lines and
         _UrlEncodeLen('\n'.join(included_lines + lines[:1])) <= max_str_len):
    included_lines.append(lines.pop(0))
  excluded_lines = lines
  if excluded_lines:
    included_lines.append(TRUNCATED_INFO_MESSAGE)
  return '\n'.join(included_lines), '\n'.join(excluded_lines)


def GetDivider(text=''):
  """Return a console-width divider (ex: '======================' (etc.)).

  Supports messages (ex: '=== Messsage Here ===').

  Args:
    text: str, a message to display centered in the divider.

  Returns:
    str, the formatted divider
  """
  if text:
    text = ' ' + text + ' '
  width, _ = console_attr_os.GetTermSize()
  return text.center(width, '=')


def _FormatIssueBody(info, log_data=None):
  """Construct a useful issue body with which to pre-populate the issue tracker.

  Args:
    info: InfoHolder, holds information about the Cloud SDK install
    log_data: LogData, parsed log data for a gcloud run

  Returns:
    CommentHolder, a class containing the issue comment body, part of comment
        before stacktrace, the stacktrace portion of the comment, and the
        exception
  """
  gcloud_info = six.text_type(info)

  formatted_command = ''
  if log_data and log_data.command:
    formatted_command = 'Issue running command [{0}].\n\n'.format(
        log_data.command)

  pre_stacktrace = COMMENT_PRE_STACKTRACE_TEMPLATE.format(
      formatted_command=formatted_command)

  formatted_traceback = ''
  formatted_stacktrace = ''
  exception = ''
  if log_data and log_data.traceback:
    # Because we have a limited number of characters to work with (see
    # MAX_URL_LENGTH), we reduce the size of the traceback by stripping out the
    # unnecessary information, such as the runtime root and function names.
    formatted_stacktrace, exception = _FormatTraceback(log_data.traceback)
    formatted_traceback = 'Trace:\n' + formatted_stacktrace + exception

  comment_body = COMMENT_TEMPLATE.format(
      formatted_command=formatted_command, gcloud_info=gcloud_info.strip(),
      formatted_traceback=formatted_traceback)

  return CommentHolder(comment_body, pre_stacktrace, formatted_stacktrace,
                       exception)


def _StacktraceEntryReplacement(entry):
  """Used in re.sub to format a stacktrace entry to make it more compact.

  File "qux.py", line 13, in run      ===>      qux.py:13
    foo = math.sqrt(bar) / foo                   foo = math.sqrt(bar)...

  Args:
    entry: re.MatchObject, the original unformatted stacktrace entry

  Returns:
    str, the formatted stacktrace entry
  """

  filename = entry.group('file')
  line_no = entry.group('line')
  code_snippet = entry.group('code_snippet')
  formatted_code_snippet = code_snippet.strip()[:MAX_CODE_SNIPPET_LENGTH]
  if len(code_snippet) > MAX_CODE_SNIPPET_LENGTH:
    formatted_code_snippet += '...'
  formatted_entry = '{0}:{1}\n {2}\n'.format(filename, line_no,
                                             formatted_code_snippet)
  return formatted_entry


def _SysPath():
  """Return the Python paths (can be mocked for testing)."""
  return sys.path


def _StripLongestSysPath(path):
  python_paths = sorted(_SysPath(), key=len, reverse=True)
  for python_path in python_paths:
    prefix = python_path + os.path.sep
    if path.startswith(prefix):
      return path[len(prefix):]
  return path


def _StripCommonDir(path):
  prefix = 'googlecloudsdk' + os.path.sep
  return path[len(prefix):] if path.startswith(prefix) else path


def _StripPath(path):
  """Removes common elements (sys.path, common SDK directories) from path."""
  return _StripCommonDir(os.path.normpath(_StripLongestSysPath(path)))


def _FormatTraceback(traceback):
  """Compacts stack trace portion of traceback and extracts exception.

  Args:
    traceback: str, the original unformatted traceback

  Returns:
    tuple of (str, str) where the first str is the formatted stack trace and the
    second str is exception.
  """
  # Separate stacktrace and exception
  match = re.search(PARTITION_TRACEBACK_PATTERN, traceback)
  if not match:
    return traceback, ''

  stacktrace = match.group('stacktrace')
  exception = match.group('exception')

  # Strip trailing whitespace.
  formatted_stacktrace = '\n'.join(line.strip() for line in
                                   stacktrace.splitlines())
  formatted_stacktrace += '\n'

  stacktrace_files = re.findall(r'File "(.*)"', stacktrace)

  for path in stacktrace_files:
    formatted_stacktrace = formatted_stacktrace.replace(path, _StripPath(path))

  # Make each stack frame entry more compact
  formatted_stacktrace = re.sub(TRACEBACK_ENTRY_REGEXP,
                                _StacktraceEntryReplacement,
                                formatted_stacktrace)

  formatted_stacktrace = formatted_stacktrace.replace(
      'Traceback (most recent call last):\n', '')

  return formatted_stacktrace, exception


def OpenNewIssueInBrowser(info, log_data):
  """Opens a new tab in the web browser to the new issue page for Cloud SDK.

  The page will be pre-populated with relevant information.

  Args:
    info: InfoHolder, the data from of `gcloud info`
    log_data: LogData, parsed representation of a recent log
  """
  comment = _FormatIssueBody(info, log_data)
  url = _FormatNewIssueUrl(comment.body)
  if len(url) > MAX_URL_LENGTH:
    max_info_len = MAX_URL_LENGTH - len(_FormatNewIssueUrl(''))
    truncated, remaining = _ShortenIssueBody(comment, max_info_len)
    log.warning('Truncating included information. '
                'Please consider including the remainder:')
    divider_text = 'TRUNCATED INFORMATION (PLEASE CONSIDER INCLUDING)'
    log.status.Print(GetDivider(divider_text))
    log.status.Print(remaining.strip())
    log.status.Print(GetDivider('END ' + divider_text))
    log.warning('The output of gcloud info is too long to pre-populate the '
                'new issue form.')
    log.warning('Please consider including the remainder (above).')
    url = _FormatNewIssueUrl(truncated)
  OpenInBrowser(url)
  log.status.Print('Opening your browser to a new Google Cloud SDK issue.')
  log.status.Print(
      'If your browser does not open or you have issues loading the web page, '
      'please ensure you are signed into your account on %s first, then try '
      'again.' % ISSUE_TRACKER_BASE_URL)
  log.status.Print(
      'If you still have issues loading the web page, please file an issue: %s'
      % ISSUE_TRACKER_URL)
