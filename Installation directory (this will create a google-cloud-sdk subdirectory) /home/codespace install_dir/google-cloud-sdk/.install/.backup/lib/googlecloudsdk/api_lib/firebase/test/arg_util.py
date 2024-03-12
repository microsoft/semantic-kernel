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
"""A shared library for processing and validating test arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import arg_file
from googlecloudsdk.api_lib.firebase.test import arg_validate
from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
import six

ANDROID_INSTRUMENTATION_TEST = 'ANDROID INSTRUMENTATION TEST'
ANDROID_ROBO_TEST = 'ANDROID ROBO TEST'
ANDROID_GAME_LOOP_TEST = 'ANDROID GAME-LOOP TEST'
DEPRECATED_DEVICE_DIMENSIONS = 'DEPRECATED DEVICE DIMENSIONS'


def AddCommonTestRunArgs(parser):
  """Register args which are common to all 'gcloud test run' commands.

  Args:
    parser: An argparse parser used to add arguments that follow a command
        in the CLI.
  """
  parser.add_argument(
      'argspec',
      nargs='?',
      completer=arg_file.ArgSpecCompleter,
      help='An ARG_FILE:ARG_GROUP_NAME pair, where ARG_FILE is the path to a '
      'file containing groups of test arguments in yaml format, and '
      'ARG_GROUP_NAME is the particular yaml object holding a group of '
      'arg:value pairs to use. Run *$ gcloud topic arg-files* for more '
      'information and examples.')

  parser.add_argument(
      '--async',
      action='store_true',
      default=None,
      dest='async_',
      help='Invoke a test asynchronously without waiting for test results.')
  parser.add_argument(
      '--client-details',
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE',
      help="""\
      Comma-separated, KEY=VALUE map of additional details to attach to the test
      matrix. Arbitrary KEY=VALUE pairs may be attached to a test matrix to
      provide additional context about the tests being run. When consuming the
      test results, such as in Cloud Functions or a CI system, these details can
      add additional context such as a link to the corresponding pull request.

      Example:

      ```
      --client-details=buildNumber=1234,pullRequest=https://example.com/link/to/pull-request
      ```

      To help you identify and locate your test matrix in the Firebase console,
      use the matrixLabel key.

      Example:

      ```
      --client-details=matrixLabel="Example matrix label"
      ```
      """,
  )
  parser.add_argument(
      '--num-flaky-test-attempts',
      metavar='int',
      type=arg_validate.NONNEGATIVE_INT_PARSER,
      help="""\
      Specifies the number of times a test execution should be reattempted if
      one or more of its test cases fail for any reason. An execution that
      initially fails but succeeds on any reattempt is reported as FLAKY.\n
      The maximum number of reruns allowed is 10. (Default: 0, which implies
      no reruns.) All additional attempts are executed in parallel.
      """,
  )
  parser.add_argument(
      '--record-video',
      action='store_true',
      default=None,
      help='Enable video recording during the test. Enabled by default, use '
      '--no-record-video to disable.')
  parser.add_argument(
      '--results-bucket',
      help='The name of a Google Cloud Storage bucket where raw test results '
      'will be stored (default: "test-lab-<random-UUID>"). Note that the '
      'bucket must be owned by a billing-enabled project, and that using a '
      'non-default bucket will result in billing charges for the storage used.')
  parser.add_argument(
      '--results-dir',
      help='The name of a *unique* Google Cloud Storage object within the '
      'results bucket where raw test results will be stored (default: a '
      'timestamp with a random suffix). Caution: if specified, this argument '
      '*must be unique* for each test matrix you create, otherwise results '
      'from multiple test matrices will be overwritten or intermingled.')
  parser.add_argument(
      '--timeout',
      category=base.COMMONLY_USED_FLAGS,
      type=arg_validate.TIMEOUT_PARSER,
      help='The max time this test execution can run before it is cancelled '
      '(default: 15m). It does not include any time necessary to prepare and '
      'clean up the target device. The maximum possible testing time is 45m '
      'on physical devices and 60m on virtual devices. The _TIMEOUT_ units can '
      'be h, m, or s. If no unit is given, seconds are assumed. Examples:\n'
      '- *--timeout 1h* is 1 hour\n'
      '- *--timeout 5m* is 5 minutes\n'
      '- *--timeout 200s* is 200 seconds\n'
      '- *--timeout 100* is 100 seconds')


def AddAndroidTestArgs(parser):
  """Register args which are specific to Android test commands.

  Args:
    parser: An argparse parser used to add arguments that follow a command in
        the CLI.
  """
  parser.add_argument(
      '--app',
      category=base.COMMONLY_USED_FLAGS,
      help='The path to the application binary file. The path may be in the '
      'local filesystem or in Google Cloud Storage using gs:// notation. '
      'Android App Bundles are specified as .aab, all other files are assumed '
      'to be APKs.')
  parser.add_argument(
      '--app-package',
      action=actions.DeprecationAction('--app-package', removed=True),
      help='The Java package of the application under test. By default, the '
      'application package name is parsed from the APK manifest.')
  parser.add_argument(
      '--additional-apks',
      type=arg_parsers.ArgList(min_length=1, max_length=100),
      metavar='APK',
      help='A list of up to 100 additional APKs to install, in addition to '
      'those being directly tested. The path may be in the local filesystem or '
      'in Google Cloud Storage using gs:// notation.')
  parser.add_argument(
      '--auto-google-login',
      action='store_true',
      default=None,
      help='Automatically log into the test device using a preconfigured '
      'Google account before beginning the test. Enabled by default, use '
      '--no-auto-google-login to disable.')
  parser.add_argument(
      '--directories-to-pull',
      type=arg_parsers.ArgList(),
      metavar='DIR_TO_PULL',
      help='A list of paths that will be copied from the device\'s storage to '
      'the designated results bucket after the test is complete. These must be '
      'absolute paths under `/sdcard`, `/storage`, or `/data/local/tmp` (for '
      'example, '
      '`--directories-to-pull /sdcard/tempDir1,/data/local/tmp/tempDir2`). '
      'Path names are restricted to the characters ```a-zA-Z0-9_-./+```. '
      'The paths `/sdcard` and `/data` will be made available and treated as '
      'implicit path substitutions. E.g. if `/sdcard` on a particular device '
      'does not map to external storage, the system will replace it with the '
      'external storage path prefix for that device. Note that access to some '
      'directories on API levels 29 and later may also be limited by scoped '
      'storage rules.')
  parser.add_argument(
      '--environment-variables',
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE',
      help="""\
      A comma-separated, key=value map of environment variables and their
      desired values. The environment variables are mirrored as extra options to
      the `am instrument -e KEY1 VALUE1 ...` command and passed to your test
      runner (typically AndroidJUnitRunner). Examples:

      Enable code coverage and provide a directory to store the coverage
      results when using Android Test Orchestrator (`--use-orchestrator`):

      ```
      --environment-variables clearPackageData=true,coverage=true,coverageFilePath=/sdcard/Download/
      ```

      Enable code coverage and provide a file path to store the coverage
      results when *not* using Android Test Orchestrator
      (`--no-use-orchestrator`):

      ```
      --environment-variables coverage=true,coverageFile=/sdcard/Download/coverage.ec
      ```

      Note: If you need to embed a comma into a `VALUE` string, please refer to
      `gcloud topic escaping` for ways to change the default list delimiter.
      """)
  parser.add_argument(
      '--network-profile',
      metavar='PROFILE_ID',
      help='The name of the network traffic profile, for example '
      '`--network-profile=LTE`, which consists of a set of parameters to '
      'emulate network conditions when running the test (default: no network '
      'shaping; see available profiles listed by the '
      '$ {grandparent_command} network-profiles list command). '
      'This feature only works on physical devices.')
  parser.add_argument(
      '--obb-files',
      type=arg_parsers.ArgList(min_length=1, max_length=2),
      metavar='OBB_FILE',
      help='A list of one or two Android OBB file names which will be copied '
      'to each test device before the tests will run (default: None). Each '
      'OBB file name must conform to the format as specified by Android (e.g. '
      '[main|patch].0300110.com.example.android.obb) and will be installed '
      'into <shared-storage>/Android/obb/<package-name>/ on the test device.')
  parser.add_argument(
      '--other-files',
      type=arg_parsers.ArgDict(min_length=1),
      metavar='DEVICE_PATH=FILE_PATH',
      help="""\
      A list of device-path=file-path pairs that indicate the device paths to
      push files to the device before starting tests, and the paths of files to
      push.\n
      Device paths must be under absolute, approved paths
      (${EXTERNAL_STORAGE}, or ${ANDROID_DATA}/local/tmp). Source file paths may
      be in the local filesystem or in Google Cloud Storage (gs://...).\n
      Examples:\n
      ```
      --other-files /sdcard/dir1/file1.txt=local/file.txt,/storage/dir2/file2.jpg=gs://bucket/file.jpg
      ```\n
      This flag only copies files to the device. To install files, like OBB or
      APK files, see --obb-files and --additional-apks.
      """)
  parser.add_argument(
      '--performance-metrics',
      action='store_true',
      default=None,
      help='Monitor and record performance metrics: CPU, memory, network usage,'
      ' and FPS (game-loop only). Enabled by default, use '
      '--no-performance-metrics to disable.')
  parser.add_argument(
      '--results-history-name',
      help='The history name for your test results (an arbitrary string label; '
      'default: the application\'s label from the APK manifest). All tests '
      'which use the same history name will have their results grouped '
      'together in the Firebase console in a time-ordered test history list.')
  parser.add_argument(
      '--robo-script',
      category=ANDROID_ROBO_TEST,
      help='The path to a Robo Script JSON file. The path may be in the local '
      'filesystem or in Google Cloud Storage using gs:// notation. You can '
      'guide the Robo test to perform specific actions by recording a Robo '
      'Script in Android Studio and then specifying this argument. Learn more '
      'at https://firebase.google.com/docs/test-lab/robo-ux-test#scripting.')
  parser.add_argument(
      '--type',
      category=base.COMMONLY_USED_FLAGS,
      choices=['instrumentation', 'robo', 'game-loop'],
      help='The type of test to run.')

  # The following args are specific to Android instrumentation tests.

  parser.add_argument(
      '--test',
      category=base.COMMONLY_USED_FLAGS,
      help='The path to the binary file containing instrumentation tests. The '
      'given path may be in the local filesystem or in Google Cloud Storage '
      'using a URL beginning with `gs://`.')
  parser.add_argument(
      '--test-package',
      action=actions.DeprecationAction('--test-package', removed=True),
      category=ANDROID_INSTRUMENTATION_TEST,
      help='The Java package name of the instrumentation test. By default, the '
      'test package name is parsed from the APK manifest.')
  parser.add_argument(
      '--test-runner-class',
      category=ANDROID_INSTRUMENTATION_TEST,
      help='The fully-qualified Java class name of the instrumentation test '
      'runner (default: the last name extracted from the APK manifest).')
  parser.add_argument(
      '--test-targets',
      category=ANDROID_INSTRUMENTATION_TEST,
      type=arg_parsers.ArgList(min_length=1),
      metavar='TEST_TARGET',
      help="""\
      A list of one or more test target filters to apply (default: run all test
      targets). Each target filter must be fully qualified with the package
      name, class name, or test annotation desired. Any test filter supported by
      `am instrument -e ...` is supported. See
       https://developer.android.com/reference/android/support/test/runner/AndroidJUnitRunner
       for more information. Examples:

         * `--test-targets "package com.my.package.name"`
         * `--test-targets "notPackage com.package.to.skip"`
         * `--test-targets "class com.foo.ClassName"`
         * `--test-targets "notClass com.foo.ClassName#testMethodToSkip"`
         * `--test-targets "annotation com.foo.AnnotationToRun"`
         * `--test-targets "size large notAnnotation com.foo.AnnotationToSkip"`
      """)
  parser.add_argument(
      '--use-orchestrator',
      category=ANDROID_INSTRUMENTATION_TEST,
      action='store_true',
      default=None,
      help='Whether each test runs in its own Instrumentation instance with '
      'the Android Test Orchestrator (default: Orchestrator is not used, same '
      'as specifying --no-use-orchestrator). Orchestrator is only compatible '
      'with AndroidJUnitRunner v1.1 or higher. See '
      'https://developer.android.com/training/testing/junit-runner.html'
      '#using-android-test-orchestrator for more information about Android '
      'Test Orchestrator.')

  # The following args are specific to Android Robo tests.

  parser.add_argument(
      '--robo-directives',
      metavar='TYPE:RESOURCE_NAME=INPUT',
      category=ANDROID_ROBO_TEST,
      type=arg_parsers.ArgDict(),
      help='A comma-separated (`<type>:<key>=<value>`) map of '
      '`robo_directives` that you can use to customize the behavior of Robo '
      'test. The `type` specifies the action type of the directive, which may '
      'take on values `click`, `text` or `ignore`. If no `type` is provided, '
      '`text` will be used by default. Each key should be the Android resource '
      'name of a target UI element and each value should be the text input for '
      'that element. Values are only permitted for `text` type elements, so no '
      'value should be specified for `click` and `ignore` type elements. No '
      'more than one `click` element is allowed.'
      '\n\n'
      'To provide custom login credentials for your app, use'
      '\n\n'
      '    --robo-directives text:username_resource=username,'
      'text:password_resource=password'
      '\n\n'
      'To instruct Robo to click on the sign-in button, use'
      '\n\n'
      '    --robo-directives click:sign_in_button='
      '\n\n'
      'To instruct Robo to ignore any UI elements with resource names which '
      'equal or start with the user-defined value, use'
      '\n\n'
      '  --robo-directives ignore:ignored_ui_element_resource_name='
      '\n\n'
      'To learn more about Robo test and robo_directives, see '
      'https://firebase.google.com/docs/test-lab/android/command-line#custom_login_and_text_input_with_robo_test.'
      '\n\n'
      'Caution: You should only use credentials for test accounts that are not '
      'associated with real users.')

  # The following args are specific to Android game-loop tests.

  parser.add_argument(
      '--scenario-numbers',
      metavar='int',
      type=arg_parsers.ArgList(element_type=int, min_length=1, max_length=1024),
      category=ANDROID_GAME_LOOP_TEST,
      help='A list of game-loop scenario numbers which will be run as part of '
      'the test (default: all scenarios). A maximum of 1024 scenarios may be '
      'specified in one test matrix, but the maximum number may also be '
      'limited by the overall test *--timeout* setting.')

  parser.add_argument(
      '--scenario-labels',
      metavar='LABEL',
      type=arg_parsers.ArgList(min_length=1),
      category=ANDROID_GAME_LOOP_TEST,
      help='A list of game-loop scenario labels (default: None). '
      'Each game-loop scenario may be labeled in the APK manifest file with '
      'one or more arbitrary strings, creating logical groupings (e.g. '
      'GPU_COMPATIBILITY_TESTS). If *--scenario-numbers* and '
      '*--scenario-labels* are specified together, Firebase Test Lab will '
      'first execute each scenario from *--scenario-numbers*. It will then '
      'expand each given scenario label into a list of scenario numbers marked '
      'with that label, and execute those scenarios.')


def AddIosTestArgs(parser):
  """Register args which are specific to iOS test commands.

  Args:
    parser: An argparse parser used to add arguments that follow a command in
        the CLI.
  """
  parser.add_argument(
      '--type',
      category=base.COMMONLY_USED_FLAGS,
      choices=['xctest', 'game-loop', 'robo'],
      # TODO(b/260103145): Include links to test documentation
      help='The type of iOS test to run.')
  parser.add_argument(
      '--test',
      category=base.COMMONLY_USED_FLAGS,
      metavar='XCTEST_ZIP',
      help='The path to the test package (a zip file containing the iOS app '
      'and XCTest files). The given path may be in the local filesystem or in '
      'Google Cloud Storage using a URL beginning with `gs://`. Note: any '
      '.xctestrun file in this zip file will be ignored if *--xctestrun-file* '
      'is specified.')
  parser.add_argument(
      '--xctestrun-file',
      category=base.COMMONLY_USED_FLAGS,
      metavar='XCTESTRUN_FILE',
      help='The path to an .xctestrun file that will override any .xctestrun '
      'file contained in the *--test* package. Because the .xctestrun file '
      'contains environment variables along with test methods to run and/or '
      'ignore, this can be useful for customizing or sharding test suites. The '
      'given path may be in the local filesystem or in Google Cloud Storage '
      'using a URL beginning with `gs://`.')
  parser.add_argument(
      '--xcode-version',
      category=base.COMMONLY_USED_FLAGS,
      help="""\
      The version of Xcode that should be used to run an XCTest. Defaults to the
      latest Xcode version supported in Firebase Test Lab. This Xcode version
      must be supported by all iOS versions selected in the test matrix. The
      list of Xcode versions supported by each version of iOS can be viewed by
      running `$ {parent_command} versions list`.""")
  parser.add_argument(
      '--device',
      category=base.COMMONLY_USED_FLAGS,
      type=arg_parsers.ArgDict(min_length=1),
      action='append',
      metavar='DIMENSION=VALUE',
      help="""\
      A list of ``DIMENSION=VALUE'' pairs which specify a target device to test
      against. This flag may be repeated to specify multiple devices. The device
      dimensions are: *model*, *version*, *locale*, and *orientation*. If any
      dimensions are omitted, they will use a default value. The default value,
      and all possible values, for each dimension can be found with the
      ``list'' command for that dimension, such as `$ {parent_command} models
      list`. Omitting this flag entirely will run tests against a single device
      using defaults for every dimension.

      Examples:\n
      ```
      --device model=iphone8plus
      --device version=11.2
      --device model=ipadmini4,version=11.2,locale=zh_CN,orientation=landscape
      ```
      """)
  parser.add_argument(
      '--results-history-name',
      help='The history name for your test results (an arbitrary string label; '
      'default: the bundle ID for the iOS application). All tests '
      'which use the same history name will have their results grouped '
      'together in the Firebase console in a time-ordered test history list.')
  parser.add_argument(
      '--app',
      help='The path to the application archive (.ipa file) for game-loop '
           'testing. The path may be in the local filesystem or in Google '
           'Cloud Storage using gs:// notation. This flag is only valid when '
           '*--type* is *game-loop* or *robo*.'
  )

  # The following args are specific to iOS xctest tests.
  parser.add_argument(
      '--test-special-entitlements',
      action='store_true',
      default=None,
      help="""\
      Enables testing special app entitlements. Re-signs an app having special
      entitlements with a new application-identifier. This currently supports
      testing Push Notifications (aps-environment) entitlement for up to one
      app in a project.

      Note: Because this changes the app's identifier, make sure none of the
      resources in your zip file contain direct references to the test app's
      bundle id.
      """)


def AddBetaArgs(parser):
  """Register args which are only available in the beta run commands.

  Args:
    parser: An argparse parser used to add args that follow a command.
  """
  del parser  # Unused by AddBetaArgs


def AddGaArgs(parser):
  """Register args which are only available in the GA run command.

  Args:
    parser: An argparse parser used to add args that follow a command.
  """
  del parser  # Unused by AddGaArgs


def AddAndroidBetaArgs(parser):
  """Register args which are only available in the Android beta run command.

  Args:
    parser: An argparse parser used to add args that follow a command.
  """
  # Mutually exclusive sharding options group.
  sharding_options = parser.add_group(mutex=True, help='Sharding options.')
  sharding_options.add_argument(
      '--num-uniform-shards',
      metavar='int',
      type=arg_validate.POSITIVE_INT_PARSER,
      help="""\
      Specifies the number of shards across which to distribute test cases. The
      shards are run in parallel on separate devices. For example, if your test
      execution contains 20 test cases and you specify four shards, the
      instrumentation command passes arguments of `-e numShards 4` to
      AndroidJUnitRunner and each shard executes about five test cases. Based on
      the sharding mechanism AndroidJUnitRunner uses, there is no guarantee that
      test cases will be distributed with perfect uniformity.

      The number of shards specified must always be a positive number that is no
      greater than the total number of test cases. When you select one or more
      physical devices, the number of shards specified must be <= 50. When you
      select one or more Arm virtual devices, the number of shards specified
      must be <= 200. When you select only x86 virtual devices, the number of
      shards specified must be <= 500.
      """)
  sharding_options.add_argument(
      '--test-targets-for-shard',
      metavar='TEST_TARGETS_FOR_SHARD',
      action='append',
      help="""\
      Specifies a group of packages, classes, and/or test cases to run in
      each shard (a group of test cases). Each time this flag is repeated, it
      creates a new shard. The shards are run in parallel on separate devices.
      You can repeat this flag up to 50 times when you select one or more
      physical devices, up to 200 times when you select one or more Arm virtual
      devices, and up to 500 times when you select only x86 virtual devices.

      Note: If you include the flags *--environment-variable* or
      *--test-targets* when running *--test-targets-for-shard*, the former flags
      are applied to all of the shards you create.

      Examples:

      You can also specify multiple packages, classes, or test cases in the
      same shard by separating each item with a comma. For example:

      ```
      --test-targets-for-shard
      "package com.package1.for.shard1,com.package2.for.shard1"
      ```

      ```
      --test-targets-for-shard
      "class com.foo.ClassForShard2#testMethod1,com.foo.ClassForShard2#testMethod2"
      ```

      To specify both package and class in the same shard, separate `package`
      and `class` with semicolons:

      ```
      --test-targets-for-shard
      "class com.foo.ClassForShard3;package com.package.for.shard3"
      ```
      """)
  parser.add_argument(
      '--grant-permissions',
      metavar='PERMISSIONS',
      help='Whether to grant runtime permissions on the device before the test '
      'begins. By default, all permissions are granted.',
      default=None,
      choices=['all', 'none'])
  parser.add_argument(
      '--resign',
      category=ANDROID_ROBO_TEST,
      action='store_true',
      default=None,
      help='Make Robo re-sign the app-under-test APK for a higher quality '
      'crawl. If your app cannot properly function when re-signed, disable '
      'this feature. When an app-under-test APK is not re-signed, Robo crawl '
      'is slower and Robo has access to less information about the state of '
      'the crawled app, which reduces crawl quality. Consequently, if your '
      'Roboscript has actions on elements of RecyclerView or AdapterView, and '
      'you disable APK re-signing, those actions might require manual tweaking '
      'because Robo does not identify RecyclerView and AdapterView in this '
      'mode. Enabled by default, use `--no-resign` to disable.')


def AddIosBetaArgs(parser):
  """Register args which are only available in the iOS beta run command.

  Args:
    parser: An argparse parser used to add args that follow a command.
  """
  parser.add_argument(
      '--additional-ipas',
      type=arg_parsers.ArgList(min_length=1, max_length=100),
      metavar='IPA',
      help='List of up to 100 additional IPAs to install, in addition to '
      'the one being directly tested. The path may be in the local filesystem '
      'or in Google Cloud Storage using gs:// notation.')
  parser.add_argument(
      '--other-files',
      type=arg_parsers.ArgDict(min_length=1),
      metavar='DEVICE_PATH=FILE_PATH',
      help="""\
      A list of device-path=file-path pairs that specify the paths of the test
      device and the files you want pushed to the device prior to testing.\n
      Device paths should either be under the Media shared folder (e.g. prefixed
      with /private/var/mobile/Media) or within the documents directory of the
      filesystem of an app under test (e.g. /Documents). Device paths to app
      filesystems should be prefixed by the bundle ID and a colon. Source file
      paths may be in the local filesystem or in Google Cloud Storage
      (gs://...).\n
      Examples:\n
      ```
      --other-files com.my.app:/Documents/file.txt=local/file.txt,/private/var/mobile/Media/file.jpg=gs://bucket/file.jpg
      ```
      """)
  parser.add_argument(
      '--directories-to-pull',
      type=arg_parsers.ArgList(),
      metavar='DIR_TO_PULL',
      help="""\
      A list of paths that will be copied from the device\'s storage to
      the designated results bucket after the test is complete. These must be
      absolute paths under `/private/var/mobile/Media` or `/Documents` of the
      app under test. If the path is under an app\'s `/Documents`, it must be
      prefixed with the app\'s bundle id and a colon.\n
      Example:\n
      ```
      --directories-to-pull=com.my.app:/Documents/output,/private/var/mobile/Media/output
      ```
      """)

  # The following args are specific to iOS game-loop tests.

  parser.add_argument(
      '--scenario-numbers',
      metavar='int',
      type=arg_parsers.ArgList(element_type=int, min_length=1, max_length=1024),
      help='A list of game-loop scenario numbers which will be run as part of '
           'the test (default: scenario 1). A maximum of 1024 scenarios may be '
           'specified in one test matrix, but the maximum number may also be '
           'limited by the overall test *--timeout* setting. This flag is only '
           'valid when *--type=game-loop* is also set.'
  )

  # The following args are specific to iOS Robo tests.

  parser.add_argument(
      '--robo-script',
      help="""\
      The path to a Robo Script JSON file. The path may be in the local
      filesystem or in Google Cloud Storage using gs:// notation. You can
      guide the Robo test to perform specific actions by specifying a Robo
      Script with this argument. Learn more at
      https://firebase.google.com/docs/test-lab/robo-ux-test#scripting.
      This flag is only valid when *--type=robo* is also set.
      """)


def AddMatrixArgs(parser):
  """Register the repeatable args which define the axes for a test matrix.

  Args:
    parser: An argparse parser used to add arguments that follow a command
        in the CLI.
  """
  parser.add_argument(
      '--device',
      category=base.COMMONLY_USED_FLAGS,
      type=arg_parsers.ArgDict(min_length=1),
      action='append',
      metavar='DIMENSION=VALUE',
      help="""\
      A list of ``DIMENSION=VALUE'' pairs which specify a target device to test
      against. This flag may be repeated to specify multiple devices. The four
      device dimensions are: *model*, *version*, *locale*, and *orientation*. If
      any dimensions are omitted, they will use a default value. The default
      value, and all possible values, for each dimension can be found with the
      ``list'' command for that dimension, such as `$ {parent_command} models
      list`. *--device* is now the preferred way to specify test devices and may
      not be used in conjunction with *--devices-ids*, *--os-version-ids*,
      *--locales*, or *--orientations*. Omitting all of the preceding
      dimension-related flags will run tests against a single device using
      defaults for all four device dimensions.

      Examples:\n
      ```
      --device model=Nexus6
      --device version=23,orientation=portrait
      --device model=shamu,version=22,locale=zh_CN,orientation=default
      ```
      """)
  parser.add_argument(
      '--device-ids',
      '-d',
      category=DEPRECATED_DEVICE_DIMENSIONS,
      type=arg_parsers.ArgList(min_length=1),
      metavar='MODEL_ID',
      help='The list of MODEL_IDs to test against (default: one device model '
      'determined by the Firebase Test Lab device catalog; see TAGS listed '
      'by the `$ {parent_command} models list` command).')
  parser.add_argument(
      '--os-version-ids',
      '-v',
      category=DEPRECATED_DEVICE_DIMENSIONS,
      type=arg_parsers.ArgList(min_length=1),
      metavar='OS_VERSION_ID',
      help='The list of OS_VERSION_IDs to test against (default: a version ID '
      'determined by the Firebase Test Lab device catalog).')
  parser.add_argument(
      '--locales',
      '-l',
      category=DEPRECATED_DEVICE_DIMENSIONS,
      type=arg_parsers.ArgList(min_length=1),
      metavar='LOCALE',
      help='The list of LOCALEs to test against (default: a single locale '
      'determined by the Firebase Test Lab device catalog).')
  parser.add_argument(
      '--orientations',
      '-o',
      category=DEPRECATED_DEVICE_DIMENSIONS,
      type=arg_parsers.ArgList(
          min_length=1, max_length=2, choices=arg_validate.ORIENTATION_LIST),
      completer=arg_parsers.GetMultiCompleter(OrientationsCompleter),
      metavar='ORIENTATION',
      help='The device orientation(s) to test against (default: portrait). '
      'Specifying \'default\' will pick the preferred orientation '
      'for the app.')


def OrientationsCompleter(prefix, unused_parsed_args, unused_kwargs):
  return [p for p in arg_validate.ORIENTATION_LIST if p.startswith(prefix)]


def GetSetOfAllTestArgs(type_rules, shared_rules):
  """Build a set of all possible 'gcloud test run' args.

  We need this set to test for invalid arg combinations because gcloud core
  adds many args to our args.Namespace that we don't care about and don't want
  to validate. We also need this to validate args coming from an arg-file.

  Args:
    type_rules: a nested dictionary defining the required and optional args
      per type of test, plus any default values.
    shared_rules: a nested dictionary defining the required and optional args
      shared among all test types, plus any default values.

  Returns:
    A set of strings for every gcloud-test argument.
  """
  all_test_args_list = (
      shared_rules['required'] + shared_rules['optional'] + list(
          shared_rules['defaults'].keys()))
  for type_dict in type_rules.values():
    all_test_args_list += (
        type_dict['required'] + type_dict['optional'] + list(
            type_dict['defaults'].keys()))
  return set(all_test_args_list)


def ApplyLowerPriorityArgs(args, lower_pri_args, issue_cli_warning=False):
  """Apply lower-priority arg values from a dictionary to args without values.

  May be used to apply arg default values, or to merge args from another source,
  such as an arg-file. Args which already have a value are never modified by
  this function. Thus, if there are multiple sets of lower-priority args, they
  should be applied in order from highest-to-lowest precedence.

  Args:
    args: the existing argparse.Namespace. All the arguments that were provided
      to the command invocation (i.e. group and command arguments combined),
      plus any arg defaults already applied to the namespace. These args have
      higher priority than the lower_pri_args.
    lower_pri_args: a dict mapping lower-priority arg names to their values.
    issue_cli_warning: (boolean) issue a warning if an arg already has a value
      from the command line and we do not apply the lower-priority arg value
      (used for arg-files where any args specified in the file are lower in
      priority than the CLI args.).
  """
  for arg in lower_pri_args:
    if getattr(args, arg, None) is None:
      log.debug('Applying default {0}: {1}'
                .format(arg, six.text_type(lower_pri_args[arg])))
      setattr(args, arg, lower_pri_args[arg])
    elif issue_cli_warning and getattr(args, arg) != lower_pri_args[arg]:
      ext_name = exceptions.ExternalArgNameFrom(arg)
      log.warning(
          'Command-line argument "--{0} {1}" overrides file argument "{2}: {3}"'
          .format(ext_name,
                  _FormatArgValue(getattr(args, arg)), ext_name,
                  _FormatArgValue(lower_pri_args[arg])))


def _FormatArgValue(value):
  if isinstance(value, list):
    return ' '.join(value)
  else:
    return six.text_type(value)
