# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Utilities for loading runtime defs from git."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import contextlib
import os

from dulwich import client
from dulwich import errors
from dulwich import index
from dulwich import porcelain
from dulwich import repo

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
import six

# Fake out 'WindowsError' if it doesn't exist (the WindowsError exception
# class only exists in Python on Windows, but we need to catch it in order to
# deal with certain error cases).
try:
  WindowsError
except NameError:

  class WindowsError(Exception):
    pass


class UnsupportedClientType(exceptions.Error):
  """Raised when you try to pull from an unknown repository type.

  The URL passed to InstallRuntimeDef identifies an arbitrary git repository.
  This exception is raised when we get one we don't know how to GetRefs() from.
  """


class RepositoryCommunicationError(exceptions.Error):
  """An error occurred communicating to a git repository."""


class InvalidTargetDirectoryError(exceptions.Error):
  """An invalid target directory was specified."""


class InvalidRepositoryError(exceptions.Error):
  """Attempted to fetch or clone from a repository missing something basic.

  This gets raised if we try to fetch or clone from a repo that is either
  missing a HEAD or missing both a "latest" tag and a master branch.
  """


def WrapClient(location):
  """Returns a ClientWrapper."""
  transport, path = client.get_transport_and_path(location)
  if isinstance(transport, client.TraditionalGitClient):
    return TraditionalClient(transport, path)
  elif isinstance(transport, client.HttpGitClient):
    return HTTPClient(transport, path)
  elif isinstance(transport, client.LocalGitClient):
    return LocalClient(transport, path)
  else:
    # We can't currently trigger this, everything falls through to a local
    # repository, but just in case...
    raise UnsupportedClientType(transport.__class__.__name__)


