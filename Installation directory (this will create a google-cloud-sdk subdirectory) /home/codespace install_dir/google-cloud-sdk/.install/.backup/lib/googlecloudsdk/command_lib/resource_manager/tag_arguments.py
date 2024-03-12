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
"""Utilities for defining CRM Tag arguments on a parser."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


def AddShortNameArgToParser(parser):
  """Adds positional argument to parser.

  Args:
    parser: ArgumentInterceptor, an argparse parser.
  """
  parser.add_argument(
      "short_name",
      metavar="SHORT_NAME",
      help=("User specified, friendly name of the TagKey or TagValue. The field"
            " must be 1-63 characters, beginning and ending with an "
            "alphanumeric character ([a-z0-9A-Z]) with dashes (-), "
            "underscores ( _ ), dots (.), and alphanumerics between. "))


def AddParentArgToParser(parser, required=True, message=""):
  """Adds argument for the TagKey or TagValue's parent to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
    required: Boolean, to enforce --parent as a required flag.
    message: String, replacement help text for flag.
  """
  parser.add_argument(
      "--parent",
      metavar="PARENT",
      required=required,
      help=message if message else ("Parent of the resource."))


def AddDescriptionArgToParser(parser):
  """Adds argument for the TagKey's or TagValue's description to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "--description",
      metavar="DESCRIPTION",
      help=("User-assigned description of the TagKey or TagValue. "
            "Must not exceed 256 characters."))


def AddPurposeArgToParser(parser):
  """Adds argument for the TagKey's purpose to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "--purpose",
      metavar="PURPOSE",
      choices=["GCE_FIREWALL"],
      help=("Purpose specifier of the TagKey that can only be set on creation. "
            "Specifying this field adds additional validation from the policy "
            "system that corresponds to the purpose."))


def AddPurposeDataArgToParser(parser):
  """Adds argument for the TagKey's purpose data to the parser.

  Args:
     parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "--purpose-data",
      type=arg_parsers.ArgDict(
          spec={"network": str},
          max_length=1,
      ),
      help=("Purpose data of the TagKey that can only be set on creation. "
            "This data is validated by the policy system that corresponds"
            " to the purpose."))


def AddAsyncArgToParser(parser):
  """Adds async flag to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  base.ASYNC_FLAG.AddToParser(parser)


def AddResourceNameArgToParser(parser):
  """Adds resource name argument for the namespaced name or resource name to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "RESOURCE_NAME",
      metavar="RESOURCE_NAME",
      help=("Resource name or namespaced name. The resource name should "
            "be in the form {resource_type}/{numeric_id}. The namespaced name "
            "should be in the form {org_id}/{short_name} where short_name "
            "must be 1-63 characters, beginning and ending with an "
            "alphanumeric character ([a-z0-9A-Z]) with dashes (-), underscores "
            "( _ ), dots (.), and alphanumerics between."))


def AddForceArgToParser(parser):
  """Adds force argument  to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "--force", action="store_true", help=("Force argument to bypass checks."))


def AddPolicyFileArgToParser(parser):
  """Adds argument for the local Policy file to set.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "POLICY_FILE",
      metavar="POLICY_FILE",
      help=(
          "Path to a local JSON or YAML formatted file containing a valid "
          "policy. The output of the `get-iam-policy` command is a valid "
          "file, as is any JSON or YAML file conforming to the structure of "
          "a [Policy](https://cloud.google.com/iam/reference/rest/v1/Policy)."))


def AddTagValueArgToParser(parser):
  """Adds the TagValue argument to the parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
  """
  parser.add_argument(
      "--tag-value",
      metavar="TAG_VALUE",
      required=True,
      help=("Tag value name or namespaced name. The name should "
            "be in the form tagValues/{numeric_id}. The namespaced name "
            "should be in the form {org_id}/{tag_key_short_name}/{short_name} "
            "where short_name must be 1-63 characters, beginning and ending "
            "with an alphanumeric character ([a-z0-9A-Z]) with dashes (-), "
            "underscores (_), dots (.), and alphanumerics between."))


def AddLocationArgToParser(parser, message):
  """Adds argument for the location.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
    message: String, help text for flag.
  """
  parser.add_argument(
      "--location", metavar="LOCATION", required=False, help=message)


def AddEffectiveArgToParser(parser, message):
  """Adds argument for the effective option.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
    message: String, help text for flag.
  """
  parser.add_argument(
      "--effective", action="store_true", required=False, help=message)
