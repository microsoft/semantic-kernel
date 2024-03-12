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
"""The gcloud dlp datasources command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Datasources(base.Group):
  # pylint: disable=line-too-long
  """Cloud DLP Commands for analyzing Google Cloud data repositories.

  Cloud DLP Commands for inspecting and analyzing sensitive data in Google Cloud
  data repositories.

  See [Inspecting Storage and Databases for Sensitive Data]
  (https://cloud.google.com/dlp/docs/inspecting-storage)
  for more details.
  """
  # pylint: enable=line-too-long
