# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Common utility functions for Image Version validation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import re

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.composer import image_versions_util as image_version_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import flags
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.core.util import semver

# Envs must be running at least this version of Composer to be upgradeable.
MIN_UPGRADEABLE_COMPOSER_VER = '1.0.0'

# Required for version comparisons
COMPOSER_LATEST_VERSION_PLACEHOLDER = '2.1.12'

UpgradeValidator = collections.namedtuple('UpgradeValidator',
                                          ['upgrade_valid', 'error'])


class InvalidImageVersionError(command_util.Error):
  """Class for errors raised when an invalid image version is encountered."""


class _ImageVersionItem(object):
  """Class used to dissect and analyze image version components and strings."""

  def __init__(self, image_ver=None, composer_ver=None, airflow_ver=None):
    image_version_regex = r'^composer-(\d+(?:(?:\.\d+\.\d+(?:-[a-z]+\.\d+)?)?)?|latest)-airflow-(\d+(?:\.\d+(?:\.\d+)?)?)'
    composer_version_alias_regex = r'^(\d+|latest)$'
    airflow_version_alias_regex = r'^(\d+|\d+\.\d+)$'

    if image_ver is not None:
      iv_parts = re.findall(image_version_regex, image_ver)[0]
      self.composer_ver = iv_parts[0]
      self.airflow_ver = iv_parts[1]

    if composer_ver is not None:
      self.composer_ver = composer_ver

    if airflow_ver is not None:
      self.airflow_ver = airflow_ver

    # Determines the state of aliases
    self.composer_contains_alias = re.match(composer_version_alias_regex,
                                            self.composer_ver)
    self.airflow_contains_alias = re.match(airflow_version_alias_regex,
                                           self.airflow_ver)

  def GetImageVersionString(self):
    return 'composer-{}-airflow-{}'.format(self.composer_ver, self.airflow_ver)


def ListImageVersionUpgrades(env_ref, release_track=base.ReleaseTrack.GA):
  """List of available image version upgrades for provided env_ref."""
  env_details = environments_api_util.Get(env_ref, release_track)
  proj_location_ref = env_ref.Parent()
  cur_image_version_id = env_details.config.softwareConfig.imageVersion
  cur_python_version = env_details.config.softwareConfig.pythonVersion

  return _BuildUpgradeCandidateList(proj_location_ref, cur_image_version_id,
                                    cur_python_version, release_track)


def IsValidImageVersionUpgrade(cur_image_version_str,
                               image_version_id):
  """Checks if image version candidate is a valid upgrade for environment."""

  # Checks for the use of an alias and confirms that a valid airflow upgrade has
  # been requested.
  cur_image_ver = _ImageVersionItem(
      image_ver=cur_image_version_str)

  is_composer3 = IsVersionComposer3Compatible(
      cur_image_version_str
  )
  if not is_composer3 and not (
      CompareVersions(MIN_UPGRADEABLE_COMPOSER_VER, cur_image_ver.composer_ver)
      <= 0
  ):
    raise InvalidImageVersionError(
        'This environment does not support upgrades.')
  return _ValidateCandidateImageVersionId(
      cur_image_version_str,
      image_version_id)


def ImageVersionFromAirflowVersion(new_airflow_version, cur_image_version=None):
  """Converts airflow-version string into a image-version string."""

  is_composer3 = cur_image_version and IsVersionComposer3Compatible(
      cur_image_version
  )
  composer_ver = (
      _ImageVersionItem(cur_image_version).composer_ver
      if is_composer3
      else 'latest'
  )

  return _ImageVersionItem(
      composer_ver=composer_ver,
      airflow_ver=new_airflow_version).GetImageVersionString()


def IsImageVersionStringComposerV1(image_version):
  """Checks if string composer-X.Y.Z-airflow-A.B.C is Composer v1 version."""
  return image_version is not None and (
      image_version.startswith('composer-1.')
      or image_version.startswith('composer-1-')
  )


def IsDefaultImageVersion(image_version):
  return image_version is None or image_version.startswith('composer-latest')


def BuildDefaultComposerVersionWarning(image_version, airflow_version):
  """Builds warning message about using default Composer version."""
  message = (
      '{} resolves to Cloud Composer current default version, which is'
      ' presently Composer 2 and is subject to'
      ' further changes in the future. Consider using'
      ' --image-version=composer-A-airflow-X[.Y[.Z]]. More info at'
      ' https://cloud.google.com/composer/docs/concepts/versioning/composer-versioning-overview#version-aliases'
  )
  if airflow_version:
    return message.format('Using --airflow-version=X[.Y[.Z]]')
  if image_version:
    return message.format(
        'Using --image-version=composer-latest-airflow-X[.Y[.Z]]'
    )
  return message.format('Not defining --image-version')


