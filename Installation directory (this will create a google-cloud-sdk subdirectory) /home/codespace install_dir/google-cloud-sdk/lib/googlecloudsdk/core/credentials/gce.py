# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Fetching GCE metadata."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import threading

from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import gce_cache
from googlecloudsdk.core.credentials import gce_read
from googlecloudsdk.core.util import retry

from six.moves import urllib


# Cloudtops are assigned a common service account in order to use some identity
# management APIs in GCE. Unfortunately, gcloud reports this account. The shared
# service account should be ignored. (see go/cloudtop-faq#miscellaneous)
CLOUDTOP_COMMON_SERVICE_ACCOUNT = 'insecure-cloudtop-shared-user@cloudtop-prod.google.com.iam.gserviceaccount.com'


class Error(Exception):
  """Exceptions for the gce module."""


class MetadataServerException(Error):
  """Exception for when the metadata server cannot be reached."""


class CannotConnectToMetadataServerException(MetadataServerException):
  """Exception for when the metadata server cannot be reached."""


class MissingAudienceForIdTokenError(Error):
  """Exception for when audience is missing from ID token minting call."""


@retry.RetryOnException(max_retrials=3)
def _ReadNoProxyWithCleanFailures(
    uri,
    http_errors_to_ignore=(),
    timeout=properties.VALUES.compute.gce_metadata_read_timeout_sec.GetInt()):
  """Reads data from a URI with no proxy, yielding cloud-sdk exceptions."""
  try:
    return gce_read.ReadNoProxy(uri, timeout)
  except urllib.error.HTTPError as e:
    if e.code in http_errors_to_ignore:
      return None
    if e.code == 403:
      raise MetadataServerException(
          'The request is rejected. Please check if the metadata server is '
          'concealed.\n'
          'See https://cloud.google.com/kubernetes-engine/docs/how-to/protecting-cluster-metadata#concealment '
          'for more information about metadata server concealment.')
    raise MetadataServerException(e)
  except urllib.error.URLError as e:
    raise CannotConnectToMetadataServerException(e)


def _HandleMissingMetadataServer(return_list=False):
  """Handles when the metadata server is missing and resets the caches.

  If you move gcloud from one environment to another, it might still think it
  in on GCE from a previous invocation (which would result in a crash).
  Instead of crashing, we ignore the error and just update the cache.

  Args:
    return_list: True to return [] instead of None as the default empty answer.

  Returns:
    The value the underlying method would return.
  """

  #  pylint: disable=missing-docstring
  def _Wrapper(f):

    def Inner(self, *args, **kwargs):
      try:
        return f(self, *args, **kwargs)
      except CannotConnectToMetadataServerException:
        with _metadata_lock:
          self.connected = gce_cache.ForceCacheRefresh()
        return [] if return_list else None

    return Inner

  return _Wrapper


