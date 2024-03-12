#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""Main module for Google Cloud Storage command line tool."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import datetime
import errno
import getopt
import logging
import os
import re
import signal
import socket
import sys
import textwrap
import traceback

import six
from six.moves import configparser
from six.moves import range

from google.auth import exceptions as google_auth_exceptions
import gslib.exception
from gslib.exception import CommandException
from gslib.exception import ControlCException

from gslib.utils.version_check import check_python_version_support
from gslib.utils.arg_helper import GetArgumentsAndOptions
from gslib.utils.user_agent_helper import GetUserAgent

# Load the gsutil version number and append it to boto.UserAgent so the value is
# set before anything instantiates boto. This has to run after THIRD_PARTY_DIR
# is modified (done in gsutil.py) but before any calls are made that would cause
# boto.s3.Connection to be loaded - otherwise the Connection class would end up
# with a static reference to the pre-modified version of the UserAgent field,
# so boto requests would not include gsutil/version# in the UserAgent string.
import boto
import gslib
from gslib.utils import system_util, text_util

# pylint: disable=g-import-not-at-top
# This module also imports boto, and will override the UserAgent global variable
# if imported above.
from gslib import metrics

# We parse the options and arguments here so we can pass the results to the user
# agent helper.
try:
  opts, args = GetArgumentsAndOptions()
except CommandException as e:
  reason = e.reason if e.informational else 'CommandException: %s' % e.reason
  err = '%s\n' % reason
  try:
    text_util.print_to_fd(err, end='', file=sys.stderr)
  except UnicodeDecodeError:
    # Can happen when outputting invalid Unicode filenames.
    sys.stderr.write(err)
  if e:
    metrics.LogFatalError(e)
  sys.exit(1)

# This calculated user agent can be stored for use in StorageV1.
gslib.USER_AGENT = GetUserAgent(args, metrics.MetricsCollector.IsDisabled())
boto.UserAgent += gslib.USER_AGENT

# pylint: disable=g-bad-import-order
import httplib2
import oauth2client
from google_reauth import reauth_creds
from google_reauth import errors as reauth_errors
from gslib import context_config
from gslib import wildcard_iterator
from gslib.cloud_api import AccessDeniedException
from gslib.cloud_api import ArgumentException
from gslib.cloud_api import BadRequestException
from gslib.cloud_api import ProjectIdException
from gslib.cloud_api import ServiceException
from gslib.command_runner import CommandRunner
import apitools.base.py.exceptions as apitools_exceptions
from gslib.utils import boto_util
from gslib.utils import constants
from gslib.utils import system_util
from gslib.sig_handling import GetCaughtSignals
from gslib.sig_handling import InitializeSignalHandling
from gslib.sig_handling import RegisterSignalHandler

CONFIG_KEYS_TO_REDACT = ['proxy', 'proxy_port', 'proxy_user', 'proxy_pass']

# We don't use the oauth2 authentication plugin directly; importing it here
# ensures that it's loaded and available by default when an operation requiring
# authentication is performed.
try:
  # pylint: disable=unused-import,g-import-not-at-top
  import gcs_oauth2_boto_plugin
except ImportError:
  pass

DEBUG_WARNING = """
***************************** WARNING *****************************
*** You are running gsutil with debug output enabled.
*** Be aware that debug output includes authentication credentials.
*** Make sure to remove the value of the Authorization header for
*** each HTTP request printed to the console prior to posting to
*** a public medium such as a forum post or Stack Overflow.
***************************** WARNING *****************************
""".lstrip()

TRACE_WARNING = """
***************************** WARNING *****************************
*** You are running gsutil with trace output enabled.
*** Be aware that trace output includes authentication credentials
*** and may include the contents of any files accessed during the trace.
***************************** WARNING *****************************
""".lstrip()

HTTP_WARNING = """
***************************** WARNING *****************************
*** You are running gsutil with the "https_validate_certificates" config
*** variable set to False. This option should always be set to True in
*** production environments to protect against man-in-the-middle attacks,
*** and leaking of user data.
***************************** WARNING *****************************
""".lstrip()