def _CompareVersions(v1, v2):
  """Compares versions."""
  if v1 == v2:
    return 0
  elif v1 > v2:
    return 1
  else:
    return -1


def CompareLooseVersions(v1, v2):
  """Compares loose version strings.

  Args:
    v1: first loose version string
    v2: second loose version string

  Returns:
    Value == 1 when v1 is greater; Value == -1 when v2 is greater; otherwise 0.
  """
  v1, v2 = _VersionStrToLooseVersion(v1), _VersionStrToLooseVersion(v2)
  return _CompareVersions(v1, v2)


def CompareVersions(v1, v2):
  """Compares semantic version strings.

  Args:
    v1: first semantic version string
    v2: second semantic version string

  Returns:
    Value == 1 when v1 is greater; Value == -1 when v2 is greater; otherwise 0.
  """
  v1, v2 = _VersionStrToSemanticVersion(v1), _VersionStrToSemanticVersion(v2)
  return _CompareVersions(v1, v2)


def IsVersionComposer3Compatible(image_version):
  """Checks if given `image_version` is compatible with Composer 3.

  Args:
    image_version: image version str that includes Composer version.

  Returns:
    True if Composer version is greater than or equal to 3.0.0 or its prerelease
    variant, otherwise False.
  """

  if image_version:
    version_item = _ImageVersionItem(image_version)
    if version_item and version_item.composer_ver:
      composer_version = version_item.composer_ver
      if composer_version == '3':
        return True
      if composer_version == 'latest':
        composer_version = COMPOSER_LATEST_VERSION_PLACEHOLDER
      return IsVersionInRange(
          composer_version, flags.MIN_COMPOSER3_VERSION, None,
          True)
  return False


def IsVersionAirflowCommandsApiCompatible(image_version):
  """Checks if given `version` is compatible with Composer Airflow Commands API.

  Args:
    image_version: image version str that includes Composer version.

  Returns:
    True if Composer version is compatible with Aiflow Commands API,
    otherwise False.
  """

  if image_version:
    version_item = _ImageVersionItem(image_version)
    if version_item and version_item.composer_ver:
      composer_version = version_item.composer_ver
      return IsVersionInRange(
          composer_version,
          flags.MIN_COMPOSER_RUN_AIRFLOW_CLI_VERSION,
          None,
          True,
      )
  return False


def IsVersionTriggererCompatible(image_version):
  """Checks if given `version` is compatible with triggerer .

  Args:
    image_version: image version str that includes airflow version.

  Returns:
    True if given airflow version is compatible with Triggerer(>=2.2.x)
    and Composer version is >=2.0.31 otherwise False
  """

  if image_version:
    version_item = _ImageVersionItem(image_version)
    # Triggerer is supported in Composer 3.
    if IsVersionComposer3Compatible(image_version):
      return True
    if version_item and version_item.airflow_ver and version_item.composer_ver:
      airflow_version = version_item.airflow_ver
      composer_version = version_item.composer_ver
      if composer_version == 'latest':
        composer_version = COMPOSER_LATEST_VERSION_PLACEHOLDER
      return IsVersionInRange(
          composer_version, flags.MIN_TRIGGERER_COMPOSER_VERSION, None, True
      ) and IsVersionInRange(
          airflow_version, flags.MIN_TRIGGERER_AIRFLOW_VERSION, None, True
      )
  return False


def IsVersionInRange(version, range_from, range_to, loose=False):
  """Checks if given `version` is in range of (`range_from`, `range_to`).

  Args:
    version: version to check
    range_from: left boundary of range (inclusive), if None - no boundary
    range_to: right boundary of range (exclusive), if None - no boundary
    loose: if true use LooseVersion to compare, use SemVer otherwise

  Returns:
    True if given version is in range, otherwise False.
  """
  compare_fn = CompareLooseVersions if loose else CompareVersions
  return ((range_from is None or compare_fn(range_from, version) <= 0) and
          (range_to is None or compare_fn(version, range_to) < 0))