class ClientWrapper(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for a git client wrapper.

  This provides a uniform interface around the various types of git clients
  from dulwich 0.10.1.
  """

  def __init__(self, transport, path):
    self._transport = transport
    self._path = path

  @abc.abstractmethod
  def GetRefs(self):
    """Get a dictionary of all refs available from the repository.

    Returns:
      ({str: str, ...}) Dictionary mapping ref names to commit ids.
    """
    pass


class TraditionalClient(ClientWrapper):
  """Wraps a dulwich.client.TraditionalGitClient."""

  def GetRefs(self):
    # We need to access _connect() to make this work, at least until we get a
    # more recent version of dulwich.
    # pylint:disable=protected-access
    proto = self._transport._connect(b'upload-pack', self._path)[0]
    with proto:
      refs = client.read_pkt_refs(proto)[0]
      proto.write_pkt_line(None)
      return refs


class HTTPClient(ClientWrapper):
  """Wraps a dulwich.client.TCPGitClient."""

  def GetRefs(self):
    # We need to access _get_url and _discover_references() to make this
    # work, at least until we get a more recent version of dulwich.
    # pylint:disable=protected-access
    url = self._transport._get_url(self._path)
    refs, unused_capabilities, url = (
        self._transport._discover_references(b'git-upload-pack', url))
    return refs


class LocalClient(ClientWrapper):
  """Wraps a dulwich.LocalGitClient."""

  def GetRefs(self):
    with contextlib.closing(repo.Repo(self._path)) as r:
      return r.get_refs()


def _PullTags(local_repo, client_wrapper, target_dir):
  """Pull tags from 'client_wrapper' into 'local_repo'.

  Args:
    local_repo: (repo.Repo)
    client_wrapper: (ClientWrapper)
    target_dir: (str) The directory of the local repo (for error reporting).

  Returns:
    (str, dulwich.objects.Commit) The tag that was actually pulled (we try to
    get "latest" but fall back to "master") and the commit object
    associated with it.

  Raises:
    errors.HangupException: Hangup during communication to a remote repository.
  """
  for ref, obj_id in six.iteritems(client_wrapper.GetRefs()):
    if ref.startswith('refs/tags/'):
      try:
        local_repo[ref] = obj_id
      except WindowsError as ex:
        raise InvalidTargetDirectoryError(
            'Unable to checkout directory {0}: {1}'.format(target_dir,
                                                           ex.message))
  # Try to get the "latest" tag (latest released version)
  revision = None
  tag = None
  for tag in (b'refs/tags/latest', b'refs/heads/master'):
    try:
      log.debug('looking up ref %s', tag)
      revision = local_repo[tag]
      break
    except KeyError:
      log.warning('Unable to checkout branch %s', tag)

  else:
    raise AssertionError('No "refs/heads/master" tag found in repository.')

  return tag, revision


def _FetchRepo(target_dir, url):
  """Fetch a git repository from 'url' into 'target_dir'.

  See InstallRuntimeDef() for information on which version is selected.

  Args:
    target_dir: (str) Directory name.
    url: (str) Git repository URL.

  Raises:
    errors.HangupException: Hangup during communication to a remote repository.
  """
  if os.path.exists(target_dir):
    # If the target directory exists, just update it.
    log.debug('Fetching from %s into existing directory.', url)
    try:
      porcelain.fetch(target_dir, url)
    except (IOError, OSError) as ex:
      raise InvalidTargetDirectoryError('Unable to fetch into target '
                                        'directory {0}: {1}'.format(
                                            target_dir, ex.message))
  else:
    try:
      log.debug('Cloning from %s into %s', url, target_dir)
      porcelain.clone(url, target_dir, checkout=False)
    except (errors.NotGitRepository, OSError) as ex:
      # This gets thrown for an invalid directory, e.g. if the base base
      # directory doesn't exist.
      raise InvalidTargetDirectoryError('Unable to clone into target '
                                        'directory {0}: {1}'.format(
                                            target_dir, ex.message))
    except KeyError as ex:
      # When we try to clone an empty git repo, we get KeyError('HEAD') when
      # clone tries to look up the head tag.
      if ex.message == 'HEAD':
        raise InvalidRepositoryError()
      else:
        raise


def _CheckoutLatestVersion(target_dir, url):
  """Pull tags and checkout the latest version of the target directory.

  Args:
    target_dir: (str) Directory name.
    url: (str) Git repository URL.

  Raises:
    errors.HangupException: Hangup during communication to a remote repository.
  """
  local_repo = repo.Repo(target_dir)
  try:
    # We don't get the tags with a clone or a fetch, so we have to get them
    # after the fact.
    client_wrapper = WrapClient(url)
    local_repo = repo.Repo(target_dir)
    tag, revision = _PullTags(local_repo, client_wrapper, target_dir)

    log.info('Checking out revision [%s] of [%s] into [%s]', tag, url,
             target_dir)
    try:
      # Checkout the specified revision of the runtime definition from git.
      index.build_index_from_tree(local_repo.path, local_repo.index_path(),
                                  local_repo.object_store,
                                  revision.tree)
    except (IOError, OSError, WindowsError) as ex:
      raise InvalidTargetDirectoryError(
          'Unable to checkout directory {0}: {1}'.format(target_dir,
                                                         ex.message))
  except (AssertionError) as ex:
    raise InvalidRepositoryError()
  finally:
    local_repo.close()


def InstallRuntimeDef(url, target_dir):
  """Install a runtime definition in the target directory.

  This installs the runtime definition identified by 'url' into the target
  directory.  At this time, the runtime definition url must be the URL of a
  git repository and we identify the tree to checkout based on 1) the presence
  of a "latest" tag ("refs/tags/latest") 2) if there is no "latest" tag, the
  head of the "master" branch ("refs/heads/master").

  Args:
    url: (str) A URL identifying a git repository.  The HTTP, TCP and local
      git protocols are formally supported. e.g.
        https://github.com/project/repo.git
        git://example.com:1234
        /some/git/directory
    target_dir: (str) The path where the definition will be installed.

  Raises:
    InvalidTargetDirectoryError: An invalid target directory was specified.
    RepositoryCommunicationError: An error occurred communicating to the
      repository identified by 'url'.
  """
  try:
    _FetchRepo(target_dir, url)
    _CheckoutLatestVersion(target_dir, url)
  except (errors.HangupException, errors.GitProtocolError) as ex:
    raise RepositoryCommunicationError('An error occurred accessing '
                                       '{0}: {1}'.format(url, ex.message))
