#!/usr/bin/env python
#
# Copyright 2015 Google Inc.
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

"""Common credentials classes and constructors."""
from __future__ import print_function

import argparse
import contextlib
import datetime
import json
import os
import threading
import warnings

import httplib2
import oauth2client
import oauth2client.client
from oauth2client import service_account
from oauth2client import tools  # for gflags declarations
import six
from six.moves import http_client
from six.moves import urllib

from apitools.base.py import exceptions
from apitools.base.py import util

# App Engine does not support ctypes which are required for the
# monotonic time used in fasteners. Conversely, App Engine does
# not support colocated concurrent processes, so process locks
# are not needed.
try:
    import fasteners
    _FASTENERS_AVAILABLE = True
except ImportError as import_error:
    server_env = os.environ.get('SERVER_SOFTWARE', '')
    if not (server_env.startswith('Development') or
            server_env.startswith('Google App Engine')):
        raise import_error
    _FASTENERS_AVAILABLE = False

# Note: we try the oauth2client imports two ways, to accomodate layout
# changes in oauth2client 2.0+. We can remove these once we no longer
# support oauth2client < 2.0.
#
# pylint: disable=wrong-import-order,ungrouped-imports
try:
    from oauth2client.contrib import gce
except ImportError:
    from oauth2client import gce

try:
    from oauth2client.contrib import multiprocess_file_storage
    _NEW_FILESTORE = True
except ImportError:
    _NEW_FILESTORE = False
    try:
        from oauth2client.contrib import multistore_file
    except ImportError:
        from oauth2client import multistore_file

try:
    import gflags
    FLAGS = gflags.FLAGS
except ImportError:
    FLAGS = None


__all__ = [
    'CredentialsFromFile',
    'GaeAssertionCredentials',
    'GceAssertionCredentials',
    'GetCredentials',
    'GetUserinfo',
    'ServiceAccountCredentialsFromFile',
]


# Lock when accessing the cache file to avoid resource contention.
cache_file_lock = threading.Lock()


def SetCredentialsCacheFileLock(lock):
    global cache_file_lock  # pylint: disable=global-statement
    cache_file_lock = lock


# List of additional methods we use when attempting to construct
# credentials. Users can register their own methods here, which we try
# before the defaults.
_CREDENTIALS_METHODS = []


def _RegisterCredentialsMethod(method, position=None):
    """Register a new method for fetching credentials.

    This new method should be a function with signature:
      client_info, **kwds -> Credentials or None
    This method can be used as a decorator, unless position needs to
    be supplied.

    Note that method must *always* accept arbitrary keyword arguments.

    Args:
      method: New credential-fetching method.
      position: (default: None) Where in the list of methods to
        add this; if None, we append. In all but rare cases,
        this should be either 0 or None.
    Returns:
      method, for use as a decorator.

    """
    if position is None:
        position = len(_CREDENTIALS_METHODS)
    else:
        position = min(position, len(_CREDENTIALS_METHODS))
    _CREDENTIALS_METHODS.insert(position, method)
    return method


def GetCredentials(package_name, scopes, client_id, client_secret, user_agent,
                   credentials_filename=None,
                   api_key=None,  # pylint: disable=unused-argument
                   client=None,  # pylint: disable=unused-argument
                   oauth2client_args=None,
                   **kwds):
    """Attempt to get credentials, using an oauth dance as the last resort."""
    scopes = util.NormalizeScopes(scopes)
    client_info = {
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': ' '.join(sorted(scopes)),
        'user_agent': user_agent or '%s-generated/0.1' % package_name,
    }
    for method in _CREDENTIALS_METHODS:
        credentials = method(client_info, **kwds)
        if credentials is not None:
            return credentials
    credentials_filename = credentials_filename or os.path.expanduser(
        '~/.apitools.token')
    credentials = CredentialsFromFile(credentials_filename, client_info,
                                      oauth2client_args=oauth2client_args)
    if credentials is not None:
        return credentials
    raise exceptions.CredentialsError('Could not create valid credentials')


