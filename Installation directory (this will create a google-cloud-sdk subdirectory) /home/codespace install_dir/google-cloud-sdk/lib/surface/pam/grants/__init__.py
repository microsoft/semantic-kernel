# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""The command group for the PAM Grants CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Grants(base.Group):
  """Manage PAM Grants.

     The gcloud pam grants command group lets you manage Privileged
     Access Manager (PAM) Grants.

     ## EXAMPLES

     To display the details of a grant with the name grant-name,
     run:

     $ {command} describe grant-name

     To list all grants under an entitlement,
     run:

     $ {command} list --entitlement entitlement-name

     To deny a grant with a given name and reason, run:

     $ {command} deny grant-name --reason denial-reason

     To approve a grant with a given name and reason, run:

     $ {command} approve grant-name --reason approval-reason

  """
