#!/usr/bin/env python
#
# Copyright 2012 Google Inc. All Rights Reserved.
"""Python script for interacting with BigQuery."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cmd
import collections
import datetime
import functools
import json
import logging
import os
import pdb
import re
import shlex
import sys
import time
import traceback
import types
from typing import List, Optional, Tuple

__author__ = 'craigcitro@google.com (Craig Citro)'

# Add to path dependencies if present.
_THIRD_PARTY_DIR = os.path.join(os.path.dirname(__file__), 'third_party')
if os.path.isdir(_THIRD_PARTY_DIR) and _THIRD_PARTY_DIR not in sys.path:
  sys.path.insert(0, _THIRD_PARTY_DIR)

# This strange import below ensures that the correct 'google' is imported.
# We reload after sys.path is updated, so we know if we'll find our google
# before any other.
# pylint:disable=g-import-not-at-top
if 'google' in sys.modules:
  import google
  try:
    reload(google)
  except NameError:
    import importlib
    importlib.reload(google)


from absl import app
from absl import flags

import googleapiclient
import httplib2

from pyglib import appcommands

import yaml

# pylint: disable=g-bad-import-order
import six
from six.moves import input
from six.moves import map
from six.moves import range
from six.moves import zip
import six.moves.http_client
import termcolor
import textwrap

import table_formatter
import bigquery_client
import bq_flags
import bq_utils
import credential_loader

from utils import bq_error
from utils import bq_logging

flags.adopt_module_key_flags(bq_flags)

FLAGS = flags.FLAGS
# These are long names.
# pylint: disable=g-bad-name
JobReference = bigquery_client.ApiClientHelper.JobReference
ProjectReference = bigquery_client.ApiClientHelper.ProjectReference
DatasetReference = bigquery_client.ApiClientHelper.DatasetReference
TableReference = bigquery_client.ApiClientHelper.TableReference
TransferConfigReference = (
    bigquery_client.ApiClientHelper.TransferConfigReference)
TransferRunReference = bigquery_client.ApiClientHelper.TransferRunReference
TransferLogReference = bigquery_client.ApiClientHelper.TransferLogReference
NextPageTokenReference = bigquery_client.ApiClientHelper.NextPageTokenReference
ModelReference = bigquery_client.ApiClientHelper.ModelReference
RoutineReference = bigquery_client.ApiClientHelper.RoutineReference
RowAccessPolicyReference = (
    bigquery_client.ApiClientHelper.RowAccessPolicyReference)
EncryptionServiceAccount = (
    bigquery_client.ApiClientHelper.EncryptionServiceAccount)
BigqueryClient = bigquery_client.BigqueryClient
ApiClientHelper = bigquery_client.ApiClientHelper
JobIdGenerator = bigquery_client.JobIdGenerator
JobIdGeneratorIncrementing = bigquery_client.JobIdGeneratorIncrementing
JobIdGeneratorRandom = bigquery_client.JobIdGeneratorRandom
JobIdGeneratorFingerprint = bigquery_client.JobIdGeneratorFingerprint
ReservationReference = bigquery_client.ApiClientHelper.ReservationReference
BetaReservationReference = bigquery_client.ApiClientHelper.BetaReservationReference
CapacityCommitmentReference = bigquery_client.ApiClientHelper.CapacityCommitmentReference  # pylint: disable=line-too-long
ReservationAssignmentReference = bigquery_client.ApiClientHelper.ReservationAssignmentReference  # pylint: disable=line-too-long
BetaReservationAssignmentReference = bigquery_client.ApiClientHelper.BetaReservationAssignmentReference  # pylint: disable=line-too-long
ConnectionReference = bigquery_client.ApiClientHelper.ConnectionReference

# pylint: enable=g-bad-name

CONNECTION_ID_PATTERN = re.compile(r'[\w-]+')
_RANGE_PATTERN = re.compile(r'^\[(\S+.+\S+), (\S+.+\S+)\)$')

_DELIMITER_MAP = {
    'tab': '\t',
    '\\t': '\t',
}
_DDL_OPERATION_MAP = {
    'SKIP': 'Skipped',
    'CREATE': 'Created',
    'REPLACE': 'Replaced',
    'ALTER': 'Altered',
    'DROP': 'Dropped',
}
_PARQUET_LIST_INFERENCE_DESCRIPTION = (
    'Use schema inference specifically for Parquet LIST logical type.\n It '
    'checks whether the LIST node is in the standard form as documented in:\n '
    'https://github.com/apache/parquet-format/blob/master/LogicalTypes.md#lists\n'
    '  <optional | required> group <name> (LIST) {\n    repeated group list '
    '{\n      <optional | required> <element-type> element;\n    }\n  }\n '
    'Returns the "element" node in list_element_node. The corresponding field '
    'for the LIST node in the converted schema is treated as if the node has '
    'the following schema:\n repeated <element-type> <name>\n This means nodes'
    ' "list" and "element" are omitted.\n\n Otherwise, the LIST node must be '
    'in one of the forms described by the backward-compatibility rules as '
    'documented in:\n '
    'https://github.com/apache/parquet-format/blob/master/LogicalTypes.md#backward-compatibility-rules\n'
    ' <optional | required> group <name> (LIST) {\n   repeated <element-type> '
    '<element-name>\n }\n Returns the <element-name> node in '
    'list_element_node. The corresponding field for the LIST node in the '
    'converted schema is treated as if the node has the following schema:\n '
    'repeated <element-type> <name>\n This means the element node is omitted.')
# These aren't relevant for user-facing docstrings:
# pylint: disable=g-doc-return-or-yield
# pylint: disable=g-doc-args
# TODO(user): Write some explanation of the structure of this file.

####################
# flags processing
####################


def _FormatDataTransferIdentifiers(client, transfer_identifier):
  """Formats a transfer config or run identifier.

  Transfer configuration/run commands should be able to support different
  formats of how the user could input the project information. This function
  will take the user input and create a uniform transfer config or
  transfer run reference that can be used for various commands.

  This function will also set the client's project id to the specified
  project id.

  Returns:
    The formatted transfer config or run.
  """

  formatted_identifier = transfer_identifier
  match = re.search(r'projects/([^/]+)', transfer_identifier)
  if not match:
    formatted_identifier = ('projects/' +
                            client.GetProjectReference().projectId + '/' +
                            transfer_identifier)
  else:
    client.project_id = match.group(1)

  return formatted_identifier


def _FormatProjectIdentifier(client, project_id):
  """Formats a project identifier.

  If the user specifies a project with "projects/${PROJECT_ID}", isolate the
  project id and return it.

  This function will also set the client's project id to the specified
  project id.

  Returns:
    The project is.
  """

  formatted_identifier = project_id
  match = re.search(r'projects/([^/]+)', project_id)
  if match:
    formatted_identifier = match.group(1)
    client.project_id = formatted_identifier

  return formatted_identifier


def _ValidateGlobalFlags():
  """Validate combinations of global flag values."""
  if FLAGS.service_account and FLAGS.use_gce_service_account:
    raise app.UsageError(
        'Cannot specify both --service_account and --use_gce_service_account.')


def ValidateAtMostOneSelected(*args):
  """Validates that at most one of the argument flags is selected.

  Returns:
    True if more than 1 flag was selected, False if 1 or 0 were selected.
  """
  count = 0
  for arg in args:
    if arg:
      count += 1
  return count > 1


def _ConfigureLogging(logging_utils):
  try:
    logging_utils.ConfigurePythonLogger(FLAGS.apilog)
  except IOError as e:
    if e.errno == 2:
      print('Could not configure logging. %s: %s' % (e.strerror, e.filename))
      sys.exit(1)
    raise e


def _UseServiceAccount():
  return bool(
      FLAGS.use_gce_service_account
      or FLAGS.service_account
  )


def _GetFormatterFromFlags(secondary_format='sparse'):
  if FLAGS['format'].present:
    return table_formatter.GetFormatter(FLAGS.format)
  else:
    return table_formatter.GetFormatter(secondary_format)


def _PrintDryRunInfo(job):
  """Prints the dry run info."""
  num_bytes = job['statistics']['query']['totalBytesProcessed']
  num_bytes_accuracy = job['statistics']['query'].get(
      'totalBytesProcessedAccuracy', 'PRECISE')
  if FLAGS.format in ['prettyjson', 'json']:
    bq_utils.PrintFormattedJsonObject(job)
  elif FLAGS.format == 'csv':
    print(num_bytes)
  else:
    if job['statistics']['query'].get('statementType', '') == 'LOAD_DATA':
      print(
          'Query successfully validated. Assuming the files are not modified, '
          'running this query will process %s files loading %s bytes of data.' %
          (
              job['statistics']['query']['loadQueryStatistics']['inputFiles'],
              job['statistics']['query']['loadQueryStatistics']
              ['inputFileBytes'],
          ))
    elif num_bytes_accuracy == 'PRECISE':
      print(
          'Query successfully validated. Assuming the tables are not modified, '
          'running this query will process %s bytes of data.' % (num_bytes,))
    elif num_bytes_accuracy == 'LOWER_BOUND':
      print(
          'Query successfully validated. Assuming the tables are not modified, '
          'running this query will process lower bound of %s bytes of data.' %
          (num_bytes,))
    elif num_bytes_accuracy == 'UPPER_BOUND':
      print(
          'Query successfully validated. Assuming the tables are not modified, '
          'running this query will process upper bound of %s bytes of data.' %
          (num_bytes,))
    else:
      if job['statistics']['query']['statementType'] == 'CREATE_MODEL':
        print('Query successfully validated. The number of bytes that will '
              'be processed by this query cannot be calculated automatically. '
              'More information about this can be seen in '
              'https://cloud.google.com/bigquery-ml/pricing#dry_run')
      else:
        print('Query successfully validated. Assuming the tables are not '
              'modified, running this query will process %s of data and the '
              'accuracy is unknown because of federated tables or clustered '
              'tables.' % (num_bytes,))


def _GetJobIdFromFlags():
  """Returns the job id or job generator from the flags."""
  if FLAGS.fingerprint_job_id and FLAGS.job_id:
    raise app.UsageError(
        'The fingerprint_job_id flag cannot be specified with the job_id '
        'flag.')
  if FLAGS.fingerprint_job_id:
    return JobIdGeneratorFingerprint()
  elif FLAGS.job_id is None:
    return JobIdGeneratorIncrementing(JobIdGeneratorRandom())
  elif FLAGS.job_id:
    return FLAGS.job_id
  else:
    # User specified a job id, but it was empty. Let the
    # server come up with a job id.
    return None


def _GetWaitPrinterFactoryFromFlags():
  """Returns the default wait_printer_factory to use while waiting for jobs."""
  if FLAGS.quiet:
    return BigqueryClient.QuietWaitPrinter
  if FLAGS.headless:
    return BigqueryClient.TransitionWaitPrinter
  return BigqueryClient.VerboseWaitPrinter


def _RawInput(message):
  try:
    return input(message)
  except EOFError:
    if sys.stdin.isatty():
      print('\nGot EOF; exiting.')
    else:
      print('\nGot EOF; exiting. Is your input from a terminal?')
    sys.exit(1)


def _PromptWithDefault(message):
  """Prompts user with message, return key pressed or '' on enter."""
  if FLAGS.headless:
    print('Running --headless, accepting default for prompt: %s' % (message,))
    return ''
  return _RawInput(message).lower()


def _PromptYN(message):
  """Prompts user with message, returning the key 'y', 'n', or '' on enter."""
  response = None
  while response not in ['y', 'n', '']:
    response = _PromptWithDefault(message)
  return response


def _NormalizeFieldDelimiter(field_delimiter):
  """Validates and returns the correct field_delimiter."""
  # The only non-string delimiter we allow is None, which represents
  # no field delimiter specified by the user.
  if field_delimiter is None:
    return field_delimiter

  # Allow TAB and \\t substitution.
  key = field_delimiter.lower()
  return _DELIMITER_MAP.get(key, field_delimiter)


def _ValidateHivePartitioningOptions(hive_partitioning_mode):
  """Validates the string provided is one the API accepts.

  Should not receive None as an input, since that will fail the comparison.
  Args:
    hive_partitioning_mode: String representing which hive partitioning mode is
      requested.  Only 'AUTO' and 'STRINGS' are supported.
  """
  if hive_partitioning_mode not in ['AUTO', 'STRINGS', 'CUSTOM']:
    raise app.UsageError(
        'Only the following hive partitioning modes are supported: "AUTO", '
        '"STRINGS" and "CUSTOM"')




def _ParseLabels(labels):
  """Parses a list of user-supplied strings representing labels.

  Args:
    labels: A list of user-supplied strings representing labels.  It is expected
      to be in the format "key:value".

  Returns:
    A dict mapping label keys to label values.

  Raises:
    UsageError: Incorrect label arguments were supplied.
  """
  labels_dict = {}
  for key_value in labels:
    k, _, v = key_value.partition(':')
    k = k.strip()
    if k in labels_dict:
      raise app.UsageError('Cannot specify label key "%s" multiple times' % k)
    if k.strip():
      labels_dict[k.strip()] = v.strip()
  return labels_dict


def IsRangeBoundaryUnbounded(value):
  return value.upper() == 'UNBOUNDED' or value.upper() == 'NULL'


def _ParseRangeString(value: str) -> Optional[Tuple[str, str]]:
  match = _RANGE_PATTERN.match(value)
  if not match:
    return None
  start, end = match.groups()
  return start, end


class TablePrinter(object):
  """Base class for printing a table, with a default implementation."""

  def __init__(self, **kwds):
    super(TablePrinter, self).__init__()
    # Most extended classes will require state.
    for key, value in six.iteritems(kwds):
      setattr(self, key, value)

  @staticmethod
  def _ValidateFields(fields, formatter):
    if isinstance(formatter, table_formatter.CsvFormatter):
      for field in fields:
        if field['type'].upper() == 'RECORD':
          raise app.UsageError(('Error printing table: Cannot print record '
                                'field "%s" in CSV format.') % field['name'])
        if field.get('mode', 'NULLABLE').upper() == 'REPEATED':
          raise app.UsageError(('Error printing table: Cannot print repeated '
                                'field "%s" in CSV format.') % (field['name']))

  @staticmethod
  def _NormalizeRecord(field, value):
    """Returns bq-specific formatting of a RECORD type."""
    result = collections.OrderedDict()
    for subfield, subvalue in zip(field.get('fields', []), value):
      result[subfield.get('name', '')] = TablePrinter._NormalizeField(
          subfield, subvalue)
    return result

  @staticmethod
  def _NormalizeTimestamp(unused_field, value):
    """Returns bq-specific formatting of a TIMESTAMP type."""
    try:
      date = datetime.datetime.fromtimestamp(
          0,
          tz=datetime.timezone.utc) + datetime.timedelta(seconds=float(value))
      # Remove the extra timezone info "+00:00" at the end of the date.
      date = date.replace(tzinfo=None)
      # Our goal is the equivalent of '%Y-%m-%d %H:%M:%S' via strftime but that
      # doesn't work for dates with years prior to 1900.  Instead we zero out
      # fractional seconds then call isoformat with a space separator.
      date = date.replace(microsecond=0)
      return date.isoformat(' ')
    except ValueError:
      return '<date out of range for display>'

  @staticmethod
  def _NormalizeRange(field, value):
    """Returns bq-specific formatting of a RANGE type."""
    parsed = _ParseRangeString(value)
    if parsed is None:
      return '<invalid range>'
    start, end = parsed

    if field.get('rangeElementType').get('type').upper() != 'TIMESTAMP':
      start = start.upper() if IsRangeBoundaryUnbounded(start) else start
      end = end.upper() if IsRangeBoundaryUnbounded(end) else end
      return '[%s, %s)' % (start, end)

    normalized_start = (
        start.upper()
        if IsRangeBoundaryUnbounded(start)
        else TablePrinter._NormalizeTimestamp(field, start)
    )
    normalized_end = (
        end.upper()
        if IsRangeBoundaryUnbounded(end)
        else TablePrinter._NormalizeTimestamp(field, end)
    )
    return '[%s, %s)' % (normalized_start, normalized_end)

  _FIELD_NORMALIZERS = {
      'RECORD': _NormalizeRecord.__func__,
      'TIMESTAMP': _NormalizeTimestamp.__func__,
      'RANGE': _NormalizeRange.__func__,
  }

  @staticmethod
  def _NormalizeField(field, value):
    """Returns bq-specific formatting of a field."""
    if value is None:
      return None
    normalizer = TablePrinter._FIELD_NORMALIZERS.get(
        field.get('type', '').upper(), lambda _, x: x)
    if field.get('mode', '').upper() == 'REPEATED':
      return [normalizer(field, value) for value in value]
    return normalizer(field, value)

  @staticmethod
  def _MaybeConvertToJson(value):
    """Converts dicts and lists to JSON; returns everything else as-is."""
    if isinstance(value, dict) or isinstance(value, list):
      return json.dumps(value, separators=(',', ':'), ensure_ascii=False)
    return value

  @staticmethod
  def _FormatRow(fields, row, formatter):
    """Convert fields in a single row to bq-specific formatting."""
    values = [
        TablePrinter._NormalizeField(field, value)
        for field, value in zip(fields, row)
    ]
    # Convert complex values to JSON if we're not already outputting as such.
    if not isinstance(formatter, table_formatter.JsonFormatter):
      values = map(TablePrinter._MaybeConvertToJson, values)
    # Convert NULL values to strings for CSV and non-JSON formats.
    if isinstance(formatter, table_formatter.CsvFormatter):
      values = ['' if value is None else value for value in values]
    elif not isinstance(formatter, table_formatter.JsonFormatter):
      values = ['NULL' if value is None else value for value in values]
    return values

  def PrintTable(self, fields, rows):
    formatter = _GetFormatterFromFlags(secondary_format='pretty')
    self._ValidateFields(fields, formatter)
    formatter.AddFields(fields)
    formatter.AddRows(
        TablePrinter._FormatRow(fields, row, formatter) for row in rows)
    formatter.Print()


class Factory(object):
  """Class encapsulating factory creation of BigqueryClient."""
  _BIGQUERY_CLIENT_FACTORY = None

  class ClientTablePrinter(object):
    _TABLE_PRINTER = None

    @classmethod
    def GetTablePrinter(cls):
      if cls._TABLE_PRINTER is None:
        cls._TABLE_PRINTER = TablePrinter()
      return cls._TABLE_PRINTER

    @classmethod
    def SetTablePrinter(cls, printer):
      if not isinstance(printer, TablePrinter):
        raise TypeError('Printer must be an instance of TablePrinter.')
      cls._TABLE_PRINTER = printer

  @classmethod
  def GetBigqueryClientFactory(cls):
    if cls._BIGQUERY_CLIENT_FACTORY is None:
      cls._BIGQUERY_CLIENT_FACTORY = bigquery_client.BigqueryClient
    return cls._BIGQUERY_CLIENT_FACTORY

  @classmethod
  def SetBigqueryClientFactory(cls, factory):
    if not issubclass(factory, bigquery_client.BigqueryClient):
      raise TypeError('Factory must be subclass of BigqueryClient.')
    cls._BIGQUERY_CLIENT_FACTORY = factory


class Client(object):
  """Class caching bigquery_client.BigqueryClient based on arguments."""
  client_cache = {}

  @staticmethod
  def _CollectArgs(config_logging=True, **kwds):
    """Collect and combine FLAGS and kwds to create BQ Client.

    Args:
      config_logging: if True, set python logging according to --apilog.
      **kwds: keyword arguments for creating BigqueryClient.
    """

    def KwdsOrFlags(name):
      return kwds[name] if name in kwds else getattr(FLAGS, name)

    # Note that we need to handle possible initialization tasks
    # for the case of being loaded as a library.
    bq_utils.ProcessBigqueryrc()
    if config_logging:
      _ConfigureLogging(bq_logging)

    if FLAGS.httplib2_debuglevel:
      httplib2.debuglevel = FLAGS.httplib2_debuglevel

    client_args = {}
    global_args = (
        'credential_file',
        'job_property',
        'project_id',
        'dataset_id',
        'trace',
        'sync',
        'api',
        'api_version',
        'quota_project_id',
    )
    for name in global_args:
      client_args[name] = KwdsOrFlags(name)

    client_args['wait_printer_factory'] = _GetWaitPrinterFactoryFromFlags()
    if FLAGS.discovery_file:
      with open(FLAGS.discovery_file) as f:
        client_args['discovery_document'] = f.read()
    client_args['enable_resumable_uploads'] = (
        True if FLAGS.enable_resumable_uploads is None else
        FLAGS.enable_resumable_uploads)
    if FLAGS.max_rows_per_request:
      client_args['max_rows_per_request'] = FLAGS.max_rows_per_request

    return client_args

  @staticmethod
  def Create(config_logging=True, **kwds):
    """Build a new BigqueryClient configured from kwds and FLAGS.

    Args:
      config_logging: if True, set python logging according to --apilog.
      **kwds: keyword arguments for creating BigqueryClient.
    """
    # Resolve flag values first.
    client_args = Client._CollectArgs(config_logging, **kwds)

    if 'credentials' in kwds:
      logging.info('Credentials passed in directly')
      credentials = kwds.pop('credentials')
    else:
      logging.info('Credentials loaded using oauth2client')
      credentials = credential_loader.GetCredentialsFromFlags()
    assert credentials is not None

    bigquery_client_factory = Factory.GetBigqueryClientFactory()
    return bigquery_client_factory(credentials=credentials, **client_args)


  @classmethod
  def _GetClientCacheKey(cls, **kwds):
    client_args = Client._CollectArgs(**kwds)
    return ('client_args={client_args},'
            'service_account_credential_file={service_account_credential_file},'
            'apilog={apilog},'.format(
                client_args=client_args,
                service_account_credential_file=FLAGS
                .service_account_credential_file,
                apilog=FLAGS.apilog))

  @classmethod
  def Get(cls):
    """Return a BigqueryClient initialized from flags."""
    cache_key = Client._GetClientCacheKey()
    if cache_key not in cls.client_cache:
      try:
        cls.client_cache[cache_key] = Client.Create()
      except ValueError as e:
        # Convert constructor parameter errors into flag usage errors.
        raise app.UsageError(e)

    return cls.client_cache[cache_key]

  @classmethod
  def Delete(cls):
    """Delete the existing client.

    This is needed when flags have changed, and we need to force
    client recreation to reflect new flag values.
    """
    cache_key = Client._GetClientCacheKey()
    if cache_key in cls.client_cache:
      del cls.client_cache[cache_key]


def _Typecheck(obj, types, message=None):  # pylint: disable=redefined-outer-name
  """Raises a user error if obj is not an instance of types."""
  if not isinstance(obj, types):
    message = message or 'Type of %s is not one of %s' % (obj, types)
    raise app.UsageError(message)


# TODO(user): This code uses more than the average amount of
# Python magic. Explain what the heck is going on throughout.
class NewCmd(appcommands.Cmd):
  """Featureful extension of appcommands.Cmd."""

  def __init__(self, name, flag_values):
    super(NewCmd, self).__init__(name, flag_values)
    run_with_args = getattr(self, 'RunWithArgs', None)
    self._new_style = isinstance(run_with_args, types.MethodType)
    if self._new_style:
      func = run_with_args.__func__
      code = func.__code__  # pylint: disable=redefined-outer-name
      self._full_arg_list = list(code.co_varnames[:code.co_argcount])
      # TODO(user): There might be some corner case where this
      # is *not* the right way to determine bound vs. unbound method.
      if isinstance(run_with_args.__self__, run_with_args.__self__.__class__):
        self._full_arg_list.pop(0)
      self._max_args = len(self._full_arg_list)
      self._min_args = self._max_args - len(func.__defaults__ or [])
      self._star_args = bool(code.co_flags & 0x04)
      self._star_kwds = bool(code.co_flags & 0x08)
      if self._star_args:
        self._max_args = sys.maxsize
      self.surface_in_shell = True
      self.__doc__ = self.RunWithArgs.__doc__
    elif self.Run.__func__ is NewCmd.Run.__func__:
      raise appcommands.AppCommandsError(
          'Subclasses of NewCmd must override Run or RunWithArgs')

  def __getattr__(self, name):
    if name in self._command_flags:
      return self._command_flags[name].value
    return super(NewCmd, self).__getattribute__(name)

  def _GetFlag(self, flagname):
    if flagname in self._command_flags:
      return self._command_flags[flagname]
    else:
      return None

  def _CheckFlags(self):
    """Validate flags after command specific flags have been loaded.

    This function will run through all values in appcommands._cmd_argv and
    pick out any unused flags and verify their validity.  If the flag is
    not defined, we will print the flags.FlagsError text and exit; otherwise,
    we will print a positioning error message and exit.  Print statements
    were used in this case because raising app.UsageError caused the usage
    help text to be printed.

    If no extraneous flags exist, this function will do nothing.
    """
    unused_flags = [
        f for f in appcommands.GetCommandArgv()
        if f.startswith('--') or f.startswith('-')
    ]
    for flag in unused_flags:
      flag_name = flag[4:] if flag.startswith('--no') else flag[2:]
      flag_name = flag_name.split('=')[0]
      if flag_name not in FLAGS:
        print(("FATAL Flags parsing error: Unknown command line flag '%s'\n"
               "Run 'bq help' to get help" % flag))
        sys.exit(1)
      else:
        print(("FATAL Flags positioning error: Flag '%s' appears after final "
               'command line argument. Please reposition the flag.\n'
               "Run 'bq help' to get help." % flag))
        sys.exit(1)

  def Run(self, argv):
    """Run this command.

    If self is a new-style command, we set up arguments and call
    self.RunWithArgs, gracefully handling exceptions. If not, we
    simply call self.Run(argv).

    Args:
      argv: List of arguments as strings.

    Returns:
      0 on success, nonzero on failure.
    """
    self._CheckFlags()
    self._debug_mode = FLAGS.debug_mode
    if not self._new_style:
      return super(NewCmd, self).Run(argv)

    original_values = {
        name: self._command_flags[name].value for name in self._command_flags
    }
    original_presence = {
        name: self._command_flags[name].present for name in self._command_flags
    }
    try:
      args = self._command_flags(argv)[1:]
      for flag_name in self._command_flags:
        value = self._command_flags[flag_name].value
        setattr(self, flag_name, value)
        if value == original_values[flag_name]:
          original_values.pop(flag_name)
      new_args = []
      for argname in self._full_arg_list[:self._min_args]:
        flag = self._GetFlag(argname)
        if flag is not None and flag.present:
          new_args.append(flag.value)
        elif args:
          new_args.append(args.pop(0))
        else:
          print('Not enough positional args, still looking for %s' % (argname,))
          if self.usage:
            print('Usage: %s' % (self.usage,))
          return 1

      new_kwds = {}
      for argname in self._full_arg_list[self._min_args:]:
        flag = self._GetFlag(argname)
        if flag is not None and flag.present:
          new_kwds[argname] = flag.value
        elif args:
          new_kwds[argname] = args.pop(0)

      if args and not self._star_args:
        print('Too many positional args, still have %s' % (args,))
        return 1
      new_args.extend(args)

      if self._debug_mode:
        return self.RunDebug(new_args, new_kwds)
      else:
        return self.RunSafely(new_args, new_kwds)
    finally:
      for flag, value in six.iteritems(original_values):
        setattr(self, flag, value)
        self._command_flags[flag].value = value
        self._command_flags[flag].present = original_presence[flag]

  def RunCmdLoop(self, argv):
    """Hook for use in cmd.Cmd-based command shells."""
    try:
      args = shlex.split(argv)
    except ValueError as e:
      raise SyntaxError(bq_logging.EncodeForPrinting(e)) from e
    return self.Run([self._command_name] + args)

  def _HandleError(self, e):
    message = bq_logging.EncodeForPrinting(e)
    if isinstance(e, bq_error.BigqueryClientConfigurationError):
      message += ' Try running "bq init".'
    print('Exception raised in %s operation: %s' %
          (self._command_name, message))
    return 1

  def RunDebug(self, args, kwds):
    """Run this command in debug mode."""
    try:
      return_value = self.RunWithArgs(*args, **kwds)
    # pylint: disable=broad-except
    except (BaseException, googleapiclient.errors.ResumableUploadError) as e:
      # Don't break into the debugger for expected exceptions.
      if (isinstance(e, app.UsageError) or
          (isinstance(e, bq_error.BigqueryError) and
           not isinstance(e, bq_error.BigqueryInterfaceError)) or
          isinstance(e, googleapiclient.errors.ResumableUploadError)):
        return self._HandleError(e)
      print()
      print('****************************************************')
      print('**  Unexpected Exception raised in bq execution!  **')
      if FLAGS.headless:
        print('**  --headless mode enabled, exiting.             **')
        print('**  See STDERR for traceback.                     **')
      else:
        print('**  --debug_mode enabled, starting pdb.           **')
      print('****************************************************')
      print()
      traceback.print_exc()
      print()
      if not FLAGS.headless:
        pdb.post_mortem()
      return 1
    return return_value

  def RunSafely(self, args, kwds):
    """Run this command, turning exceptions into print statements."""
    try:
      return_value = self.RunWithArgs(*args, **kwds)
    except BaseException as e:
      return self._HandleError(e)
    return return_value


class BigqueryCmd(NewCmd):
  """Bigquery-specific NewCmd wrapper."""

  def _NeedsInit(self):
    """Returns true if this command requires the init command before running.

    Subclasses will override for any exceptional cases.
    """
    return (not _UseServiceAccount() and
            not (os.path.exists(bq_utils.GetBigqueryRcFilename()) or
                 os.path.exists(FLAGS.credential_file)))

  def Run(self, argv):
    """Bigquery commands run `init` before themselves if needed."""

    if FLAGS.debug_mode:
      cmd_flags = [
          FLAGS[f].serialize().strip() for f in FLAGS if FLAGS[f].present
      ]
      print(' '.join(sorted(set(f for f in cmd_flags if f))))

    if self._NeedsInit():
      appcommands.GetCommandByName('init').Run(['init'])
    return super(BigqueryCmd, self).Run(argv)

  def RunSafely(self, args, kwds):
    """Run this command, printing information about any exceptions raised."""
    try:
      return_value = self.RunWithArgs(*args, **kwds)
    except BaseException as e:
      return bq_utils.ProcessError(e, name=self._command_name)
    return return_value

  def PrintJobStartInfo(self, job):
    """Print a simple status line."""
    if FLAGS.format in ['prettyjson', 'json']:
      bq_utils.PrintFormattedJsonObject(job)
    else:
      reference = BigqueryClient.ConstructObjectReference(job)
      print('Successfully started %s %s' % (self._command_name, reference))

  def _ProcessCommandRc(self, fv):
    bq_utils.ProcessBigqueryrcSection(self._command_name, fv)


class _Load(BigqueryCmd):
  usage = """load <destination_table> <source> <schema>"""

  def __init__(self, name, fv):
    super(_Load, self).__init__(name, fv)
    flags.DEFINE_string(
        'field_delimiter',
        None,
        'The character that indicates the boundary between columns in the '
        'input file. "\\t" and "tab" are accepted names for tab.',
        short_name='F',
        flag_values=fv)
    flags.DEFINE_enum(
        'encoding',
        None,
        ['UTF-8', 'ISO-8859-1', 'UTF-16BE', 'UTF-16LE', 'UTF-32BE', 'UTF-32LE'],
        (
            'The character encoding used by the input file.  Options include:'
            '\n ISO-8859-1 (also known as Latin-1)'
            '\n UTF-8'
            '\n UTF-16BE (UTF-16 BigEndian)'
            '\n UTF-16LE (UTF-16 LittleEndian)'
            '\n UTF-32BE (UTF-32 BigEndian)'
            '\n UTF-32LE (UTF-32 LittleEndian)'
        ),
        short_name='E',
        flag_values=fv,
    )
    flags.DEFINE_integer(
        'skip_leading_rows',
        None,
        'The number of rows at the beginning of the source file to skip.',
        flag_values=fv)
    flags.DEFINE_string(
        'schema',
        None,
        'Either a filename or a comma-separated list of fields in the form '
        'name[:type].',
        flag_values=fv)
    flags.DEFINE_boolean(
        'replace',
        False,
        'If true existing data is erased when new data is loaded.',
        flag_values=fv)
    flags.DEFINE_string(
        'quote',
        None, 'Quote character to use to enclose records. Default is ". '
        'To indicate no quote character at all, use an empty string.',
        flag_values=fv)
    flags.DEFINE_integer(
        'max_bad_records',
        0,
        'Maximum number of bad records allowed before the entire job fails.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'allow_quoted_newlines',
        None,
        'Whether to allow quoted newlines in CSV import data.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'allow_jagged_rows',
        None, 'Whether to allow missing trailing optional columns '
        'in CSV import data.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'preserve_ascii_control_characters',
        None,
        'Whether to preserve embedded Ascii Control characters in CSV import '
        'data.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'ignore_unknown_values',
        None,
        'Whether to allow and ignore extra, unrecognized values in CSV or JSON '
        'import data.',
        flag_values=fv)
    flags.DEFINE_enum(
        'source_format',
        None, [
            'CSV', 'NEWLINE_DELIMITED_JSON', 'DATASTORE_BACKUP', 'AVRO',
            'PARQUET', 'ORC', 'THRIFT'
        ], 'Format of source data. Options include:'
        '\n CSV'
        '\n NEWLINE_DELIMITED_JSON'
        '\n DATASTORE_BACKUP'
        '\n AVRO'
        '\n PARQUET'
        '\n ORC'
        '\n THRIFT',
        flag_values=fv)
    flags.DEFINE_list(
        'projection_fields', [],
        'If sourceFormat is set to "DATASTORE_BACKUP", indicates which entity '
        'properties to load into BigQuery from a Cloud Datastore backup. '
        'Property names are case sensitive and must refer to top-level '
        'properties.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'autodetect',
        None,
        'Enable auto detection of schema and options for formats that are not '
        'self describing like CSV and JSON.',
        flag_values=fv)
    flags.DEFINE_multi_string(
        'schema_update_option',
        None,
        'Can be specified when append to a table, or replace a table partition.'
        ' When specified, the schema of the destination table will be updated '
        'with the schema of the new data. One or more of the following options '
        'can be specified:'
        '\n ALLOW_FIELD_ADDITION: allow new fields to be added'
        '\n ALLOW_FIELD_RELAXATION: allow relaxing required fields to nullable',
        flag_values=fv)
    flags.DEFINE_string(
        'null_marker',
        None, 'An optional custom string that will represent a NULL value'
        'in CSV import data.',
        flag_values=fv)
    flags.DEFINE_string(
        'time_partitioning_type',
        None,
        'Enables time based partitioning on the table and set the type. The '
        'default value is DAY, which will generate one partition per day. '
        'Other supported values are HOUR, MONTH, and YEAR.',
        flag_values=fv)
    flags.DEFINE_integer(
        'time_partitioning_expiration',
        None,
        'Enables time based partitioning on the table and sets the number of '
        'seconds for which to keep the storage for the partitions in the table.'
        ' The storage in a partition will have an expiration time of its '
        'partition time plus this value.',
        flag_values=fv)
    flags.DEFINE_string(
        'range_partitioning',
        None, 'Enables range partitioning on the table. The format should be '
        '"field,start,end,interval". The table will be partitioned based on the'
        ' value of the field. Field must be a top-level, non-repeated INT64 '
        'field. Start, end, and interval are INT64 values defining the ranges.',
        flag_values=fv)
    flags.DEFINE_string(
        'time_partitioning_field',
        None,
        'Enables time based partitioning on the table and the table will be '
        'partitioned based on the value of this field. If time based '
        'partitioning is enabled without this value, the table will be '
        'partitioned based on the loading time.',
        flag_values=fv)
    flags.DEFINE_string(
        'destination_kms_key',
        None,
        'Cloud KMS key for encryption of the destination table data.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'require_partition_filter',
        None,
        'Whether to require partition filter for queries over this table. '
        'Only apply to partitioned table.',
        flag_values=fv)
    flags.DEFINE_string(
        'clustering_fields',
        None,
        'Comma-separated list of field names that specifies the columns on '
        'which a table is clustered. To remove the clustering, set an empty '
        'value.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'use_avro_logical_types',
        None, 'If sourceFormat is set to "AVRO", indicates whether to enable '
        'interpreting logical types into their corresponding types '
        '(ie. TIMESTAMP), instead of only using their raw types (ie. INTEGER).',
        flag_values=fv)
    flags.DEFINE_string(
        'reference_file_schema_uri',
        None, 'provide a reference file with the reader schema, currently '
        'enabled for the format: AVRO, PARQUET, ORC.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'parquet_enum_as_string',
        False, 'Infer Parquet ENUM logical type as STRING '
        '(instead of BYTES by default).',
        flag_values=fv)
    flags.DEFINE_boolean(
        'parquet_enable_list_inference',
        False,
        _PARQUET_LIST_INFERENCE_DESCRIPTION,
        flag_values=fv)
    flags.DEFINE_string(
        'hive_partitioning_mode',
        None,
        'Enables hive partitioning.  AUTO indicates to perform '
        'automatic type inference.  STRINGS indicates to treat all hive '
        'partition keys as STRING typed.  No other values are accepted',
        flag_values=fv)
    flags.DEFINE_string(
        'hive_partitioning_source_uri_prefix',
        None, 'Prefix after which hive partition '
        'encoding begins.  For URIs like gs://bucket/path/key1=value/file, '
        'the value should be gs://bucket/path.',
        flag_values=fv)
    flags.DEFINE_multi_enum(
        'decimal_target_types',
        None, ['NUMERIC', 'BIGNUMERIC', 'STRING'],
        'Specifies the list of possible BigQuery data types to '
        'which the source decimal values are converted. This list and the '
        'precision and the scale parameters of the decimal field determine the '
        'target type in the following preference order, and '
        'one or more of the following options could be specified: '
        '\n NUMERIC: decimal values could be converted to NUMERIC type, '
        'depending on the precision and scale of the decimal schema.'
        '\n BIGNUMERIC: decimal values could be converted to BIGNUMERIC type, '
        'depending on the precision and scale of the decimal schema.'
        '\n STRING: decimal values could be converted to STRING type, '
        'depending on the precision and scale of the decimal schema.',
        flag_values=fv)
    flags.DEFINE_enum(
        'file_set_spec_type',
        None, ['FILE_SYSTEM_MATCH', 'NEW_LINE_DELIMITED_MANIFEST'],
        '[Experimental] Specifies how to discover files given source URIs. '
        'Options include: '
        '\n FILE_SYSTEM_MATCH: expand source URIs by listing files from the '
        'underlying object store. This is the default behavior.'
        '\n NEW_LINE_DELIMITED_MANIFEST: indicate the source URIs provided are '
        'new line delimited manifest files, where each line contains a URI '
        'with no wild-card.',
        flag_values=fv)
    flags.DEFINE_string(
        'thrift_schema_idl_root_dir',
        None,
        'If "source_format" is set to "THRIFT", indicates the root directory '
        'of the Thrift IDL bundle containing all Thrift files that should be '
        'used to parse the schema of the serialized Thrift records.',
        flag_values=fv)
    flags.DEFINE_string(
        'thrift_schema_idl_uri',
        None,
        'If "source_format" is set to "THRIFT", indicates the file uri that '
        'contains the Thrift IDL struct to be parsed as schema. This file will '
        'be used as the entry point to parse the schema and all its included '
        'Thrift IDL files should be in "thrift_schema_idl_root_dir".',
        flag_values=fv)
    flags.DEFINE_string(
        'thrift_schema_struct',
        None,
        'If "source_format" is set to "THRIFT", indicates the root Thrift '
        'struct that should be used as the schema. This struct should be '
        'defined in the "thrift_schema_idl_uri" file.',
        flag_values=fv)
    flags.DEFINE_enum(
        'thrift_deserialization',
        None, ['T_BINARY_PROTOCOL'],
        'If "source_format" is set to "THRIFT", configures how serialized '
        'Thrift record should be deserialized (using TProtocol). '
        'Options include: '
        '\n T_BINARY_PROTOCOL',
        flag_values=fv)
    flags.DEFINE_enum(
        'thrift_framing',
        None,
        ['NOT_FRAMED', 'FRAMED_WITH_BIG_ENDIAN', 'FRAMED_WITH_LITTLE_ENDIAN'],
        'If "source_format" is set to "THRIFT", configures how Thrift records '
        'or data blocks are framed (e.g. using TFramedTransport). '
        'Options includes: '
        '\n NOT_FRAMED, '
        '\n FRAMED_WITH_BIG_ENDIAN, '
        '\n FRAMED_WITH_LITTLE_ENDIAN',
        flag_values=fv)
    flags.DEFINE_string(
        'boundary_bytes_base64',
        None,
        'If "source_format" is set to "THRIFT", indicates the sequence of '
        'boundary bytes (encoded in base64) that are added in front of the '
        'serialized Thrift records, or data blocks, or the frame when used '
        'with `thrift_framing`.',
        flag_values=fv)
    flags.DEFINE_enum(
        'json_extension',
        None, ['GEOJSON'], '(experimental) Allowed values: '
        'GEOJSON: only allowed when source_format is specified as '
        'NEWLINE_DELIMITED_JSON. When specified, the input is loaded as '
        'newline-delimited GeoJSON.',
        flag_values=fv)
    flags.DEFINE_string(
        'session_id',
        None,
        'If loading to a temporary table, specifies the session ID of the '
        'temporary table',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, destination_table, source, schema=None):
    """Perform a load operation of source into destination_table.

    Usage:
      load <destination_table> <source> [<schema>] [--session_id=[session]]

    The <destination_table> is the fully-qualified table name of table to
    create, or append to if the table already exists.

    To load to a temporary table, specify the table name in <destination_table>
    without a dataset and specify the session id with --session_id.

    The <source> argument can be a path to a single local file, or a
    comma-separated list of URIs.

    The <schema> argument should be either the name of a JSON file or a text
    schema. This schema should be omitted if the table already has one.

    In the case that the schema is provided in text form, it should be a
    comma-separated list of entries of the form name[:type], where type will
    default to string if not specified.

    In the case that <schema> is a filename, it should be a JSON file
    containing a single array, each entry of which should be an object with
    properties 'name', 'type', and (optionally) 'mode'. For more detail:
    https://cloud.google.com/bigquery/docs/schemas#specifying_a_json_schema_file

    Note: the case of a single-entry schema with no type specified is
    ambiguous; one can use name:string to force interpretation as a
    text schema.

    Examples:
      bq load ds.new_tbl ./info.csv ./info_schema.json
      bq load ds.new_tbl gs://mybucket/info.csv ./info_schema.json
      bq load ds.small gs://mybucket/small.csv name:integer,value:string
      bq load ds.small gs://mybucket/small.csv field1,field2,field3
      bq load temp_tbl --session_id=my_session ./info.csv ./info_schema.json

    Arguments:
      destination_table: Destination table name.
      source: Name of local file to import, or a comma-separated list of URI
        paths to data to import.
      schema: Either a text schema or JSON file, as above.
    """
    client = Client.Get()
    default_dataset_id = ''
    if self.session_id:
      default_dataset_id = '_SESSION'
    table_reference = client.GetTableReference(destination_table,
                                               default_dataset_id)
    opts = {
        'encoding': self.encoding,
        'skip_leading_rows': self.skip_leading_rows,
        'max_bad_records': self.max_bad_records,
        'allow_quoted_newlines': self.allow_quoted_newlines,
        'job_id': _GetJobIdFromFlags(),
        'source_format': self.source_format,
        'projection_fields': self.projection_fields,
    }
    if FLAGS.location:
      opts['location'] = FLAGS.location
    if self.session_id:
      opts['connection_properties'] = [{
          'key': 'session_id',
          'value': self.session_id
      }]
    if self.replace:
      opts['write_disposition'] = 'WRITE_TRUNCATE'
    if self.field_delimiter is not None:
      opts['field_delimiter'] = _NormalizeFieldDelimiter(self.field_delimiter)
    if self.quote is not None:
      opts['quote'] = _NormalizeFieldDelimiter(self.quote)
    if self.allow_jagged_rows is not None:
      opts['allow_jagged_rows'] = self.allow_jagged_rows
    if self.preserve_ascii_control_characters is not None:
      opts[
          'preserve_ascii_control_characters'] = self.preserve_ascii_control_characters
    if self.ignore_unknown_values is not None:
      opts['ignore_unknown_values'] = self.ignore_unknown_values
    if self.autodetect is not None:
      opts['autodetect'] = self.autodetect
    if self.schema_update_option:
      opts['schema_update_options'] = self.schema_update_option
    if self.null_marker:
      opts['null_marker'] = self.null_marker
    time_partitioning = _ParseTimePartitioning(
        self.time_partitioning_type,
        self.time_partitioning_expiration,
        self.time_partitioning_field,
        None,
        self.require_partition_filter)
    if time_partitioning is not None:
      opts['time_partitioning'] = time_partitioning
    range_partitioning = _ParseRangePartitioning(self.range_partitioning)
    if range_partitioning:
      opts['range_partitioning'] = range_partitioning
    clustering = _ParseClustering(self.clustering_fields)
    if clustering:
      opts['clustering'] = clustering
    if self.destination_kms_key is not None:
      opts['destination_encryption_configuration'] = {
          'kmsKeyName': self.destination_kms_key
      }
    if self.use_avro_logical_types is not None:
      opts['use_avro_logical_types'] = self.use_avro_logical_types
    if self.reference_file_schema_uri is not None:
      opts['reference_file_schema_uri'] = self.reference_file_schema_uri
    if self.hive_partitioning_mode is not None:
      _ValidateHivePartitioningOptions(self.hive_partitioning_mode)
      hive_partitioning_options = {}
      hive_partitioning_options['mode'] = self.hive_partitioning_mode
      if self.hive_partitioning_source_uri_prefix is not None:
        hive_partitioning_options[
            'sourceUriPrefix'] = self.hive_partitioning_source_uri_prefix
      opts['hive_partitioning_options'] = hive_partitioning_options
    if self.json_extension is not None:
      opts['json_extension'] = self.json_extension
    opts['decimal_target_types'] = self.decimal_target_types
    if self.file_set_spec_type is not None:
      opts['file_set_spec_type'] = _ParseFileSetSpecType(self.file_set_spec_type)
    if opts['source_format'] == 'THRIFT':
      thrift_options = {}
      if self.thrift_schema_idl_root_dir is not None:
        thrift_options['schema_idl_root_dir'] = self.thrift_schema_idl_root_dir
      if self.thrift_schema_idl_uri is not None:
        thrift_options['schema_idl_uri'] = self.thrift_schema_idl_uri
      if self.thrift_schema_struct is not None:
        thrift_options['schema_struct'] = self.thrift_schema_struct
      # Default to 'THRIFT_BINARY_PROTOCOL_OPTION'.
      thrift_options['deserialization_option'] = 'THRIFT_BINARY_PROTOCOL_OPTION'
      if self.thrift_deserialization is not None:
        if self.thrift_deserialization == 'T_BINARY_PROTOCOL':
          thrift_options[
              'deserialization_option'] = 'THRIFT_BINARY_PROTOCOL_OPTION'
      # Default to 'NOT_FRAMED'.
      thrift_options['framing_option'] = 'NOT_FRAMED'
      if self.thrift_framing is not None:
        thrift_options['framing_option'] = self.thrift_framing
      if self.boundary_bytes_base64 is not None:
        thrift_options['boundary_bytes'] = self.boundary_bytes_base64
      opts['thrift_options'] = thrift_options
    if opts['source_format'] == 'PARQUET':
      parquet_options = {}
      if self.parquet_enum_as_string is not None:
        parquet_options['enum_as_string'] = self.parquet_enum_as_string
      if self.parquet_enable_list_inference is not None:
        parquet_options[
            'enable_list_inference'] = self.parquet_enable_list_inference
      opts['parquet_options'] = parquet_options
    job = client.Load(table_reference, source, schema=schema, **opts)
    if FLAGS.sync:
      _PrintJobMessages(client.FormatJobInfo(job))
    else:
      self.PrintJobStartInfo(job)


def _CreateExternalTableDefinition(
    source_format,
    source_uris,
    schema,
    autodetect,
    connection_id=None,
    ignore_unknown_values=False,
    hive_partitioning_mode=None,
    hive_partitioning_source_uri_prefix=None,
    require_hive_partition_filter=None,
    use_avro_logical_types=False,
    parquet_enum_as_string=False,
    parquet_enable_list_inference=False,
    metadata_cache_mode=None,
    object_metadata=None,
    preserve_ascii_control_characters=False,
    reference_file_schema_uri=None,
    encoding=None,
    file_set_spec_type=None,
):
  """Creates an external table definition with the given URIs and the schema.

  Arguments:
    source_format: Format of source data. For CSV files, specify 'CSV'. For
      Google spreadsheet files, specify 'GOOGLE_SHEETS'. For newline-delimited
      JSON, specify 'NEWLINE_DELIMITED_JSON'. For Cloud Datastore backup,
      specify 'DATASTORE_BACKUP'. For Avro files, specify 'AVRO'. For Orc files,
      specify 'ORC'. For Parquet files, specify 'PARQUET'.
      For Iceberg tables, specify 'ICEBERG'.
    source_uris: Comma separated list of URIs that contain data for this table.
    schema: Either an inline schema or path to a schema file.
    autodetect: Indicates if format options, compression mode and schema be auto
      detected from the source data. True - means that autodetect is on, False
      means that it is off. None means format specific default: - For CSV it
      means autodetect is OFF - For JSON it means that autodetect is ON. For
      JSON, defaulting to autodetection is safer because the only option
      autodetected is compression. If a schema is passed, then the user-supplied
      schema is used.
    ignore_unknown_values:  Indicates if BigQuery should allow extra values that
      are not represented in the table schema. If true, the extra values are
      ignored. If false, records with extra columns are treated as bad records,
      and if there are too many bad records, an invalid error is returned in the
      job result. The default value is false. The sourceFormat property
      determines what BigQuery treats as an extra value: - CSV: Trailing columns
      - JSON: Named values that don't match any column names.
    hive_partitioning_mode: Enables hive partitioning.  AUTO indicates to
      perform automatic type inference.  STRINGS indicates to treat all hive
      partition keys as STRING typed.  No other values are accepted.
    hive_partitioning_source_uri_prefix: Shared prefix for all files until hive
      partitioning encoding begins.
    metadata_cache_mode: Enables metadata cache for an external table with a
      connection. Specify 'AUTOMATIC' to automatically refresh the cached
      metadata. Specify 'MANUAL' to stop the automatic refresh.
    object_metadata: Object Metadata Type.
    encoding: Encoding types for CSV files. Available options are: 'UTF-8',
    'ISO-8859-1', 'UTF-16BE', 'UTF-16LE', 'UTF-32BE', and 'UTF-32LE'.
    The default value is 'UTF-8'.
    file_set_spec_type: Set how to discover files given source URIs. Specify
      'FILE_SYSTEM_MATCH' (default behavior) to expand source URIs by listing
      files from the underlying object store. Specify
      'NEW_LINE_DELIMITED_MANIFEST' to parse the URIs as new line delimited
      manifest files, where each line contains a URI (No wild-card URIs are
      supported).

  Returns:
    A python dictionary that contains a external table definition for the given
    format with the most common options set.
  """
  try:
    supported_formats = [
        'CSV',
        'NEWLINE_DELIMITED_JSON',
        'DATASTORE_BACKUP',
        'AVRO',
        'ORC',
        'PARQUET',
        'GOOGLE_SHEETS',
        'ICEBERG'
    ]

    if source_format not in supported_formats:
      raise app.UsageError(('%s is not a supported format.') % source_format)

    external_table_def = {'sourceFormat': source_format}
    if file_set_spec_type is not None:
      external_table_def['fileSetSpecType'] = file_set_spec_type
    if metadata_cache_mode is not None:
      external_table_def['metadataCacheMode'] = metadata_cache_mode
    if object_metadata is not None:
      supported_obj_metadata_types = ['DIRECTORY', 'SIMPLE']

      if object_metadata not in supported_obj_metadata_types:
        raise app.UsageError('%s is not a supported Object Metadata Type.' %
                             object_metadata)

      external_table_def['sourceFormat'] = None
      external_table_def['objectMetadata'] = object_metadata

    if external_table_def['sourceFormat'] == 'CSV':
      if autodetect:
        external_table_def['autodetect'] = True
        external_table_def['csvOptions'] = yaml.safe_load("""
            {
                "quote": '"',
                "encoding": "UTF-8"
            }
        """)
      else:
        external_table_def['csvOptions'] = yaml.safe_load("""
            {
                "allowJaggedRows": false,
                "fieldDelimiter": ",",
                "allowQuotedNewlines": false,
                "quote": '"',
                "skipLeadingRows": 0,
                "encoding": "UTF-8"
            }
        """)
      external_table_def['csvOptions'][
          'preserveAsciiControlCharacters'] = preserve_ascii_control_characters
      external_table_def['csvOptions']['encoding'] = encoding or 'UTF-8'
    elif external_table_def['sourceFormat'] == 'NEWLINE_DELIMITED_JSON':
      if autodetect is None or autodetect:
        external_table_def['autodetect'] = True
      external_table_def['jsonOptions'] = {'encoding': encoding or 'UTF-8'}
    elif external_table_def['sourceFormat'] == 'GOOGLE_SHEETS':
      if autodetect is None or autodetect:
        external_table_def['autodetect'] = True
      else:
        external_table_def['googleSheetsOptions'] = yaml.safe_load("""
            {
                "skipLeadingRows": 0
            }
        """)
    elif external_table_def['sourceFormat'] == 'AVRO':
      external_table_def['avroOptions'] = {
          'useAvroLogicalTypes': use_avro_logical_types
      }
      if reference_file_schema_uri is not None:
        external_table_def['referenceFileSchemaUri'] = reference_file_schema_uri
    elif external_table_def['sourceFormat'] == 'PARQUET':
      external_table_def['parquetOptions'] = {
          'enumAsString': parquet_enum_as_string,
          'enableListInference': parquet_enable_list_inference
      }
      if reference_file_schema_uri is not None:
        external_table_def['referenceFileSchemaUri'] = reference_file_schema_uri
    elif external_table_def['sourceFormat'] == 'ORC':
      if reference_file_schema_uri is not None:
        external_table_def['referenceFileSchemaUri'] = reference_file_schema_uri
    elif (
        external_table_def['sourceFormat'] == 'ICEBERG'
    ):
      source_format = (
          'Iceberg'
          if external_table_def['sourceFormat'] == 'ICEBERG'
          else 'Delta Lake'
      )
      if autodetect is not None and not autodetect or schema:
        raise app.UsageError(
            'Cannot create %s table from user-specified schema.'
            % (source_format,)
        )
      # Always autodetect schema for ICEBERG from manifest
      external_table_def['autodetect'] = True
      if len(source_uris.split(',')) != 1:
        raise app.UsageError(
            'Must provide only one source_uri for %s table.' % (source_format,))


    if ignore_unknown_values:
      external_table_def['ignoreUnknownValues'] = True


    if hive_partitioning_mode is not None:
      _ValidateHivePartitioningOptions(hive_partitioning_mode)
      hive_partitioning_options = {}
      hive_partitioning_options['mode'] = hive_partitioning_mode
      if hive_partitioning_source_uri_prefix is not None:
        hive_partitioning_options[
            'sourceUriPrefix'] = hive_partitioning_source_uri_prefix
      external_table_def['hivePartitioningOptions'] = hive_partitioning_options
      if require_hive_partition_filter:
        hive_partitioning_options['requirePartitionFilter'] = True

    if schema:
      fields = BigqueryClient.ReadSchema(schema)
      external_table_def['schema'] = {'fields': fields}

    if connection_id:
      external_table_def['connectionId'] = connection_id

    external_table_def['sourceUris'] = source_uris.split(',')

    return external_table_def

  except ValueError as e:
    raise app.UsageError(
        ('Error occurred while creating table definition: %s') % e)


class _MakeExternalTableDefinition(BigqueryCmd):
  usage = """mkdef <source_uri> [<schema>]"""

  def __init__(self, name, fv):
    super(_MakeExternalTableDefinition, self).__init__(name, fv)

    flags.DEFINE_boolean(
        'autodetect',
        None,
        'Should schema and format options be autodetected.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'ignore_unknown_values',
        None,
        'Ignore any values in a row that are not present in the schema.',
        short_name='i',
        flag_values=fv)
    flags.DEFINE_string(
        'hive_partitioning_mode',
        None,
        'Enables hive partitioning.  AUTO indicates to perform '
        'automatic type inference.  STRINGS indicates to treat all hive '
        'partition keys as STRING typed.  No other values are accepted',
        flag_values=fv)
    flags.DEFINE_string(
        'hive_partitioning_source_uri_prefix',
        None, 'Prefix after which hive partition '
        'encoding begins.  For URIs like gs://bucket/path/key1=value/file, '
        'the value should be gs://bucket/path.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'require_hive_partition_filter',
        None, 'Whether queries against a table are required to '
        'include a hive partition key in a query predicate.',
        flag_values=fv)
    flags.DEFINE_enum(
        'source_format',
        'CSV',
        [
            'CSV',
            'GOOGLE_SHEETS',
            'NEWLINE_DELIMITED_JSON',
            'DATASTORE_BACKUP',
            'ORC',
            'PARQUET',
            'AVRO',
            'ICEBERG'
        ],
        'Format of source data. Options include:'
        '\n CSV'
        '\n GOOGLE_SHEETS'
        '\n NEWLINE_DELIMITED_JSON'
        '\n DATASTORE_BACKUP'
        '\n ORC'
        '\n PARQUET'
        '\n ICEBERG (preview)'
        '\n AVRO',
        flag_values=fv)
    flags.DEFINE_string(
        'connection_id',
        None,
        'The connection specifying the credentials to be used to read external '
        'storage, such as Azure Blob, Cloud Storage, or S3. The connection_id '
        'can have the form "<project_id>.<location_id>.<connection_id>" or '
        '"projects/<project_id>/locations/<location_id>/connections/'
        '<connection_id>".',
        flag_values=fv)
    flags.DEFINE_boolean(
        'use_avro_logical_types',
        True, 'If sourceFormat is set to "AVRO", indicates whether to enable '
        'interpreting logical types into their corresponding types '
        '(ie. TIMESTAMP), instead of only using their raw types (ie. INTEGER).',
        flag_values=fv)
    flags.DEFINE_boolean(
        'parquet_enum_as_string',
        False, 'Infer Parquet ENUM logical type as STRING '
        '(instead of BYTES by default).',
        flag_values=fv)
    flags.DEFINE_boolean(
        'parquet_enable_list_inference',
        False,
        _PARQUET_LIST_INFERENCE_DESCRIPTION,
        flag_values=fv)
    flags.DEFINE_enum(
        'metadata_cache_mode',
        None, ['AUTOMATIC', 'MANUAL'],
        'Enables metadata cache for an external table with a connection. '
        'Specify AUTOMATIC to automatically refresh the cached metadata. '
        'Specify MANUAL to stop the automatic refresh.',
        flag_values=fv)
    flags.DEFINE_enum(
        'object_metadata',
        None, ['DIRECTORY', 'SIMPLE'], 'Object Metadata Type. Options include:'
        '\n SIMPLE.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'preserve_ascii_control_characters',
        False,
        'Whether to preserve embedded Ascii Control characters in CSV External table ',
        flag_values=fv)
    flags.DEFINE_string(
        'reference_file_schema_uri',
        None,
        'provide a referencing file with the expected table schema, currently '
        'enabled for the formats: AVRO, PARQUET, ORC.',
        flag_values=fv)
    flags.DEFINE_enum(
        'encoding',
        None,
        ['UTF-8', 'ISO-8859-1', 'UTF-16BE', 'UTF-16LE', 'UTF-32BE', 'UTF-32LE'],
        'The character encoding used by the input file.  Options include:'
        '\n ISO-8859-1 (also known as Latin-1)'
        '\n UTF-8'
        '\n UTF-16BE (UTF-16 BigEndian)'
        '\n UTF-16LE (UTF-16 LittleEndian)'
        '\n UTF-32BE (UTF-32 BigEndian)'
        '\n UTF-32LE (UTF-16 LittleEndian)',
        short_name='E',
        flag_values=fv)
    flags.DEFINE_enum(
        'file_set_spec_type',
        None, ['FILE_SYSTEM_MATCH', 'NEW_LINE_DELIMITED_MANIFEST'],
        '[Experimental] Specifies how to discover files given source URIs. '
        'Options include: '
        '\n FILE_SYSTEM_MATCH: expand source URIs by listing files from the '
        'underlying object store. This is the default behavior.'
        '\n NEW_LINE_DELIMITED_MANIFEST: indicate the source URIs provided are '
        'new line delimited manifest files, where each line contains a URI '
        'with no wild-card.',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, source_uris, schema=None):
    """Emits a definition in JSON for an external table, such as GCS.

    The output of this command can be redirected to a file and used for the
    external_table_definition flag with the "bq query" and "bq mk" commands.
    It produces a definition with the most commonly used values for options.
    You can modify the output to override option values.

    The <source_uris> argument is a comma-separated list of URIs indicating
    the data referenced by this external table.

    The <schema> argument should be either the name of a JSON file or a text
    schema.

    In the case that the schema is provided in text form, it should be a
    comma-separated list of entries of the form name[:type], where type will
    default to string if not specified.

    In the case that <schema> is a filename, it should be a JSON file
    containing a single array, each entry of which should be an object with
    properties 'name', 'type', and (optionally) 'mode'. For more detail:
    https://cloud.google.com/bigquery/docs/schemas#specifying_a_json_schema_file

    Note: the case of a single-entry schema with no type specified is
    ambiguous; one can use name:string to force interpretation as a
    text schema.

    Usage:
      mkdef <source_uris> [<schema>]

    Examples:
      bq mkdef 'gs://bucket/file.csv' field1:integer,field2:string

    Arguments:
      source_uris: Comma-separated list of URIs.
      schema: Either a text schema or JSON file, as above.
    """
    # pylint: disable=line-too-long
    json.dump(
        _CreateExternalTableDefinition(
            source_format=self.source_format,
            source_uris=source_uris,
            schema=schema,
            autodetect=self.autodetect,
            connection_id=self.connection_id,
            ignore_unknown_values=self.ignore_unknown_values,
            hive_partitioning_mode=self.hive_partitioning_mode,
            hive_partitioning_source_uri_prefix=self
            .hive_partitioning_source_uri_prefix,
            require_hive_partition_filter=self.require_hive_partition_filter,
            use_avro_logical_types=self.use_avro_logical_types,
            parquet_enum_as_string=self.parquet_enum_as_string,
            parquet_enable_list_inference=self.parquet_enable_list_inference,
            metadata_cache_mode=self.metadata_cache_mode,
            object_metadata=self.object_metadata,
            preserve_ascii_control_characters=self
            .preserve_ascii_control_characters,
            reference_file_schema_uri=self.reference_file_schema_uri,
            encoding=self.encoding,
            file_set_spec_type=self.file_set_spec_type,
            ),
        sys.stdout,
        sort_keys=True,
        indent=2)
    # pylint: enable=line-too-long


class _Query(BigqueryCmd):
  usage = """query <sql>"""

  def __init__(self, name, fv):
    super(_Query, self).__init__(name, fv)
    flags.DEFINE_string(
        'destination_table',
        '',
        'Name of destination table for query results.',
        flag_values=fv)
    flags.DEFINE_string(
        'destination_schema',
        '', 'Schema for the destination table. Either a filename or '
        'a comma-separated list of fields in the form name[:type].',
        flag_values=fv)
    flags.DEFINE_integer(
        'start_row',
        0,
        'First row to return in the result.',
        short_name='s',
        flag_values=fv)
    flags.DEFINE_integer(
        'max_rows',
        100,
        'How many rows to return in the result.',
        short_name='n',
        flag_values=fv)
    flags.DEFINE_boolean(
        'batch',
        None,
        'Whether to run the query in batch mode. Ignored if --priority flag is '
        'specified.',
        flag_values=fv)
    flags.DEFINE_enum(
        'priority',
        None, [
            'HIGH',
            'INTERACTIVE',
            'BATCH',
        ], 'Query priority. If not specified, priority is determined using the '
        '--batch flag. Options include:'
        '\n HIGH (only available for whitelisted reservations)'
        '\n INTERACTIVE'
        '\n BATCH',
        flag_values=fv)
    flags.DEFINE_boolean(
        'append_table',
        False,
        'When a destination table is specified, whether or not to append.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'rpc',
        False,
        'If true, use rpc-style query API instead of jobs.insert().',
        flag_values=fv)
    flags.DEFINE_string(
        'request_id',
        None, 'The request_id to use for the jobs.query request. '
        'Only valid when used in combination with --rpc.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'replace',
        False,
        'If true, erase existing contents before loading new data.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'allow_large_results',
        None,
        'Enables larger destination table sizes for legacy SQL queries.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'dry_run',
        None,
        'Whether the query should be validated without executing.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'require_cache',
        None,
        'Whether to only run the query if it is already cached.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'use_cache',
        None,
        'Whether to use the query cache to avoid rerunning cached queries.',
        flag_values=fv)
    flags.DEFINE_float(
        'min_completion_ratio',
        None,
        '[Experimental] The minimum fraction of data that must be scanned '
        'before a query returns. If not set, the default server value (1.0) '
        'will be used.',
        lower_bound=0,
        upper_bound=1.0,
        flag_values=fv)
    flags.DEFINE_boolean(
        'flatten_results',
        None,
        'Whether to flatten nested and repeated fields in the result schema '
        'for legacy SQL queries. '
        'If not set, the default behavior is to flatten.',
        flag_values=fv)
    flags.DEFINE_multi_string(
        'external_table_definition',
        None, 'Specifies a table name and either an inline table definition '
        'or a path to a file containing a JSON table definition to use in the '
        'query. The format is "table_name::path_to_file_with_json_def" or '
        '"table_name::schema@format=uri@connection". '
        'For example, '
        '"--external_table_definition=Example::/tmp/example_table_def.txt" '
        'will define a table named "Example" using the URIs and schema '
        'encoded in example_table_def.txt.',
        flag_values=fv)
    flags.DEFINE_multi_string(
        'udf_resource',
        None, 'The URI or local filesystem path of a code file to load and '
        'evaluate immediately as a User-Defined Function resource.',
        flag_values=fv)
    flags.DEFINE_integer(
        'maximum_billing_tier',
        None,
        'The upper limit of billing tier for the query.',
        flag_values=fv)
    flags.DEFINE_integer(
        'maximum_bytes_billed',
        None,
        'The upper limit of bytes billed for the query.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'use_legacy_sql',
        None,
        ('The choice of using Legacy SQL for the query is optional. If not '
         'specified, the server will automatically determine the dialect based '
         'on query information, such as dialect prefixes. If no prefixes are '
         'found, it will default to Legacy SQL.'),
        flag_values=fv)
    flags.DEFINE_multi_string(
        'schema_update_option',
        None,
        'Can be specified when append to a table, or replace a table partition.'
        ' When specified, the schema of the destination table will be updated '
        'with the schema of the new data. One or more of the following options '
        'can be specified:'
        '\n ALLOW_FIELD_ADDITION: allow new fields to be added'
        '\n ALLOW_FIELD_RELAXATION: allow relaxing required fields to nullable',
        flag_values=fv)
    flags.DEFINE_multi_string(
        'label',
        None,
        'A label to set on a query job. The format is "key:value"',
        flag_values=fv)
    flags.DEFINE_multi_string(
        'parameter',
        None,
        ('Either a file containing a JSON list of query parameters, or a query '
         'parameter in the form "name:type:value". An empty name produces '
         'a positional parameter. The type may be omitted to assume STRING: '
         'name::value or ::value. The value "NULL" produces a null value.'),
        flag_values=fv)
    flags.DEFINE_string(
        'time_partitioning_type',
        None,
        'Enables time based partitioning on the table and set the type. The '
        'default value is DAY, which will generate one partition per day. '
        'Other supported values are HOUR, MONTH, and YEAR.',
        flag_values=fv)
    flags.DEFINE_integer(
        'time_partitioning_expiration',
        None,
        'Enables time based partitioning on the table and sets the number of '
        'seconds for which to keep the storage for the partitions in the table.'
        ' The storage in a partition will have an expiration time of its '
        'partition time plus this value.',
        flag_values=fv)
    flags.DEFINE_string(
        'time_partitioning_field',
        None,
        'Enables time based partitioning on the table and the table will be '
        'partitioned based on the value of this field. If time based '
        'partitioning is enabled without this value, the table will be '
        'partitioned based on the loading time.',
        flag_values=fv)
    flags.DEFINE_string(
        'range_partitioning',
        None, 'Enables range partitioning on the table. The format should be '
        '"field,start,end,interval". The table will be partitioned based on the'
        ' value of the field. Field must be a top-level, non-repeated INT64 '
        'field. Start, end, and interval are INT64 values defining the ranges.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'require_partition_filter',
        None,
        'Whether to require partition filter for queries over this table. '
        'Only apply to partitioned table.',
        flag_values=fv)
    flags.DEFINE_string(
        'clustering_fields',
        None,
        'Comma-separated list of field names that specifies the columns on '
        'which a table is clustered. To remove the clustering, set an empty '
        'value.',
        flag_values=fv)
    flags.DEFINE_string(
        'destination_kms_key',
        None,
        'Cloud KMS key for encryption of the destination table data.',
        flag_values=fv)
    flags.DEFINE_string(
        'script_statement_timeout_ms',
        None,
        'Maximum time to complete each statement in a script.',
        flag_values=fv)
    flags.DEFINE_string(
        'script_statement_byte_budget',
        None,
        'Maximum bytes that can be billed for any statement in a script.',
        flag_values=fv)
    flags.DEFINE_integer(
        'max_statement_results',
        100,
        'Maximum number of script statements to display the results for.',
        flag_values=fv)
    flags.DEFINE_integer(
        'max_child_jobs',
        1000,
        'Maximum number of child jobs to fetch results from after executing a '
        'script.  If the number of child jobs exceeds this limit, only the '
        'final result will be displayed.',
        flag_values=fv)
    flags.DEFINE_string(
        'job_timeout_ms',
        None,
        'Maximum time to run the entire script.',
        flag_values=fv)
    flags.DEFINE_string(
        'schedule',
        None,
        'Scheduled query schedule. If non-empty, this query requests could '
        'create a scheduled query understand the customer project. See '
        'https://cloud.google.com/appengine/docs/flexible/python/scheduling-jobs-with-cron-yaml#the_schedule_format '  # pylint: disable=line-too-long
        'for the schedule format',
        flag_values=fv)
    flags.DEFINE_bool(
        'no_auto_scheduling',
        False,
        'Create a scheduled query configuration with automatic scheduling '
        'disabled.',
        flag_values=fv)
    flags.DEFINE_string(
        'display_name',
        '',
        'Display name for the created scheduled query configuration.',
        flag_values=fv)
    flags.DEFINE_string(
        'target_dataset',
        None,
        'Target dataset used to create scheduled query.',
        flag_values=fv)
    flags.DEFINE_multi_string(
        'connection_property', None, 'Connection properties', flag_values=fv)
    flags.DEFINE_boolean(
        'create_session',
        None,
        'Whether to create a new session and run the query in the sesson.',
        flag_values=fv)
    flags.DEFINE_string(
        'session_id',
        None,
        'An existing session id where the query will be run.',
        flag_values=fv)
    flags.DEFINE_bool(
        'continuous',
        False,
        'Whether to run the query as continuous query',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, *args):
    # pylint: disable=g-doc-exception
    """Execute a query.

    Query should be specified on command line, or passed on stdin.

    Examples:
      bq query 'select count(*) from publicdata:samples.shakespeare'
      echo 'select count(*) from publicdata:samples.shakespeare' | bq query

    Usage:
      query [<sql_query>]
    """
    # Set up the params that are the same for rpc-style and jobs.insert()-style
    # queries.
    kwds = {
        'dry_run': self.dry_run,
        'use_cache': self.use_cache,
        'min_completion_ratio': self.min_completion_ratio,
    }
    if self.external_table_definition:
      external_table_defs = {}
      for raw_table_def in self.external_table_definition:
        table_name_and_def = raw_table_def.split('::', 1)
        if len(table_name_and_def) < 2:
          raise app.UsageError(
              'external_table_definition parameter is invalid, expected :: as '
              'the separator.')
        external_table_defs[table_name_and_def[0]] = _GetExternalDataConfig(
            table_name_and_def[1])
      kwds['external_table_definitions_json'] = dict(external_table_defs)
    if self.udf_resource:
      kwds['udf_resources'] = _ParseUdfResources(self.udf_resource)
    if self.maximum_billing_tier:
      kwds['maximum_billing_tier'] = self.maximum_billing_tier
    if self.maximum_bytes_billed:
      kwds['maximum_bytes_billed'] = self.maximum_bytes_billed
    if self.schema_update_option:
      kwds['schema_update_options'] = self.schema_update_option
    if self.label is not None:
      kwds['labels'] = _ParseLabels(self.label)
    if self.request_id is not None:
      kwds['request_id'] = self.request_id
    if self.parameter:
      kwds['query_parameters'] = _ParseParameters(self.parameter)
    query = ' '.join(args)
    if not query:
      query = sys.stdin.read()
    client = Client.Get()
    if FLAGS.location:
      kwds['location'] = FLAGS.location
    kwds['use_legacy_sql'] = self.use_legacy_sql
    time_partitioning = _ParseTimePartitioning(
        self.time_partitioning_type,
        self.time_partitioning_expiration,
        self.time_partitioning_field,
        None,
        self.require_partition_filter)
    if time_partitioning is not None:
      kwds['time_partitioning'] = time_partitioning
    range_partitioning = _ParseRangePartitioning(self.range_partitioning)
    if range_partitioning:
      kwds['range_partitioning'] = range_partitioning
    clustering = _ParseClustering(self.clustering_fields)
    if clustering:
      kwds['clustering'] = clustering
    if self.destination_schema and not self.destination_table:
      raise app.UsageError(
          'destination_schema can only be used with destination_table.')
    read_schema = None
    if self.destination_schema:
      read_schema = BigqueryClient.ReadSchema(self.destination_schema)
    if self.destination_kms_key:
      kwds['destination_encryption_configuration'] = {
          'kmsKeyName': self.destination_kms_key
      }
    if ((self.script_statement_timeout_ms is not None) or
        (self.script_statement_byte_budget is not None)
       ):
      script_options = {
          'statementTimeoutMs': self.script_statement_timeout_ms,
          'statementByteBudget': self.script_statement_byte_budget,
      }
      kwds['script_options'] = {
          name: value
          for name, value in six.iteritems(script_options)
          if value is not None
      }

    if self.schedule or self.no_auto_scheduling:
      transfer_client = client.GetTransferV1ApiClient()
      reference = 'projects/' + (client.GetProjectReference().projectId)
      scheduled_queries_reference = (reference + '/dataSources/scheduled_query')
      try:
        transfer_client.projects().dataSources().get(
            name=scheduled_queries_reference).execute()
      except Exception as e:
        raise bq_error.BigqueryAccessDeniedError(
            'Scheduled queries are not enabled on this project. Please enable '
            'them at '
            'https://console.cloud.google.com/bigquery/scheduled-queries',
            {'reason': 'notFound'}, []) from e
      if self.use_legacy_sql is None or self.use_legacy_sql:
        raise app.UsageError(
            'Scheduled queries do not support legacy SQL. Please use standard '
            'SQL and set the --use_legacy_sql flag to false.')
      credentials = CheckValidCreds(reference, 'scheduled_query',
                                    transfer_client)
      auth_info = {}
      if not credentials:
        auth_info = RetrieveAuthorizationInfo(reference, 'scheduled_query',
                                              transfer_client)
      schedule_args = bigquery_client.TransferScheduleArgs(
          schedule=self.schedule,
          disable_auto_scheduling=self.no_auto_scheduling)
      params = {
          'query': query,
      }
      target_dataset = self.target_dataset
      if self.destination_table:
        target_dataset = client.GetTableReference(
            self.destination_table).GetDatasetReference().datasetId
        destination_table = client.GetTableReference(
            self.destination_table).tableId
        params['destination_table_name_template'] = destination_table
      if self.append_table:
        params['write_disposition'] = 'WRITE_APPEND'
      if self.replace:
        params['write_disposition'] = 'WRITE_TRUNCATE'
      if self.time_partitioning_field:
        params['partitioning_field'] = self.time_partitioning_field
      if self.time_partitioning_type:
        params['partitioning_type'] = self.time_partitioning_type
      transfer_name = client.CreateTransferConfig(
          reference=reference,
          data_source='scheduled_query',
          target_dataset=target_dataset,
          display_name=self.display_name,
          params=json.dumps(params),
          auth_info=auth_info,
          destination_kms_key=self.destination_kms_key,
          schedule_args=schedule_args,
          location=FLAGS.location)
      print(('Transfer configuration \'%s\' successfully created.' %
             transfer_name))
      return

    if self.connection_property:
      kwds['connection_properties'] = []
      for key_value in self.connection_property:
        key_value = key_value.split('=', 2)
        if len(key_value) != 2:
          raise app.UsageError(
              'Invalid connection_property syntax; expected key=value')
        kwds['connection_properties'].append({
            'key': key_value[0],
            'value': key_value[1]
        })
    if self.session_id:
      if 'connection_properties' not in kwds:
        kwds['connection_properties'] = []
      for connection_property in kwds['connection_properties']:
        if connection_property['key'] == 'session_id':
          raise app.UsageError(
              '--session_id should not be set if session_id is specified in '
              '--connection_properties')
      kwds['connection_properties'].append({
          'key': 'session_id',
          'value': self.session_id
      })
    if self.create_session:
      kwds['create_session'] = self.create_session
    if self.rpc:
      if self.allow_large_results:
        raise app.UsageError(
            'allow_large_results cannot be specified in rpc mode.')
      if self.destination_table:
        raise app.UsageError(
            'destination_table cannot be specified in rpc mode.')
      if FLAGS.job_id or FLAGS.fingerprint_job_id:
        raise app.UsageError(
            'job_id and fingerprint_job_id cannot be specified in rpc mode.')
      if self.batch:
        raise app.UsageError('batch cannot be specified in rpc mode.')
      if self.flatten_results:
        raise app.UsageError('flatten_results cannot be specified in rpc mode.')
      if self.continuous:
        raise app.UsageError(
            'continuous cannot be specified in rpc mode.')
      kwds['max_results'] = self.max_rows
      fields, rows, execution = client.RunQueryRpc(query, **kwds)
      if self.dry_run:
        _PrintDryRunInfo(execution)
      else:
        Factory.ClientTablePrinter.GetTablePrinter().PrintTable(fields, rows)
        # If we are here, the job succeeded, but print warnings if any.
        _PrintJobMessages(execution)
    else:
      if self.destination_table and self.append_table:
        kwds['write_disposition'] = 'WRITE_APPEND'
      if self.destination_table and self.replace:
        kwds['write_disposition'] = 'WRITE_TRUNCATE'
      if self.require_cache:
        kwds['create_disposition'] = 'CREATE_NEVER'
      if ((self.batch and self.priority is not None and
           self.priority != 'BATCH') or
          (self.batch is not None and not self.batch and
           self.priority == 'BATCH')):
        raise app.UsageError('Conflicting values of --batch and --priority.')
      priority = None
      if self.batch:
        priority = 'BATCH'
      if self.priority is not None:
        priority = self.priority
      if priority is not None:
        kwds['priority'] = priority

      kwds['destination_table'] = self.destination_table
      kwds['allow_large_results'] = self.allow_large_results
      kwds['flatten_results'] = self.flatten_results
      kwds['continuous'] = self.continuous
      kwds['job_id'] = _GetJobIdFromFlags()
      if self.job_timeout_ms:
        kwds['job_timeout_ms'] = self.job_timeout_ms

      job = client.Query(query, **kwds)

      if self.dry_run:
        _PrintDryRunInfo(job)
      elif not FLAGS.sync:
        self.PrintJobStartInfo(job)
      else:
        self._PrintQueryJobResults(client, job)
    if read_schema:
      client.UpdateTable(
          client.GetTableReference(self.destination_table),
          read_schema)

  def _PrintQueryJobResults(self, client, job):
    """Prints the results of a successful query job.

    This function is invoked only for successful jobs.  Output is printed to
    stdout.  Depending on flags, the output is printed in either free-form or
    json style.

    Args:
      client: Bigquery client object
      job: json of the job, expressed as a dictionary
    """
    if (job['statistics']['query']['statementType'] == 'SCRIPT'
        ):
      self._PrintScriptJobResults(client, job)
    else:
      self.PrintNonScriptQueryJobResults(client, job)

  def _PrintScriptJobResults(self, client, job):
    """Prints the results of a successful script job.

    This function is invoked only for successful script jobs.  Prints the output
    of each successful child job representing a statement to stdout.

    Child jobs representing expression evaluations are not printed, as are child
    jobs which failed, but whose error was handled elsewhere in the script.

    Depending on flags, the output is printed in either free-form or
    json style.

    Args:
      client: Bigquery client object
      job: json of the script job, expressed as a dictionary
    """
    # Fetch one more child job than the maximum, so we can tell if some of the
    # child jobs are missing.
    child_jobs = list(
        client.ListJobs(
            reference=bigquery_client.ApiClientHelper.ProjectReference.Create(
                projectId=job['jobReference']['projectId']),
            max_results=self.max_child_jobs + 1,
            all_users=False,
            min_creation_time=None,
            max_creation_time=None,
            page_token=None,
            parent_job_id=job['jobReference']['jobId']))

    # If there is no child job, show the parent job result instead.
    if not child_jobs:
      self.PrintNonScriptQueryJobResults(client, job)
      return

    child_jobs.sort(key=lambda job: job['statistics']['creationTime'])
    if len(child_jobs) == self.max_child_jobs + 1:
      # The number of child jobs exceeds the maximum number to fetch.  There
      # is no way to tell which child jobs are missing, so just display the
      # final result of the script.
      sys.stderr.write(
          'Showing only the final result because the number of child jobs '
          'exceeds --max_child_jobs (%s).\n' % self.max_child_jobs)
      self.PrintNonScriptQueryJobResults(client, job)
      return
    # To reduce verbosity, only show the results for statements, not
    # expressions.
    statement_child_jobs = [
        job for job in child_jobs if job.get('statistics', {}).get(
            'scriptStatistics', {}).get('evaluationKind', '') == 'STATEMENT'
    ]
    is_raw_json = FLAGS.format == 'json'
    is_json = is_raw_json or FLAGS.format == 'prettyjson'
    if is_json:
      sys.stdout.write('[')
    statements_printed = 0
    for (i, child_job_info) in enumerate(statement_child_jobs):
      if BigqueryClient.IsFailedJob(child_job_info):
        # Skip failed jobs; if the error was handled, we want to ignore it;
        # if it wasn't handled, we'll see it soon enough when we print the
        # failure for the overall script.
        continue
      if statements_printed >= self.max_statement_results:
        if not is_json:
          sys.stdout.write('Maximum statement results limit reached. '
                           'Specify --max_statement_results to increase this '
                           'limit.\n')
        break
      if is_json:
        if i > 0:
          if is_raw_json:
            sys.stdout.write(',')
          else:
            sys.stdout.write(',\n')
      else:
        stack_frames = (
            child_job_info.get('statistics', {}).get('scriptStatistics',
                                                     {}).get('stackFrames', []))
        if len(stack_frames) <= 0:
          break
        sys.stdout.write('%s; ' %
                         six.ensure_str(stack_frames[0].get('text', '')))
        if len(stack_frames) >= 2:
          sys.stdout.write('\n')
        # Print stack traces
        for stack_frame in stack_frames:
          sys.stdout.write(
              '-- at %s[%d:%d]\n' %
              (stack_frame.get('procedureId', ''), stack_frame['startLine'],
               stack_frame['startColumn']))
      self.PrintNonScriptQueryJobResults(client, child_job_info)
      statements_printed = statements_printed + 1
    if is_json:
      sys.stdout.write(']\n')

  def PrintNonScriptQueryJobResults(self, client, job):
    printable_job_info = client.FormatJobInfo(job)
    is_assert_job = job['statistics']['query']['statementType'] == 'ASSERT'
    if not BigqueryClient.IsFailedJob(job) and not _IsSuccessfulDmlOrDdlJob(
        printable_job_info) and not is_assert_job:
      # ReadSchemaAndJobRows can handle failed jobs, but cannot handle
      # a successful DML job if the destination table is already deleted.
      # DML, DDL, and ASSERT do not have query result, so skip
      # ReadSchemaAndJobRows.
      fields, rows = client.ReadSchemaAndJobRows(
          job['jobReference'], start_row=self.start_row, max_rows=self.max_rows)
      Factory.ClientTablePrinter.GetTablePrinter().PrintTable(fields, rows)
    # If we are here, the job succeeded, but print warnings if any.
    _PrintJobMessages(printable_job_info)


def _GetExternalDataConfig(
    file_path_or_simple_spec,
    use_avro_logical_types=False,
    parquet_enum_as_string=False,
    parquet_enable_list_inference=False,
    metadata_cache_mode=None,
    object_metadata=None,
    preserve_ascii_control_characters=None,
    reference_file_schema_uri=None,
    file_set_spec_type=None,
):
  """Returns a ExternalDataConfiguration from the file or specification string.

  Determines if the input string is a file path or a string,
  then returns either the parsed file contents, or the parsed configuration from
  string. The file content is expected to be JSON representation of
  ExternalDataConfiguration. The specification is expected to be of the form
  schema@format=uri i.e. schema is separated from format and uri by '@'. If the
  uri itself contains '@' or '=' then the JSON file option should be used.
  "format=" can be omitted for CSV files.

  Raises:
    UsageError: when incorrect usage or invalid args are used.
  """
  maybe_filepath = os.path.expanduser(file_path_or_simple_spec)
  if os.path.isfile(maybe_filepath):
    try:
      with open(maybe_filepath) as external_config_file:
        return yaml.safe_load(external_config_file)
    except yaml.error.YAMLError as e:
      raise app.UsageError(
          ('Error decoding YAML external table definition from '
           'file %s: %s') % (maybe_filepath, e))
  else:
    source_format = 'CSV'
    schema = None
    connection_id = None
    error_msg = ('Error decoding external_table_definition. '
                 'external_table_definition should either be the name of a '
                 'JSON file or the text representation of an external table '
                 'definition. Given:%s') % (
                     file_path_or_simple_spec)

    parts = file_path_or_simple_spec.split('@')
    if len(parts) == 1:
      # Schema and connection are not specified.
      format_and_uri = parts[0]
    elif len(parts) == 2:
      # when there are 2 components, it can be:
      # 1. format=uri@connection_id.e.g csv=gs://bucket/file@us.conn1
      # 2. schema@format=uri        e.g.col1::INTEGER@csv=gs://bucket/file
      # if the first element is format=uri, then second element is connnection.
      # Else, the first is schema, second is format=uri.
      if parts[0].find('://') >= 0:
        # format=uri and connection specified.
        format_and_uri = parts[0]
        connection_id = parts[1]
      else:
        # Schema and format=uri are specified.
        schema = parts[0]
        format_and_uri = parts[1]
    elif len(parts) == 3:
      # Schema and connection both are specified
      schema = parts[0]
      format_and_uri = parts[1]
      connection_id = parts[2]
    else:
      raise app.UsageError(error_msg)

    separator_pos = format_and_uri.find('=')
    if separator_pos < 0:
      # Format is not specified
      uri = format_and_uri
    else:
      source_format = format_and_uri[0:separator_pos]
      uri = format_and_uri[separator_pos + 1:]

    if not uri:
      raise app.UsageError(error_msg)
    # When using short notation for external table definition
    # autodetect is always performed.

    return _CreateExternalTableDefinition(
        source_format,
        uri,
        schema,
        True,
        connection_id,
        use_avro_logical_types=use_avro_logical_types,
        parquet_enum_as_string=parquet_enum_as_string,
        parquet_enable_list_inference=parquet_enable_list_inference,
        metadata_cache_mode=metadata_cache_mode,
        object_metadata=object_metadata,
        preserve_ascii_control_characters=preserve_ascii_control_characters,
        reference_file_schema_uri=reference_file_schema_uri,
        file_set_spec_type=file_set_spec_type,
    )


class _Extract(BigqueryCmd):
  usage = """extract <source_table> <destination_uris>"""

  def __init__(self, name, fv):
    super(_Extract, self).__init__(name, fv)
    flags.DEFINE_string(
        'field_delimiter',
        None,
        'The character that indicates the boundary between columns in the '
        'output file. "\\t" and "tab" are accepted names for tab. '
        'Not applicable when extracting models.',
        short_name='F',
        flag_values=fv)
    flags.DEFINE_enum(
        'destination_format',
        None, [
            'CSV', 'NEWLINE_DELIMITED_JSON', 'AVRO', 'PARQUET',
            'ML_TF_SAVED_MODEL', 'ML_XGBOOST_BOOSTER'
        ], 'The extracted file format. Format CSV, NEWLINE_DELIMITED_JSON, '
        'PARQUET and AVRO are applicable for extracting tables. '
        'Formats ML_TF_SAVED_MODEL and ML_XGBOOST_BOOSTER are applicable for '
        'extracting models. The default value for tables is CSV. Tables with '
        'nested or repeated fields cannot be exported as CSV. The default '
        'value for models is ML_TF_SAVED_MODEL.',
        flag_values=fv)
    flags.DEFINE_integer(
        'trial_id',
        None,
        '1-based ID of the trial to be exported from a hyperparameter tuning '
        'model. The default_trial_id will be exported if not specified. This '
        'does not apply for models not trained with hyperparameter tuning.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'add_serving_default_signature',
        None, 'Whether to add serving_default signature for export BigQuery ML '
        'trained tf based models.',
        flag_values=fv)
    flags.DEFINE_enum(
        'compression',
        'NONE', ['GZIP', 'DEFLATE', 'SNAPPY', 'ZSTD', 'NONE'],
        'The compression type to use for exported files. Possible values '
        'include GZIP, DEFLATE, SNAPPY, ZSTD, and NONE. The default value is '
        'None. Not applicable when extracting models.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'print_header',
        None, 'Whether to print header rows for formats that '
        'have headers. Prints headers by default.'
        'Not applicable when extracting models.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'use_avro_logical_types',
        None,
        'If destinationFormat is set to "AVRO", this flag indicates whether to '
        'enable extracting applicable column types (such as TIMESTAMP) to '
        'their corresponding AVRO logical types (timestamp-micros), instead of '
        'only using their raw types (avro-long). '
        'Not applicable when extracting models.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'model',
        False,
        'Extract model with this model ID.',
        short_name='m',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier, destination_uris):
    """Perform an extract operation of source into destination_uris.

    Usage:
      extract <source_table> <destination_uris>

    Use -m option to extract a source_model.

    Examples:
      bq extract ds.table gs://mybucket/table.csv
      bq extract -m ds.model gs://mybucket/model

    Arguments:
      source_table: Source table to extract.
      source_model: Source model to extract.
      destination_uris: One or more Google Cloud Storage URIs, separated by
        commas.
    """
    client = Client.Get()
    kwds = {
        'job_id': _GetJobIdFromFlags(),
    }
    if FLAGS.location:
      kwds['location'] = FLAGS.location

    if self.m:
      reference = client.GetModelReference(identifier)
    else:
      reference = client.GetTableReference(identifier)
    job = client.Extract(
        reference,
        destination_uris,
        print_header=self.print_header,
        field_delimiter=_NormalizeFieldDelimiter(self.field_delimiter),
        destination_format=self.destination_format,
        trial_id=self.trial_id,
        add_serving_default_signature=self.add_serving_default_signature,
        compression=self.compression,
        use_avro_logical_types=self.use_avro_logical_types,
        **kwds)
    if FLAGS.sync:
      # If we are here, the job succeeded, but print warnings if any.
      _PrintJobMessages(client.FormatJobInfo(job))
    else:
      self.PrintJobStartInfo(job)


class _Partition(BigqueryCmd):  # pylint: disable=missing-docstring
  usage = """partition source_prefix destination_table"""

  def __init__(self, name, fv):
    super(_Partition, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'no_clobber',
        False,
        'Do not overwrite an existing partition.',
        short_name='n',
        flag_values=fv)
    flags.DEFINE_string(
        'time_partitioning_type',
        'DAY',
        'Enables time based partitioning on the table and set the type. The '
        'default value is DAY, which will generate one partition per day. '
        'Other supported values are HOUR, MONTH, and YEAR.',
        flag_values=fv)
    flags.DEFINE_integer(
        'time_partitioning_expiration',
        None,
        'Enables time based partitioning on the table and sets the number of '
        'seconds for which to keep the storage for the partitions in the table.'
        ' The storage in a partition will have an expiration time of its '
        'partition time plus this value.',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, source_prefix, destination_table):
    """Copies source tables into partitioned tables.

    Usage:
    bq partition <source_table_prefix> <destination_partitioned_table>

    Copies tables of the format <source_table_prefix><time_unit_suffix> to a
    destination partitioned table, with the <time_unit_suffix> of the source
    tables becoming the partition ID of the destination table partitions. The
    suffix is <YYYYmmdd> by default, <YYYY> if the time_partitioning_type flag
    is set to YEAR, <YYYYmm> if set to MONTH, and <YYYYmmddHH> if set to HOUR.

    If the destination table does not exist, one will be created with
    a schema and that matches the last table that matches the supplied
    prefix.

    Examples:
      bq partition dataset1.sharded_ dataset2.partitioned_table
    """

    client = Client.Get()
    formatter = _GetFormatterFromFlags()

    source_table_prefix = client.GetReference(source_prefix)
    _Typecheck(source_table_prefix, TableReference,
               'Cannot determine table associated with "%s"' % (source_prefix,))
    destination_table = client.GetReference(destination_table)
    _Typecheck(
        destination_table, TableReference,
        'Cannot determine table associated with "%s"' % (destination_table,))

    source_dataset = source_table_prefix.GetDatasetReference()
    source_id_prefix = six.ensure_str(source_table_prefix.tableId)
    source_id_len = len(source_id_prefix)

    job_id_prefix = _GetJobIdFromFlags()
    if isinstance(job_id_prefix, JobIdGenerator):
      job_id_prefix = job_id_prefix.Generate(
          [source_table_prefix, destination_table])

    destination_dataset = destination_table.GetDatasetReference()

    BigqueryClient.ConfigureFormatter(formatter, TableReference)
    results = map(client.FormatTableInfo,
                  client.ListTables(source_dataset, max_results=1000 * 1000))

    partition_ids = []
    representative_table = None

    time_format = '%Y%m%d'  # default to format for DAY
    if self.time_partitioning_type == 'HOUR':
      time_format = '%Y%m%d%H'
    elif self.time_partitioning_type == 'MONTH':
      time_format = '%Y%m'
    elif self.time_partitioning_type == 'YEAR':
      time_format = '%Y'

    for result in results:
      table_id = six.ensure_str(result['tableId'])
      if table_id.startswith(source_id_prefix):
        suffix = table_id[source_id_len:]
        try:
          partition_id = datetime.datetime.strptime(suffix, time_format)
          partition_ids.append(partition_id.strftime(time_format))
          representative_table = result
        except ValueError:
          pass

    if not representative_table:
      print('No matching source tables found')
      return

    print('Copying %d source partitions to %s' %
          (len(partition_ids), destination_table))

    # Check to see if we need to create the destination table.
    if not client.TableExists(destination_table):
      source_table_id = representative_table['tableId']
      source_table_ref = source_dataset.GetTableReference(source_table_id)
      source_table_schema = client.GetTableSchema(source_table_ref)
      # Get fields in the schema.
      if source_table_schema:
        source_table_schema = source_table_schema['fields']

      time_partitioning = _ParseTimePartitioning(
          self.time_partitioning_type, self.time_partitioning_expiration)

      print('Creating table: %s with schema from %s and partition spec %s' %
            (destination_table, source_table_ref, time_partitioning))

      client.CreateTable(
          destination_table,
          schema=source_table_schema,
          time_partitioning=time_partitioning)
      print('%s successfully created.' % (destination_table,))

    for partition_id in partition_ids:
      destination_table_id = '%s$%s' % (destination_table.tableId, partition_id)
      source_table_id = '%s%s' % (source_id_prefix, partition_id)
      current_job_id = '%s%s' % (job_id_prefix, partition_id)

      source_table = source_dataset.GetTableReference(source_table_id)
      destination_partition = destination_dataset.GetTableReference(
          destination_table_id)

      avoid_copy = False
      if self.no_clobber:
        maybe_destination_partition = client.TableExists(destination_partition)
        avoid_copy = (
            maybe_destination_partition and
            int(maybe_destination_partition['numBytes']) > 0)

      if avoid_copy:
        print("Table '%s' already exists, skipping" % (destination_partition,))
      else:
        print('Copying %s to %s' % (source_table, destination_partition))
        kwds = {
            'write_disposition': 'WRITE_TRUNCATE',
            'job_id': current_job_id,
        }
        if FLAGS.location:
          kwds['location'] = FLAGS.location
        job = client.CopyTable([source_table], destination_partition, **kwds)
        if not FLAGS.sync:
          self.PrintJobStartInfo(job)
        else:
          print('Successfully copied %s to %s' %
                (source_table, destination_partition))


class _List(BigqueryCmd):  # pylint: disable=missing-docstring
  usage = """ls [(-j|-p|-d)] [-a] [-n <number>] [<identifier>]"""

  def __init__(self, name, fv):
    super(_List, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'all',
        None, 'Show all results. For jobs, will show jobs from all users. For '
        'datasets, will list hidden datasets.'
        'For transfer configs and runs, '
        'this flag is redundant and not necessary.'
        '',
        short_name='a',
        flag_values=fv)
    flags.DEFINE_boolean(
        'all_jobs', None, 'DEPRECATED. Use --all instead', flag_values=fv)
    flags.DEFINE_boolean(
        'jobs',
        False,
        'Show jobs described by this identifier.',
        short_name='j',
        flag_values=fv)
    flags.DEFINE_integer(
        'max_results',
        None,
        'Maximum number to list.',
        short_name='n',
        flag_values=fv)
    flags.DEFINE_integer(
        'min_creation_time',
        None,
        'Timestamp in milliseconds. Return jobs created after this timestamp.',
        flag_values=fv)
    flags.DEFINE_integer(
        'max_creation_time',
        None,
        'Timestamp in milliseconds. Return jobs created before this timestamp.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'projects', False, 'Show all projects.', short_name='p', flag_values=fv)
    flags.DEFINE_boolean(
        'datasets',
        False,
        'Show datasets described by this identifier.',
        short_name='d',
        flag_values=fv)
    flags.DEFINE_boolean(
        'models', False, 'Show all models.', short_name='m', flag_values=fv)
    flags.DEFINE_boolean(
        'routines', False, 'Show all routines.', flag_values=fv)
    flags.DEFINE_boolean(
        'row_access_policies',
        False,
        'Show all row access policies.',
        flag_values=fv)
    flags.DEFINE_string(
        'transfer_location',
        None,
        'Location for list transfer config (e.g., "eu" or "us").',
        flag_values=fv)
    flags.DEFINE_boolean(
        'transfer_config',
        False, 'Show transfer configurations described by this identifier. '
        'This requires setting --transfer_location.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'transfer_run', False, 'List the transfer runs.', flag_values=fv)
    flags.DEFINE_string(
        'run_attempt',
        'LATEST', 'For transfer run, respresents which runs should be '
        'pulled. See https://cloud.google.com/bigquery/docs/reference/'
        'datatransfer/rest/v1/projects.transferConfigs.runs/list#RunAttempt '
        'for details',
        flag_values=fv)
    flags.DEFINE_bool(
        'transfer_log',
        False,
        'List messages under the run specified',
        flag_values=fv)
    flags.DEFINE_string(
        'message_type',
        None, 'usage:- messageTypes:INFO '
        'For transferlog, represents which messages should '
        'be listed. See '
        'https://cloud.google.com/bigquery/docs/reference'
        '/datatransfer/rest/v1/projects.transferConfigs'
        '.runs.transferLogs#MessageSeverity '
        'for details.',
        flag_values=fv)
    flags.DEFINE_string(
        'page_token',
        None,
        'Start listing from this page token.',
        short_name='k',
        flag_values=fv)
    flags.DEFINE_boolean(
        'print_last_token',
        False,
        'If true, also print the next page token for the jobs list.',
        flag_values=fv)
    flags.DEFINE_string(
        'filter',
        None, 'Filters resources based on the filter expression.'
        '\nFor datasets, use a space-separated list of label keys and values '
        'in the form "labels.key:value". Datasets must match '
        'all provided filter expressions. See '
        'https://cloud.google.com/bigquery/docs/filtering-labels'
        '#filtering_datasets_using_labels '
        'for details'
        '\nFor transfer configurations, the filter expression, '
        'in the form "dataSourceIds:value(s)", will show '
        'transfer configurations with '
        ' the specified dataSourceId. '
        '\nFor transfer runs, the filter expression, '
        'in the form "states:VALUE(s)", will show '
        'transfer runs with the specified states. See '
        'https://cloud.google.com/bigquery/docs/reference/datatransfer/rest/v1/'
        'TransferState '
        'for details.'
        '\nFor jobs, filtering is currently not supported.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'reservation',
        None,
        'List all reservations for the given project and location.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'capacity_commitment',
        None,
        'Lists all capacity commitments (e.g. slots) for the given project and '
        'location.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'reservation_assignment',
        None,
        'List all reservation assignments for given project/location',
        flag_values=fv)
    flags.DEFINE_string(
        'parent_job_id',
        None,
        'Only show jobs which are children of this parent job; if omitted, '
        'shows all jobs which have no parent.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'connection',
        None,
        'List all connections for given project/location',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier=''):
    """List the objects contained in the named collection.

    List the objects in the named project or dataset. A trailing : or
    . can be used to signify a project or dataset.
     * With -j, show the jobs in the named project.
     * With -p, show all projects.

    Examples:
      bq ls
      bq ls -j proj
      bq ls -p -n 1000
      bq ls mydataset
      bq ls -a
      bq ls -m mydataset
      bq ls --routines mydataset
      bq ls --row_access_policies mytable (requires whitelisting)
      bq ls --filter labels.color:red
      bq ls --filter 'labels.color:red labels.size:*'
      bq ls --transfer_config --transfer_location='us'
          --filter='dataSourceIds:play,adwords'
      bq ls --transfer_run --filter='states:SUCCESSED,PENDING'
          --run_attempt='LATEST' projects/p/locations/l/transferConfigs/c
      bq ls --transfer_log --message_type='messageTypes:INFO,ERROR'
          projects/p/locations/l/transferConfigs/c/runs/r
      bq ls --capacity_commitment --project_id=proj --location='us'
      bq ls --reservation --project_id=proj --location='us'
      bq ls --reservation_assignment --project_id=proj --location='us'
      bq ls --reservation_assignment --project_id=proj --location='us'
          <reservation_id>
      bq ls --connection --project_id=proj --location=us
    """

    # pylint: disable=g-doc-exception
    if ValidateAtMostOneSelected(self.j, self.p, self.d):
      raise app.UsageError('Cannot specify more than one of -j, -p, or -d.')
    if self.j and self.p:
      raise app.UsageError('Cannot specify more than one of -j and -p.')
    if self.p and identifier:
      raise app.UsageError('Cannot specify an identifier with -p')

    # Copy deprecated flag specifying 'all' to current one.
    if self.all_jobs is not None:
      self.a = self.all_jobs

    client = Client.Get()
    if identifier:
      reference = client.GetReference(identifier)
    else:
      try:
        reference = client.GetReference(identifier)
      except bq_error.BigqueryError:
        # We want to let through the case of no identifier, which
        # will fall through to the second case below.
        reference = None

    if self.row_access_policies:
      _Typecheck(reference, TableReference,
                 ('Invalid identifier "%s" for ls, cannot list row access '
                  'policies on object of type %s') %
                 (identifier, type(reference).__name__))
    else:
      # If we got a TableReference, we might be able to make sense
      # of it as a DatasetReference, as in 'ls foo' with dataset_id
      # set.
      if isinstance(reference, TableReference):
        try:
          reference = client.GetDatasetReference(identifier)
        except bq_error.BigqueryError:
          pass
      _Typecheck(reference, (type(None), ProjectReference, DatasetReference),
                 ('Invalid identifier "%s" for ls, cannot call list on object '
                  'of type %s') % (identifier, type(reference).__name__))

    if self.d and isinstance(reference, DatasetReference):
      reference = reference.GetProjectReference()

    page_token = self.k
    results = None
    object_type = None
    if self.j:
      object_type = JobReference
      reference = client.GetProjectReference(identifier)
      _Typecheck(reference, ProjectReference,
                 'Cannot determine job(s) associated with "%s"' % (identifier,))
      if self.print_last_token:
        results = client.ListJobsAndToken(
            reference=reference,
            max_results=self.max_results,
            all_users=self.a,
            min_creation_time=self.min_creation_time,
            max_creation_time=self.max_creation_time,
            page_token=page_token,
            parent_job_id=self.parent_job_id)
        assert object_type is not None
        _PrintObjectsArrayWithToken(results, object_type)
        return
      results = client.ListJobs(
          reference=reference,
          max_results=self.max_results,
          all_users=self.a,
          min_creation_time=self.min_creation_time,
          max_creation_time=self.max_creation_time,
          page_token=page_token,
          parent_job_id=self.parent_job_id)
    elif self.m:
      object_type = ModelReference
      reference = client.GetDatasetReference(identifier)
      response = client.ListModels(
          reference=reference,
          max_results=self.max_results,
          page_token=page_token)
      if 'models' in response:
        results = response['models']
      if 'nextPageToken' in response:
        _PrintPageToken(response)
    elif self.routines:
      object_type = RoutineReference
      reference = client.GetDatasetReference(identifier)
      response = client.ListRoutines(
          reference=reference,
          max_results=self.max_results,
          page_token=page_token,
          filter_expression=self.filter)
      if 'routines' in response:
        results = response['routines']
      if 'nextPageToken' in response:
        _PrintPageToken(response)
    elif self.reservation_assignment:
      try:
        if FLAGS.api_version == 'v1beta1':
          object_type = BetaReservationAssignmentReference
        else:
          object_type = ReservationAssignmentReference
        reference = client.GetReservationReference(
            identifier=identifier if identifier else '-',
            default_location=FLAGS.location,
            default_reservation_id=' ')
        response = client.ListReservationAssignments(reference,
                                                     self.max_results,
                                                     self.page_token)
        if 'assignments' in response:
          results = response['assignments']
        else:
          print('No reservation assignments found.')
        if 'nextPageToken' in response:
          _PrintPageToken(response)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to list reservation assignments '%s': %s" % (identifier, e))
    elif self.capacity_commitment:
      try:
        object_type = CapacityCommitmentReference
        reference = client.GetCapacityCommitmentReference(
            identifier=identifier,
            default_location=FLAGS.location,
            default_capacity_commitment_id=' ')
        response = client.ListCapacityCommitments(reference, self.max_results,
                                                  self.page_token)
        if 'capacityCommitments' in response:
          results = response['capacityCommitments']
        else:
          print('No capacity commitments found.')
        if 'nextPageToken' in response:
          _PrintPageToken(response)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to list capacity commitments '%s': %s" % (identifier, e))
    elif self.reservation:
      response = None
      if FLAGS.api_version == 'v1beta1':
        object_type = BetaReservationReference
      else:
        object_type = ReservationReference
      reference = client.GetReservationReference(
          identifier=identifier,
          default_location=FLAGS.location,
          default_reservation_id=' ')
      try:
        if True:
          response = client.ListBiReservations(reference)
          results = [response]
        if response and 'size' in response:
          size_in_bytes = int(response['size'])
          size_in_gbytes = size_in_bytes / (1024 * 1024 * 1024)
          print('BI Engine reservation: %sGB' % size_in_gbytes)
      except bq_error.BigqueryNotFoundError:
        pass
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to list BI reservations '%s': %s" % (identifier, e))

      try:
        if True:
          response = client.ListReservations(
              reference=reference,
              page_size=self.max_results,
              page_token=self.page_token)
          results = (response['reservations'] if 'reservations' in response
                     else [])
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to list reservations '%s': %s" % (identifier, e))
      if not results:
        print('No reservations found.')
      if response and 'nextPageToken' in response:
        _PrintPageToken(response)
    elif self.transfer_config:
      object_type = TransferConfigReference
      reference = client.GetProjectReference(
          _FormatProjectIdentifier(client, identifier))
      _Typecheck(
          reference, ProjectReference,
          'Cannot determine transfer configuration(s) '
          'associated with "%s"' % (identifier,))

      if self.transfer_location is None:
        raise app.UsageError(('Need to specify transfer_location for '
                              'list transfer configs.'))

      # transfer_configs tuple contains transfer configs at index 0 and
      # next page token at index 1 if there is one.
      transfer_configs = client.ListTransferConfigs(
          reference=reference,
          location=self.transfer_location,
          page_size=self.max_results,
          page_token=page_token,
          data_source_ids=self.filter)
      # If the max_results flag is set and the length of transfer_configs is 2
      # then it also contains the next_page_token.
      if self.max_results and len(transfer_configs) == 2:
        page_token = dict(nextPageToken=transfer_configs[1])
        _PrintPageToken(page_token)
      results = transfer_configs[0]
    elif self.transfer_run:
      object_type = TransferRunReference
      run_attempt = self.run_attempt
      formatted_identifier = _FormatDataTransferIdentifiers(client, identifier)
      reference = TransferRunReference(transferRunName=formatted_identifier)
      # list_transfer_runs_result tuple contains transfer runs at index 0 and
      # next page token at index 1 if there is next page token.
      list_transfer_runs_result = client.ListTransferRuns(
          reference,
          run_attempt,
          max_results=self.max_results,
          page_token=self.page_token,
          states=self.filter)
      # If the max_results flag is set and the length of response is 2
      # then it also contains the next_page_token.
      if self.max_results and len(list_transfer_runs_result) == 2:
        page_token = dict(nextPageToken=list_transfer_runs_result[1])
        _PrintPageToken(page_token)
      results = list_transfer_runs_result[0]
    elif self.transfer_log:
      object_type = TransferLogReference
      formatted_identifier = _FormatDataTransferIdentifiers(client, identifier)
      reference = TransferLogReference(transferRunName=formatted_identifier)
      # list_transfer_log_result tuple contains transfer logs at index 0 and
      # next page token at index 1 if there is one.
      list_transfer_log_result = client.ListTransferLogs(
          reference,
          message_type=self.message_type,
          max_results=self.max_results,
          page_token=self.page_token)
      if self.max_results and len(list_transfer_log_result) == 2:
        page_token = dict(nextPageToken=list_transfer_log_result[1])
        _PrintPageToken(page_token)
      results = list_transfer_log_result[0]
    elif self.connection:
      object_type = ConnectionReference
      list_connections_results = client.ListConnections(
          FLAGS.project_id,
          FLAGS.location,
          max_results=self.max_results,
          page_token=self.page_token)
      if 'connections' in list_connections_results:
        results = list_connections_results['connections']
      else:
        print('No connections found.')
      if 'nextPageToken' in list_connections_results:
        _PrintPageToken(list_connections_results)
    elif self.row_access_policies:
      object_type = RowAccessPolicyReference
      response = client.ListRowAccessPoliciesWithGrantees(
          reference,
          self.max_results,
          self.page_token,
      )
      if 'rowAccessPolicies' in response:
        results = response['rowAccessPolicies']
      else:
        print('No row access policies found.')
      if 'nextPageToken' in response:
        _PrintPageToken(response)
    elif self.p or reference is None:
      object_type = ProjectReference
      results = client.ListProjects(
          max_results=self.max_results, page_token=page_token)
    elif isinstance(reference, ProjectReference):
      object_type = DatasetReference
      results = client.ListDatasets(
          reference,
          max_results=self.max_results,
          list_all=self.a,
          page_token=page_token,
          filter_expression=self.filter)
    else:  # isinstance(reference, DatasetReference):
      object_type = TableReference
      results = client.ListTables(
          reference, max_results=self.max_results, page_token=page_token)
    if results:
      assert object_type is not None
      _PrintObjectsArray(results, object_type)


def _PrintPageToken(page_token):
  """Prints the page token in the pretty format.

  Args:
    page_token: The dictonary mapping of pageToken with string 'nextPageToken'.
  """
  formatter = _GetFormatterFromFlags(secondary_format='pretty')
  BigqueryClient.ConfigureFormatter(formatter, NextPageTokenReference)
  formatter.AddDict(page_token)
  formatter.Print()


class _Delete(BigqueryCmd):
  usage = """rm [-f] [-r] [(-d|-t)] <identifier>"""

  def __init__(self, name, fv):
    super(_Delete, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'dataset',
        False,
        'Remove dataset described by this identifier.',
        short_name='d',
        flag_values=fv)
    flags.DEFINE_boolean(
        'table',
        False,
        'Remove table described by this identifier.',
        short_name='t',
        flag_values=fv)
    flags.DEFINE_boolean(
        'job',
        False,
        'Remove job described by this identifier.',
        short_name='j',
        flag_values=fv)
    flags.DEFINE_boolean(
        'transfer_config',
        False,
        'Remove transfer configuration described by this identifier.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'force',
        None,
        "Ignore existing tables and datasets, don't prompt.",
        short_name='f',
        flag_values=fv)
    flags.DEFINE_boolean(
        'recursive',
        False,
        'Remove dataset and any tables it may contain.',
        short_name='r',
        flag_values=fv)
    flags.DEFINE_boolean(
        'reservation',
        False,
        'Deletes the reservation described by this identifier.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'capacity_commitment',
        False,
        'Deletes the capacity commitment described by this identifier.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'reservation_assignment',
        False,
        'Delete a reservation assignment.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'model',
        False,
        'Remove model with this model ID.',
        short_name='m',
        flag_values=fv)
    flags.DEFINE_boolean(
        'routine',
        False,
        'Remove routine with this routine ID.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'connection', False, 'Delete a connection.', flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier):
    """Delete the dataset, table, transfer config, or reservation described by identifier.

    Always requires an identifier, unlike the show and ls commands.
    By default, also requires confirmation before deleting. Supports
    the -d -t flags to signify that the identifier is a dataset
    or table.
     * With -f, don't ask for confirmation before deleting.
     * With -r, remove all tables in the named dataset.

    Examples:
      bq rm ds.table
      bq rm -m ds.model
      bq rm --routine ds.routine
      bq rm -r -f old_dataset
      bq rm --transfer_config=projects/p/locations/l/transferConfigs/c
      bq rm --connection --project_id=proj --location=us con
      bq rm --capacity_commitment proj:US.capacity_commitment_id
      bq rm --reservation --project_id=proj --location=us reservation_name
      bq rm --reservation_assignment --project_id=proj --location=us
          assignment_name
    """

    client = Client.Get()

    # pylint: disable=g-doc-exception
    if (self.d + self.t + self.j + self.routine + self.transfer_config +
        self.reservation + self.reservation_assignment +
        self.capacity_commitment + self.connection) > 1:
      raise app.UsageError('Cannot specify more than one resource type.')
    if not identifier:
      raise app.UsageError('Must provide an identifier for rm.')

    if self.t:
      reference = client.GetTableReference(identifier)
    elif self.m:
      reference = client.GetModelReference(identifier)
    elif self.routine:
      reference = client.GetRoutineReference(identifier)
    elif self.d:
      reference = client.GetDatasetReference(identifier)
    elif self.j:
      reference = client.GetJobReference(
          identifier, default_location=FLAGS.location)
    elif self.transfer_config:
      formatted_identifier = _FormatDataTransferIdentifiers(client, identifier)
      reference = TransferConfigReference(
          transferConfigName=formatted_identifier)
    elif self.reservation:
      try:
        reference = client.GetReservationReference(
            identifier=identifier, default_location=FLAGS.location)
        client.DeleteReservation(
            reference
        )
        print("Reservation '%s' successfully deleted." % identifier)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to delete reservation '%s': %s" % (identifier, e))
    elif self.reservation_assignment:
      try:
        reference = client.GetReservationAssignmentReference(
            identifier=identifier, default_location=FLAGS.location)
        client.DeleteReservationAssignment(reference)
        print("Reservation assignment '%s' successfully deleted." % identifier)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to delete reservation assignment '%s': %s" %
            (identifier, e))
    elif self.capacity_commitment:
      try:
        reference = client.GetCapacityCommitmentReference(
            identifier=identifier, default_location=FLAGS.location)
        client.DeleteCapacityCommitment(reference, self.force)
        print("Capacity commitment '%s' successfully deleted." % identifier)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to delete capacity commitment '%s': %s" % (identifier, e))
    elif self.connection:
      reference = client.GetConnectionReference(
          identifier=identifier, default_location=FLAGS.location)
      client.DeleteConnection(reference)
    else:
      reference = client.GetReference(identifier)
      _Typecheck(reference, (DatasetReference, TableReference),
                 'Invalid identifier "%s" for rm.' % (identifier,))

    if isinstance(reference, TableReference) and self.r:
      raise app.UsageError('Cannot specify -r with %r' % (reference,))

    if isinstance(reference, ModelReference) and self.r:
      raise app.UsageError('Cannot specify -r with %r' % (reference,))

    if isinstance(reference, RoutineReference) and self.r:
      raise app.UsageError('Cannot specify -r with %r' % (reference,))

    if not self.force:
      if ((isinstance(reference, DatasetReference) and
           client.DatasetExists(reference)) or
          (isinstance(reference, TableReference) and
           client.TableExists(reference)) or
          (isinstance(reference, JobReference) and client.JobExists(reference))
          or (isinstance(reference, ModelReference) and
              client.ModelExists(reference)) or
          (isinstance(reference, RoutineReference) and
           client.RoutineExists(reference)) or
          (isinstance(reference, TransferConfigReference) and
           client.TransferExists(reference))):
        if 'y' != _PromptYN('rm: remove %r? (y/N) ' % (reference,)):
          print('NOT deleting %r, exiting.' % (reference,))
          return 0

    if isinstance(reference, DatasetReference):
      client.DeleteDataset(
          reference,
          ignore_not_found=self.force,
          delete_contents=self.recursive)
    elif isinstance(reference, TableReference):
      client.DeleteTable(reference, ignore_not_found=self.force)
    elif isinstance(reference, JobReference):
      client.DeleteJob(reference, ignore_not_found=self.force)
    elif isinstance(reference, ModelReference):
      client.DeleteModel(reference, ignore_not_found=self.force)
    elif isinstance(reference, RoutineReference):
      client.DeleteRoutine(reference, ignore_not_found=self.force)
    elif isinstance(reference, TransferConfigReference):
      client.DeleteTransferConfig(reference, ignore_not_found=self.force)


class _Copy(BigqueryCmd):
  usage = """cp [-n] <source_table>[,<source_table>]* <dest_table>"""

  _NOTE = '**** NOTE! **** '
  _DATASET_NOT_FOUND = (
      'Dataset %s not found. Please enter a valid dataset name.'
  )
  _CROSS_REGION_WARNING = (
      'Warning: This operation is a cross-region copy operation. This may incur'
      ' additional charges.'
  )
  _SYNC_FLAG_ENABLED_WARNING = (
      'Warning: This operation is a cross-region copy operation. This may incur'
      ' additional charges and take a long time to complete.\nThis command is'
      ' running in sync mode. It is recommended to use async mode (-sync=false)'
      ' for cross-region copy operation.'
  )
  _CONFIRM_CROSS_REGION = 'cp: Proceed with cross-region copy of %s? [y/N]: '
  _CONFIRM_OVERWRITE = 'cp: Table %s already exists. Replace the table? [y/N]: '
  _NOT_COPYING = ' %s, exiting.'

  def __init__(self, name, fv):
    super(_Copy, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'no_clobber',
        False,
        'Do not overwrite an existing table.',
        short_name='n',
        flag_values=fv)
    flags.DEFINE_boolean(
        'force',
        False,
        "Ignore existing destination tables, don't prompt.",
        short_name='f',
        flag_values=fv)
    flags.DEFINE_boolean(
        'append_table',
        False,
        'Append to an existing table.',
        short_name='a',
        flag_values=fv)
    flags.DEFINE_string(
        'destination_kms_key',
        None,
        'Cloud KMS key for encryption of the destination table data.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'snapshot',
        False,
        'Create a table snapshot of source table.',
        short_name='s',
        flag_values=fv)
    flags.DEFINE_boolean(
        'restore',
        False,
        'Restore table snapshot to a live table. Deprecated, please use clone '
        ' instead.',
        short_name='r',
        flag_values=fv)
    flags.DEFINE_integer(
        'expiration',
        None,
        'Expiration time, in seconds from now, of the destination table.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'clone', False, 'Create a clone of source table.', flag_values=fv)
    self._ProcessCommandRc(fv)

  def _CheckAllSourceDatasetsInSameRegionAndGetFirstSourceRegion(
      self,
      client: BigqueryClient,
      source_references: List[ApiClientHelper.Reference],
  ) -> Tuple[bool, str]:
    """Checks whether all source datasets are from same region.

    Args:
      client: Bigquery client
      source_references: Source reference

    Returns:
      true  - all source datasets are from the same region. Includes the
              scenario in which there is only one source dataset
      false - all source datasets are not from the same region.
    Raises:
      bq_error.BigqueryNotFoundError: If unable to compute the dataset
        region
    """
    all_source_datasets_in_same_region = True
    first_source_region = None
    for _, val in enumerate(source_references):
      source_dataset = val.GetDatasetReference()
      source_region = client.GetDatasetRegion(source_dataset)
      if source_region is None:
        raise bq_error.BigqueryNotFoundError(
            self._DATASET_NOT_FOUND % (str(source_dataset),),
            {'reason': 'notFound'},
            [],
        )
      if first_source_region is None:
        first_source_region = source_region
      elif first_source_region != source_region:
        all_source_datasets_in_same_region = False
        break
    return all_source_datasets_in_same_region, first_source_region

  def shouldContinueAfterCrossRegionCheck(
      self,
      client,
      source_references,
      source_references_str,
      dest_reference,
      destination_region,
  ):
    """Checks if it is a Cross Region Copy operation and obtain confirmation from user.

    Args:
      client: Bigquery client
      source_references: Source reference
      source_references_str: Source reference string
      dest_reference: Destination dataset reference
      destination_region: Destination dataset region

    Returns:
      true  - it is not a cross-region operation, or user has used force option,
              or cross-region operation is verified confirmed with user, or
              Insufficient permissions to query datasets for validation
      false - if user did not allow cross-region operation, or
              Dataset does not exist hence operation can't be performed.
    Raises:
      bq_error.BigqueryNotFoundError: If unable to compute the dataset
        region
    """
    destination_dataset = dest_reference.GetDatasetReference()

    try:
      all_source_datasets_in_same_region, first_source_region = (
          self._CheckAllSourceDatasetsInSameRegionAndGetFirstSourceRegion(
              client, source_references
          )
      )
      if destination_region is None:
        destination_region = client.GetDatasetRegion(destination_dataset)
    except bq_error.BigqueryAccessDeniedError as err:
      print(
          'Unable to determine source or destination dataset location, skipping'
          ' cross-region validation: '
          + str(err)
      )
      return True
    if destination_region is None:
      raise bq_error.BigqueryNotFoundError(
          self._DATASET_NOT_FOUND % (str(destination_dataset),),
          {'reason': 'notFound'},
          [],
      )
    if all_source_datasets_in_same_region and (
        destination_region == first_source_region
    ):
      return True
    print(
        self._NOTE,
        '\n' + self._SYNC_FLAG_ENABLED_WARNING
        if FLAGS.sync
        else '\n' + self._CROSS_REGION_WARNING,
    )
    if self.force:
      return True
    if 'y' != _PromptYN(self._CONFIRM_CROSS_REGION % (source_references_str,)):
      print(self._NOT_COPYING % (source_references_str,))
      return False
    return True

  def RunWithArgs(self, source_tables, dest_table):
    """Copies one table to another.

    Examples:
      bq cp dataset.old_table dataset2.new_table
      bq cp --destination_kms_key=kms_key dataset.old_table dataset2.new_table
    """
    client = Client.Get()
    source_references = [
        client.GetTableReference(src) for src in source_tables.split(',')
    ]
    source_references_str = ', '.join(str(src) for src in source_references)
    dest_reference = client.GetTableReference(dest_table)

    if self.append_table:
      write_disposition = 'WRITE_APPEND'
      ignore_already_exists = True
    elif self.no_clobber:
      write_disposition = 'WRITE_EMPTY'
      ignore_already_exists = True
    else:
      write_disposition = 'WRITE_TRUNCATE'
      ignore_already_exists = False

    # Check if destination table exists, confirm overwrite
    destination_region = None
    if not ignore_already_exists and not self.force:
      destination_region = client.GetTableRegion(dest_reference)
      if destination_region and 'y' != _PromptYN(
          self._CONFIRM_OVERWRITE % (dest_reference)
      ):
        print(self._NOT_COPYING % (source_references_str,))
        return 0

    if not self.shouldContinueAfterCrossRegionCheck(
        client,
        source_references,
        source_references_str,
        dest_reference,
        destination_region,
    ):
      return 0

    operation = 'copied'
    if self.snapshot:
      operation_type = 'SNAPSHOT'
      operation = 'snapshotted'
    elif self.restore:
      operation_type = 'RESTORE'
      operation = 'restored'
    elif self.clone:
      operation_type = 'CLONE'
      operation = 'cloned'
    else:
      operation_type = 'COPY'
    kwds = {
        'write_disposition': write_disposition,
        'ignore_already_exists': ignore_already_exists,
        'job_id': _GetJobIdFromFlags(),
        'operation_type': operation_type,
    }
    if FLAGS.location:
      kwds['location'] = FLAGS.location

    if self.destination_kms_key:
      kwds['encryption_configuration'] = {
          'kmsKeyName': self.destination_kms_key
      }
    if self.expiration:
      datetime_utc = datetime.datetime.utcfromtimestamp(
          int(self.expiration + time.time()))
      kwds['destination_expiration_time'] = _FormatRfc3339(datetime_utc)
    job = client.CopyTable(source_references, dest_reference, **kwds)
    if job is None:
      print("Table '%s' already exists, skipping" % (dest_reference,))
    elif not FLAGS.sync:
      self.PrintJobStartInfo(job)
    else:
      plurality = 's' if len(source_references) > 1 else ''
      print("Table%s '%s' successfully %s to '%s'" %
            (plurality, source_references_str, operation, dest_reference))
      # If we are here, the job succeeded, but print warnings if any.
      _PrintJobMessages(client.FormatJobInfo(job))






def _ParseTimePartitioning(partitioning_type=None,
                           partitioning_expiration=None,
                           partitioning_field=None,
                           partitioning_minimum_partition_date=None,
                           partitioning_require_partition_filter=None):
  """Parses time partitioning from the arguments.

  Args:
    partitioning_type: type for the time partitioning. Supported types are HOUR,
      DAY, MONTH, and YEAR. The default value is DAY when other arguments are
      specified, which generates one partition per day.
    partitioning_expiration: number of seconds to keep the storage for a
      partition. A negative value clears this setting.
    partitioning_field: if not set, the table is partitioned based on the
      loading time; if set, the table is partitioned based on the value of this
      field.
    partitioning_minimum_partition_date: lower boundary of partition date for
      field based partitioning table.
    partitioning_require_partition_filter: if true, queries on the table must
      have a partition filter so not all partitions are scanned.

  Returns:
    Time partitioning if any of the arguments is not None, otherwise None.

  Raises:
    UsageError: when failed to parse.
  """

  time_partitioning = {}
  key_type = 'type'
  key_expiration = 'expirationMs'
  key_field = 'field'
  key_minimum_partition_date = 'minimumPartitionDate'
  key_require_partition_filter = 'requirePartitionFilter'
  if partitioning_type is not None:
    time_partitioning[key_type] = partitioning_type
  if partitioning_expiration is not None:
    time_partitioning[key_expiration] = partitioning_expiration * 1000
  if partitioning_field is not None:
    time_partitioning[key_field] = partitioning_field
  if partitioning_minimum_partition_date is not None:
    if partitioning_field is not None:
      time_partitioning[
          key_minimum_partition_date] = partitioning_minimum_partition_date
    else:
      raise app.UsageError('Need to specify --time_partitioning_field for '
                           '--time_partitioning_minimum_partition_date.')
  if partitioning_require_partition_filter is not None:
    if time_partitioning:
      time_partitioning[
          key_require_partition_filter] = partitioning_require_partition_filter

  if time_partitioning:
    if key_type not in time_partitioning:
      time_partitioning[key_type] = 'DAY'
    if (key_expiration in time_partitioning and
        time_partitioning[key_expiration] <= 0):
      time_partitioning[key_expiration] = None
    return time_partitioning
  else:
    return None


def _ParseFileSetSpecType(file_set_spec_type=None):
  """Parses the file set specification type from the arguments.

  Args:
    file_set_spec_type: specifies how to discover files given source URIs.

  Returns:
    file set specification type.
  Raises:
    UsageError: when an illegal value is passed.
  """
  if file_set_spec_type is None:
    return None
  valid_spec_types = ['FILE_SYSTEM_MATCH', 'NEW_LINE_DELIMITED_MANIFEST']
  if file_set_spec_type not in valid_spec_types:
    raise app.UsageError(
        'Error parsing file_set_spec_type, only FILE_SYSTEM_MATCH, '
        'NEW_LINE_DELIMITED_MANIFEST or no value are accepted')
  return 'FILE_SET_SPEC_TYPE_' + file_set_spec_type


def _ParseClustering(clustering_fields=None):
  """Parses clustering from the arguments.

  Args:
    clustering_fields: Comma-separated field names.

  Returns:
    Clustering if any of the arguments is not None, otherwise None. Special
    case if clustering_fields is passed in as an empty string instead of None,
    in which case we'll return {}, to support the scenario where user wants to
    update a table and remove the clustering spec.
  """

  if clustering_fields == '':  # pylint: disable=g-explicit-bool-comparison
    return {}
  elif clustering_fields is not None:
    return {'fields': clustering_fields.split(',')}
  else:
    return None


def _ParseNumericTypeConversionMode(numeric_type_conversion_mode=None):
  """Parses the numeric type conversion mode from the arguments.

  Args:
    numeric_type_conversion_mode: specifies how the numeric values are handled
      when the value is out of scale.
  Return: Conversion mode.

  Raises:
    UsageError: when an illegal value is passed.
  """

  if numeric_type_conversion_mode is None:
    return None
  elif numeric_type_conversion_mode == 'ROUND':
    return 'NUMERIC_TYPE_VALUE_ROUND'
  else:
    raise app.UsageError(
        'Error parsing numeric_type_conversion_mode, only ROUND or no value '
        'are accepted')


def _ParseRangePartitioning(range_partitioning_spec=None):
  """Parses range partitioning from the arguments.

  Args:
    range_partitioning_spec: specification for range partitioning in the format
      of field,start,end,interval.

  Returns:
    Range partitioning if range_partitioning_spec is not None, otherwise None.
  Raises:
    UsageError: when the spec fails to parse.
  """

  range_partitioning = {}
  key_field = 'field'
  key_range = 'range'
  key_range_start = 'start'
  key_range_end = 'end'
  key_range_interval = 'interval'

  if range_partitioning_spec is not None:
    parts = range_partitioning_spec.split(',')
    if len(parts) != 4:
      raise app.UsageError(
          'Error parsing range_partitioning. range_partitioning should be in '
          'the format of "field,start,end,interval"')
    range_partitioning[key_field] = parts[0]
    range_spec = {}
    range_spec[key_range_start] = parts[1]
    range_spec[key_range_end] = parts[2]
    range_spec[key_range_interval] = parts[3]
    range_partitioning[key_range] = range_spec

  if range_partitioning:
    return range_partitioning
  else:
    return None


class _Make(BigqueryCmd):
  """Creates a dataset or a table."""
  usage = """mk [-d] <identifier>  OR  mk [-t] <identifier> [<schema>]"""

  def __init__(self, name, fv):
    super(_Make, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'force',
        False,
        'Ignore errors reporting that the object already exists.',
        short_name='f',
        flag_values=fv)
    flags.DEFINE_boolean(
        'dataset',
        False,
        'Create dataset with this name.',
        short_name='d',
        flag_values=fv)
    flags.DEFINE_boolean(
        'table',
        False,
        'Create table with this name.',
        short_name='t',
        flag_values=fv)
    flags.DEFINE_boolean(
        'transfer_config', None, 'Create transfer config.', flag_values=fv)
    flags.DEFINE_string(
        'target_dataset',
        '',
        'Target dataset for the created transfer configuration.',
        flag_values=fv)
    flags.DEFINE_string(
        'display_name',
        '',
        'Display name for the created transfer configuration or connection.',
        flag_values=fv)
    flags.DEFINE_string(
        'data_source',
        '',
        'Data source for the created transfer configuration.',
        flag_values=fv)
    flags.DEFINE_integer(
        'refresh_window_days',
        0,
        'Refresh window days for the created transfer configuration.',
        flag_values=fv)
    flags.DEFINE_string(
        'params',
        None,
        'Parameters for the created transfer configuration in JSON format. '
        'For example: --params=\'{\"param\":\"param_value\"}\'',
        short_name='p',
        flag_values=fv)
    flags.DEFINE_string(
        'service_account_name',
        '',
        'Service account used as the credential on the transfer config.',
        flag_values=fv)
    flags.DEFINE_string(
        'notification_pubsub_topic',
        '',
        'Pub/Sub topic used for notification after transfer run completed or '
        'failed.',
        flag_values=fv)
    flags.DEFINE_bool(
        'transfer_run',
        False,
        'Creates transfer runs for a time range.',
        flag_values=fv)
    flags.DEFINE_string(
        'start_time',
        None, 'Start time of the range of transfer runs. '
        'The format for the time stamp is RFC3339 UTC "Zulu". '
        'Example: 2019-01-20T06:50:0Z. Read more: '
        'https://developers.google.com/protocol-buffers/docs/'
        'reference/google.protobuf#google.protobuf.Timestamp ',
        flag_values=fv)
    flags.DEFINE_string(
        'end_time',
        None, 'Exclusive end time of the range of transfer runs. '
        'The format for the time stamp is RFC3339 UTC "Zulu". '
        'Example: 2019-01-20T06:50:0Z. Read more: '
        'https://developers.google.com/protocol-buffers/docs/'
        'reference/google.protobuf#google.protobuf.Timestamp ',
        flag_values=fv)
    flags.DEFINE_string(
        'run_time',
        None, 'Specific time for a transfer run. '
        'The format for the time stamp is RFC3339 UTC "Zulu". '
        'Example: 2019-01-20T06:50:0Z. Read more: '
        'https://developers.google.com/protocol-buffers/docs/'
        'reference/google.protobuf#google.protobuf.Timestamp ',
        flag_values=fv)
    flags.DEFINE_string(
        'schedule_start_time',
        None, 'Time to start scheduling transfer runs for the given '
        'transfer configuration. If empty, the default value for '
        'the start time will be used to start runs immediately.'
        'The format for the time stamp is RFC3339 UTC "Zulu". '
        'Read more: '
        'https://developers.google.com/protocol-buffers/docs/'
        'reference/google.protobuf#google.protobuf.Timestamp',
        flag_values=fv)
    flags.DEFINE_string(
        'schedule_end_time',
        None, 'Time to stop scheduling transfer runs for the given '
        'transfer configuration. If empty, the default value for '
        'the end time will be used to schedule runs indefinitely.'
        'The format for the time stamp is RFC3339 UTC "Zulu". '
        'Read more: '
        'https://developers.google.com/protocol-buffers/docs/'
        'reference/google.protobuf#google.protobuf.Timestamp',
        flag_values=fv)
    flags.DEFINE_string(
        'schedule',
        None,
        'Data transfer schedule. If the data source does not support a custom '
        'schedule, this should be empty. If empty, the default '
        'value for the data source will be used. The specified times are in '
        'UTC. Examples of valid format: 1st,3rd monday of month 15:30, '
        'every wed,fri of jan,jun 13:15, and first sunday of quarter 00:00. '
        'See more explanation about the format here: '
        'https://cloud.google.com/appengine/docs/flexible/python/scheduling-jobs-with-cron-yaml#the_schedule_format',  # pylint: disable=line-too-long
        flag_values=fv)
    flags.DEFINE_bool(
        'no_auto_scheduling',
        False, 'Disables automatic scheduling of data transfer runs for this '
        'configuration.',
        flag_values=fv)
    flags.DEFINE_string(
        'schema',
        '', 'Either a filename or a comma-separated list of fields in the form '
        'name[:type].',
        flag_values=fv)
    flags.DEFINE_string(
        'description',
        None,
        'Description of the dataset, table or connection.',
        flag_values=fv)
    flags.DEFINE_string(
        'data_location',
        None, 'Geographic location of the data. See details at '
        'https://cloud.google.com/bigquery/docs/locations.',
        flag_values=fv)
    flags.DEFINE_integer(
        'expiration',
        None,
        'Expiration time, in seconds from now, of a table.',
        flag_values=fv)
    flags.DEFINE_integer(
        'default_table_expiration',
        None, 'Default lifetime, in seconds, for newly-created tables in a '
        'dataset. Newly-created tables will have an expiration time of '
        'the current time plus this value.',
        flag_values=fv)
    flags.DEFINE_integer(
        'default_partition_expiration',
        None,
        'Default partition expiration for all partitioned tables in the dataset'
        ', in seconds. The storage in a partition will have an expiration time '
        'of its partition time plus this value. If this property is set, '
        'partitioned tables created in the dataset will use this instead of '
        'default_table_expiration.',
        flag_values=fv)
    flags.DEFINE_string(
        'external_table_definition',
        None,
        'Specifies a table definition to use to create an external table. '
        'The value can be either an inline table definition or a path to a '
        'file containing a JSON table definition. '
        'The format of inline definition is "schema@format=uri@connection", '
        'where "schema@", "format=", and "connection" are optional and "format"'
        'has the default value of "CSV" if not specified. ',
        flag_values=fv)
    flags.DEFINE_string(
        'connection_id',
        None,
        'The connection specifying the credentials to be used to read external '
        'storage. The connection_id can have the form '
        '"<project_id>.<location_id>.<connection_id>" or '
        '"projects/<project_id>/locations/<location_id>/connections/<connection_id>". ',
        flag_values=fv)
    flags.DEFINE_string(
        'storage_uri',
        None,
        (
            'The fully qualified location prefix of the external folder where'
            ' the table data of a BigLake table is stored. The "*" wildcard'
            ' character is not allowed. The URI should be in the format'
            ' "gs://bucket/path_to_table/". '
        ),
        flag_values=fv,
    )
    flags.DEFINE_enum(
        'file_format',
        None, ['PARQUET'],
        'The file format the table data of a BigLake table is stored in. ',
        flag_values=fv)
    flags.DEFINE_enum(
        'table_format',
        None,
        ['ICEBERG'],
        (
            'The table format the metadata only snapshots of a BigLake table'
            ' are stored in. '
        ),
        flag_values=fv,
    )
    flags.DEFINE_string(
        'view', '', 'Create view with this SQL query.', flag_values=fv)
    flags.DEFINE_multi_string(
        'view_udf_resource',
        None, 'The URI or local filesystem path of a code file to load and '
        'evaluate immediately as a User-Defined Function resource used '
        'by the view.',
        flag_values=fv)
    flags.DEFINE_string(
        'materialized_view',
        None,
        '[Experimental] Create materialized view with this Standard SQL query.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'enable_refresh',
        None,
        'Whether to enable automatic refresh of the materialized views when '
        'the base table is updated. If not set, the default is true.',
        flag_values=fv)
    flags.DEFINE_integer(
        'refresh_interval_ms',
        None,
        'Milliseconds that must have elapsed since last refresh until the '
        'materialized view can be automatically refreshed again. If not set, '
        'the default value is "1800000" (30 minutes).',
        flag_values=fv)
    flags.DEFINE_string(
        'max_staleness',
        None,
        'INTERVAL value that determines the maximum staleness allowed when '
        'querying a materialized view or an external table. By default no '
        'staleness is allowed. Examples of valid max_staleness values: '
        '1 day: "0-0 1 0:0:0"; 1 hour: "0-0 0 1:0:0".'
        'See more explanation about the INTERVAL values: '
        'https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types#interval_type',  # pylint: disable=line-too-long
        flag_values=fv)
    flags.DEFINE_boolean(
        'use_legacy_sql',
        None,
        ('The choice of using Legacy SQL for the query is optional. If not '
         'specified, the server will automatically determine the dialect based '
         'on query information, such as dialect prefixes. If no prefixes are '
         'found, it will default to Legacy SQL.'),
        flag_values=fv)
    flags.DEFINE_string(
        'time_partitioning_type',
        None,
        'Enables time based partitioning on the table and set the type. The '
        'default value is DAY, which will generate one partition per day. '
        'Other supported values are HOUR, MONTH, and YEAR.',
        flag_values=fv)
    flags.DEFINE_integer(
        'time_partitioning_expiration',
        None,
        'Enables time based partitioning on the table and sets the number of '
        'seconds for which to keep the storage for the partitions in the table.'
        ' The storage in a partition will have an expiration time of its '
        'partition time plus this value.',
        flag_values=fv)
    flags.DEFINE_string(
        'time_partitioning_field',
        None,
        'Enables time based partitioning on the table and the table will be '
        'partitioned based on the value of this field. If time based '
        'partitioning is enabled without this value, the table will be '
        'partitioned based on the loading time.',
        flag_values=fv)
    flags.DEFINE_string(
        'destination_kms_key',
        None,
        'Cloud KMS key for encryption of the destination table data.',
        flag_values=fv)
    flags.DEFINE_multi_string(
        'label',
        None,
        'A label to set on the table or dataset. The format is "key:value"',
        flag_values=fv)
    flags.DEFINE_boolean(
        'require_partition_filter',
        None,
        'Whether to require partition filter for queries over this table. '
        'Only apply to partitioned table.',
        flag_values=fv)
    flags.DEFINE_string(
        'clustering_fields',
        None,
        'Comma-separated list of field names that specifies the columns on '
        'which a table is clustered.',
        flag_values=fv)
    flags.DEFINE_string(
        'range_partitioning',
        None, 'Enables range partitioning on the table. The format should be '
        '"field,start,end,interval". The table will be partitioned based on the'
        ' value of the field. Field must be a top-level, non-repeated INT64 '
        'field. Start, end, and interval are INT64 values defining the ranges.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'reservation',
        None,
        'Creates a reservation described by this identifier. ',
        flag_values=fv)
    flags.DEFINE_boolean(
        'capacity_commitment',
        None,
        'Creates a capacity commitment. You do not need to specify a capacity '
        'commitment id, this will be assigned automatically.',
        flag_values=fv)
    flags.DEFINE_enum(
        'plan',
        None,
        [
            'FLEX',
            'MONTHLY',
            'ANNUAL',
            'THREE_YEAR',
        ],
        'Commitment plan for this capacity commitment. Plans cannot be deleted '
        'before their commitment period is over. Options include:'
        '\n FLEX'
        '\n MONTHLY'
        '\n ANNUAL'
        '\n THREE_YEAR',
        flag_values=fv)
    flags.DEFINE_enum(
        'renewal_plan',
        None,
        [
            'FLEX',
            'MONTHLY',
            'ANNUAL',
            'THREE_YEAR',
            'NONE',
        ],
        'The plan this capacity commitment is converted to after committed '
        'period ends. Options include:'
        '\n NONE'
        '\n FLEX'
        '\n MONTHLY'
        '\n ANNUAL'
        '\n THREE_YEAR'
        '\n NONE can only be used in conjunction with --edition, '
        '\n while FLEX and MONTHLY cannot be used together with --edition.',
        flag_values=fv)
    flags.DEFINE_integer(
        'slots',
        0,
        'The number of baseline slots associated with the reservation.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'multi_region_auxiliary',
        False, 'If true, capacity commitment or reservation is placed in the '
        'organization'
        's auxiliary region which is designated for disaster '
        'recovery purposes. Applicable only for US and EU locations. Available '
        'only for allow-listed projects.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'use_idle_slots',
        True,
        'If true, any query running in this reservation will be able to use '
        'idle slots from other reservations. Used if ignore_idle_slots is '
        'None.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'ignore_idle_slots',
        None,
        'If false, any query running in this reservation will be able to use '
        'idle slots from other reservations.',
        flag_values=fv)
    flags.DEFINE_integer(
        'max_concurrency',
        None,
        'Deprecated, please use target_job_concurrency instead.',
        flag_values=fv)
    flags.DEFINE_integer(
        'concurrency',
        None,
        'Deprecated, please use target_job_concurrency instead.',
        flag_values=fv)
    flags.DEFINE_integer(
        'target_job_concurrency',
        None,
        'Sets a soft upper bound on the number of jobs that can run '
        'concurrently in the reservation. Default value is 0 which means that '
        'concurrency target will be automatically computed by the system.',
        flag_values=fv)
    flags.DEFINE_bool(
        'enable_queuing_and_priorities',
        None,
        'Whether to enable queuing and new job prioritization behavior for the '
        'reservation. Reservation must be whitelisted in order to set this '
        'flag.',
        flag_values=fv)
    flags.DEFINE_integer(
        'autoscale_max_slots',
        None,
        'Number of slots to be scaled when needed. Autoscale will be enabled '
        'when setting this.',
        flag_values=fv)
    flags.DEFINE_enum(
        'job_type',
        None,
        [
            'QUERY',
            'PIPELINE',
            'ML_EXTERNAL',
            'BACKGROUND',
            'SPARK',
            'CONTINUOUS',
        ],
        (
            'Type of jobs to create reservation assignment for. Options'
            ' include:\n QUERY\n PIPELINE\n Note if PIPELINE reservations are'
            ' created, then load jobs will just use the slots from this'
            " reservation and slots from shared pool won't be used.\n"
            ' ML_EXTERNAL\n BigQuery ML jobs that use services external to BQ'
            ' for model training will use slots from this reservation. Slots'
            ' used by these jobs are not preemptible, i.e., they are not'
            ' available for other jobs running in the reservation. These jobs'
            ' will not utilize idle slots from other reservations.\n'
            ' BACKGROUND\n BigQuery CDC background merge will use BACKGROUND'
            ' reservations to execute if created.\n SPARK\n BigQuery Spark jobs'
            ' that use services external to BQ for executing SPARK procedure'
            ' job. Slots used by these jobs are not preemptible, i.e., they are'
            ' not available for other jobs running in the reservation. These'
            ' jobs will not utilize idle slots from other reservations.'
        ),
        flag_values=fv,
    )
    flags.DEFINE_enum(
        'priority',
        None, [
            'HIGH',
            'INTERACTIVE',
            'BATCH',
        ], 'Reservation assignment default job priority. Only available for '
        'whitelisted reservations. Options include:'
        '\n HIGH'
        '\n INTERACTIVE'
        '\n BATCH',
        flag_values=fv)
    flags.DEFINE_string(
        'reservation_id',
        None, 'Reservation ID used to create reservation assignment for. '
        'Used in conjunction with --reservation_assignment.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'reservation_assignment',
        None,
        'Create a reservation assignment.',
        flag_values=fv)
    flags.DEFINE_enum(
        'assignee_type',
        None, ['PROJECT', 'FOLDER', 'ORGANIZATION'],
        'Type of assignees for the reservation assignment. Options include:'
        '\n PROJECT'
        '\n FOLDER'
        '\n ORGANIZATION'
        '\n Used in conjunction with --reservation_assignment.',
        flag_values=fv)
    flags.DEFINE_string(
        'assignee_id',
        None,
        'Project/folder/organization ID, to which the reservation is assigned. '
        'Used in conjunction with --reservation_assignment.',
        flag_values=fv)
    flags.DEFINE_enum(
        'edition',
        None, ['STANDARD', 'ENTERPRISE', 'ENTERPRISE_PLUS'],
        'Type of editions for the reservation or capacity commitment. '
        'Options include:'
        '\n STANDARD'
        '\n ENTERPRISE'
        '\n ENTERPRISE_PLUS'
        '\n Used in conjunction with --reservation or --capacity_commitment.'
        '\n STANDARD cannot be used together with --capacity_commitment.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'connection', None, 'Create a connection.', flag_values=fv)
    flags.DEFINE_enum(
        'connection_type',
        None,
        bigquery_client.CONNECTION_TYPES,
        'Connection type. Valid values:\n ' + \
        '\n '.join(bigquery_client.CONNECTION_TYPES),
        flag_values=fv)
    flags.DEFINE_string(
        'properties',
        None,
        'Connection properties in JSON format.',
        flag_values=fv)
    flags.DEFINE_string(
        'connection_credential',
        None,
        'Connection credential in JSON format.',
        flag_values=fv)
    flags.DEFINE_string(
        'iam_role_id', None, '[Experimental] IAM role id.', flag_values=fv)
    # TODO(b/231712311): look into cleaning up this flag now that only federated
    # aws connections are supported.
    flags.DEFINE_boolean(
        'federated_aws',
        True,
        '[Experimental] Federated identity.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'federated_azure',
        None,
        '[Experimental] Federated identity for Azure.',
        flag_values=fv)
    flags.DEFINE_string(
        'tenant_id', None, '[Experimental] Tenant id.', flag_values=fv)
    flags.DEFINE_string(
        'federated_app_client_id',
        None,
        '[Experimental] The application (client) id of the Active Directory '
        'application to use with Azure federated identity.',
        flag_values=fv)
    flags.DEFINE_string(
        'default_kms_key',
        None,
        'Defines default KMS key name for all newly objects created in the '
        'dataset. Table/Model creation request can override this default.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'use_avro_logical_types',
        True, 'If sourceFormat is set to "AVRO", indicates whether to enable '
        'interpreting logical types into their corresponding types '
        '(ie. TIMESTAMP), instead of only using their raw types (ie. INTEGER).',
        flag_values=fv)
    flags.DEFINE_string(
        'source_dataset',
        None,
        'When set to a dataset reference, creates a Linked Dataset pointing to '
        'the source dataset.',
        flag_values=fv)
    flags.DEFINE_string(
        'external_source',
        None,
        (
            'External source that backs this dataset. Currently only AWS Glue'
            ' databases are supported (format'
            ' aws-glue://<AWS_ARN_OF_GLUE_DATABASE>)'
        ),
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'parquet_enum_as_string',
        False, 'Infer Parquet ENUM logical type as STRING '
        '(instead of BYTES by default).',
        flag_values=fv)
    flags.DEFINE_boolean(
        'parquet_enable_list_inference',
        False,
        _PARQUET_LIST_INFERENCE_DESCRIPTION,
        flag_values=fv)
    flags.DEFINE_integer(
        'max_time_travel_hours',
        None,
        'Optional. Define the max time travel in hours. The value can be from '
        '48 to 168 hours (2 to 7 days). The default value is 168 hours if this '
        'is not set.',
        flag_values=fv)
    flags.DEFINE_enum(
        'storage_billing_model',
        None, ['LOGICAL', 'PHYSICAL'],
        'Optional. Sets the storage billing model for the dataset. \n'
        'LOGICAL - switches to logical billing model \n'
        'PHYSICAL - switches to physical billing model.',
        flag_values=fv)
    flags.DEFINE_enum(
        'metadata_cache_mode',
        None, ['AUTOMATIC', 'MANUAL'],
        'Enables metadata cache for an external table with a connection. '
        'Specify AUTOMATIC to automatically refresh the cached metadata. '
        'Specify MANUAL to stop the automatic refresh.',
        flag_values=fv)
    flags.DEFINE_enum(
        'object_metadata',
        None, ['DIRECTORY', 'SIMPLE'],
        'Object Metadata Type used to create Object Tables. SIMPLE is the '
        'only supported value to create an Object Table containing a directory '
        'listing of objects found at the uri in external_data_definition.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'preserve_ascii_control_characters',
        False,
        'Whether to preserve embedded Ascii Control characters in CSV External table ',
        flag_values=fv)
    flags.DEFINE_string(
        'reference_file_schema_uri',
        None, 'provide a reference file with the table schema, currently '
        'enabled for the formats: AVRO, PARQUET, ORC.',
        flag_values=fv)
    flags.DEFINE_enum(
        'file_set_spec_type',
        None, ['FILE_SYSTEM_MATCH', 'NEW_LINE_DELIMITED_MANIFEST'],
        '[Experimental] Specifies how to discover files given source URIs. '
        'Options include: '
        '\n FILE_SYSTEM_MATCH: expand source URIs by listing files from the '
        'underlying object store. This is the default behavior.'
        '\n NEW_LINE_DELIMITED_MANIFEST: indicate the source URIs provided are '
        'new line delimited manifest files, where each line contains a URI '
        'with no wild-card.',
        flag_values=fv)
    flags.DEFINE_string(
        'kms_key_name',
        None,
        'Cloud KMS key name used for encryption.',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'add_tags',
        None,
        'Tags to attach to the table. The format is namespaced key:value pair '
        'like "1234567/my_tag_key:my_tag_value,test-project123/environment:production"',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier='', schema=''):
    # pylint: disable=g-doc-exception
    """Create a dataset, table, view, or transfer configuration with this name.

    See 'bq help load' for more information on specifying the schema.

    Examples:
      bq mk new_dataset
      bq mk new_dataset.new_table
      bq --dataset_id=new_dataset mk table
      bq mk -t new_dataset.newtable name:integer,value:string
      bq mk --view='select 1 as num' new_dataset.newview
         (--view_udf_resource=path/to/file.js)
      bq mk --materialized_view='select sum(x) as sum_x from dataset.table'
          new_dataset.newview
      bq mk -d --data_location=EU new_dataset
      bq mk -d --source_dataset=src_dataset new_dataset (requires allowlisting)
      bq mk -d
        --external_source=aws-glue://<aws_arn_of_glue_database>
        --connection_id=<connection>
        new_dataset
      bq mk --transfer_config --target_dataset=dataset --display_name=name
          -p='{"param":"value"}' --data_source=source
          --schedule_start_time={schedule_start_time}
          --schedule_end_time={schedule_end_time}
      bq mk --transfer_run --start_time={start_time} --end_time={end_time}
          projects/p/locations/l/transferConfigs/c
      bq mk --transfer_run --run_time={run_time}
          projects/p/locations/l/transferConfigs/c
      bq mk --reservation --project_id=project --location=us reservation_name
      bq mk --reservation_assignment --reservation_id=project:us.dev
          --job_type=QUERY --assignee_type=PROJECT --assignee_id=myproject
      bq mk --reservation_assignment --reservation_id=project:us.dev
          --job_type=QUERY --assignee_type=FOLDER --assignee_id=123
      bq mk --reservation_assignment --reservation_id=project:us.dev
          --job_type=QUERY --assignee_type=ORGANIZATION --assignee_id=456
      bq mk --connection --connection_type='CLOUD_SQL'
        --properties='{"instanceId" : "instance",
        "database" : "db", "type" : "MYSQL" }'
        --connection_credential='{"username":"u", "password":"p"}'
        --project_id=proj --location=us --display_name=name new_connection
    """

    client = Client.Get()

    if self.d and self.t:
      raise app.UsageError('Cannot specify both -d and -t.')
    if ValidateAtMostOneSelected(self.schema, self.view,
                                 self.materialized_view):
      raise app.UsageError('Cannot specify more than one of'
                           ' --schema or --view or --materialized_view.')
    if self.t:
      reference = client.GetTableReference(identifier)
    elif self.view:
      reference = client.GetTableReference(identifier)
    elif self.materialized_view:
      reference = client.GetTableReference(identifier)
    elif self.reservation:
      object_info = None
      reference = client.GetReservationReference(
          identifier=identifier, default_location=FLAGS.location)
      try:
        ignore_idle_arg = self.ignore_idle_slots
        if ignore_idle_arg is None:
          ignore_idle_arg = not self.use_idle_slots
        concurrency = self.target_job_concurrency
        if concurrency is None:
          concurrency = (
              self.concurrency
              if self.concurrency is not None else self.max_concurrency)
        object_info = client.CreateReservation(
            reference=reference,
            slots=self.slots,
            ignore_idle_slots=ignore_idle_arg,
            edition=self.edition,
            target_job_concurrency=concurrency,
            enable_queuing_and_priorities=self.enable_queuing_and_priorities,
            multi_region_auxiliary=self.multi_region_auxiliary,
            autoscale_max_slots=self.autoscale_max_slots,
        )
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to create reservation '%s': %s" % (identifier, e))
      if object_info is not None:
        _PrintObjectInfo(object_info, reference, custom_format='show')
    elif self.capacity_commitment:
      reference = client.GetCapacityCommitmentReference(
          identifier=identifier,
          default_location=FLAGS.location,
          default_capacity_commitment_id=' ')
      try:
        object_info = client.CreateCapacityCommitment(
            reference,
            self.edition,
            self.slots,
            self.plan,
            self.renewal_plan,
            self.multi_region_auxiliary,
        )
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to create capacity commitment in '%s': %s" %
            (identifier, e))
      if object_info is not None:
        _PrintObjectInfo(object_info, reference, custom_format='show')
    elif self.reservation_assignment:
      try:
        reference = client.GetReservationReference(
            default_location=FLAGS.location, identifier=self.reservation_id)
        object_info = client.CreateReservationAssignment(
            reference=reference,
            job_type=self.job_type,
            priority=self.priority,
            assignee_type=self.assignee_type,
            assignee_id=self.assignee_id)
        reference = client.GetReservationAssignmentReference(
            path=object_info['name'])
        _PrintObjectInfo(object_info, reference, custom_format='show')
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to create reservation assignment '%s': %s" %
            (identifier, e))
    elif self.transfer_config:
      transfer_client = client.GetTransferV1ApiClient()
      reference = 'projects/' + (client.GetProjectReference().projectId)
      credentials = False
      if self.data_source:
        credentials = CheckValidCreds(reference, self.data_source,
                                      transfer_client)
      else:
        raise bq_error.BigqueryError('A data source must be provided.')
      auth_info = {}
      if (not credentials and self.data_source != 'loadtesting' and
          not self.service_account_name):
        auth_info = RetrieveAuthorizationInfo(reference, self.data_source,
                                              transfer_client)
      location = self.data_location or FLAGS.location
      schedule_args = bigquery_client.TransferScheduleArgs(
          schedule=self.schedule,
          start_time=self.schedule_start_time,
          end_time=self.schedule_end_time,
          disable_auto_scheduling=self.no_auto_scheduling)
      transfer_name = client.CreateTransferConfig(
          reference=reference,
          data_source=self.data_source,
          target_dataset=self.target_dataset,
          display_name=self.display_name,
          refresh_window_days=self.refresh_window_days,
          params=self.params,
          auth_info=auth_info,
          service_account_name=self.service_account_name,
          destination_kms_key=self.destination_kms_key,
          notification_pubsub_topic=self.notification_pubsub_topic,
          schedule_args=schedule_args,
          location=location)
      print(('Transfer configuration \'%s\' successfully created.' %
             transfer_name))
    elif self.transfer_run:
      formatter = _GetFormatterFromFlags()
      formatted_identifier = _FormatDataTransferIdentifiers(client, identifier)
      reference = TransferConfigReference(
          transferConfigName=formatted_identifier)
      incompatible_options = (self.start_time or self.end_time) \
                              and self.run_time
      incomplete_options = (not self.start_time or not self.end_time) \
                            and not self.run_time
      if incompatible_options or incomplete_options:
        raise app.UsageError(
            'Need to specify either both --start_time and --end_time '
            'or only --run_time.')
      results = list(
          map(
              client.FormatTransferRunInfo,
              client.StartManualTransferRuns(
                  reference=reference,
                  start_time=self.start_time,
                  end_time=self.end_time,
                  run_time=self.run_time)))
      BigqueryClient.ConfigureFormatter(
          formatter,
          TransferRunReference,
          print_format='make',
          object_info=results[0])
      for result in results:
        formatter.AddDict(result)
      formatter.Print()
    elif self.connection:
      # Create a new connection.
      connection_type_defined = self.connection_type
      if not connection_type_defined:
        error = 'Need to specify --connection_type'
        raise app.UsageError(error)

      if self.connection_type == 'AWS' and self.iam_role_id:
        self.properties = bigquery_client.MakeAccessRolePropertiesJson(
            self.iam_role_id)
        if not self.federated_aws:
          raise app.UsageError('Non-federated AWS connections are deprecated.')
      if self.connection_type == 'Azure' and self.tenant_id:
        if self.federated_azure:
          if not self.federated_app_client_id:
            raise app.UsageError(
                'Must specify --federated_app_client_id for federated Azure connections.'
            )
          self.properties = bigquery_client.MakeAzureFederatedAppClientAndTenantIdPropertiesJson(
              self.tenant_id, self.federated_app_client_id)
        else:
          self.properties = bigquery_client.MakeTenantIdPropertiesJson(
              self.tenant_id)

      param_properties = self.properties
      # All connection types require properties, except CLOUD_RESOURCE as
      # it serves as a container for a service account that is generated
      # by the connection service.
      if not param_properties and self.connection_type == 'CLOUD_RESOURCE':
        param_properties = '{}'
      # SPARK connections does not require properties since all the fields in
      # the properties are optional.
      if not param_properties and self.connection_type == 'SPARK':
        param_properties = '{}'
      properties_defined = param_properties
      if not properties_defined:
        error = 'Need to specify --properties'
        raise app.UsageError(error)
      created_connection = client.CreateConnection(
          project_id=FLAGS.project_id,
          location=FLAGS.location,
          connection_type=self.connection_type,
          properties=param_properties,
          connection_credential=self.connection_credential,
          display_name=self.display_name,
          description=self.description,
          connection_id=identifier,
          kms_key_name=self.kms_key_name,
      )
      if created_connection:
        reference = client.GetConnectionReference(
            path=created_connection['name'])
        print('Connection %s successfully created' % reference)
        bigquery_client.MaybePrintManualInstructionsForConnection(
            created_connection, flag_format=FLAGS.format)
    elif self.d or not identifier:
      reference = client.GetDatasetReference(identifier)
      if reference.datasetId and identifier:
        ValidateDatasetName(reference.datasetId)
    else:
      reference = client.GetReference(identifier)
      _Typecheck(reference, (DatasetReference, TableReference),
                 "Invalid identifier '%s' for mk." % (identifier,))
    if isinstance(reference, DatasetReference):
      if self.schema:
        raise app.UsageError('Cannot specify schema with a dataset.')
      if self.expiration:
        raise app.UsageError('Cannot specify an expiration for a dataset.')
      if self.external_table_definition is not None:
        raise app.UsageError(
            'Cannot specify an external_table_definition for a dataset.')
      if client.DatasetExists(reference):
        message = "Dataset '%s' already exists." % (reference,)
        if not self.f:
          raise bq_error.BigqueryError(message)
        else:
          print(message)
          return
      default_table_exp_ms = None
      if self.default_table_expiration is not None:
        default_table_exp_ms = self.default_table_expiration * 1000
      default_partition_exp_ms = None
      if self.default_partition_expiration is not None:
        default_partition_exp_ms = self.default_partition_expiration * 1000

      location = self.data_location or FLAGS.location
      labels = None
      if self.label is not None:
        labels = _ParseLabels(self.label)

      if self.source_dataset:
        source_dataset_reference = client.GetDatasetReference(
            self.source_dataset)
      else:
        source_dataset_reference = None

      if self.external_source and self.source_dataset:
        raise app.UsageError(
            'Cannot specify both external_source and linked dataset.'
        )

      if self.external_source and not self.connection_id:
        raise app.UsageError(
            'connection_id is required when external_source is specified.'
        )

      client.CreateDataset(
          reference,
          ignore_existing=True,
          description=self.description,
          default_table_expiration_ms=default_table_exp_ms,
          default_partition_expiration_ms=default_partition_exp_ms,
          data_location=location,
          default_kms_key=self.default_kms_key,
          labels=labels,
          source_dataset_reference=source_dataset_reference,
          external_source=self.external_source,
          connection_id=self.connection_id,
          max_time_travel_hours=self.max_time_travel_hours,
          storage_billing_model=self.storage_billing_model,
      )
      print("Dataset '%s' successfully created." % (reference,))
    elif isinstance(reference, TableReference):
      if self.source_dataset:
        raise app.UsageError('Cannot specify --source_dataset for a table.')
      object_name = 'Table'
      if self.view:
        object_name = 'View'
      if self.materialized_view:
        object_name = 'Materialized View'
      if client.TableExists(reference):
        message = ("%s '%s' could not be created; a table with this name "
                   'already exists.') % (
                       object_name,
                       reference,
                   )
        if not self.f:
          raise bq_error.BigqueryError(message)
        else:
          print(message)
          return
      if schema:
        schema = bigquery_client.BigqueryClient.ReadSchema(schema)
      else:
        schema = None
      expiration = None
      labels = None
      if self.label is not None:
        labels = _ParseLabels(self.label)
      if self.data_location:
        raise app.UsageError('Cannot specify data location for a table.')
      if self.default_table_expiration:
        raise app.UsageError('Cannot specify default expiration for a table.')
      if self.expiration:
        expiration = int(self.expiration + time.time()) * 1000
      view_query_arg = self.view or None
      materialized_view_query_arg = self.materialized_view or None

      external_data_config = None
      if self.external_table_definition is not None:
        external_data_config = _GetExternalDataConfig(
            self.external_table_definition,
            self.use_avro_logical_types,
            self.parquet_enum_as_string,
            self.parquet_enable_list_inference,
            self.metadata_cache_mode,
            self.object_metadata,
            self.preserve_ascii_control_characters,
            self.reference_file_schema_uri,
            self.file_set_spec_type,
        )
        if 'fileSetSpecType' in external_data_config:
          external_data_config['fileSetSpecType'] = _ParseFileSetSpecType(
              external_data_config['fileSetSpecType'])

      biglake_config = None
      has_all_required_biglake_config = (
          self.connection_id
          and self.storage_uri
          and self.table_format
      )
      has_some_required_biglake_config = (
          self.connection_id
          or self.storage_uri
          or self.file_format
          or self.table_format
      )
      if has_all_required_biglake_config:
        biglake_config = {
            'connection_id': self.connection_id,
            'storage_uri': self.storage_uri,
            'file_format': self.file_format,
            'table_format': self.table_format,
        }
      elif has_some_required_biglake_config:
        raise app.UsageError(
            'BigLake tables require all of connection_id, storage_uri,'
            ' and table_format to be specified'
        )

      view_udf_resources = None
      if self.view_udf_resource:
        view_udf_resources = _ParseUdfResources(self.view_udf_resource)
      time_partitioning = _ParseTimePartitioning(
          self.time_partitioning_type,
          self.time_partitioning_expiration,
          self.time_partitioning_field,
          None,
          self.require_partition_filter)
      clustering = _ParseClustering(self.clustering_fields)
      range_partitioning = _ParseRangePartitioning(self.range_partitioning)
      table_constraints = None
      resource_tags = None
      if self.add_tags is not None:
        resource_tags = bq_utils.ParseTags(self.add_tags)
      client.CreateTable(
          reference,
          ignore_existing=True,
          schema=schema,
          description=self.description,
          expiration=expiration,
          view_query=view_query_arg,
          materialized_view_query=materialized_view_query_arg,
          enable_refresh=self.enable_refresh,
          refresh_interval_ms=self.refresh_interval_ms,
          max_staleness=self.max_staleness,
          view_udf_resources=view_udf_resources,
          use_legacy_sql=self.use_legacy_sql,
          external_data_config=external_data_config,
          biglake_config=biglake_config,
          labels=labels,
          time_partitioning=time_partitioning,
          clustering=clustering,
          range_partitioning=range_partitioning,
          require_partition_filter=self.require_partition_filter,
          destination_kms_key=(self.destination_kms_key),
          table_constraints=table_constraints,
          resource_tags=resource_tags)
      print("%s '%s' successfully created." % (
          object_name,
          reference,
      ))


class _Truncate(BigqueryCmd):  # pylint: disable=missing-docstring
  usage = """bq truncate project_id:dataset[.table] [--timestamp] [--dry_run] [--overwrite] [--skip_fully_replicated_tables]
