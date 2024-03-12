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
"""Additional flags for data-catalog tag-templates commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


def AddCreateTagTemplateFlags():
  """Hook for adding flags to tag-template create."""
  field_flag = base.Argument(
      '--field',
      type=arg_parsers.ArgDict(spec={
          'id': str,
          'type': str,
          'display-name': str,
          'required': bool,
      }, required_keys=['id', 'type']),
      action='append',
      required=True,
      metavar='id=ID,type=TYPE,display-name=DISPLAY_NAME,required=REQUIRED',
      help="""\
        Specification for a tag template field. This flag can be repeated to
        specify multiple fields. The following keys are allowed:

          *id*::: (Required) ID of the tag template field.

          *type*::: (Required) Type of the tag template field. Choices are
              double, string, bool, timestamp, and enum.

                    To specify a string field:
                      `type=string`

                    To specify an enum field with values 'A' and 'B':
                      `type=enum(A|B)`

          *display-name*::: Display name of the tag template field.

          *required*::: Indicates if the tag template field is required.
              Defaults to FALSE.
      """)

  return [field_flag]
