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
"""This package defines Tag a way of representing an image uri."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import os
import sys
import six.moves.urllib.parse



class BadNameException(Exception):
  """Exceptions when a bad docker name is supplied."""


_REPOSITORY_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789_-./'
_TAG_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789_-.ABCDEFGHIJKLMNOPQRSTUVWXYZ'
# These have the form: sha256:<hex string>
_DIGEST_CHARS = 'sh:0123456789abcdef'

# TODO(b/73235733): Add a flag to allow specifying custom app name to be
# appended to useragent.
_APP = os.path.basename(sys.argv[0]) if sys.argv[0] else 'console'
USER_AGENT = '//containerregistry/client:%s' % _APP

DEFAULT_DOMAIN = 'index.docker.io'
DEFAULT_TAG = 'latest'


def _check_element(name, element, characters, min_len,
                   max_len):
  """Checks a given named element matches character and length restrictions.

  Args:
    name: the name of the element being validated
    element: the actual element being checked
    characters: acceptable characters for this element, or None
    min_len: minimum element length, or None
    max_len: maximum element length, or None

  Raises:
    BadNameException: one of the restrictions was not met.
  """
  length = len(element)
  if min_len and length < min_len:
    raise BadNameException('Invalid %s: %s, must be at least %s characters' %
                           (name, element, min_len))

  if max_len and length > max_len:
    raise BadNameException('Invalid %s: %s, must be at most %s characters' %
                           (name, element, max_len))

  if element.strip(characters):
    raise BadNameException('Invalid %s: %s, acceptable characters include: %s' %
                           (name, element, characters))


def _check_repository(repository):
  _check_element('repository', repository, _REPOSITORY_CHARS, 2, 255)


def _check_tag(tag):
  _check_element('tag', tag, _TAG_CHARS, 1, 127)


def _check_digest(digest):
  _check_element('digest', digest, _DIGEST_CHARS, 7 + 64, 7 + 64)


def _check_registry(registry):
  # Per RFC 3986, netlocs (authorities) are required to be prefixed with '//'
  parsed_hostname = six.moves.urllib.parse.urlparse('//' + registry)

  # If urlparse doesn't recognize the given registry as a netloc, fail
  # validation.
  if registry != parsed_hostname.netloc:
    raise BadNameException('Invalid registry: %s' % (registry))


class Registry(object):
  """Stores a docker registry name in a structured form."""

  def __init__(self, name, strict = True):
    if strict:
      if not name:
        raise BadNameException('A Docker registry domain must be specified.')
      _check_registry(name)

    self._registry = name

  @property
  def registry(self):
    return self._registry or DEFAULT_DOMAIN

  def __str__(self):
    return self._registry

  def __repr__(self):
    return self.__str__()

  def __eq__(self, other):
    return (bool(other) and
            # pylint: disable=unidiomatic-typecheck
            type(self) == type(other) and
            self.registry == other.registry)

  def __ne__(self, other):
    return not self.__eq__(other)

  def __hash__(self):
    return hash(self.registry)

  def scope(self, unused_action):
    # The only resource under 'registry' is 'catalog'. http://goo.gl/N9cN9Z
    return 'registry:catalog:*'


class Repository(Registry):
  """Stores a docker repository name in a structured form."""

  def __init__(self, name, strict = True):
    if not name:
      raise BadNameException('A Docker image name must be specified')

    domain = ''
    repo = name
    parts = name.split('/', 1)
    if len(parts) == 2:
      # The first part of the repository is treated as the registry domain
      # iff it contains a '.' or ':' character, otherwise it is all repository
      # and the domain defaults to DockerHub.
      if '.' in parts[0] or ':' in parts[0]:
        domain = parts[0]
        repo = parts[1]

    super(Repository, self).__init__(domain, strict=strict)

    self._repository = repo
    _check_repository(self._repository)

  def _validation_exception(self, name):
    return BadNameException('Docker image name must have the form: '
                            'registry/repository, saw: %s' % name)

  @property
  def repository(self):
    return self._repository

  def __str__(self):
    base = super(Repository, self).__str__()
    if base:
      return '{registry}/{repository}'.format(
          registry=base, repository=self._repository)
    else:
      return self._repository

  def __eq__(self, other):
    return (bool(other) and
            # pylint: disable=unidiomatic-typecheck
            type(self) == type(other) and
            self.registry == other.registry and
            self.repository == other.repository)

  def __ne__(self, other):
    return not self.__eq__(other)

  def __hash__(self):
    return hash((self.registry, self.repository))

  def scope(self, action):
    return 'repository:{resource}:{action}'.format(
        resource=self._repository,
        action=action)


class Tag(Repository):
  """Stores a docker repository tag in a structured form."""

  def __init__(self, name, strict = True):
    parts = name.rsplit(':', 1)
    if len(parts) != 2:
      base = name
      tag = ''
    else:
      base = parts[0]
      tag = parts[1]

    self._tag = tag
    # We don't require a tag, but if we get one check it's valid,
    # even when not being strict.
    # If we are being strict, we want to validate the tag regardless in case
    # it's empty.
    if self._tag or strict:
      _check_tag(self._tag)
    # Parse the (base) repository portion of the name.
    super(Tag, self).__init__(base, strict=strict)

  @property
  def tag(self):
    return self._tag or DEFAULT_TAG

  def __str__(self):
    base = super(Tag, self).__str__()
    if self._tag:
      return '{base}:{tag}'.format(base=base, tag=self._tag)
    else:
      return base

  def as_repository(self):
    # Construct a new Repository object from the string representation
    # our parent class (Repository) produces.  This is a convenience
    # method to allow consumers to stringify the repository portion of
    # a tag or digest without their own format string.
    # We have already validated, and we don't persist strictness.
    return Repository(super(Tag, self).__str__(), strict=False)

  def __eq__(self, other):
    return (bool(other) and
            # pylint: disable=unidiomatic-typecheck
            type(self) == type(other) and
            self.registry == other.registry and
            self.repository == other.repository and
            self.tag == other.tag)

  def __ne__(self, other):
    return not self.__eq__(other)

  def __hash__(self):
    return hash((self.registry, self.repository, self.tag))


class Digest(Repository):
  """Stores a docker repository digest in a structured form."""

  def __init__(self, name, strict = True):
    parts = name.split('@')
    if len(parts) != 2:
      raise self._validation_exception(name)

    self._digest = parts[1]
    _check_digest(self._digest)
    super(Digest, self).__init__(parts[0], strict=strict)

  def _validation_exception(self, name):
    return BadNameException('Docker image name must be fully qualified (e.g.'
                            'registry/repository@digest) saw: %s' % name)

  @property
  def digest(self):
    return self._digest

  def __str__(self):
    base = super(Digest, self).__str__()
    return '{base}@{digest}'.format(base=base, digest=self.digest)

  def as_repository(self):
    # Construct a new Repository object from the string representation
    # our parent class (Repository) produces.  This is a convenience
    # method to allow consumers to stringify the repository portion of
    # a tag or digest without their own format string.
    # We have already validated, and we don't persist strictness.
    return Repository(super(Digest, self).__str__(), strict=False)

  def __eq__(self, other):
    return (bool(other) and
            # pylint: disable=unidiomatic-typecheck
            type(self) == type(other) and
            self.registry == other.registry and
            self.repository == other.repository and
            self.digest == other.digest)

  def __ne__(self, other):
    return not self.__eq__(other)

  def __hash__(self):
    return hash((self.registry, self.repository, self.digest))


def from_string(name):
  """Parses the given name string.

  Parsing is done strictly; registry is required and a Tag will only be returned
  if specified explicitly in the given name string.
  Args:
    name: The name to convert.
  Returns:
    The parsed name.
  Raises:
    BadNameException: The name could not be parsed.
  """
  for name_type in [Digest, Tag, Repository, Registry]:
    # Re-uses validation logic in the name classes themselves.
    try:
      return name_type(name, strict=True)
    except BadNameException:
      pass
  raise BadNameException("'%s' is not a valid Tag, Digest, Repository or "
                         "Registry" % (name))