"""

  def __init__(self, name, fv):
    super(_Truncate, self).__init__(name, fv)
    flags.DEFINE_integer(
        'timestamp',
        None,
        'Optional timestamp to which table(s) will be truncated. Specified as milliseconds since epoch.',
        short_name='t',
        flag_values=fv)
    flags.DEFINE_boolean(
        'dry_run',
        None,
        'No-op that simply prints out information and the recommended timestamp without modifying tables or datasets.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'overwrite',
        False,
        'Overwrite existing tables. Otherwise timestamp will be appended to all output table names.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'skip_fully_replicated_tables',
        True,
        'Skip tables that are fully replicated (synced) and do not need to be truncated back to a point in time. This could result in datasets that have tables synchronized to different points in time, but will require less data to be re-loaded',
        short_name='s',
        flag_values=fv)

    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier=''):
    # pylint: disable=g-doc-exception
    """Truncates table/dataset/project to a particular timestamp.

    Examples:
      bq truncate project_id:dataset
      bq truncate --overwrite project_id:dataset --timestamp 123456789
      bq truncate --skip_fully_replicated_tables=false project_id:dataset
    """
    client = Client.Get()

    if identifier:
      reference = client.GetReference(identifier.strip())
    else:
      raise app.UsageError('Must specify one of project, dataset or table')

    self.truncated_table_count = 0
    self.skipped_table_count = 0
    self.failed_table_count = 0
    status = []
    if self.timestamp and not self.dry_run:
      print(
          'Truncating to user specified timestamp %s.(Not skipping fully replicated tables.)'
          % self.timestamp)
      if isinstance(reference, TableReference):
        all_tables = [reference]
      else:
        if isinstance(reference, DatasetReference):
          all_tables = list(
              map(lambda x: client.GetReference(x['id']),
                  client.ListTables(reference, max_results=1000 * 1000)))
      for a_table in all_tables:
        try:
          status.append(
              self._TruncateTable(a_table, str(self.timestamp), False))
        except bq_error.BigqueryError as e:
          print(e)
          status.append((self._formatOutputString(a_table, 'Failed')))
          self.failed_table_count += 1
    else:
      if isinstance(reference, TableReference):
        all_table_infos = self._GetTableInfo(reference)
      else:
        if isinstance(reference, DatasetReference):
          all_table_infos = self._GetTableInfosFromDataset(reference)
      try:
        recovery_timestamp = min(
            list(map(self._GetRecoveryTimestamp, all_table_infos)))
      except (ValueError, TypeError):
        recovery_timestamp = None
      # Error out if we can't figure out a recovery timestamp
      # This can happen in following cases:
      # 1. No multi_site_info present for a table because no commit has been
      #  made to the table.
      # 2. No secondary site is present.
      if not recovery_timestamp:
        raise app.UsageError(
            'Unable to figure out a recovery timestamp for %s. Exiting.' %
            reference)
      print('Recommended timestamp to truncate to is %s' % recovery_timestamp)

      for a_table in all_table_infos:
        try:
          table_reference = ApiClientHelper.TableReference.Create(
              projectId=reference.projectId,
              datasetId=reference.datasetId,
              tableId=a_table['name'])
          status.append(
              self._TruncateTable(table_reference, str(recovery_timestamp),
                                  a_table['fully_replicated']))
        except bq_error.BigqueryError as e:
          print(e)
          status.append((self._formatOutputString(table_reference, 'Failed')))
          self.failed_table_count += 1
    print(
        '%s tables truncated, %s tables failed to truncate, %s tables skipped' %
        (self.truncated_table_count, self.failed_table_count,
         self.skipped_table_count))
    print(*status, sep='\n')

  def _GetTableInfosFromDataset(self, dataset_reference):

    # Find minimum of second maximum(latest_replicated_time) for all tables in
    # the dataset and if they are fully replicated.
    recovery_timestamp_for_dataset_query = ("""SELECT
  TABLE_NAME,
  UNIX_MILLIS(replicated_time_at_remote_site),
  CASE
    WHEN last_update_time <= min_latest_replicated_time THEN TRUE
  ELSE
  FALSE
