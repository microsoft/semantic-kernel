# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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


"""Various functions to be used to modify a request before it is sent."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.apis import arg_utils


def SetFieldFromArg(api_field, arg_name):
  def Process(unused_ref, args, req):
    arg_utils.SetFieldInMessage(
        req, api_field, arg_utils.GetFromNamespace(args, arg_name))
    return req
  return Process


def SetFieldFromRelativeName(api_field):
  def Process(ref, args, request):
    del args  # Unused in Process
    arg_utils.SetFieldInMessage(request, api_field, ref.RelativeName())
    return request
  return Process


def SetFieldFromName(api_field):
  def Process(ref, args, request):
    del args  # Unused in Process
    arg_utils.SetFieldInMessage(request, api_field, ref.Name())
    return request
  return Process


def SetParentRequestHook(ref, args, request):
  """Declarative request hook to add relative parent to issued requests."""
  del args  # Unused
  request.parent = ref.Parent().RelativeName()
  return request
