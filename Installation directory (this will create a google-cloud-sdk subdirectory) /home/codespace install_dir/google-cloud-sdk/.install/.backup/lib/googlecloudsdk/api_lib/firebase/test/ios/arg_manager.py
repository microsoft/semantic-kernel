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
"""A shared library for processing and validating iOS test arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import arg_file
from googlecloudsdk.api_lib.firebase.test import arg_util
from googlecloudsdk.api_lib.firebase.test import arg_validate
from googlecloudsdk.api_lib.firebase.test.ios import catalog_manager
from googlecloudsdk.calliope import exceptions


def TypedArgRules():
  """Returns the rules for iOS test args which depend on the test type.

  This dict is declared in a function rather than globally to avoid garbage
  collection issues during unit tests.

  Returns:
    A dict keyed by whether type-specific args are required or optional, and
    with a nested dict containing any default values for those shared args.
  """
  return {
      'xctest': {
          'required': ['test'],
          'optional': [
              'xcode_version',
              'xctestrun_file',
              'test_special_entitlements',
          ],
          'defaults': {
              'test_special_entitlements': False
          }
      },
      'game-loop': {
          'required': ['app'],
          'optional': ['scenario_numbers'],
          'defaults': {
              'scenario_numbers': [1]
          }
      },
      'robo': {
          'required': ['app'],
          'optional': ['test_special_entitlements', 'robo_script'],
          'defaults': {
              'test_special_entitlements': False
          },
      }
  }


def SharedArgRules():
  """Returns the rules for iOS test args which are shared by all test types.

  This dict is declared in a function rather than globally to avoid garbage
  collection issues during unit tests.

  Returns:
    A dict keyed by whether shared args are required or optional, and with a
    nested dict containing any default values for those shared args.
  """
  return {
      'required': ['type'],
      'optional': [
          'additional_ipas',
          'async_',
          'client_details',
          'device',
          'directories_to_pull',
          'network_profile',
          'num_flaky_test_attempts',
          'other_files',
          'record_video',
          'results_bucket',
          'results_dir',
          'results_history_name',
          'timeout',
      ],
      'defaults': {
          'async_': False,
          'device': [{}],  # Default dimensions will come from the iOS catalog.
          'num_flaky_test_attempts': 0,
          'record_video': True,
          'timeout': 900,  # 15 minutes
      }
  }


def AllArgsSet():
  """Returns a set containing the names of every iOS test arg."""
  return arg_util.GetSetOfAllTestArgs(TypedArgRules(), SharedArgRules())


class IosArgsManager(object):
  """Manages test arguments for iOS devices."""

  def __init__(self,
               catalog_mgr=None,
               typed_arg_rules=None,
               shared_arg_rules=None):
    """Constructs an IosArgsManager for a single iOS test matrix.

    Args:
      catalog_mgr: an IosCatalogManager object.
      typed_arg_rules: a nested dict of dicts which are keyed first on the test
        type, then by whether args are required or optional, and what their
        default values are. If None, the default from TypedArgRules() is used.
      shared_arg_rules: a dict keyed by whether shared args are required or
        optional, and with a nested dict containing any default values for those
        shared args. If None, the default dict from SharedArgRules() is used.
    """
    self._catalog_mgr = catalog_mgr or catalog_manager.IosCatalogManager()
    self._typed_arg_rules = typed_arg_rules or TypedArgRules()
    self._shared_arg_rules = shared_arg_rules or SharedArgRules()

  def Prepare(self, args):
    """Load, apply defaults, and perform validation on test arguments.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        gcloud command invocation (i.e. group and command arguments combined).
        Arg values from an optional arg-file and/or arg default values may be
        added to this argparse namespace.

    Raises:
      InvalidArgumentException: If an argument name is unknown, an argument does
        not contain a valid value, or an argument is not valid when used with
        the given type of test.
      RequiredArgumentException: If a required arg is missing.
    """
    all_test_args_set = arg_util.GetSetOfAllTestArgs(self._typed_arg_rules,
                                                     self._shared_arg_rules)
    args_from_file = arg_file.GetArgsFromArgFile(args.argspec,
                                                 all_test_args_set)

    arg_util.ApplyLowerPriorityArgs(args, args_from_file, True)

    test_type = self.GetTestTypeOrRaise(args)
    typed_arg_defaults = self._typed_arg_rules[test_type]['defaults']
    shared_arg_defaults = self._shared_arg_rules['defaults']
    arg_util.ApplyLowerPriorityArgs(args, typed_arg_defaults)
    arg_util.ApplyLowerPriorityArgs(args, shared_arg_defaults)
    arg_validate.ValidateArgsForTestType(args, test_type, self._typed_arg_rules,
                                         self._shared_arg_rules,
                                         all_test_args_set)
    arg_validate.ValidateDeviceList(args, self._catalog_mgr)
    arg_validate.ValidateXcodeVersion(args, self._catalog_mgr)
    arg_validate.ValidateResultsBucket(args)
    arg_validate.ValidateResultsDir(args)
    arg_validate.ValidateScenarioNumbers(args)
    arg_validate.ValidateIosDirectoriesToPullList(args)

  def GetTestTypeOrRaise(self, args):
    """If the test type is not user-specified, infer the most reasonable value.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        gcloud command invocation (i.e. group and command arguments combined).

    Returns:
      The type of the test to be run (e.g. 'xctest'), and also sets the 'type'
      arg if it was not user-specified.

    Raises:
      InvalidArgumentException if an explicit test type is invalid.
    """
    if not args.type:
      args.type = 'xctest'
    if args.type not in self._typed_arg_rules:
      raise exceptions.InvalidArgumentException(
          'type', "'{0}' is not a valid test type.".format(args.type))
    return args.type
