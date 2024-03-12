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

"""The super-group for the update manager."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import os

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import platforms


class Repositories(base.Group):
  """Manage additional component repositories for Trusted Tester programs."""

  detailed_help = {
      'DESCRIPTION': """\
          List, add, and remove component repositories for Trusted Tester
          programs.  If you are not participating in a Trusted Tester program,
          these commands are not necessary for updating your Google Cloud CLI
          installation.

          If you are participating in a Trusted Tester program, you will be
          instructed on the location of repositories that you should add.
          These commands allow you to manage the set of repositories you have
          registered.

          Once you have a repository registered, the component manager will use
          that location to locate new Google Cloud CLI components that are
          available, or possibly different versions of existing components that
          can be installed.

          If you want to revert to a standard version of the Google Cloud CLI at
          any time, you may remove all repositories and then run:

            $ gcloud components update

          to revert to a standard installation.
      """,
  }
