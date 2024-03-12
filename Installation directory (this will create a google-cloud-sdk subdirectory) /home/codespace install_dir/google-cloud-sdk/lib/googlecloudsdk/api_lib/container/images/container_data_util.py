# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Utilities for the container data model."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class ImageSummary(object):
  """ImageSummary is a container class whose structure creates command output.
  """

  def __init__(self, registry, repository, digest):
    self.fully_qualified_digest = (
        '{registry}/{repository}@{digest}'.format(
            registry=registry,
            repository=repository,
            digest=digest))
    self.registry = registry
    self.repository = repository
    self.digest = digest


class ContainerData(object):
  """ContainerData objects get returned from a command for formatted output.
  """

  def __init__(self, registry, repository, digest):
    self.image_summary = ImageSummary(registry, repository, digest)