def ServiceAccountCredentialsFromFile(filename, scopes, user_agent=None):
    """Use the credentials in filename to create a token for scopes."""
    filename = os.path.expanduser(filename)
    # We have two options, based on our version of oauth2client.
    if oauth2client.__version__ > '1.5.2':
        # oauth2client >= 2.0.0
        credentials = (
            service_account.ServiceAccountCredentials.from_json_keyfile_name(
                filename, scopes=scopes))
        if credentials is not None:
            if user_agent is not None:
                credentials.user_agent = user_agent
        return credentials
    else:
        # oauth2client < 2.0.0
        with open(filename) as keyfile:
            service_account_info = json.load(keyfile)
        account_type = service_account_info.get('type')
        if account_type != oauth2client.client.SERVICE_ACCOUNT:
            raise exceptions.CredentialsError(
                'Invalid service account credentials: %s' % (filename,))
        # pylint: disable=protected-access
        credentials = service_account._ServiceAccountCredentials(
            service_account_id=service_account_info['client_id'],
            service_account_email=service_account_info['client_email'],
            private_key_id=service_account_info['private_key_id'],
            private_key_pkcs8_text=service_account_info['private_key'],
            scopes=scopes, user_agent=user_agent)
        # pylint: enable=protected-access
        return credentials


def ServiceAccountCredentialsFromP12File(
        service_account_name, private_key_filename, scopes, user_agent):
    """Create a new credential from the named .p12 keyfile."""
    private_key_filename = os.path.expanduser(private_key_filename)
    scopes = util.NormalizeScopes(scopes)
    if oauth2client.__version__ > '1.5.2':
        # oauth2client >= 2.0.0
        credentials = (
            service_account.ServiceAccountCredentials.from_p12_keyfile(
                service_account_name, private_key_filename, scopes=scopes))
        if credentials is not None:
            credentials.user_agent = user_agent
        return credentials
    else:
        # oauth2client < 2.0.0
        with open(private_key_filename, 'rb') as key_file:
            return oauth2client.client.SignedJwtAssertionCredentials(
                service_account_name, key_file.read(), scopes,
                user_agent=user_agent)


def _GceMetadataRequest(relative_url, use_metadata_ip=False):
    """Request the given url from the GCE metadata service."""
    if use_metadata_ip:
        base_url = os.environ.get('GCE_METADATA_IP', '169.254.169.254')
    else:
        base_url = os.environ.get(
            'GCE_METADATA_ROOT', 'metadata.google.internal')
    url = 'http://' + base_url + '/computeMetadata/v1/' + relative_url
    # Extra header requirement can be found here:
    # https://developers.google.com/compute/docs/metadata
    headers = {'Metadata-Flavor': 'Google'}
    request = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        response = opener.open(request)
    except urllib.error.URLError as e:
        raise exceptions.CommunicationError(
            'Could not reach metadata service: %s' % e.reason)
    return response


