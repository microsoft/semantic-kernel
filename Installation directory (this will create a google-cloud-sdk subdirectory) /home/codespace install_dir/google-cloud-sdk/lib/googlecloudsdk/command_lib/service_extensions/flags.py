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
"""Common flags for service-extensions resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.service_extensions import util
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def AddWasmPluginResource(parser, api_version, message):
  wasm_plugin_data = yaml_data.ResourceYAMLData.FromPath(
      'service_extensions.wasmPlugin'
  )
  concept_parsers.ConceptParser(
      [
          presentation_specs.ResourcePresentationSpec(
              'wasm_plugin',
              concepts.ResourceSpec.FromYaml(
                  wasm_plugin_data.GetData(),
                  api_version=api_version,
              ),
              message,
              required=True,
          )
      ],
  ).AddToParser(parser)


def AddDescriptionFlag(parser):
  parser.add_argument(
      '--description',
      help='A human-readable description of the resource.')


def AddLogConfigFlag(parser):
  parser.add_argument(
      '--log-config',
      action='append',
      type=util.LogConfig(),
      required=False,
      metavar='LOG_CONFIG',
      help=textwrap.dedent("""\
        Logging options for the activity performed by this plugin.
        The following options can be set:
        * `enable`: whether to enable logging. If `log-config` flag is set,
          `enable` option is required.

        * `sample-rate`: configures the sampling rate of activity logs, where
          `1.0` means all logged activity is reported and `0.0` means no
          activity is reported. The default value is `1.0`, and the value of
          the field must be in range `0` to `1` (inclusive).

        * `min-log-level`: specifies the lowest level of the logs that
          should be exported to Cloud Logging. The default value is `INFO`.

        Example usage:
        `--log-config=enable=True,sample-rate=0.5,min-log-level=INFO
        --log_config=enable=False`
        """),
  )


def AddVersionFlag(parser, version_message):
  parser.add_argument('--main-version', help=version_message)


def AddImageFlag(parser):
  parser.add_argument(
      '--image',
      help=textwrap.dedent("""\
          URI of the container image containing the plugin's Wasm module,
          stored in the Artifact Registry."""),
  )


def AddPluginConfigFlag(parser):
  """Adds flags defining plugin config."""
  plugin_config_group = parser.add_group(
      mutex=True,
      required=False,
      help="""Configuration for the plugin, provided at runtime by the
              `on_configure` function (Rust Proxy-Wasm SDK) or the
              `onConfigure` method (C++ Proxy-Wasm SDK).""",
  )
  plugin_config_group.add_argument(
      '--plugin-config',
      required=False,
      help="""Plugin runtime configuration in the textual format."""
  )
  plugin_config_group.add_argument(
      '--plugin-config-file',
      required=False,
      type=arg_parsers.FileContents(binary=True),
      help="""Path to a local file containing the plugin runtime
              configuration."""
  )
  plugin_config_group.add_argument(
      '--plugin-config-uri',
      required=False,
      help="""URI of the container image containing the plugin's runtime
              configuration, stored in the Artifact Registry."""
  )


def AddWasmPluginVersionArgs(parser, version_message):
  wasm_plugin_version_group = parser.add_group(mutex=False, required=False)
  AddVersionFlag(wasm_plugin_version_group, version_message)
  AddImageFlag(wasm_plugin_version_group)
  AddPluginConfigFlag(wasm_plugin_version_group)
