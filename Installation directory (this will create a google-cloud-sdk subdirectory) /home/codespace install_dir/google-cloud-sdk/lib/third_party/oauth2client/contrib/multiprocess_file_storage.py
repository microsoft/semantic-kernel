# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Multiprocess file credential storage.

This module provides file-based storage that supports multiple credentials and
cross-thread and process access.

This module supersedes the functionality previously found in `multistore_file`.

This module provides :class:`MultiprocessFileStorage` which:
    * Is tied to a single credential via a user-specified key. This key can be
      used to distinguish between multiple users, client ids, and/or scopes.
    * Can be safely accessed and refreshed across threads and processes.

Process & thread safety guarantees the following behavior:
    * If one thread or process refreshes a credential, subsequent refreshes
      from other processes will re-fetch the credentials from the file instead
      of performing an http request.
    * If two processes or threads attempt to refresh concurrently, only one
      will be able to acquire the lock and refresh, with the deadlock caveat
      below.
    * The interprocess lock will not deadlock, instead, the if a process can
      not acquire the interprocess lock within ``INTERPROCESS_LOCK_DEADLINE``
      it will allow refreshing the credential but will not write the updated
      credential to disk, This logic happens during every lock cycle - if the
      credentials are refreshed again it will retry locking and writing as
      normal.

Usage
=====

Before using the storage, you need to decide how you want to key the
credentials. A few common strategies include:

    * If you're storing credentials for multiple users in a single file, use
      a unique identifier for each user as the key.
    * If you're storing credentials for multiple client IDs in a single file,
      use the client ID as the key.
    * If you're storing multiple credentials for one user, use the scopes as
      the key.
    * If you have a complicated setup, use a compound key. For example, you
      can use a combination of the client ID and scopes as the key.

Create an instance of :class:`MultiprocessFileStorage` for each credential you
want to store, for example::

    filename = 'credentials'
    key = '{}-{}'.format(client_id, user_id)
    storage = MultiprocessFileStorage(filename, key)

To store the credentials::

    storage.put(credentials)

If you're going to continue to use the credentials after storing them, be sure
to call :func:`set_store`::

    credentials.set_store(storage)

To retrieve the credentials::

    storage.get(credentials)