class GceAssertionCredentials(gce.AppAssertionCredentials):

    """Assertion credentials for GCE instances."""

    def __init__(self, scopes=None, service_account_name='default', **kwds):
        """Initializes the credentials instance.

        Args:
          scopes: The scopes to get. If None, whatever scopes that are
              available to the instance are used.
          service_account_name: The service account to retrieve the scopes
              from.
          **kwds: Additional keyword args.

        """
        # If there is a connectivity issue with the metadata server,
        # detection calls may fail even if we've already successfully
        # identified these scopes in the same execution. However, the
        # available scopes don't change once an instance is created,
        # so there is no reason to perform more than one query.
        self.__service_account_name = six.ensure_text(
            service_account_name,
            encoding='utf-8',)
        cached_scopes = None
        cache_filename = kwds.get('cache_filename')
        if cache_filename:
            cached_scopes = self._CheckCacheFileForMatch(
                cache_filename, scopes)

        scopes = cached_scopes or self._ScopesFromMetadataServer(scopes)

        if cache_filename and not cached_scopes:
            self._WriteCacheFile(cache_filename, scopes)

        # We check the scopes above, but don't need them again after
        # this point. Newer versions of oauth2client let us drop them
        # here, but since we support older versions as well, we just
        # catch and squelch the warning.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            super(GceAssertionCredentials, self).__init__(scope=scopes, **kwds)

    @classmethod
    def Get(cls, *args, **kwds):
        try:
            return cls(*args, **kwds)
        except exceptions.Error:
            return None

    def _CheckCacheFileForMatch(self, cache_filename, scopes):
        """Checks the cache file to see if it matches the given credentials.

        Args:
          cache_filename: Cache filename to check.
          scopes: Scopes for the desired credentials.

        Returns:
          List of scopes (if cache matches) or None.
        """
        creds = {  # Credentials metadata dict.
            'scopes': sorted(list(scopes)) if scopes else None,
            'svc_acct_name': self.__service_account_name,
        }
        cache_file = _MultiProcessCacheFile(cache_filename)
        try:
            cached_creds_str = cache_file.LockedRead()
            if not cached_creds_str:
                return None
            cached_creds = json.loads(cached_creds_str)
            if creds['svc_acct_name'] == cached_creds['svc_acct_name']:
                if creds['scopes'] in (None, cached_creds['scopes']):
                    return cached_creds['scopes']
        except KeyboardInterrupt:
            raise
        except:  # pylint: disable=bare-except
            # Treat exceptions as a cache miss.
            pass

    def _WriteCacheFile(self, cache_filename, scopes):
        """Writes the credential metadata to the cache file.

        This does not save the credentials themselves (CredentialStore class
        optionally handles that after this class is initialized).

        Args:
          cache_filename: Cache filename to check.
          scopes: Scopes for the desired credentials.
        """
        # Credentials metadata dict.
        scopes = sorted([six.ensure_text(scope) for scope in scopes])
        creds = {'scopes': scopes,
                 'svc_acct_name': self.__service_account_name}
        creds_str = json.dumps(creds)
        cache_file = _MultiProcessCacheFile(cache_filename)
        try:
            cache_file.LockedWrite(creds_str)
        except KeyboardInterrupt:
            raise
        except:  # pylint: disable=bare-except
            # Treat exceptions as a cache miss.
            pass

    def _ScopesFromMetadataServer(self, scopes):
        """Returns instance scopes based on GCE metadata server."""
        if not util.DetectGce():
            raise exceptions.ResourceUnavailableError(
                'GCE credentials requested outside a GCE instance')
        if not self.GetServiceAccount(self.__service_account_name):
            raise exceptions.ResourceUnavailableError(
                'GCE credentials requested but service account '
                '%s does not exist.' % self.__service_account_name)
        if scopes:
            scope_ls = util.NormalizeScopes(scopes)
            instance_scopes = self.GetInstanceScopes()
            if scope_ls > instance_scopes:
                raise exceptions.CredentialsError(
                    'Instance did not have access to scopes %s' % (
                        sorted(list(scope_ls - instance_scopes)),))
        else:
            scopes = self.GetInstanceScopes()
        return scopes

    def GetServiceAccount(self, account):
        relative_url = 'instance/service-accounts'
        response = _GceMetadataRequest(relative_url)
        response_lines = [six.ensure_str(line).rstrip(u'/\n\r')
                          for line in response.readlines()]
        return account in response_lines

    def GetInstanceScopes(self):
        relative_url = 'instance/service-accounts/{0}/scopes'.format(
            self.__service_account_name)
        response = _GceMetadataRequest(relative_url)
        return util.NormalizeScopes(six.ensure_str(scope).strip()
                                    for scope in response.readlines())

    # pylint: disable=arguments-differ
    def _refresh(self, do_request):
        """Refresh self.access_token.

        This function replaces AppAssertionCredentials._refresh, which
        does not use the credential store and is therefore poorly
        suited for multi-threaded scenarios.

        Args:
          do_request: A function matching httplib2.Http.request's signature.

        """
        # pylint: disable=protected-access
        oauth2client.client.OAuth2Credentials._refresh(self, do_request)
        # pylint: enable=protected-access

    def _do_refresh_request(self, unused_http_request):
        """Refresh self.access_token by querying the metadata server.

        If self.store is initialized, store acquired credentials there.
        """
        relative_url = 'instance/service-accounts/{0}/token'.format(
            self.__service_account_name)
        try:
            response = _GceMetadataRequest(relative_url)
        except exceptions.CommunicationError:
            self.invalid = True
            if self.store:
                self.store.locked_put(self)
            raise
        content = six.ensure_str(response.read())
        try:
            credential_info = json.loads(content)
        except ValueError:
            raise exceptions.CredentialsError(
                'Could not parse response as JSON: %s' % content)

        self.access_token = credential_info['access_token']
        if 'expires_in' in credential_info:
            expires_in = int(credential_info['expires_in'])
            self.token_expiry = (
                datetime.timedelta(seconds=expires_in) +
                datetime.datetime.utcnow())
        else:
            self.token_expiry = None
        self.invalid = False
        if self.store:
            self.store.locked_put(self)

    def to_json(self):
        # OAuth2Client made gce.AppAssertionCredentials unserializable as of
        # v3.0, but we need those credentials to be serializable for use with
        # this library, so we use AppAssertionCredentials' parent's to_json
        # method.
        # pylint: disable=bad-super-call
        return super(gce.AppAssertionCredentials, self).to_json()

    @classmethod
    def from_json(cls, json_data):
        data = json.loads(json_data)
        kwargs = {}
        if 'cache_filename' in data.get('kwargs', []):
            kwargs['cache_filename'] = data['kwargs']['cache_filename']
        # Newer versions of GceAssertionCredentials don't have a "scope"
        # attribute.
        scope_list = None
        if 'scope' in data:
            scope_list = [data['scope']]
        credentials = GceAssertionCredentials(scopes=scope_list, **kwargs)
        if 'access_token' in data:
            credentials.access_token = data['access_token']
        if 'token_expiry' in data:
            credentials.token_expiry = datetime.datetime.strptime(
                data['token_expiry'], oauth2client.client.EXPIRY_FORMAT)
        if 'invalid' in data:
            credentials.invalid = data['invalid']
        return credentials

    @property
    def serialization_data(self):
        raise NotImplementedError(
            'Cannot serialize credentials for GCE service accounts.')


