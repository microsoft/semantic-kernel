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
  brief: Set the IAM policy for the ${singular_name}.
  description: |
    *{command}* displays the IAM policy associated with the ${singular_name}.
    If formatted as JSON,the output can be edited and used as a
    policy file for set-iam-policy. The output includes an "etag" field
    identifying the version emitted and allowing detection of
    concurrent policy updates; see
    $ {parent} set-iam-policy for additional details.
  examples: |
    To print the IAM policy for a given ${singular_name}, run:

      $ {command} my-${singular_name} ${flags} policy.json

request:
  collection: ${collection_name}
  api_version: ${api_version}
  use_relative_name: ${use_relative_name}

iam:
  # Whether the command can accept 'condition' as part of IAM policy binding.
  enable_condition: true
  # IAM Policy version. Valid options are "0", "1", and "3".
  # (Version 3 allows conditions.)
  policy_version: 3

arguments:
  resource:
    help_text: The ${singular_name} for which to display the IAM policy.
    # the following should point to the resource argument definition under your
    # surface's command_lib directory:
    spec: !REF googlecloudsdk.command_lib.${api_name}.resources:${singular_name}
