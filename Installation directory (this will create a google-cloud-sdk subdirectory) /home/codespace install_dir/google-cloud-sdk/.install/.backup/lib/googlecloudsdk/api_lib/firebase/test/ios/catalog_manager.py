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
"""A wrapper for working with the iOS Test Environment Catalog."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test import util


_MODEL_DIMENSION = 'model'
_VERSION_DIMENSION = 'version'
_LOCALE_DIMENSION = 'locale'
_ORIENTATION_DIMENSION = 'orientation'


class IosCatalogManager(object):
  """Encapsulates operations on the iOS TestEnvironmentCatalog."""

  def __init__(self, catalog=None):
    """Construct an IosCatalogManager object from a TestEnvironmentCatalog.

    Args:
      catalog: an iOS TestEnvironmentCatalog from Testing API. If it is not
        injected, the catalog is retrieved from the Testing service.

    Attributes:
      catalog: an iOS TestEnvironmentCatalog.
    """
    self.catalog = catalog or util.GetIosCatalog()
    models = self.catalog.models
    versions = self.catalog.versions
    locales = self.catalog.runtimeConfiguration.locales
    orientations = self.catalog.runtimeConfiguration.orientations

    self._model_ids = [m.id for m in models]
    self._version_ids = [v.id for v in versions]
    self._locale_ids = [l.id for l in locales]
    self._orientation_ids = [o.id for o in orientations]

    # Dimension defaults are lazily computed and cached by GetDefault* methods.
    self._default_model = None
    self._default_version = None
    self._default_locale = None
    self._default_orientation = None

  def GetDefaultModel(self):
    """Return the default model listed in the iOS environment catalog."""
    model = (self._default_model if self._default_model else
             self._FindDefaultDimension(self.catalog.models))
    if not model:
      raise exceptions.DefaultDimensionNotFoundError(_MODEL_DIMENSION)
    return model

  def GetDefaultVersion(self):
    """Return the default version listed in the iOS environment catalog."""
    version = (self._default_version if self._default_version else
               self._FindDefaultDimension(self.catalog.versions))
    if not version:
      raise exceptions.DefaultDimensionNotFoundError(_VERSION_DIMENSION)
    return version

  def GetDefaultLocale(self):
    """Return the default iOS locale."""
    locales = self.catalog.runtimeConfiguration.locales
    locale = (
        self._default_locale
        if self._default_locale else self._FindDefaultDimension(locales))
    if not locale:
      raise exceptions.DefaultDimensionNotFoundError(_LOCALE_DIMENSION)
    return locale

  def GetDefaultOrientation(self):
    """Return the default iOS orientation."""
    orientations = self.catalog.runtimeConfiguration.orientations
    orientation = (
        self._default_orientation if self._default_orientation else
        self._FindDefaultDimension(orientations))
    if not orientation:
      raise exceptions.DefaultDimensionNotFoundError(_ORIENTATION_DIMENSION)
    return orientation

  def _FindDefaultDimension(self, dimension_table):
    for dimension in dimension_table:
      if 'default' in dimension.tags:
        return dimension.id
    return None

  def ValidateDimensionAndValue(self, dim_name, dim_value):
    """Validates that a matrix dimension has a valid name and value."""
    if dim_name == _MODEL_DIMENSION:
      if dim_value not in self._model_ids:
        raise exceptions.ModelNotFoundError(dim_value)
    elif dim_name == _VERSION_DIMENSION:
      if dim_value not in self._version_ids:
        raise exceptions.VersionNotFoundError(dim_value)
    elif dim_name == _LOCALE_DIMENSION:
      if dim_value not in self._locale_ids:
        raise exceptions.LocaleNotFoundError(dim_value)
    elif dim_name == _ORIENTATION_DIMENSION:
      if dim_value not in self._orientation_ids:
        raise exceptions.OrientationNotFoundError(dim_value)
    else:
      raise exceptions.InvalidDimensionNameError(dim_name)
    return dim_value

  def ValidateXcodeVersion(self, xcode_version):
    """Validates that an Xcode version is in the TestEnvironmentCatalog."""
    if xcode_version not in [xv.version for xv in self.catalog.xcodeVersions]:
      raise exceptions.XcodeVersionNotFoundError(xcode_version)