# TODO(craigcitro): Currently, we can't even *load*
# `oauth2client.appengine` without being on appengine, because of how
# it handles imports. Fix that by splitting that module into
# GAE-specific and GAE-independent bits, and guarding imports.
class GaeAssertionCredentials(oauth2client.client.AssertionCredentials):

    """Assertion credentials for Google App Engine apps."""

    def __init__(self, scopes, **kwds):
        if not util.DetectGae():
            raise exceptions.ResourceUnavailableError(
                'GCE credentials requested outside a GCE instance')
        self._scopes = list(util.NormalizeScopes(scopes))
        super(GaeAssertionCredentials, self).__init__(None, **kwds)

    @classmethod
    def Get(cls, *args, **kwds):
        try:
            return cls(*args, **kwds)
        except exceptions.Error:
            return None

    @classmethod
    def from_json(cls, json_data):
        data = json.loads(json_data)
        return GaeAssertionCredentials(data['_scopes'])

    def _refresh(self, _):
        """Refresh self.access_token.

        Args:
          _: (ignored) A function matching httplib2.Http.request's signature.
        """
        # pylint: disable=import-error
        from google.appengine.api import app_identity
        try:
            token, _ = app_identity.get_access_token(self._scopes)
        except app_identity.Error as e:
            raise exceptions.CredentialsError(str(e))
        self.access_token = token

    def sign_blob(self, blob):
        """Cryptographically sign a blob (of bytes).

        This method is provided to support a common interface, but
        the actual key used for a Google Compute Engine service account
        is not available, so it can't be used to sign content.

        Args:
            blob: bytes, Message to be signed.

        Raises:
            NotImplementedError, always.
        """
        raise NotImplementedError(
            'Compute Engine service accounts cannot sign blobs')


def _GetRunFlowFlags(args=None):
    """Retrieves command line flags based on gflags module."""
    # There's one rare situation where gsutil will not have argparse
    # available, but doesn't need anything depending on argparse anyway,
    # since they're bringing their own credentials. So we just allow this
    # to fail with an ImportError in those cases.
    #
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    # Get command line argparse flags.
    flags, _ = parser.parse_known_args(args=args)

    # Allow `gflags` and `argparse` to be used side-by-side.
    if hasattr(FLAGS, 'auth_host_name'):
        flags.auth_host_name = FLAGS.auth_host_name
    if hasattr(FLAGS, 'auth_host_port'):
        flags.auth_host_port = FLAGS.auth_host_port
    if hasattr(FLAGS, 'auth_local_webserver'):
        flags.noauth_local_webserver = (not FLAGS.auth_local_webserver)
    return flags


