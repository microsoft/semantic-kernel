# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Helper methods for record-set transactions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import files


DEFAULT_PATH = 'transaction.yaml'


class Error(exceptions.Error):
  """Base exception for all transaction errors."""


class TransactionFileAlreadyExists(Error):
  """Transaction file already exists."""


class UnableToAccessTransactionFile(Error):
  """Unable to access transaction file."""


class TransactionFileNotFound(Error):
  """Transaction file not found."""


class CorruptedTransactionFileError(Error):

  def __init__(self):
    super(CorruptedTransactionFileError, self).__init__(
        'Corrupted transaction file.\n\n'
        'Please abort and start a new transaction.')


class RecordDoesNotExist(Error):
  """Specified record-set does not exist."""


def WriteToYamlFile(yaml_file, change):
  """Writes the given change in yaml format to the given file.

  Args:
    yaml_file: file, File into which the change should be written.
    change: Change, Change to be written out.
  """
  resource_printer.Print([change], print_format='yaml', out=yaml_file)


def _RecordSetsFromDictionaries(messages, record_set_dictionaries):
  """Converts list of record-set dictionaries into list of ResourceRecordSets.

  Args:
    messages: Messages object for the API with Record Sets to be created.
    record_set_dictionaries: [{str:str}], list of record-sets as dictionaries.

  Returns:
    list of ResourceRecordSets equivalent to given list of yaml record-sets
  """
  record_sets = []
  for record_set_dict in record_set_dictionaries:
    record_set = messages.ResourceRecordSet()
    # Need to assign kind to default value for useful equals comparisons.
    record_set.kind = record_set.kind
    record_set.name = record_set_dict['name']
    record_set.ttl = record_set_dict['ttl']
    record_set.type = record_set_dict['type']
    record_set.rrdatas = record_set_dict['rrdatas']
    record_sets.append(record_set)
  return record_sets


def ChangeFromYamlFile(yaml_file, api_version='v1'):
  """Returns the change contained in the given yaml file.

  Args:
    yaml_file: file, A yaml file with change.
    api_version: [str], the api version to use for creating the change object.

  Returns:
    Change, the change contained in the given yaml file.

  Raises:
    CorruptedTransactionFileError: if the record_set_dictionaries are invalid
  """
  messages = apis.GetMessagesModule('dns', api_version)
  try:
    change_dict = yaml.load(yaml_file) or {}
  except yaml.YAMLParseError:
    raise CorruptedTransactionFileError()
  if (change_dict.get('additions') is None or
      change_dict.get('deletions') is None):
    raise CorruptedTransactionFileError()
  change = messages.Change()
  change.additions = _RecordSetsFromDictionaries(
      messages, change_dict['additions'])
  change.deletions = _RecordSetsFromDictionaries(
      messages, change_dict['deletions'])
  return change


class TransactionFile(object):
  """Context for reading/writing from/to a transaction file."""

  def __init__(self, trans_file_path, mode='r'):
    if not os.path.isfile(trans_file_path):
      raise TransactionFileNotFound(
          'Transaction not found at [{0}]'.format(trans_file_path))

    self.__trans_file_path = trans_file_path

    try:
      if mode == 'r':
        self.__trans_file = files.FileReader(trans_file_path)
      elif mode == 'w':
        self.__trans_file = files.FileWriter(trans_file_path)
      else:
        raise ValueError('Unrecognized mode [{}]'.format(mode))
    except IOError as exp:
      msg = 'Unable to open transaction [{0}] because [{1}]'
      msg = msg.format(trans_file_path, exp)
      raise UnableToAccessTransactionFile(msg)

  def __enter__(self):
    return self.__trans_file

  def __exit__(self, typ, value, traceback):
    self.__trans_file.close()

    if typ is IOError or typ is yaml.Error:
      msg = 'Unable to read/write transaction [{0}] because [{1}]'
      msg = msg.format(self.__trans_file_path, value)
      raise UnableToAccessTransactionFile(msg)