debug_level = 0
test_exception_traces = False


# pylint: disable=unused-argument
def _CleanupSignalHandler(signal_num, cur_stack_frame):
  """Cleans up if process is killed with SIGINT, SIGQUIT or SIGTERM.

  Note that this method is called after main() has been called, so it has
  access to all the modules imported at the start of main().

  Args:
    signal_num: Unused, but required in the method signature.
    cur_stack_frame: Unused, but required in the method signature.
  """
  _Cleanup()
  if (gslib.utils.parallelism_framework_util.
      CheckMultiprocessingAvailableAndInit().is_available):
    gslib.command.TeardownMultiprocessingProcesses()


def _Cleanup():
  for fname in boto_util.GetCleanupFiles():
    try:
      os.unlink(fname)
    except:  # pylint: disable=bare-except
      pass


def _OutputAndExit(message, exception=None):
  """Outputs message to stderr and exits gsutil with code 1.

  This function should only be called in single-process, single-threaded mode.

  Args:
    message: Message to print to stderr.
    exception: The exception that caused gsutil to fail.
  """
  if debug_level >= constants.DEBUGLEVEL_DUMP_REQUESTS or test_exception_traces:
    stack_trace = traceback.format_exc()
    err = ('DEBUG: Exception stack trace:\n    %s\n%s\n' %
           (re.sub('\\n', '\n    ', stack_trace), message))
  else:
    err = '%s\n' % message
  try:
    text_util.print_to_fd(err, end='', file=sys.stderr)
  except UnicodeDecodeError:
    # Can happen when outputting invalid Unicode filenames.
    sys.stderr.write(err)
  if exception:
    metrics.LogFatalError(exception)
  sys.exit(1)


def _OutputUsageAndExit(command_runner):
  command_runner.RunNamedCommand('help')
  sys.exit(1)


class GsutilFormatter(logging.Formatter):
  """A logging.Formatter that supports logging microseconds (%f)."""

  def formatTime(self, record, datefmt=None):
    if datefmt:
      return datetime.datetime.fromtimestamp(record.created).strftime(datefmt)

    # Use default implementation if datefmt is not specified.
    return super(GsutilFormatter, self).formatTime(record, datefmt=datefmt)


def _ConfigureRootLogger(level=logging.INFO):
  """Similar to logging.basicConfig() except it always adds a handler."""
  log_format = '%(levelname)s %(asctime)s %(filename)s] %(message)s'
  date_format = '%m%d %H:%M:%S.%f'
  formatter = GsutilFormatter(fmt=log_format, datefmt=date_format)
  handler = logging.StreamHandler()
  handler.setFormatter(formatter)
  root_logger = logging.getLogger()
  root_logger.addHandler(handler)
  root_logger.setLevel(level)