# TODO(craigcitro): Switch this from taking a path to taking a stream.
def CredentialsFromFile(path, client_info, oauth2client_args=None):
    """Read credentials from a file."""
    user_agent = client_info['user_agent']
    scope_key = client_info['scope']
    if not isinstance(scope_key, six.string_types):
        scope_key = ':'.join(scope_key)
    storage_key = client_info['client_id'] + user_agent + scope_key

    if _NEW_FILESTORE:
        credential_store = multiprocess_file_storage.MultiprocessFileStorage(
            path, storage_key)
    else:
        credential_store = multistore_file.get_credential_storage_custom_string_key(  # noqa
            path, storage_key)
    if hasattr(FLAGS, 'auth_local_webserver'):
        FLAGS.auth_local_webserver = False
    credentials = credential_store.get()
    if credentials is None or credentials.invalid:
        print('Generating new OAuth credentials ...')
        for _ in range(20):
            # If authorization fails, we want to retry, rather than let this
            # cascade up and get caught elsewhere. If users want out of the
            # retry loop, they can ^C.
            try:
                flow = oauth2client.client.OAuth2WebServerFlow(**client_info)
                flags = _GetRunFlowFlags(args=oauth2client_args)
                credentials = tools.run_flow(flow, credential_store, flags)
                break
            except (oauth2client.client.FlowExchangeError, SystemExit) as e:
                # Here SystemExit is "no credential at all", and the
                # FlowExchangeError is "invalid" -- usually because
                # you reused a token.
                print('Invalid authorization: %s' % (e,))
            except httplib2.HttpLib2Error as e:
                print('Communication error: %s' % (e,))
                raise exceptions.CredentialsError(
                    'Communication error creating credentials: %s' % e)
    return credentials


class _MultiProcessCacheFile(object):
    """Simple multithreading and multiprocessing safe cache file.

    Notes on behavior:
    * the fasteners.InterProcessLock object cannot reliably prevent threads
      from double-acquiring a lock. A threading lock is used in addition to
      the InterProcessLock. The threading lock is always acquired first and
      released last.
    * The interprocess lock will not deadlock. If a process can not acquire
      the interprocess lock within `_lock_timeout` the call will return as
      a cache miss or unsuccessful cache write.
    * App Engine environments cannot be process locked because (1) the runtime
      does not provide monotonic time and (2) different processes may or may
      not share the same machine. Because of this, process locks are disabled
      and locking is only guaranteed to protect against multithreaded access.
    """

    _lock_timeout = 1
    _encoding = 'utf-8'
    _thread_lock = threading.Lock()

    def __init__(self, filename):
        self._file = None
        self._filename = filename
        if _FASTENERS_AVAILABLE:
            self._process_lock_getter = self._ProcessLockAcquired
            self._process_lock = fasteners.InterProcessLock(
                '{0}.lock'.format(filename))
        else:
            self._process_lock_getter = self._DummyLockAcquired
            self._process_lock = None

    @contextlib.contextmanager
    def _ProcessLockAcquired(self):
        """Context manager for process locks with timeout."""
        try:
            is_locked = self._process_lock.acquire(timeout=self._lock_timeout)
            yield is_locked
        finally:
            if is_locked:
                self._process_lock.release()

    @contextlib.contextmanager
    def _DummyLockAcquired(self):
        """Lock context manager for environments without process locks."""
        yield True

    def LockedRead(self):
        """Acquire an interprocess lock and dump cache contents.

        This method safely acquires the locks then reads a string
        from the cache file. If the file does not exist and cannot
        be created, it will return None. If the locks cannot be
        acquired, this will also return None.

        Returns:
          cache data - string if present, None on failure.
        """
        file_contents = None
        with self._thread_lock:
            if not self._EnsureFileExists():
                return None
            with self._process_lock_getter() as acquired_plock:
                if not acquired_plock:
                    return None
                with open(self._filename, 'rb') as f:
                    file_contents = f.read().decode(encoding=self._encoding)
        return file_contents

    def LockedWrite(self, cache_data):
        """Acquire an interprocess lock and write a string.

        This method safely acquires the locks then writes a string
        to the cache file. If the string is written successfully
        the function will return True, if the write fails for any
        reason it will return False.

        Args:
          cache_data: string or bytes to write.

        Returns:
          bool: success
        """
        if isinstance(cache_data, six.text_type):
            cache_data = cache_data.encode(encoding=self._encoding)

        with self._thread_lock:
            if not self._EnsureFileExists():
                return False
            with self._process_lock_getter() as acquired_plock:
                if not acquired_plock:
                    return False
                with open(self._filename, 'wb') as f:
                    f.write(cache_data)
                return True

    def _EnsureFileExists(self):
        """Touches a file; returns False on error, True on success."""
        if not os.path.exists(self._filename):
            old_umask = os.umask(0o177)
            try:
                open(self._filename, 'a+b').close()
            except OSError:
                return False
            finally:
                os.umask(old_umask)
        return True


