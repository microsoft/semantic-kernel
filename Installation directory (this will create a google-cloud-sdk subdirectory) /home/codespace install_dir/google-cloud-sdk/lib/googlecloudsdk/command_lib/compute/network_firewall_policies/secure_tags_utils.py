# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Code that's shared between multiple org firewall policies subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.resource_manager import tag_utils


def TranslateSecureTagsForFirewallPolicy(client, secure_tags):
  """Returns a list of firewall policy rule secure tags, translating namespaced tags if needed.

  Args:
    client: compute client
    secure_tags: array of secure tag values

  Returns:
    List of firewall policy rule secure tags
  """

  ret_secure_tags = []
  for tag in secure_tags:
    name = TranslateSecureTag(tag)
    ret_secure_tags.append(
        client.messages.FirewallPolicyRuleSecureTag(name=name)
    )

  return ret_secure_tags


def TranslateSecureTag(secure_tag: str):
  """Returns a unified secure tag identifier.

  Translates the namespaced tag if required.

  Args:
    secure_tag: secure tag value in format tagValues/ID or
      ORG_ID/TAG_KEY_NAME/TAG_VALUE_NAME

  Returns:
    Secure tag name in unified format tagValues/ID
  """
  if secure_tag.startswith('tagValues/'):
    return secure_tag
  return tag_utils.GetNamespacedResource(secure_tag, tag_utils.TAG_VALUES).name
