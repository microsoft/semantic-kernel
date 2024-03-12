# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utilities for calling the Metastore API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions as core_exceptions

METASTORE_API_NAME = 'metastore'
METASTORE_ALPHA_API_VERSION = 'v1alpha'
METASTORE_BETA_API_VERSION = 'v1beta'
METASTORE_GA_API_VERSION = 'v1'


class Error(core_exceptions.Error):
  """Class for errors raised by Metastore API."""


class OperationError(Error):
  """Class for errors raised when a polled operation completes with an error."""

  def __init__(self, operation_name, description):
    super(OperationError, self).__init__('Operation [{}] failed: {}'.format(
        operation_name, description))


class ServiceDeleteError(Error):
  """Class for errors raised when deleting a service."""


class FederationDeleteError(Error):
  """Class for errors raised when deleting a federation."""


class AlterLocationError(Error):
  """Class for errors raised when altering metadata resource location."""


class MoveTableToDatabaseError(Error):
  """Class for errors raised when moving table to database."""


class QueryMetadataError(Error):
  """Class for errors raised when querying metadata."""


def GetApiVersion(release_track=base.ReleaseTrack.GA):
  if release_track == base.ReleaseTrack.ALPHA:
    return METASTORE_ALPHA_API_VERSION
  elif release_track == base.ReleaseTrack.BETA:
    return METASTORE_BETA_API_VERSION
  else:
    return METASTORE_GA_API_VERSION


def GetMessagesModule(release_track=base.ReleaseTrack.GA):
  return apis.GetMessagesModule(METASTORE_API_NAME,
                                GetApiVersion(release_track=release_track))


def GetClientInstance(release_track=base.ReleaseTrack.GA):
  return apis.GetClientInstance(METASTORE_API_NAME,
                                GetApiVersion(release_track=release_track))
