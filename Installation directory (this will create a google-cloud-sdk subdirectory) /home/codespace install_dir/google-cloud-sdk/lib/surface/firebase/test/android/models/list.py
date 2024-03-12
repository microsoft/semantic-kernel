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

"""The 'gcloud firebase test android models list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


DETAILED_HELP = {
    'EXAMPLES': """
    To list all models which are available for testing, run:

      $ {command}

    To list all models made by Samsung, run:

      $ {command} --filter=Samsung

    To list all virtual device models, run:

      $ {command} --filter=virtual
    """,
}


class List(base.ListCommand):
  """List all Android models available for testing."""

  @staticmethod
  def Args(parser):
    """Method called by Calliope to register flags for this command.

    Args:
      parser: An argparse parser used to add arguments that follow this
          command in the CLI. Positional arguments are allowed.
    """
    parser.display_info.AddFormat("""
        table[box](
          id:label=MODEL_ID,
          manufacturer:label=MAKE,
          name:label=MODEL_NAME,
          form.color(blue=VIRTUAL,yellow=PHYSICAL,green=EMULATOR):label=FORM,
          format("{0:4} x {1}", screenY, screenX):label=RESOLUTION,
          supportedVersionIds.list(undefined="none"):label=OS_VERSION_IDS,
          tags.join(sep=", ").color(green=default,red=deprecated,yellow=preview)
        )
    """)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """Run the 'gcloud firebase test android models list' command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation (i.e. group and command arguments combined).

    Returns:
      The list of device models we want to have printed later. Obsolete models
      with no currently supported OS versions are filtered out.
    """
    catalog = util.GetAndroidCatalog(self.context)
    filtered_models = [
        model for model in catalog.models if model.supportedVersionIds
    ]
    self._epilog = util.GetDeprecatedTagWarning(filtered_models, 'android')

    return filtered_models

  def Epilog(self, resources_were_displayed=True):
    super(List, self).Epilog(resources_were_displayed)

    if self._epilog:
      log.warning(self._epilog)


List.detailed_help = DETAILED_HELP
