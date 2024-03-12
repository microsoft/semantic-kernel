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
"""gcloud service-extensions wasm-plugins update command."""

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
class Update(base.UpdateCommand):
  """Update a `WasmPlugin` resource."""

  detailed_help = {
      'DESCRIPTION': textwrap.dedent("""\
          Update an existing `WasmPlugin` resource and optionally create
          a `WasmPluginVersion` resource and set it as the main (serving) one.

          If `--image` is not specified:
              * the method only updates the `WasmPlugin` resource without
                creating a `WasmPluginVersion`.
              * the `--plugin-config***` flags are disallowed.
              * if `--main-version` is set, then the referenced
                `WasmPluginVersion` must already exist and it is set as the
                main (serving) one.

          If `--image` is specified:
              * the `--main-version` flag must also be specified.
              * the method updates the `WasmPlugin` resource and creates a new
                `WasmPluginVersion` with `--main-version` name and sets it as
                the main (serving) one.
              * the `--plugin-config***` flags are allowed.
              * the `--async` flag is disallowed.
      """),
      'EXAMPLES': textwrap.dedent("""\
          To update a `WasmPlugin` called `my-plugin`, run:

          $ {command} my-plugin --main-version=new-version
          --description="A new description." --labels=label1=value1

          To update a `WasmPlugin` called `my-plugin` and also create a new
          version called `v1` and set it as main:

          $ {command} my-plugin --main-version=v1
          --description="A new description." --labels=label1=value1
          --image=...-docker.pkg.dev/my-project/repository/container:tag
          """)
  }

  @classmethod
  def Args(cls, parser):
    flags.AddWasmPluginResource(
        parser=parser,
        api_version=util.GetApiVersion(cls.ReleaseTrack()),
        message='The ID of the `WasmPlugin` to update.',
    )

    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)
    flags.AddDescriptionFlag(parser)
    flags.AddLogConfigFlag(parser)

    flags.AddWasmPluginVersionArgs(
        parser=parser,
        version_message="""
            The ID of the `WasmPluginVersion` that should be the currently
            serving one. The version referred to must be a child of this
            `WasmPlugin`.

            If the `--image` flag was also provided, the `WasmPluginVersion`
            will be created for that `WasmPlugin` and will be set as the
            current main version.
        """,
    )

    # Changes the default output format.
    parser.display_info.AddFormat('yaml')

  def Run(self, args):
    update_wasm_plugin_and_create_version = None
    if (
        args.main_version is not None
        and args.image is not None
        and not args.async_
    ):
      update_wasm_plugin_and_create_version = True
    elif args.image is None:
      update_wasm_plugin_and_create_version = False
    elif args.main_version is None:
      raise calliope_exceptions.RequiredArgumentException(
          '--main-version',
          'Both flags --image and --main-version should be set or neither of'
          ' them.',
      )
    else:
      raise calliope_exceptions.ConflictingArgumentsException(
          '--async',
          'If --async flag is set, --image and --config flags can\'t be used.',
      )
    if not update_wasm_plugin_and_create_version:
      if (
          GetPluginConfigData(args) is not None
          or args.plugin_config_uri is not None
      ):
        raise calliope_exceptions.ConflictingArgumentsException(
            '--plugin_config or --plugin_config_file or --plugin_config_uri',
            'If one of the flags is set, then --image and --main-version'
            ' flags also should be set.',
        )

    wasm_plugin_ref = args.CONCEPTS.wasm_plugin.Parse()
    main_version = args.main_version
    if update_wasm_plugin_and_create_version:
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

    wp_client = wasm_plugin_api.Client(self.ReleaseTrack())
    labels = labels_util.ParseCreateArgs(
        args, wp_client.messages.WasmPlugin.LabelsValue
    )
    log_config = _GetLogConfig(args)

    update_mask = []
    if args.IsSpecified('description'):
      update_mask.append('description')
    if args.IsSpecified('labels'):
      update_mask.append('labels')
    if args.IsSpecified('log_config'):
      update_mask.append('logConfig')
    if args.IsSpecified('main_version'):
      update_mask.append('mainVersionId')

    op_ref = wp_client.UpdateWasmPlugin(
        name=wasm_plugin_ref.RelativeName(),
        main_version=main_version,
        update_mask=','.join(sorted(update_mask)),
        description=args.description,
        labels=labels,
        log_config=log_config,
    )

    log.status.Print('Update request issued for: [{}]'.format(
        wasm_plugin_ref.Name()))

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    result = wp_client.WaitForOperation(
        operation_ref=op_ref,
        message='Waiting for operation [{}] to complete'.format(op_ref.name),
    )

    log.status.Print('Updated WasmPlugin [{}].'.format(wasm_plugin_ref.Name()))

    return result