def main():
  InitializeSignalHandling()
  # Any modules used in initializing multiprocessing variables must be
  # imported after importing gslib.__main__.
  # pylint: disable=redefined-outer-name,g-import-not-at-top
  import gslib.boto_translation
  import gslib.command
  import gslib.utils.parallelism_framework_util
  # pylint: disable=unused-variable
  from gcs_oauth2_boto_plugin import oauth2_client
  from apitools.base.py import credentials_lib
  # pylint: enable=unused-variable
  if (gslib.utils.parallelism_framework_util.
      CheckMultiprocessingAvailableAndInit().is_available):
    # These setup methods must be called, and, on Windows, they can only be
    # called from within an "if __name__ == '__main__':" block.
    gslib.command.InitializeMultiprocessingVariables()
    gslib.boto_translation.InitializeMultiprocessingVariables()
  else:
    gslib.command.InitializeThreadingVariables()

  # This needs to be done after InitializeMultiprocessingVariables(), since
  # otherwise we can't call CreateLock.
  try:
    # pylint: disable=unused-import,g-import-not-at-top
    import gcs_oauth2_boto_plugin
    gsutil_client_id, gsutil_client_secret = (
        system_util.GetGsutilClientIdAndSecret())
    gcs_oauth2_boto_plugin.oauth2_helper.SetFallbackClientIdAndSecret(
        gsutil_client_id, gsutil_client_secret)
    gcs_oauth2_boto_plugin.oauth2_helper.SetLock(
        gslib.utils.parallelism_framework_util.CreateLock())
    credentials_lib.SetCredentialsCacheFileLock(
        gslib.utils.parallelism_framework_util.CreateLock())
  except ImportError:
    pass

  global debug_level
  global test_exception_traces

  supported, err = check_python_version_support()
  if not supported:
    raise CommandException(err)
    sys.exit(1)

  boto_util.MonkeyPatchBoto()
  system_util.MonkeyPatchHttp()

  # In gsutil 4.0 and beyond, we don't use the boto library for the JSON
  # API. However, we still store gsutil configuration data in the .boto
  # config file for compatibility with previous versions and user convenience.
  # Many users have a .boto configuration file from previous versions, and it
  # is useful to have all of the configuration for gsutil stored in one place.
  command_runner = CommandRunner()
  if not boto_util.BOTO_IS_SECURE:
    raise CommandException('\n'.join(
        textwrap.wrap(
            'Your boto configuration has is_secure = False. Gsutil cannot be '
            'run this way, for security reasons.')))

  headers = {}
  parallel_operations = False
  quiet = False
  version = False
  debug_level = 0
  trace_token = None
  perf_trace_token = None
  test_exception_traces = False
  user_project = None

  # If user enters no commands just print the usage info.
  if len(sys.argv) == 1:
    sys.argv.append('help')

  # Change the default of the 'https_validate_certificates' boto option to
  # True (it is currently False in boto).
  if not boto.config.has_option('Boto', 'https_validate_certificates'):
    if not boto.config.has_section('Boto'):
      boto.config.add_section('Boto')
    boto.config.setbool('Boto', 'https_validate_certificates', True)

  for signal_num in GetCaughtSignals():
    RegisterSignalHandler(signal_num, _CleanupSignalHandler)

  try:
    for o, a in opts:
      if o in ('-d', '--debug'):
        # Also causes boto to include httplib header output.
        debug_level = constants.DEBUGLEVEL_DUMP_REQUESTS
      elif o in ('-D', '--detailedDebug'):
        # We use debug level 3 to ask gsutil code to output more detailed
        # debug output. This is a bit of a hack since it overloads the same
        # flag that was originally implemented for boto use. And we use -DD
        # to ask for really detailed debugging (i.e., including HTTP payload).
        if debug_level == constants.DEBUGLEVEL_DUMP_REQUESTS:
          debug_level = constants.DEBUGLEVEL_DUMP_REQUESTS_AND_PAYLOADS
        else:
          debug_level = constants.DEBUGLEVEL_DUMP_REQUESTS
      elif o in ('-?', '--help'):
        _OutputUsageAndExit(command_runner)
      elif o in ('-h', '--header'):
        (hdr_name, _, hdr_val) = a.partition(':')
        if not hdr_name:
          _OutputUsageAndExit(command_runner)
        headers[hdr_name.lower()] = hdr_val
      elif o in ('-m', '--multithreaded'):
        parallel_operations = True
      elif o in ('-q', '--quiet'):
        quiet = True
      elif o == '-u':
        user_project = a
      elif o in ('-v', '--version'):
        version = True
      elif o in ('-i', '--impersonate-service-account'):
        constants.IMPERSONATE_SERVICE_ACCOUNT = a
      elif o == '--perf-trace-token':
        perf_trace_token = a
      elif o == '--trace-token':
        trace_token = a
      elif o == '--testexceptiontraces':  # Hidden flag for integration tests.
        test_exception_traces = True
        # Avoid printing extra warnings to stderr regarding long retries by
        # setting the threshold very high.
        constants.LONG_RETRY_WARN_SEC = 3600
      elif o in ('-o', '--option'):
        (opt_section_name, _, opt_value) = a.partition('=')
        if not opt_section_name:
          _OutputUsageAndExit(command_runner)
        (opt_section, _, opt_name) = opt_section_name.partition(':')
        if not opt_section or not opt_name:
          _OutputUsageAndExit(command_runner)
        if not boto.config.has_section(opt_section):
          boto.config.add_section(opt_section)
        boto.config.set(opt_section, opt_name, opt_value)

    # Now that any Boto option overrides (via `-o` args) have been parsed,
    # perform initialization that depends on those options.
    boto_util.configured_certs_file = (boto_util.ConfigureCertsFile())

    metrics.LogCommandParams(global_opts=opts)
    httplib2.debuglevel = debug_level
    if trace_token:
      sys.stderr.write(TRACE_WARNING)
    if debug_level >= constants.DEBUGLEVEL_DUMP_REQUESTS:
      sys.stderr.write(DEBUG_WARNING)
      _ConfigureRootLogger(level=logging.DEBUG)
      command_runner.RunNamedCommand('ver', ['-l'])

      config_items = []
      for config_section in ('Boto', 'GSUtil'):
        try:
          config_items.extend(boto.config.items(config_section))
        except configparser.NoSectionError:
          pass
      for i in range(len(config_items)):
        config_item_key = config_items[i][0]
        if config_item_key in CONFIG_KEYS_TO_REDACT:
          config_items[i] = (config_item_key, 'REDACTED')
      sys.stderr.write('Command being run: %s\n' % ' '.join(sys.argv))
      sys.stderr.write('config_file_list: %s\n' %
                       boto_util.GetFriendlyConfigFilePaths())
      sys.stderr.write('config: %s\n' % str(config_items))
    else:  # Non-debug log level.
      root_logger_level = logging.WARNING if quiet else logging.INFO
      # oauth2client uses INFO and WARNING logging in places that would better
      # correspond to gsutil's debug logging (e.g., when refreshing
      # access tokens), so we bump the threshold one level higher where
      # appropriate. These log levels work for regular- and quiet-level logging.
      oa2c_logger_level = logging.WARNING
      oa2c_multiprocess_file_storage_logger_level = logging.ERROR

      _ConfigureRootLogger(level=root_logger_level)
      oauth2client.client.logger.setLevel(oa2c_logger_level)
      oauth2client.contrib.multiprocess_file_storage.logger.setLevel(
          oa2c_multiprocess_file_storage_logger_level)
      # pylint: disable=protected-access
      oauth2client.transport._LOGGER.setLevel(oa2c_logger_level)
      reauth_creds._LOGGER.setLevel(oa2c_logger_level)
      # pylint: enable=protected-access

    # TODO(reauth): Fix once reauth pins to pyu2f version newer than 0.1.3.
    # Fixes pyu2f v0.1.3 bug.
    import six  # pylint: disable=g-import-not-at-top
    six.input = six.moves.input

    if not boto_util.CERTIFICATE_VALIDATION_ENABLED:
      sys.stderr.write(HTTP_WARNING)

    if version:
      command_name = 'version'
    elif not args:
      command_name = 'help'
    else:
      command_name = args[0]
      if command_name != 'test':
        # Don't initialize mTLS authentication because
        # tests that need it will do this initialization themselves.
        context_config.create_context_config(logging.getLogger())

    _CheckAndWarnForProxyDifferences()

    # Both 1 and 2 are valid _ARGCOMPLETE values; this var tells argcomplete at
    # what argv[] index the command to match starts. We want it to start at the
    # value for the path to gsutil, so:
    # $ gsutil <command>  # Should be the 1st argument, so '1'
    # $ python gsutil <command>  # Should be the 2nd argument, so '2'
    # Both are valid; most users invoke gsutil in the first style, but our
    # integration and prerelease tests invoke it in the second style, as we need
    # to specify the Python interpreter used to run gsutil.
    if os.environ.get('_ARGCOMPLETE', '0') in ('1', '2'):
      return _PerformTabCompletion(command_runner)

    return _RunNamedCommandAndHandleExceptions(
        command_runner,
        command_name,
        args=args[1:],
        headers=headers,
        debug_level=debug_level,
        trace_token=trace_token,
        parallel_operations=parallel_operations,
        perf_trace_token=perf_trace_token,
        user_project=user_project)
  finally:
    _Cleanup()


