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
"""gcloud service-extensions wasm-plugins create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.service_extensions import wasm_plugin_api
from googlecloudsdk.api_lib.service_extensions import wasm_plugin_version_api
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.service_extensions import flags
from googlecloudsdk.command_lib.service_extensions import util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _GetLogConfig(args):
  """Converts the dict representation of the log_config to proto.

  Args:
    args: args with log_level parsed ordered dict. If log-level flag is set,
          enable option should also be set.

  Returns:
    a value of messages.WasmPluginLogConfig or None,
    if log-level flag were not provided.
  """

  if args.log_config is None:
    return None
  return util.GetLogConfig(args.log_config[0])


def GetPluginConfigData(args):
  return args.plugin_config or args.plugin_config_file


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a `WasmPlugin` resource."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          Create a new `WasmPlugin` resource.
      """),
      'EXAMPLES': textwrap.dedent("""\
          To create a WasmPlugin called `my-plugin`, run:

          $ {command} my-plugin

          To create a `WasmPlugin` called `my-plugin`, together with a new
          version called `v1`, and set it as main, run:

          $ {command} my-plugin --main-version=v1
          --image=...-docker.pkg.dev/my-project/repository/container:tag
          """)
  }

  @classmethod
  def Args(cls, parser):
    flags.AddWasmPluginResource(
        parser=parser,
        api_version=util.GetApiVersion(cls.ReleaseTrack()),
        message='The ID of the `WasmPlugin` resource to create.',
    )

    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)
    flags.AddDescriptionFlag(parser)
    flags.AddLogConfigFlag(parser)

    flags.AddWasmPluginVersionArgs(
        parser=parser,
        version_message=(
            'ID of the `WasmPluginVersion` resource that will be created for '
            'that `WasmPlugin` and that will be set as the current '
            'main version.'
        ),
    )

  def Run(self, args):
    create_wasm_plugin_with_version = None
    if (
        args.main_version is not None
        and args.image is not None
        and not args.async_
    ):
      create_wasm_plugin_with_version = True
    elif args.main_version is None and args.image is None:
      create_wasm_plugin_with_version = False
    else:
      if args.main_version is None:
        raise calliope_exceptions.RequiredArgumentException(
            '--main-version', 'Both flags --image and'
            ' --main-version should be set or neither of them.')
      elif args.image is None:
        raise calliope_exceptions.RequiredArgumentException(
            '--image', 'Both flags --image and --main-version should be set'
            ' or neither of them.')
      else:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--async', 'If --async flag is set, --image and'
            ' --main-version flags can\'t be used')
    if not create_wasm_plugin_with_version:
      if (
          GetPluginConfigData(args) is not None
          or args.plugin_config_uri is not None
      ):
        raise calliope_exceptions.ConflictingArgumentsException(
            '--plugin_config or --plugin_config_file or --plugin_config_uri',
            'If one of the flags is set, then --image and --main-version'
            ' flags also should be set.',
        )

    wp_client = wasm_plugin_api.Client(self.ReleaseTrack())

    wasm_plugin_ref = args.CONCEPTS.wasm_plugin.Parse()
    labels = labels_util.ParseCreateArgs(
        args, wp_client.messages.WasmPlugin.LabelsValue
    )
    log_config = _GetLogConfig(args)

    op_ref = wp_client.CreateWasmPlugin(
        parent=wasm_plugin_ref.Parent().RelativeName(),
        name=wasm_plugin_ref.Name(),
        description=args.description,
        labels=labels,
        log_config=log_config,
    )
    log.status.Print('Create request issued for: [{}]'.format(
        wasm_plugin_ref.Name()))

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    wasm_plugin = wp_client.WaitForOperation(
        operation_ref=op_ref,
        message='Waiting for operation [{}] to complete'.format(op_ref.name),
    )

    if not create_wasm_plugin_with_version:
      log.status.Print(
          'Created WasmPlugin [{}].'.format(wasm_plugin_ref.Name())
      )
      return wasm_plugin

    log.status.Print(
        'Created WasmPlugin, proceeding to create a WasmPluginVersion [{}].'
        .format(wasm_plugin_ref.Name())
    )

    main_version = args.main_version
    wpv_client = wasm_plugin_version_api.Client(self.ReleaseTrack())

    op_ref = wpv_client.CreateWasmPluginVersion(
        parent=wasm_plugin_ref.RelativeName(),
        name=main_version,
        image=args.image,
        plugin_config_data=GetPluginConfigData(args),
        plugin_config_uri=args.plugin_config_uri,
    )
    log.status.Print('Create request issued for: [{}]'.format(main_version))

    _ = wpv_client.WaitForOperation(
        operation_ref=op_ref,
        message='Waiting for operation [{}] to complete'.format(op_ref.name),
    )
    log.status.Print('Created WasmPluginVersion [{}].'.format(main_version))

    op_ref = wp_client.UpdateWasmPlugin(
        name=wasm_plugin_ref.RelativeName(),
        main_version=main_version,
        # Do this now to prevent removing labels from WasmPlugin during update.
        # TODO(b/286219289): Remove labels from the updatedMask and function
        # arguments when resolved.
        update_mask='labels,mainVersionId',
        labels=labels,
    )
    log.status.Print('Update request issued for: [{}]'.format(
        wasm_plugin_ref.Name()))

    result = wp_client.WaitForOperation(
        operation_ref=op_ref,
        message='Waiting for operation [{}] to complete'.format(op_ref.name),
    )

    log.status.Print(
        'Created WasmPlugin [{}] with WasmPluginVersion [{}].'.format(
            wasm_plugin_ref.Name(), main_version
        )
    )

    return result
