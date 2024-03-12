# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Additional help about object versioning."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.help_provider import HelpProvider

_DETAILED_HELP_TEXT = ("""
<B>OVERVIEW</B>
  Versioning-enabled buckets maintain noncurrent versions of objects, providing
  a way to un-delete data that you accidentally deleted, or to retrieve older
  versions of your data. Noncurrent objects are ignored by gsutil commands
  unless you indicate it should do otherwise by setting a relevant command flag
  or by including a specific generation number in your command. For example,
  wildcards like ``*`` and ``**`` do not, by themselves, act on noncurrent
  object versions.
  
  When using gsutil cp, you cannot specify a version-specific URL as the
  destination, because writes to Cloud Storage always create a new version.
  Trying to specify a version-specific URL as the destination of ``gsutil cp``
  results in an error. When you specify a noncurrent object as a source in a
  copy command, you always create a new object version and retain the original
  (even when using the command to restore a live version). You can use the 
  ``gsutil mv`` command to simultaneously restore an object version and remove
  the noncurrent copy that was used as the source.

  You can turn versioning on or off for a bucket at any time. Turning
  versioning off leaves existing object versions in place and simply causes
  the bucket to delete the existing live version of the object whenever a new
  version is uploaded.

  Regardless of whether you have enabled versioning on a bucket, every object
  has two associated positive integer fields:

  - the generation, which is updated when a new object replaces an existing
    object with the same name. Note that there is no guarantee that generation
    numbers increase for successive versions, only that each new version has a
    unique generation number.
  - the metageneration, which identifies the metadata generation. It starts
    at 1; is updated every time the metadata (e.g., ACL or Content-Type) for a
    given content generation is updated; and gets reset when the generation
    number changes.

  Of these two integers, only the generation is used when working with versioned
  data. Both generation and metageneration can be used with concurrency control.
  
  To learn more about versioning and concurrency, see the following documentation:
  
  - `Overview of Object Versioning
    <https://cloud.google.com/storage/docs/object-versioning>`_
  - `Guide for using Object Versioning
    <https://cloud.google.com/storage/docs/using-object-versioning>`_
  - The `reference page for the gsutil versioning command
    <https://cloud.google.com/storage/docs/gsutil/commands/versioning>`_
  - `Request preconditions
    <https://cloud.google.com/storage/docs/request-preconditions>`_
""")


class CommandOptions(HelpProvider):
  """Additional help about object versioning."""

  # Help specification. See help_provider.py for documentation.
  help_spec = HelpProvider.HelpSpec(
      help_name='versions',
      help_name_aliases=['concurrency', 'concurrency control'],
      help_type='additional_help',
      help_one_line_summary='Object Versioning and Concurrency Control',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )
