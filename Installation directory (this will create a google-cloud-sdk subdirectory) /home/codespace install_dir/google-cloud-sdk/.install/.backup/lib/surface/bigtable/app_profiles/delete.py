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
"""bigtable app profiles delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py.exceptions import HttpError
from googlecloudsdk.api_lib.bigtable import app_profiles
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class DeleteAppProfile(base.DeleteCommand):
  """Delete a Bigtable app profile."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To delete an app profile, run:

            $ {command} my-app-profile-id --instance=my-instance-id

          """),
  }

  @staticmethod
  def Args(parser):
    arguments.AddAppProfileResourceArg(parser, 'to delete')
    arguments.ArgAdder(parser).AddForce('delete')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    app_profile_ref = args.CONCEPTS.app_profile.Parse()
    console_io.PromptContinue(
        'You are about to delete app profile: [{}]'.format(
            app_profile_ref.Name()),
        throw_if_unattended=True,
        cancel_on_no=True)
    try:
      response = app_profiles.Delete(app_profile_ref, force=args.force)
    except HttpError as e:
      util.FormatErrorMessages(e)
    else:
      log.DeletedResource(app_profile_ref.Name(), 'app profile')
      return response
