# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Implements parallel task execution for the storage surface.

See go/parallel-processing-in-gcloud-storage for more information.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import functools
import multiprocessing
import sys
import threading

from googlecloudsdk.api_lib.storage.gcs_json import patch_apitools_messages
from googlecloudsdk.command_lib import crash_handling
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage.tasks import task
from googlecloudsdk.command_lib.storage.tasks import task_buffer
from googlecloudsdk.command_lib.storage.tasks import task_graph as task_graph_module
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import transport
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import creds_context_managers
from googlecloudsdk.core.util import platforms
from six.moves import queue


# TODO(b/171296237): Remove this when fixes are submitted in apitools.
patch_apitools_messages.patch()


if sys.version_info.major == 2:
  # multiprocessing.get_context is only available in Python 3. We don't support
  # Python 2, but some of our code still runs at import in Python 2 tests, so
  # we need to provide a value here.
  multiprocessing_context = multiprocessing

else:
  _should_force_spawn = (
      # On MacOS, fork is unsafe: https://bugs.python.org/issue33725. The
      # default start method is spawn on versions >= 3.8, but we need to set it
      # explicitly for older versions.
      platforms.OperatingSystem.Current() is platforms.OperatingSystem.MACOSX or
      # On Linux, fork causes issues when mTLS is enabled: go/ecp-gcloud-storage
      # The default start method on Linux is fork, hence we will set it to spawn
      # when client certificate authentication (mTLS) is enabled.
      (properties.VALUES.context_aware.use_client_certificate.GetBool() and
       platforms.OperatingSystem.Current() is platforms.OperatingSystem.LINUX)
  )

  if _should_force_spawn:
    multiprocessing_context = multiprocessing.get_context(method='spawn')
  else:
    # Uses platform default.
    multiprocessing_context = multiprocessing.get_context()


_TASK_QUEUE_LOCK = threading.Lock()


# TODO(b/203819260): Check if this lock can be removed on Windows, since message
# patches are applied above.
@contextlib.contextmanager
def _task_queue_lock():
  """Context manager which acquires a lock when queue.get is unsafe.

  On Python 3.5 with spawn enabled, a race condition affects unpickling
  objects in queue.get calls. This manifests as an AttributeError intermittently
  thrown by ForkingPickler.loads, e.g.:

  AttributeError: Can't get attribute 'FileDownloadTask' on <module
  'googlecloudsdk.command_lib.storage.tasks.cp.file_download_task' from
  'googlecloudsdk/command_lib/storage/tasks/cp/file_download_task.py'

  Adding a lock around queue.get calls using this context manager resolves the
  issue.

  Yields:
    None, but acquires a lock which is released on exit.
  """
  get_is_unsafe = (
      sys.version_info.major == 3 and sys.version_info.minor <= 5
      and multiprocessing_context.get_start_method() == 'spawn'
  )

  try:
    if get_is_unsafe:
      _TASK_QUEUE_LOCK.acquire()
    yield
  finally:
    if get_is_unsafe:
      _TASK_QUEUE_LOCK.release()


# When threads get this value, they should prepare to exit.
#
# Threads should check for this value with `==` and not `is`, since the pickling
# carried out by multiprocessing.Queue may cause `is` to incorrectly return
# False.
#
# When the executor is shutting down, this value is added to
# TaskGraphExecutor._executable_tasks and is passed to
# TaskGraphExecutor._task_queue.
_SHUTDOWN = 'SHUTDOWN'

_CREATE_WORKER_PROCESS = 'CREATE_WORKER_PROCESS'


class SharedProcessContext:
  """Context manager used to collect and set global state."""

  def __init__(self):
    """Collects global state in the main process."""
    if multiprocessing_context.get_start_method() == 'fork':
      return

    self._environment_variables = execution_utils.GetToolEnv()
    self._creds_context_manager = (
        creds_context_managers.CredentialProvidersManager())
    self._key_store = encryption_util._key_store
    self._invocation_id = transport.INVOCATION_ID

  def __enter__(self):
    """Sets global state in child processes."""
    if multiprocessing_context.get_start_method() == 'fork':
      return

    self._environment_context_manager = execution_utils.ReplaceEnv(
        **self._environment_variables)

    self._environment_context_manager.__enter__()
    self._creds_context_manager.__enter__()
    encryption_util._key_store = self._key_store
    transport.INVOCATION_ID = self._invocation_id

    # Passing None causes log settings to be refreshed based on property values.
    log.SetUserOutputEnabled(None)
    log.SetVerbosity(None)

  def __exit__(self, exc_type, exc_value, exc_traceback):
    """Cleans up global state in child processes."""
    if multiprocessing_context.get_start_method() == 'fork':
      return

    self._environment_context_manager.__exit__(
        exc_type, exc_value, exc_traceback)
    self._creds_context_manager.__exit__(exc_type, exc_value, exc_traceback)


