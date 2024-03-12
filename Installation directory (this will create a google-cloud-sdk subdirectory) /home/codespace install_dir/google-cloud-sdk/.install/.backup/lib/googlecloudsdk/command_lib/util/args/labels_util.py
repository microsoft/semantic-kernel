# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Module for labels API support.

Typical usage (create command):

  # When defining arguments
  labels_util.AddCreateLabelsFlags(parser)
  # When running the command
  new_resource.labels = labels_util.ParseCreateArgs(args, labels_cls)
  Create(..., new_resource)

Typical usage (update command):

  # When defining arguments
  labels_util.AddUpdateLabelsFlags(parser)

  # When running the command
  labels_diff = labels_util.Diff.FromUpdateArgs(args)
  if labels_diff.MayHaveUpdates():
    orig_resource = Get(...)  # to prevent unnecessary Get calls
    labels_update = labels_diff.Apply(labels_cls, orig_resource.labels)
    if labels_update.needs_update:
      new_resource.labels = labels_update.labels
      field_mask.append('labels')
  Update(..., new_resource)

  # Or alternatively, when running the command
  labels_update = labels_util.ProcessUpdateArgsLazy(
    args, labels_cls, lambda: Get(...).labels)
  if labels_update.needs_update:
    new_resource.labels = labels_update.labels
    field_mask.append('labels')
  Update(..., new_resource)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions

import six


def _IsLower(c):
  """Returns True if c is lower case or a caseless ideograph."""
  return c.isalpha() and (c.islower() or not c.isupper())


def _IsValueOrSubsequent(c):
  """Returns True if c is a valid value or subsequent (not first) character."""
  return c in ('_', '-') or c.isdigit() or _IsLower(c)


def IsValidLabelValue(value):
  r"""Implements the PCRE r'[\p{Ll}\p{Lo}\p{N}_-]{0,63}'.

  Only hyphens (-), underscores (_), lowercase characters, and numbers are
  allowed. International characters are allowed.

  Args:
    value: The label value, a string.

  Returns:
    True is the value is valid; False if not.
  """
  if value is None or len(value) > 63:
    return False
  return all(_IsValueOrSubsequent(c) for c in value)


def IsValidLabelKey(key):
  r"""Implements the PCRE r'[\p{Ll}\p{Lo}][\p{Ll}\p{Lo}\p{N}_-]{0,62}'.

  The key must start with a lowercase character and must be a valid label value.

  Args:
    key: The label key, a string.

  Returns:
    True if the key is valid; False if not.
  """
  if not key or not _IsLower(key[0]):
    return False
  return IsValidLabelValue(key)


_KEY_FORMAT_ERROR = (
    'Only hyphens (-), underscores (_), lowercase characters, and numbers are '
    'allowed. Keys must start with a lowercase character. International '
    'characters are allowed. Key length must not exceed 63 characters.')
KEY_FORMAT_HELP = (
    'Keys must start with a lowercase character and contain only hyphens '
    '(`-`), underscores (```_```), lowercase characters, and numbers.')

_VALUE_FORMAT_ERROR = (
    'Only hyphens (-), underscores (_), lowercase characters, and numbers are '
    'allowed. International characters are allowed.')
VALUE_FORMAT_HELP = (
    'Values must contain only hyphens (`-`), underscores (```_```), lowercase '
    'characters, and numbers.')

KEY_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    IsValidLabelKey, _KEY_FORMAT_ERROR)

VALUE_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    IsValidLabelValue, _VALUE_FORMAT_ERROR)


def GetCreateLabelsFlag(extra_message='', labels_name='labels',
                        validate_keys=True, validate_values=True):
  """Makes the base.Argument for --labels flag."""
  key_type = KEY_FORMAT_VALIDATOR if validate_keys else None
  value_type = VALUE_FORMAT_VALIDATOR if validate_values else None
  format_help = []
  if validate_keys:
    format_help.append(KEY_FORMAT_HELP)
  if validate_values:
    format_help.append(VALUE_FORMAT_HELP)
  help_parts = ['List of label KEY=VALUE pairs to add.']
  if format_help:
    help_parts.append(' '.join(format_help))
  if extra_message:
    help_parts.append(extra_message)

  return base.Argument(
      '--{}'.format(labels_name),
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(
          key_type=key_type, value_type=value_type),
      action=arg_parsers.UpdateAction,
      help=('\n\n'.join(help_parts)))


def GetClearLabelsFlag(labels_name='labels'):
  return base.Argument(
      '--clear-{}'.format(labels_name),
      action='store_true',
      help="""\
          Remove all labels. If `--update-{labels}` is also specified then
          `--clear-{labels}` is applied first.

          For example, to remove all labels:

              $ {{command}} --clear-{labels}

          To remove all existing labels and create two new labels,
          ``foo'' and ``baz'':

              $ {{command}} --clear-{labels} --update-{labels} foo=bar,baz=qux
          """.format(labels=labels_name))


def GetUpdateLabelsFlag(extra_message, labels_name='labels',
                        validate_keys=True, validate_values=True):
  """Makes a base.Argument for the `--update-labels` flag."""
  key_type = KEY_FORMAT_VALIDATOR if validate_keys else None
  value_type = VALUE_FORMAT_VALIDATOR if validate_values else None
  format_help = []
  if validate_keys:
    format_help.append(KEY_FORMAT_HELP)
  if validate_values:
    format_help.append(VALUE_FORMAT_HELP)
  help_parts = [
      ('List of label KEY=VALUE pairs to update. If a label exists, its value '
       'is modified. Otherwise, a new label is created.')]
  if format_help:
    help_parts.append(' '.join(format_help))
  if extra_message:
    help_parts.append(extra_message)

  return base.Argument(
      '--update-{}'.format(labels_name),
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(
          key_type=key_type, value_type=value_type),
      action=arg_parsers.UpdateAction,
      help='\n\n'.join(help_parts))


def GetRemoveLabelsFlag(extra_message, labels_name='labels'):
  return base.Argument(
      '--remove-{}'.format(labels_name),
      metavar='KEY',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help="""\
      List of label keys to remove. If a label does not exist it is
      silently ignored. If `--update-{labels}` is also specified then
      `--update-{labels}` is applied first.""".format(labels=labels_name) +
      extra_message)


def AddCreateLabelsFlags(parser):
  """Adds create command labels flags to an argparse parser.

  Args:
    parser: The argparse parser to add the flags to.
  """
  GetCreateLabelsFlag().AddToParser(parser)


def AddUpdateLabelsFlags(
    parser, extra_update_message='', extra_remove_message='',
    enable_clear=True):
  """Adds update command labels flags to an argparse parser.

  Args:
    parser: The argparse parser to add the flags to.
    extra_update_message: str, extra message to append to help text for
                          --update-labels flag.
    extra_remove_message: str, extra message to append to help text for
                          --delete-labels flag.
    enable_clear: bool, whether to include the --clear-labels flag.
  """
  GetUpdateLabelsFlag(extra_update_message).AddToParser(parser)
  if enable_clear:
    remove_group = parser.add_mutually_exclusive_group()
    GetClearLabelsFlag().AddToParser(remove_group)
    GetRemoveLabelsFlag(extra_remove_message).AddToParser(remove_group)
  else:
    GetRemoveLabelsFlag(extra_remove_message).AddToParser(parser)


def GetUpdateLabelsDictFromArgs(args):
  """Returns the update labels dict from the parsed args.

  Args:
    args: The parsed args.

  Returns:
    The update labels dict from the parsed args.
  """
  return args.labels if hasattr(args, 'labels') else args.update_labels


def GetRemoveLabelsListFromArgs(args):
  """Returns the remove labels list from the parsed args.

  Args:
    args: The parsed args.

  Returns:
    The remove labels list from the parsed args.
  """
  return args.remove_labels


def GetAndValidateOpsFromArgs(parsed_args):
  """Validates and returns labels specific args for update.

  At least one of --update-labels, --clear-labels or --remove-labels must be
  provided. The --clear-labels flag *must* be a declared argument, whether it
  was specified on the command line or not.

  Args:
    parsed_args: The parsed args.

  Returns:
    (update_labels, remove_labels)
    update_labels contains values from --labels and --update-labels flags
    respectively.
    remove_labels contains values from --remove-labels flag

  Raises:
    RequiredArgumentException: if all labels arguments are absent.
    AttributeError: if the --clear-labels flag is absent.
  """
  diff = Diff.FromUpdateArgs(parsed_args)
  if not diff.MayHaveUpdates():
    raise calliope_exceptions.RequiredArgumentException(
        'LABELS',
        'At least one of --update-labels, --remove-labels, or --clear-labels '
        'must be specified.')

  return diff


def _PackageLabels(labels_cls, labels):
  # Sorted for test stability
  return labels_cls(additionalProperties=[
      labels_cls.AdditionalProperty(key=key, value=value)
      for key, value in sorted(six.iteritems(labels))])


def _GetExistingLabelsDict(labels):
  if not labels:
    return {}
  return {l.key: l.value for l in labels.additionalProperties}


class UpdateResult(object):
  """Result type for Diff application.

  Attributes:
    needs_update: bool, whether the diff resulted in any changes to the existing
      labels proto.
    _labels: LabelsValue, the new populated LabelsValue object. If needs_update
      is False, this is identical to the original LabelValue object.
  """

  def __init__(self, needs_update, labels):
    self.needs_update = needs_update
    self._labels = labels

  @property
  def labels(self):
    """Returns the new labels.

    Raises:
      ValueError: if needs_update is False.
    """
    if not self.needs_update:
      raise ValueError(
          'If no update is needed (self.needs_update == False), '
          'checking labels is unnecessary.')
    return self._labels

  def GetOrNone(self):
    """Returns the new labels if an update is needed or None otherwise.

    NOTE: If this function returns None, make sure not to include the labels
    field in the field mask of the update command. Otherwise, it's possible to
    inadvertently clear the labels on the resource.
    """
    try:
      return self.labels
    except ValueError:
      return None


class Diff(object):
  """A change to the labels on a resource."""

  def __init__(self, additions=None, subtractions=None, clear=False):
    """Initialize a Diff.

    Only one of [subtractions, clear] may be specified.

    Args:
      additions: {str: str}, any label values to be updated
      subtractions: List[str], any labels to be removed
      clear: bool, whether to clear the labels

    Returns:
      Diff.

    Raises:
      ValueError: if both subtractions and clear are specified.
    """
    self._additions = additions or {}
    self._subtractions = subtractions or []
    self._clear = clear
    if self._subtractions and self._clear:
      raise ValueError('Only one of [subtractions, clear] may be specified.')

  def _RemoveLabels(self, existing_labels, new_labels):
    """Remove labels."""
    del existing_labels  # Unused in _RemoveLabels; needed by subclass
    new_labels = new_labels.copy()
    for key in self._subtractions:
      new_labels.pop(key, None)
    return new_labels

  def _ClearLabels(self, existing_labels):
    del existing_labels  # Unused in _ClearLabels; needed by subclass
    return {}

  def _AddLabels(self, new_labels):
    new_labels = new_labels.copy()
    new_labels.update(self._additions)
    return new_labels

  def Apply(self, labels_cls, labels=None):
    """Apply this Diff to the (possibly non-existing) labels.

    First, makes any additions. Then, removes any labels.

    Args:
      labels_cls: type, the LabelsValue class for the resource.
      labels: LabelsValue, the existing LabelsValue object for the original
        resource (or None, which is treated the same as empty labels)

    Returns:
      labels_cls, the instantiated LabelsValue message with the new set up
        labels, or None if there are no changes.
    """
    # Add pre-existing labels.
    existing_labels = _GetExistingLabelsDict(labels)
    new_labels = existing_labels.copy()

    if self._clear:
      new_labels = self._ClearLabels(existing_labels)

    if self._additions:
      new_labels = self._AddLabels(new_labels)

    if self._subtractions:
      new_labels = self._RemoveLabels(existing_labels, new_labels)

    needs_update = new_labels != existing_labels
    return UpdateResult(needs_update, _PackageLabels(labels_cls, new_labels))

  def MayHaveUpdates(self):
    """Returns true if this Diff is non-empty."""
    return any([self._additions, self._subtractions, self._clear])

  @classmethod
  def FromUpdateArgs(cls, args, enable_clear=True):
    """Initializes a Diff based on the arguments in AddUpdateLabelsFlags."""
    if enable_clear:
      clear = args.clear_labels
    else:
      clear = None
    return cls(args.update_labels, args.remove_labels, clear)


def ProcessUpdateArgsLazy(args, labels_cls, orig_labels_thunk):
  """Returns the result of applying the diff constructed from args.

  Lazily fetches the original labels value if needed.

  Args:
    args: argparse.Namespace, the parsed arguments with update_labels,
      remove_labels, and clear_labels
    labels_cls: type, the LabelsValue class for the new labels.
    orig_labels_thunk: callable, a thunk which will return the original labels
      object (of type LabelsValue) when evaluated.

  Returns:
    UpdateResult: the result of applying the diff.

  """
  diff = Diff.FromUpdateArgs(args)
  orig_labels = orig_labels_thunk() if diff.MayHaveUpdates() else None
  return diff.Apply(labels_cls, orig_labels)


def ParseCreateArgs(args, labels_cls, labels_dest='labels'):
  """Initializes labels based on args and the given class."""
  labels = getattr(args, labels_dest)
  if labels is None:
    return None
  return _PackageLabels(labels_cls, labels)


class ExplicitNullificationDiff(Diff):
  """A change to labels for resources where API requires explicit nullification.

  That is, to clear a label {'foo': 'bar'}, you must pass {'foo': None} to the
  API.
  """

  def _RemoveLabels(self, existing_labels, new_labels):
    """Remove labels."""
    new_labels = new_labels.copy()
    for key in self._subtractions:
      if key in existing_labels:
        new_labels[key] = None
      elif key in new_labels:
        del new_labels[key]
    return new_labels

  def _ClearLabels(self, existing_labels):
    return {key: None for key in existing_labels}
