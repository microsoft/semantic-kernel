# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Library for safe migrations of config files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import shutil

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
from googlecloudsdk.third_party.appengine.datastore import datastore_index_xml
from googlecloudsdk.third_party.appengine.tools import cron_xml_parser
from googlecloudsdk.third_party.appengine.tools import dispatch_xml_parser
from googlecloudsdk.third_party.appengine.tools import queue_xml_parser


_CRON_DESC = 'Translates a cron.xml into cron.yaml.'
_QUEUE_DESC = 'Translates a queue.xml into queue.yaml.'
_DISPATCH_DESC = 'Translates a dispatch.xml into dispatch.yaml.'
_INDEX_DESC = 'Translates a datastore-indexes.xml into index.yaml.'


class MigrationError(exceptions.Error):
  pass


def _Bakify(file_path):
  return file_path + '.bak'


class MigrationResult(object):
  """The changes that are about to be applied on a declarative form.

  Args:
    new_files: {str, str} a mapping from absolute file path to new contents of
      the file, or None if the file should be deleted.
  """

  def __init__(self, new_files):
    self.new_files = new_files

  def __eq__(self, other):
    return self.new_files == other.new_files

  def __ne__(self, other):
    return not self == other

  def _Backup(self):
    for path in self.new_files.keys():
      bak_path = _Bakify(path)
      if not os.path.isfile(path):
        continue
      if os.path.exists(bak_path):
        raise MigrationError(
            'Backup file path [{}] already exists.'.format(bak_path))
      log.err.Print('Copying [{}] to [{}]'.format(path, bak_path))
      shutil.copy2(path, bak_path)

  def _WriteFiles(self):
    for path, new_contents in self.new_files.items():
      if new_contents is None:
        log.err.Print('Deleting [{}]'.format(path))
        os.remove(path)
      else:
        log.err.Print('{} [{}]'.format(
            'Overwriting' if os.path.exists(path) else 'Writing', path))
        files.WriteFileContents(path, new_contents)

  def Apply(self):
    """Backs up first, then deletes, overwrites and writes new files."""
    self._Backup()
    self._WriteFiles()


def _MigrateCronXML(src, dst):
  """Migration script for cron.xml."""
  xml_str = files.ReadFileContents(src)
  yaml_contents = cron_xml_parser.GetCronYaml(None, xml_str)
  new_files = {src: None, dst: yaml_contents}
  return MigrationResult(new_files)


def _MigrateQueueXML(src, dst):
  """Migration script for queue.xml."""
  xml_str = files.ReadFileContents(src)
  yaml_contents = queue_xml_parser.GetQueueYaml(None, xml_str)
  new_files = {src: None, dst: yaml_contents}
  return MigrationResult(new_files)


def _MigrateDispatchXML(src, dst):
  """Migration script for dispatch.xml."""
  xml_str = files.ReadFileContents(src)
  yaml_contents = dispatch_xml_parser.GetDispatchYaml(None, xml_str)
  new_files = {src: None, dst: yaml_contents}
  return MigrationResult(new_files)


def _MigrateDatastoreIndexXML(src, dst, auto_src=None):
  """Migration script for datastore-indexes.xml."""
  xml_str = files.ReadFileContents(src)
  indexes = datastore_index_xml.IndexesXmlToIndexDefinitions(xml_str)
  new_files = {src: None}
  if auto_src:
    xml_str_2 = files.ReadFileContents(auto_src)
    auto_indexes = datastore_index_xml.IndexesXmlToIndexDefinitions(xml_str_2)
    indexes.indexes += auto_indexes.indexes
    new_files[auto_src] = None
  new_files[dst] = indexes.ToYAML()
  return MigrationResult(new_files)


class MigrationScript(object):
  """Object representing a migration script and its metadata.

  Attributes:
    migrate_fn: a function which accepts a variable number of self-defined
      kwargs and returns a MigrationResult.
    description: str, description for help texts and prompts.
  """

  def __init__(self, migrate_fn, description):
    self.migrate_fn = migrate_fn
    self.description = description


def Run(entry, **kwargs):
  """Run a migration entry, with prompts and warnings.

  Args:
    entry: MigrationScript, the entry to run.
    **kwargs: keyword args for the migration function.
  """
  result = entry.migrate_fn(**kwargs)  # Get errors early
  log.warning('Please *back up* existing files.\n')
  console_io.PromptContinue(
      entry.description, default=True,
      prompt_string='Do you want to run the migration script now?',
      cancel_on_no=True)
  result.Apply()


# Registry of all migration entries. Key corresponds to command name
REGISTRY = {
    'cron-xml-to-yaml': MigrationScript(_MigrateCronXML, _CRON_DESC),
    'queue-xml-to-yaml': MigrationScript(_MigrateQueueXML, _QUEUE_DESC),
    'dispatch-xml-to-yaml': MigrationScript(_MigrateDispatchXML,
                                            _DISPATCH_DESC),
    'datastore-indexes-xml-to-yaml': MigrationScript(_MigrateDatastoreIndexXML,
                                                     _INDEX_DESC),
}

