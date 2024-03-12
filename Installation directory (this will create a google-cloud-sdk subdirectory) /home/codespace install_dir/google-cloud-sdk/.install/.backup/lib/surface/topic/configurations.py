# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Gcloud named configuration files supplementary help."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class TestingArgFiles(base.TopicCommand):
  """Supplementary help for named configurations.

  gcloud properties can be stored in *named configurations*, which
  are collections of key-value pairs that influence the behavior of
  gcloud.

  Named configurations are intended to be an advanced feature,
  and you can probably ignore them entirely if you only work with one
  project.

  Properties that are commonly stored in configurations include
  default Google Compute Engine zone, verbosity level, project ID, and
  active user or service account. Configurations allow you to define
  and enable these and other settings together as a group.

  Configuration data is typically stored in $HOME/.config/gcloud,
  you can override this location by setting the environment variable
  CLOUDSDK_CONFIG. This can be useful if $HOME points to a read only
  filesystem or you are running commands inside docker.

  Configurations are especially useful if you:
    - Work with multiple projects. You can create a separate
      configuration for each project.
    - Use multiple accounts, for example, a user account and a
      service account, etc.
    - Perform generally orthogonal tasks (work on an appengine app in
      project foo, administer a Google Compute Engine cluster in zone
      user-central-1a, manage the network configurations for region
      asia-east-1, etc.)

  Property information stored in named configurations are readable by
  all gcloud commands and may be modified by `gcloud config set`
  and `gcloud config unset`.

  # Creating configurations

  Named configurations may be defined by users or built into gcloud.

  User defined configurations have lowercase names, such as
  'johndoe', 'default', 'jeff-staging', or 'foo2'.  These are defined
  by the following regular expression: ```^[a-z][-a-z0-9]*$```

  Additionally there is a builtin configuration named NONE that has
  no properties set.

  The easiest way to create a brand new configuration is by
  running

    $ gcloud init

  This will guide you through setting up your first named configuration,
  creating a new named configuration, or reinitializing an existing
  named configuration. (Note: reinitializing an existing configuration
  will remove all its existing properties!)

  You can create a new empty configuration with

    $ gcloud config configurations create my-config

  # Using configurations

  gcloud may have at most one *active* configuration which provides
  property values.  Inactive configurations have no effect on
  gcloud executions.

  You can activate a configuration with

    $ gcloud config configurations activate my-config

  To display the path of the active configuration, run:

    $ gcloud info --format="get(config.paths.active_config_path)"

  Note that changes to your OS login, Google Cloud Platform account or project
  could change the path.

  You can view and change the properties of your active configuration
  using the following commands:

    $ gcloud config list
    $ gcloud config set

  Additionally, commands under `gcloud config configurations`
  allow you to to list, activate, describe, and delete configurations
  that may or may not be active.

  You can activate a configuration for a single gcloud invocation using
  flag, `--configuration my-config`, or environment variable
  `CLOUDSDK_ACTIVE_CONFIG_NAME=my-config`.

  ## AVAILABLE PROPERTIES

  {properties}
  """

  detailed_help = {'properties': properties.VALUES.GetHelpString()}
