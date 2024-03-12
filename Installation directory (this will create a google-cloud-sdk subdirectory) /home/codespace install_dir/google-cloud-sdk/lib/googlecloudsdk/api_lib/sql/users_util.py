# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Common command-agnostic utility functions for sql users commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def CreateSetPasswordRequest(sql_messages,
                             args,
                             dual_password_type,
                             project):
  """Creates the set password request to send to UpdateUser.

  Args:
    sql_messages: module, The messages module that should be used.
    args: argparse.Namespace, The arguments that this command was invoked with.
    dual_password_type: How we want to interact with the dual password.
    project: the project that this user is in

  Returns:
    CreateSetPasswordRequest
  """
  user = sql_messages.User(
      project=project,
      instance=args.instance,
      name=args.username,
      host=args.host,
      password=args.password)
  if dual_password_type:
    user.dualPasswordType = dual_password_type

  return sql_messages.SqlUsersUpdateRequest(
      project=project,
      instance=args.instance,
      name=args.username,
      host=args.host,
      user=user)
