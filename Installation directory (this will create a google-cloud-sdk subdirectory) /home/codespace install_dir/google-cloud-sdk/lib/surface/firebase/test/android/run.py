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
"""The 'gcloud firebase test android run' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import arg_util
from googlecloudsdk.api_lib.firebase.test import ctrl_c_handler
from googlecloudsdk.api_lib.firebase.test import exit_code
from googlecloudsdk.api_lib.firebase.test import history_picker
from googlecloudsdk.api_lib.firebase.test import matrix_ops
from googlecloudsdk.api_lib.firebase.test import results_bucket
from googlecloudsdk.api_lib.firebase.test import results_summary
from googlecloudsdk.api_lib.firebase.test import tool_results
from googlecloudsdk.api_lib.firebase.test import util
from googlecloudsdk.api_lib.firebase.test.android import arg_manager
from googlecloudsdk.api_lib.firebase.test.android import matrix_creator
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
import six

_APK_MIME_TYPE = 'application/vnd.android.package-archive'


@base.UnicodeIsSupported
class _BaseRun(object):
  """Invoke a test in Firebase Test Lab for Android and view test results."""

  detailed_help = {
      'DESCRIPTION': """
          *{command}* invokes and monitors tests in Firebase Test Lab for
          Android.

          Three main types of Android tests are currently supported:
          - *robo*: runs a smart, automated exploration of the activities in
            your Android app which records any installation failures or crashes
            and builds an activity map with associated screenshots and video.
          - *instrumentation*: runs automated unit or integration tests written
            using a testing framework. Firebase Test Lab for Android currently
            supports the Espresso and UI Automator 2.0 testing
            frameworks.
          - *game-loop*: executes a special intent built into the game app (a
            "demo mode") that simulates the actions of a real player. This test
            type can include multiple game loops (also called "scenarios"),
            which can be logically organized using scenario labels so that you
            can run related loops together. Refer to
            https://firebase.google.com/docs/test-lab/android/game-loop for
            more information about how to build and run Game Loop tests.

          The type of test to run can be specified with the *--type* flag,
          although the type can often be inferred from other flags.
          Specifically, if the *--test* flag is present, the test *--type*
          defaults to `instrumentation`. If *--test* is not present, then
          *--type* defaults to `robo`.

          All arguments for *{command}* may be specified on the command line
          and/or within an argument file. Run *$ gcloud topic arg-files* for
          more information about argument files.
          """,
      'EXAMPLES': """
          To invoke a robo test lasting 100 seconds against the default device
          environment, run:

            $ {command} --app=APP_APK --timeout=100s

          When specifying devices to test against, the preferred method is to
          use the --device flag. For example, to invoke a robo test against a
          virtual, generic MDPI Nexus device in landscape orientation, run:

            $ {command} --app=APP_APK --device=model=NexusLowRes,orientation=landscape

          To invoke an instrumentation test against a physical Nexus 6 device
          (MODEL_ID: shamu) which is running Android API level 21 in French, run:

            $ {command} --app=APP_APK --test=TEST_APK --device=model=shamu,version=21,locale=fr

          To test against multiple devices, specify --device more than once:

            $ {command} --app=APP_APK --test=TEST_APK --device=model=Nexus4,version=19 --device=model=Nexus4,version=21 --device=model=NexusLowRes,version=25

          To invoke a robo test on an Android App Bundle, pass the .aab file
          using the --app flag.

            $ {command} --app=bundle.aab

          You may also use the legacy dimension flags (deprecated) to specify
          which devices to use. Firebase Test Lab will run tests against every
          possible combination of the listed device dimensions. Note that some
          combinations of device models and OS versions may not be valid or
          available in Test Lab. Any unsupported combinations of dimensions in
          the test matrix will be skipped.

          For example, to execute a series of 5-minute robo tests against a very
          comprehensive matrix of virtual and physical devices, OS versions,
          locales and orientations, run:

            $ {command} --app=APP_APK --timeout=5m --device-ids=shamu,NexusLowRes,Nexus5,g3,zeroflte --os-version-ids=19,21,22,23,24,25 --locales=en_GB,es,fr,ru,zh --orientations=portrait,landscape

          The above command will generate a test matrix with a total of 300 test
          executions, but only the subset of executions with valid dimension
          combinations will actually run your tests.

          To help you identify and locate your test matrix in the Firebase
          console, run:

            $ {command} --app=APP_APK --client-details=matrixLabel="Example matrix label"

          Controlling Results Storage

          By default, Firebase Test Lab stores detailed test results for a
          limited time in a Google Cloud Storage bucket provided for you at
          no charge. If you wish to use a storage bucket that you control, or
          if you need to retain detailed test results for a longer period,
          use the *--results-bucket* option. See
          https://firebase.google.com/docs/test-lab/analyzing-results#detailed
          for more information.

          Detailed test result files are prefixed by default with a timestamp
          and a random character string. If you require a predictable path
          where detailed test results are stored within the results bucket
          (say, if you have a Continuous Integration system which does custom
          post-processing of test result artifacts), use the *--results-dir*
          option. _Note that each test invocation *must* have a unique storage
          location, so never reuse the same value for *--results-dir* between
          different test runs_. Possible strategies could include using a UUID
          or sequence number for *--results-dir*.

          For example, to run a robo test using a specific Google Cloud Storage
          location to hold the raw test results, run:

            $ {command} --app=APP_APK --results-bucket=gs://my-bucket --results-dir=my/test/results/<unique-value>

          To run an instrumentation test and specify a custom name under which
          the history of your tests will be collected and displayed in the
          Firebase console, run:

            $ {command} --app=APP_APK --test=TEST_APK --results-history-name='Excelsior App Test History'

          Argument Files

          All test arguments for a given test may alternatively be stored in an
          argument group within a YAML-formatted argument file. The _ARG_FILE_
          may contain one or more named argument groups, and argument groups may
          be combined using the `include:` attribute (Run *$ gcloud topic
          arg-files* for more information). The ARG_FILE can easily be shared
          with colleagues or placed under source control to ensure consistent
          test executions.

          To run a test using arguments loaded from an ARG_FILE named
          *excelsior_args*, which contains an argument group named *robo-args:*,
          use the following syntax:

            $ {command} path/to/excelsior_args:robo-args
          """,
  }

  def Run(self, args):
    """Run the 'gcloud firebase test run' command to invoke a test in Test Lab.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation (i.e. group and command arguments combined).

    Returns:
      One of:
        - a list of TestOutcome tuples (if ToolResults are available).
        - a URL string pointing to the user's results in ToolResults or GCS.
    """
    if args.async_ and not args.IsSpecified('format'):
      args.format = """
          value(format(
            'Final test results will be available at [ {0} ].', [])
          )
      """
    log.status.Print('\nHave questions, feedback, or issues? Get support by '
                     'visiting:\n  https://firebase.google.com/support/\n')

    arg_manager.AndroidArgsManager().Prepare(args)

    project = util.GetProject()
    tr_client = self.context['toolresults_client']
    tr_messages = self.context['toolresults_messages']
    storage_client = self.context['storage_client']

    bucket_ops = results_bucket.ResultsBucketOps(project, args.results_bucket,
                                                 args.results_dir, tr_client,
                                                 tr_messages, storage_client)
    bucket_ops.UploadFileToGcs(args.app, _APK_MIME_TYPE)
    if args.test:
      bucket_ops.UploadFileToGcs(args.test, _APK_MIME_TYPE)
    for obb_file in (args.obb_files or []):
      bucket_ops.UploadFileToGcs(obb_file, 'application/octet-stream')
    if getattr(args, 'robo_script', None):
      bucket_ops.UploadFileToGcs(args.robo_script, 'application/json')
    additional_apks = getattr(args, 'additional_apks', None) or []
    for additional_apk in additional_apks:
      bucket_ops.UploadFileToGcs(additional_apk, _APK_MIME_TYPE)
    other_files = getattr(args, 'other_files', None) or {}
    for device_path, file_to_upload in six.iteritems(other_files):
      bucket_ops.UploadFileToGcs(
          file_to_upload,
          None,
          destination_object=util.GetRelativeDevicePath(device_path))
    bucket_ops.LogGcsResultsUrl()

    tr_history_picker = history_picker.ToolResultsHistoryPicker(
        project, tr_client, tr_messages)
    history_name = PickHistoryName(args)
    history_id = tr_history_picker.GetToolResultsHistoryId(history_name)

    matrix = matrix_creator.CreateMatrix(args, self.context, history_id,
                                         bucket_ops.gcs_results_root,
                                         six.text_type(self.ReleaseTrack()))
    monitor = matrix_ops.MatrixMonitor(matrix.testMatrixId, args.type,
                                       self.context)

    with ctrl_c_handler.CancellableTestSection(monitor):
      tr_ids = tool_results.GetToolResultsIds(matrix, monitor)
      matrix = monitor.GetTestMatrixStatus()
      supported_executions = monitor.HandleUnsupportedExecutions(matrix)

      url = tool_results.CreateToolResultsUiUrl(project, tr_ids)
      log.status.Print('')
      if args.async_:
        return url
      log.status.Print('Test results will be streamed to [ {0} ].'.format(url))

      # If we have exactly one testExecution, show detailed progress info.
      if len(supported_executions) == 1 and args.num_flaky_test_attempts == 0:
        monitor.MonitorTestExecutionProgress(supported_executions[0].id)
      else:
        monitor.MonitorTestMatrixProgress()

    log.status.Print('\nMore details are available at [ {0} ].'.format(url))
    # Fetch the per-dimension test outcomes list, and also the "rolled-up"
    # matrix outcome from the Tool Results service.
    summary_fetcher = results_summary.ToolResultsSummaryFetcher(
        project, tr_client, tr_messages, tr_ids, matrix.testMatrixId)
    self.exit_code = exit_code.ExitCodeFromRollupOutcome(
        summary_fetcher.FetchMatrixRollupOutcome(),
        tr_messages.Outcome.SummaryValueValuesEnum)
    return summary_fetcher.CreateMatrixOutcomeSummaryUsingEnvironments()


@base.ReleaseTracks(base.ReleaseTrack.GA)
class RunGA(_BaseRun, base.ListCommand):
  """Invoke a test in Firebase Test Lab for Android and view test results."""

  @staticmethod
  def Args(parser):
    arg_util.AddCommonTestRunArgs(parser)
    arg_util.AddMatrixArgs(parser)
    arg_util.AddAndroidTestArgs(parser)
    arg_util.AddGaArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(util.OUTCOMES_FORMAT)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class RunBeta(_BaseRun, base.ListCommand):
  """Invoke a test in Firebase Test Lab for Android and view test results."""

  @staticmethod
  def Args(parser):
    arg_util.AddCommonTestRunArgs(parser)
    arg_util.AddMatrixArgs(parser)
    arg_util.AddAndroidTestArgs(parser)
    arg_util.AddAndroidBetaArgs(parser)
    arg_util.AddBetaArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(util.OUTCOMES_FORMAT)


def PickHistoryName(args):
  """Returns the results history name to use to look up a history ID.

  The history ID corresponds to a history name. If the user provides their
  own history name, we use that to look up the history ID; If not, but the user
  provides an app-package name, we use the app-package name with ' (gcloud)'
  appended as the history name. Otherwise, we punt and let the Testing service
  determine the appropriate history ID to publish to.

  Args:
    args: an argparse namespace. All the arguments that were provided to the
      command invocation (i.e. group and command arguments combined).

  Returns:
    Either a string containing a history name derived from user-supplied data,
    or None if we lack the required information.
  """
  if args.results_history_name:
    return args.results_history_name
  if args.app_package:
    return args.app_package + ' (gcloud)'
  return None
