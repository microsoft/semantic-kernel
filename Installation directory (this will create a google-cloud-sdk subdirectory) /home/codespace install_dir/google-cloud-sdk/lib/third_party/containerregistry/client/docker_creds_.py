# Copyright 2017 Google Inc. All Rights Reserved.
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
"""This package exposes credentials for talking to a Docker registry."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import abc
import base64
import errno
import io
import json
import logging
import os
import subprocess

from containerregistry.client import docker_name
import httplib2
from oauth2client import client as oauth2client

import six


class Provider(six.with_metaclass(abc.ABCMeta, object)):
  """Interface for providing User Credentials for use with a Docker Registry."""

  # pytype: disable=bad-return-type
  @abc.abstractmethod
  def Get(self):
    """Produces a value suitable for use in the Authorization header."""
  # pytype: enable=bad-return-type


class Anonymous(Provider):
  """Implementation for anonymous access."""

  def Get(self):
    """Implement anonymous authentication."""
    return ''


class SchemeProvider(Provider):
  """Implementation for providing a challenge response credential."""

  def __init__(self, scheme):
    self._scheme = scheme

  # pytype: disable=bad-return-type
  @property
  @abc.abstractmethod
  def suffix(self):
    """Returns the authentication payload to follow the auth scheme."""
  # pytype: enable=bad-return-type

  def Get(self):
    """Gets the credential in a form suitable for an Authorization header."""
    return u'%s %s' % (self._scheme, self.suffix)


class Basic(SchemeProvider):
  """Implementation for providing a username/password-based creds."""

  def __init__(self, username, password):
    super(Basic, self).__init__('Basic')
    self._username = username
    self._password = password

  @property
  def username(self):
    return self._username

  @property
  def password(self):
    return self._password

  @property
  def suffix(self):
    u = self.username.encode('utf8')
    p = self.password.encode('utf8')
    return base64.b64encode(u + b':' + p).decode('utf8')


_USERNAME = '_token'


class OAuth2(Basic):
  """Base class for turning OAuth2Credentials into suitable GCR credentials."""

  def __init__(self, creds,
               transport):
    """Constructor.

    Args:
      creds: the credentials from which to retrieve access tokens.
      transport: the http transport to use for token exchanges.
    """
    super(OAuth2, self).__init__(_USERNAME, 'does not matter')
    self._creds = creds
    self._transport = transport

  @property
  def password(self):
    # WORKAROUND...
    # The python oauth2client library only loads the credential from an
    # on-disk cache the first time 'refresh()' is called, and doesn't
    # actually 'Force a refresh of access_token' as advertised.
    # This call will load the credential, and the call below will refresh
    # it as needed.  If the credential is unexpired, the call below will
    # simply return a cache of this refresh.
    unused_at = self._creds.get_access_token(http=self._transport)

    # Most useful API ever:
    # https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={at}
    return self._creds.get_access_token(http=self._transport).access_token


_MAGIC_NOT_FOUND_MESSAGE = 'credentials not found in native keychain'


class Helper(Basic):
  """This provider wraps a particularly named credential helper."""

  def __init__(self, name, registry):
    """Constructor.

    Args:
      name: the name of the helper, as it appears in the Docker config.
      registry: the registry for which we're invoking the helper.
    """
    super(Helper, self).__init__('does not matter', 'does not matter')
    self._name = name
    self._registry = registry.registry

  def Get(self):
    # Invokes:
    #   echo -n {self._registry} | docker-credential-{self._name} get
    # The resulting JSON blob will have 'Username' and 'Secret' fields.

    bin_name = 'docker-credential-{name}'.format(name=self._name)
    logging.info('Invoking %r to obtain Docker credentials.', bin_name)
    try:
      p = subprocess.Popen(
          [bin_name, 'get'],
          stdout=subprocess.PIPE,
          stdin=subprocess.PIPE,
          stderr=subprocess.STDOUT)
    except OSError as e:
      if e.errno == errno.ENOENT:
        raise Exception('executable not found: ' + bin_name)
      raise

    # Some keychains expect a scheme:
    # https://github.com/bazelbuild/rules_docker/issues/111
    stdout = p.communicate(
        input=('https://' + self._registry).encode('utf-8'))[0]
    if stdout.strip() == _MAGIC_NOT_FOUND_MESSAGE:
      # Use empty auth when no auth is found.
      logging.info('Credentials not found, falling back to anonymous auth.')
      return Anonymous().Get()

    if p.returncode != 0:
      raise Exception('Error fetching credential for %s, exit status: %d\n%s' %
                      (self._name, p.returncode, stdout))

    blob = json.loads(stdout.decode('utf-8'))
    logging.info('Successfully obtained Docker credentials.')
    return Basic(blob['Username'], blob['Secret']).Get()


class Keychain(six.with_metaclass(abc.ABCMeta, object)):
  """Interface for resolving an image reference to a credential."""

  # pytype: disable=bad-return-type
  @abc.abstractmethod
  def Resolve(self, name):
    """Resolves the appropriate credential for the given registry.

    Args:
      name: the registry for which we need a credential.

    Returns:
      a Provider suitable for use with registry operations.
    """
  # pytype: enable=bad-return-type


_FORMATS = [
    # Allow naked domains
    '%s',
    # Allow scheme-prefixed.
    'https://%s',
    'http://%s',
    # Allow scheme-prefixes with version in url path.
    'https://%s/v1/',
    'http://%s/v1/',
    'https://%s/v2/',
    'http://%s/v2/',
]


def _GetUserHomeDir():
  if os.name == 'nt':
    # %HOME% has precedence over %USERPROFILE% for os.path.expanduser('~')
    # The Docker config resides under %USERPROFILE% on Windows
    return os.path.expandvars('%USERPROFILE%')
  else:
    return os.path.expanduser('~')


def _GetConfigDirectory():
  # Return the value of $DOCKER_CONFIG, if it exists, otherwise ~/.docker
  # see https://github.com/docker/docker/blob/master/cliconfig/config.go
  if os.environ.get('DOCKER_CONFIG') is not None:
    return os.environ.get('DOCKER_CONFIG')
  else:
    return os.path.join(_GetUserHomeDir(), '.docker')


class _DefaultKeychain(Keychain):
  """This implements the default docker credential resolution."""

  def __init__(self):
    # Store a custom directory to get the Docker configuration JSON from
    self._config_dir = None
    # Name of the docker configuration JSON file to look for in the
    # configuration directory
    self._config_file = 'config.json'

  def setCustomConfigDir(self, config_dir):
    # Override the configuration directory where the docker configuration
    # JSON is searched for
    if not os.path.isdir(config_dir):
      raise Exception('Attempting to override docker configuration directory'
                      ' to invalid directory: {}'.format(config_dir))
    self._config_dir = config_dir

  def Resolve(self, name):
    # TODO(user): Consider supporting .dockercfg, which was used prior
    # to Docker 1.7 and consisted of just the contents of 'auths' below.
    logging.info('Loading Docker credentials for repository %r', str(name))
    config_file = None
    if self._config_dir is not None:
      config_file = os.path.join(self._config_dir, self._config_file)
    else:
      config_file = os.path.join(_GetConfigDirectory(), self._config_file)
    try:
      with io.open(config_file, u'r', encoding='utf8') as reader:
        cfg = json.loads(reader.read())
    except IOError:
      # If the file doesn't exist, fallback on anonymous auth.
      return Anonymous()

    # Per-registry credential helpers take precedence.
    cred_store = cfg.get('credHelpers', {})
    for form in _FORMATS:
      if form % name.registry in cred_store:
        return Helper(cred_store[form % name.registry], name)

    # A global credential helper is next in precedence.
    if 'credsStore' in cfg:
      return Helper(cfg['credsStore'], name)

    # Lastly, the 'auths' section directly contains basic auth entries.
    auths = cfg.get('auths', {})
    for form in _FORMATS:
      if form % name.registry in auths:
        entry = auths[form % name.registry]
        if 'auth' in entry:
          decoded = base64.b64decode(entry['auth']).decode('utf8')
          username, password = decoded.split(':', 1)
          return Basic(username, password)
        elif 'username' in entry and 'password' in entry:
          return Basic(entry['username'], entry['password'])
        else:
          # TODO(user): Support identitytoken
          # TODO(user): Support registrytoken
          raise Exception(
              'Unsupported entry in "auth" section of Docker config: ' +
              json.dumps(entry))

    return Anonymous()


# pylint: disable=invalid-name
DefaultKeychain = _DefaultKeychain()
