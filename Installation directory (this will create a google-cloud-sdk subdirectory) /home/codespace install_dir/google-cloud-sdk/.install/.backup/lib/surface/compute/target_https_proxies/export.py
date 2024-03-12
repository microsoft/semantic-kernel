# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Export target HTTPS proxy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.target_https_proxies import flags
from googlecloudsdk.command_lib.compute.target_https_proxies import target_https_proxies_utils
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files


def _DetailedHelp():
  return {
      'brief':
          'Export a target HTTPS proxy.',
      'DESCRIPTION':
          """\
          Exports a target HTTPS proxy's configuration to a file.
          This configuration can be imported at a later time.
          """,
      'EXAMPLES':
          """\
          A target HTTPS proxy can be exported by running:

            $ {command} NAME --destination=<path-to-file>
          """
  }


def _GetApiVersion(release_track):
  """Returns the API version based on the release track."""
  if release_track == base.ReleaseTrack.ALPHA:
    return 'alpha'
  if release_track == base.ReleaseTrack.BETA:
    return 'beta'
  return 'v1'


def _GetSchemaPath(release_track, for_help=False):
  """Returns the resource schema path."""
  return export_util.GetSchemaPath(
      'compute',
      _GetApiVersion(release_track),
      'TargetHttpsProxy',
      for_help=for_help)


def _Run(args, holder, target_https_proxy_arg, release_track):
  """Issues requests necessary to export target HTTPS proxies."""
  client = holder.client

  target_https_proxy_ref = target_https_proxy_arg.ResolveAsResource(
      args,
      holder.resources,
      default_scope=compute_scope.ScopeEnum.GLOBAL,
      scope_lister=compute_flags.GetDefaultScopeLister(client))

  target_https_proxy = target_https_proxies_utils.SendGetRequest(
      client, target_https_proxy_ref)

  if args.destination:
    with files.FileWriter(args.destination) as stream:
      export_util.Export(
          message=target_https_proxy,
          stream=stream,
          schema_path=_GetSchemaPath(release_track))
  else:
    export_util.Export(
        message=target_https_proxy,
        stream=sys.stdout,
        schema_path=_GetSchemaPath(release_track))


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Export(base.Command):
  """Export a target HTTPS proxy."""

  detailed_help = _DetailedHelp()
  TARGET_HTTPS_PROXY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.TARGET_HTTPS_PROXY_ARG = flags.TargetHttpsProxyArgument()
    cls.TARGET_HTTPS_PROXY_ARG.AddArgument(parser, operation_type='export')
    export_util.AddExportFlags(
        parser, _GetSchemaPath(cls.ReleaseTrack(), for_help=True))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.TARGET_HTTPS_PROXY_ARG, self.ReleaseTrack())
