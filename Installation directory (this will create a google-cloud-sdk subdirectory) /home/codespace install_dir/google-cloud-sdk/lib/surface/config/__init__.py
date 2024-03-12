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

"""config command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Config(base.Group):
  """View and edit Google Cloud CLI properties.

  The {command} command group lets you set, view and unset properties used by
  Google Cloud CLI.

  A configuration is a set of properties that govern the behavior of `gcloud`
  and other Google Cloud CLI tools. The initial `default` configuration is set
  when `gcloud init` is run. You can create additional named configurations
  using `gcloud init` or `{command} configurations create`.

  To display the path of the active configuration along with information
  about the current `gcloud` environment, run $ gcloud info.

  To switch between configurations, use `{command} configurations activate`.

  gcloud supports several flags that have the same effect as properties in
  a configuration (for example, gcloud supports both the `--project` flag and
  `project` property). Properties differ from flags in that flags affect command
  behavior on a per-invocation basis. Properties allow you to maintain the same
  settings across command executions.

  In addition to setting properties in a configuration, and the use of flags, it
  is possible to override the value of a property with an environment variable.
  The matching environment variable for a property is of the form
  'CLOUDSDK_CATEGORY_PROPERTY'. For example, to demonstrate overriding
  the ``project'' property in the ``core'' category to ``my-project'', use a
  command like:

    $ CLOUDSDK_CORE_PROJECT=my-project gcloud config get core/project

  For more information on configurations, see `gcloud topic configurations`.

  ## AVAILABLE PROPERTIES

  {properties}
  """

  category = base.SDK_TOOLS_CATEGORY

  detailed_help = {
      'properties': properties.VALUES.GetHelpString(),
  }
