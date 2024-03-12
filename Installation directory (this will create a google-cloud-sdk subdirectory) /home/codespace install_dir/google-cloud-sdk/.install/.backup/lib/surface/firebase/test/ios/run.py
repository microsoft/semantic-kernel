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
"""The 'gcloud firebase test ios run' command."""

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
from googlecloudsdk.api_lib.firebase.test.ios import arg_manager
from googlecloudsdk.api_lib.firebase.test.ios import matrix_creator
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
import six

_IPA_MIME_TYPE = 'application/octet-stream'


@base.UnicodeIsSupported
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Run(base.ListCommand):
  """Invoke a test in Firebase Test Lab for iOS and view test results."""

  detailed_help = {
      'DESCRIPTION': """\
          *{command}* invokes and monitors tests in Firebase Test Lab for iOS.

          The currently supported iOS test frameworks are XCTest and XCUITest.
          Other iOS testing frameworks which are built upon XCTest and XCUITest
          should also work.

          The XCTEST_ZIP test package is a zip file built using Apple's Xcode
          and supporting tools. For a detailed description of the process to
          create your XCTEST_ZIP file, see
          https://firebase.google.com/docs/test-lab/ios/command-line.

          All arguments for *{command}* may be specified on the command line
          and/or within an argument file. Run *$ gcloud topic arg-files* for
          more information about argument files.
          """,
      'EXAMPLES': """\
          To invoke an XCTest lasting up to five minutes against the default
          device environment, run:

            $ {command} --test=XCTEST_ZIP --timeout=5m

          To invoke an XCTest against an iPad 5 running iOS 11.2, run:

            $ {command} --test=XCTEST_ZIP --device=model=ipad5,version=11.2

          To run your tests against multiple iOS devices simultaneously, specify
          the *--device* flag more than once:

            $ {command} --test=XCTEST_ZIP --device=model=iphone7 --device=model=ipadmini4,version=11.2 --device=model=iphonese

          To run your XCTest using a specific version of Xcode, say 9.4.1, run:

            $ {command} --test=XCTEST_ZIP --xcode-version=9.4.1

          To help you identify and locate your test matrix in the Firebase
          console, run:

            $ {command} --test=XCTEST_ZIP --client-details=matrixLabel="Example matrix label"

          All test arguments for a given test may alternatively be stored in an
          argument group within a YAML-formatted argument file. The _ARG_FILE_
          may contain one or more named argument groups, and argument groups may
          be combined using the `include:` attribute (Run *$ gcloud topic
          arg-files* for more information). The ARG_FILE can easily be shared
          with colleagues or placed under source control to ensure consistent
          test executions.

          To run a test using arguments loaded from an ARG_FILE named
          *excelsior_app_args*, which contains an argument group named
          *ios-args:*, use the following syntax:

            $ {command} path/to/excelsior_app_args:ios-args
          """,
  }

  @staticmethod
  def Args(parser):
    """Method called by Calliope to register flags for this command.

    Args:
      parser: An argparse parser used to add arguments that follow this command
        in the CLI. Positional arguments are allowed.
    """
    arg_util.AddCommonTestRunArgs(parser)
    arg_util.AddIosTestArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(util.OUTCOMES_FORMAT)

  def Run(self, args):
    """Run the 'firebase test ios run' command to invoke a test in Test Lab.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation (i.e. group and command arguments combined).

    Returns:
      One of:
        - a list of TestOutcome tuples (if ToolResults are available).
        - a URL string pointing to the user's results in ToolResults or GCS.
    """
    # TODO(b/79369595): expand libs to share more code with android run command.
    if args.async_ and not args.IsSpecified('format'):
      args.format = """
          value(format('Final test results will be available at [ {0} ].', []))
      """
    log.status.Print('\nHave questions, feedback, or issues? Get support by '
                     'emailing:\n  ftl-ios-feedback@google.com\n')

    arg_manager.IosArgsManager().Prepare(args)

    project = util.GetProject()
    tr_client = self.context['toolresults_client']
    tr_messages = self.context['toolresults_messages']
    storage_client = self.context['storage_client']

    bucket_ops = results_bucket.ResultsBucketOps(project, args.results_bucket,
                                                 args.results_dir, tr_client,
                                                 tr_messages, storage_client)
    if args.app:
      bucket_ops.UploadFileToGcs(args.app, _IPA_MIME_TYPE)
    if args.test:
      bucket_ops.UploadFileToGcs(args.test, 'application/zip')
    if args.xctestrun_file:
      bucket_ops.UploadFileToGcs(args.xctestrun_file, 'text/xml')
    additional_ipas = getattr(args, 'additional_ipas', None) or []
    for additional_ipa in additional_ipas:
      bucket_ops.UploadFileToGcs(additional_ipa, _IPA_MIME_TYPE)
    other_files = getattr(args, 'other_files', {}) or {}
    for device_path, file_to_upload in six.iteritems(other_files):
      path = device_path
      if ':' in path:
        path = path[path.find(':') + 1:]
      bucket_ops.UploadFileToGcs(
          file_to_upload,
          None,
          destination_object=util.GetRelativeDevicePath(path))
    if getattr(args, 'robo_script', None):
      bucket_ops.UploadFileToGcs(args.robo_script, 'application/json')
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
      supported_executions = monitor.HandleUnsupportedExecutions(matrix)
      tr_ids = tool_results.GetToolResultsIds(matrix, monitor)

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


