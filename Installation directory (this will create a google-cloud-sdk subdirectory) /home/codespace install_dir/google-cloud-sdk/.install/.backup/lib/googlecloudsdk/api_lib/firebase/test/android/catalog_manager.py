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
"""A wrapper for working with the Android Test Environment Catalog."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test import util


class AndroidCatalogManager(object):
  """Encapsulates operations on the Android TestEnvironmentCatalog."""

  def __init__(self, catalog=None):
    """Construct an AndroidCatalogManager object from a TestEnvironmentCatalog.

    Args:
      catalog: an Android TestEnvironmentCatalog from Testing API. If it is not
        injected, the catalog is retrieved from the Testing service.

    Attributes:
      catalog: an Android TestEnvironmentCatalog.
    """
    self.catalog = catalog or util.GetAndroidCatalog()
    models = self.catalog.models
    versions = self.catalog.versions
    locales = self.catalog.runtimeConfiguration.locales
    orientations = self.catalog.runtimeConfiguration.orientations

    self._model_ids = [m.id for m in models]
    self._version_ids = [v.id for v in versions]
    self._locale_ids = [l.id for l in locales]
    self._orientation_ids = [o.id for o in orientations]

    self._version_name_to_id = {v.versionString: v.id for v in versions}

    # Dimension defaults are lazily computed and cached by GetDefault* methods.
    self._default_model = None
    self._default_version = None
    self._default_locale = None
    self._default_orientation = None

  def GetDefaultModel(self):
    """Return the default model listed in the Android environment catalog."""
    model = (self._default_model if self._default_model else
             self._FindDefaultDimension(self.catalog.models))
    if not model:
      raise exceptions.DefaultDimensionNotFoundError('model')
    return model

  def GetDefaultVersion(self):
    """Return the default version listed in the Android environment catalog."""
    version = (self._default_version if self._default_version else
               self._FindDefaultDimension(self.catalog.versions))
    if not version:
      raise exceptions.DefaultDimensionNotFoundError('version')
    return version

  def GetDefaultLocale(self):
    """Return the default locale listed in the Android environment catalog."""
    locales = self.catalog.runtimeConfiguration.locales
    locale = (self._default_locale
              if self._default_locale else self._FindDefaultDimension(locales))
    if not locale:
      raise exceptions.DefaultDimensionNotFoundError('locale')
    return locale

  def GetDefaultOrientation(self):
    """Return the default orientation in the Android environment catalog."""
    orientations = self.catalog.runtimeConfiguration.orientations
    orientation = (self._default_orientation if self._default_orientation else
                   self._FindDefaultDimension(orientations))
    if not orientation:
      raise exceptions.DefaultDimensionNotFoundError('orientation')
    return orientation

  def _FindDefaultDimension(self, dimension_table):
    for dimension in dimension_table:
      if 'default' in dimension.tags:
        return dimension.id
    return None

  def ValidateDimensionAndValue(self, dim_name, dim_value):
    """Validates that a matrix dimension has a valid name and value."""
    if dim_name == 'model':
      if dim_value not in self._model_ids:
        raise exceptions.ModelNotFoundError(dim_value)
    elif dim_name == 'locale':
      if dim_value not in self._locale_ids:
        raise exceptions.LocaleNotFoundError(dim_value)
    elif dim_name == 'orientation':
      if dim_value not in self._orientation_ids:
        raise exceptions.OrientationNotFoundError(dim_value)
    elif dim_name == 'version':
      if dim_value not in self._version_ids:
        # Users are allowed to specify either version name or version ID.
        version_id = self._version_name_to_id.get(dim_value, None)
        if not version_id:
          raise exceptions.VersionNotFoundError(dim_value)
        return version_id
    else:
      raise exceptions.InvalidDimensionNameError(dim_name)
    return dim_value