END
  AS fully_replicated
FROM (
  SELECT
    TABLE_NAME,
    multi_site_info.last_update_time,
    ARRAY_AGG(site_info.latest_replicated_time
    ORDER BY
      latest_replicated_time DESC)[safe_OFFSET(1)] AS replicated_time_at_remote_site,
    ARRAY_AGG(site_info.latest_replicated_time
    ORDER BY
      latest_replicated_time ASC)[safe_OFFSET(0)] AS min_latest_replicated_time
  FROM
    %s.INFORMATION_SCHEMA.TABLES t,
    t.multi_site_info.site_info
  GROUP BY
    1,
    2)""") % dataset_reference.datasetId
    return self._ReadTableInfo(recovery_timestamp_for_dataset_query,
                               1000 * 1000)

  def _GetTableInfo(self, table_reference):

    # Find second maximum of latest_replicated_time across all sites for this
    # table and if the table is fully replicated
    recovery_timestamp_for_table_query = ("""SELECT
  TABLE_NAME,
  UNIX_MILLIS(replicated_time_at_remote_site),
  CASE
    WHEN last_update_time <= min_latest_replicated_time THEN TRUE
  ELSE
  FALSE
END
  AS fully_replicated
FROM (
  SELECT
    TABLE_NAME,
    multi_site_info.last_update_time,
    ARRAY_AGG(site_info.latest_replicated_time
    ORDER BY
      latest_replicated_time DESC)[safe_OFFSET(1)] AS replicated_time_at_remote_site,
    ARRAY_AGG(site_info.latest_replicated_time
    ORDER BY
      latest_replicated_time ASC)[safe_OFFSET(0)] AS min_latest_replicated_time
  FROM
    %s.INFORMATION_SCHEMA.TABLES t,
    t.multi_site_info.site_info
  WHERE
    TABLE_NAME = '%s'
  GROUP BY
    1,
    2 )""") % (table_reference.datasetId, table_reference.tableId)
    return self._ReadTableInfo(recovery_timestamp_for_table_query, row_count=1)

  def _GetRecoveryTimestamp(self, table_info):
    return int(table_info['recovery_timestamp']
              ) if table_info['recovery_timestamp'] else None

  def _ReadTableInfo(self, query, row_count):
    client = Client.Get()
    try:
      job = client.Query(query, use_legacy_sql=False)
    except bq_error.BigqueryError as e:
      if 'Name multi_site_info not found' in e.error['message']:
        raise app.UsageError(
            'This functionality is not enabled for the current project.')
      else:
        raise e
    all_table_infos = []
    if not BigqueryClient.IsFailedJob(job):
      _, rows = client.ReadSchemaAndJobRows(
          job['jobReference'], start_row=0, max_rows=row_count)
      for i in range(len(rows)):
        table_info = {}
        table_info['name'] = rows[i][0]
        table_info['recovery_timestamp'] = rows[i][1]
        table_info['fully_replicated'] = rows[i][2] == 'true'
        all_table_infos.append(table_info)
      return all_table_infos

  def _formatOutputString(self, table_reference, status):
    return '%s %200s' % (table_reference, status)

  def _TruncateTable(self, table_reference, recovery_timestamp,
                     is_fully_replicated):
    client = Client.Get()
    kwds = {}
    if not self.overwrite:
      dest = ApiClientHelper.TableReference.Create(
          projectId=table_reference.projectId,
          datasetId=table_reference.datasetId,
          tableId='_'.join(
              [table_reference.tableId, 'TRUNCATED_AT', recovery_timestamp]))
    else:
      dest = table_reference

    if self.skip_fully_replicated_tables and is_fully_replicated:
      self.skipped_table_count += 1
      return self._formatOutputString(table_reference,
                                      'Fully replicated...Skipped')
    if self.dry_run:
      return self._formatOutputString(
          dest, 'will be Truncated@%s' % recovery_timestamp)
    kwds = {
        'write_disposition': 'WRITE_TRUNCATE',
        'ignore_already_exists': 'False',
        'operation_type': 'COPY',
    }
    if FLAGS.location:
      kwds['location'] = FLAGS.location
    source_table = client.GetTableReference(
        '%s@%s' % (table_reference, recovery_timestamp))
    job_ref = ' '
    try:
      job = client.CopyTable([source_table], dest, **kwds)
      if job is None:
        self.failed_table_count += 1
        return self._formatOutputString(dest, 'Failed')
      job_ref = BigqueryClient.ConstructObjectReference(job)
      self.truncated_table_count += 1
      return self._formatOutputString(dest, 'Successful %s ' % job_ref)
    except bq_error.BigqueryError as e:
      print(e)
      self.failed_table_count += 1
      return self._formatOutputString(dest, 'Failed %s ' % job_ref)


class _Update(BigqueryCmd):
  usage = """update [-d] [-t] <identifier> [<schema>]"""

  def __init__(self, name, fv):
    super(_Update, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'dataset',
        False,
        'Updates a dataset with this name.',
        short_name='d',
        flag_values=fv)
    flags.DEFINE_boolean(
        'table',
        False,
        'Updates a table with this name.',
        short_name='t',
        flag_values=fv)
    flags.DEFINE_boolean(
        'model',
        False,
        'Updates a model with this model ID.',
        short_name='m',
        flag_values=fv)
    flags.DEFINE_boolean(
        'reservation',
        None,
        'Updates a reservation described by this identifier.',
        flag_values=fv)
    flags.DEFINE_integer(
        'slots',
        None,
        'The number of baseline slots associated with the reservation.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'capacity_commitment',
        None,
        'Updates a capacity commitment described by this identifier.',
        flag_values=fv)
    flags.DEFINE_enum(
        'plan',
        None, ['MONTHLY', 'ANNUAL', 'THREE_YEAR'],
        'Commitment plan for this capacity commitment. Plan can only be '
        'updated to the one with longer committed period. Options include:'
        '\n MONTHLY'
        '\n ANNUAL'
        '\n THREE_YEAR',
        flag_values=fv)
    flags.DEFINE_enum(
        'renewal_plan',
        None,
        [
            'FLEX',
            'MONTHLY',
            'ANNUAL',
            'THREE_YEAR',
            'NONE',
        ],
        'The plan this capacity commitment is converted to after committed '
        'period ends. Options include:'
        '\n NONE'
        '\n FLEX'
        '\n MONTHLY'
        '\n ANNUAL'
        '\n THREE_YEAR'
        '\n NONE can only be used in conjunction with --edition, '
        '\n while FLEX and MONTHLY cannot be used together with --edition.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'split',
        None,
        'If true, splits capacity commitment into two. Split parts are defined '
        'by the --slots param.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'merge',
        None,
        'If true, merges capacity commitments into one. At least two comma '
        'separated capacity commitment ids must be specified.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'reservation_assignment',
        None,
        'Updates a reservation assignment and so that the assignee will use a '
        'new reservation. '
        'Used in conjunction with --destination_reservation_id',
        flag_values=fv)
    flags.DEFINE_string(
        'destination_reservation_id',
        None, 'Destination reservation ID. '
        'Used in conjunction with --reservation_assignment.',
        flag_values=fv)
    flags.DEFINE_enum(
        'priority',
        None, [
            'HIGH',
            'INTERACTIVE',
            'BATCH',
            '',
        ], 'Reservation assignment default job priority. Only available for '
        'whitelisted reservations. Options include:'
        '\n HIGH'
        '\n INTERACTIVE'
        '\n BATCH'
        '\n empty string to unset priority',
        flag_values=fv)
    flags.DEFINE_string(
        'reservation_size',
        None,
        'DEPRECATED, Please use bi_reservation_size instead.',
        flag_values=fv)
    flags.DEFINE_string(
        'bi_reservation_size',
        None, 'BI reservation size. Can be specified in bytes '
        '(--bi_reservation_size=2147483648) or in GB (--bi_reservation_size=1G). '
        'Minimum 1GB. Use 0 to remove reservation.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'use_idle_slots',
        None,
        'If true, any query running in this reservation will be able to use '
        'idle slots from other reservations. Used if ignore_idle_slots is '
        'None.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'ignore_idle_slots',
        None,
        'If false, any query running in this reservation will be able to use '
        'idle slots from other reservations.',
        flag_values=fv)
    flags.DEFINE_integer(
        'max_concurrency',
        None,
        'Deprecated, please use target_job_concurrency instead.',
        flag_values=fv)
    flags.DEFINE_integer(
        'concurrency',
        None,
        'Deprecated, please use target_job_concurrency instead.',
        flag_values=fv)
    flags.DEFINE_integer(
        'target_job_concurrency',
        None,
        'Sets a soft upper bound on the number of jobs that can run '
        'concurrently in the reservation. Default value is 0 which means that '
        'concurrency target will be automatically computed by the system.',
        flag_values=fv)
    flags.DEFINE_bool(
        'enable_queuing_and_priorities',
        None,
        'Whether to enable queuing and new job prioritization behavior for the '
        'reservation. Reservation must be whitelisted in order to set this '
        'flag.',
        flag_values=fv)
    flags.DEFINE_integer(
        'autoscale_max_slots',
        None,
        'Number of slots to be scaled when needed. Autoscale will be enabled '
        'when setting this.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'transfer_config',
        False,
        'Updates a transfer configuration for a configuration resource name.',
        flag_values=fv)
    flags.DEFINE_string(
        'target_dataset',
        '',
        'Updated dataset ID for the transfer configuration.',
        flag_values=fv)
    flags.DEFINE_string(
        'display_name',
        '',
        'Updated display name for the transfer configuration or connection.',
        flag_values=fv)
    flags.DEFINE_integer(
        'refresh_window_days',
        None,
        'Updated refresh window days for the updated transfer configuration.',
        flag_values=fv)
    flags.DEFINE_string(
        'params',
        None, 'Updated parameters for the updated transfer configuration '
        'in JSON format.'
        'For example: --params=\'{\"param\":\"param_value\"}\'',
        short_name='p',
        flag_values=fv)
    flags.DEFINE_boolean(
        'update_credentials',
        False,
        'Update the transfer configuration credentials.',
        flag_values=fv)
    flags.DEFINE_string(
        'schedule_start_time',
        None, 'Time to start scheduling transfer runs for the given '
        'transfer configuration. If empty, the default value for '
        'the start time will be used to start runs immediately.'
        'The format for the time stamp is RFC3339 UTC "Zulu". '
        'Read more: '
        'https://developers.google.com/protocol-buffers/docs/'
        'reference/google.protobuf#google.protobuf.Timestamp',
        flag_values=fv)
    flags.DEFINE_string(
        'schedule_end_time',
        None, 'Time to stop scheduling transfer runs for the given '
        'transfer configuration. If empty, the default value for '
        'the end time will be used to schedule runs indefinitely.'
        'The format for the time stamp is RFC3339 UTC "Zulu". '
        'Read more: '
        'https://developers.google.com/protocol-buffers/docs/'
        'reference/google.protobuf#google.protobuf.Timestamp',
        flag_values=fv)
    flags.DEFINE_string(
        'schedule',
        None,
        'Data transfer schedule. If the data source does not support a custom '
        'schedule, this should be empty. If empty, the default '
        'value for the data source will be used. The specified times are in '
        'UTC. Examples of valid format: 1st,3rd monday of month 15:30, '
        'every wed,fri of jan,jun 13:15, and first sunday of quarter 00:00. '
        'See more explanation about the format here: '
        'https://cloud.google.com/appengine/docs/flexible/python/scheduling-jobs-with-cron-yaml#the_schedule_format',  # pylint: disable=line-too-long
        flag_values=fv)
    flags.DEFINE_bool(
        'no_auto_scheduling',
        False, 'Disables automatic scheduling of data transfer runs for this '
        'configuration.',
        flag_values=fv)
    flags.DEFINE_string(
        'service_account_name',
        '',
        'Service account used as the credential on the transfer config.',
        flag_values=fv)
    flags.DEFINE_string(
        'notification_pubsub_topic',
        '',
        'Pub/Sub topic used for notification after transfer run completed or '
        'failed.',
        flag_values=fv)
    flags.DEFINE_string(
        'schema',
        '', 'Either a filename or a comma-separated list of fields in the form '
        'name[:type].',
        flag_values=fv)
    flags.DEFINE_string(
        'description',
        None,
        'Description of the dataset, table, view or connection.',
        flag_values=fv)
    flags.DEFINE_multi_string(
        'set_label',
        None,
        'A label to set on a dataset or a table. The format is "key:value"',
        flag_values=fv)
    flags.DEFINE_multi_string(
        'clear_label',
        None,
        'A label key to remove from a dataset or a table.',
        flag_values=fv)
    flags.DEFINE_integer(
        'expiration',
        None, 'Expiration time, in seconds from now, of a table or view. '
        'Specifying 0 removes expiration time.',
        flag_values=fv)
    flags.DEFINE_integer(
        'default_table_expiration',
        None, 'Default lifetime, in seconds, for newly-created tables in a '
        'dataset. Newly-created tables will have an expiration time of '
        'the current time plus this value. Specify "0" to remove existing '
        'expiration.',
        flag_values=fv)
    flags.DEFINE_integer(
        'default_partition_expiration',
        None,
        'Default partition expiration for all partitioned tables in the dataset'
        ', in seconds. The storage in a partition will have an expiration time '
        'of its partition time plus this value. If this property is set, '
        'partitioned tables created in the dataset will use this instead of '
        'default_table_expiration. Specify "0" to remove existing expiration.',
        flag_values=fv)
    flags.DEFINE_string(
        'source',
        None,
        'Path to file with JSON payload for an update',
        flag_values=fv)
    flags.DEFINE_string('view', '', 'SQL query of a view.', flag_values=fv)
    flags.DEFINE_string(
        'materialized_view',
        None,
        'Standard SQL query of a materialized view.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'enable_refresh',
        None,
        'Whether to enable automatic refresh of the materialized views when '
        'the base table is updated. If not set, the default is true.',
        flag_values=fv)
    flags.DEFINE_integer(
        'refresh_interval_ms',
        None,
        'Milliseconds that must have elapsed since last refresh until the '
        'materialized view can be automatically refreshed again. If not set, '
        'the default value is "1800000" (30 minutes).',
        flag_values=fv)
    flags.DEFINE_string(
        'max_staleness',
        None,
        'INTERVAL value that determines the maximum staleness allowed when '
        'querying a materialized view or an external table. By default no '
        'staleness is allowed. Examples of valid max_staleness values: '
        '1 day: "0-0 1 0:0:0"; 1 hour: "0-0 0 1:0:0".'
        'See more explanation about the INTERVAL values: '
        'https://cloud.google.com/bigquery/docs/reference/standard-sql/data-types#interval_type',  # pylint: disable=line-too-long
        flag_values=fv)
    flags.DEFINE_string(
        'external_table_definition',
        None,
        'Specifies a table definition to use to update an external table. '
        'The value can be either an inline table definition or a path to a '
        'file containing a JSON table definition.'
        'The format of inline definition is "schema@format=uri@connection". ',
        flag_values=fv)
    flags.DEFINE_enum(
        'metadata_cache_mode',
        None, ['AUTOMATIC', 'MANUAL'],
        'Enables metadata cache for an external table with a connection. '
        'Specify AUTOMATIC to automatically refresh the cached metadata. '
        'Specify MANUAL to stop the automatic refresh.',
        flag_values=fv)
    flags.DEFINE_enum(
        'object_metadata',
        None, ['DIRECTORY', 'SIMPLE'],
        'Object Metadata Type used to create Object Tables. SIMPLE is the '
        'only supported value to create an Object Table containing a directory '
        'listing of objects found at the uri in external_data_definition.',
        flag_values=fv)
    flags.DEFINE_multi_string(
        'view_udf_resource',
        None, 'The URI or local filesystem path of a code file to load and '
        'evaluate immediately as a User-Defined Function resource used '
        'by the view.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'use_legacy_sql',
        None,
        ('The choice of using Legacy SQL for the query is optional. If not '
         'specified, the server will automatically determine the dialect based '
         'on query information, such as dialect prefixes. If no prefixes are '
         'found, it will default to Legacy SQL.'),
        flag_values=fv)
    flags.DEFINE_string(
        'time_partitioning_type',
        None,
        'Enables time based partitioning on the table and set the type. The '
        'default value is DAY, which will generate one partition per day. '
        'Other supported values are HOUR, MONTH, and YEAR.',
        flag_values=fv)
    flags.DEFINE_integer(
        'time_partitioning_expiration',
        None,
        'Enables time based partitioning on the table and sets the number of '
        'seconds for which to keep the storage for the partitions in the table.'
        ' The storage in a partition will have an expiration time of its '
        'partition time plus this value. A negative number means no '
        'expiration.',
        flag_values=fv)
    flags.DEFINE_string(
        'time_partitioning_field',
        None,
        'Enables time based partitioning on the table and the table will be '
        'partitioned based on the value of this field. If time based '
        'partitioning is enabled without this value, the table will be '
        'partitioned based on the loading time.',
        flag_values=fv)
    flags.DEFINE_string(
        'clustering_fields',
        None,
        'Comma-separated list of field names that specifies the columns on '
        'which a table is clustered. To remove the clustering, set an empty '
        'value.',
        flag_values=fv)
    flags.DEFINE_string(
        'etag', None, 'Only update if etag matches.', flag_values=fv)
    flags.DEFINE_string(
        'destination_kms_key',
        None,
        'Cloud KMS key for encryption of the destination table data.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'require_partition_filter',
        None,
        'Whether to require partition filter for queries over this table. '
        'Only apply to partitioned table.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'connection', None, 'Update connection.', flag_values=fv)
    flags.DEFINE_enum(
        'connection_type',
        None,
        bigquery_client.CONNECTION_TYPES,
        'Connection type. Valid values:\n ' + \
        '\n '.join(bigquery_client.CONNECTION_TYPES),
        flag_values=fv)
    flags.DEFINE_string(
        'properties',
        None,
        'Connection properties in JSON format.',
        flag_values=fv)
    flags.DEFINE_string(
        'connection_credential',
        None,
        'Connection credential in JSON format.',
        flag_values=fv)
    flags.DEFINE_string(
        'iam_role_id', None, '[Experimental] IAM role id.', flag_values=fv)
    # TODO(b/231712311): look into cleaning up this flag now that only federated
    # aws connections are supported.
    flags.DEFINE_boolean(
        'federated_aws',
        True,
        '[Experimental] Federated identity.',
        flag_values=fv)
    flags.DEFINE_string(
        'tenant_id', None, '[Experimental] Tenant id.', flag_values=fv)
    flags.DEFINE_string(
        'federated_app_client_id',
        None,
        '[Experimental] The application (client) id of the Active Directory '
        'application to use with Azure federated identity.',
        flag_values=fv)
    flags.DEFINE_string(
        'range_partitioning',
        None, 'Enables range partitioning on the table. The format should be '
        '"field,start,end,interval". The table will be partitioned based on the'
        ' value of the field. Field must be a top-level, non-repeated INT64 '
        'field. Start, end, and interval are INT64 values defining the ranges.',
        flag_values=fv)
    flags.DEFINE_string(
        'default_kms_key',
        None,
        'Defines default KMS key name for all newly objects created in the '
        'dataset. Table/Model creation request can override this default.',
        flag_values=fv)
    flags.DEFINE_integer(
        'max_time_travel_hours',
        None,
        'Optional. Define the max time travel in hours. The value can be from '
        '48 to 168 hours (2 to 7 days). The default value is 168 hours if this '
        'is not set.',
        flag_values=fv)
    flags.DEFINE_enum(
        'storage_billing_model',
        None, ['LOGICAL', 'PHYSICAL'],
        'Optional. Sets the storage billing model for the dataset. \n'
        'LOGICAL - switches to logical billing model \n'
        'PHYSICAL - switches to physical billing model.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'autodetect_schema',
        False,
        'Optional. If true, schema is autodetected; else schema is unchanged.',
        flag_values=fv)
    flags.DEFINE_string(
        'vertex_ai_model_id',
        None,
        'Optional. Define the Vertex AI model ID to register to Vertex AI for '
        'BigQuery ML models.',
        flag_values=fv)
    flags.DEFINE_string(
        'kms_key_name',
        None,
        'Cloud KMS key name used for encryption.',
        flag_values=fv,
    )
    flags.DEFINE_string(
        'add_tags',
        None,
        'Tags to attach to the table. The format is namespaced key:value pair '
        'like "1234567/my_tag_key:my_tag_value,test-project123/environment:production"',
        flag_values=fv)
    flags.DEFINE_string(
        'remove_tags',
        None,
        'Tags to remove from the table. The format is namespaced keys like'
        ' "1234567/my_tag_key,test-project123/environment"',
        flag_values=fv)
    flags.DEFINE_boolean(
        'clear_all_tags',
        False,
        'Clear all tags attached to the table',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier='', schema=''):
    # pylint: disable=g-doc-exception
    """Updates a dataset, table, view or transfer configuration with this name.

    See 'bq help load' for more information on specifying the schema.

    Examples:
      bq update --description "Dataset description" existing_dataset
      bq update --description "My table" existing_dataset.existing_table
      bq update --description "My model" -m existing_dataset.existing_model
      bq update -t existing_dataset.existing_table name:integer,value:string
      bq update --destination_kms_key
          projects/p/locations/l/keyRings/r/cryptoKeys/k
          existing_dataset.existing_table
      bq update --view='select 1 as num' existing_dataset.existing_view
         (--view_udf_resource=path/to/file.js)
      bq update --transfer_config --display_name=name -p='{"param":"value"}'
          projects/p/locations/l/transferConfigs/c
      bq update --transfer_config --target_dataset=dataset
          --refresh_window_days=5 --update_credentials
          projects/p/locations/l/transferConfigs/c
      bq update --reservation --location=US --project_id=my-project
          --bi_reservation_size=2G
      bq update --capacity_commitment --location=US --project_id=my-project
          --plan=MONTHLY --renewal_plan=FLEX commitment_id
      bq update --capacity_commitment --location=US --project_id=my-project
        --split --slots=500 commitment_id
      bq update --capacity_commitment --location=US --project_id=my-project
        --merge commitment_id1,commitment_id2
      bq update --reservation_assignment
          --destination_reservation_id=proj:US.new_reservation
          proj:US.old_reservation.assignment_id
      bq update --connection_credential='{"username":"u", "password":"p"}'
        --location=US --project_id=my-project existing_connection
    """
    client = Client.Get()
    if self.d and self.t:
      raise app.UsageError('Cannot specify both -d and -t.')
    if ValidateAtMostOneSelected(self.schema, self.view,
                                 self.materialized_view):
      raise app.UsageError('Cannot specify more than one of'
                           ' --schema or --view or --materialized_view.')
    if self.t:
      reference = client.GetTableReference(identifier)
    elif self.view:
      reference = client.GetTableReference(identifier)
    elif self.materialized_view:
      reference = client.GetTableReference(identifier)
    elif self.reservation:
      try:
        if self.reservation_size is not None or self.bi_reservation_size is not None:
          size = self.bi_reservation_size
          if size is None:
            size = self.reservation_size
          reference = client.GetBiReservationReference(FLAGS.location)
          object_info = client.UpdateBiReservation(reference, size)
          print(object_info)
        else:
          reference = client.GetReservationReference(
              identifier=identifier, default_location=FLAGS.location)
          ignore_idle_arg = self.ignore_idle_slots
          if ignore_idle_arg is None and self.use_idle_slots is not None:
            ignore_idle_arg = not self.use_idle_slots
          concurrency = self.target_job_concurrency
          if concurrency is None:
            concurrency = (
                self.concurrency
                if self.concurrency is not None else self.max_concurrency)
          object_info = client.UpdateReservation(
              reference=reference,
              slots=self.slots,
              ignore_idle_slots=ignore_idle_arg,
              target_job_concurrency=concurrency,
              enable_queuing_and_priorities=self.enable_queuing_and_priorities,
              autoscale_max_slots=self.autoscale_max_slots,
          )
          _PrintObjectInfo(object_info, reference, custom_format='show')
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to update reservation '%s': %s" % (identifier, e))
    elif self.capacity_commitment:
      try:
        if self.split and self.merge:
          raise bq_error.BigqueryError(
              'Cannot specify both --split and --merge.')
        reference = client.GetCapacityCommitmentReference(
            identifier=identifier,
            default_location=FLAGS.location,
            allow_commas=self.merge)
        if self.split:
          response = client.SplitCapacityCommitment(reference, self.slots)
          _PrintObjectsArray(response, objects_type=CapacityCommitmentReference)
        elif self.merge:
          object_info = client.MergeCapacityCommitments(
              reference.location, reference.capacityCommitmentId.split(','))
          reference = client.GetCapacityCommitmentReference(
              path=object_info['name'])
          _PrintObjectInfo(object_info, reference, custom_format='show')
        else:
          object_info = client.UpdateCapacityCommitment(reference, self.plan,
                                                        self.renewal_plan)
          _PrintObjectInfo(object_info, reference, custom_format='show')
      except BaseException as e:
        err = ''
        # Merge error is not specific to identifier, so making it more generic.
        if self.merge:
          err = 'Capacity commitments merge failed: %s' % (e)
        else:
          err = "Failed to update capacity commitment '%s': %s" % (identifier,
                                                                   e)
        raise bq_error.BigqueryError(err)
    elif self.reservation_assignment:
      try:
        reference = client.GetReservationAssignmentReference(
            identifier=identifier, default_location=FLAGS.location)
        if self.destination_reservation_id and self.priority is not None:
          raise bq_error.BigqueryError(
              'Cannot specify both --destination_reservation_id and '
              '--priority.')
        if self.destination_reservation_id:
          object_info = client.MoveReservationAssignment(
              reference=reference,
              destination_reservation_id=self.destination_reservation_id,
              default_location=FLAGS.location)
          reference = client.GetReservationAssignmentReference(
              path=object_info['name'])
        elif self.priority is not None:
          object_info = client.UpdateReservationAssignment(
              reference, self.priority)
        else:
          raise bq_error.BigqueryError(
              'Either --destination_reservation_id or --priority must be '
              'specified.')

        _PrintObjectInfo(
            object_info, reference, custom_format='show', print_reference=False)
      except BaseException as e:
        raise bq_error.BigqueryError(
            "Failed to update reservation assignment '%s': %s" %
            (identifier, e))
    elif self.d or not identifier:
      reference = client.GetDatasetReference(identifier)
    elif self.m:
      reference = client.GetModelReference(identifier)
    elif self.transfer_config:
      formatted_identifier = _FormatDataTransferIdentifiers(client, identifier)
      reference = TransferConfigReference(
          transferConfigName=formatted_identifier)
    elif self.connection or self.connection_credential:
      reference = client.GetConnectionReference(
          identifier=identifier, default_location=FLAGS.location)
      if self.connection_type == 'AWS' and self.iam_role_id:
        self.properties = bigquery_client.MakeAccessRolePropertiesJson(
            self.iam_role_id)
      if self.connection_type == 'Azure':
        if self.tenant_id and self.federated_app_client_id:
          self.properties = bigquery_client.MakeAzureFederatedAppClientAndTenantIdPropertiesJson(
              self.tenant_id, self.federated_app_client_id)
        elif self.federated_app_client_id:
          self.properties = bigquery_client.MakeAzureFederatedAppClientIdPropertiesJson(
              self.federated_app_client_id)
        elif self.tenant_id:
          self.properties = bigquery_client.MakeTenantIdPropertiesJson(
              self.tenant_id)
      if (
          self.properties or
          self.display_name or
          self.description or
          self.connection_credential or
          self.kms_key_name is not None
      ):
        updated_connection = client.UpdateConnection(
            reference=reference,
            display_name=self.display_name,
            description=self.description,
            connection_type=self.connection_type,
            properties=self.properties,
            connection_credential=self.connection_credential,
            kms_key_name=self.kms_key_name,
        )
        bigquery_client.MaybePrintManualInstructionsForConnection(
            updated_connection)

    else:
      reference = client.GetReference(identifier)
      _Typecheck(reference, (DatasetReference, TableReference),
                 "Invalid identifier '%s' for update." % (identifier,))

    label_keys_to_remove = None
    labels_to_set = None
    if self.set_label is not None:
      labels_to_set = _ParseLabels(self.set_label)
    if self.clear_label is not None:
      label_keys_to_remove = set(self.clear_label)

    if isinstance(reference, DatasetReference):
      if self.schema:
        raise app.UsageError('Cannot specify schema with a dataset.')
      if self.view:
        raise app.UsageError('Cannot specify view with a dataset.')
      if self.materialized_view:
        raise app.UsageError('Cannot specify materialized view with a dataset.')
      if self.expiration:
        raise app.UsageError('Cannot specify an expiration for a dataset.')
      if self.external_table_definition is not None:
        raise app.UsageError(
            'Cannot specify an external_table_definition for a dataset.')
      if self.source and self.description:
        raise app.UsageError('Cannot specify description with a source.')
      default_table_exp_ms = None
      if self.default_table_expiration is not None:
        default_table_exp_ms = self.default_table_expiration * 1000
      default_partition_exp_ms = None
      if self.default_partition_expiration is not None:
        default_partition_exp_ms = self.default_partition_expiration * 1000
      _UpdateDataset(
          client,
          reference,
          description=self.description,
          source=self.source,
          default_table_expiration_ms=default_table_exp_ms,
          default_partition_expiration_ms=default_partition_exp_ms,
          labels_to_set=labels_to_set,
          label_keys_to_remove=label_keys_to_remove,
          default_kms_key=self.default_kms_key,
          etag=self.etag,
          max_time_travel_hours=self.max_time_travel_hours,
          storage_billing_model=self.storage_billing_model)
      print("Dataset '%s' successfully updated." % (reference,))
    elif isinstance(reference, TableReference):
      object_name = 'Table'
      if self.view:
        object_name = 'View'
      if self.materialized_view:
        object_name = 'Materialized View'
      if self.source:
        raise app.UsageError('%s update does not support --source.' %
                             object_name)
      if schema:
        schema = bigquery_client.BigqueryClient.ReadSchema(schema)
      else:
        schema = None
      expiration = None
      if self.expiration is not None:
        if self.expiration == 0:
          expiration = 0
        else:
          expiration = int(self.expiration + time.time()) * 1000
      if self.default_table_expiration:
        raise app.UsageError('Cannot specify default expiration for a table.')
      external_data_config = None
      if self.external_table_definition is not None:
        external_data_config = _GetExternalDataConfig(
            self.external_table_definition,
            metadata_cache_mode=self.metadata_cache_mode,
            object_metadata=self.object_metadata,
        )
        # When updating, move the schema out of the external_data_config.
        # If schema is set explicitly on this update, prefer it over the
        # external_data_config schema.
        # Note: binary formats and text formats with autodetect enabled may not
        # have a schema set.
        # Hive partitioning requires that the schema be set on the external data
        # config.
        if ('schema' in external_data_config) and ('hivePartitioningOptions'
                                                   not in external_data_config):
          if schema is None:
            schema = external_data_config['schema']['fields']
          # Regardless delete schema from the external data config.
          del external_data_config['schema']
      view_query_arg = self.view or None
      materialized_view_query_arg = self.materialized_view or None
      view_udf_resources = None
      if self.view_udf_resource:
        view_udf_resources = _ParseUdfResources(self.view_udf_resource)
      time_partitioning = _ParseTimePartitioning(
          self.time_partitioning_type, self.time_partitioning_expiration,
          self.time_partitioning_field, None, self.require_partition_filter)
      range_partitioning = _ParseRangePartitioning(self.range_partitioning)
      clustering = _ParseClustering(self.clustering_fields)

      encryption_configuration = None
      if self.destination_kms_key:
        encryption_configuration = {'kmsKeyName': self.destination_kms_key}
      table_constraints = None
      tags_to_attach = None
      if self.add_tags:
        tags_to_attach = bq_utils.ParseTags(self.add_tags)
      tags_to_remove = None
      if self.remove_tags:
        tags_to_remove = bq_utils.ParseTagKeys(self.remove_tags)

      client.UpdateTable(
          reference,
          schema=schema,
          description=self.description,
          expiration=expiration,
          view_query=view_query_arg,
          materialized_view_query=materialized_view_query_arg,
          enable_refresh=self.enable_refresh,
          refresh_interval_ms=self.refresh_interval_ms,
          max_staleness=self.max_staleness,
          view_udf_resources=view_udf_resources,
          use_legacy_sql=self.use_legacy_sql,
          external_data_config=external_data_config,
          labels_to_set=labels_to_set,
          label_keys_to_remove=label_keys_to_remove,
          time_partitioning=time_partitioning,
          range_partitioning=range_partitioning,
          clustering=clustering,
          require_partition_filter=self.require_partition_filter,
          etag=self.etag,
          encryption_configuration=encryption_configuration,
          autodetect_schema=self.autodetect_schema,
          table_constraints=table_constraints,
          tags_to_attach=tags_to_attach,
          tags_to_remove=tags_to_remove,
          clear_all_tags=self.clear_all_tags,
          )

      print("%s '%s' successfully updated." % (
          object_name,
          reference,
      ))
    elif isinstance(reference, TransferConfigReference):
      if client.TransferExists(reference):
        auth_info = {}
        service_account_name = ''
        if self.update_credentials:
          if self.service_account_name:
            service_account_name = self.service_account_name
          else:
            transfer_config_name = _FormatDataTransferIdentifiers(
                client, reference.transferConfigName)
            current_config = client.GetTransferConfig(transfer_config_name)
            auth_info = RetrieveAuthorizationInfo(
                'projects/' + client.GetProjectReference().projectId,
                current_config['dataSourceId'], client.GetTransferV1ApiClient())
        schedule_args = bigquery_client.TransferScheduleArgs(
            schedule=self.schedule,
            start_time=self.schedule_start_time,
            end_time=self.schedule_end_time,
            disable_auto_scheduling=self.no_auto_scheduling)
        client.UpdateTransferConfig(
            reference=reference,
            target_dataset=self.target_dataset,
            display_name=self.display_name,
            refresh_window_days=self.refresh_window_days,
            params=self.params,
            auth_info=auth_info,
            service_account_name=service_account_name,
            destination_kms_key=self.destination_kms_key,
            notification_pubsub_topic=self.notification_pubsub_topic,
            schedule_args=schedule_args)
        print("Transfer configuration '%s' successfully updated." %
              (reference,))
      else:
        raise bq_error.BigqueryNotFoundError(
            'Not found: %r' % (reference,), {'reason': 'notFound'}, [])
    elif isinstance(reference, ModelReference):
      expiration = None
      if self.expiration:
        expiration = int(self.expiration + time.time()) * 1000
      else:
        expiration = self.expiration  # None or 0
      client.UpdateModel(
          reference,
          description=self.description,
          expiration=expiration,
          labels_to_set=labels_to_set,
          label_keys_to_remove=label_keys_to_remove,
          vertex_ai_model_id=self.vertex_ai_model_id,
          etag=self.etag)
      print("Model '%s' successfully updated." % (reference))


def CheckValidCreds(reference, data_source, transfer_client):
  """Checks valid credentials.

  Checks if Data Transfer Service valid credentials exist for the given data
  source and requesting user. Some data sources don't support service account,
  so we need to talk to them on behalf of the end user. This method just checks
  whether we have OAuth token for the particular user, which is a pre-requisite
  before a user can create a transfer config.

  Args:
    reference: The project reference.
    data_source: The data source of the transfer config.
    transfer_client: The transfer api client.

  Returns:
    credentials: It contains an instance of CheckValidCredsResponse if valid
    credentials exist.

  """
  credentials = None
  if FLAGS.location:
    data_source_reference = (
        reference + '/locations/' + FLAGS.location + '/dataSources/' +
        data_source)
    credentials = transfer_client.projects().locations().dataSources(
    ).checkValidCreds(
        name=data_source_reference, body={}).execute()
  else:
    data_source_reference = (reference + '/dataSources/' + data_source)
    credentials = transfer_client.projects().dataSources().checkValidCreds(
        name=data_source_reference, body={}).execute()
  return credentials


def RetrieveAuthorizationInfo(reference, data_source, transfer_client):
  """Retrieves the authorization code.

  An authorization code is needed if the Data Transfer Service does not
  have credentials for the requesting user and data source. The Data
  Transfer Service will convert this authorization code into a refresh
  token to perform transfer runs on the user's behalf.

  Args:
    reference: The project reference.
    data_source: The data source of the transfer config.
    transfer_client: The transfer api client.

  Returns:
    auth_info: A dict which contains authorization info from user. It is either
    an authorization_code or a version_info.

  """
  data_source_retrieval = reference + '/dataSources/' + data_source
  data_source_info = transfer_client.projects().dataSources().get(
      name=data_source_retrieval).execute()
  first_party_oauth = False
  if data_source_info['authorizationType'] == 'FIRST_PARTY_OAUTH':
    first_party_oauth = True
  auth_uri = ('https://www.gstatic.com/bigquerydatatransfer/oauthz/'
              'auth?client_id=' + data_source_info['clientId'] + '&scope=' +
              '%20'.join(data_source_info['scopes']) +
              '&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=' +
              ('version_info' if first_party_oauth else 'authorization_code'))
  print('\n' + auth_uri)

  auth_info = {}
  if first_party_oauth:
    print('Please copy and paste the above URL into your web browser'
          ' and follow the instructions to retrieve a version_info.')
    auth_info[bigquery_client.VERSION_INFO] = _RawInput(
        'Enter your version_info here: ')
  else:
    print('Please copy and paste the above URL into your web browser'
          ' and follow the instructions to retrieve an authorization code.')
    auth_info[bigquery_client.AUTHORIZATION_CODE] = _RawInput(
        'Enter your authorization code here: ')

  return auth_info


def _UpdateDataset(
    client,
    reference,
    description=None,
    source=None,
    default_table_expiration_ms=None,
    default_partition_expiration_ms=None,
    labels_to_set=None,
    label_keys_to_remove=None,
    etag=None,
    default_kms_key=None,
    max_time_travel_hours=None,
    storage_billing_model=None):
  """Updates a dataset.

  Reads JSON file if specified and loads updated values, before calling bigquery
  dataset update.

  Args:
    client: the BigQuery client.
    reference: the DatasetReference to update.
    description: an optional dataset description.
    source: an optional filename containing the JSON payload.
    default_table_expiration_ms: optional number of milliseconds for the default
      expiration duration for new tables created in this dataset.
    default_partition_expiration_ms: optional number of milliseconds for the
      default partition expiration duration for new partitioned tables created
      in this dataset.
    labels_to_set: an optional dict of labels to set on this dataset.
    label_keys_to_remove: an optional list of label keys to remove from this
      dataset.
    default_kms_key: an optional CMEK encryption key for all new tables in the
      dataset.
    max_time_travel_hours: Optional. Define the max time travel in hours. The
      value can be from 48 to 168 hours (2 to 7 days). The default value is 168
      hours if this is not set.
    storage_billing_model: Optional. Sets the storage billing model for the
      dataset.

  Raises:
    UsageError: when incorrect usage or invalid args are used.
  """
  acl = None
  if source is not None:
    if not os.path.exists(source):
      raise app.UsageError('Source file not found: %s' % (source,))
    if not os.path.isfile(source):
      raise app.UsageError('Source path is not a file: %s' % (source,))
    with open(source) as f:
      try:
        payload = json.load(f)
        if payload.__contains__('description'):
          description = payload['description']
        if payload.__contains__('access'):
          acl = payload['access']
      except ValueError as e:
        raise app.UsageError('Error decoding JSON schema from file %s: %s' %
                             (source, e))
  client.UpdateDataset(
      reference,
      description=description,
      acl=acl,
      default_table_expiration_ms=default_table_expiration_ms,
      default_partition_expiration_ms=default_partition_expiration_ms,
      labels_to_set=labels_to_set,
      label_keys_to_remove=label_keys_to_remove,
      etag=etag,
      default_kms_key=default_kms_key,
      max_time_travel_hours=max_time_travel_hours,
      storage_billing_model=storage_billing_model)


class _Show(BigqueryCmd):
  usage = """show [<identifier>]"""

  def __init__(self, name, fv):
    super(_Show, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'job',
        False,
        'If true, interpret this identifier as a job id.',
        short_name='j',
        flag_values=fv)
    flags.DEFINE_boolean(
        'dataset',
        False,
        'Show dataset with this name.',
        short_name='d',
        flag_values=fv)
    flags.DEFINE_boolean(
        'view',
        False,
        'Show view specific details instead of general table details.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'materialized_view',
        False,
        'Show materialized view specific details instead of general table '
        'details.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'table_replica',
        False,
        'Show table replica specific details instead of general table details.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'schema',
        False,
        'Show only the schema instead of general table details.',
        flag_values=fv,
    )
    flags.DEFINE_boolean(
        'encryption_service_account',
        False,
        'Show the service account for a user if it exists, or create one '
        'if it does not exist.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'transfer_config',
        False,
        'Show transfer configuration for configuration resource name.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'transfer_run',
        False,
        'Show information about the particular transfer run.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'model',
        False,
        'Show details of model with this model ID.',
        short_name='m',
        flag_values=fv)
    flags.DEFINE_boolean(
        'routine',
        False,
        'Show the details of a particular routine.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'reservation',
        None,
        'Shows details for the reservation described by this identifier.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'capacity_commitment',
        None, 'Shows details for the capacity commitment described by this '
        'identifier.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'reservation_assignment',
        None, 'Looks up reservation assignments for a specified '
        'project/folder/organization. Explicit reservation assignments will be '
        'returned if exist. Otherwise implicit reservation assignments from '
        'parents will be returned. '
        'Used in conjunction with --job_type, --assignee_type and '
        '--assignee_id.',
        flag_values=fv)
    flags.DEFINE_enum(
        'job_type',
        None,
        [
            'QUERY',
            'PIPELINE',
            'ML_EXTERNAL',
            'BACKGROUND',
            'SPARK',
            'CONTINUOUS',
        ],
        (
            'Type of jobs to search reservation assignment for. Options'
            ' include:\n QUERY\n PIPELINE\n ML_EXTERNAL\n BACKGROUND\n SPARK\n'
            ' Used in conjunction with --reservation_assignment.'
        ),
        flag_values=fv,
    )
    flags.DEFINE_enum(
        'assignee_type',
        None, ['PROJECT', 'FOLDER', 'ORGANIZATION'],
        'Type of assignees for the reservation assignment. Options include:'
        '\n PROJECT'
        '\n FOLDER'
        '\n ORGANIZATION'
        '\n Used in conjunction with --reservation_assignment.',
        flag_values=fv)
    flags.DEFINE_string(
        'assignee_id',
        None,
        'Project/folder/organization ID, to which the reservation is assigned. '
        'Used in conjunction with --reservation_assignment.',
        flag_values=fv)
    flags.DEFINE_boolean(
        'connection',
        None,
        'Shows details for the connection described by this identifier.',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier=''):
    """Show all information about an object.

    Examples:
      bq show -j <job_id>
      bq show dataset
      bq show [--schema] dataset.table
      bq show [--view] dataset.view
      bq show [--materialized_view] dataset.materialized_view
      bq show -m ds.model
      bq show --routine ds.routine
      bq show --transfer_config projects/p/locations/l/transferConfigs/c
      bq show --transfer_run projects/p/locations/l/transferConfigs/c/runs/r
      bq show --encryption_service_account
      bq show --connection --project_id=project --location=us connection
      bq show --capacity_commitment project:US.capacity_commitment_id
      bq show --reservation --location=US --project_id=project reservation_name
      bq show --reservation_assignment --project_id=project --location=US
          --assignee_type=PROJECT --assignee_id=myproject --job_type=QUERY
      bq show --reservation_assignment --project_id=project --location=US
          --assignee_type=FOLDER --assignee_id=123 --job_type=QUERY
      bq show --reservation_assignment --project_id=project --location=US
          --assignee_type=ORGANIZATION --assignee_id=456 --job_type=QUERY
    """
    # pylint: disable=g-doc-exception
    client = Client.Get()
    custom_format = 'show'
    object_info = None
    print_reference = True
    if self.j:
      reference = client.GetJobReference(identifier, FLAGS.location)
    elif self.d:
      reference = client.GetDatasetReference(identifier)
    elif self.view:
      reference = client.GetTableReference(identifier)
      custom_format = 'view'
    elif self.materialized_view:
      reference = client.GetTableReference(identifier)
      custom_format = 'materialized_view'
    elif self.table_replica:
      reference = client.GetTableReference(identifier)
      custom_format = 'table_replica'
    elif self.schema:
      if FLAGS.format not in [None, 'prettyjson', 'json']:
        raise app.UsageError(
            'Table schema output format must be json or prettyjson.')
      reference = client.GetTableReference(identifier)
      custom_format = 'schema'
    elif self.transfer_config:
      formatted_identifier = _FormatDataTransferIdentifiers(client, identifier)
      reference = TransferConfigReference(
          transferConfigName=formatted_identifier)
      object_info = client.GetTransferConfig(formatted_identifier)
    elif self.transfer_run:
      formatted_identifier = _FormatDataTransferIdentifiers(client, identifier)
      reference = TransferRunReference(transferRunName=formatted_identifier)
      object_info = client.GetTransferRun(formatted_identifier)
    elif self.m:
      reference = client.GetModelReference(identifier)
    elif self.routine:
      reference = client.GetRoutineReference(identifier)
    elif self.reservation:
      reference = client.GetReservationReference(
          identifier=identifier, default_location=FLAGS.location)
      object_info = client.GetReservation(reference)
    elif self.reservation_assignment:
      search_all_projects = True
      if search_all_projects:
        object_info = client.SearchAllReservationAssignments(
            location=FLAGS.location,
            job_type=self.job_type,
            assignee_type=self.assignee_type,
            assignee_id=self.assignee_id)
      # Here we just need any object of ReservationAssignmentReference type, but
      # the value of the object doesn't matter here.
      # _PrintObjectInfo() will use the type and object_info to format the
      # output.
      reference = ApiClientHelper.ReservationAssignmentReference.Create(
          projectId=' ',
          location=' ',
          reservationId=' ',
          reservationAssignmentId=' ')
      print_reference = False
    elif self.capacity_commitment:
      reference = client.GetCapacityCommitmentReference(
          identifier=identifier, default_location=FLAGS.location)
      object_info = client.GetCapacityCommitment(reference)
    elif self.encryption_service_account:
      object_info = client.apiclient.projects().getServiceAccount(
          projectId=client.GetProjectReference().projectId).execute()
      email = object_info['email']
      object_info = {'ServiceAccountID': email}
      reference = EncryptionServiceAccount(serviceAccount='serviceAccount')
    elif self.connection:
      reference = client.GetConnectionReference(
          identifier, default_location=FLAGS.location)
      object_info = client.GetConnection(reference)
    else:
      reference = client.GetReference(identifier)
    if reference is None:
      raise app.UsageError('Must provide an identifier for show.')

    if object_info is None:
      object_info = client.GetObjectInfo(reference)
    _PrintObjectInfo(
        object_info,
        reference,
        custom_format=custom_format,
        print_reference=print_reference,
    )


def _IsSuccessfulDmlOrDdlJob(printable_job_info):
  """Returns True iff the job is successful and is a DML/DDL query job."""
  return (
      'Affected Rows' in printable_job_info
      or 'DDL Operation Performed' in printable_job_info
  )


def _MaybeGetSessionTempObjectName(dataset_id, object_id):
  """If we have a session temporary object, returns the user name of the object.

  Args:
    dataset_id: Dataset of object
    object_id: Id of object

  Returns: If the object is a session temp object, the name of the object after
    stripping out internal stuff such as session prefix and signature encodings.

    If the object is not a session temp object, the return value is None.
  """
  if not re.fullmatch('_[0-9a-f]{40}', dataset_id):
    return None  # Not an anonymous dataset

  session_prefix_regexp = (
      '_[0-9a-f]{8}_[0-9a-f]{4}_[0-9a-f]{4}_[0-9a-f]{4}_[0-9a-f]{12}_'
  )
  opt_signature_encoding_regexp = '(?:_b0a98f6_.*)?'
  match = re.fullmatch(
      session_prefix_regexp + '(.*?)' + opt_signature_encoding_regexp, object_id
  )
  if not match:
    return None  # No session prefix
  return match.group(1)


def _PrintJobMessages(printable_job_info):
  """Prints additional info from a job formatted for printing.

  If the job had a fatal error, non-fatal warnings are not shown.

  If any error/warning does not have a 'message' key, printable_job_info must
  have 'jobReference' identifying the job.

  For DML queries prints number of affected rows.
  For DDL queries prints the performed operation and the target.
  """

  job_ref = '(unknown)'  # Should never be seen, but beats a weird crash.
  if 'jobReference' in printable_job_info:
    job_ref = printable_job_info['jobReference']

  # For failing jobs, display the error but not any warnings, because those
  # may be more distracting than helpful.
  if printable_job_info['State'] == 'FAILURE':
    error_result = printable_job_info['status']['errorResult']
    error_ls = printable_job_info['status'].get('errors', [])
    error = bq_error.CreateBigqueryError(error_result, error_result, error_ls)
    print('Error encountered during job execution:\n%s\n' % (error,))
  elif 'errors' in printable_job_info['status']:
    warnings = printable_job_info['status']['errors']
    print(('Warning%s encountered during job execution:\n' %
           ('' if len(warnings) == 1 else 's')))
    recommend_show = False
    for w in warnings:
      # Some warnings include detailed error messages, and some just
      # include programmatic error codes.  Some have a 'location'
      # separately, and some put it in the 'message' text.
      if 'message' not in w:
        recommend_show = True
      else:
        if 'location' in w:
          message = '[%s] %s' % (w['location'], w['message'])
        else:
          message = w['message']
        if message is not None:
          message = message.encode('utf-8')
        print('%s\n' % message)
    if recommend_show:
      print('Use "bq show -j %s" to view job warnings.' % job_ref)
  elif 'Affected Rows' in printable_job_info:
    print('Number of affected rows: %s\n' % printable_job_info['Affected Rows'])
  elif 'DDL Target Table' in printable_job_info:
    ddl_target_table = printable_job_info['DDL Target Table']
    project_id = ddl_target_table.get('projectId')
    dataset_id = ddl_target_table.get('datasetId')
    table_id = ddl_target_table.get('tableId')
    op = _DDL_OPERATION_MAP.get(
        printable_job_info.get('DDL Operation Performed'))
    # DDL Target Table is returned for both TABLE DDL and DROP ALL ROW ACCESS
    # POLICIES DDL statements.
    if project_id and dataset_id and table_id and op:
      if 'DDL Affected Row Access Policy Count' in printable_job_info:
        ddl_affected_row_access_policy_count = printable_job_info[
            'DDL Affected Row Access Policy Count']
        print('{op} {count} row access policies on table '
              '{project}.{dataset}.{table}\n'.format(
                  op=op,
                  count=ddl_affected_row_access_policy_count,
                  project=project_id,
                  dataset=dataset_id,
                  table=table_id))
      elif (
          'Statement Type' in printable_job_info
          and 'INDEX' in printable_job_info['Statement Type']
      ):
        if 'SEARCH_INDEX' in printable_job_info['Statement Type']:
          print('%s search index on table %s.%s.%s\n' %
                (six.ensure_str(op), six.ensure_str(project_id),
                 six.ensure_str(dataset_id), six.ensure_str(table_id)))
        elif 'VECTOR_INDEX' in printable_job_info['Statement Type']:
          print('%s vector index on table %s.%s.%s\n' %
                (six.ensure_str(op), six.ensure_str(project_id),
                 six.ensure_str(dataset_id), six.ensure_str(table_id)))
      else:
        print('%s %s.%s.%s\n' %
              (six.ensure_str(op), six.ensure_str(project_id),
               six.ensure_str(dataset_id), six.ensure_str(table_id)))
  elif 'DDL Target Routine' in printable_job_info:
    ddl_target_routine = printable_job_info['DDL Target Routine']
    project_id = ddl_target_routine.get('projectId')
    dataset_id = ddl_target_routine.get('datasetId')
    routine_id = ddl_target_routine.get('routineId')
    op = _DDL_OPERATION_MAP.get(
        printable_job_info.get('DDL Operation Performed'))
    temp_object_name = _MaybeGetSessionTempObjectName(dataset_id, routine_id)
    if temp_object_name is not None:
      print('%s temporary routine %s' % (op, temp_object_name))
    else:
      print('%s %s.%s.%s' % (op, project_id, dataset_id, routine_id))
  elif 'DDL Target Row Access Policy' in printable_job_info:
    ddl_target_row_access_policy = printable_job_info[
        'DDL Target Row Access Policy']
    project_id = ddl_target_row_access_policy.get('projectId')
    dataset_id = ddl_target_row_access_policy.get('datasetId')
    table_id = ddl_target_row_access_policy.get('tableId')
    row_access_policy_id = ddl_target_row_access_policy.get('policyId')
    op = _DDL_OPERATION_MAP.get(
        printable_job_info.get('DDL Operation Performed'))
    if project_id and dataset_id and table_id and row_access_policy_id and op:
      print(
          '{op} row access policy {policy} on table {project}.{dataset}.{table}'
          .format(
              op=op,
              policy=row_access_policy_id,
              project=project_id,
              dataset=dataset_id,
              table=table_id))
  elif 'Assertion' in printable_job_info:
    print('Assertion successful')

  if 'Session Id' in printable_job_info:
    print('In session: %s' % printable_job_info['Session Id'])


def _PrintObjectInfo(object_info,
                     reference,
                     custom_format,
                     print_reference=True):
  """Prints the object with various formats."""
  # The JSON formats are handled separately so that they don't print
  # the record as a list of one record.
  if custom_format == 'schema':
    if 'schema' not in object_info or 'fields' not in object_info['schema']:
      raise app.UsageError('Unable to retrieve schema from specified table.')
    bq_utils.PrintFormattedJsonObject(object_info['schema']['fields'])
  elif FLAGS.format in ['prettyjson', 'json']:
    bq_utils.PrintFormattedJsonObject(object_info)
  elif FLAGS.format in [None, 'sparse', 'pretty']:
    formatter = _GetFormatterFromFlags()
    BigqueryClient.ConfigureFormatter(
        formatter,
        type(reference),
        print_format=custom_format,
        object_info=object_info)
    object_info = BigqueryClient.FormatInfoByType(object_info, type(reference))
    if object_info:
      formatter.AddDict(object_info)
    if reference.typename and print_reference:
      print('%s %s\n' % (reference.typename.capitalize(), reference))
    formatter.Print()
    print()
    if isinstance(reference, JobReference):
      _PrintJobMessages(object_info)
  else:
    formatter = _GetFormatterFromFlags()
    formatter.AddColumns(list(object_info.keys()))
    formatter.AddDict(object_info)
    formatter.Print()


def _PrintObjectsArray(object_infos, objects_type):
  if FLAGS.format in ['prettyjson', 'json']:
    bq_utils.PrintFormattedJsonObject(object_infos)
  elif FLAGS.format in [None, 'sparse', 'pretty']:
    if not object_infos:
      return
    formatter = _GetFormatterFromFlags()
    BigqueryClient.ConfigureFormatter(
        formatter, objects_type, print_format='list')
    formatted_infos = list(
        map(
            functools.partial(
                BigqueryClient.FormatInfoByType, object_type=objects_type),
            object_infos))
    for info in formatted_infos:
      formatter.AddDict(info)
    formatter.Print()
  elif object_infos:
    formatter = _GetFormatterFromFlags()
    formatter.AddColumns(list(object_infos[0].keys()))
    for info in object_infos:
      formatter.AddDict(info)
    formatter.Print()


def _PrintObjectsArrayWithToken(object_infos, objects_type):
  if FLAGS.format in ['prettyjson', 'json']:
    bq_utils.PrintFormattedJsonObject(object_infos)
  elif FLAGS.format in [None, 'sparse', 'pretty']:
    _PrintObjectsArray(object_infos['results'], objects_type)
    if 'token' in object_infos:
      print('\nNext token: ' + object_infos['token'])


class _Cancel(BigqueryCmd):
  """Attempt to cancel the specified job if it is running."""

  usage = """cancel [--nosync] [<job_id>]"""

  def __init__(self, name, fv):
    super(_Cancel, self).__init__(name, fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, job_id=''):
    # pylint: disable=g-doc-exception
    """Request a cancel and waits for the job to be cancelled.

    Requests a cancel and then either:
    a) waits until the job is done if the sync flag is set [default], or
    b) returns immediately if the sync flag is not set.
    Not all job types support a cancel, an error is returned if it cannot be
    cancelled. Even for jobs that support a cancel, success is not guaranteed,
    the job may have completed by the time the cancel request is noticed, or
    the job may be in a stage where it cannot be cancelled.

    Examples:
      bq cancel job_id  # Requests a cancel and waits until the job is done.
      bq --nosync cancel job_id  # Requests a cancel and returns immediately.

    Arguments:
      job_id: Job ID to cancel.
    """
    client = Client.Get()
    job_reference_dict = dict(client.GetJobReference(job_id, FLAGS.location))
    job = client.CancelJob(
        job_id=job_reference_dict['jobId'],
        location=job_reference_dict['location'])
    _PrintObjectInfo(
        job, JobReference.Create(**job['jobReference']), custom_format='show')
    status = job['status']
    if status['state'] == 'DONE':
      if ('errorResult' in status and 'reason' in status['errorResult'] and
          status['errorResult']['reason'] == 'stopped'):
        print('Job has been cancelled successfully.')
      else:
        print('Job completed before it could be cancelled.')
    else:
      print('Job cancel has been requested.')
    return 0


class _Head(BigqueryCmd):
  usage = """head [-n <max rows>] [-j] [-t] <identifier>"""

  def __init__(self, name, fv):
    super(_Head, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'job',
        False,
        'Reads the results of a query job.',
        short_name='j',
        flag_values=fv)
    flags.DEFINE_boolean(
        'table',
        False,
        'Reads rows from a table.',
        short_name='t',
        flag_values=fv)
    flags.DEFINE_integer(
        'start_row',
        0,
        'The number of rows to skip before showing table data.',
        short_name='s',
        flag_values=fv)
    flags.DEFINE_integer(
        'max_rows',
        100,
        'The number of rows to print when showing table data.',
        short_name='n',
        flag_values=fv)
    flags.DEFINE_string(
        'selected_fields',
        None,
        'A subset of fields (including nested fields) to return when showing '
        'table data. If not specified, full row will be retrieved. '
        'For example, "-c:a,b".',
        short_name='c',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier=''):
    # pylint: disable=g-doc-exception
    """Displays rows in a table.

    Examples:
      bq head dataset.table
      bq head -j job
      bq head -n 10 dataset.table
      bq head -s 5 -n 10 dataset.table
    """
    client = Client.Get()
    if self.j and self.t:
      raise app.UsageError('Cannot specify both -j and -t.')

    if self.j:
      reference = client.GetJobReference(identifier, FLAGS.location)
    else:
      reference = client.GetTableReference(identifier)

    if isinstance(reference, JobReference):
      fields, rows = client.ReadSchemaAndJobRows(
          dict(reference), start_row=self.s, max_rows=self.n)
    elif isinstance(reference, TableReference):
      fields, rows = client.ReadSchemaAndRows(
          dict(reference),
          start_row=self.s,
          max_rows=self.n,
          selected_fields=self.c)
    else:
      raise app.UsageError("Invalid identifier '%s' for head." % (identifier,))

    Factory.ClientTablePrinter.GetTablePrinter().PrintTable(fields, rows)


class _Insert(BigqueryCmd):
  usage = """insert [-s] [-i] [-x=<suffix>] <table identifier> [file]"""

  def __init__(self, name, fv):
    super(_Insert, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'skip_invalid_rows',
        None,
        'Attempt to insert any valid rows, even if invalid rows are present.',
        short_name='s',
        flag_values=fv)
    flags.DEFINE_boolean(
        'ignore_unknown_values',
        None,
        'Ignore any values in a row that are not present in the schema.',
        short_name='i',
        flag_values=fv)
    flags.DEFINE_string(
        'template_suffix',
        None,
        'If specified, treats the destination table as a base template, and '
        'inserts the rows into an instance table named '
        '"{destination}{templateSuffix}". BigQuery will manage creation of the '
        'instance table, using the schema of the base template table.',
        short_name='x',
        flag_values=fv)
    flags.DEFINE_string(
        'insert_id',
        None,
        'Used to ensure repeat executions do not add unintended data. '
        'A present insert_id value will be appended to the row number of '
        'each row to be inserted and used as the insertId field for the row. '
        'Internally the insertId field is used for deduping of inserted rows.',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier='', filename=None):
    """Inserts rows in a table.

    Inserts the records formatted as newline delimited JSON from file
    into the specified table. If file is not specified, reads from stdin.
    If there were any insert errors it prints the errors to stdout.

    Examples:
      bq insert dataset.table /tmp/mydata.json
      echo '{"a":1, "b":2}' | bq insert dataset.table

    Template table examples:
    Insert to dataset.template_suffix table using dataset.template table as
    its template.
      bq insert -x=_suffix dataset.table /tmp/mydata.json
    """
    if filename:
      with open(filename, 'r') as json_file:
        return self._DoInsert(
            identifier,
            json_file,
            skip_invalid_rows=self.skip_invalid_rows,
            ignore_unknown_values=self.ignore_unknown_values,
            template_suffix=self.template_suffix,
            insert_id=self.insert_id)
    else:
      return self._DoInsert(
          identifier,
          sys.stdin,
          skip_invalid_rows=self.skip_invalid_rows,
          ignore_unknown_values=self.ignore_unknown_values,
          template_suffix=self.template_suffix,
          insert_id=self.insert_id)

  def _DoInsert(self,
                identifier,
                json_file,
                skip_invalid_rows=None,
                ignore_unknown_values=None,
                template_suffix=None,
                insert_id=None):
    """Insert the contents of the file into a table."""
    client = Client.Get()
    reference = client.GetReference(identifier)
    _Typecheck(reference, (TableReference,),
               'Must provide a table identifier for insert.')
    reference = dict(reference)
    batch = []

    def Flush():
      result = client.InsertTableRows(
          reference,
          batch,
          skip_invalid_rows=skip_invalid_rows,
          ignore_unknown_values=ignore_unknown_values,
          template_suffix=template_suffix)
      del batch[:]
      return result, result.get('insertErrors', None)

    result = {}
    errors = None
    lineno = 1
    for line in json_file:
      try:
        unique_insert_id = None
        if insert_id is not None:
          unique_insert_id = insert_id + '_' + str(lineno)
        batch.append(bigquery_client.JsonToInsertEntry(unique_insert_id, line))
        lineno += 1
      except bq_error.BigqueryClientError as e:
        raise app.UsageError('Line %d: %s' % (lineno, str(e)))
      if (FLAGS.max_rows_per_request and
          len(batch) == FLAGS.max_rows_per_request):
        result, errors = Flush()
      if errors:
        break
    if batch and not errors:
      result, errors = Flush()

    if FLAGS.format in ['prettyjson', 'json']:
      bq_utils.PrintFormattedJsonObject(result)
    elif FLAGS.format in [None, 'sparse', 'pretty']:
      if errors:
        for entry in result['insertErrors']:
          entry_errors = entry['errors']
          sys.stdout.write('record %d errors: ' % (entry['index'],))
          for error in entry_errors:
            print('\t%s: %s' % (six.ensure_str(
                error['reason']), six.ensure_str(error.get('message'))))
    return 1 if errors else 0


class _Wait(BigqueryCmd):  # pylint: disable=missing-docstring
  usage = """wait [<job_id>] [<secs>]"""

  def __init__(self, name, fv):
    super(_Wait, self).__init__(name, fv)
    flags.DEFINE_boolean(
        'fail_on_error',
        True, 'When done waiting for the job, exit the process with an error '
        'if the job is still running, or ended with a failure.',
        flag_values=fv)
    flags.DEFINE_string(
        'wait_for_status',
        'DONE',
        'Wait for the job to have a certain status. Default is DONE.',
        flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, job_id='', secs=sys.maxsize):
    # pylint: disable=g-doc-exception
    """Wait some number of seconds for a job to finish.

    Poll job_id until either (1) the job is DONE or (2) the
    specified number of seconds have elapsed. Waits forever
    if unspecified. If no job_id is specified, and there is
    only one running job, we poll that job.

    Examples:
      bq wait # Waits forever for the currently running job.
      bq wait job_id  # Waits forever
      bq wait job_id 100  # Waits 100 seconds
      bq wait job_id 0  # Polls if a job is done, then returns immediately.
      # These may exit with a non-zero status code to indicate "failure":
      bq wait --fail_on_error job_id  # Succeeds if job succeeds.
      bq wait --fail_on_error job_id 100  # Succeeds if job succeeds in 100 sec.

    Arguments:
      job_id: Job ID to wait on.
      secs: Number of seconds to wait (must be >= 0).
    """
    try:
      secs = BigqueryClient.NormalizeWait(secs)
    except ValueError:
      raise app.UsageError('Invalid wait time: %s' % (secs,))

    client = Client.Get()
    if not job_id:
      running_jobs = client.ListJobRefs(state_filter=['PENDING', 'RUNNING'])
      if len(running_jobs) != 1:
        raise bq_error.BigqueryError(
            'No job_id provided, found %d running jobs' % (len(running_jobs),))
      job_reference = running_jobs.pop()
    else:
      job_reference = client.GetJobReference(job_id, FLAGS.location)
    try:
      job = client.WaitJob(
          job_reference=job_reference, wait=secs, status=self.wait_for_status)
      _PrintObjectInfo(
          job, JobReference.Create(**job['jobReference']), custom_format='show')
      return 1 if self.fail_on_error and BigqueryClient.IsFailedJob(job) else 0
    except StopIteration as e:
      print()
      print(e)
    # If we reach this point, we have not seen the job succeed.
    return 1 if self.fail_on_error else 0


class _IamPolicyCmd(BigqueryCmd):
  """Common superclass for commands that interact with BQ's IAM meta API.

  Provides common flags, identifier decoding logic, and GetIamPolicy and
  SetIamPolicy logic.
  """

  def __init__(self, name, fv, verb):
    """Initialize.

    Args:
      name: the command name string to bind to this handler class.
      fv: the FlagValues flag-registry object.
      verb: the verb string (e.g. 'Set', 'Get', 'Add binding to', ...) to print
        in various descriptions.
    """
    super(_IamPolicyCmd, self).__init__(name, fv)

    # The shell doesn't currently work with commands containing hyphens. That
    # requires some internal rewriting logic.
    self.surface_in_shell = False

    flags.DEFINE_boolean(
        'dataset',
        False,
        '%s IAM policy for dataset described by this identifier.' % verb,
        short_name='d',
        flag_values=fv)
    flags.DEFINE_boolean(
        'table',
        False,
        '%s IAM policy for table described by this identifier.' % verb,
        short_name='t',
        flag_values=fv)
    flags.DEFINE_boolean(
        'connection',
        None,
        '%s IAM policy for connection described by this identifier.' % verb,
        flag_values=fv,
    )
    # Subclasses should call self._ProcessCommandRc(fv) after calling this
    # superclass initializer and adding their own flags.

  def GetReferenceFromIdentifier(self, client, identifier):
    # pylint: disable=g-doc-exception
    provided_flags = [
        f
        for f in [self.d, self.t, self.connection]
        if f is not None and f
    ]
    if len(provided_flags) > 1:
      raise app.UsageError(
          'Cannot specify more than one of -d, -t or -connection.'
      )
    if not identifier:
      raise app.UsageError(
          'Must provide an identifier for %s.' % (self._command_name,)
      )

    if self.t:
      reference = client.GetTableReference(identifier)
    elif self.d:
      reference = client.GetDatasetReference(identifier)
    elif self.connection:
      reference = client.GetConnectionReference(
          identifier, default_location=FLAGS.location
      )
    else:
      reference = client.GetReference(identifier)
      _Typecheck(
          reference, (DatasetReference, TableReference),
          'Invalid identifier "%s" for %s.' % (identifier, self._command_name))
    return reference

  def GetPolicyForReference(self, client, reference):
    """Get the IAM policy for a table or dataset.

    Args:
      reference: A DatasetReference or TableReference.

    Returns:
      The policy object, composed of dictionaries, lists, and primitive types.

    Raises:
      RuntimeError: reference isn't an expected type.
    """
    if isinstance(reference, TableReference):
      return client.GetTableIAMPolicy(reference)
    elif isinstance(reference, DatasetReference):
      return client.GetDatasetIAMPolicy(reference)
    elif isinstance(reference, ConnectionReference):
      return client.GetConnectionIAMPolicy(reference)
    raise RuntimeError(
        'Unexpected reference type: {r_type}'.format(r_type=type(reference)))

  def SetPolicyForReference(self, client, reference, policy):
    """Set the IAM policy for a table or dataset.

    Args:
      reference: A DatasetReference or TableReference.
      policy: The policy object, composed of dictionaries, lists, and primitive
        types.

    Raises:
      RuntimeError: reference isn't an expected type.
    """
    if isinstance(reference, TableReference):
      return client.SetTableIAMPolicy(reference, policy)
    elif isinstance(reference, DatasetReference):
      return client.SetDatasetIAMPolicy(reference, policy)
    elif isinstance(reference, ConnectionReference):
      return client.SetConnectionIAMPolicy(reference, policy)
    raise RuntimeError(
        'Unexpected reference type: {r_type}'.format(r_type=type(reference)))


class _GetIamPolicy(_IamPolicyCmd):  # pylint: disable=missing-docstring
  usage = """get-iam-policy [(-d|-t|-connection)] <identifier>"""

  def __init__(self, name, fv):
    super(_GetIamPolicy, self).__init__(name, fv, 'Get')
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier):
    """Get the IAM policy for a resource.

    Gets the IAM policy for a dataset, table or connection resource, and prints
    it to stdout. The policy is in JSON format.

    Usage:
    get-iam-policy <identifier>

    Examples:
      bq get-iam-policy ds.table1
      bq get-iam-policy --project_id=proj -t ds.table1
      bq get-iam-policy proj:ds.table1

    Arguments:
      identifier: The identifier of the resource. Presently only table, view and
        connection resources are fully supported. (Last updated: 2022-04-25)
    """
    client = Client.Get()
    reference = self.GetReferenceFromIdentifier(client, identifier)
    result_policy = self.GetPolicyForReference(client, reference)
    bq_utils.PrintFormattedJsonObject(
        result_policy, default_format='prettyjson')


class _SetIamPolicy(_IamPolicyCmd):  # pylint: disable=missing-docstring
  usage = """set-iam-policy [(-d|-t|-connection)] <identifier> <filename>"""

  def __init__(self, name, fv):
    super(_SetIamPolicy, self).__init__(name, fv, 'Set')
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier, filename):
    """Set the IAM policy for a resource.

    Sets the IAM policy for a dataset, table or connection resource. After
    setting the policy, the new policy is printed to stdout. Policies are in
    JSON format.

    If the 'etag' field is present in the policy, it must match the value in the
    current policy, which can be obtained with 'bq get-iam-policy'. Otherwise
    this command will fail. This feature allows users to prevent concurrent
    updates.

    Usage:
    set-iam-policy <identifier> <filename>

    Examples:
      bq set-iam-policy ds.table1 /tmp/policy.json
      bq set-iam-policy --project_id=proj -t ds.table1 /tmp/policy.json
      bq set-iam-policy proj:ds.table1 /tmp/policy.json

    Arguments:
      identifier: The identifier of the resource. Presently only table, view and
        connection resources are fully supported. (Last updated: 2022-04-25)
      filename: The name of a file containing the policy in JSON format.
    """
    client = Client.Get()
    reference = self.GetReferenceFromIdentifier(client, identifier)
    with open(filename, 'r') as file_obj:
      policy = json.load(file_obj)
      result_policy = self.SetPolicyForReference(client, reference, policy)
      bq_utils.PrintFormattedJsonObject(
          result_policy, default_format='prettyjson')


class _IamPolicyBindingCmd(_IamPolicyCmd):  # pylint: disable=missing-docstring
  """Common superclass for _AddIamPolicyBinding and _RemoveIamPolicyBinding.

  Provides the flags that are common to both commands, and also inherits
  flags and logic from the _IamPolicyCmd class.
  """

  def __init__(self, name, fv, verb):
    super(_IamPolicyBindingCmd, self).__init__(name, fv, verb)
    flags.DEFINE_string(
        'member',
        None,
        ('The member part of the IAM policy binding. Acceptable values include '
         '"user:<email>", "group:<email>", "serviceAccount:<email>", '
         '"allAuthenticatedUsers" and "allUsers".'
         '\n'
         '\n"allUsers" is a special value that represents every user. '
         '"allAuthenticatedUsers" is a special value that represents every '
         'user that is authenticated with a Google account or a service account.'
         '\n'
         '\nExamples:'
         '\n  "user:myaccount@gmail.com"'
         '\n  "group:mygroup@example-company.com"'
         '\n  "serviceAccount:myserviceaccount@sub.example-company.com"'
         '\n  "domain:sub.example-company.com"'
         '\n  "allUsers"'
         '\n  "allAuthenticatedUsers"'),
        flag_values=fv)
    flags.DEFINE_string(
        'role',
        None, 'The role part of the IAM policy binding.'
        '\n'
        '\nExamples:'
        '\n'
        '\nA predefined (built-in) BigQuery role:'
        '\n  "roles/bigquery.dataViewer"'
        '\n'
        '\nA custom role defined in a project:'
        '\n  "projects/my-project/roles/MyCustomRole"'
        '\n'
        '\nA custom role defined in an organization:'
        '\n  "organizations/111111111111/roles/MyCustomRole"',
        flag_values=fv)
    flags.mark_flag_as_required('member', flag_values=fv)
    flags.mark_flag_as_required('role', flag_values=fv)
    # Subclasses should call self._ProcessCommandRc(fv) after calling this
    # superclass initializer and adding their own flags.


class _AddIamPolicyBinding(_IamPolicyBindingCmd):  # pylint: disable=missing-docstring
  usage = ('add-iam-policy-binding --member=<member> --role=<role> [(-d|-t)] '
           '<identifier>')

  def __init__(self, name, fv):
    super(_AddIamPolicyBinding, self).__init__(name, fv, verb='Add binding to')
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier):
    r"""Add a binding to a BigQuery resource's policy in IAM.

    Usage:
      add-iam-policy-binding --member=<member> --role=<role> <identifier>

    One binding consists of a member and a role, which are specified with
    (required) flags.

    Examples:

      bq add-iam-policy-binding \
        --member='user:myaccount@gmail.com' \
        --role='roles/bigquery.dataViewer' \
        table1

      bq add-iam-policy-binding \
        --member='serviceAccount:my.service.account@my-domain.com' \
        --role='roles/bigquery.dataEditor' \
        project1:dataset1.table1

      bq add-iam-policy-binding \
       --member='allAuthenticatedUsers' \
       --role='roles/bigquery.dataViewer' \
       --project_id=proj -t ds.table1

    Arguments:
      identifier: The identifier of the resource. Presently only table and view
        resources are fully supported. (Last updated: 2020-08-03)
    """
    client = Client.Get()
    reference = self.GetReferenceFromIdentifier(client, identifier)
    policy = self.GetPolicyForReference(client, reference)
    if 'etag' not in [key.lower() for key in policy]:
      raise ValueError(
          "Policy doesn't have an 'etag' field. This is unexpected. The etag "
          'is required to prevent unexpected results from concurrent edits.')
    self.AddBindingToPolicy(policy, self.member, self.role)
    result_policy = self.SetPolicyForReference(client, reference, policy)
    print(("Successfully added member '{member}' to role '{role}' in IAM "
           "policy for {resource_type} '{identifier}':\n").format(
               member=self.member,
               role=self.role,
               resource_type=reference.typename,  # e.g. 'table' or 'dataset'
               identifier=reference))
    bq_utils.PrintFormattedJsonObject(
        result_policy, default_format='prettyjson')

  @staticmethod
  def AddBindingToPolicy(policy, member, role):
    """Add a binding to an IAM policy.

    Args:
      policy: The policy object, composed of dictionaries, lists, and primitive
        types. This object will be modified, and also returned for convenience.
      member: The string to insert into the 'members' array of the binding.
      role: The role string of the binding to remove.

    Returns:
      The same object referenced by the policy arg, after adding the binding.
    """
    # Check for version 1 (implicit if not specified), because this code can't
    # handle policies with conditions correctly.
    if policy.get('version', 1) > 1:
      raise ValueError(
          ('Only policy versions up to 1 are supported. version: {version}'
          ).format(version=policy.get('version', 'None')))

    bindings = policy.setdefault('bindings', [])
    if not isinstance(bindings, list):
      raise ValueError(
          ("Policy field 'bindings' does not have an array-type value. "
           "'bindings': {value}").format(value=repr(bindings)))

    # Insert the member into the binding section if a binding section for the
    # role already exists and the member is not already present. Otherwise, add
    # a new binding section with the role and member. This is more polite than
    # IAM currently requires, currently (you can put redundant bindings and
    # members, and IAM seems to just merge and deduplicate).
    for binding in bindings:
      if not isinstance(binding, dict):
        raise ValueError(
            ("At least one element of the policy's 'bindings' array is not "
             'an object type. element: {value}').format(value=repr(binding)))
      if binding.get('role') == role:
        break
    else:
      binding = {'role': role}
      bindings.append(binding)
    members = binding.setdefault('members', [])
    if not isinstance(members, list):
      raise ValueError(
          ("Policy binding field 'members' does not have an array-type "
           "value. 'members': {value}").format(value=repr(members)))
    if member not in members:
      members.append(member)
    return policy


class _RemoveIamPolicyBinding(_IamPolicyBindingCmd):  # pylint: disable=missing-docstring
  usage = ('remove-iam-policy-binding --member=<member> --role=<role> '
           '[(-d|-t)] <identifier>')

  def __init__(self, name, fv):
    super(_RemoveIamPolicyBinding, self).__init__(
        name, fv, verb='Remove binding from')
    self._ProcessCommandRc(fv)

  def RunWithArgs(self, identifier):
    r"""Remove a binding from a BigQuery resource's policy in IAM.

    Usage:
      remove-iam-policy-binding --member=<member> --role=<role> <identifier>

    One binding consists of a member and a role, which are specified with
    (required) flags.

    Examples:

      bq remove-iam-policy-binding \
        --member='user:myaccount@gmail.com' \
        --role='roles/bigquery.dataViewer' \
        table1

      bq remove-iam-policy-binding \
        --member='serviceAccount:my.service.account@my-domain.com' \
        --role='roles/bigquery.dataEditor' \
        project1:dataset1.table1

      bq remove-iam-policy-binding \
       --member='allAuthenticatedUsers' \
       --role='roles/bigquery.dataViewer' \
       --project_id=proj -t ds.table1

    Arguments:
      identifier: The identifier of the resource. Presently only table and view
        resources are fully supported. (Last updated: 2020-08-03)
    """
    client = Client.Get()
    reference = self.GetReferenceFromIdentifier(client, identifier)
    policy = self.GetPolicyForReference(client, reference)
    if 'etag' not in [key.lower() for key in policy]:
      raise ValueError(
          "Policy doesn't have an 'etag' field. This is unexpected. The etag "
          'is required to prevent unexpected results from concurrent edits.')
    self.RemoveBindingFromPolicy(policy, self.member, self.role)
    result_policy = self.SetPolicyForReference(client, reference, policy)
    print(("Successfully removed member '{member}' from role '{role}' in IAM "
           "policy for {resource_type} '{identifier}':\n").format(
               member=self.member,
               role=self.role,
               resource_type=reference.typename,  # e.g. 'table' or 'dataset'
               identifier=reference))
    bq_utils.PrintFormattedJsonObject(
        result_policy, default_format='prettyjson')

  @staticmethod
  def RemoveBindingFromPolicy(policy, member, role):
    """Remove a binding from an IAM policy.

    Will remove the member from the binding, and remove the entire binding if
    its members array is empty.

    Args:
      policy: The policy object, composed of dictionaries, lists, and primitive
        types. This object will be modified, and also returned for convenience.
      member: The string to remove from the 'members' array of the binding.
      role: The role string of the binding to remove.

    Returns:
      The same object referenced by the policy arg, after adding the binding.
    """
    # Check for version 1 (implicit if not specified), because this code can't
    # handle policies with conditions correctly.
    if policy.get('version', 1) > 1:
      raise ValueError(
          ('Only policy versions up to 1 are supported. version: {version}'
          ).format(version=policy.get('version', 'None')))

    bindings = policy.get('bindings', [])
    if not isinstance(bindings, list):
      raise ValueError(
          ("Policy field 'bindings' does not have an array-type value. "
           "'bindings': {value}").format(value=repr(bindings)))

    for binding in bindings:
      if not isinstance(binding, dict):
        raise ValueError(
            ("At least one element of the policy's 'bindings' array is not "
             'an object type. element: {value}').format(value=repr(binding)))
      if binding.get('role') == role:
        members = binding.get('members', [])
        if not isinstance(members, list):
          raise ValueError(
              ("Policy binding field 'members' does not have an array-type "
               "value. 'members': {value}").format(value=repr(members)))
        for j, member_j in enumerate(members):
          if member_j == member:
            del members[j]
            # Remove empty bindings. Currently IAM would accept an empty binding
            # and prune it, but maybe in the future it won't, so do this
            # defensively.
            bindings = [b for b in bindings if b.get('members', [])]
            policy['bindings'] = bindings
            return policy
    raise app.UsageError(
        "No binding found for member '{member}' in role '{role}'".format(
            member=member, role=role))


# pylint: disable=g-bad-name
class CommandLoop(cmd.Cmd):
  """Instance of cmd.Cmd built to work with NewCmd."""

  class TerminateSignal(Exception):
    """Exception type used for signaling loop completion."""
    pass

  def __init__(self, commands, prompt=None):
    cmd.Cmd.__init__(self)
    self._commands = {'help': commands['help']}
    self._special_command_names = ['help', 'repl', 'EOF']
    for name, command in six.iteritems(commands):
      if (name not in self._special_command_names and
          isinstance(command, NewCmd) and command.surface_in_shell):
        self._commands[name] = command
        setattr(self, 'do_%s' % (name,), command.RunCmdLoop)
    self._default_prompt = prompt or 'BigQuery> '
    self._set_prompt()
    self._last_return_code = 0

  @property
  def last_return_code(self):
    return self._last_return_code

  def _set_prompt(self):
    client = Client().Get()
    if client.project_id:
      path = str(client.GetReference())
      self.prompt = '%s> ' % (path,)
    else:
      self.prompt = self._default_prompt

  def do_EOF(self, *unused_args):
    """Terminate the running command loop.

    This function raises an exception to avoid the need to do
    potentially-error-prone string parsing inside onecmd.

    Returns:
      Never returns.

    Raises:
      CommandLoop.TerminateSignal: always.
    """
    raise CommandLoop.TerminateSignal()

  def postloop(self):
    print('Goodbye.')

  def completedefault(self, unused_text, line, unused_begidx, unused_endidx):
    if not line:
      return []
    else:
      command_name = line.partition(' ')[0].lower()
      usage = ''
      if command_name in self._commands:
        usage = self._commands[command_name].usage
      elif command_name == 'set':
        usage = 'set (project_id|dataset_id) <name>'
      elif command_name == 'unset':
        usage = 'unset (project_id|dataset_id)'
      if usage:
        print()
        print(usage)
        print('%s%s' % (self.prompt, line), end=' ')
      return []

  def emptyline(self):
    print('Available commands:', end=' ')
    print(' '.join(list(self._commands)))

  def precmd(self, line):
    """Preprocess the shell input."""
    if line == 'EOF':
      return line
    if line.startswith('exit') or line.startswith('quit'):
      return 'EOF'
    words = line.strip().split()
    if len(words) > 1 and words[0].lower() == 'select':
      return 'query %s' % (shlex.quote(line),)
    if len(words) == 1 and words[0] not in ['help', 'ls', 'version']:
      return 'help %s' % (line.strip(),)
    return line

  def onecmd(self, line):
    """Process a single command.

    Runs a single command, and stores the return code in
    self._last_return_code. Always returns False unless the command
    was EOF.

    Args:
      line: (str) Command line to process.

    Returns:
      A bool signaling whether or not the command loop should terminate.
    """
    try:
      self._last_return_code = cmd.Cmd.onecmd(self, line)
    except CommandLoop.TerminateSignal:
      return True
    except BaseException as e:
      name = line.split(' ')[0]
      bq_utils.ProcessError(e, name=name)
      self._last_return_code = 1
    return False

  def get_names(self):
    names = dir(self)
    commands = (
        name for name in self._commands
        if name not in self._special_command_names)
    names.extend('do_%s' % (name,) for name in commands)
    names.append('do_select')
    names.remove('do_EOF')
    return names

  def do_set(self, line):
    """Set the value of the project_id or dataset_id flag."""
    client = Client().Get()
    name, value = (line.split(' ') + ['', ''])[:2]
    if (name not in ('project_id', 'dataset_id') or
        not 1 <= len(line.split(' ')) <= 2):
      print('set (project_id|dataset_id) <name>')
    elif name == 'dataset_id' and not client.project_id:
      print('Cannot set dataset_id with project_id unset')
    else:
      setattr(client, name, value)
      self._set_prompt()
    return 0

  def do_unset(self, line):
    """Unset the value of the project_id or dataset_id flag."""
    name = line.strip()
    client = Client.Get()
    if name not in ('project_id', 'dataset_id'):
      print('unset (project_id|dataset_id)')
    else:
      setattr(client, name, '')
      if name == 'project_id':
        client.dataset_id = ''
      self._set_prompt()
    return 0

  def do_help(self, command_name):
    """Print the help for command_name (if present) or general help."""

    # TODO(user): Add command-specific flags.
    def FormatOneCmd(name, command, command_names):
      indent_size = appcommands.GetMaxCommandLength() + 3
      if len(command_names) > 1:
        indent = ' ' * indent_size
        command_help = flags.text_wrap(
            command.CommandGetHelp('', cmd_names=command_names),
            indent=indent,
            firstline_indent='')
        first_help_line, _, rest = command_help.partition('\n')
        first_line = '%-*s%s' % (indent_size, name + ':', first_help_line)
        return '\n'.join((first_line, rest))
      else:
        default_indent = '  '
        return '\n' + flags.text_wrap(
            command.CommandGetHelp('', cmd_names=command_names),
            indent=default_indent,
            firstline_indent=default_indent) + '\n'

    if not command_name:
      print('\nHelp for Bigquery commands:\n')
      command_names = list(self._commands)
      print('\n\n'.join(
          FormatOneCmd(name, command, command_names)
          for name, command in six.iteritems(self._commands)
          if name not in self._special_command_names))
      print()
    elif command_name in self._commands:
      print(
          FormatOneCmd(
              command_name,
              self._commands[command_name],
              command_names=[command_name]))
    return 0

  def postcmd(self, stop, line):
    return bool(stop) or line == 'EOF'



# pylint: enable=g-bad-name


class _Repl(BigqueryCmd):
  """Start an interactive bq session."""

  def __init__(self, name, fv):
    super(_Repl, self).__init__(name, fv)
    self.surface_in_shell = False
    flags.DEFINE_string(
        'prompt', '', 'Prompt to use for BigQuery shell.', flag_values=fv)
    self._ProcessCommandRc(fv)

  def RunWithArgs(self):
    """Start an interactive bq session."""
    repl = CommandLoop(appcommands.GetCommandList(), prompt=self.prompt)
    print('Welcome to BigQuery! (Type help for more information.)')
    while True:
      try:
        repl.cmdloop()
        break
      except KeyboardInterrupt:
        print()
    return repl.last_return_code


class _Init(BigqueryCmd):
  """Create a .bigqueryrc file and set up OAuth credentials."""

  def __init__(self, name, fv):
    super(_Init, self).__init__(name, fv)
    self.surface_in_shell = False
    flags.DEFINE_boolean(
        'delete_credentials',
        False,
        'If specified, the credentials file associated with this .bigqueryrc '
        'file is deleted.',
        flag_values=fv)

  def _NeedsInit(self):
    """Init never needs to call itself before running."""
    return False

  def DeleteCredentials(self):
    """Deletes this user's credential file."""
    bq_utils.ProcessBigqueryrc()
    filename = FLAGS.service_account_credential_file or FLAGS.credential_file
    if not os.path.exists(filename):
      print('Credential file %s does not exist.' % (filename,))
      return 0
    try:
      if 'y' != _PromptYN('Delete credential file %s? (y/N) ' % (filename,)):
        print('NOT deleting %s, exiting.' % (filename,))
        return 0
      os.remove(filename)
    except OSError as e:
      print('Error removing %s: %s' % (filename, e))
      return 1

  def RunWithArgs(self):
    """Authenticate and create a default .bigqueryrc file."""
    message = ('BQ CLI will soon require all users to log in using'
               ' `gcloud auth login`. `bq init` will no longer handle'
               ' authentication after January 1, 2024.\n')
    termcolor.cprint(
        '\n'.join(textwrap.wrap(message, width=80)),
        color='red',
        attrs=['bold'],
        file=sys.stdout,
    )

    # Capture project_id before loading defaults from ~/.bigqueryrc so that we
    # get the true value of the flag as specified on the command line.
    project_id_flag = FLAGS.project_id
    bq_utils.ProcessBigqueryrc()
    _ConfigureLogging(bq_logging)
    if self.delete_credentials:
      return self.DeleteCredentials()
    bigqueryrc = bq_utils.GetBigqueryRcFilename()
    # Delete the old one, if it exists.
    print()
    print('Welcome to BigQuery! This script will walk you through the ')
    print('process of initializing your .bigqueryrc configuration file.')
    print()
    if os.path.exists(bigqueryrc):
      print(' **** NOTE! ****')
      print('An existing .bigqueryrc file was found at %s.' % (bigqueryrc,))
      print('Are you sure you want to continue and overwrite your existing ')
      print('configuration?')
      print()

      if 'y' != _PromptYN('Overwrite %s? (y/N) ' % (bigqueryrc,)):
        print('NOT overwriting %s, exiting.' % (bigqueryrc,))
        return 0
      print()
      try:
        os.remove(bigqueryrc)
      except OSError as e:
        print('Error removing %s: %s' % (bigqueryrc, e))
        return 1

    print('First, we need to set up your credentials if they do not ')
    print('already exist.')
    print()
    # NOTE: even if the client is not used below (when --project_id is
    # specified), getting the client will start the authorization workflow if
    # credentials do not already exist and so it is important this is done
    # unconditionally.
    client = Client.Get()

    entries = {'credential_file': FLAGS.credential_file}
    if project_id_flag:
      print('Setting project_id %s as the default.' % project_id_flag)
      print()
      entries['project_id'] = project_id_flag
    else:
      projects = client.ListProjects(max_results=1000)
      print('Credential creation complete. Now we will select a default '
            'project.')
      print()
      if not projects:
        print('No projects found for this user. Please go to ')
        print('  https://console.cloud.google.com/')
        print('and create a project.')
        print()
      else:
        print('List of projects:')
        formatter = _GetFormatterFromFlags()
        formatter.AddColumn('#')
        BigqueryClient.ConfigureFormatter(formatter, ProjectReference)
        for index, project in enumerate(projects):
          result = BigqueryClient.FormatProjectInfo(project)
          result.update({'#': index + 1})
          formatter.AddDict(result)
        formatter.Print()

        if len(projects) == 1:
          project_reference = BigqueryClient.ConstructObjectReference(
              projects[0])
          print('Found only one project, setting %s as the default.' %
                (project_reference,))
          print()
          entries['project_id'] = project_reference.projectId
        else:
          print('Found multiple projects. Please enter a selection for ')
          print('which should be the default, or leave blank to not ')
          print('set a default.')
          print()

          response = None
          while not isinstance(response, int):
            response = _PromptWithDefault('Enter a selection (1 - %s): ' %
                                          (len(projects),))
            try:
              if not response or 1 <= int(response) <= len(projects):
                response = int(response or 0)
            except ValueError:
              pass
          print()
          if response:
            project_reference = BigqueryClient.ConstructObjectReference(
                projects[response - 1])
            entries['project_id'] = project_reference.projectId

    try:
      with open(bigqueryrc, 'w') as rcfile:
        for flag, value in six.iteritems(entries):
          print('%s = %s' % (flag, value), file=rcfile)
    except IOError as e:
      print('Error writing %s: %s' % (bigqueryrc, e))
      return 1

    print('BigQuery configuration complete! Type "bq" to get started.')
    print()
    bq_utils.ProcessBigqueryrc()
    # Destroy the client we created, so that any new client will
    # pick up new flag values.
    Client.Delete()
    return 0


