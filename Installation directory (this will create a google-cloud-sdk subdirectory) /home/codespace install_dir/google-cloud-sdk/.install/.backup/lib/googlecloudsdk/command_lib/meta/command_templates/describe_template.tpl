# -*- coding: utf-8 -*- #
## Copyright 2020 Google LLC. All Rights Reserved.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##    http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
release_tracks: ${release_tracks}

help_text:
  brief: Show details about the ${singular_name}.
  description: Show details about the ${singular_name}.
  examples: |
    To show details about a device, run:

      $ {command} my-${singular_name} ${flags}

request:
  collection: ${collection_name}
  api_version: ${api_version}

arguments:
  resource:
    help_text: The ${singular_name} you want to describe.
    # The following should point to the resource argument definition under your
    # surface's command_lib directory.:
    spec: !REF googlecloudsdk.command_lib.${api_name}.resources:${singular_name}
