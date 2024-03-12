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
"""Command sub-group for Security Profiles Threat Prevention Profile."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ThreatPrevention(base.Group):
  """Manage Security Profiles - Threat Prevention Profile.

  Manage Security Profiles - Threat Prevention Profile.

  ## EXAMPLES

  To create a Security Profile with the name `my-security-profile` which
  includes location as global or region specifed and organization ID, optional
  description as `New Security Profile`, run:

    $ {command} create my-security-profile  --description="New Security Profile"

  To add an override, run:

    $ {command} add-override my-security-profile --severities=MEDIUM
    --action=ALLOW

    `my-security-profile` is the name of the Security Profile in the
    format organizations/{organizationID}/locations/{location}/securityProfiles/
    {security_profile_id} where organizationID is the organization ID to which
    the changes should apply, location either global or region specified and
    security_profile_id the Security Profile Identifier.

  To update an override, run:

    $ {command} update-override my-security-profile --severities=MEDIUM
    --action=ALLOW

    `my-security-profile` is the name of the Security Profile in the
    format organizations/{organizationID}/locations/{location}/securityProfiles/
    {security_profile_id} where organizationID is the organization ID to which
    the changes should apply, location either global or region specified and
    security_profile_id the Security Profile Identifier.

  To list overrides, run:

    $ {command} list-overrides my-security-profile

    `my-security-profile` is the name of the Security Profile in the
    format organizations/{organizationID}/locations/{location}/securityProfiles/
    {security_profile_id} where organizationID is the organization ID to which
    the changes should apply, location either global or region specified and
    security_profile_id the Security Profile Identifier.

  To delete an override, run:

    $ {command} delete-override my-security-profile --severities=MEDIUM

    `my-security-profile` is the name of the Security Profile in the
    format organizations/{organizationID}/locations/{location}/securityProfiles/
    {security_profile_id} where organizationID is the organization ID to which
    the changes should apply, location either global or region specified and
    security_profile_id the Security Profile Identifier.

  To list Security Profiles in specifed location and organization, run:

    $ {command} list --location=global

  To delete a Security Profile called `my-security-profile` which includes
  location as global or region specifed and organization ID, run:

      $ {command} delete my-security-profile
  """
  category = base.NETWORK_SECURITY_CATEGORY