# TODO(craigcitro): Push this into oauth2client.
def GetUserinfo(credentials, http=None):  # pylint: disable=invalid-name
    """Get the userinfo associated with the given credentials.

    This is dependent on the token having either the userinfo.email or
    userinfo.profile scope for the given token.

    Args:
      credentials: (oauth2client.client.Credentials) incoming credentials
      http: (httplib2.Http, optional) http instance to use

    Returns:
      The email address for this token, or None if the required scopes
      aren't available.
    """
    http = http or httplib2.Http()
    url = _GetUserinfoUrl(credentials)
    # We ignore communication woes here (i.e. SSL errors, socket
    # timeout), as handling these should be done in a common location.
    response, content = http.request(url)
    if response.status == http_client.BAD_REQUEST:
        credentials.refresh(http)
        url = _GetUserinfoUrl(credentials)
        response, content = http.request(url)
    return json.loads(content or '{}')  # Save ourselves from an empty reply.


def _GetUserinfoUrl(credentials):
    url_root = 'https://oauth2.googleapis.com/tokeninfo'
    query_args = {'access_token': credentials.access_token}
    return '?'.join((url_root, urllib.parse.urlencode(query_args)))


@_RegisterCredentialsMethod
def _GetServiceAccountCredentials(
        client_info, service_account_name=None, service_account_keyfile=None,
        service_account_json_keyfile=None, **unused_kwds):
    """Returns ServiceAccountCredentials from give file."""
    scopes = client_info['scope'].split()
    user_agent = client_info['user_agent']
    # Use the .json credentials, if provided.
    if service_account_json_keyfile:
        return ServiceAccountCredentialsFromFile(
            service_account_json_keyfile, scopes, user_agent=user_agent)
    # Fall back to .p12 if there's no .json credentials.
    if ((service_account_name and not service_account_keyfile) or
            (service_account_keyfile and not service_account_name)):
        raise exceptions.CredentialsError(
            'Service account name or keyfile provided without the other')
    if service_account_name is not None:
        return ServiceAccountCredentialsFromP12File(
            service_account_name, service_account_keyfile, scopes, user_agent)


@_RegisterCredentialsMethod
def _GetGaeServiceAccount(client_info, **unused_kwds):
    scopes = client_info['scope'].split(' ')
    return GaeAssertionCredentials.Get(scopes=scopes)


@_RegisterCredentialsMethod
def _GetGceServiceAccount(client_info, **unused_kwds):
    scopes = client_info['scope'].split(' ')
    return GceAssertionCredentials.Get(scopes=scopes)


@_RegisterCredentialsMethod
def _GetApplicationDefaultCredentials(
        client_info, skip_application_default_credentials=False,
        **unused_kwds):
    """Returns ADC with right scopes."""
    scopes = client_info['scope'].split()
    if skip_application_default_credentials:
        return None
    gc = oauth2client.client.GoogleCredentials
    with cache_file_lock:
        try:
            # pylint: disable=protected-access
            # We've already done our own check for GAE/GCE
            # credentials, we don't want to pay for checking again.
            credentials = gc._implicit_credentials_from_files()
        except oauth2client.client.ApplicationDefaultCredentialsError:
            return None
    # If we got back a non-service account credential, we need to use
    # a heuristic to decide whether or not the application default
    # credential will work for us. We assume that if we're requesting
    # cloud-platform, our scopes are a subset of cloud scopes, and the
    # ADC will work.
    cp = 'https://www.googleapis.com/auth/cloud-platform'
    if credentials is None:
        return None
    if not isinstance(credentials, gc) or cp in scopes:
        return credentials.create_scoped(scopes)
    return None
