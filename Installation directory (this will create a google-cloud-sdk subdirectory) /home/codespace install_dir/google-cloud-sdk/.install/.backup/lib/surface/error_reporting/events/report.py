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

"""The gcloud error-reporting events report command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.error_reporting import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.error_reporting import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


class Report(base.Command):
  """Report an error.

  {command} is used to report errors using the error-reporting service.
  The required arguments are a service name and either an
  error-file containing details of an error or an inline error message.

  The error message must contain a header (typically consisting of the
  exception type name and an error message) and an exception stack trace in one
  of the supported programming languages and formats. Details about supported
  languages and formats can be found at
  https://cloud.google.com/error-reporting/docs/formatting-error-messages

  ## EXAMPLES

  To report an error, run:

    $ {command} --service=SERVICE_NAME --message="Error message"

  or:

    $ {command} --service=SERVICE_NAME --message-file=ERROR_MESSAGE.EXT
  """

  @staticmethod
  def Args(parser):
    """Get arguments for this command.

    Args:
      parser: argparse.ArgumentParser, the parser for this command.
    """
    parser.add_argument(
        '--service',
        required=True,
        help='The name of the service that generated the error')
    parser.add_argument(
        '--service-version',
        help='The release version of the service')

    # add mutually exclusive arguments
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--message',
        help='Inline details of the error')
    group.add_argument(
        '--message-file',
        help='File containing details of the error')

  def GetMessage(self, args):
    """Get error message.

    Args:
      args: the arguments for the command

    Returns:
      error_message read from error file or provided inline

    Raises:
      CannotOpenFileError: When there is a problem with reading the file
    """
    error_message = ''
    if args.message_file:
      try:
        error_message = files.ReadFileContents(args.message_file)
      except files.Error as e:
        raise exceptions.CannotOpenFileError(args.message_file, e)
    elif args.message:
      error_message = args.message
    return error_message

  def GetProject(self, args):
    """Get project name."""
    return properties.VALUES.core.project.Get(required=True)

  def Run(self, args):
    """Send an error report based on the given args."""

    # Get required message components for API report request
    error_message = self.GetMessage(args)
    service = args.service
    # Get service version if provided, otherwise service_version=None
    service_version = args.service_version
    project = self.GetProject(args)

    # Send error report
    error_event = util.ErrorReporting()
    error_event.ReportEvent(error_message, service, service_version, project)

    log.status.Print('Your error has been reported.')
