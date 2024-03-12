# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command to assist user in submitting feedback about gcloud.

Does one of two things:

1. If invoked in the context of a recent gcloud crash (i.e. an exception that
was not caught anywhere in the Cloud SDK), will direct the user to the Cloud SDK
bug tracker, with a partly pre-filled form.

2. Otherwise, directs the user to either the Cloud SDK bug tracker,
StackOverflow, or the Cloud SDK groups page.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib import feedback_util
from googlecloudsdk.command_lib import info_holder
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import text as text_util

import six
from six.moves import map


STACKOVERFLOW_URL = 'http://stackoverflow.com/questions/tagged/gcloud'
GROUPS_PAGE_URL = ('https://groups.google.com/forum/?fromgroups#!forum/'
                   'google-cloud-dev')


FEEDBACK_MESSAGE = """\

We appreciate your feedback.

If you have a question, post it on Stack Overflow using the "gcloud" tag at
[{0}].

For general feedback, use our groups page
[{1}],
send a mail to [google-cloud-dev@googlegroups.com] or visit the [#gcloud] IRC
channel on freenode.
""".format(STACKOVERFLOW_URL, GROUPS_PAGE_URL)


FEEDBACK_PROMPT = """\
Would you like to file a bug using our issue tracker site at [{0}] \
(will open a new browser tab)?\
""".format(feedback_util.ISSUE_TRACKER_URL)


def _PrintQuiet(info_str, log_data):
  """Print message referring to various feedback resources for quiet execution.

  Args:
    info_str: str, the output of `gcloud info`
    log_data: info_holder.LogData, log data for the provided log file
  """
  if log_data:
    if not log_data.traceback:
      log.Print(('Please consider including the log file [{0}] in any '
                 'feedback you submit.').format(log_data.filename))

  log.Print(textwrap.dedent("""\

      If you have a question, post it on Stack Overflow using the "gcloud" tag
      at [{0}].

      For general feedback, use our groups page
      [{1}],
      send a mail to [google-cloud-dev@googlegroups.com], or visit the [#gcloud]
      IRC channel on freenode.

      If you have found a bug, file it using our issue tracker site at
      [{2}].

      Please include the following information when filing a bug report:\
      """).format(STACKOVERFLOW_URL, GROUPS_PAGE_URL,
                  feedback_util.ISSUE_TRACKER_URL))
  divider = feedback_util.GetDivider()
  log.Print(divider)
  if log_data and log_data.traceback:
    log.Print(log_data.traceback)
  log.Print(info_str.strip())
  log.Print(divider)


def _SuggestIncludeRecentLogs():
  recent_runs = info_holder.LogsInfo().GetRecentRuns()
  if recent_runs:
    now = datetime.datetime.now()
    def _FormatLogData(run):
      crash = ' (crash detected)' if run.traceback else ''
      time = 'Unknown time'
      if run.date:
        time = text_util.PrettyTimeDelta(now - run.date) + ' ago'
      return '[{0}]{1}: {2}'.format(run.command, crash, time)
    idx = console_io.PromptChoice(
        list(map(_FormatLogData, recent_runs)) + ['None of these'], default=0,
        message=('Which recent gcloud invocation would you like to provide '
                 'feedback about? This will open a new browser tab.'))
    if idx < len(recent_runs):
      return recent_runs[idx]


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Feedback(base.Command):
  """Provide feedback to the Google Cloud CLI team.

  The Google Cloud CLI team offers support through a number of channels:

  * Google Cloud CLI Issue Tracker
  * Stack Overflow "#gcloud" tag
  * google-cloud-dev Google group

  This command lists the available channels and facilitates getting help through
  one of them by opening a web browser to the relevant page, possibly with
  information relevant to the current install and configuration pre-populated in
  form fields on that page.
  """

  detailed_help = {
      'EXAMPLES': """
          To send feedback, including the log file for the most recent command,
          run:

            $ {command}

          To send feedback with a previously generated log file named
          'my-logfile', run:

            $ {command} --log-file=my-logfile
          """,
  }

  category = base.SDK_TOOLS_CATEGORY

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--log-file',
        help='Path to the log file from a prior gcloud run.')

  def Run(self, args):
    info = info_holder.InfoHolder(anonymizer=info_holder.Anonymizer())
    log_data = None
    if args.log_file:
      try:
        log_data = info_holder.LogData.FromFile(args.log_file)
      except files.Error as err:
        log.warning('Error reading the specified file [{0}]: '
                    '{1}\n'.format(args.log_file, err))
    if args.quiet:
      _PrintQuiet(six.text_type(info), log_data)
    else:
      log.status.Print(FEEDBACK_MESSAGE)
      if not log_data:
        log_data = _SuggestIncludeRecentLogs()
      if log_data or console_io.PromptContinue(
          prompt_string=('No invocation selected. Would you still like to file '
                         'a bug (will open a new browser tab)')):
        feedback_util.OpenNewIssueInBrowser(info, log_data)
