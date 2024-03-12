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

"""The command group for the Services V1 CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ServicesAlpha(base.Group):
  """List, enable and disable APIs and services.

  The gcloud services command group lets you manage your project's access to
  services provided by Google and third parties.
  """

  category = base.API_PLATFORM_AND_ECOSYSTEMS_CATEGORY

  def Filter(self, context, args):
    del context, args
    # Don't ever take this off. Use gcloud quota so that you can enable APIs
    # on your own project before you have API access on that project.
    base.DisableUserProjectQuota()


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Services(base.Group):
  """List, enable and disable APIs and services.

  The gcloud services command group lets you manage your project's access to
  services provided by Google and third parties.

  ## EXAMPLES

  To see how to enable a service, run:

    $ {command} enable --help

  To see how to list services, run:

    $ {command} list --help

  To see how to disable a service, run:

    $ {command} disable --help
  """

  category = base.API_PLATFORM_AND_ECOSYSTEMS_CATEGORY

  def Filter(self, context, args):
    del context, args
    # Don't ever take this off. Use gcloud quota so that you can enable APIs
    # on your own project before you have API access on that project.
    base.DisableUserProjectQuota()