def _CheckAndWarnForProxyDifferences():
  # If there are both boto config and environment variable config present for
  # proxies, unset the environment variable and warn if it differs.
  boto_port = boto.config.getint('Boto', 'proxy_port', 0)
  if boto.config.get('Boto', 'proxy', None) or boto_port:
    for proxy_env_var in ['http_proxy', 'https_proxy', 'HTTPS_PROXY']:
      if proxy_env_var in os.environ and os.environ[proxy_env_var]:
        differing_values = []
        proxy_info = boto_util.ProxyInfoFromEnvironmentVar(proxy_env_var)
        if proxy_info.proxy_host != boto.config.get('Boto', 'proxy', None):
          differing_values.append(
              'Boto proxy host: "%s" differs from %s proxy host: "%s"' %
              (boto.config.get('Boto', 'proxy',
                               None), proxy_env_var, proxy_info.proxy_host))
        if (proxy_info.proxy_user != boto.config.get('Boto', 'proxy_user',
                                                     None)):
          differing_values.append(
              'Boto proxy user: "%s" differs from %s proxy user: "%s"' %
              (boto.config.get('Boto', 'proxy_user',
                               None), proxy_env_var, proxy_info.proxy_user))
        if (proxy_info.proxy_pass != boto.config.get('Boto', 'proxy_pass',
                                                     None)):
          differing_values.append(
              'Boto proxy password differs from %s proxy password' %
              proxy_env_var)
        # Only compare ports if at least one is present, since the
        # boto logic for selecting default ports has not yet executed.
        if ((proxy_info.proxy_port or boto_port) and
            proxy_info.proxy_port != boto_port):
          differing_values.append(
              'Boto proxy port: "%s" differs from %s proxy port: "%s"' %
              (boto_port, proxy_env_var, proxy_info.proxy_port))
        if differing_values:
          sys.stderr.write('\n'.join(
              textwrap.wrap(
                  'WARNING: Proxy configuration is present in both the %s '
                  'environment variable and boto configuration, but '
                  'configuration differs. boto configuration proxy values will '
                  'be used. Differences detected:' % proxy_env_var)))
          sys.stderr.write('\n%s\n' % '\n'.join(differing_values))
        # Regardless of whether the proxy configuration values matched,
        # delete the environment variable so as not to confuse boto.
        del os.environ[proxy_env_var]


