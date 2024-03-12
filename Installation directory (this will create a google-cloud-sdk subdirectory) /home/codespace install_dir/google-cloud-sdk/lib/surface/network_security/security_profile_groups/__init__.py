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
"""Command group for Network Security Security Profile Groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class SecurityProfileGroups(base.Group):
  """Manage Network Security - Security Profile Groups.

  Manage Network Security - Security Profile Groups.

  ## EXAMPLES

  To create a Security Profile Group with the name `my-security-profile-group`
  (Either a fully specified path or `--location` and `--organization` flags for
  SPG should be specified), `--threat-prevention-profile` `my-security-profile`
  and optional description as `optional description`, run:

      $ {command} create my-security-profile-group --organization=1234
      --location=global
      --threat-prevention-profile=`organizations/1234/locations/global/securityProfiles/my-security-profile`
      --description='optional description'

  To delete an Security Profile Group called `my-security-profile-group` (Either
  a fully specified path or `--location` and `--organization` flags for SPG
  should be specified) run:

      $ {command} delete my-security-profile-group --organization=1234
      --location=global

  To show details of a Security Profile Group named `my-security-profile-group`
  (Either a fully specified path or `--location` and `--organization` flags for
  SPG should be specified) run:

      $ {command} describe my-security-profile-group --organization=1234
      --location=global

  To list Security Profile Groups in specifed location and organization, run:

      $ {command} list --location=global

  To update an SPG with new Threat prevention profile `my-new-security-profile`
  (Either a fully specified path or `--location` and `--organization` flags for
  SPG should be specified), run:

      $ {command} update my-security-profile-group --organization=1234
      --location=global
      --threat-prevention-profile=`organizations/1234/locations/global/securityProfiles/my-new-security-profile`
      --description='New Security Profile of type threat prevention'
  """
  category = base.NETWORK_SECURITY_CATEGORY
