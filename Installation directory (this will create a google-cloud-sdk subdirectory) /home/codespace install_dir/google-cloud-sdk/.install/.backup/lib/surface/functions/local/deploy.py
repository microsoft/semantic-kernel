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
"""Deploys a function locally."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import textwrap
import typing

from googlecloudsdk.api_lib.functions.v2 import client as client_v2
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.functions import flags as flag_util
from googlecloudsdk.command_lib.functions import source_util
from googlecloudsdk.command_lib.functions.local import flags as local_flags
from googlecloudsdk.command_lib.functions.local import util
from googlecloudsdk.command_lib.functions.v2.deploy import env_vars_util
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files as file_utils


_LOCAL_DEPLOY_MESSAGE = textwrap.dedent("""\
    Your function {name} is serving at localhost:{port}.

    To call this locally deployed function using gcloud:
    gcloud alpha functions local call {name} [--data=DATA] | [--cloud-event=CLOUD_EVENT]

    To call local HTTP functions using curl:
    curl -m 60 -X POST localhost:{port} -H "Content-Type: application/json" -d '{{}}'

    To call local CloudEvent and Background functions using curl, please see:
    https://cloud.google.com/functions/docs/running/calling
    """)
_DETAILED_HELP = {
    'DESCRIPTION': """
        `{command}` Deploy a Google Cloud Function locally.
        """,
}
_REGION = 'us-central1'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Deploy(base.Command):
  """Deploy a Google Cloud Function locally."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    local_flags.AddDeploymentNameFlag(parser)
    local_flags.AddPortFlag(parser)
    local_flags.AddBuilderFlag(parser)

    flag_util.AddEntryPointFlag(parser)
    flag_util.AddRuntimeFlag(parser)
    flag_util.AddIgnoreFileFlag(parser)
    # TODO(b/296916846): Add memory and CPU flags
    flag_util.AddSourceFlag(parser)

    env_vars_util.AddBuildEnvVarsFlags(parser)
    env_vars_util.AddUpdateEnvVarsFlags(parser)

    # Add NO-OP gen2 flag for user familiarity
    flag_util.AddGen2Flag(parser, hidden=True)

  def Run(self, args):
    util.ValidateDependencies()
    labels = self._CreateAndUpdateLabels(args)

    client = client_v2.FunctionsClient(release_track=base.ReleaseTrack.ALPHA)
    runtimes = sorted({r.name for r in client.ListRuntimes(_REGION).runtimes})
    flags = labels.get('flags')
    self._ValidateFlags(flags, runtimes)

    name = args.NAME[0]

    with file_utils.TemporaryDirectory() as tmp_dir:
      path = source_util.CreateSourcesZipFile(
          tmp_dir,
          source_path=flags.get('source', '.'),
          ignore_file=flags.get('ignore-file')
      )
      util.RunPack(name=name,
                   builder=flags.get('--builder'),
                   runtime=flags.get('--runtime'),
                   entry_point=flags.get('--entry-point'),
                   path=path,
                   build_env_vars=labels.get('build-env-vars'))

    util.RunDockerContainer(name=name,
                            port=flags.get('--port', '8080'),
                            env_vars=labels.get('env-vars'),
                            labels=labels)

    log.status.Print(_LOCAL_DEPLOY_MESSAGE.format(
        name=name, port=flags.get('--port', '8080')))

  def _CreateAndUpdateLabels(
      self, args: parser_extensions.Namespace) -> typing.Dict[str, typing.Any]:
    labels = {}

    old_labels = util.GetDockerContainerLabels(args.NAME[0])
    old_flags = json.loads(old_labels.get('flags', '{}'))
    old_env_vars = json.loads(old_labels.get('env-vars', '{}'))
    old_build_env_vars = json.loads(old_labels.get('build-env-vars', '{}'))

    labels['flags'] = self._ApplyNewFlags(args, old_flags)

    env_vars = map_util.GetMapFlagsFromArgs('env-vars', args)
    labels['env-vars'] = map_util.ApplyMapFlags(old_env_vars, **env_vars)

    build_env_vars = map_util.GetMapFlagsFromArgs('build-env-vars', args)
    labels['build-env-vars'] = map_util.ApplyMapFlags(
        old_build_env_vars, **build_env_vars)

    return labels

  def _ApplyNewFlags(self, args: parser_extensions.Namespace,
                     old_flags: typing.Dict[str, str]) -> typing.Dict[str, str]:
    flags = {**old_flags, **args.GetSpecifiedArgs()}
    flags = {k: v for (k, v) in flags.items()
             if not('NAME' in k or 'env-vars' in k)}
    return flags

  def _ValidateFlags(self, flags: typing.Dict[str, str],
                     runtimes: typing.Set[str]) -> None:
    if '--entry-point' not in flags:
      raise exceptions.RequiredArgumentException(
          '--entry-point', 'Flag `--entry-point` required.'
      )
    # Require runtime if builder not specified.
    if '--builder' not in flags and '--runtime' not in flags:
      flags['--runtime'] = self._PromptUserForRuntime(runtimes)
    if flags.get('--runtime') not in runtimes:
      log.out.Print('--runtime must be one of the following:')
      flags['--runtime'] = self._PromptUserForRuntime(runtimes)

  def _PromptUserForRuntime(self, runtimes: typing.Set[str]) -> str:
    if not console_io.CanPrompt():
      raise exceptions.RequiredArgumentException(
          '--runtime', 'Flag `--runtime` required when builder not specified.'
      )
    idx = console_io.PromptChoice(
        runtimes, message='Please select a runtime:\n'
    )
    return runtimes[idx]
