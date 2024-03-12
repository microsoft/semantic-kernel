# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Common flags for policies API commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


def GetAttachmentPointFlag():
  return base.Argument(
      '--attachment-point',
      required=True,
      help='Resource to which the policy is attached. For valid formats, see '
      'https://cloud.google.com/iam/help/deny/attachment-point.')


def GetKindFlag():
  return base.Argument(
      '--kind',
      required=True,
      help='Policy type. Use `denypolicies` for deny policies.')


def GetPolicyIDFlag():
  return base.Argument(
      'policy_id',
      help='Policy ID that is unique for the resource to which the policy is '
      'attached.')


# etag is only used in DeletePolicy
def GetEtagFlag():
  return base.Argument(
      '--etag',
      help='Etag that identifies the version of the existing policy. If omitted'
      ', the policy is deleted regardless of its current etag.')


def GetPolicyFileFlag():
  return base.Argument(
      '--policy-file', required=True, help='Path to the file that contains the '
      'policy, in JSON or YAML format. For valid syntax, see '
      'https://cloud.google.com/iam/help/deny/policy-syntax.')


def GetPageTokenFlag():
  return base.Argument(
      '--page_token',
      help='Page token received from a previous call. Provide this token to '
      'retrieve the next page.')


def AddIncludeDenyFlag(parser):
  base.Argument(
      '--include-deny',
      help='Include deny policies on the project and its ancestors in the result',
      action='store_true',
      default=False,
  ).AddToParser(parser)
