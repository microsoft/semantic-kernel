#!/usr/bin/env python
"""Provides Logic for Fetching and Storing Discovery Documents from an on-disc cache."""

import errno
import os
import shutil
import tempfile
from typing import Optional
from absl import logging
from pyglib import stringutil

_DISCOVERY_CACHE_FILE = 'api_discovery.json'


def get_from_cache(
    cache_root: str, api_name: str, api_version: str
) -> Optional[str]:
  """Loads a discovery document from the on-disc cache using key `api` and `version`.

  Args:
    cache_root: [str], a directory where all cache files are stored.
    api_name: [str], Name of api `discovery_document` to be saved.
    api_version: [str], Version of document to get

  Returns:
    Discovery document as a dict.
    None if any errors occur during loading, or parsing the document
  """
  # TODO(b/263521050): use pathlib for whole function.
  file = os.path.join(cache_root, api_name, api_version, _DISCOVERY_CACHE_FILE)

  if not os.path.isfile(file):
    logging.info('Discovery doc not in cache. %s', file)
    return None

  try:
    with open(file, 'rb') as f:
      contents = f.read()
    return contents.decode('utf-8')

  except Exception as e:  # pylint: disable=broad-except
    logging.warning('Error loading discovery document %s: %s', file, e)
    return None


def save_to_cache(
    cache_root: str, api_name: str, api_version: str, discovery_document: str
) -> None:
  """Saves a discovery document to the on-disc cache with key `api` and `version`.

  Args:
    cache_root: [str], a directory where all cache files are stored.
    api_name: [str], Name of api `discovery_document` to be saved.
    api_version: [str], Version of `discovery_document`.
    discovery_document: [str]. Discovery document as a json string.

  Raises:
    OSError: If an error occurs when the file is written.
  """
  # TODO(b/263521050): use pathlib for whole function.
  # Store all files as: $cache_root/$api_name/$api_version
  directory = os.path.join(cache_root, api_name, api_version)
  file = os.path.join(directory, _DISCOVERY_CACHE_FILE)

  # Return. File already cached.
  if os.path.isfile(file):
    return

  # TODO(b/263521050): Cleanup try block w/ `exist_ok=True`
  # Ensure `directory` & ancestors exist.
  try:
    os.makedirs(directory)
  except OSError as e:
    if e.errno != errno.EEXIST:
      raise

  # Here we will write the discovery doc to a temp file and then rename that
  # temp file to our destination cache file. This is to ensure we have an
  # atomic file operation. Without this it could be possible to have a bq
  # client see the cached discovery file and load it although it is empty.
  # The temporary file needs to be in a unique path so that different
  # invocations don't conflict; both will be able to write to their temp
  # file, and the last one will move to final place.
  # TOO
  tmpdir = tempfile.mkdtemp(dir=directory)
  try:
    # TODO(b/263521050): switch to tempfile.TemporaryDirectory() after py3 move.
    temp_file_path = os.path.join(tmpdir, 'tmp.json')
    with open(temp_file_path, 'wb') as f:
      f.write(stringutil.ensure_binary(discovery_document, 'utf8'))
      # Flush followed by fsync to ensure all data is written to temp file
      # before our rename operation.
      f.flush()
      os.fsync(f.fileno())
    # Atomically create (via rename) the 'real' cache file.
    os.rename(temp_file_path, file)
  finally:
    shutil.rmtree(tmpdir, ignore_errors=True)