def _HandleUnknownFailure(e):
  # Called if we fall through all known/handled exceptions.
  raise
  _OutputAndExit(message='Failure: %s.' % e, exception=e)


def _HandleCommandException(e):
  if e.informational:
    _OutputAndExit(message=e.reason, exception=e)
  else:
    _OutputAndExit(message='CommandException: %s' % e.reason, exception=e)


# pylint: disable=unused-argument
def _HandleControlC(signal_num, cur_stack_frame):
  """Called when user hits ^C.

  This function prints a brief message instead of the normal Python stack trace
  (unless -D option is used).

  Args:
    signal_num: Signal that was caught.
    cur_stack_frame: Unused.
  """
  if debug_level >= 2:
    stack_trace = ''.join(traceback.format_list(traceback.extract_stack()))
    _OutputAndExit('DEBUG: Caught CTRL-C (signal %d) - Exception stack trace:\n'
                   '    %s' %
                   (signal_num, re.sub('\\n', '\n    ', stack_trace)),
                   exception=ControlCException())
  else:
    _OutputAndExit('Caught CTRL-C (signal %d) - exiting' % signal_num,
                   exception=ControlCException())


def _HandleSigQuit(signal_num, cur_stack_frame):
  r"""Called when user hits ^\, so we can force breakpoint a running gsutil."""
  import pdb  # pylint: disable=g-import-not-at-top
  pdb.set_trace()


