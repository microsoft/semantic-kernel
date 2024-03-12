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
"""This file provides the implementation of the `functions add-iam-policy-binding` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v1 import util


def Run(args):
  """Adds a binding to the IAM policy for a Google Cloud Function.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.

  Returns:
    The updated IAM policy.
  """
  function_ref = args.CONCEPTS.name.Parse()
  return util.AddFunctionIamPolicyBinding(function_ref.RelativeName(),
                                          args.member, args.role)
