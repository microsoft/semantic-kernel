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
- release_tracks: ${release_tracks}

  help_text:
    brief: List ${uppercase_api_name} ${plural_resource_name}.
    description: |
      List ${uppercase_api_name} ${plural_resource_name}.
    examples: |
      To list the ${plural_resource_name}, run:

        $ {command}

  request:
    collection: ${collection_name}
    api_version: ${api_version}

  response:
    id_field: name

  arguments:
    resource:
      help_text: Parent ${uppercase_api_name} ${parent} to list all contained ${uppercase_api_name} ${plural_resource_name}.
      # The following should point to the parent resource argument definition
      # under your surface's command_lib directory.:
      spec: !REF googlecloudsdk.command_lib.${api_name}.resources:${parent}

  output:
    format: |
      table(
        name.basename():label=NAME,
        % for field in create_args:
        ${field}:label=${field.upper()}${'' if loop.last else ','}
        % endfor
      )