def _ConstructAccountProblemHelp(reason):
  """Constructs a help string for an access control error.

  Args:
    reason: e.reason string from caught exception.

  Returns:
    Contructed help text.
  """
  default_project_id = boto.config.get_value('GSUtil', 'default_project_id')
  # pylint: disable=line-too-long, g-inconsistent-quotes
  acct_help = (
      "Your request resulted in an AccountProblem (403) error. Usually this "
      "happens if you attempt to create a bucket without first having "
      "enabled billing for the project you are using. Please ensure billing is "
      "enabled for your project by following the instructions at "
      "`Google Cloud Platform Console<https://support.google.com/cloud/answer/6158867>`. "
  )
  if default_project_id:
    acct_help += (
        "In the project overview, ensure that the Project Number listed for "
        "your project matches the project ID (%s) from your boto config file. "
        % default_project_id)
  acct_help += (
      "If the above doesn't resolve your AccountProblem, please send mail to "
      "buganizer-system+187143@google.com requesting assistance, noting the "
      "exact command you ran, the fact that you received a 403 AccountProblem "
      "error, and your project ID. Please do not post your project ID on "
      "StackOverflow. "
      "Note: It's possible to use Google Cloud Storage without enabling "
      "billing if you're only listing or reading objects for which you're "
      "authorized, or if you're uploading objects to a bucket billed to a "
      "project that has billing enabled. But if you're attempting to create "
      "buckets or upload objects to a bucket owned by your own project, you "
      "must first enable billing for that project.")
  return acct_help


def _CheckAndHandleCredentialException(e, args):
  # Provide detail to users who have no boto config file (who might previously
  # have been using gsutil only for accessing publicly readable buckets and
  # objects).
  if (not boto_util.HasConfiguredCredentials() and not boto.config.get_value(
      'Tests', 'bypass_anonymous_access_warning', False)):
    # The check above allows tests to assert that we get a particular,
    # expected failure, rather than always encountering this error message
    # when there are no configured credentials. This allows tests to
    # simulate a second user without permissions, without actually requiring
    # two separate configured users.
    if system_util.InvokedViaCloudSdk():
      message = '\n'.join(
          textwrap.wrap(
              'You are attempting to access protected data with no configured '
              'credentials. Please visit '
              'https://cloud.google.com/console#/project and sign up for an '
              'account, and then run the "gcloud auth login" command to '
              'configure gsutil to use these credentials.'))
    else:
      message = '\n'.join(
          textwrap.wrap(
              'You are attempting to access protected data with no configured '
              'credentials. Please visit '
              'https://cloud.google.com/console#/project and sign up for an '
              'account, and then run the "gsutil config" command to configure '
              'gsutil to use these credentials.'))
    _OutputAndExit(message=message, exception=e)
  elif (e.reason and
        (e.reason == 'AccountProblem' or e.reason == 'Account disabled.' or
         'account for the specified project has been disabled' in e.reason) and
        ','.join(args).find('gs://') != -1):
    _OutputAndExit('\n'.join(
        textwrap.wrap(_ConstructAccountProblemHelp(e.reason))),
                   exception=e)