"""

import base64
import json
import logging
import os
import threading

import fasteners
from six import iteritems

from oauth2client import _helpers
from oauth2client import client


#: The maximum amount of time, in seconds, to wait when acquire the
#: interprocess lock before falling back to read-only mode.
INTERPROCESS_LOCK_DEADLINE = 1

logger = logging.getLogger(__name__)
_backends = {}
_backends_lock = threading.Lock()


def _create_file_if_needed(filename):
    """Creates the an empty file if it does not already exist.

    Returns:
        True if the file was created, False otherwise.
    """
    if os.path.exists(filename):
        return False
    else:
        # Equivalent to "touch".
        open(filename, 'a+b').close()
        logger.info('Credential file {0} created'.format(filename))
        return True


def _load_credentials_file(credentials_file):
    """Load credentials from the given file handle.

    The file is expected to be in this format:

        {
            "file_version": 2,
            "credentials": {
                "key": "base64 encoded json representation of credentials."
            }
        }

    This function will warn and return empty credentials instead of raising
    exceptions.

    Args:
        credentials_file: An open file handle.

    Returns:
        A dictionary mapping user-defined keys to an instance of
        :class:`oauth2client.client.Credentials`.
    """
    try:
        credentials_file.seek(0)
        data = json.load(credentials_file)
    except Exception:
        logger.warning(
            'Credentials file could not be loaded, will ignore and '
            'overwrite.')
        return {}

    if data.get('file_version') != 2:
        logger.warning(
            'Credentials file is not version 2, will ignore and '
            'overwrite.')
        return {}

    credentials = {}

    for key, encoded_credential in iteritems(data.get('credentials', {})):
        try:
            credential_json = base64.b64decode(encoded_credential)
            credential = client.Credentials.new_from_json(credential_json)
            credentials[key] = credential
        except:
            logger.warning(
                'Invalid credential {0} in file, ignoring.'.format(key))

    return credentials


def _write_credentials_file(credentials_file, credentials):
    """Writes credentials to a file.

    Refer to :func:`_load_credentials_file` for the format.

    Args:
        credentials_file: An open file handle, must be read/write.
        credentials: A dictionary mapping user-defined keys to an instance of
            :class:`oauth2client.client.Credentials`.
    """
    data = {'file_version': 2, 'credentials': {}}

    for key, credential in iteritems(credentials):
        credential_json = credential.to_json()
        encoded_credential = _helpers._from_bytes(base64.b64encode(
            _helpers._to_bytes(credential_json)))
        data['credentials'][key] = encoded_credential

    credentials_file.seek(0)
    json.dump(data, credentials_file)
    credentials_file.truncate()


class _MultiprocessStorageBackend(object):
    """Thread-local backend for multiprocess storage.

    Each process has only one instance of this backend per file. All threads
    share a single instance of this backend. This ensures that all threads
    use the same thread lock and process lock when accessing the file.
    """

    def __init__(self, filename):
        self._file = None
        self._filename = filename
        self._process_lock = fasteners.InterProcessLock(
            '{0}.lock'.format(filename))
        self._thread_lock = threading.Lock()
        self._read_only = False
        self._credentials = {}

    def _load_credentials(self):
        """(Re-)loads the credentials from the file."""
        if not self._file:
            return

        loaded_credentials = _load_credentials_file(self._file)
        self._credentials.update(loaded_credentials)

        logger.debug('Read credential file')

    def _write_credentials(self):
        if self._read_only:
            logger.debug('In read-only mode, not writing credentials.')
            return

        _write_credentials_file(self._file, self._credentials)
        logger.debug('Wrote credential file {0}.'.format(self._filename))

    def acquire_lock(self):
        self._thread_lock.acquire()
        locked = self._process_lock.acquire(timeout=INTERPROCESS_LOCK_DEADLINE)

        if locked:
            _create_file_if_needed(self._filename)
            self._file = open(self._filename, 'r+')
            self._read_only = False

        else:
            logger.warn(
                'Failed to obtain interprocess lock for credentials. '
                'If a credential is being refreshed, other processes may '
                'not see the updated access token and refresh as well.')
            if os.path.exists(self._filename):
                self._file = open(self._filename, 'r')
            else:
                self._file = None
            self._read_only = True

        self._load_credentials()

    def release_lock(self):
        if self._file is not None:
            self._file.close()
            self._file = None

        if not self._read_only:
            self._process_lock.release()

        self._thread_lock.release()

    def _refresh_predicate(self, credentials):
        if credentials is None:
            return True
        elif credentials.invalid:
            return True
        elif credentials.access_token_expired:
            return True
        else:
            return False

    def locked_get(self, key):
        # Check if the credential is already in memory.
        credentials = self._credentials.get(key, None)

        # Use the refresh predicate to determine if the entire store should be
        # reloaded. This basically checks if the credentials are invalid
        # or expired. This covers the situation where another process has
        # refreshed the credentials and this process doesn't know about it yet.
        # In that case, this process won't needlessly refresh the credentials.
        if self._refresh_predicate(credentials):
            self._load_credentials()
            credentials = self._credentials.get(key, None)

        return credentials

    def locked_put(self, key, credentials):
        self._load_credentials()
        self._credentials[key] = credentials
        self._write_credentials()

    def locked_delete(self, key):
        self._load_credentials()
        self._credentials.pop(key, None)
        self._write_credentials()


def _get_backend(filename):
    """A helper method to get or create a backend with thread locking.

    This ensures that only one backend is used per-file per-process, so that
    thread and process locks are appropriately shared.

    Args:
        filename: The full path to the credential storage file.

    Returns:
        An instance of :class:`_MultiprocessStorageBackend`.
    """
    filename = os.path.abspath(filename)

    with _backends_lock:
        if filename not in _backends:
            _backends[filename] = _MultiprocessStorageBackend(filename)
        return _backends[filename]


class MultiprocessFileStorage(client.Storage):
    """Multiprocess file credential storage.

    Args:
      filename: The path to the file where credentials will be stored.
      key: An arbitrary string used to uniquely identify this set of
          credentials. For example, you may use the user's ID as the key or
          a combination of the client ID and user ID.
    """
    def __init__(self, filename, key):
        self._key = key
        self._backend = _get_backend(filename)

    def acquire_lock(self):
        self._backend.acquire_lock()

    def release_lock(self):
        self._backend.release_lock()

    def locked_get(self):
        """Retrieves the current credentials from the store.

        Returns:
            An instance of :class:`oauth2client.client.Credentials` or `None`.
        """
        credential = self._backend.locked_get(self._key)

        if credential is not None:
            credential.set_store(self)

        return credential

    def locked_put(self, credentials):
        """Writes the given credentials to the store.

        Args:
            credentials: an instance of
                :class:`oauth2client.client.Credentials`.
        """
        return self._backend.locked_put(self._key, credentials)

    def locked_delete(self):
        """Deletes the current credentials from the store."""
        return self._backend.locked_delete(self._key)
