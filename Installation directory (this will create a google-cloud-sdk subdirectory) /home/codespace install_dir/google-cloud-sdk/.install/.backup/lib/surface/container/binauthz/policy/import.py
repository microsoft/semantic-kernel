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
"""Import Binary Authorization policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import policies
from googlecloudsdk.api_lib.container.binauthz import util
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import arg_parsers
from googlecloudsdk.command_lib.container.binauthz import parsing
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


# TODO(b/77499756): Add help text for etags here (or maybe to the group help).
class Import(base.Command):
  """Import a Binary Authorization policy to the current project.

  This command accepts a description of the desired policy in the form of a
  YAML-formatted file. A representation of the current policy can be retrieved
  using the  $ {parent_command} export  command. One method of modifying the
  policy is to run `$ {parent_command} export`, dump the contents to a file,
  modify the policy file to reflect the desired new policy, and provide this
  modified file to `$ {command}`.

  ## EXAMPLES

  To update the current project's policy:

    $ {parent_command} export > my_policy.yaml

    $ edit my_policy.yaml

    $ {command} my_policy.yaml
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'policy_file',
        type=arg_parsers.PolicyFileName,
        help='The file containing the YAML-formatted policy description.')
    parser.add_argument(
        '--strict-validation',
        action='store_true',
        required=False,
        help='Whether to perform additional checks on the validity of policy '
        'contents.')

  def Run(self, args):
    api_version = apis.GetApiVersion(self.ReleaseTrack())
    messages = apis.GetMessagesModule(api_version)

    # Load the policy file into a Python object.
    policy_obj = parsing.LoadResourceFile(args.policy_file)
    if not policy_obj:
      # NOTE: This is necessary because apitools falls over when you provide it
      # with None and that's what the yaml returns when passed an empty string.
      policy_obj = {}

      # Make sure the user meant to do this.
      log.warning('Empty Policy provided!')
      console_io.PromptContinue(
          prompt_string='Do you want to import an empty policy?',
          cancel_on_no=True)

    # Decode the dict into a Policy message, allowing DecodeErrors to bubble up
    # to the user if they are raised.
    policy = messages_util.DictToMessageWithErrorCheck(
        policy_obj, messages.Policy)

    return policies.Client(api_version).Set(util.GetPolicyRef(), policy)