class _Version(BigqueryCmd):
  usage = """version"""

  def _NeedsInit(self):
    """If just printing the version, don't run `init` first."""
    return False

  def RunWithArgs(self):
    """Return the version of bq."""
    print('This is BigQuery CLI %s' % (bq_utils.VERSION_NUMBER,))


class _Info(BigqueryCmd):
  usage = """info"""

  def _NeedsInit(self):
    """If just printing known versions, don't run `init` first."""
    return False

  def RunWithArgs(self):
    """Return the execution information of bq."""
    print(bq_utils.GetInfoString())


def _ParseUdfResources(udf_resources):
  """Parses UDF resources from an array of resource URIs.

     Arguments:
       udf_resources: Array of udf resource URIs.

     Returns:
       Array of UDF resources parsed into the format expected by
       the BigQuery API client.
  """

  if udf_resources is None:
    return None
  inline_udf_resources = []
  external_udf_resources = []
  for uris in udf_resources:
    for uri in uris.split(','):
      if os.path.isfile(uri):
        with open(uri) as udf_file:
          inline_udf_resources.append(udf_file.read())
      else:
        if not uri.startswith('gs://'):
          raise app.UsageError(
              'Non-inline resources must be Google Cloud Storage '
              '(gs://) URIs')
        external_udf_resources.append(uri)
  udfs = []
  if inline_udf_resources:
    for udf_code in inline_udf_resources:
      udfs.append({'inlineCode': udf_code})
  if external_udf_resources:
    for uri in external_udf_resources:
      udfs.append({'resourceUri': uri})
  return udfs


