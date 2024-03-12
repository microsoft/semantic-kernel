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
"""Additional help about object metadata."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.help_provider import HelpProvider

_DETAILED_HELP_TEXT = ("""
<B>OVERVIEW OF METADATA</B>
  Objects can have associated metadata, which control aspects of how
  GET requests are handled, including ``Content-Type``, ``Cache-Control``,
  ``Content-Disposition``, and ``Content-Encoding``. In addition, you can
  set custom ``key:value`` metadata for use by your applications. For a
  discussion of specific metadata properties, see the `metadata concept
  page <https://cloud.google.com/storage/docs/metadata>`_.

  There are two ways to set metadata on objects:

  - At upload time you can specify one or more metadata properties to
    associate with objects, using the ``gsutil -h option``.  For example,
    the following command would cause gsutil to set the ``Content-Type`` and
    ``Cache-Control`` for each of the files being uploaded from a local
    directory named ``images``:

      gsutil -h "Content-Type:text/html" \\
             -h "Cache-Control:public, max-age=3600" cp -r images \\
             gs://bucket/images

    Note that -h is an option on the gsutil command, not the cp sub-command.

  - You can set or remove metadata fields from already uploaded objects using
    the ``gsutil setmeta`` command. See "gsutil help setmeta".

<B>SETTABLE FIELDS; FIELD VALUES</B>
  You can't set some metadata fields, such as ETag and Content-Length. The
  fields you can set are:

  - ``Cache-Control``
  - ``Content-Disposition``
  - ``Content-Encoding``
  - ``Content-Language``
  - ``Content-Type``
  - ``Custom-Time``
  - Custom metadata

  Field names are case-insensitive.

  All fields and their values must consist only of ASCII characters, with the
  exception of values for ``x-goog-meta-`` fields, which may contain arbitrary
  Unicode values. Note that when setting metadata using the XML API, which sends
  custom metadata as HTTP headers, Unicode characters are encoded using
  UTF-8, then url-encoded to ASCII. For example:

    gsutil setmeta -h "x-goog-meta-foo: ã" gs://bucket/object

  stores the custom metadata key-value pair of ``foo`` and ``%C3%A3``.
  Subsequently, running ``ls -L`` using the JSON API to list the object's
  metadata prints ``%C3%A3``, while ``ls -L`` using the XML API
  url-decodes this value automatically, printing the character ``ã``.


<B>VIEWING CURRENTLY SET METADATA</B>
  You can see what metadata is currently set on an object by using:

    gsutil ls -L gs://the_bucket/the_object
""")


class CommandOptions(HelpProvider):
  """Additional help about object metadata."""

  # Help specification. See help_provider.py for documentation.
  help_spec = HelpProvider.HelpSpec(
      help_name='metadata',
      help_name_aliases=[
          'cache-control',
          'caching',
          'content type',
          'mime type',
          'mime',
          'type',
      ],
      help_type='additional_help',
      help_one_line_summary='Working With Object Metadata',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )
