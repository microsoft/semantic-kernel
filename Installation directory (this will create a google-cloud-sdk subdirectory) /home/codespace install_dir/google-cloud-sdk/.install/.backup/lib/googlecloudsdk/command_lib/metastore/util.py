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
"""Common utilities for Metastore commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.core.resource import resource_printer


def ConstructList(title, items):
  """Constructs text output listing the elements of items and a title.

  Args:
    title: string, the listing title
    items: iterable, the iterable whose elements to list

  Returns:
    string, text representing list title and elements.
  """
  buf = io.StringIO()
  resource_printer.Print(items, 'list[title="{0}"]'.format(title), out=buf)
  return buf.getvalue()