def ValidateDatasetName(dataset_name):
  """A regex to ensure the dataset name is valid.


   Args:
     dataset_name: string name of the dataset to be validated.

   Raises:
     UsageError: An error occurred due to invalid dataset string.
  """
  is_valid = re.fullmatch(r'[a-zA-Z0-9\_]{1,1024}', dataset_name)
  if not is_valid:
    raise app.UsageError(
        'Dataset name: %s is invalid, must be letters '
        '(uppercase or lowercase), numbers, and underscores up to '
        '1024 characters.' % dataset_name)


def _ParseParameters(parameters):
  """Parses query parameters from an array of name:type:value.

  Arguments:
    parameters: An iterable of string-form query parameters: name:type:value.
      Name may be omitted to indicate a positional parameter: :type:value. Type
      may be omitted to indicate a string: name::value, or ::value.

  Returns:
    A list of query parameters in the form for the BigQuery API client.
  """
  if not parameters:
    return None
  results = []
  for param_string in parameters:
    if os.path.isfile(param_string):
      with open(param_string) as f:
        results += json.load(f)
    else:
      results.append(_ParseParameter(param_string))
  return results


def _SplitParam(param_string):
  split = param_string.split(':', 1)
  if len(split) != 2:
    raise app.UsageError('Query parameters must be of the form: '
                         '"name:type:value", ":type:value", or "name::value". '
                         'An empty name produces a positional parameter. '
                         'An empty type produces a STRING parameter.')
  return split


def _ParseParameter(param_string):
  """Parse a string of the form <name><type>:<value> into each part."""
  name, param_string = _SplitParam(param_string)
  try:
    type_dict, value_dict = _ParseParameterTypeAndValue(param_string)
  except app.UsageError as e:
    print('Error parsing parameter %s: %s' % (name, e))
    sys.exit(1)
  result = {'parameterType': type_dict, 'parameterValue': value_dict}
  if name:
    result['name'] = name
  return result


def _ParseParameterTypeAndValue(param_string):
  """Parse a string of the form <recursive_type>:<value> into each part."""
  type_string, value_string = _SplitParam(param_string)
  if not type_string:
    type_string = 'STRING'
  type_dict = _ParseParameterType(type_string)
  return type_dict, _ParseParameterValue(type_dict, value_string)


def _ParseParameterType(type_string):
  """Parse a parameter type string into a JSON dict for the BigQuery API."""
  type_dict = {'type': type_string.upper()}
  if type_string.upper().startswith('ARRAY<') and type_string.endswith('>'):
    type_dict = {
        'type': 'ARRAY',
        'arrayType': _ParseParameterType(type_string[6:-1])
    }
  if type_string.startswith('STRUCT<') and type_string.endswith('>'):
    type_dict = {
        'type': 'STRUCT',
        'structTypes': _ParseStructType(type_string[7:-1])
    }
  if type_string.startswith('RANGE<') and type_string.endswith('>'):
    type_dict = {
        'type': 'RANGE',
        'rangeElementType': _ParseParameterType(type_string[6:-1]),
    }
  if not type_string:
    raise app.UsageError('Query parameter missing type')
  return type_dict


def _ParseStructType(type_string):
  """Parse a Struct QueryParameter type into a JSON dict form."""
  subtypes = []
  for name, sub_type in _StructTypeSplit(type_string):
    subtypes.append({'type': _ParseParameterType(sub_type), 'name': name})
  return subtypes


def _StructTypeSplit(type_string):
  """Yields single field-name, sub-types tuple from a StructType string.

  Raises:
    UsageError: When a field name is missing.
  """
  while type_string:
    next_span = type_string.split(',', 1)[0]
    if '<' in next_span:
      angle_count = 0
      i = 0
      for i in range(next_span.find('<'), len(type_string)):
        if type_string[i] == '<':
          angle_count += 1
        if type_string[i] == '>':
          angle_count -= 1
        if angle_count == 0:
          break
      if angle_count != 0:
        raise app.UsageError('Malformatted struct type')
      next_span = type_string[:i + 1]
    type_string = type_string[len(next_span) + 1:]
    splits = next_span.split(None, 1)
    if len(splits) != 2:
      raise app.UsageError('Struct parameter missing name for field')
    yield splits


def _FormatRfc3339(datetime_obj):
  """Formats a datetime.datetime object (UTC) in RFC3339.

  https://developers.google.com/protocol-buffers/docs/reference/google.protobuf#timestamp

  Args:
    datetime_obj: A datetime.datetime object representing a datetime in UTC.

  Returns:
    The string representation of the date in RFC3339.
  """
  return datetime_obj.isoformat('T') + 'Z'


