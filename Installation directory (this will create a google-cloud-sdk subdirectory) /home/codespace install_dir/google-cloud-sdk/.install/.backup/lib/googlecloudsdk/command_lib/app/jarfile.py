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
"""Code for handling Manifest file in a Java jar file.

Jar files are just zip files with a particular interpretation for certain files
in the zip under the META-INF/ directory. So we can read and write them using
the standard zipfile module.

The specification for jar files is at
http://docs.oracle.com/javase/7/docs/technotes/guides/jar/jar.html
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from __future__ import with_statement
import re
import zipfile


_MANIFEST_NAME = 'META-INF/MANIFEST.MF'


class Error(Exception):
  pass


class InvalidJarError(Error):
  pass


class Manifest(object):
  """The parsed manifest from a jar file.

  Attributes:
    main_section: a dict representing the main (first) section of the manifest.
      Each key is a string that is an attribute, such as 'Manifest-Version', and
      the corresponding value is a string that is the value of the attribute,
      such as '1.0'.
    sections: a dict representing the other sections of the manifest. Each key
      is a string that is the value of the 'Name' attribute for the section,
      and the corresponding value is a dict like the main_section one, for the
      other attributes.
  """

  def __init__(self, main_section, sections):
    self.main_section = main_section
    self.sections = sections


def ReadManifest(jar_file_name):
  """Read and parse the manifest out of the given jar.

  Args:
    jar_file_name: the name of the jar from which the manifest is to be read.

  Returns:
    A parsed Manifest object, or None if the jar has no manifest.

  Raises:
    IOError: if the jar does not exist or cannot be read.
  """
  with zipfile.ZipFile(jar_file_name) as jar:
    try:
      manifest_string = jar.read(_MANIFEST_NAME).decode('utf-8')
    except KeyError:
      return None
    return _ParseManifest(manifest_string, jar_file_name)


def _ParseManifest(manifest_string, jar_file_name):
  """Parse a Manifest object out of the given string.

  Args:
    manifest_string: a str or unicode that is the manifest contents.
    jar_file_name: a str that is the path of the jar, for use in exception
      messages.

  Returns:
    A Manifest object parsed out of the string.

  Raises:
    InvalidJarError: if the manifest is not well-formed.
  """

  # Lines in the manifest might be terminated by \r\n so normalize.
  manifest_string = '\n'.join(manifest_string.splitlines()).rstrip('\n')
  section_strings = re.split('\n{2,}', manifest_string)
  parsed_sections = [_ParseManifestSection(s, jar_file_name)
                     for s in section_strings]
  main_section = parsed_sections[0]
  sections = {}
  for entry in parsed_sections[1:]:
    name = entry.get('Name')
    if name is None:
      raise InvalidJarError('%s: Manifest entry has no Name attribute: %r' %
                            (jar_file_name, entry))
    else:
      sections[name] = entry
  return Manifest(main_section, sections)


def _ParseManifestSection(section, jar_file_name):
  """Parse a dict out of the given manifest section string.

  Args:
    section: a str or unicode that is the manifest section. It looks something
      like this (without the >):
      > Name: section-name
      > Some-Attribute: some value
      > Another-Attribute: another value
    jar_file_name: a str that is the path of the jar, for use in exception
      messages.

  Returns:
    A dict where the keys are the attributes (here, 'Name', 'Some-Attribute',
    'Another-Attribute'), and the values are the corresponding attribute values.

  Raises:
    InvalidJarError: if the manifest section is not well-formed.
  """
  # Join continuation lines.
  section = section.replace('\n ', '').rstrip('\n')
  if not section:
    return {}
  try:
    return dict(line.split(': ', 1) for line in section.split('\n'))
  except ValueError:
    raise InvalidJarError('%s: Invalid manifest %r' % (jar_file_name, section))