def _RunNamedCommandAndHandleExceptions(command_runner,
                                        command_name,
                                        args=None,
                                        headers=None,
                                        debug_level=0,
                                        trace_token=None,
                                        parallel_operations=False,
                                        perf_trace_token=None,
                                        user_project=None):
  """Runs the command and handles common exceptions."""
  # Note that this method is run at the end of main() and thus has access to
  # all of the modules imported there.
  # pylint: disable=g-import-not-at-top
  try:
    # Catch ^C so we can print a brief message instead of the normal Python
    # stack trace. Register as a final signal handler because this handler kills
    # the main gsutil process (so it must run last).
    RegisterSignalHandler(signal.SIGINT, _HandleControlC, is_final_handler=True)
    # Catch ^\ so we can force a breakpoint in a running gsutil.
    if not system_util.IS_WINDOWS:
      RegisterSignalHandler(signal.SIGQUIT, _HandleSigQuit)

    return command_runner.RunNamedCommand(command_name,
                                          args,
                                          headers,
                                          debug_level,
                                          trace_token,
                                          parallel_operations,
                                          perf_trace_token=perf_trace_token,
                                          collect_analytics=True,
                                          user_project=user_project)
  except AttributeError as e:
    if str(e).find('secret_access_key') != -1:
      _OutputAndExit(
          'Missing credentials for the given URI(s). Does your '
          'boto config file contain all needed credentials?',
          exception=e)
    else:
      _OutputAndExit(message=str(e), exception=e)
  except CommandException as e:
    _HandleCommandException(e)
  except getopt.GetoptError as e:
    _HandleCommandException(CommandException(e.msg))
  except boto.exception.InvalidUriError as e:
    _OutputAndExit(message='InvalidUriError: %s.' % e.message, exception=e)
  except gslib.exception.InvalidUrlError as e:
    _OutputAndExit(message='InvalidUrlError: %s.' % e.message, exception=e)
  except boto.auth_handler.NotReadyToAuthenticate as e:
    _OutputAndExit(message='NotReadyToAuthenticate', exception=e)
  except gslib.exception.ExternalBinaryError as e:
    _OutputAndExit(message=str(e), exception=e)
  except OSError as e:
    # In Python 3, IOError (next except) is an alias for OSError
    # Sooo... we need the same logic here
    if (e.errno == errno.EPIPE or
        (system_util.IS_WINDOWS and e.errno == errno.EINVAL) and
        not system_util.IsRunningInteractively()):
      # If we get a pipe error, this just means that the pipe to stdout or
      # stderr is broken. This can happen if the user pipes gsutil to a command
      # that doesn't use the entire output stream. Instead of raising an error,
      # just swallow it up and exit cleanly.
      sys.exit(0)
    else:
      _OutputAndExit(message='OSError: %s.' % e.strerror, exception=e)
  except IOError as e:
    if (e.errno == errno.EPIPE or
        (system_util.IS_WINDOWS and e.errno == errno.EINVAL) and
        not system_util.IsRunningInteractively()):
      # If we get a pipe error, this just means that the pipe to stdout or
      # stderr is broken. This can happen if the user pipes gsutil to a command
      # that doesn't use the entire output stream. Instead of raising an error,
      # just swallow it up and exit cleanly.
      sys.exit(0)
    else:
      raise
  except wildcard_iterator.WildcardException as e:
    _OutputAndExit(message=e.reason, exception=e)
  except ProjectIdException as e:
    _OutputAndExit(
        'You are attempting to perform an operation that requires a '
        'project id, with none configured. Please re-run '
        'gsutil config and make sure to follow the instructions for '
        'finding and entering your default project id.',
        exception=e)
  except BadRequestException as e:
    if e.reason == 'MissingSecurityHeader':
      _CheckAndHandleCredentialException(e, args)
    _OutputAndExit(message=e, exception=e)
  except AccessDeniedException as e:
    _CheckAndHandleCredentialException(e, args)
    _OutputAndExit(message=e, exception=e)
  except ArgumentException as e:
    _OutputAndExit(message=e, exception=e)
  except ServiceException as e:
    _OutputAndExit(message=e, exception=e)
  except (oauth2client.client.HttpAccessTokenRefreshError,
          google_auth_exceptions.OAuthError) as e:
    if system_util.InvokedViaCloudSdk():
      _OutputAndExit(
          'Your credentials are invalid. '
          'Please run\n$ gcloud auth login',
          exception=e)
    else:
      _OutputAndExit(
          'Your credentials are invalid. For more help, see '
          '"gsutil help creds", or re-run the gsutil config command (see '
          '"gsutil help config").',
          exception=e)
  except apitools_exceptions.HttpError as e:
    # These should usually be retried by the underlying implementation or
    # wrapped by CloudApi ServiceExceptions, but if we do get them,
    # print something useful.
    _OutputAndExit('HttpError: %s, %s' %
                   (getattr(e.response, 'status', ''), e.content or ''),
                   exception=e)
  except socket.error as e:
    if e.args[0] == errno.EPIPE:
      # Retrying with a smaller file (per suggestion below) works because
      # the library code send loop (in boto/s3/key.py) can get through the
      # entire file and then request the HTTP response before the socket
      # gets closed and the response lost.
      _OutputAndExit(
          'Got a "Broken pipe" error. This can happen to clients using Python '
          '2.x, when the server sends an error response and then closes the '
          'socket (see http://bugs.python.org/issue5542). If you are trying to '
          'upload a large object you might retry with a small (say 200k) '
          'object, and see if you get a more specific error code.',
          exception=e)
    elif e.args[0] == errno.ECONNRESET and ' '.join(args).contains('s3://'):
      _OutputAndExit('\n'.join(
          textwrap.wrap(
              'Got a "Connection reset by peer" error. One way this can happen is '
              'when copying data to/from an S3 regional bucket. If you are using a '
              'regional S3 bucket you could try re-running this command using the '
              'regional S3 endpoint, for example '
              's3://s3-<region>.amazonaws.com/your-bucket. For details about this '
              'problem see https://github.com/boto/boto/issues/2207')),
                     exception=e)
    else:
      _HandleUnknownFailure(e)
  except oauth2client.client.FlowExchangeError as e:
    _OutputAndExit('\n%s\n\n' % '\n'.join(
        textwrap.wrap(
            'Failed to retrieve valid credentials (%s). Make sure you selected and '
            'pasted the ENTIRE authorization code (including any numeric prefix '
            "e.g. '4/')." % e)),
                   exception=e)
  except reauth_errors.ReauthSamlLoginRequiredError:
    if system_util.InvokedViaCloudSdk():
      _OutputAndExit('You must re-authenticate with your SAML IdP. '
                     'Please run\n$ gcloud auth login')
    else:
      _OutputAndExit('You must re-authenticate with your SAML IdP. '
                     'Please run\n$ gsutil config')
  except Exception as e:  # pylint: disable=broad-except
    config_paths = ', '.join(boto_util.GetFriendlyConfigFilePaths())
    # Check for two types of errors related to service accounts. These errors
    # appear to be the same except for their messages, but they are caused by
    # different problems and both have unhelpful error messages. Moreover,
    # the error type belongs to PyOpenSSL, which is not necessarily installed.
    if 'mac verify failure' in str(e):
      _OutputAndExit(
          'Encountered an error while refreshing access token. '
          'If you are using a service account,\nplease verify that the '
          'gs_service_key_file_password field in your config file(s),'
          '\n%s, is correct.' % config_paths,
          exception=e)
    elif 'asn1 encoding routines' in str(e):
      _OutputAndExit(
          'Encountered an error while refreshing access token. '
          'If you are using a service account,\nplease verify that the '
          'gs_service_key_file field in your config file(s),\n%s, is correct.' %
          config_paths,
          exception=e)
    _HandleUnknownFailure(e)


def _PerformTabCompletion(command_runner):
  """Performs gsutil-specific tab completion for the shell."""
  # argparse and argcomplete are bundled with the Google Cloud SDK.
  # When gsutil is invoked from the Google Cloud SDK, both should be available.
  try:
    import argcomplete
    import argparse
  except ImportError as e:
    _OutputAndExit('A library required for performing tab completion was'
                   ' not found.\nCause: %s' % e,
                   exception=e)
  parser = argparse.ArgumentParser(add_help=False)
  command_runner.ConfigureCommandArgumentParsers(parser)
  argcomplete.autocomplete(parser, exit_method=sys.exit)

  return 0


if __name__ == '__main__':
  sys.exit(main())