def _ParseRangeParameterValue(range_value: str) -> Tuple[str, str]:
  """Parse a range parameter value string into its components.

  Args:
    range_value: A range value string of the form "[<start>, <end>)".

  Returns:
    A tuple (<start>, <end>).

  Raises:
    app.UsageError: if the input range value string was not formatted correctly.
  """
  parsed = _ParseRangeString(range_value)
  if parsed is None:
    raise app.UsageError(
        f'Invalid range parameter value: {range_value}. Expected format:'
        ' "[<start>, <end>)"'
    )
  return parsed


def _ParseParameterValue(type_dict, value_input):
  """Parse a parameter value of type `type_dict` from value_input.

  Arguments:
    type_dict: The JSON-dict type as which to parse `value_input`.
    value_input: Either a string representing the value, or a JSON dict for
      array and value types.
  """
  if 'structTypes' in type_dict:
    if isinstance(value_input, str):
      if value_input == 'NULL':
        return {'structValues': None}
      value_input = json.loads(value_input)
    type_map = dict([(x['name'], x['type']) for x in type_dict['structTypes']])
    values = {}
    for (field_name, value) in six.iteritems(value_input):
      values[field_name] = _ParseParameterValue(type_map[field_name], value)
    return {'structValues': values}
  if 'arrayType' in type_dict:
    if isinstance(value_input, str):
      if value_input == 'NULL':
        return {'arrayValues': None}
      try:
        value_input = json.loads(value_input)
      except json.decoder.JSONDecodeError:
        tb = sys.exc_info()[2]
        # pylint: disable=raise-missing-from
        raise app.UsageError(('Error parsing string as JSON: %s') %
                             value_input).with_traceback(tb)
    values = [
        _ParseParameterValue(type_dict['arrayType'], x) for x in value_input
    ]
    if not values:  # Workaround to pass empty array parameter.
      return {'value': {}}  # An empty arrayValues list is the same as NULL.
    return {'arrayValues': values}
  if 'rangeElementType' in type_dict:
    if value_input == 'NULL':
      return {'rangeValue': None}
    start, end = _ParseRangeParameterValue(value_input)
    return {
        'rangeValue': {
            'start': _ParseParameterValue(type_dict['rangeElementType'], start),
            'end': _ParseParameterValue(type_dict['rangeElementType'], end),
        }
    }
  return {'value': value_input if value_input != 'NULL' else None}


def main(unused_argv):
  # Avoid using global flags in main(). In this command line:
  # bq <global flags> <command> <global and local flags> <command args>,
  # only "<global flags>" will parse before main, not "<global and local flags>"


  try:
    _ValidateGlobalFlags()

    bq_commands = {
        # Keep the commands alphabetical.
        'add-iam-policy-binding': _AddIamPolicyBinding,
        'cancel': _Cancel,
        'cp': _Copy,
        'extract': _Extract,
        'get-iam-policy': _GetIamPolicy,
        'head': _Head,
        'info': _Info,
        'init': _Init,
        'insert': _Insert,
        'load': _Load,
        'ls': _List,
        'mk': _Make,
        'mkdef': _MakeExternalTableDefinition,
        'partition': _Partition,
        'query': _Query,
        'remove-iam-policy-binding': _RemoveIamPolicyBinding,
        'rm': _Delete,
        'set-iam-policy': _SetIamPolicy,
        'shell': _Repl,
        'show': _Show,
        'truncate': _Truncate,
        'update': _Update,
        'version': _Version,
        'wait': _Wait,
    }

    for command, function in six.iteritems(bq_commands):
      if command not in appcommands.GetCommandList():
        appcommands.AddCmd(command, function)

  except KeyboardInterrupt as e:
    print('Control-C pressed, exiting.')
    sys.exit(1)
  except BaseException as e:  # pylint: disable=broad-except
    print('Error initializing bq client: %s' % (e,))
    # Use global flags if they're available, but we're exitting so we can't
    # count on global flag parsing anyways.
    if FLAGS.debug_mode or FLAGS.headless:
      traceback.print_exc()
      if not FLAGS.headless:
        pdb.post_mortem()
    sys.exit(1)


# pylint: disable=g-bad-name
def run_main():
  """Function to be used as setuptools script entry point.

  Appcommands assumes that it always runs as __main__, but launching
  via a setuptools-generated entry_point breaks this rule. We do some
  trickery here to make sure that appcommands and flags find their
  state where they expect to by faking ourselves as __main__.
  """

  # Put the flags for this module somewhere the flags module will look
  # for them.
  new_name = sys.argv[0]
  sys.modules[new_name] = sys.modules['__main__']
  for flag in FLAGS.flags_by_module_dict().get(__name__, []):
    FLAGS.register_flag_by_module(new_name, flag)
    for key_flag in FLAGS.key_flags_by_module_dict().get(__name__, []):
      FLAGS.register_key_flag_for_module(new_name, key_flag)

  # Now set __main__ appropriately so that appcommands will be
  # happy.
  sys.modules['__main__'] = sys.modules[__name__]
  appcommands.Run()
  sys.modules['__main__'] = sys.modules.pop(new_name)


if __name__ == '__main__':
  appcommands.Run()
