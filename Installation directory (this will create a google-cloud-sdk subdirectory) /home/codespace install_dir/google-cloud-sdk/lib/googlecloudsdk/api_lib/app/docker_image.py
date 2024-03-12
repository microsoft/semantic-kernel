# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Encapsulation of a docker image."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class Image(object):
  """Docker image that requires building and should be removed afterwards."""

  def __init__(self, dockerfile_dir=None, repo=None, tag=None, nocache=False,
               rm=True):
    """Initializer for Image.

    Args:
      dockerfile_dir: str, Path to the directory with the Dockerfile.
      repo: str, Repository name to be applied to the image in case of
          successful build.
      tag: str, Repository tag to be applied to the image in case of successful
          build.
      nocache: boolean, True if cache should not be used when building the
          image.
      rm: boolean, True if intermediate images should be removed after a
          successful build. Default value is set to True because this is the
          default value used by "docker build" command.
    """
    self._dockerfile_dir = dockerfile_dir
    self._repo = repo
    self._tag = tag
    self._nocache = nocache
    self._rm = rm
    # Will be set during Build() method.
    self._id = None

  @property
  def dockerfile_dir(self):
    """Returns the directory the image is to be built from."""
    return self._dockerfile_dir

  @property
  def id(self):
    """Returns 64 hexadecimal digit string identifying the image."""
    # Might also be a first 12-characters shortcut.
    return self._id

  @property
  def repo(self):
    """Returns image repo string."""
    return self._repo

  @property
  def tag(self):
    """Returns image tag string."""
    return self._tag

  @property
  def tagged_repo(self):
    """Returns image repo string with tag, if it exists."""
    return '{0}:{1}'.format(self.repo, self.tag) if self.tag else self.repo
