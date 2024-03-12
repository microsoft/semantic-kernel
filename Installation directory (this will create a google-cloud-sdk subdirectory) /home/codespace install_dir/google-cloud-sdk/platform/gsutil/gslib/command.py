# -*- coding: utf-8 -*-
# Copyright 2010 Google Inc. All Rights Reserved.
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
"""Base class for gsutil commands.

In addition to base class code, this file contains helpers that depend on base
class state (such as GetAndPrintAcl) In general, functions that depend on
class state and that are used by multiple commands belong in this file.
Functions that don't depend on class state belong in util.py, and non-shared
helpers belong in individual subclasses.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import codecs
from collections import namedtuple
import copy
import getopt
import json
import logging
import os
import signal
import sys
import textwrap
import threading
import time
import traceback

import boto
from boto.storage_uri import StorageUri
import gslib
from gslib.cloud_api import AccessDeniedException
from gslib.cloud_api import ArgumentException
from gslib.cloud_api import ServiceException
from gslib.cloud_api_delegator import CloudApiDelegator
from gslib.cs_api_map import ApiSelector
from gslib.cs_api_map import GsutilApiMapFactory
from gslib.exception import CommandException
from gslib.help_provider import HelpProvider
from gslib.metrics import CaptureThreadStatException
from gslib.metrics import LogPerformanceSummaryParams
from gslib.name_expansion import CopyObjectInfo
from gslib.name_expansion import CopyObjectsIterator
from gslib.name_expansion import NameExpansionIterator
from gslib.name_expansion import NameExpansionResult
from gslib.name_expansion import SeekAheadNameExpansionIterator
from gslib.plurality_checkable_iterator import PluralityCheckableIterator
from gslib.seek_ahead_thread import SeekAheadThread
from gslib.sig_handling import ChildProcessSignalHandler
from gslib.sig_handling import GetCaughtSignals
from gslib.sig_handling import KillProcess
from gslib.sig_handling import MultithreadedMainSignalHandler
from gslib.sig_handling import RegisterSignalHandler
from gslib.storage_url import HaveFileUrls
from gslib.storage_url import HaveProviderUrls
from gslib.storage_url import StorageUrlFromString
from gslib.storage_url import UrlsAreForSingleProvider
from gslib.storage_url import UrlsAreMixOfBucketsAndObjects
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.thread_message import FinalMessage
from gslib.thread_message import MetadataMessage
from gslib.thread_message import PerformanceSummaryMessage
from gslib.thread_message import ProducerThreadMessage
from gslib.ui_controller import MainThreadUIQueue
from gslib.ui_controller import UIController
from gslib.ui_controller import UIThread
from gslib.utils.boto_util import GetFriendlyConfigFilePaths
from gslib.utils.boto_util import GetMaxConcurrentCompressedUploads
from gslib.utils.constants import NO_MAX
from gslib.utils.constants import UTF8
import gslib.utils.parallelism_framework_util
from gslib.utils.parallelism_framework_util import AtomicDict
from gslib.utils.parallelism_framework_util import CheckMultiprocessingAvailableAndInit
from gslib.utils.parallelism_framework_util import multiprocessing_context
from gslib.utils.parallelism_framework_util import ProcessAndThreadSafeInt
from gslib.utils.parallelism_framework_util import PutToQueueWithTimeout
from gslib.utils.parallelism_framework_util import SEEK_AHEAD_JOIN_TIMEOUT
from gslib.utils.parallelism_framework_util import ShouldProhibitMultiprocessing
from gslib.utils.parallelism_framework_util import UI_THREAD_JOIN_TIMEOUT
from gslib.utils.parallelism_framework_util import ZERO_TASKS_TO_DO_ARGUMENT
from gslib.utils.rsync_util import RsyncDiffToApply
from gslib.utils.shim_util import GcloudStorageCommandMixin
from gslib.utils.system_util import GetTermLines
from gslib.utils.system_util import IS_WINDOWS
from gslib.utils.translation_helper import AclTranslation
from gslib.utils.translation_helper import GetNonMetadataHeaders
from gslib.utils.translation_helper import PRIVATE_DEFAULT_OBJ_ACL
from gslib.wildcard_iterator import CreateWildcardIterator
from six.moves import queue as Queue

# pylint: disable=g-import-not-at-top
try:
  from Crypto import Random as CryptoRandom
except ImportError:
  CryptoRandom = None
# pylint: enable=g-import-not-at-top

OFFER_GSUTIL_M_SUGGESTION_THRESHOLD = 5
OFFER_GSUTIL_M_SUGGESTION_FREQUENCY = 1000


def CreateOrGetGsutilLogger(command_name):
  """Fetches a logger with the given name that resembles 'print' output.

  Initial Logger Configuration:

  The logger abides by gsutil -d/-D/-DD/-q options. If none of those options
  were specified at invocation, the returned logger will display all messages
  logged with level INFO or above. Log propagation is disabled.

  If a logger with the specified name has already been created and configured,
  it is not reconfigured, e.g.:

    foo = CreateOrGetGsutilLogger('foo')  # Creates and configures Logger "foo".
    foo.setLevel(logging.DEBUG)  # Change level from INFO to DEBUG
    foo = CreateOrGetGsutilLogger('foo')  # Does not reset level to INFO.

  Args:
    command_name: (str) Command name to create logger for.

  Returns:
    A logging.Logger object.
  """
  log = logging.getLogger(command_name)
  # There are some scenarios (e.g. unit tests, commands like `mv` that call
  # other commands) in which we call this function multiple times. To avoid
  # adding duplicate handlers or overwriting logger attributes set elsewhere,
  # we only configure the logger if it's one we haven't configured before (i.e.
  # one that doesn't have a handler set yet).
  if not log.handlers:
    log.propagate = False
    log.setLevel(logging.root.level)
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter('%(message)s'))
    log.addHandler(log_handler)
  return log


def _DefaultExceptionHandler(cls, e):
  cls.logger.exception(e)


def _UrlArgChecker(command_instance, url):
  if not command_instance.exclude_symlinks:
    return True
  exp_src_url = url.expanded_storage_url
  if exp_src_url.IsFileUrl() and os.path.islink(exp_src_url.object_name):
    command_instance.logger.info('Skipping symbolic link %s...', exp_src_url)
    return False
  return True


def DummyArgChecker(*unused_args):
  return True


def SetAclFuncWrapper(cls, name_expansion_result, thread_state=None):
  return cls.SetAclFunc(name_expansion_result, thread_state=thread_state)


def SetAclExceptionHandler(cls, e):
  """Exception handler that maintains state about post-completion status."""
  cls.logger.error(str(e))
  cls.everything_set_okay = False


# We will keep this list of all thread- or process-safe queues (except the
# global status queue) ever created by the main thread so that we can
# forcefully kill them upon shutdown. Otherwise, we encounter a Python bug in
# which empty queues block forever on join (which is called as part of the
# Python exit function cleanup) under the impression that they are non-empty.
# However, this also lets us shut down somewhat more cleanly when interrupted.
queues = []


def _CryptoRandomAtFork():
  if CryptoRandom and getattr(CryptoRandom, 'atfork', None):
    # Fixes https://github.com/GoogleCloudPlatform/gsutil/issues/390. The
    # oauth2client module uses Python's Crypto library when pyOpenSSL isn't
    # present; that module requires calling atfork() in both the parent and
    # child process after a new process is forked.
    CryptoRandom.atfork()


def _NewMultiprocessingQueue():
  new_queue = multiprocessing_context.Queue(MAX_QUEUE_SIZE)
  queues.append(new_queue)
  return new_queue


def _NewThreadsafeQueue():
  new_queue = Queue.Queue(MAX_QUEUE_SIZE)
  queues.append(new_queue)
  return new_queue


# The maximum size of a process- or thread-safe queue. Imposing this limit
# prevents us from needing to hold an arbitrary amount of data in memory.
# However, setting this number too high (e.g., >= 32768 on OS X) can cause
# problems on some operating systems.
MAX_QUEUE_SIZE = 32500

# Related to the max queue size above, once we cross this threshold of
# iterated tasks added to the queue, kick off the SeekAheadThread that will
# estimate the total work necessary for the command.
DEFAULT_TASK_ESTIMATION_THRESHOLD = 30000


def _GetTaskEstimationThreshold():
  return boto.config.getint('GSUtil', 'task_estimation_threshold',
                            DEFAULT_TASK_ESTIMATION_THRESHOLD)


# That maximum depth of the tree of recursive calls to command.Apply. This is
# an arbitrary limit put in place to prevent developers from accidentally
# causing problems with infinite recursion, and it can be increased if needed.
MAX_RECURSIVE_DEPTH = 5

# Map from deprecated aliases to the current command and subcommands that
# provide the same behavior.
# TODO: Remove this map and deprecate old commands on 9/9/14.
OLD_ALIAS_MAP = {
    'chacl': ['acl', 'ch'],
    'getacl': ['acl', 'get'],
    'setacl': ['acl', 'set'],
    'getcors': ['cors', 'get'],
    'setcors': ['cors', 'set'],
    'chdefacl': ['defacl', 'ch'],
    'getdefacl': ['defacl', 'get'],
    'setdefacl': ['defacl', 'set'],
    'disablelogging': ['logging', 'set', 'off'],
    'enablelogging': ['logging', 'set', 'on'],
    'getlogging': ['logging', 'get'],
    'getversioning': ['versioning', 'get'],
    'setversioning': ['versioning', 'set'],
    'getwebcfg': ['web', 'get'],
    'setwebcfg': ['web', 'set']
}

# Declare all of the module level variables - see
# InitializeMultiprocessingVariables for an explanation of why this is
# necessary.
# pylint: disable=global-at-module-level
global manager, consumer_pools, task_queues, caller_id_lock, caller_id_counter
global total_tasks, call_completed_map, global_return_values_map
global need_pool_or_done_cond, caller_id_finished_count, new_pool_needed
global current_max_recursive_level, shared_vars_map, shared_vars_list_map
global class_map, worker_checking_level_lock, failure_count, thread_stats
global glob_status_queue, ui_controller, concurrent_compressed_upload_lock


def InitializeMultiprocessingVariables():
  """Initializes module-level variables that will be inherited by subprocesses.

  On Windows, a multiprocessing.Manager object should only
  be created within an "if __name__ == '__main__':" block. This function
  must be called, otherwise every command that calls Command.Apply will fail.

  While multiprocessing variables are initialized at the beginning of
  gsutil execution, new processes and threads are created only by calls
  to Command.Apply. When multiple processes and threads are used,
  the flow of startup/teardown looks like this:

  1. __main__: initializes multiprocessing variables, including any necessary
     Manager processes (here and in gslib.utils.parallelism_framework_util).
  2. __main__: Registers signal handlers for terminating signals responsible
     for cleaning up multiprocessing variables and manager processes upon exit.
  3. Command.Apply registers signal handlers for the main process to kill
     itself after the cleanup handlers registered by __main__ have executed.
  4. If worker processes have not been created for the current level of
     recursive calls, Command.Apply creates those processes.

  ---- Parallel operations start here, so steps are no longer numbered. ----
  - Command.Apply in the main thread starts the ProducerThread.
    - The Producer thread adds task arguments to the global task queue.
      - It optionally starts the SeekAheadThread which estimates total
        work for the Apply call.

  - Command.Apply in the main thread starts the UIThread, which will consume
    messages from the global status queue, process them, and display them to
    the user.

  - Each worker process creates a thread pool to perform work.
    - The worker process registers signal handlers to kill itself in
      response to a terminating signal.
    - The main thread of the worker process moves items from the global
      task queue to the process-local task queue.
    - Worker threads retrieve items from the process-local task queue,
      perform the work, and post messages to the global status queue.
    - Worker threads may themselves call Command.Apply.
      - This creates a new pool of worker subprocesses with the same size
        as the main pool. This pool is shared amongst all Command.Apply calls
        at the given recursion depth.
      - This reuses the global UIThread, global status queue, and global task
        queue.
      - This starts a new ProducerThread.
      - A SeekAheadThread is not started at this level; only one such thread
        exists at the top level, and it provides estimates for top-level work
        only.

  - The ProducerThread runs out of tasks, or the user signals cancellation.
    - The ProducerThread cancels the SeekAheadThread (if it is running) via
      an event.
    - The ProducerThread enqueues special terminating messages on the
      global task queue and global status queue, signaling the UI Thread to
      shut down and the main thread to continue operation.
    - In the termination case, existing processes exit in response to
      terminating signals from the main process.

  ---- Parallel operations end here. ----
  5. Further top-level calls to Command.Apply can be made, which will repeat
     all of the steps made in #4, except that worker processes will be
     reused.
  """
  # This list of global variables must exactly match the above list of
  # declarations.
  # pylint: disable=global-variable-undefined
  global manager, consumer_pools, task_queues, caller_id_lock, caller_id_counter
  global total_tasks, call_completed_map, global_return_values_map, thread_stats
  global need_pool_or_done_cond, caller_id_finished_count, new_pool_needed
  global current_max_recursive_level, shared_vars_map, shared_vars_list_map
  global class_map, worker_checking_level_lock, failure_count, glob_status_queue
  global concurrent_compressed_upload_lock

  manager = multiprocessing_context.Manager()

  # List of ConsumerPools - used during shutdown to clean up child processes.
  consumer_pools = []

  # List of all existing task queues - used by all pools to find the queue
  # that's appropriate for the given recursive_apply_level.
  task_queues = []

  # Used to assign a globally unique caller ID to each Apply call.
  caller_id_lock = manager.Lock()
  caller_id_counter = ProcessAndThreadSafeInt(True)

  # Map from caller_id to total number of tasks to be completed for that ID.
  total_tasks = AtomicDict(manager=manager)

  # Map from caller_id to a boolean which is True iff all its tasks are
  # finished.
  call_completed_map = AtomicDict(manager=manager)

  # Used to keep track of the set of return values for each caller ID.
  global_return_values_map = AtomicDict(manager=manager)

  # Condition used to notify any waiting threads that a task has finished or
  # that a call to Apply needs a new set of consumer processes.
  need_pool_or_done_cond = manager.Condition()

  # Lock used to prevent multiple worker processes from asking the main thread
  # to create a new consumer pool for the same level.
  worker_checking_level_lock = manager.Lock()

  # Map from caller_id to the current number of completed tasks for that ID.
  caller_id_finished_count = AtomicDict(manager=manager)

  # Used as a way for the main thread to distinguish between being woken up
  # by another call finishing and being woken up by a call that needs a new set
  # of consumer processes.
  new_pool_needed = ProcessAndThreadSafeInt(True)

  current_max_recursive_level = ProcessAndThreadSafeInt(True)

  # Map from (caller_id, name) to the value of that shared variable.
  shared_vars_map = AtomicDict(manager=manager)
  shared_vars_list_map = AtomicDict(manager=manager)

  # Map from (process id, thread id) to a _ThreadStat object (see WorkerThread).
  # Used to keep track of thread idle time and execution time.
  thread_stats = AtomicDict(manager=manager)

  # Map from caller_id to calling class.
  class_map = manager.dict()

  # Number of tasks that resulted in an exception in calls to Apply().
  failure_count = ProcessAndThreadSafeInt(True)

  # Central queue for status reporting across multiple processes and threads.
  # It's possible that if many processes and threads are executing small file
  # writes or metadata changes quickly, performance may be bounded by lock
  # contention on the queue. Initial testing conducted with
  # 12 processes * 5 threads per process showed little difference.  If this
  # becomes a performance bottleneck in the future, consider creating a queue
  # per-process and having the UI thread poll all of the queues; that approach
  # would need to address:
  # - Queue fairness if one queue grows to be disproportionately large
  # - Reasonable time correlation with events as they occur
  #
  # This queue must be torn down after worker processes/threads and the
  # UI thread have been torn down. Otherwise, these threads may have
  # undefined behavior when trying to interact with a non-existent queue.
  glob_status_queue = manager.Queue(MAX_QUEUE_SIZE)

  # Semaphore lock used to prevent resource exhaustion when running many
  # compressed uploads in parallel.
  concurrent_compressed_upload_lock = manager.BoundedSemaphore(
      GetMaxConcurrentCompressedUploads())


def TeardownMultiprocessingProcesses():
  """Should be called by signal handlers prior to shut down."""
  # Shut down all processes in consumer pools in preparation for exiting.
  ShutDownGsutil()
  # Shut down command and util's multiprocessing.Manager().
  # pylint: disable=global-variable-not-assigned,global-variable-undefined
  global manager
  # pylint: enable=global-variable-not-assigned,global-variable-undefined
  manager.shutdown()
  gslib.utils.parallelism_framework_util.top_level_manager.shutdown()


def InitializeThreadingVariables():
  """Initializes module-level variables used when running multi-threaded.

  When multiprocessing is not available (or on Windows where only 1 process
  is used), thread-safe analogs to the multiprocessing global variables
  must be initialized. This function is the thread-safe analog to
  InitializeMultiprocessingVariables.
  """
  # pylint: disable=global-variable-undefined
  global global_return_values_map, shared_vars_map, failure_count
  global caller_id_finished_count, shared_vars_list_map, total_tasks
  global need_pool_or_done_cond, call_completed_map, class_map, thread_stats
  global task_queues, caller_id_lock, caller_id_counter, glob_status_queue
  global worker_checking_level_lock, current_max_recursive_level
  global concurrent_compressed_upload_lock
  caller_id_counter = ProcessAndThreadSafeInt(False)
  caller_id_finished_count = AtomicDict()
  caller_id_lock = threading.Lock()
  call_completed_map = AtomicDict()
  class_map = AtomicDict()
  current_max_recursive_level = ProcessAndThreadSafeInt(False)
  failure_count = ProcessAndThreadSafeInt(False)
  glob_status_queue = Queue.Queue(MAX_QUEUE_SIZE)
  global_return_values_map = AtomicDict()
  need_pool_or_done_cond = threading.Condition()
  shared_vars_list_map = AtomicDict()
  shared_vars_map = AtomicDict()
  thread_stats = AtomicDict()
  task_queues = []
  total_tasks = AtomicDict()
  worker_checking_level_lock = threading.Lock()
  concurrent_compressed_upload_lock = threading.BoundedSemaphore(
      GetMaxConcurrentCompressedUploads())


# Each subclass of Command must define a property named 'command_spec' that is
# an instance of the following class.
CommandSpec = namedtuple(
    'CommandSpec',
    [
        # Name of command.
        'command_name',
        # Usage synopsis.
        'usage_synopsis',
        # List of command name aliases.
        'command_name_aliases',
        # Min number of args required by this command.
        'min_args',
        # Max number of args required by this command, or NO_MAX.
        'max_args',
        # Getopt-style string specifying acceptable sub args.
        'supported_sub_args',
        # True if file URLs are acceptable for this command.
        'file_url_ok',
        # True if provider-only URLs are acceptable for this command.
        'provider_url_ok',
        # Index in args of first URL arg.
        'urls_start_arg',
        # List of supported APIs
        'gs_api_support',
        # Default API to use for this command
        'gs_default_api',
        # Private arguments (for internal testing)
        'supported_private_args',
        'argparse_arguments',
    ])


class Command(HelpProvider, GcloudStorageCommandMixin):
  """Base class for all gsutil commands."""

  # Each subclass must override this with an instance of CommandSpec.
  command_spec = None

  _commands_with_subcommands_and_subopts = ('acl', 'defacl', 'iam', 'kms',
                                            'label', 'logging', 'notification',
                                            'retention', 'web')

  # This keeps track of the recursive depth of the current call to Apply.
  recursive_apply_level = 0

  # If the multiprocessing module isn't available, we'll use this to keep track
  # of the caller_id.
  sequential_caller_id = -1

  @staticmethod
  def CreateCommandSpec(command_name,
                        usage_synopsis=None,
                        command_name_aliases=None,
                        min_args=0,
                        max_args=NO_MAX,
                        supported_sub_args='',
                        file_url_ok=False,
                        provider_url_ok=False,
                        urls_start_arg=0,
                        gs_api_support=None,
                        gs_default_api=None,
                        supported_private_args=None,
                        argparse_arguments=None):
    """Creates an instance of CommandSpec, with defaults."""
    return CommandSpec(command_name=command_name,
                       usage_synopsis=usage_synopsis,
                       command_name_aliases=command_name_aliases or [],
                       min_args=min_args,
                       max_args=max_args,
                       supported_sub_args=supported_sub_args,
                       file_url_ok=file_url_ok,
                       provider_url_ok=provider_url_ok,
                       urls_start_arg=urls_start_arg,
                       gs_api_support=gs_api_support or [ApiSelector.XML],
                       gs_default_api=gs_default_api or ApiSelector.XML,
                       supported_private_args=supported_private_args,
                       argparse_arguments=argparse_arguments or [])

  # Define a convenience property for command name, since it's used many places.
  def _GetDefaultCommandName(self):
    return self.command_spec.command_name

  command_name = property(_GetDefaultCommandName)

  def _CalculateUrlsStartArg(self):
    """Calculate the index in args of the first URL arg.

    Returns:
      Index of the first URL arg (according to the command spec).
    """
    return self.command_spec.urls_start_arg

  def _TranslateDeprecatedAliases(self, args):
    """Map deprecated aliases to the corresponding new command, and warn."""
    new_command_args = OLD_ALIAS_MAP.get(self.command_alias_used, None)
    if new_command_args:
      # Prepend any subcommands for the new command. The command name itself
      # is not part of the args, so leave it out.
      args = new_command_args[1:] + args
      self.logger.warn('\n'.join(
          textwrap.wrap(
              ('You are using a deprecated alias, "%(used_alias)s", for the '
               '"%(command_name)s" command. This will stop working on 9/9/2014. '
               'Please use "%(command_name)s" with the appropriate sub-command in '
               'the future. See "gsutil help %(command_name)s" for details.') %
              {
                  'used_alias': self.command_alias_used,
                  'command_name': self.command_name
              })))
    return args

  def __init__(self,
               command_runner,
               args,
               headers,
               debug,
               trace_token,
               parallel_operations,
               bucket_storage_uri_class,
               gsutil_api_class_map_factory,
               logging_filters=None,
               command_alias_used=None,
               perf_trace_token=None,
               user_project=None):
    """Instantiates a Command.

    Args:
      command_runner: CommandRunner (for commands built atop other commands).
      args: Command-line args (arg0 = actual arg, not command name ala bash).
      headers: Dictionary containing optional HTTP headers to pass to boto.
      debug: Debug level to pass in to boto connection (range 0..3).
      trace_token: Trace token to pass to the API implementation.
      parallel_operations: Should command operations be executed in parallel?
      bucket_storage_uri_class: Class to instantiate for cloud StorageUris.
                                Settable for testing/mocking.
      gsutil_api_class_map_factory: Creates map of cloud storage interfaces.
                                    Settable for testing/mocking.
      logging_filters: Optional list of logging. Filters to apply to this
                       command's logger.
      command_alias_used: The alias that was actually used when running this
                          command (as opposed to the "official" command name,
                          which will always correspond to the file name).
      perf_trace_token: Performance measurement trace token to use when making
          API calls.
      user_project: Project to be billed for this request.

    Implementation note: subclasses shouldn't need to define an __init__
    method, and instead depend on the shared initialization that happens
    here. If you do define an __init__ method in a subclass you'll need to
    explicitly call super().__init__(). But you're encouraged not to do this,
    because it will make changing the __init__ interface more painful.
    """
    # Save class values from constructor params.
    super().__init__()
    self.command_runner = command_runner
    self.unparsed_args = args
    self.headers = headers
    self.debug = debug
    self.trace_token = trace_token
    self.perf_trace_token = perf_trace_token
    self.parallel_operations = parallel_operations
    self.user_project = user_project
    self.bucket_storage_uri_class = bucket_storage_uri_class
    self.gsutil_api_class_map_factory = gsutil_api_class_map_factory
    self.exclude_symlinks = False
    self.recursion_requested = False
    self.all_versions = False
    self.command_alias_used = command_alias_used
    self.seek_ahead_gsutil_api = None
    # pylint: disable=global-variable-not-assigned
    # pylint: disable=global-variable-undefined
    global ui_controller
    # pylint: enable=global-variable-undefined
    # pylint: enable=global-variable-not-assigned
    # Global instance of a threaded logger object.
    self.logger = CreateOrGetGsutilLogger(self.command_name)
    if logging_filters:
      for log_filter in logging_filters:
        self.logger.addFilter(log_filter)

    if self.headers is not None:
      self.non_metadata_headers = GetNonMetadataHeaders(self.headers)
    else:
      self.non_metadata_headers = None

    if self.command_spec is None:
      raise CommandException('"%s" command implementation is missing a '
                             'command_spec definition.' % self.command_name)

    self.quiet_mode = not self.logger.isEnabledFor(logging.INFO)
    ui_controller = UIController(quiet_mode=self.quiet_mode,
                                 dump_status_messages_file=boto.config.get(
                                     'GSUtil', 'dump_status_messages_file',
                                     None))

    # Parse and validate args.
    self.args = self._TranslateDeprecatedAliases(args)
    self.ParseSubOpts()

    # Named tuple public functions start with _
    # pylint: disable=protected-access
    self.command_spec = self.command_spec._replace(
        urls_start_arg=self._CalculateUrlsStartArg())

    if (len(self.args) < self.command_spec.min_args or
        len(self.args) > self.command_spec.max_args):
      self.RaiseWrongNumberOfArgumentsException()

    if self.command_name not in self._commands_with_subcommands_and_subopts:
      self.CheckArguments()

    # Build the support and default maps from the command spec.
    support_map = {
        'gs': self.command_spec.gs_api_support,
        's3': [ApiSelector.XML]
    }
    default_map = {
        'gs': self.command_spec.gs_default_api,
        's3': ApiSelector.XML
    }
    self.gsutil_api_map = GsutilApiMapFactory.GetApiMap(
        self.gsutil_api_class_map_factory, support_map, default_map)

    self.project_id = None
    self.gsutil_api = CloudApiDelegator(self.bucket_storage_uri_class,
                                        self.gsutil_api_map,
                                        self.logger,
                                        MainThreadUIQueue(
                                            sys.stderr, ui_controller),
                                        debug=self.debug,
                                        http_headers=self.non_metadata_headers,
                                        trace_token=self.trace_token,
                                        perf_trace_token=self.perf_trace_token,
                                        user_project=self.user_project)
    # Cross-platform path to run gsutil binary.
    self.gsutil_cmd = ''
    # If running on Windows, invoke python interpreter explicitly.
    if IS_WINDOWS:
      self.gsutil_cmd += 'python '
    # Add full path to gsutil to make sure we test the correct version.
    self.gsutil_path = gslib.GSUTIL_PATH
    self.gsutil_cmd += self.gsutil_path

    # We're treating recursion_requested like it's used by all commands, but
    # only some of the commands accept the -R option.
    if self.sub_opts:
      for o, unused_a in self.sub_opts:
        if o == '-r' or o == '-R':
          self.recursion_requested = True
          break

    self.multiprocessing_is_available = (
        CheckMultiprocessingAvailableAndInit().is_available)

  def RaiseWrongNumberOfArgumentsException(self):
    """Raises exception for wrong number of arguments supplied to command."""
    if len(self.args) < self.command_spec.min_args:
      tail_str = 's' if self.command_spec.min_args > 1 else ''
      message = ('The %s command requires at least %d argument%s.' %
                 (self.command_name, self.command_spec.min_args, tail_str))
    else:
      message = ('The %s command accepts at most %d arguments.' %
                 (self.command_name, self.command_spec.max_args))
    message += ' Usage:\n%s\nFor additional help run:\n  gsutil help %s' % (
        self.command_spec.usage_synopsis, self.command_name)
    raise CommandException(message)

  def RaiseInvalidArgumentException(self):
    """Raises exception for specifying an invalid argument to command."""
    message = ('Incorrect option(s) specified. Usage:\n%s\n'
               'For additional help run:\n  gsutil help %s' %
               (self.command_spec.usage_synopsis, self.command_name))
    raise CommandException(message)

  def ParseSubOpts(self,
                   check_args=False,
                   args=None,
                   should_update_sub_opts_and_args=True):
    """Parses sub-opt args.

    Args:
      check_args: True to have CheckArguments() called after parsing.
      args: List of args. If None, self.args will be used.
      should_update_sub_opts_and_args: True if self.sub_opts and self.args
        should be updated with the values returned after parsing. Else return a
        tuple of sub_opts, args returned by getopt.getopt. This is done
        to allow this method to be called from get_gcloud_storage_args in which
        case we do not want to update self.sub_opts and self.args.

    Raises:
      RaiseInvalidArgumentException: Invalid args specified.
    """
    if args is None:
      unparsed_args = self.args
    else:
      unparsed_args = args
    try:
      parsed_sub_opts, parsed_args = getopt.getopt(
          unparsed_args, self.command_spec.supported_sub_args,
          self.command_spec.supported_private_args or [])
    except getopt.GetoptError:
      self.RaiseInvalidArgumentException()
    if should_update_sub_opts_and_args:
      self.sub_opts, self.args = parsed_sub_opts, parsed_args
      if check_args:
        self.CheckArguments()
    else:
      if check_args:
        # This is just for sanity check. Only get_gcloud_storage_args will
        # call this method with should_update_sub_opts_and_args=False, and it
        # does not set check_args to True.
        raise TypeError('Requested to check arguments'
                        ' but sub_opts and args have not been updated.')
      return parsed_sub_opts, parsed_args

  def CheckArguments(self):
    """Checks that command line arguments match the command_spec.

    Any commands in self._commands_with_subcommands_and_subopts are responsible
    for calling this method after handling initial parsing of their arguments.
    This prevents commands with sub-commands as well as options from breaking
    the parsing of getopt.

    TODO: Provide a function to parse commands and sub-commands more
    intelligently once we stop allowing the deprecated command versions.

    Raises:
      CommandException if the arguments don't match.
    """

    if (not self.command_spec.file_url_ok and
        HaveFileUrls(self.args[self.command_spec.urls_start_arg:])):
      raise CommandException('"%s" command does not support "file://" URLs. '
                             'Did you mean to use a gs:// URL?' %
                             self.command_name)
    if (not self.command_spec.provider_url_ok and
        HaveProviderUrls(self.args[self.command_spec.urls_start_arg:])):
      raise CommandException('"%s" command does not support provider-only '
                             'URLs.' % self.command_name)

  def WildcardIterator(self, url_string, all_versions=False):
    """Helper to instantiate gslib.WildcardIterator.

    Args are same as gslib.WildcardIterator interface, but this method fills in
    most of the values from instance state.

    Args:
      url_string: URL string naming wildcard objects to iterate.
      all_versions: If true, the iterator yields all versions of objects
                    matching the wildcard.  If false, yields just the live
                    object version.

    Returns:
      WildcardIterator for use by caller.
    """
    return CreateWildcardIterator(url_string,
                                  self.gsutil_api,
                                  all_versions=all_versions,
                                  project_id=self.project_id,
                                  logger=self.logger)

  def GetSeekAheadGsutilApi(self):
    """Helper to instantiate a Cloud API instance for a seek-ahead iterator.

    This must be separate from the core command.gsutil_api instance for
    thread-safety, since other iterators typically use that instance and the
    SeekAheadIterator operates in parallel.

    Returns:
      Cloud API instance for use by the seek-ahead iterator.
    """
    # This is initialized in Initialize(Multiprocessing|Threading)Variables
    # pylint: disable=global-variable-not-assigned
    # pylint: disable=global-variable-undefined
    global glob_status_queue
    # pylint: enable=global-variable-not-assigned
    # pylint: enable=global-variable-undefined
    if not self.seek_ahead_gsutil_api:
      self.seek_ahead_gsutil_api = CloudApiDelegator(
          self.bucket_storage_uri_class,
          self.gsutil_api_map,
          logging.getLogger('dummy'),
          glob_status_queue,
          debug=self.debug,
          http_headers=self.non_metadata_headers,
          trace_token=self.trace_token,
          perf_trace_token=self.perf_trace_token,
          user_project=self.user_project)
    return self.seek_ahead_gsutil_api

  def RunCommand(self):
    """Abstract function in base class. Subclasses must implement this.

    The return value of this function will be used as the exit status of the
    process, so subclass commands should return an integer exit code (0 for
    success, a value in [1,255] for failure).
    """
    raise CommandException('Command %s is missing its RunCommand() '
                           'implementation' % self.command_name)

  ############################################################
  # Shared helper functions that depend on base class state. #
  ############################################################

  # TODO: Refactor ACL functions to a different module and pass the
  # command object as state, as opposed to defining them as member functions
  # of the command class.
  def ApplyAclFunc(self,
                   acl_func,
                   acl_excep_handler,
                   url_strs,
                   object_fields=None):
    """Sets the standard or default object ACL depending on self.command_name.

    Args:
      acl_func: ACL function to be passed to Apply.
      acl_excep_handler: ACL exception handler to be passed to Apply.
      url_strs: URL strings on which to set ACL.
      object_fields: If present, list of object metadata fields to retrieve;
          if None, default name expansion iterator fields will be used.

    Raises:
      CommandException if an ACL could not be set.
    """
    multi_threaded_url_args = []

    urls = list(map(StorageUrlFromString, url_strs))

    if (UrlsAreMixOfBucketsAndObjects(urls) and not self.recursion_requested):
      raise CommandException('Cannot operate on a mix of buckets and objects.')

    # Handle bucket ACL setting operations single-threaded, because
    # our threading machinery currently assumes it's working with objects
    # (name_expansion_iterator), and normally we wouldn't expect users to need
    # to set ACLs on huge numbers of buckets at once anyway.
    for url in urls:
      if url.IsCloudUrl() and url.IsBucket():
        if self.recursion_requested:
          # If user specified -R option, convert any bucket args to bucket
          # wildcards (e.g., gs://bucket/*), to prevent the operation from
          # being applied to the buckets themselves.
          url.object_name = '*'
          multi_threaded_url_args.append(url.url_string)
        else:
          # Convert to a NameExpansionResult so we can re-use the threaded
          # function for the single-threaded implementation.  RefType is unused.
          for blr in self.WildcardIterator(
              url.url_string).IterBuckets(bucket_fields=['id']):
            name_expansion_for_url = NameExpansionResult(
                source_storage_url=url,
                is_multi_source_request=False,
                is_multi_top_level_source_request=False,
                names_container=False,
                expanded_storage_url=blr.storage_url,
                expanded_result=None)
            acl_func(self, name_expansion_for_url)
      else:
        multi_threaded_url_args.append(url.url_string)

    if len(multi_threaded_url_args) >= 1:
      name_expansion_iterator = NameExpansionIterator(
          self.command_name,
          self.debug,
          self.logger,
          self.gsutil_api,
          multi_threaded_url_args,
          self.recursion_requested,
          all_versions=self.all_versions,
          continue_on_error=self.continue_on_error or self.parallel_operations,
          bucket_listing_fields=object_fields)

      seek_ahead_iterator = SeekAheadNameExpansionIterator(
          self.command_name,
          self.debug,
          self.GetSeekAheadGsutilApi(),
          multi_threaded_url_args,
          self.recursion_requested,
          all_versions=self.all_versions)

      # Perform requests in parallel (-m) mode, if requested, using
      # configured number of parallel processes and threads. Otherwise,
      # perform requests with sequential function calls in current process.
      self.Apply(acl_func,
                 name_expansion_iterator,
                 acl_excep_handler,
                 fail_on_error=not self.continue_on_error,
                 seek_ahead_iterator=seek_ahead_iterator)

    if not self.everything_set_okay and not self.continue_on_error:
      raise CommandException('ACLs for some objects could not be set.')

  def SetAclFunc(self, name_expansion_result, thread_state=None):
    """Sets the object ACL for the name_expansion_result provided.

    Args:
      name_expansion_result: NameExpansionResult describing the target object.
      thread_state: If present, use this gsutil Cloud API instance for the set.
    """
    if thread_state:
      assert not self.def_acl
      gsutil_api = thread_state
    else:
      gsutil_api = self.gsutil_api
    op_string = 'default object ACL' if self.def_acl else 'ACL'
    url = name_expansion_result.expanded_storage_url
    self.logger.info('Setting %s on %s...', op_string, url)
    if (gsutil_api.GetApiSelector(url.scheme) == ApiSelector.XML and
        url.scheme != 'gs'):
      # If we are called with a non-google ACL model, we need to use the XML
      # passthrough. acl_arg should either be a canned ACL or an XML ACL.
      self._SetAclXmlPassthrough(url, gsutil_api)
    else:
      # Normal Cloud API path. acl_arg is a JSON ACL or a canned ACL.
      self._SetAclGsutilApi(url, gsutil_api)
    PutToQueueWithTimeout(gsutil_api.status_queue,
                          MetadataMessage(message_time=time.time()))

  def _SetAclXmlPassthrough(self, url, gsutil_api):
    """Sets the ACL for the URL provided using the XML passthrough functions.

    This function assumes that self.def_acl, self.canned,
    and self.continue_on_error are initialized, and that self.acl_arg is
    either an XML string or a canned ACL string.

    Args:
      url: CloudURL to set the ACL on.
      gsutil_api: gsutil Cloud API to use for the ACL set. Must support XML
          passthrough functions.
    """
    orig_prefer_api = gsutil_api.prefer_api
    try:
      gsutil_api.prefer_api = ApiSelector.XML
      gsutil_api.XmlPassThroughSetAcl(self.acl_arg,
                                      url,
                                      canned=self.canned,
                                      def_obj_acl=self.def_acl,
                                      provider=url.scheme)
    except ServiceException as e:
      if self.continue_on_error:
        self.everything_set_okay = False
        self.logger.error(e)
      else:
        raise
    finally:
      gsutil_api.prefer_api = orig_prefer_api

  def _SetAclGsutilApi(self, url, gsutil_api):
    """Sets the ACL for the URL provided using the gsutil Cloud API.

    This function assumes that self.def_acl, self.canned,
    and self.continue_on_error are initialized, and that self.acl_arg is
    either a JSON string or a canned ACL string.

    Args:
      url: CloudURL to set the ACL on.
      gsutil_api: gsutil Cloud API to use for the ACL set.
    """
    try:
      if url.IsBucket():
        if self.def_acl:
          if self.canned:
            gsutil_api.PatchBucket(url.bucket_name,
                                   apitools_messages.Bucket(),
                                   canned_def_acl=self.acl_arg,
                                   provider=url.scheme,
                                   fields=['id'])
          else:
            def_obj_acl = AclTranslation.JsonToMessage(
                self.acl_arg, apitools_messages.ObjectAccessControl)
            if not def_obj_acl:
              # Use a sentinel value to indicate a private (no entries) default
              # object ACL.
              def_obj_acl.append(PRIVATE_DEFAULT_OBJ_ACL)
            bucket_metadata = apitools_messages.Bucket(
                defaultObjectAcl=def_obj_acl)
            gsutil_api.PatchBucket(url.bucket_name,
                                   bucket_metadata,
                                   provider=url.scheme,
                                   fields=['id'])
        else:
          if self.canned:
            gsutil_api.PatchBucket(url.bucket_name,
                                   apitools_messages.Bucket(),
                                   canned_acl=self.acl_arg,
                                   provider=url.scheme,
                                   fields=['id'])
          else:
            bucket_acl = AclTranslation.JsonToMessage(
                self.acl_arg, apitools_messages.BucketAccessControl)
            bucket_metadata = apitools_messages.Bucket(acl=bucket_acl)
            gsutil_api.PatchBucket(url.bucket_name,
                                   bucket_metadata,
                                   provider=url.scheme,
                                   fields=['id'])
      else:  # url.IsObject()
        if self.canned:
          gsutil_api.PatchObjectMetadata(url.bucket_name,
                                         url.object_name,
                                         apitools_messages.Object(),
                                         provider=url.scheme,
                                         generation=url.generation,
                                         canned_acl=self.acl_arg)
        else:
          object_acl = AclTranslation.JsonToMessage(
              self.acl_arg, apitools_messages.ObjectAccessControl)
          object_metadata = apitools_messages.Object(acl=object_acl)
          gsutil_api.PatchObjectMetadata(url.bucket_name,
                                         url.object_name,
                                         object_metadata,
                                         provider=url.scheme,
                                         generation=url.generation)
    except ArgumentException as e:
      raise
    except ServiceException as e:
      if self.continue_on_error:
        self.everything_set_okay = False
        self.logger.error(e)
      else:
        raise

  def SetAclCommandHelper(self, acl_func, acl_excep_handler):
    """Sets ACLs on the self.args using the passed-in acl function.

    Args:
      acl_func: ACL function to be passed to Apply.
      acl_excep_handler: ACL exception handler to be passed to Apply.
    """
    acl_arg = self.args[0]
    url_args = self.args[1:]
    # Disallow multi-provider setacl requests, because there are differences in
    # the ACL models.
    if not UrlsAreForSingleProvider(url_args):
      raise CommandException('"%s" command spanning providers not allowed.' %
                             self.command_name)

    # Determine whether acl_arg names a file containing XML ACL text vs. the
    # string name of a canned ACL.
    if os.path.isfile(acl_arg):
      with codecs.open(acl_arg, 'r', UTF8) as f:
        acl_arg = f.read()
      self.canned = False
    else:
      # No file exists, so expect a canned ACL string.
      # validate=False because we allow wildcard urls.
      storage_uri = boto.storage_uri(
          url_args[0],
          debug=self.debug,
          validate=False,
          bucket_storage_uri_class=self.bucket_storage_uri_class)

      canned_acls = storage_uri.canned_acls()
      if acl_arg not in canned_acls:
        raise CommandException('Invalid canned ACL "%s".' % acl_arg)
      self.canned = True

    # Used to track if any ACLs failed to be set.
    self.everything_set_okay = True
    self.acl_arg = acl_arg

    self.ApplyAclFunc(acl_func, acl_excep_handler, url_args)
    if not self.everything_set_okay and not self.continue_on_error:
      raise CommandException('ACLs for some objects could not be set.')

  def _WarnServiceAccounts(self):
    """Warns service account users who have received an AccessDenied error.

    When one of the metadata-related commands fails due to AccessDenied, user
    must ensure that they are listed as an Owner in the API console.
    """
    # Import this here so that the value will be set first in
    # gcs_oauth2_boto_plugin.
    # pylint: disable=g-import-not-at-top
    from gcs_oauth2_boto_plugin.oauth2_plugin import IS_SERVICE_ACCOUNT

    if IS_SERVICE_ACCOUNT:
      # This method is only called when canned ACLs are used, so the warning
      # definitely applies.
      self.logger.warning('\n'.join(
          textwrap.wrap(
              'It appears that your service account has been denied access while '
              'attempting to perform a metadata operation. If you believe that you '
              'should have access to this metadata (i.e., if it is associated with '
              'your account), please make sure that your service account'
              's email '
              'address is listed as an Owner in the Permissions tab of the API '
              'console. See "gsutil help creds" for further information.\n')))

  def GetAndPrintAcl(self, url_str):
    """Prints the standard or default object ACL depending on self.command_name.

    Args:
      url_str: URL string to get ACL for.
    """
    blr = self.GetAclCommandBucketListingReference(url_str)
    url = StorageUrlFromString(url_str)
    if (self.gsutil_api.GetApiSelector(url.scheme) == ApiSelector.XML and
        url.scheme != 'gs'):
      # Need to use XML passthrough.
      try:
        acl = self.gsutil_api.XmlPassThroughGetAcl(url,
                                                   def_obj_acl=self.def_acl,
                                                   provider=url.scheme)
        print(acl.to_xml())
      except AccessDeniedException as _:
        self._WarnServiceAccounts()
        raise
    else:
      if self.command_name == 'defacl':
        acl = blr.root_object.defaultObjectAcl
        if not acl:
          self.logger.warn(
              'No default object ACL present for %s. This could occur if '
              'the default object ACL is private, in which case objects '
              'created in this bucket will be readable only by their '
              'creators. It could also mean you do not have OWNER permission '
              'on %s and therefore do not have permission to read the '
              'default object ACL. It could also mean that %s has Bucket '
              'Policy Only enabled and therefore object ACLs and default '
              'object ACLs are disabled (see '
              'https://cloud.google.com/storage/docs/bucket-policy-only).',
              url_str, url_str, url_str)
      else:
        acl = blr.root_object.acl
        # Use the access controls api to check if the acl is actually empty or
        # if the user has 403 access denied or 400 invalid argument.
        if not acl:
          self._ListAccessControlsAcl(url)

      print(AclTranslation.JsonFromMessage(acl))

  def _ListAccessControlsAcl(self, storage_url):
    """Returns either bucket or object access controls for a storage url.

    Args:
      storage_url: StorageUrl object representing the bucket or object.

    Returns:
      BucketAccessControls, ObjectAccessControls, or None if storage_url does
      not represent a cloud bucket or cloud object.

    Raises:
      ServiceException if there was an error in the request.
    """
    if storage_url.IsBucket():
      return self.gsutil_api.ListBucketAccessControls(
          storage_url.bucket_name, provider=storage_url.scheme)
    elif storage_url.IsObject():
      return self.gsutil_api.ListObjectAccessControls(
          storage_url.bucket_name,
          storage_url.object_name,
          provider=storage_url.scheme)
    else:
      return None

  def GetAclCommandBucketListingReference(self, url_str):
    """Gets a single bucket listing reference for an acl get command.

    Args:
      url_str: URL string to get the bucket listing reference for.

    Returns:
      BucketListingReference for the URL string.

    Raises:
      CommandException if string did not result in exactly one reference.
    """
    # We're guaranteed by caller that we have the appropriate type of url
    # string for the call (ex. we will never be called with an object string
    # by getdefacl)
    wildcard_url = StorageUrlFromString(url_str)
    if wildcard_url.IsObject():
      plurality_iter = PluralityCheckableIterator(
          self.WildcardIterator(url_str).IterObjects(
              bucket_listing_fields=['acl']))
    else:
      # Bucket or provider.  We call IterBuckets explicitly here to ensure that
      # the root object is populated with the acl.
      if self.command_name == 'defacl':
        bucket_fields = ['defaultObjectAcl']
      else:
        bucket_fields = ['acl']
      plurality_iter = PluralityCheckableIterator(
          self.WildcardIterator(url_str).IterBuckets(
              bucket_fields=bucket_fields))
    if plurality_iter.IsEmpty():
      raise CommandException('No URLs matched')
    if plurality_iter.HasPlurality():
      raise CommandException(
          '%s matched more than one URL, which is not allowed by the %s '
          'command' % (url_str, self.command_name))
    return list(plurality_iter)[0]

  def GetSingleBucketUrlFromArg(self, arg, bucket_fields=None):
    """Gets a single bucket URL based on the command arguments.

    Args:
      arg: String argument to get bucket URL for.
      bucket_fields: Fields to populate for the bucket.

    Returns:
      (StorageUrl referring to a single bucket, Bucket metadata).

    Raises:
      CommandException if args did not match exactly one bucket.
    """
    plurality_checkable_iterator = self.GetBucketUrlIterFromArg(
        arg, bucket_fields=bucket_fields)
    if plurality_checkable_iterator.HasPlurality():
      raise CommandException('%s matched more than one URL, which is not\n'
                             'allowed by the %s command' %
                             (arg, self.command_name))
    blr = list(plurality_checkable_iterator)[0]
    return StorageUrlFromString(blr.url_string), blr.root_object

  def GetBucketUrlIterFromArg(self, arg, bucket_fields=None):
    """Gets a single bucket URL based on the command arguments.

    Args:
      arg: String argument to iterate over.
      bucket_fields: Fields to populate for the bucket.

    Returns:
      PluralityCheckableIterator over buckets.

    Raises:
      CommandException if iterator matched no buckets.
    """
    arg_url = StorageUrlFromString(arg)
    if not arg_url.IsCloudUrl() or arg_url.IsObject():
      raise CommandException('"%s" command must specify a bucket' %
                             self.command_name)

    plurality_checkable_iterator = PluralityCheckableIterator(
        self.WildcardIterator(arg).IterBuckets(bucket_fields=bucket_fields))
    if plurality_checkable_iterator.IsEmpty():
      raise CommandException('No URLs matched')
    return plurality_checkable_iterator

  ######################
  # Private functions. #
  ######################

  def _ResetConnectionPool(self):
    # Each OS process needs to establish its own set of connections to
    # the server to avoid writes from different OS processes interleaving
    # onto the same socket (and garbling the underlying SSL session).
    # We ensure each process gets its own set of connections here by
    # reinitializing state that tracks connections.
    connection_pool = StorageUri.provider_pool
    if connection_pool:
      for i in connection_pool:
        connection_pool[i].connection.close()

    StorageUri.provider_pool = {}
    StorageUri.connection = None

  def _GetProcessAndThreadCount(self,
                                process_count,
                                thread_count,
                                parallel_operations_override,
                                print_macos_warning=True):
    """Determines the values of process_count and thread_count.

    These values are used for parallel operations.
    If we're not performing operations in parallel, then ignore
    existing values and use process_count = thread_count = 1.

    Args:
      process_count: A positive integer or None. In the latter case, we read
                     the value from the .boto config file.
      thread_count: A positive integer or None. In the latter case, we read
                    the value from the .boto config file.
      parallel_operations_override: Used to override self.parallel_operations.
                                    This allows the caller to safely override
                                    the top-level flag for a single call.
      print_macos_warning: Print a warning about parallel processing on MacOS
                           if true.

    Returns:
      (process_count, thread_count): The number of processes and threads to use,
                                     respectively.
    """
    # Set OS process and python thread count as a function of options
    # and config.
    if self.parallel_operations or parallel_operations_override:
      if not process_count:
        process_count = boto.config.getint(
            'GSUtil', 'parallel_process_count',
            gslib.commands.config.DEFAULT_PARALLEL_PROCESS_COUNT)
      if process_count < 1:
        raise CommandException('Invalid parallel_process_count "%d".' %
                               process_count)
      if not thread_count:
        thread_count = boto.config.getint(
            'GSUtil', 'parallel_thread_count',
            gslib.commands.config.DEFAULT_PARALLEL_THREAD_COUNT)
      if thread_count < 1:
        raise CommandException('Invalid parallel_thread_count "%d".' %
                               thread_count)
    else:
      # If -m not specified, then assume 1 OS process and 1 Python thread.
      process_count = 1
      thread_count = 1

    should_prohibit_multiprocessing, os_name = ShouldProhibitMultiprocessing()
    if should_prohibit_multiprocessing and process_count > 1:
      raise CommandException('\n'.join(
          textwrap.wrap(
              ('It is not possible to set process_count > 1 on %s. Please '
               'update your config file(s) (located at %s) and set '
               '"parallel_process_count = 1".') %
              (os_name, ', '.join(GetFriendlyConfigFilePaths())))))
    is_main_thread = self.recursive_apply_level == 0
    if print_macos_warning and os_name == 'macOS' and process_count > 1 and is_main_thread:
      self.logger.info(
          'If you experience problems with multiprocessing on MacOS, they '
          'might be related to https://bugs.python.org/issue33725. You can '
          'disable multiprocessing by editing your .boto config or by adding '
          'the following flag to your command: '
          '`-o "GSUtil:parallel_process_count=1"`. Note that multithreading is '
          'still available even if you disable multiprocessing.\n')

    self.logger.debug('process count: %d', process_count)
    self.logger.debug('thread count: %d', thread_count)
    return (process_count, thread_count)

  def _SetUpPerCallerState(self):
    """Set up the state for a caller id, corresponding to one Apply call."""
    # pylint: disable=global-variable-undefined,global-variable-not-assigned
    # These variables are initialized in InitializeMultiprocessingVariables or
    # InitializeThreadingVariables
    global global_return_values_map, shared_vars_map, failure_count
    global caller_id_finished_count, shared_vars_list_map, total_tasks
    global need_pool_or_done_cond, call_completed_map, class_map
    global task_queues, caller_id_lock, caller_id_counter
    # Get a new caller ID.
    with caller_id_lock:
      caller_id_counter.Increment()
      caller_id = caller_id_counter.GetValue()

    # Create a copy of self with an incremented recursive level. This allows
    # the class to report its level correctly if the function called from it
    # also needs to call Apply.
    cls = copy.copy(self)
    cls.recursive_apply_level += 1

    # Thread-safe loggers can't be pickled, so we will remove it here and
    # recreate it later in the WorkerThread. This is not a problem since any
    # logger with the same name will be treated as a singleton.
    cls.logger = None

    # Likewise, the default API connection(s) can't be pickled, but are unused
    # anyway as each thread gets its own API delegator.
    cls.gsutil_api = None
    cls.seek_ahead_gsutil_api = None

    class_map[caller_id] = cls
    total_tasks[caller_id] = -1  # -1 => the producer hasn't finished yet.
    call_completed_map[caller_id] = False
    caller_id_finished_count[caller_id] = 0
    global_return_values_map[caller_id] = []
    return caller_id

  def _CreateNewConsumerPool(self, num_processes, num_threads, status_queue):
    """Create a new pool of processes that call _ApplyThreads."""
    processes = []
    task_queue = _NewMultiprocessingQueue()
    task_queues.append(task_queue)

    current_max_recursive_level.Increment()
    if current_max_recursive_level.GetValue() > MAX_RECURSIVE_DEPTH:
      raise CommandException('Recursion depth of Apply calls is too great.')
    for _ in range(num_processes):
      recursive_apply_level = len(consumer_pools)
      p = multiprocessing_context.Process(target=self._ApplyThreads,
                                          args=(num_threads, num_processes,
                                                recursive_apply_level,
                                                status_queue))
      p.daemon = True
      processes.append(p)
      _CryptoRandomAtFork()
      p.start()
    consumer_pool = _ConsumerPool(processes, task_queue)
    consumer_pools.append(consumer_pool)

  class ParallelOverrideReason(object):
    """Enum class to describe purpose of overriding parallel operations."""
    # For the case when we use slice parallelism.
    SLICE = 'slice'
    # For the case when we run a helper Apply call (such as in the _DiffIterator
    # of rsync) and override to make the command go faster.
    SPEED = 'speed'
    # For when we run Apply calls in perfdiag.
    PERFDIAG = 'perfdiag'

  def Apply(self,
            func,
            args_iterator,
            exception_handler,
            shared_attrs=None,
            arg_checker=_UrlArgChecker,
            parallel_operations_override=None,
            process_count=None,
            thread_count=None,
            should_return_results=False,
            fail_on_error=False,
            seek_ahead_iterator=None):
    """Calls _Parallel/SequentialApply based on multiprocessing availability.

    Args:
      func: Function to call to process each argument.
      args_iterator: Iterable collection of arguments to be put into the
                     work queue.
      exception_handler: Exception handler for WorkerThread class.
      shared_attrs: List of attributes to manage across sub-processes.
      arg_checker: Used to determine whether we should process the current
                   argument or simply skip it. Also handles any logging that
                   is specific to a particular type of argument.
      parallel_operations_override: A string (see ParallelOverrideReason)
                                    describing the reason to override
                                    self.parallel_operations. This allows the
                                    caller to safely override the top-level flag
                                    for a single call.
      process_count: The number of processes to use. If not specified, then
                     the configured default will be used.
      thread_count: The number of threads per process. If not specified, then
                    the configured default will be used..
      should_return_results: If true, then return the results of all successful
                             calls to func in a list.
      fail_on_error: If true, then raise any exceptions encountered when
                     executing func. This is only applicable in the case of
                     process_count == thread_count == 1.
      seek_ahead_iterator: If present, a seek-ahead iterator that will
          provide an approximation of the total number of tasks and bytes that
          will be iterated by the ProducerThread. Used only if multiple
          processes and/or threads are used.

    Returns:
      Results from spawned threads.
    """
    # This is initialized in Initialize(Multiprocessing|Threading)Variables
    # pylint: disable=global-variable-not-assigned
    # pylint: disable=global-variable-undefined
    global thread_stats
    # pylint: enable=global-variable-not-assigned
    # pylint: enable=global-variable-undefined
    if shared_attrs:
      original_shared_vars_values = {}  # We'll add these back in at the end.
      for name in shared_attrs:
        original_shared_vars_values[name] = getattr(self, name)
        # By setting this to 0, we simplify the logic for computing deltas.
        # We'll add it back after all of the tasks have been performed.
        setattr(self, name, 0)

    (process_count, thread_count) = self._GetProcessAndThreadCount(
        process_count, thread_count, parallel_operations_override)

    is_main_thread = (self.recursive_apply_level == 0 and
                      self.sequential_caller_id == -1)

    if is_main_thread:
      # This initializes the initial performance summary parameters.
      LogPerformanceSummaryParams(num_processes=process_count,
                                  num_threads=thread_count)

    # We don't honor the fail_on_error flag in the case of multiple threads
    # or processes.
    fail_on_error = fail_on_error and (process_count * thread_count == 1)

    # Only check this from the first call in the main thread. Apart from the
    # fact that it's  wasteful to try this multiple times in general, it also
    # will never work when called from a subprocess since we use daemon
    # processes, and daemons can't create other processes.
    if (is_main_thread and not self.multiprocessing_is_available and
        process_count > 1):
      # Run the check again and log the appropriate warnings. This was run
      # before, when the Command object was created, in order to calculate
      # self.multiprocessing_is_available, but we don't want to print the
      # warning until we're sure the user actually tried to use multiple
      # threads or processes.
      CheckMultiprocessingAvailableAndInit(logger=self.logger)

    caller_id = self._SetUpPerCallerState()

    # If any shared attributes passed by caller, create a dictionary of
    # shared memory variables for every element in the list of shared
    # attributes.
    if shared_attrs:
      shared_vars_list_map[caller_id] = shared_attrs
      for name in shared_attrs:
        shared_vars_map[(caller_id, name)] = 0

    # Make all of the requested function calls.
    usable_processes_count = (process_count
                              if self.multiprocessing_is_available else 1)
    if thread_count * usable_processes_count > 1:
      self._ParallelApply(
          func,
          args_iterator,
          exception_handler,
          caller_id,
          arg_checker,
          usable_processes_count,
          thread_count,
          should_return_results,
          fail_on_error,
          seek_ahead_iterator=seek_ahead_iterator,
          parallel_operations_override=parallel_operations_override)
      if is_main_thread:
        _AggregateThreadStats()
    else:
      self._SequentialApply(func, args_iterator, exception_handler, caller_id,
                            arg_checker, should_return_results, fail_on_error)

    if shared_attrs:
      for name in shared_attrs:
        # This allows us to retain the original value of the shared variable,
        # and simply apply the delta after what was done during the call to
        # apply.
        final_value = (original_shared_vars_values[name] + shared_vars_map.get(
            (caller_id, name)))
        setattr(self, name, final_value)

    if should_return_results:
      return global_return_values_map.get(caller_id)

  def _MaybeSuggestGsutilDashM(self):
    """Outputs a suggestion to the user to use gsutil -m."""
    if not (boto.config.getint('GSUtil', 'parallel_process_count', 0) == 1 and
            boto.config.getint('GSUtil', 'parallel_thread_count', 0) == 1):
      self.logger.info('\n' + textwrap.fill(
          '==> NOTE: You are performing a sequence of gsutil operations that '
          'may run significantly faster if you instead use gsutil -m %s ...\n'
          'Please see the -m section under "gsutil help options" for further '
          'information about when gsutil -m can be advantageous.' %
          self.command_spec.command_name) + '\n')

  # pylint: disable=g-doc-args
  def _SequentialApply(self, func, args_iterator, exception_handler, caller_id,
                       arg_checker, should_return_results, fail_on_error):
    """Performs all function calls sequentially in the current thread.

    No other threads or processes will be spawned. This degraded functionality
    is used when the multiprocessing module is not available or the user
    requests only one thread and one process.
    """
    # Create a WorkerThread to handle all of the logic needed to actually call
    # the function. Note that this thread will never be started, and all work
    # is done in the current thread.
    worker_thread = WorkerThread(None,
                                 False,
                                 headers=self.non_metadata_headers,
                                 perf_trace_token=self.perf_trace_token,
                                 trace_token=self.trace_token,
                                 user_project=self.user_project)
    args_iterator = iter(args_iterator)
    # Count of sequential calls that have been made. Used for producing
    # suggestion to use gsutil -m.
    sequential_call_count = 0
    while True:

      # Try to get the next argument, handling any exceptions that arise.
      try:
        args = next(args_iterator)
      except StopIteration as e:
        break
      except Exception as e:  # pylint: disable=broad-except
        _IncrementFailureCount()
        if fail_on_error:
          raise
        else:
          try:
            exception_handler(self, e)
          except Exception as _:  # pylint: disable=broad-except
            self.logger.debug(
                'Caught exception while handling exception for %s:\n%s', func,
                traceback.format_exc())
          continue

      sequential_call_count += 1
      if (sequential_call_count == OFFER_GSUTIL_M_SUGGESTION_THRESHOLD or
          sequential_call_count % OFFER_GSUTIL_M_SUGGESTION_FREQUENCY == 0):
        # Output suggestion near beginning of run, so user sees it early, and
        # every so often while the command is executing, so they can ^C and try
        # gsutil -m.
        self._MaybeSuggestGsutilDashM()
      if arg_checker(self, args):
        # Now that we actually have the next argument, perform the task.
        task = Task(func, args, caller_id, exception_handler,
                    should_return_results, arg_checker, fail_on_error)
        worker_thread.PerformTask(task, self)

    lines_since_suggestion_last_printed = (sequential_call_count %
                                           OFFER_GSUTIL_M_SUGGESTION_FREQUENCY)
    if lines_since_suggestion_last_printed >= GetTermLines():
      # Output suggestion at end of long run, in case user missed it at the
      # start and it scrolled off-screen.
      self._MaybeSuggestGsutilDashM()

    PutToQueueWithTimeout(self.gsutil_api.status_queue,
                          FinalMessage(time.time()))

    # If the final iterated argument results in an exception, and that
    # exception modifies shared_attrs, we need to publish the results.
    worker_thread.shared_vars_updater.Update(caller_id, self)

    # Now that all the work is done, log the types of source URLs encountered.
    self._ProcessSourceUrlTypes(args_iterator)

  # pylint: disable=g-doc-args
  def _ParallelApply(self,
                     func,
                     args_iterator,
                     exception_handler,
                     caller_id,
                     arg_checker,
                     process_count,
                     thread_count,
                     should_return_results,
                     fail_on_error,
                     seek_ahead_iterator=None,
                     parallel_operations_override=None):
    r"""Dispatches input arguments across a thread/process pool.

    Pools are composed of parallel OS processes and/or Python threads,
    based on options (-m or not) and settings in the user's config file.

    If only one OS process is requested/available, dispatch requests across
    threads in the current OS process.

    In the multi-process case, we will create one pool of worker processes for
    each level of the tree of recursive calls to Apply. E.g., if A calls
    Apply(B), and B ultimately calls Apply(C) followed by Apply(D), then we
    will only create two sets of worker processes - B will execute in the first,
    and C and D will execute in the second. If C is then changed to call
    Apply(E) and D is changed to call Apply(F), then we will automatically
    create a third set of processes (lazily, when needed) that will be used to
    execute calls to E and F. This might look something like:

    Pool1 Executes:                B
                                  / \
    Pool2 Executes:              C   D
                                /     \
    Pool3 Executes:            E       F

    Apply's parallelism is generally broken up into 4 cases:
    - If process_count == thread_count == 1, then all tasks will be executed
      by _SequentialApply.
    - If process_count > 1 and thread_count == 1, then the main thread will
      create a new pool of processes (if they don't already exist) and each of
      those processes will execute the tasks in a single thread.
    - If process_count == 1 and thread_count > 1, then this process will create
      a new pool of threads to execute the tasks.
    - If process_count > 1 and thread_count > 1, then the main thread will
      create a new pool of processes (if they don't already exist) and each of
      those processes will, upon creation, create a pool of threads to
      execute the tasks.

    Args:
      caller_id: The caller ID unique to this call to command.Apply.
      See command.Apply for description of other arguments.
    """
    # This is initialized in Initialize(Multiprocessing|Threading)Variables
    # pylint: disable=global-variable-not-assigned
    # pylint: disable=global-variable-undefined
    global glob_status_queue, ui_controller
    # pylint: enable=global-variable-not-assigned
    # pylint: enable=global-variable-undefined
    is_main_thread = self.recursive_apply_level == 0

    if (parallel_operations_override == self.ParallelOverrideReason.SLICE and
        self.recursive_apply_level <= 1):
      # The operation uses slice parallelism if the recursive apply level > 0 or
      # if we're executing _ParallelApply without the -m option.
      glob_status_queue.put(PerformanceSummaryMessage(time.time(), True))

    if not IS_WINDOWS and is_main_thread:
      # For multi-thread or multi-process scenarios, the main process must
      # kill itself on a terminating signal, because sys.exit(1) only exits
      # the currently executing thread, leaving orphaned processes. The main
      # thread is responsible for cleaning up multiprocessing variables such
      # as manager processes. Therefore, the main thread's signal handling
      # chain is:
      # 1: __main__._CleanupSignalHandler (clean up processes)
      # 2: MultithreadedSignalHandler (kill self)
      for signal_num in (signal.SIGINT, signal.SIGTERM):
        RegisterSignalHandler(signal_num,
                              MultithreadedMainSignalHandler,
                              is_final_handler=True)

    if not task_queues:
      # The process we create will need to access the next recursive level
      # of task queues if it makes a call to Apply, so we always keep around
      # one more queue than we know we need. OTOH, if we don't create a new
      # process, the existing process still needs a task queue to use.
      if process_count > 1:
        task_queues.append(_NewMultiprocessingQueue())
      else:
        task_queue = _NewThreadsafeQueue()
        task_queues.append(task_queue)
        # Create a top-level worker pool since this is the first execution
        # of ParallelApply on the main thread.
        WorkerPool(thread_count,
                   self.logger,
                   task_queue=task_queue,
                   bucket_storage_uri_class=self.bucket_storage_uri_class,
                   gsutil_api_map=self.gsutil_api_map,
                   debug=self.debug,
                   status_queue=glob_status_queue,
                   headers=self.non_metadata_headers,
                   perf_trace_token=self.perf_trace_token,
                   trace_token=self.trace_token,
                   user_project=self.user_project)

    if process_count > 1:  # Handle process pool creation.
      # Check whether this call will need a new set of workers.

      # Each worker must acquire a shared lock before notifying the main thread
      # that it needs a new worker pool, so that at most one worker asks for
      # a new worker pool at once.
      try:
        if not is_main_thread:
          worker_checking_level_lock.acquire()
        if self.recursive_apply_level >= current_max_recursive_level.GetValue():
          with need_pool_or_done_cond:
            # Only the main thread is allowed to create new processes -
            # otherwise, we will run into some Python bugs.
            if is_main_thread:
              self._CreateNewConsumerPool(process_count, thread_count,
                                          glob_status_queue)
            else:
              # Notify the main thread that we need a new consumer pool.
              new_pool_needed.Reset(reset_value=1)
              need_pool_or_done_cond.notify_all()
              # The main thread will notify us when it finishes.
              need_pool_or_done_cond.wait()
      finally:
        if not is_main_thread:
          worker_checking_level_lock.release()
    else:  # Handle new worker thread pool creation.
      if not is_main_thread:
        try:
          worker_checking_level_lock.acquire()
          if self.recursive_apply_level > _GetCurrentMaxRecursiveLevel():
            # We don't have a thread pool for this level of recursive apply
            # calls, so create a pool and corresponding task queue.
            _IncrementCurrentMaxRecursiveLevel()
            task_queue = _NewThreadsafeQueue()
            task_queues.append(task_queue)
            WorkerPool(thread_count,
                       self.logger,
                       task_queue=task_queue,
                       bucket_storage_uri_class=self.bucket_storage_uri_class,
                       gsutil_api_map=self.gsutil_api_map,
                       debug=self.debug,
                       status_queue=glob_status_queue,
                       headers=self.non_metadata_headers,
                       perf_trace_token=self.perf_trace_token,
                       trace_token=self.trace_token,
                       user_project=self.user_project)
        finally:
          worker_checking_level_lock.release()

    task_queue = task_queues[self.recursive_apply_level]

    # Only use the seek-ahead iterator in the main thread to provide an
    # overall estimate of operations.
    if seek_ahead_iterator and not is_main_thread:
      seek_ahead_iterator = None

    # Kick off a producer thread to throw tasks in the global task queue. We
    # do this asynchronously so that the main thread can be free to create new
    # consumer pools when needed (otherwise, any thread with a task that needs
    # a new consumer pool must block until we're completely done producing; in
    # the worst case, every worker blocks on such a call and the producer fills
    # up the task queue before it finishes, so we block forever).
    producer_thread = ProducerThread(
        copy.copy(self),
        args_iterator,
        caller_id,
        func,
        task_queue,
        should_return_results,
        exception_handler,
        arg_checker,
        fail_on_error,
        seek_ahead_iterator=seek_ahead_iterator,
        status_queue=(glob_status_queue if is_main_thread else None))

    # Start the UI thread that is responsible for displaying operation status
    # (aggregated across processes and threads) to the user.
    ui_thread = None
    if is_main_thread:
      ui_thread = UIThread(glob_status_queue, sys.stderr, ui_controller)

    # Wait here until either:
    #   1. We're the main thread in the multi-process case, and someone needs
    #      a new consumer pool - in which case we create one and continue
    #      waiting.
    #   2. Someone notifies us that all of the work we requested is done, in
    #      which case we retrieve the results (if applicable) and stop
    #      waiting.
    # At most one of these can be true, because the main thread is blocked on
    # its call to Apply, and a thread will not ask for a new consumer pool
    # unless it had more work to do.
    while True:
      with need_pool_or_done_cond:
        if call_completed_map[caller_id]:
          break
        elif (process_count > 1 and is_main_thread and
              new_pool_needed.GetValue()):
          new_pool_needed.Reset()
          self._CreateNewConsumerPool(process_count, thread_count,
                                      glob_status_queue)
          need_pool_or_done_cond.notify_all()

        # Note that we must check the above conditions before the wait() call;
        # otherwise, the notification can happen before we start waiting, in
        # which case we'll block forever.
        need_pool_or_done_cond.wait()

    # We've completed all tasks (or excepted), so signal the UI thread to
    # terminate.
    if is_main_thread:
      PutToQueueWithTimeout(glob_status_queue, ZERO_TASKS_TO_DO_ARGUMENT)
      ui_thread.join(timeout=UI_THREAD_JOIN_TIMEOUT)
      # Now that all the work is done, log the types of source URLs encountered.
      self._ProcessSourceUrlTypes(producer_thread.args_iterator)

    # We encountered an exception from the producer thread before any arguments
    # were enqueued, but it wouldn't have been propagated, so we'll now
    # explicitly raise it here.
    if producer_thread.unknown_exception:
      # pylint: disable=raising-bad-type
      raise producer_thread.unknown_exception

    # We encountered an exception from the producer thread while iterating over
    # the arguments, so raise it here if we're meant to fail on error.
    if producer_thread.iterator_exception and fail_on_error:
      # pylint: disable=raising-bad-type
      raise producer_thread.iterator_exception
    if is_main_thread and not parallel_operations_override:
      PutToQueueWithTimeout(glob_status_queue, FinalMessage(time.time()))

  def _ProcessSourceUrlTypes(self, args_iterator):
    """Logs the URL type information to analytics collection."""
    if not isinstance(args_iterator, CopyObjectsIterator):
      return
    LogPerformanceSummaryParams(is_daisy_chain=args_iterator.is_daisy_chain,
                                has_file_src=args_iterator.has_file_src,
                                has_cloud_src=args_iterator.has_cloud_src,
                                provider_types=args_iterator.provider_types)

  def _ApplyThreads(self, thread_count, process_count, recursive_apply_level,
                    status_queue):
    """Assigns the work from the multi-process global task queue.

    Work is assigned to an individual process for later consumption either by
    the WorkerThreads or (if thread_count == 1) this thread.

    Args:
      thread_count: The number of threads used to perform the work. If 1, then
                    perform all work in this thread.
      process_count: The number of processes used to perform the work.
      recursive_apply_level: The depth in the tree of recursive calls to Apply
                             of this thread.
      status_queue: Multiprocessing/threading queue for progress reporting and
          performance aggregation.
    """
    assert process_count > 1, (
        'Invalid state, calling command._ApplyThreads with only one process.')

    _CryptoRandomAtFork()
    # Separate processes should exit on a terminating signal,
    # but to avoid race conditions only the main process should handle
    # multiprocessing cleanup. Override child processes to use a single signal
    # handler.
    for catch_signal in GetCaughtSignals():
      signal.signal(catch_signal, ChildProcessSignalHandler)

    self._ResetConnectionPool()
    self.recursive_apply_level = recursive_apply_level

    task_queue = task_queues[recursive_apply_level]

    # Ensure fairness across processes by filling our WorkerPool
    # only with as many tasks as it has WorkerThreads. This semaphore is
    # acquired each time that a task is retrieved from the queue and released
    # each time a task is completed by a WorkerThread.
    worker_semaphore = threading.BoundedSemaphore(thread_count)

    # TODO: Presently, this pool gets recreated with each call to Apply. We
    # should be able to do it just once, at process creation time.
    worker_pool = WorkerPool(
        thread_count,
        self.logger,
        worker_semaphore=worker_semaphore,
        bucket_storage_uri_class=self.bucket_storage_uri_class,
        gsutil_api_map=self.gsutil_api_map,
        debug=self.debug,
        status_queue=status_queue,
        headers=self.non_metadata_headers,
        perf_trace_token=self.perf_trace_token,
        trace_token=self.trace_token,
        user_project=self.user_project)

    num_enqueued = 0
    while True:
      while not worker_semaphore.acquire(blocking=False):
        # Because Python signal handlers are only called in between atomic
        # instructions, if we block the main thread on an available worker
        # thread, we won't be able to respond to signals such as a
        # user-initiated CTRL-C until a worker thread completes a task.
        # We poll the semaphore periodically as a compromise between
        # efficiency and user responsiveness.
        time.sleep(0.01)
      task = task_queue.get()

      if task.args != ZERO_TASKS_TO_DO_ARGUMENT:
        # If we have no tasks to do and we're performing a blocking call, we
        # need a special signal to tell us to stop - otherwise, we block on
        # the call to task_queue.get() forever.
        worker_pool.AddTask(task)
        num_enqueued += 1
      else:
        # No tasks remain; since no work was dispatched to a thread, don't
        # block the semaphore on a WorkerThread completion.
        worker_semaphore.release()


# Below here lie classes and functions related to controlling the flow of tasks
# between various threads and processes.
class _ConsumerPool(object):

  def __init__(self, processes, task_queue):
    self.processes = processes
    self.task_queue = task_queue

  def ShutDown(self):
    for process in self.processes:
      KillProcess(process.pid)


class Task(
    namedtuple('Task', (
        'func args caller_id exception_handler should_return_results arg_checker '
        'fail_on_error'))):
  """Task class representing work to be completed.

  Args:
    func: The function to be executed.
    args: The arguments to func.
    caller_id: The globally-unique caller ID corresponding to the Apply call.
    exception_handler: The exception handler to use if the call to func fails.
    should_return_results: True iff the results of this function should be
                           returned from the Apply call.
    arg_checker: Used to determine whether we should process the current
                 argument or simply skip it. Also handles any logging that
                 is specific to a particular type of argument.
    fail_on_error: If true, then raise any exceptions encountered when
                   executing func. This is only applicable in the case of
                   process_count == thread_count == 1.
  """
  pass


# TODO: Refactor the various threading code that doesn't need to depend on
# command.py globals (ProducerThread, UIThread) to different files to aid
# readability and reduce the size of command.py.
def _StartSeekAheadThread(seek_ahead_iterator, seek_ahead_thread_cancel_event):
  """Initializes and runs the seek-ahead thread.

  We defer starting this thread until it is needed, since it is only useful
  when the ProducerThread iterates more results than it can store on the global
  task queue.

  Args:
    seek_ahead_iterator: Iterator that yields SeekAheadResults.
    seek_ahead_thread_cancel_event: threading.Event for signaling the
        seek-ahead thread to terminate.

  Returns:
    The thread object for the initialized thread.
  """
  # This is initialized in Initialize(Multiprocessing|Threading)Variables
  # pylint: disable=global-variable-not-assigned
  # pylint: disable=global-variable-undefined
  global glob_status_queue
  # pylint: enable=global-variable-not-assigned
  # pylint: enable=global-variable-undefined
  return SeekAheadThread(seek_ahead_iterator, seek_ahead_thread_cancel_event,
                         glob_status_queue)


class ProducerThread(threading.Thread):
  """Thread used to enqueue work for other processes and threads."""

  def __init__(self,
               cls,
               args_iterator,
               caller_id,
               func,
               task_queue,
               should_return_results,
               exception_handler,
               arg_checker,
               fail_on_error,
               seek_ahead_iterator=None,
               status_queue=None):
    """Initializes the producer thread.

    Args:
      cls: Instance of Command for which this ProducerThread was created.
      args_iterator: Iterable collection of arguments to be put into the
                     work queue.
      caller_id: Globally-unique caller ID corresponding to this call to Apply.
      func: The function to be called on each element of args_iterator.
      task_queue: The queue into which tasks will be put, to later be consumed
                  by Command._ApplyThreads.
      should_return_results: True iff the results for this call to command.Apply
                             were requested.
      exception_handler: The exception handler to use when errors are
                         encountered during calls to func.
      arg_checker: Used to determine whether we should process the current
                   argument or simply skip it. Also handles any logging that
                   is specific to a particular type of argument.
      fail_on_error: If true, then raise any exceptions encountered when
                     executing func. This is only applicable in the case of
                     process_count == thread_count == 1.
      seek_ahead_iterator: If present, a seek-ahead iterator that will
          provide an approximation of the total number of tasks and bytes that
          will be iterated by the ProducerThread.
      status_queue: status_queue to inform task_queue estimation. Only
          valid when calling from the main thread, else None. Even if this is
          the main thread, the status_queue will only properly work if args
          is a collection of NameExpansionResults, which is the type that gives
          us initial information about files to be processed. Otherwise,
          nothing will be added to the queue.
    """
    super(ProducerThread, self).__init__()
    self.func = func
    self.cls = cls
    self.args_iterator = args_iterator
    self.caller_id = caller_id
    self.task_queue = task_queue
    self.arg_checker = arg_checker
    self.exception_handler = exception_handler
    self.should_return_results = should_return_results
    self.fail_on_error = fail_on_error
    self.shared_variables_updater = _SharedVariablesUpdater()
    self.daemon = True
    self.unknown_exception = None
    self.iterator_exception = None
    self.seek_ahead_iterator = seek_ahead_iterator
    self.status_queue = status_queue
    self.start()

  def run(self):
    num_tasks = 0
    cur_task = None
    last_task = None
    task_estimation_threshold = None
    seek_ahead_thread = None
    seek_ahead_thread_cancel_event = None
    seek_ahead_thread_considered = False
    args = None
    try:
      total_size = 0
      self.args_iterator = iter(self.args_iterator)
      while True:
        try:
          args = next(self.args_iterator)
        except StopIteration as e:
          break
        except Exception as e:  # pylint: disable=broad-except
          _IncrementFailureCount()
          if self.fail_on_error:
            self.iterator_exception = e
            raise
          else:
            try:
              self.exception_handler(self.cls, e)
            except Exception as _:  # pylint: disable=broad-except
              self.cls.logger.debug(
                  'Caught exception while handling exception for %s:\n%s',
                  self.func, traceback.format_exc())
            self.shared_variables_updater.Update(self.caller_id, self.cls)
            continue

        if self.arg_checker(self.cls, args):
          num_tasks += 1
          if self.status_queue:
            if not num_tasks % 100:
              # Time to update the total number of tasks.
              if (isinstance(args, NameExpansionResult) or
                  isinstance(args, CopyObjectInfo) or
                  isinstance(args, RsyncDiffToApply)):
                PutToQueueWithTimeout(
                    self.status_queue,
                    ProducerThreadMessage(num_tasks, total_size, time.time()))
            if (isinstance(args, NameExpansionResult) or
                isinstance(args, CopyObjectInfo)):
              if args.expanded_result:
                json_expanded_result = json.loads(args.expanded_result)
                if 'size' in json_expanded_result:
                  total_size += int(json_expanded_result['size'])
            elif isinstance(args, RsyncDiffToApply):
              if args.copy_size:
                total_size += int(args.copy_size)

          if not seek_ahead_thread_considered:
            if task_estimation_threshold is None:
              task_estimation_threshold = _GetTaskEstimationThreshold()
            if task_estimation_threshold <= 0:
              # Disable the seek-ahead thread (never start it).
              seek_ahead_thread_considered = True
            elif num_tasks >= task_estimation_threshold:
              if self.seek_ahead_iterator:
                seek_ahead_thread_cancel_event = threading.Event()
                seek_ahead_thread = _StartSeekAheadThread(
                    self.seek_ahead_iterator, seek_ahead_thread_cancel_event)
                # For integration testing only, force estimation to complete
                # prior to producing further results.
                if boto.config.get('GSUtil', 'task_estimation_force', None):
                  seek_ahead_thread.join(timeout=SEEK_AHEAD_JOIN_TIMEOUT)

              seek_ahead_thread_considered = True

          last_task = cur_task
          cur_task = Task(self.func, args, self.caller_id,
                          self.exception_handler, self.should_return_results,
                          self.arg_checker, self.fail_on_error)
          if last_task:
            self.task_queue.put(last_task)
    except Exception as e:  # pylint: disable=broad-except
      # This will also catch any exception raised due to an error in the
      # iterator when fail_on_error is set, so check that we failed for some
      # other reason before claiming that we had an unknown exception.
      if not self.iterator_exception:
        self.unknown_exception = e
    finally:
      # We need to make sure to update total_tasks[caller_id] before we enqueue
      # the last task. Otherwise, a worker can retrieve the last task and
      # complete it, then check total_tasks and determine that we're not done
      # producing all before we update total_tasks. This approach forces workers
      # to wait on the last task until after we've updated total_tasks.
      total_tasks[self.caller_id] = num_tasks
      if not cur_task:
        # This happens if there were zero arguments to be put in the queue.
        cur_task = Task(None, ZERO_TASKS_TO_DO_ARGUMENT, self.caller_id, None,
                        None, None, None)
      self.task_queue.put(cur_task)

      # If the seek ahead thread is still running, cancel it and wait for it
      # to exit since we've enumerated all of the tasks already. We don't want
      # to delay command completion on an estimate that has become meaningless.
      if seek_ahead_thread is not None:
        seek_ahead_thread_cancel_event.set()
        # It's possible that the seek-ahead-thread may attempt to put to the
        # status queue after it has been torn down, for example if the system
        # is overloaded. Because the put uses a timeout, it should never block
        # command termination or signal handling.
        seek_ahead_thread.join(timeout=SEEK_AHEAD_JOIN_TIMEOUT)
      # Send a final ProducerThread message that definitively states
      # the amount of actual work performed.
      if (self.status_queue and
          (isinstance(args, NameExpansionResult) or isinstance(
              args, CopyObjectInfo) or isinstance(args, RsyncDiffToApply))):
        PutToQueueWithTimeout(
            self.status_queue,
            ProducerThreadMessage(num_tasks,
                                  total_size,
                                  time.time(),
                                  finished=True))

      # It's possible that the workers finished before we updated total_tasks,
      # so we need to check here as well.
      _NotifyIfDone(self.caller_id,
                    caller_id_finished_count.get(self.caller_id))


class WorkerPool(object):
  """Pool of worker threads to which tasks can be added."""

  def __init__(self,
               thread_count,
               logger,
               worker_semaphore=None,
               task_queue=None,
               bucket_storage_uri_class=None,
               gsutil_api_map=None,
               debug=0,
               status_queue=None,
               headers=None,
               perf_trace_token=None,
               trace_token=None,
               user_project=None):
    # In the multi-process case, a worker sempahore is required to ensure
    # even work distribution.
    #
    # In the single process case, the input task queue directly feeds worker
    # threads from the ProducerThread. Since worker threads will consume only
    # one task at a time from the queue, there is no need for a semaphore to
    # ensure even work distribution.
    #
    # Thus, exactly one of task_queue or worker_semaphore must be provided.
    assert (worker_semaphore is None) != (task_queue is None)
    self.headers = headers
    self.perf_trace_token = perf_trace_token
    self.trace_token = trace_token
    self.user_project = user_project

    self.task_queue = task_queue or _NewThreadsafeQueue()
    self.threads = []
    for _ in range(thread_count):
      worker_thread = WorkerThread(
          self.task_queue,
          logger,
          worker_semaphore=worker_semaphore,
          bucket_storage_uri_class=bucket_storage_uri_class,
          gsutil_api_map=gsutil_api_map,
          debug=debug,
          status_queue=status_queue,
          headers=self.headers,
          perf_trace_token=self.perf_trace_token,
          trace_token=self.trace_token,
          user_project=self.user_project)
      self.threads.append(worker_thread)
      worker_thread.start()

  def AddTask(self, task):
    """Adds a task to the task queue; used only in the multi-process case."""
    self.task_queue.put(task)


class WorkerThread(threading.Thread):
  """Thread where all the work will be performed.

  This makes the function calls for Apply and takes care of all error handling,
  return value propagation, and shared_vars.

  Note that this thread is NOT started upon instantiation because the function-
  calling logic is also used in the single-threaded case.
  """
  # This is initialized in Initialize(Multiprocessing|Threading)Variables
  # pylint: disable=global-variable-not-assigned
  # pylint: disable=global-variable-undefined
  global thread_stats

  # pylint: enable=global-variable-not-assigned
  # pylint: enable=global-variable-undefined

  def __init__(self,
               task_queue,
               logger,
               worker_semaphore=None,
               bucket_storage_uri_class=None,
               gsutil_api_map=None,
               debug=0,
               status_queue=None,
               headers=None,
               perf_trace_token=None,
               trace_token=None,
               user_project=None):
    """Initializes the worker thread.

    Args:
      task_queue: The thread-safe queue from which this thread should obtain
                  its work.
      logger: Logger to use for this thread.
      worker_semaphore: threading.BoundedSemaphore to be released each time a
          task is completed, or None for single-threaded execution.
      bucket_storage_uri_class: Class to instantiate for cloud StorageUris.
                                Settable for testing/mocking.
      gsutil_api_map: Map of providers and API selector tuples to api classes
                      which can be used to communicate with those providers.
                      Used for the instantiating CloudApiDelegator class.
      debug: debug level for the CloudApiDelegator class.
      status_queue: Queue for reporting status updates.
      user_project: Project to be billed for this request.
    """
    super(WorkerThread, self).__init__()

    self.pid = os.getpid()
    self.init_time = time.time()
    self.task_queue = task_queue
    self.worker_semaphore = worker_semaphore
    self.daemon = True
    self.cached_classes = {}
    self.shared_vars_updater = _SharedVariablesUpdater()
    self.headers = headers
    self.perf_trace_token = perf_trace_token
    self.trace_token = trace_token
    self.user_project = user_project

    # Note that thread_gsutil_api is not initialized in the sequential
    # case; task functions should use utils.cloud_api_helper.GetCloudApiInstance
    # to retrieve the main thread's CloudApiDelegator in that case.
    self.thread_gsutil_api = None
    if bucket_storage_uri_class and gsutil_api_map:
      self.thread_gsutil_api = CloudApiDelegator(
          bucket_storage_uri_class,
          gsutil_api_map,
          logger,
          status_queue,
          debug=debug,
          http_headers=self.headers,
          perf_trace_token=self.perf_trace_token,
          trace_token=self.trace_token,
          user_project=self.user_project)

  @CaptureThreadStatException
  def _StartBlockedTime(self):
    """Update the thread_stats AtomicDict before task_queue.get() is called."""
    if thread_stats.get((self.pid, self.ident)) is None:
      thread_stats[(self.pid, self.ident)] = _ThreadStat(self.init_time)
    # While this read/modify/write is not an atomic operation on the dict,
    # we are protected since the (process ID, thread ID) tuple is unique
    # to this thread, making this thread the only reader/writer for this key.
    thread_stat = thread_stats[(self.pid, self.ident)]
    thread_stat.StartBlockedTime()
    thread_stats[(self.pid, self.ident)] = thread_stat

  @CaptureThreadStatException
  def _EndBlockedTime(self):
    """Update the thread_stats AtomicDict after task_queue.get() is called."""
    thread_stat = thread_stats[(self.pid, self.ident)]
    thread_stat.EndBlockedTime()
    thread_stats[(self.pid, self.ident)] = thread_stat

  def PerformTask(self, task, cls):
    """Makes the function call for a task.

    Args:
      task: The Task to perform.
      cls: The instance of a class which gives context to the functions called
           by the Task's function. E.g., see SetAclFuncWrapper.
    """
    caller_id = task.caller_id
    try:
      results = task.func(cls, task.args, thread_state=self.thread_gsutil_api)
      if task.should_return_results:
        global_return_values_map.Increment(caller_id, [results],
                                           default_value=[])
    except Exception as e:  # pylint: disable=broad-except
      _IncrementFailureCount()
      if task.fail_on_error:
        raise  # Only happens for single thread and process case.
      else:
        try:
          task.exception_handler(cls, e)
        except Exception as _:  # pylint: disable=broad-except
          # Don't allow callers to raise exceptions here and kill the worker
          # threads.
          cls.logger.debug(
              'Caught exception while handling exception for %s:\n%s', task,
              traceback.format_exc())
    finally:
      if self.worker_semaphore:
        self.worker_semaphore.release()
      self.shared_vars_updater.Update(caller_id, cls)

      # Even if we encounter an exception, we still need to claim that that
      # the function finished executing. Otherwise, we won't know when to
      # stop waiting and return results.
      num_done = caller_id_finished_count.Increment(caller_id, 1)
      _NotifyIfDone(caller_id, num_done)

  def run(self):
    while True:
      self._StartBlockedTime()
      task = self.task_queue.get()
      self._EndBlockedTime()
      if task.args == ZERO_TASKS_TO_DO_ARGUMENT:
        # This can happen in the single-process case because worker threads
        # consume ProducerThread tasks directly.
        continue
      caller_id = task.caller_id

      # Get the instance of the command with the appropriate context.
      cls = self.cached_classes.get(caller_id, None)
      if not cls:
        cls = copy.copy(class_map[caller_id])
        cls.logger = CreateOrGetGsutilLogger(cls.command_name)
        self.cached_classes[caller_id] = cls

      self.PerformTask(task, cls)


class _ThreadStat(object):
  """Stores thread idle and execution time statistics."""

  def __init__(self, init_time):
    self.total_idle_time = 0
    # The last time EndBlockedTime was called, which is the last time a
    # task_queue.get() completed or when we initialized the thread.
    self.end_block_time = init_time
    # The last time StartBlockedTime was called, which is the last time a
    # task_queue.get() call started.
    self.start_block_time = time.time()
    # Between now and thread initialization, we were not blocked.
    self.total_execution_time = 0

  def StartBlockedTime(self):
    self.start_block_time = time.time()
    exec_time = self.start_block_time - self.end_block_time
    self.total_execution_time += exec_time

  def EndBlockedTime(self):
    self.end_block_time = time.time()
    idle_time = self.end_block_time - self.start_block_time
    self.total_idle_time += idle_time

  def AggregateStat(self, end_time):
    """Decide final stats upon Apply completion."""
    if self.end_block_time > self.start_block_time:
      # Apply ended before we blocked on task_queue.get(), or there was an
      # exception during StartBlockedTime. In both of these cases, we were not
      # blocked on task_queue.get() and so can add this time to execution time.
      self.total_execution_time += end_time - self.end_block_time
    else:
      # Apply ended while we were blocked on task_queue.get(), or there was an
      # exception during EndBlockedTime. In both of these cases, we were in the
      # midst of or just finishing a task_queue.get() call, and so can add this
      # time to idle time.
      self.total_idle_time += end_time - self.start_block_time


def _AggregateThreadStats():
  """At the end of the top-level Apply call, aggregate the thread stats dict.

  This should only be called in the main process and thread because it logs to
  the MetricsCollector.
  """
  cur_time = time.time()
  total_idle_time = total_execution_time = 0
  for thread_stat in thread_stats.values():
    thread_stat.AggregateStat(cur_time)
    total_idle_time += thread_stat.total_idle_time
    total_execution_time += thread_stat.total_execution_time
  LogPerformanceSummaryParams(thread_idle_time=total_idle_time,
                              thread_execution_time=total_execution_time)


class _SharedVariablesUpdater(object):
  """Used to update shared variable for a class in the global map.

     Note that each thread will have its own instance of the calling class for
     context, and it will also have its own instance of a
     _SharedVariablesUpdater.  This is used in the following way:

     1. Before any tasks are performed, each thread will get a copy of the
        calling class, and the globally-consistent value of this shared variable
        will be initialized to whatever it was before the call to Apply began.

     2. After each time a thread performs a task, it will look at the current
        values of the shared variables in its instance of the calling class.

        2.A. For each such variable, it computes the delta of this variable
             between the last known value for this class (which is stored in
             a dict local to this class) and the current value of the variable
             in the class.

        2.B. Using this delta, we update the last known value locally as well
             as the globally-consistent value shared across all classes (the
             globally consistent value is simply increased by the computed
             delta).
  """

  def __init__(self):
    self.last_shared_var_values = {}

  def Update(self, caller_id, cls):
    """Update any shared variables with their deltas."""
    shared_vars = shared_vars_list_map.get(caller_id, None)
    if shared_vars:
      for name in shared_vars:
        key = (caller_id, name)
        last_value = self.last_shared_var_values.get(key, 0)
        # Compute the change made since the last time we updated here. This is
        # calculated by simply subtracting the last known value from the current
        # value in the class instance.
        delta = getattr(cls, name) - last_value
        self.last_shared_var_values[key] = delta + last_value

        # Update the globally-consistent value by simply increasing it by the
        # computed delta.
        shared_vars_map.Increment(key, delta)


def _NotifyIfDone(caller_id, num_done):
  """Notify any threads waiting for results that something has finished.

  Each waiting thread will then need to check the call_completed_map to see if
  its work is done.

  Note that num_done could be calculated here, but it is passed in as an
  optimization so that we have one less call to a globally-locked data
  structure.

  Args:
    caller_id: The caller_id of the function whose progress we're checking.
    num_done: The number of tasks currently completed for that caller_id.
  """
  num_to_do = total_tasks[caller_id]
  if num_to_do == num_done and num_to_do >= 0:
    # Notify the Apply call that's sleeping that it's ready to return.
    with need_pool_or_done_cond:
      call_completed_map[caller_id] = True
      need_pool_or_done_cond.notify_all()


# pylint: disable=global-variable-not-assigned,global-variable-undefined
def ShutDownGsutil():
  """Shut down all processes in consumer pools in preparation for exiting."""
  global glob_status_queue
  for q in queues:
    try:
      q.cancel_join_thread()
    except:  # pylint: disable=bare-except
      pass
  for consumer_pool in consumer_pools:
    consumer_pool.ShutDown()
  try:
    glob_status_queue.cancel_join_thread()
  except:  # pylint: disable=bare-except
    pass


def _GetCurrentMaxRecursiveLevel():
  global current_max_recursive_level
  return current_max_recursive_level.GetValue()


def _IncrementCurrentMaxRecursiveLevel():
  global current_max_recursive_level
  current_max_recursive_level.Increment()


def _IncrementFailureCount():
  global failure_count
  failure_count.Increment()


def DecrementFailureCount():
  global failure_count
  failure_count.Decrement()


def GetFailureCount():
  """Returns the number of failures processed during calls to Apply()."""
  global failure_count
  return failure_count.GetValue()


def ResetFailureCount():
  """Resets the failure_count variable to 0 - useful if error is expected."""
  global failure_count
  failure_count.Reset()
