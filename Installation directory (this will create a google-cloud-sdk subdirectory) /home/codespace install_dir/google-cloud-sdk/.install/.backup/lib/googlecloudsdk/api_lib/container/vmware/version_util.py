# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utilities for Anthos On-Prem API for VMware platform version parsing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re


class Version:
  """Anthos On-Prem VMware platform version parsing and comparison library."""

  def __init__(self, version: str):
    self.original = version
    self.major = 0
    self.minor = 0
    self.patch = 0
    self.gke_patch = 0

    self.parse_version(version)

  def parse_version(self, version: str):
    """Parses the input version.

    Accept versions of form such as 1.15.2-gke.0. Every version field must be
    specified. Use self.original whenever passing the version value to the
    server to avoid distorting user intention.

    Args:
      version: str
    """
    # TODO(b/280446610)
    # Update version parsing function when the version style changes.
    version_pattern = re.compile(r'(\d+)\.(\d+)\.(\d+)-gke\.(\d+)')
    version_match = version_pattern.match(version)
    # The provided version string should match the pattern as a whole.
    if not version_match or version_match.group() != version:
      raise ValueError(
          'Invalid version: {}, example valid version: {}'.format(
              version, '1.15.1-gke.2'
          )
      )

    self.original = version
    self.major = int(version_match.group(1))
    self.minor = int(version_match.group(2))
    self.patch = int(version_match.group(3))
    self.gke_patch = int(version_match.group(4))

  def feature_available(self, feature_version: str) -> bool:
    """Check whether the current version has the feature available.

    Args:
      feature_version: The lowest version that the feature is available.

    Returns:
      bool
    """
    return not (self < Version(feature_version))

  def print_version(self):
    return 'major: {}, minor: {}, patch: {}, gke_patch: {}'.format(
        self.major, self.minor, self.patch, self.gke_patch
    )

  def __lt__(self, other_version):
    if self.major < other_version.major:
      return True
    elif self.major > other_version.major:
      return False

    if self.minor < other_version.minor:
      return True
    elif self.minor > other_version.minor:
      return False

    if self.patch < other_version.patch:
      return True
    elif self.patch > other_version.patch:
      return False

    if self.gke_patch < other_version.gke_patch:
      return True
    elif self.gke_patch > other_version.gke_patch:
      return False

    return False

  def __eq__(self, other_version):
    return (
        self.major == other_version.major
        and self.minor == other_version.minor
        and self.patch == other_version.patch
        and self.gke_patch == other_version.gke_patch
    )

  def __str__(self):
    return self.original

  def __repr__(self):
    return self.original
