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

"""Error Reporting Handler."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
import sys
import traceback

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.error_reporting import util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import command_loading
from googlecloudsdk.command_lib import error_reporting_util
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.util import platforms


def _IsInstallationCorruption(err):
  """Determines if the error may be from installation corruption.

  Args:
    err: Exception err.

  Returns:
    bool, True if installation error, False otherwise
  """
  return (isinstance(err, command_loading.CommandLoadFailure) and
          isinstance(err.root_exception, ImportError))


def _PrintInstallationAction(err, err_string):
  """Prompts installation error action.

  Args:
    err: Exception err.
    err_string: Exception err string.
  """
  # This usually indicates installation corruption.
  # We do want to suggest `gcloud components reinstall` here (ex. as opposed
  # to the similar message in gcloud.py), because there's a good chance it'll
  # work (rather than a manual reinstall).
  # Don't suggest `gcloud feedback`, because this is probably an
  # installation problem.
  log.error(
      (
          'gcloud failed to load ({command}): {err_str}\n\nThis usually'
          ' indicates corruption in your gcloud installation or problems with'
          ' your Python interpreter.\n\nPlease verify that the following is the'
          ' path to a working Python {py_major_version}.{py_minor_version}+'
          ' executable:\n    {executable}\nIf it is not, please set the'
          ' CLOUDSDK_PYTHON environment variable to point to a working Python'
          ' {py_major_version}.{py_minor_version}+ executable.\n\nIf you are'
          ' still experiencing problems, please run the following command to'
          ' reinstall:\n    $ gcloud components reinstall\n\nIf that command'
          ' fails, please reinstall the Google Cloud CLI using the instructions'
          ' here:\n    https://cloud.google.com/sdk/'
      ).format(
          command=err.command,
          err_str=err_string,
          executable=sys.executable,
          py_major_version=platforms.PythonVersion.MIN_SUPPORTED_PY3_VERSION[0],
          py_minor_version=platforms.PythonVersion.MIN_SUPPORTED_PY3_VERSION[1],
      )
  )


ERROR_PROJECT = 'cloud-sdk-user-errors'
ERROR_REPORTING_PARAM = 'AIzaSyCUuWyME_r4XylltWNeydEjKSkgXkvpVyU'
SERVICE = 'gcloud'
CRASH_PROJECT = 'cloud-sdk-crashes'
CRASH_REPORTING_PARAM = 'AIzaSyAp4DSI_Z3-mK-B8U0t7GE34n74OWDJmak'


def _GetReportingClient(is_crash=True):
  """Returns a client that uses an API key for Cloud SDK crash reports.

  Args:
     is_crash: bool, True use CRASH_REPORTING_PARAM, if False use
     ERROR_REPORTING_PARAM.

  Returns:
    An error reporting client that uses an API key for Cloud SDK crash reports.
  """
  client_class = core_apis.GetClientClass(util.API_NAME, util.API_VERSION)
  client_instance = client_class(get_credentials=False)
  if is_crash:
    client_instance.AddGlobalParam('key', CRASH_REPORTING_PARAM)
  else:
    client_instance.AddGlobalParam('key', ERROR_REPORTING_PARAM)
  return client_instance


def ReportError(is_crash):
  """Report the anonymous crash information to the Error Reporting service.

  This will report the actively handled exception.
  Args:
    is_crash: bool, True if this is a crash, False if it is a user error.
  """

  if (not properties.IsDefaultUniverse() or
      properties.VALUES.core.disable_usage_reporting.GetBool()):
    return

  # traceback prints the exception that is currently being handled
  stacktrace = traceback.format_exc()
  stacktrace = error_reporting_util.RemovePrivateInformationFromTraceback(
      stacktrace)
  command = properties.VALUES.metrics.command_name.Get()
  cid = metrics.GetCIDIfMetricsEnabled()

  client = _GetReportingClient(is_crash)
  reporter = util.ErrorReporting(client)
  try:
    method_config = client.projects_events.GetMethodConfig('Report')
    request = reporter.GenerateReportRequest(
        error_message=stacktrace,
        service=SERVICE,
        version=config.CLOUD_SDK_VERSION,
        project=CRASH_PROJECT if is_crash else ERROR_PROJECT,
        request_url=command, user=cid)
    http_request = client.projects_events.PrepareHttpRequest(
        method_config, request)
    metrics.CustomBeacon(http_request.url, http_request.http_method,
                         http_request.body, http_request.headers)

  except apitools_exceptions.Error as e:
    log.file_only_logger.error(
        'Unable to report crash stacktrace:\n{0}'.format(
            console_attr.SafeText(e)))


def HandleGcloudCrash(err):
  """Checks if installation error occurred, then proceeds with Error Reporting.

  Args:
    err: Exception err.
  """
  err_string = console_attr.SafeText(err)
  log.file_only_logger.exception('BEGIN CRASH STACKTRACE')
  if _IsInstallationCorruption(err):
    _PrintInstallationAction(err, err_string)
  else:
    log.error('gcloud crashed ({0}): {1}'.format(
        getattr(err, 'error_name', type(err).__name__), err_string))
    if 'certificate verify failed' in err_string:
      log.err.Print(
          '\ngcloud\'s default CA certificates failed to verify your connection'
          ', which can happen if you are behind a proxy or firewall.')
      log.err.Print('To use a custom CA certificates file, please run the '
                    'following command:')
      log.err.Print(
          '  gcloud config set core/custom_ca_certs_file /path/to/ca_certs')
    ReportError(is_crash=True)
    log.err.Print('\nIf you would like to report this issue, please run the '
                  'following command:')
    log.err.Print('  gcloud feedback')
    log.err.Print('\nTo check gcloud for common problems, please run the '
                  'following command:')
    log.err.Print('  gcloud info --run-diagnostics')


def CrashManager(target_function):
  """Context manager for handling gcloud crashes.

  Good for wrapping multiprocessing and multithreading target functions.

  Args:
    target_function (function): Unit test to decorate.

  Returns:
    Decorator function.
  """

  @functools.wraps(target_function)
  def Wrapper(*args, **kwargs):
    try:
      target_function(*args, **kwargs)
      # pylint:disable=broad-except
    except Exception as e:
      # pylint:enable=broad-except
      HandleGcloudCrash(e)
      if properties.VALUES.core.print_unhandled_tracebacks.GetBool():
        # We want to see the traceback as normally handled by Python
        raise
      else:
        # This is the case for most non-Cloud SDK developers. They shouldn't see
        # the full stack trace, but just the nice "gcloud crashed" message.
        sys.exit(1)

  return Wrapper
