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

"""Provide commands for managing SSL certificates of Cloud SQL instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions

_DEPRECATION_WARNING = (
    '`gcloud sql ssl-certs` is deprecated. Use `gcloud sql ssl client-certs` '
    'instead.')


@base.Deprecate(is_removed=False, warning=_DEPRECATION_WARNING)
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class SslCerts(base.Group):
  """Provide commands for managing SSL certificates of Cloud SQL instances.

  Provide commands for managing SSL certificates of Cloud SQL instances,
  including creating, deleting, listing, and getting information about
  certificates.
  """
  category = base.DATABASES_CATEGORY