@crash_handling.CrashManager
def _thread_worker(task_queue, task_output_queue, task_status_queue,
                   idle_thread_count):
  """A consumer thread run in a child process.

  Args:
    task_queue (multiprocessing.Queue): Holds task_graph.TaskWrapper instances.
    task_output_queue (multiprocessing.Queue): Sends information about completed
      tasks back to the main process.
    task_status_queue (multiprocessing.Queue|None): Used by task to report it
      progress to a central location.
    idle_thread_count (multiprocessing.Semaphore): Keeps track of how many
      threads are busy. Useful for spawning new workers if all threads are busy.
  """
  while True:
    with _task_queue_lock():
      task_wrapper = task_queue.get()
    if task_wrapper == _SHUTDOWN:
      break
    idle_thread_count.acquire()

    task_execution_error = None
    try:
      task_output = task_wrapper.task.execute(
          task_status_queue=task_status_queue)
    # pylint: disable=broad-except
    # If any exception is raised, it will prevent the executor from exiting.
    except Exception as exception:
      task_execution_error = exception
      log.error(exception)
      log.debug(exception, exc_info=sys.exc_info())

      if isinstance(exception, errors.FatalError):
        task_output = task.Output(
            additional_task_iterators=None,
            messages=[task.Message(topic=task.Topic.FATAL_ERROR, payload={})])
      elif task_wrapper.task.change_exit_code:
        task_output = task.Output(
            additional_task_iterators=None,
            messages=[
                task.Message(topic=task.Topic.CHANGE_EXIT_CODE, payload={})
            ])
      else:
        task_output = None
    # pylint: enable=broad-except
    finally:
      task_wrapper.task.exit_handler(task_execution_error, task_status_queue)

    task_output_queue.put((task_wrapper, task_output))
    idle_thread_count.release()


@crash_handling.CrashManager
def _process_worker(task_queue, task_output_queue, task_status_queue,
                    thread_count, idle_thread_count, shared_process_context):
  """Starts a consumer thread pool.

  Args:
    task_queue (multiprocessing.Queue): Holds task_graph.TaskWrapper instances.
    task_output_queue (multiprocessing.Queue): Sends information about completed
      tasks back to the main process.
    task_status_queue (multiprocessing.Queue|None): Used by task to report it
      progress to a central location.
    thread_count (int): Number of threads the process should spawn.
    idle_thread_count (multiprocessing.Semaphore): Passed on to worker threads.
    shared_process_context (SharedProcessContext): Holds values from global
      state that need to be replicated in child processes.
  """
  threads = []
  with shared_process_context:
    for _ in range(thread_count):
      thread = threading.Thread(
          target=_thread_worker,
          args=(task_queue, task_output_queue, task_status_queue,
                idle_thread_count))
      thread.start()
      threads.append(thread)

    for thread in threads:
      thread.join()


@crash_handling.CrashManager
def _process_factory(task_queue, task_output_queue, task_status_queue,
                     thread_count, idle_thread_count, signal_queue,
                     shared_process_context):
  """Create worker processes.

  This factory must run in a separate process to avoid deadlock issue,
  see go/gcloud-storage-deadlock-issue/. Although we are adding one
  extra process by doing this, it will remain idle once all the child worker
  processes are created. Thus, it does not add noticable burden on the system.

  Args:
    task_queue (multiprocessing.Queue): Holds task_graph.TaskWrapper instances.
    task_output_queue (multiprocessing.Queue): Sends information about completed
      tasks back to the main process.
    task_status_queue (multiprocessing.Queue|None): Used by task to report it
      progress to a central location.
    thread_count (int): Number of threads the process should spawn.
    idle_thread_count (multiprocessing.Semaphore): Passed on to worker threads.
    signal_queue (multiprocessing.Queue): Queue used by parent process to
      signal when a new child worker process must be created.
    shared_process_context (SharedProcessContext): Holds values from global
      state that need to be replicated in child processes.
  """
  processes = []
  while True:
    # We receive one signal message for each process to be created.
    signal = signal_queue.get()
    if signal == _SHUTDOWN:
      for _ in processes:
        for _ in range(thread_count):
          task_queue.put(_SHUTDOWN)
      break
    elif signal == _CREATE_WORKER_PROCESS:
      for _ in range(thread_count):
        idle_thread_count.release()

      process = multiprocessing_context.Process(
          target=_process_worker,
          args=(task_queue, task_output_queue, task_status_queue,
                thread_count, idle_thread_count, shared_process_context))
      processes.append(process)
      log.debug('Adding 1 process with {} threads.'
                ' Total processes: {}. Total threads: {}.'.format(
                    thread_count, len(processes),
                    len(processes) * thread_count))
      process.start()
    else:
      raise errors.Error('Received invalid signal for worker '
                         'process creation: {}'.format(signal))

  for process in processes:
    process.join()