def _BuildUpgradeCandidateList(location_ref,
                               image_version_id,
                               python_version,
                               release_track=base.ReleaseTrack.GA):
  """Builds a list of eligible image version upgrades."""
  image_version_service = image_version_api_util.ImageVersionService(
      release_track)
  image_version_item = _ImageVersionItem(image_version_id)

  available_upgrades = []
  # Checks if current composer version meets minimum threshold.
  if (CompareVersions(MIN_UPGRADEABLE_COMPOSER_VER,
                      image_version_item.composer_ver) <= 0):
    # If so, builds list of eligible upgrades.
    for version in image_version_service.List(location_ref):
      if _ValidateCandidateImageVersionId(
          image_version_id, version.imageVersionId
      ).upgrade_valid and (
          not python_version
          or python_version in version.supportedPythonVersions
      ):
        available_upgrades.append(version)
  else:
    raise InvalidImageVersionError(
        'This environment does not support upgrades.')

  return available_upgrades


def _ValidateCandidateImageVersionId(current_image_version_id,
                                     candidate_image_version_id):
  """Determines if candidate version is a valid upgrade from current version.

  Args:
    current_image_version_id: current image version
    candidate_image_version_id: image version requested for upgrade

  Returns:
    UpgradeValidator namedtuple containing True and None error message if
    given version upgrade between given versions is valid, otherwise False and
    error message with problems description.
  """
  upgrade_validator = UpgradeValidator(True, None)
  if current_image_version_id == candidate_image_version_id:
    error_message = ('Existing and requested image versions are equal ({}). '
                     'Select image version newer than current to perform '
                     'upgrade.').format(current_image_version_id)
    upgrade_validator = UpgradeValidator(False, error_message)

  parsed_curr = _ImageVersionItem(image_ver=current_image_version_id)
  parsed_cand = _ImageVersionItem(image_ver=candidate_image_version_id)

  # Checks Composer versions.
  if upgrade_validator.upgrade_valid and not parsed_cand.composer_contains_alias:
    upgrade_validator = _IsVersionUpgradeCompatible(parsed_curr.composer_ver,
                                                    parsed_cand.composer_ver,
                                                    'Composer')

  # Checks Airflow versions.
  if upgrade_validator.upgrade_valid and not parsed_cand.airflow_contains_alias:
    upgrade_validator = _IsVersionUpgradeCompatible(parsed_curr.airflow_ver,
                                                    parsed_cand.airflow_ver,
                                                    'Airflow')

  # Leaves the validity check to the Composer backend request validation.
  return upgrade_validator


def _VersionStrToSemanticVersion(version_str):
  """Parses version_str into semantic version."""
  return semver.SemVer(version_str)


def _VersionStrToLooseVersion(version_str):
  """Parses version_str into loose version."""
  return semver.LooseVersion(version_str)


def _IsVersionUpgradeCompatible(cur_version, candidate_version,
                                image_version_part):
  """Validates whether version candidate is greater than or equal to current.

  Applicable both for Airflow and Composer version upgrades. Composer supports
  both Airflow and self MINOR and PATCH-level upgrades.

  Args:
    cur_version: current 'a.b.c' version
    candidate_version: candidate 'x.y.z' version
    image_version_part: part of image to be validated. Must be either 'Airflow'
      or 'Composer'

  Returns:
    UpgradeValidator namedtuple containing boolean value whether selected image
    version component is valid for upgrade and eventual error message if it is
    not.
  """
  assert image_version_part in ['Airflow', 'Composer']
  curr_semantic_version = _VersionStrToSemanticVersion(cur_version)
  cand_semantic_version = _VersionStrToSemanticVersion(candidate_version)

  if curr_semantic_version > cand_semantic_version:
    error_message = ('Upgrade cannot decrease {composer_or_airflow1}\'s '
                     'version. Current {composer_or_airflow2} version: '
                     '{cur_version}, requested {composer_or_airflow3} version: '
                     '{req_version}.').format(
                         composer_or_airflow1=image_version_part,
                         composer_or_airflow2=image_version_part,
                         cur_version=cur_version,
                         composer_or_airflow3=image_version_part,
                         req_version=candidate_version)
    return UpgradeValidator(False, error_message)

  if curr_semantic_version.major != cand_semantic_version.major:
    error_message = ('Upgrades between different {}\'s major versions are not'
                     ' supported. Current major version {}, requested major '
                     'version {}.').format(image_version_part,
                                           curr_semantic_version.major,
                                           cand_semantic_version.major)
    return UpgradeValidator(False, error_message)

  return UpgradeValidator(True, None)
