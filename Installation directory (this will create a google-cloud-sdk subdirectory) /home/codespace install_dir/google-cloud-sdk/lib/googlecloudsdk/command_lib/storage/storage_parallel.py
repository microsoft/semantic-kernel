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
"""Utilities for parallelizing Cloud Storage file operations.

Example usage (for simplicity, use absolute *nix-style paths; in practice you'll
want to use os.path.join and friends):

>>> upload_tasks = [
...     FileUploadTask('/tmp/file1.txt', 'gs://my-bucket',
...                    'path/to/remote1.txt'),
...     FileUploadTask('/tmp/file2.txt', 'gs://my-bucket', '/remote2.txt')
... ]
>>> UploadFiles(upload_tasks, num_threads=16)

This will block until all files are uploaded, using 16 threads (but just the
current process). Afterwards, there will be objects at
'gs://my-bucket/path/to/remote1.txt' and 'gs://my-bucket/remote2.txt'.

>>> delete_tasks = [
...     ObjectDeleteTask('gs://my-bucket', 'path/to/remote1.txt'),
...     ObjectDeleteTask('gs://my-bucket', '/remote2.txt')
... ]
>>> DeleteObjects(delete_tasks, num_threads=16)

This removes the objects uploaded in the last code snippet.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import parallel
from googlecloudsdk.core.util import retry
from googlecloudsdk.core.util import text

import six


# This default value has been chosen after lots of experimentation.
DEFAULT_NUM_THREADS = 16


class Task(six.with_metaclass(abc.ABCMeta)):
  """Base clase for a storage tasks that can be parallelized."""

  @abc.abstractmethod
  def Execute(self, callback=None):
    pass


class FileUploadTask(Task):
  """Self-contained representation of a file to upload and its destination.

  Attributes:
    source_local_path: str, The local filesystem path of the source file to
      upload.
    dest_obj_ref: storage_util.ObjectReference, The object the file will be
      copied to.
  """

  def __init__(self, source_local_path, dest_obj_ref):
    self.source_local_path = source_local_path
    self.dest_obj_ref = dest_obj_ref

  def __str__(self):
    return 'Upload: {} --> {}'.format(
        self.source_local_path, self.dest_obj_ref.ToUrl())

  def __repr__(self):
    return (
        'FileUploadTask(source_path={source_path}, dest_path={dest_path})'
        .format(source_path=self.source_local_path,
                dest_path=self.dest_obj_ref.ToUrl()))

  def __hash__(self):
    return hash((self.source_local_path, self.dest_obj_ref))

  def Execute(self, callback=None):
    storage_client = storage_api.StorageClient()
    retry.Retryer(max_retrials=3).RetryOnException(
        storage_client.CopyFileToGCS,
        args=(self.source_local_path, self.dest_obj_ref))
    if callback:
      callback()


class FileDownloadTask(Task):
  """Self-contained representation of a file to download and its destination.

  Attributes:
    source_obj_ref: storage_util.ObjectReference, The object reference of the
      file to download.
    dest_local_path: str, The local filesystem path to write the file to.
  """

  def __init__(self, source_obj_ref, dest_local_path):
    self.source_obj_ref = source_obj_ref
    self.dest_local_path = dest_local_path

  def __str__(self):
    return 'Download: {} --> {}'.format(
        self.source_obj_ref.ToUrl(), self.dest_local_path)

  def __repr__(self):
    return (
        'FileDownloadTask(source_path={source_path}, dest_path={dest_path})'
        .format(source_path=self.source_obj_ref.ToUrl(),
                dest_path=self.dest_local_path))

  def __hash__(self):
    return hash((self.source_obj_ref, self.dest_local_path))

  def Execute(self, callback=None):
    storage_client = storage_api.StorageClient()
    retry.Retryer(max_retrials=3).RetryOnException(
        storage_client.CopyFileFromGCS,
        args=(self.source_obj_ref, self.dest_local_path))
    if callback:
      callback()


class FileRemoteCopyTask(Task):
  """Self-contained representation of a copy between GCS objects.

  Attributes:
    source_obj_ref: storage_util.ObjectReference, The object reference of the
      file to download.
    dest_obj_ref: storage_util.ObjectReference, The object reference to write
      the file to.
  """

  def __init__(self, source_obj_ref, dest_obj_ref):
    self.source_obj_ref = source_obj_ref
    self.dest_obj_ref = dest_obj_ref

  def __str__(self):
    return 'Copy: {} --> {}'.format(
        self.source_obj_ref.ToUrl(), self.dest_obj_ref.ToUrl())

  def __repr__(self):
    return (
        'FileRemoteCopyTask(source_path={source_path}, dest_path={dest_path})'
        .format(source_path=self.source_obj_ref.ToUrl(),
                dest_path=self.dest_obj_ref.ToUrl()))

  def __hash__(self):
    return hash((self.source_obj_ref, self.dest_obj_ref))

  def Execute(self, callback=None):
    storage_client = storage_api.StorageClient()
    retry.Retryer(max_retrials=3).RetryOnException(
        storage_client.Copy,
        args=(self.source_obj_ref, self.dest_obj_ref))
    if callback:
      callback()


class ObjectDeleteTask(Task):
  """Self-contained representation of an object to delete.

  Attributes:
    obj_ref: storage_util.ObjectReference, The object to delete.
  """

  def __init__(self, obj_ref):
    self.obj_ref = obj_ref

  def __str__(self):
    return 'Delete: {}'.format(self.obj_ref.ToUrl())

  def __repr__(self):
    return 'ObjectDeleteTask(object={obj}'.format(obj=self.obj_ref.ToUrl())

  def __hash__(self):
    return hash(self.obj_ref)

  def Execute(self, callback=None):
    """Complete one ObjectDeleteTask (safe to run in parallel)."""
    storage_client = storage_api.StorageClient()
    retry.Retryer(max_retrials=3).RetryOnException(
        storage_client.DeleteObject, args=(self.obj_ref,))
    if callback:
      callback()


def ExecuteTasks(tasks, num_threads=DEFAULT_NUM_THREADS,
                 progress_bar_label=None):
  """Perform the given storage tasks in parallel.

  Factors out common work: logging, setting up parallelism, managing a progress
  bar (if necessary).

  Args:
    tasks: [Operation], To be executed in parallel.
    num_threads: int, The number of threads to use
    progress_bar_label: str, If set, a progress bar will be shown with this
      label. Otherwise, no progress bar is displayed.
  """
  log.debug(progress_bar_label)
  log.debug('Using [%d] threads', num_threads)

  pool = parallel.GetPool(num_threads)
  if progress_bar_label:
    progress_bar = console_io.TickableProgressBar(
        len(tasks), progress_bar_label)
    callback = progress_bar.Tick
  else:
    progress_bar = console_io.NoOpProgressBar()
    callback = None

  if num_threads == 0:
    with progress_bar:
      for t in tasks:
        t.Execute(callback)
  else:
    with progress_bar, pool:
      pool.Map(lambda task: task.Execute(callback), tasks)


def UploadFiles(files_to_upload, num_threads=DEFAULT_NUM_THREADS,
                show_progress_bar=False):
  """Upload the given files to the given Cloud Storage URLs.

  Uses the appropriate parallelism (multi-process, multi-thread, both, or
  synchronous).

  Args:
    files_to_upload: list of FileUploadTask
    num_threads: int (optional), the number of threads to use.
    show_progress_bar: bool. If true, show a progress bar to the users when
      uploading files.
  """
  num_files = len(files_to_upload)
  if show_progress_bar:
    label = 'Uploading {} {} to Google Cloud Storage'.format(
        num_files, text.Pluralize(num_files, 'file'))
  else:
    label = None
  ExecuteTasks(files_to_upload, num_threads, label)


def DeleteObjects(objects_to_delete, num_threads=DEFAULT_NUM_THREADS,
                  show_progress_bar=False):
  """Delete the given Cloud Storage objects.

  Uses the appropriate parallelism (multi-process, multi-thread, both, or
  synchronous).

  Args:
    objects_to_delete: list of ObjectDeleteTask
    num_threads: int (optional), the number of threads to use.
    show_progress_bar: bool. If true, show a progress bar to the users when
      deleting files.
  """
  num_objects = len(objects_to_delete)
  if show_progress_bar:
    label = 'Deleting {} {} from Google Cloud Storage'.format(
        num_objects, text.Pluralize(num_objects, 'object'))
  else:
    label = None
  ExecuteTasks(objects_to_delete, num_threads, label)
