# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Additional help about CRC32C and installing crcmod."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.help_provider import HelpProvider

_DETAILED_HELP_TEXT = ("""
<B>OVERVIEW</B>
  To reduce the chance for `filename encoding interoperability problems
  <https://en.wikipedia.org/wiki/Filename#Encoding_indication_interoperability>`_
  gsutil uses `UTF-8 <https://en.wikipedia.org/wiki/UTF-8>`_ character encoding
  when uploading and downloading files. Because UTF-8 is in widespread (and
  growing) use, for most users nothing needs to be done to use UTF-8. Users with
  files stored in other encodings (such as
  `Latin 1 <https://en.wikipedia.org/wiki/ISO/IEC_8859-1>`_) must convert those
  filenames to UTF-8 before attempting to upload the files.

  The most common place where users who have filenames that use some other
  encoding encounter a gsutil error is while uploading files using the recursive
  (-R) option on the gsutil cp , mv, or rsync commands. When this happens you'll
  get an error like this:

      CommandException: Invalid Unicode path encountered
      ('dir1/dir2/file_name_with_\\xf6n_bad_chars').
      gsutil cannot proceed with such files present.
      Please remove or rename this file and try again.

  Note that the invalid Unicode characters have been hex-encoded in this error
  message because otherwise trying to print them would result in another
  error.

  If you encounter such an error you can either remove the problematic file(s)
  or try to rename them and re-run the command. If you have a modest number of
  such files the simplest thing to do is to think of a different name for the
  file and manually rename the file (using local filesystem tools). If you have
  too many files for that to be practical, you can use a bulk rename tool or
  script.

  Unicode errors for valid Unicode filepaths can be caused by lack of Python
  locale configuration on Linux and Mac OSes. If your file paths are Unicode
  and you get encoding errors, ensure the LANG environment variable is set
  correctly. Typically, the LANG variable should be set to something like
  "en_US.UTF-8" or "de_DE.UTF-8".

  Note also that there's no restriction on the character encoding used in file
  content - it can be UTF-8, a different encoding, or non-character
  data (like audio or video content). The gsutil UTF-8 character encoding
  requirement applies only to filenames.


<B>USING UNICODE FILENAMES ON WINDOWS</B>
  Windows support for Unicode in the command shell (cmd.exe or powershell) is
  somewhat painful, because Windows uses a Windows-specific character encoding
  called `cp1252 <https://en.wikipedia.org/wiki/Windows-1252>`_. To use Unicode
  characters you need to run this command in the command shell before the first
  time you use gsutil in that shell:

    chcp 65001

  If you neglect to do this before using gsutil, the progress messages while
  uploading files with Unicode names or listing buckets with Unicode object
  names will look garbled (i.e., with different glyphs than you expect in the
  output). If you simply run the chcp command and re-run the gsutil command, the
  output should no longer look garbled.

  gsutil attempts to translate between cp1252 encoding and UTF-8 in the main
  places that Unicode encoding/decoding problems have been encountered to date
  (traversing the local file system while uploading files, and printing Unicode
  names while listing buckets). However, because gsutil must perform
  translation, it is likely there are other erroneous edge cases when using
  Windows with Unicode. If you encounter problems, you might consider instead
  using cygwin (on Windows) or Linux or macOS - all of which support Unicode.


<B>USING UNICODE FILENAMES ON MACOS</B>
  macOS stores filenames in decomposed form (also known as
  `NFD normalization <https://en.wikipedia.org/wiki/Unicode_equivalence>`_).
  For example, if a filename contains an accented "e" character, that character
  will be converted to an "e" followed by an accent before being saved to the
  filesystem. As a consequence, it's possible to have different name strings
  for files uploaded from an operating system that doesn't enforce decomposed
  form (like Ubuntu) from one that does (like macOS).

  The following example shows how this behavior could lead to unexpected
  results. Say you create a file with non-ASCII characters on Ubuntu. Ubuntu
  stores that filename in its composed form. When you upload the file to the
  cloud, it is stored as named. But if you use gsutil rysnc to bring the file to
  a macOS machine and edit the file, then when you use gsutil rsync to bring
  this version back to the cloud, you end up with two different objects, instead
  of replacing the original. This is because macOS converted the filename to
  a decomposed form, and Cloud Storage sees this as a different object name.


<B>CROSS-PLATFORM ENCODING PROBLEMS OF WHICH TO BE AWARE</B>
  Using UTF-8 for all object names and filenames will ensure that gsutil doesn't
  encounter character encoding errors while operating on the files.
  Unfortunately, it's still possible that files uploaded / downloaded this way
  can have interoperability problems, for a number of reasons unrelated to
  gsutil. For example:

  - Windows filenames are case-insensitive, while Google Cloud Storage, Linux,
    and macOS are not. Thus, for example, if you have two filenames on Linux
    differing only in case and upload both to Google Cloud Storage and then
    subsequently download them to Windows, you will end up with just one file
    whose contents came from the last of these files to be written to the
    filesystem.
  - macOS performs character encoding decomposition based on tables stored in
    the OS, and the tables change between Unicode versions. Thus the encoding
    used by an external library may not match that performed by the OS. It is
    possible that two object names may translate to a single local filename.
  - Windows console support for Unicode is difficult to use correctly.

  For a more thorough list of such issues see `this presentation
  <http://www.i18nguy.com/unicode/filename-issues-iuc33.pdf>`_

  These problems mostly arise when sharing data across platforms (e.g.,
  uploading data from a Windows machine to Google Cloud Storage, and then
  downloading from Google Cloud Storage to a machine running macOS).
  Unfortunately these problems are a consequence of the lack of a filename
  encoding standard, and users need to be aware of the kinds of problems that
  can arise when copying filenames across platforms.

  There is one precaution users can exercise to prevent some of these problems:
  When using the Windows console specify wildcards or folders (using the -R
  option) rather than explicitly named individual files.


<B>CONVERTING FILENAMES TO UNICODE</B>
  Open-source tools are available to convert filenames for non-Unicode files.
  For example, to convert from latin1 (a common Windows encoding) to Unicode,
  you can use
  `Windows iconv <http://gnuwin32.sourceforge.net/packages/libiconv.htm>`_.
  For Unix-based systems, you can use
  `libiconv <https://www.gnu.org/software/libiconv/>`_.
""")


class CommandOptions(HelpProvider):
  """Additional help about filename encoding and interoperability problems."""

  # Help specification. See help_provider.py for documentation.
  help_spec = HelpProvider.HelpSpec(
      help_name='encoding',
      help_name_aliases=[
          'encodings',
          'utf8',
          'utf-8',
          'latin1',
          'unicode',
          'interoperability',
      ],
      help_type='additional_help',
      help_one_line_summary='Filename encoding and interoperability problems',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )
