# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""A shared library for processing and validating Android test arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import arg_file
from googlecloudsdk.api_lib.firebase.test import arg_util
from googlecloudsdk.api_lib.firebase.test import arg_validate
from googlecloudsdk.api_lib.firebase.test.android import catalog_manager
from googlecloudsdk.calliope import exceptions


def TypedArgRules():
  """Returns the rules for Android test args which depend on the test type.

  This dict is declared in a function rather than globally to avoid garbage
  collection issues during unit tests.

  Returns:
    A dict keyed by whether type-specific args are required or optional, and
    with a nested dict containing any default values for those args.
  """
  return {
      'instrumentation': {
          'required': ['test'],
          'optional': [
              'num_uniform_shards', 'test_targets_for_shard', 'test_package',
              'test_runner_class', 'test_targets', 'use_orchestrator'
          ],
          'defaults': {}
      },
      'robo': {
          'required': [],
          'optional': ['robo_directives', 'robo_script', 'resign'],
          'defaults': {
              'resign': True,
          }
      },
      'game-loop': {
          'required': [],
          'optional': ['scenario_numbers', 'scenario_labels'],
          'defaults': {}
      },
  }


def SharedArgRules():
  """Returns the rules for Android test args which are shared by all test types.

  This dict is declared in a function rather than globally to avoid garbage
  collection issues during unit tests.

  Returns:
    A dict keyed by whether shared args are required or optional, and with a
    nested dict containing any default values for those shared args.
  """
  return {
      'required': ['type', 'app'],
      'optional': [
          'additional_apks',
          'app_package',
          'async_',
          'auto_google_login',
          'client_details',
          'device',
          'device_ids',
          'directories_to_pull',
          'environment_variables',
          'grant_permissions',
          'locales',
          'network_profile',
          'num_flaky_test_attempts',
          'obb_files',
          'orientations',
          'os_version_ids',
          'other_files',
          'performance_metrics',
          'record_video',
          'results_bucket',
          'results_dir',
          'results_history_name',
          'timeout',
      ],
      'defaults': {
          'async_': False,
          'auto_google_login': True,
          'num_flaky_test_attempts': 0,
          'performance_metrics': True,
          'record_video': True,
          'timeout': 900,  # 15 minutes
          'grant_permissions': 'all',
      }
  }


def AllArgsSet():
  """Returns a set containing the names of every Android test arg."""
  return arg_util.GetSetOfAllTestArgs(TypedArgRules(), SharedArgRules())


class AndroidArgsManager(object):
  """Manages test arguments for Android devices."""

  def __init__(self,
               catalog_mgr=None,
               typed_arg_rules=None,
               shared_arg_rules=None):
    """Constructs an AndroidArgsManager for a single Android test matrix.

    Args:
      catalog_mgr: an AndroidCatalogManager object.
      typed_arg_rules: a nested dict of dicts which are keyed first on the test
        type, then by whether args are required or optional, and what their
        default values are. If None, the default from TypedArgRules() is used.
      shared_arg_rules: a dict keyed by whether shared args are required or
        optional, and with a nested dict containing any default values for those
        shared args. If None, the default dict from SharedArgRules() is used.
    """
    self._catalog_mgr = catalog_mgr or catalog_manager.AndroidCatalogManager()
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
    self._CheckForConflictingArgs(args)

    typed_arg_defaults = self._typed_arg_rules[test_type]['defaults']
    shared_arg_defaults = self._shared_arg_rules['defaults']
    arg_util.ApplyLowerPriorityArgs(args, typed_arg_defaults)
    arg_util.ApplyLowerPriorityArgs(args, shared_arg_defaults)
    self._ApplyLegacyMatrixDimensionDefaults(args)

    arg_validate.ValidateArgsForTestType(args, test_type, self._typed_arg_rules,
                                         self._shared_arg_rules,
                                         all_test_args_set)
    arg_validate.ValidateOsVersions(args, self._catalog_mgr)
    arg_validate.ValidateDeviceList(args, self._catalog_mgr)
    arg_validate.ValidateResultsBucket(args)
    arg_validate.ValidateResultsDir(args)
    arg_validate.NormalizeAndValidateObbFileNames(args.obb_files)
    arg_validate.ValidateRoboDirectivesList(args)
    arg_validate.ValidateEnvironmentVariablesList(args)
    arg_validate.ValidateTestTargetsForShard(args)
    arg_validate.NormalizeAndValidateDirectoriesToPullList(
        args.directories_to_pull)
    arg_validate.ValidateScenarioNumbers(args)

  def GetTestTypeOrRaise(self, args):
    """If the test type is not user-specified, infer the most reasonable value.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        gcloud command invocation (i.e. group and command arguments combined).

    Returns:
      The type of the test to be run (e.g. 'robo' or 'instrumentation') and
      sets the 'type' arg if it was not user-specified.

    Raises:
      InvalidArgumentException if an explicit test type is invalid.
    """
    if not args.type:
      args.type = 'instrumentation' if args.test else 'robo'
    if args.type not in self._typed_arg_rules:
      raise exceptions.InvalidArgumentException(
          'type', "'{0}' is not a valid test type.".format(args.type))
    return args.type

  def _CheckForConflictingArgs(self, args):
    """Check for any args that cannot appear simultaneously."""
    if args.device:
      # If using sparse matrix syntax, can't also use legacy dimension flags.
      if args.device_ids:
        raise exceptions.ConflictingArgumentsException('--device-ids',
                                                       '--device')
      if args.os_version_ids:
        raise exceptions.ConflictingArgumentsException('--os-version-ids',
                                                       '--device')
      if args.locales:
        raise exceptions.ConflictingArgumentsException('--locales', '--device')
      if args.orientations:
        raise exceptions.ConflictingArgumentsException('--orientations',
                                                       '--device')

  def _ApplyLegacyMatrixDimensionDefaults(self, args):
    """Apply defaults to each dimension flag only if not using sparse matrix."""
    if args.device:
      return
    # If --device is unset and all of the legacy dimension flags are unset,
    # then we want to use --device by default. So don't apply any defaults to
    # the legacy dimension flags here, which would cause conflicting args.
    if not (args.device_ids or args.os_version_ids or args.locales or
            args.orientations):
      args.device = [{}]  # Default device dimensions will be filled in later.
      return

    if not args.device_ids:
      args.device_ids = [self._catalog_mgr.GetDefaultModel()]
    if not args.os_version_ids:
      args.os_version_ids = [self._catalog_mgr.GetDefaultVersion()]
    if not args.locales:
      args.locales = [self._catalog_mgr.GetDefaultLocale()]
    if not args.orientations:
      args.orientations = [self._catalog_mgr.GetDefaultOrientation()]