def PickHistoryName(args):
  """Returns the results history name to use to look up a history ID.

  The history ID corresponds to a history name. If the user provides their own
  history name, we use that to look up the history ID; Otherwise, we punt and
  let the Testing service determine the appropriate history ID to publish to.

  Args:
    args: an argparse namespace. All the arguments that were provided to the
      command invocation (i.e. group and command arguments combined).

  Returns:
    Either a string containing a history name derived from user-supplied data,
    or None if we lack the required information.
  """
  if args.results_history_name:
    return args.results_history_name
  return None


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class RunBeta(Run):
  """Invoke a test in Firebase Test Lab for iOS and view test results."""
  detailed_help = {
      'DESCRIPTION': """\
          *{command}* invokes and monitors tests in Firebase Test Lab for iOS.

          Two types of iOS tests are currently supported:
          - *xctest*: corresponds to the XCTest and XCUITest frameworks. Other
            iOS testing frameworks which are built upon XCTest and XCUITest
            should also work. The XCTEST_ZIP test package is a zip file built
            using Apple's Xcode and supporting tools. For a detailed
            description of the process to create your XCTEST_ZIP file, see
            https://firebase.google.com/docs/test-lab/ios/command-line.
          - *game-loop*: launches the game app through a custom URL scheme to
            execute a "demo mode" built into the game app that simulates
            actions of a real player. This test type can include multiple
            game loops (also called "scenarios") indicated by positive
            numbers.

          The type of test to run can be specified with the *--type* flag,
          which defaults to `xctest`.

          All arguments for *{command}* may be specified on the command line
          and/or within an argument file. Run *$ gcloud topic arg-files* for
          more information about argument files.
        """,
      'EXAMPLES': """\
          To help you identify and locate your test matrix in the Firebase
          console, run:

            $ {command} --test=XCTEST_ZIP --client-details=matrixLabel="Example matrix label"

          To invoke an XCTest lasting up to five minutes against the default
          device environment, run:

            $ {command} --test=XCTEST_ZIP --timeout=5m

          To invoke an XCTest against an iPad 5 running iOS 11.2, run:

            $ {command} --test=XCTEST_ZIP --device=model=ipad5,version=11.2

          To run your tests against multiple iOS devices simultaneously, specify
          the *--device* flag more than once:

            $ {command} --test=XCTEST_ZIP --device=model=iphone7 --device=model=ipadmini4,version=11.2 --device=model=iphonese

          To run your XCTest using a specific version of Xcode, say 9.4.1, run:

            $ {command} --test=XCTEST_ZIP --xcode-version=9.4.1

          To help you identify and locate your test matrix in the Firebase
          console, run:

            $ {command} --test=XCTEST_ZIP --client-details=matrixLabel="Example matrix label"

          To run an iOS game loop, specify the *--type* and *--app* flags:

            $ {command} --type=game-loop --app=app.ipa

          To run an iOS game loop with specific scenario(s), use the
          *--scenario-numbers* flag:

            $ {command} --type=game-loop --app=app.ipa --scenario-numbers=1,2,3

          To run a test that pushes a local file onto the device before testing,
          use the *--other-files* flag:

            $ {command} --type=game-loop --app=app.ipa --scenario-numbers=1 --other-files=/private/var/mobile/Media/file.txt=/path/to/file.txt

          All test arguments for a given test may alternatively be stored in an
          argument group within a YAML-formatted argument file. The _ARG_FILE_
          may contain one or more named argument groups, and argument groups may
          be combined using the `include:` attribute (Run *$ gcloud topic
          arg-files* for more information). The ARG_FILE can easily be shared
          with colleagues or placed under source control to ensure consistent
          test executions.

          To run a test using arguments loaded from an ARG_FILE named
          *excelsior_app_args*, which contains an argument group named
          *ios-args:*, use the following syntax:

            $ {command} path/to/excelsior_app_args:ios-args

          """,
  }

  @staticmethod
  def Args(parser):
    super(RunBeta, RunBeta).Args(parser)
    arg_util.AddIosBetaArgs(parser)
    arg_util.AddBetaArgs(parser)