def _store_exception(target_function):
  """Decorator for storing exceptions raised from the thread targets.

  Args:
    target_function (function): Thread target to decorate.

  Returns:
    Decorator function.
  """
  @functools.wraps(target_function)
  def wrapper(self, *args, **kwargs):
    try:
      target_function(self, *args, **kwargs)
      # pylint:disable=broad-except
    except Exception as e:
      # pylint:enable=broad-except
      if not isinstance(self, TaskGraphExecutor):
        # Storing of exception is only allowed for TaskGraphExecutor.
        raise
      with self.thread_exception_lock:
        if self.thread_exception is None:
          log.debug('Storing error to raise later: %s', e)
          self.thread_exception = e
        else:
          # This indicates that the exception has been already stored for
          # another thread. We will simply log the traceback in this
          # case, since raising the error is not going to be handled by the
          # main thread anyway.
          log.error(e)
          log.debug(e, exc_info=sys.exc_info())
  return wrapper


class TaskGraphExecutor:
  """Executes an iterable of command_lib.storage.tasks.task.Task instances."""

  def __init__(self,
               task_iterator,
               max_process_count=multiprocessing.cpu_count(),
               thread_count=4,
               task_status_queue=None,
               progress_manager_args=None):
    """Initializes a TaskGraphExecutor instance.

    No threads or processes are started by the constructor.

    Args:
      task_iterator (Iterable[command_lib.storage.tasks.task.Task]): Task
        instances to execute.
      max_process_count (int): The number of processes to start.
      thread_count (int): The number of threads to start per process.
      task_status_queue (multiprocessing.Queue|None): Used by task to report its
        progress to a central location.
      progress_manager_args (task_status.ProgressManagerArgs|None):
        Determines what type of progress indicator to display.
    """
    self._task_iterator = iter(task_iterator)
    self._max_process_count = max_process_count
    self._thread_count = thread_count
    self._task_status_queue = task_status_queue
    self._progress_manager_args = progress_manager_args

    self._process_count = 0
    self._idle_thread_count = multiprocessing_context.Semaphore(value=0)

    self._worker_count = self._max_process_count * self._thread_count

    # Sends task_graph.TaskWrapper instances to child processes.
    # Size must be 1. go/lazy-process-spawning-addendum.
    self._task_queue = multiprocessing_context.Queue(maxsize=1)

    # Sends information about completed tasks to the main process.
    self._task_output_queue = multiprocessing_context.Queue(
        maxsize=self._worker_count)

    # Queue for informing worker_process_creator to create a new process.
    self._signal_queue = multiprocessing_context.Queue(
        maxsize=self._worker_count + 1)

    # Tracks dependencies between tasks in the executor to help ensure that
    # tasks returned by executed tasks are completed in the correct order.
    self._task_graph = task_graph_module.TaskGraph(
        top_level_task_limit=2 * self._worker_count)

    # Holds tasks without any dependencies.
    self._executable_tasks = task_buffer.TaskBuffer()

    # For storing exceptions.
    self.thread_exception = None
    self.thread_exception_lock = threading.Lock()

    self._accepting_new_tasks = True
    self._exit_code = 0

  def _add_worker_process(self):
    """Signal the worker process spawner to create a new process."""
    self._signal_queue.put(_CREATE_WORKER_PROCESS)
    self._process_count += 1

  @_store_exception
  def _get_tasks_from_iterator(self):
    """Adds tasks from self._task_iterator to the executor.

    This involves adding tasks to self._task_graph, marking them as submitted,
    and adding them to self._executable_tasks.
    """

    while self._accepting_new_tasks:
      try:
        task_object = next(self._task_iterator)
      except StopIteration:
        break
      task_wrapper = self._task_graph.add(task_object)
      if task_wrapper is None:
        # self._task_graph rejected the task.
        continue
      task_wrapper.is_submitted = True
      # Tasks from task_iterator should have a lower priority than tasks that
      # are spawned by other tasks. This helps keep memory usage under control
      # when a workload's task graph has a large branching factor.
      self._executable_tasks.put(task_wrapper, prioritize=False)

  @_store_exception
  def _add_executable_tasks_to_queue(self):
    """Sends executable tasks to consumer threads in child processes."""
    task_wrapper = None
    while True:
      if task_wrapper is None:
        task_wrapper = self._executable_tasks.get()
        if task_wrapper == _SHUTDOWN:
          break

      reached_process_limit = self._process_count >= self._max_process_count

      try:
        self._task_queue.put(task_wrapper, block=reached_process_limit)
        task_wrapper = None
      except queue.Full:
        if self._idle_thread_count.acquire(block=False):
          # Idle worker will take a task. Restore semaphore count.
          self._idle_thread_count.release()
        else:
          self._add_worker_process()

  @_store_exception
  def _handle_task_output(self):
    """Updates a dependency graph based on information from executed tasks."""
    while True:
      output = self._task_output_queue.get()
      if output == _SHUTDOWN:
        break

      executed_task_wrapper, task_output = output
      if task_output and task_output.messages:
        for message in task_output.messages:
          if message.topic in (task.Topic.CHANGE_EXIT_CODE,
                               task.Topic.FATAL_ERROR):
            self._exit_code = 1
            if message.topic == task.Topic.FATAL_ERROR:
              self._accepting_new_tasks = False

      submittable_tasks = self._task_graph.update_from_executed_task(
          executed_task_wrapper, task_output)

      for task_wrapper in submittable_tasks:
        task_wrapper.is_submitted = True
        self._executable_tasks.put(task_wrapper)

  @contextlib.contextmanager
  def _get_worker_process_spawner(self, shared_process_context):
    """Creates a worker process spawner.

    Must be used as a context manager since the worker process spawner must be
    non-daemonic in order to start child processes, but non-daemonic child
    processes block parent processes from exiting, so if there are any failures
    after the worker process spawner is started, gcloud storage will fail to
    exit, unless we put the shutdown logic in a `finally` block.

    Args:
      shared_process_context (SharedProcessContext): Holds values from global
        state that need to be replicated in child processes.

    Yields:
      None, allows body of a `with` statement to execute.
    """
    worker_process_spawner = multiprocessing_context.Process(
        target=_process_factory,
        args=(
            self._task_queue,
            self._task_output_queue,
            self._task_status_queue,
            self._thread_count,
            self._idle_thread_count,
            self._signal_queue,
            shared_process_context,
        ),
    )
    try:
      worker_process_spawner.start()
      yield
    finally:
      # Shutdown all the workers.
      self._signal_queue.put(_SHUTDOWN)
      worker_process_spawner.join()

  def run(self):
    """Executes tasks from a task iterator in parallel.

    Returns:
      An integer indicating the exit code. Zero indicates no fatal errors were
        raised.
    """
    shared_process_context = SharedProcessContext()
    with self._get_worker_process_spawner(shared_process_context):
      # It is now safe to start the progress_manager thread, since new processes
      # are started by a child process.
      with task_status.progress_manager(
          self._task_status_queue, self._progress_manager_args
      ):
        self._add_worker_process()

        get_tasks_from_iterator_thread = threading.Thread(
            target=self._get_tasks_from_iterator
        )
        add_executable_tasks_to_queue_thread = threading.Thread(
            target=self._add_executable_tasks_to_queue
        )
        handle_task_output_thread = threading.Thread(
            target=self._handle_task_output
        )

        get_tasks_from_iterator_thread.start()
        add_executable_tasks_to_queue_thread.start()
        handle_task_output_thread.start()

        get_tasks_from_iterator_thread.join()
        try:
          self._task_graph.is_empty.wait()
        except console_io.OperationCancelledError:
          # If user hits ctrl-c, there will be no thread to pop tasks from the
          # graph. Python garbage collection will remove unstarted tasks in the
          # graph if we skip this endless wait.
          pass

        self._executable_tasks.put(_SHUTDOWN)
        self._task_output_queue.put(_SHUTDOWN)

        handle_task_output_thread.join()
        add_executable_tasks_to_queue_thread.join()

    # Queue close calls need to be outside the worker process spawner context
    # manager since the task queue need to be open for the shutdown logic.
    self._task_queue.close()
    self._task_output_queue.close()

    with self.thread_exception_lock:
      if self.thread_exception:
        raise self.thread_exception  # pylint: disable=raising-bad-type

    return self._exit_code