class _GCEMetadata(object):
  """Class for fetching GCE metadata.

  Attributes:
      connected: bool, True if the metadata server is available.
  """

  def __init__(self):
    self.connected = gce_cache.GetOnGCE()

  @_HandleMissingMetadataServer()
  def DefaultAccount(self):
    """Get the default service account for the host GCE instance.

    Fetches GOOGLE_GCE_METADATA_DEFAULT_ACCOUNT_URI and returns its contents.

    Raises:
      CannotConnectToMetadataServerException: If the metadata server
          cannot be reached.
      MetadataServerException: If there is a problem communicating with the
          metadata server.

    Returns:
      str, The email address for the default service account. None if not on a
          GCE VM, or if there are no service accounts associated with this VM.
    """

    if not self.connected:
      return None

    account = _ReadNoProxyWithCleanFailures(
        gce_read.GOOGLE_GCE_METADATA_DEFAULT_ACCOUNT_URI,
        http_errors_to_ignore=(404,),
    )
    if account == CLOUDTOP_COMMON_SERVICE_ACCOUNT:
      return None
    return account

  @_HandleMissingMetadataServer()
  def Project(self):
    """Get the project that owns the current GCE instance.

    Fetches GOOGLE_GCE_METADATA_PROJECT_URI and returns its contents.

    Raises:
      CannotConnectToMetadataServerException: If the metadata server
          cannot be reached.
      MetadataServerException: If there is a problem communicating with the
          metadata server.

    Returns:
      str, The project ID for the current active project. None if no project is
          currently active.
    """

    if not self.connected:
      return None

    project = _ReadNoProxyWithCleanFailures(
        gce_read.GOOGLE_GCE_METADATA_PROJECT_URI)
    if project:
      return project
    return None

  @_HandleMissingMetadataServer(return_list=True)
  def Accounts(self):
    """Get the list of service accounts available from the metadata server.

    Returns:
      [str], The list of accounts. [] if not on a GCE VM.

    Raises:
      CannotConnectToMetadataServerException: If no metadata server is present.
      MetadataServerException: If there is a problem communicating with the
          metadata server.
    """

    if not self.connected:
      return []

    accounts_listing = _ReadNoProxyWithCleanFailures(
        gce_read.GOOGLE_GCE_METADATA_ACCOUNTS_URI + '/')
    accounts_lines = accounts_listing.split()
    accounts = []
    for account_line in accounts_lines:
      account = account_line.strip('/')
      if account == 'default' or account == CLOUDTOP_COMMON_SERVICE_ACCOUNT:
        continue
      accounts.append(account)
    return accounts

  @_HandleMissingMetadataServer()
  def Zone(self):
    """Get the name of the zone containing the current GCE instance.

    Fetches GOOGLE_GCE_METADATA_ZONE_URI, formats it, and returns its contents.

    Raises:
      CannotConnectToMetadataServerException: If the metadata server
          cannot be reached.
      MetadataServerException: If there is a problem communicating with the
          metadata server.

    Returns:
      str, The short name (e.g., us-central1-f) of the zone containing the
          current instance.
      None if not on a GCE VM.
    """

    if not self.connected:
      return None

    # zone_path will be formatted as, for example,
    # projects/123456789123/zones/us-central1-f
    # and we want to return only the last component.
    zone_path = _ReadNoProxyWithCleanFailures(
        gce_read.GOOGLE_GCE_METADATA_ZONE_URI)
    return zone_path.split('/')[-1]

  def Region(self):
    """Get the name of the region containing the current GCE instance.

    Fetches GOOGLE_GCE_METADATA_ZONE_URI, extracts the region associated
    with the zone, and returns it.  Extraction is based property that
    zone names have form <region>-<zone> (see https://cloud.google.com/
    compute/docs/zones) and an assumption that <zone> contains no hyphens.

    Raises:
      CannotConnectToMetadataServerException: If the metadata server
          cannot be reached.
      MetadataServerException: If there is a problem communicating with the
          metadata server.

    Returns:
      str, The short name (e.g., us-central1) of the region containing the
          current instance.
      None if not on a GCE VM.
    """

    if not self.connected:
      return None

    # Zone will be formatted as (e.g.) us-central1-a, and we want to return
    # everything ahead of the last hyphen.
    zone = self.Zone()
    return '-'.join(zone.split('-')[:-1]) if zone else None

  @_HandleMissingMetadataServer()
  def GetIdToken(self,
                 audience,
                 token_format='standard',
                 include_license=False):
    """Get a valid identity token on the host GCE instance.

    Fetches GOOGLE_GCE_METADATA_ID_TOKEN_URI and returns its contents.

    Args:
      audience: str, target audience for ID token.
      token_format: str, Specifies whether or not the project and instance
        details are included in the identity token. Choices are "standard",
        "full".
      include_license: bool, Specifies whether or not license codes for images
        associated with GCE instance are included in their identity tokens

    Raises:
      CannotConnectToMetadataServerException: If the metadata server
          cannot be reached.
      MetadataServerException: If there is a problem communicating with the
          metadata server.
      MissingAudienceForIdTokenError: If audience is missing.

    Returns:
      str, The id token or None if not on a CE VM, or if there are no
      service accounts associated with this VM.
    """

    if not self.connected:
      return None

    if not audience:
      raise MissingAudienceForIdTokenError()

    include_license = 'TRUE' if include_license else 'FALSE'
    return _ReadNoProxyWithCleanFailures(
        gce_read.GOOGLE_GCE_METADATA_ID_TOKEN_URI.format(
            audience=audience, format=token_format, licenses=include_license),
        http_errors_to_ignore=(404,))

  @_HandleMissingMetadataServer()
  def UniverseDomain(self):
    """Get the universe domain of the current GCE instance.

    If the GCE metadata server universe domain endpoint is not found, or the
    endpoint returns an empty string, return the default universe domain
    (googleapis.com); otherwise return the fetched universe domain value, or
    raise an exception if the request fails.

    Raises:
      CannotConnectToMetadataServerException: If the metadata server
          cannot be reached.
      MetadataServerException: If there is a problem communicating with the
          metadata server.

    Returns:
      str, The universe domain value from metadata server. None if not on GCE.
    """

    if not self.connected:
      return None

    universe_domain = _ReadNoProxyWithCleanFailures(
        gce_read.GOOGLE_GCE_METADATA_UNIVERSE_DOMAIN_URI,
        http_errors_to_ignore=(404,),
    )
    if not universe_domain:
      return properties.VALUES.core.universe_domain.default
    return universe_domain


_metadata = None
_metadata_lock = threading.Lock()


def Metadata():
  """Get a singleton for the GCE metadata class.

  Returns:
    _GCEMetadata, An object used to collect information from the GCE metadata
    server.
  """
  with _metadata_lock:
    global _metadata
    if not _metadata:
      _metadata = _GCEMetadata()
  return _metadata
