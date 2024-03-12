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
"""A utility library to support interaction with the Tool Results service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import os
import time

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import progress_tracker
from six.moves.urllib import parse
import uritemplate

_STATUS_INTERVAL_SECS = 3


class ToolResultsIds(
    collections.namedtuple('ToolResultsIds', ['history_id', 'execution_id'])):
  """A tuple to hold the history & execution IDs returned from Tool Results.

  Fields:
    history_id: a string with the Tool Results history ID to publish to.
    execution_id: a string with the ID of the Tool Results execution.
  """


def CreateToolResultsUiUrl(project_id, tool_results_ids):
  """Create the URL for a test's Tool Results UI in the Firebase App Manager.

  Args:
    project_id: string containing the user's GCE project ID.
    tool_results_ids: a ToolResultsIds object holding history & execution IDs.

  Returns:
    A url to the Tool Results UI.
  """
  url_base = properties.VALUES.test.results_base_url.Get()
  if not url_base:
    url_base = 'https://console.firebase.google.com'

  url_end = uritemplate.expand(
      'project/{project}/testlab/histories/{history}/matrices/{execution}', {
          'project': project_id,
          'history': tool_results_ids.history_id,
          'execution': tool_results_ids.execution_id
      })
  return parse.urljoin(url_base, url_end)


def GetToolResultsIds(matrix,
                      matrix_monitor,
                      status_interval=_STATUS_INTERVAL_SECS):
  """Gets the Tool Results history ID and execution ID for a test matrix.

  Sometimes the IDs are available immediately after a test matrix is created.
  If not, we keep checking the matrix until the Testing and Tool Results
  services have had enough time to create/assign the IDs, giving the user
  continuous feedback using gcloud core's ProgressTracker class.

  Args:
    matrix: a TestMatrix which was just created by the Testing service.
    matrix_monitor: a MatrixMonitor object.
    status_interval: float, number of seconds to sleep between status checks.

  Returns:
    A ToolResultsIds tuple containing the history ID and execution ID, which
    are shared by all TestExecutions in the TestMatrix.

  Raises:
    BadMatrixError: if the matrix finishes without both ToolResults IDs.
  """
  history_id = None
  execution_id = None
  msg = 'Creating individual test executions'
  with progress_tracker.ProgressTracker(msg, autotick=True):
    while True:
      if matrix.resultStorage.toolResultsExecution:
        history_id = matrix.resultStorage.toolResultsExecution.historyId
        execution_id = matrix.resultStorage.toolResultsExecution.executionId
        if history_id and execution_id:
          break

      if matrix.state in matrix_monitor.completed_matrix_states:
        raise exceptions.BadMatrixError(_ErrorFromMatrixInFailedState(matrix))

      time.sleep(status_interval)
      matrix = matrix_monitor.GetTestMatrixStatus()

  return ToolResultsIds(history_id=history_id, execution_id=execution_id)


def _ErrorFromMatrixInFailedState(matrix):
  """Produces a human-readable error message from an invalid matrix."""
  messages = apis.GetMessagesModule('testing', 'v1')
  if matrix.state == messages.TestMatrix.StateValueValuesEnum.INVALID:
    return _ExtractInvalidMatrixDetails(matrix)

  return _GenericErrorMessage(matrix)


def _ExtractInvalidMatrixDetails(matrix):
  invalid_details_for_user = []
  for invalid_detail in matrix.extendedInvalidMatrixDetails:
    invalid_details_for_user.append(
        f'Reason: {invalid_detail.reason} Message: {invalid_detail.message}'
    )
  if invalid_details_for_user:
    return 'Matrix [{m}] failed during validation.\n{msg}'.format(
        m=matrix.testMatrixId, msg=os.linesep.join(invalid_details_for_user)
    )
  else:
    return _GetLegacyInvalidMatrixDetails(matrix)


def _GetLegacyInvalidMatrixDetails(matrix):
  """Converts legacy invalid matrix enum to a descriptive message for the user.

  Args:
    matrix: A TestMatrix in a failed state

  Returns:
    A string containing the legacy error message when no message is available
    from the API.

  """
  messages = apis.GetMessagesModule('testing', 'v1')
  enum_values = messages.TestMatrix.InvalidMatrixDetailsValueValuesEnum
  error_dict = {
      enum_values.MALFORMED_APK:
          'The app APK is not a valid Android application',
      enum_values.MALFORMED_TEST_APK:
          'The test APK is not a valid Android instrumentation test',
      enum_values.NO_MANIFEST:
          'The app APK is missing the manifest file',
      enum_values.NO_PACKAGE_NAME:
          'The APK manifest file is missing the package name',
      enum_values.TEST_SAME_AS_APP:
          'The test APK has the same package name as the app APK',
      enum_values.NO_INSTRUMENTATION:
          'The test APK declares no instrumentation tags in the manifest',
      enum_values.NO_SIGNATURE:
          'At least one supplied APK file has a missing or invalid signature',
      enum_values.INSTRUMENTATION_ORCHESTRATOR_INCOMPATIBLE:
          ("The test runner class specified by the user or the test APK's "
           'manifest file is not compatible with Android Test Orchestrator. '
           'Please use AndroidJUnitRunner version 1.1 or higher'),
      enum_values.NO_TEST_RUNNER_CLASS:
          ('The test APK does not contain the test runner class specified by '
           'the user or the manifest file. The test runner class name may be '
           'incorrect, or the class may be mislocated in the app APK.'),
      enum_values.NO_LAUNCHER_ACTIVITY:
          'The app APK does not specify a main launcher activity',
      enum_values.FORBIDDEN_PERMISSIONS:
          'The app declares one or more permissions that are not allowed',
      enum_values.INVALID_ROBO_DIRECTIVES:
          ('Robo directives are invalid: multiple robo-directives cannot have '
           'the same resource name and there cannot be more than one `click:` '
           'directive specified.'),
      enum_values.INVALID_DIRECTIVE_ACTION:
          'Robo Directive includes at least one invalid action definition.',
      enum_values.INVALID_RESOURCE_NAME:
          'Robo Directive resource name contains invalid characters: ":" '
          ' (colon) or " " (space)',
      enum_values.TEST_LOOP_INTENT_FILTER_NOT_FOUND:
          'The app does not have a correctly formatted game-loop intent filter',
      enum_values.SCENARIO_LABEL_NOT_DECLARED:
          'A scenario-label was not declared in the manifest file',
      enum_values.SCENARIO_LABEL_MALFORMED:
          'A scenario-label in the manifest includes invalid numbers or ranges',
      enum_values.SCENARIO_NOT_DECLARED:
          'A scenario-number was not declared in the manifest file',
      enum_values.DEVICE_ADMIN_RECEIVER:
          'Device administrator applications are not allowed',
      enum_values.MALFORMED_XC_TEST_ZIP:
          'The XCTest zip file was malformed. The zip did not contain a single '
          '.xctestrun file and the contents of the DerivedData/Build/Products '
          'directory.',
      enum_values.BUILT_FOR_IOS_SIMULATOR:
          'The provided XCTest was built for the iOS simulator rather than for '
          'a physical device',
      enum_values.NO_TESTS_IN_XC_TEST_ZIP:
          'The .xctestrun file did not specify any test targets to run',
      enum_values.USE_DESTINATION_ARTIFACTS:
          'One or more of the test targets defined in the .xctestrun file '
          'specifies "UseDestinationArtifacts", which is not allowed',
      enum_values.TEST_NOT_APP_HOSTED:
          'One or more of the test targets defined in the .xctestrun file '
          'does not have a host binary to run on the physical iOS device, '
          'which may cause errors when running xcodebuild',
      enum_values.NO_CODE_APK:
          '"hasCode" is false in the Manifest. Tested APKs must contain code',
      enum_values.INVALID_INPUT_APK:
          'Either the provided input APK path was malformed, the APK file does '
          'not exist, or the user does not have permission to access the file',
      enum_values.INVALID_APK_PREVIEW_SDK:
          "Your app targets a preview version of the Android SDK that's "
          'incompatible with the selected devices.',
      enum_values.PLIST_CANNOT_BE_PARSED:
          'One or more of the Info.plist files in the zip could not be parsed',
      enum_values.INVALID_PACKAGE_NAME:
          'The APK application ID (aka package name) is invalid. See also '
          'https://developer.android.com/studio/build/application-id',
      enum_values.MALFORMED_IPA:
          'The app IPA is not a valid iOS application',
      enum_values.MISSING_URL_SCHEME:
          'The iOS game loop application does not register the custom URL '
          'scheme',
      enum_values.MALFORMED_APP_BUNDLE:
          'The iOS application bundle (.app) is invalid',
      enum_values.MATRIX_TOO_LARGE:
          'The matrix expanded to contain too many executions.',
      enum_values.TEST_QUOTA_EXCEEDED:
          'Not enough test quota to run the executions in this matrix.',
      enum_values.SERVICE_NOT_ACTIVATED:
          'A required cloud service api is not activated.',
      enum_values.UNKNOWN_PERMISSION_ERROR:
          'There was an unknown permission issue running this test.',
  }
  details_enum = matrix.invalidMatrixDetails
  if details_enum in error_dict:
    return ('\nMatrix [{m}] failed during validation: {e}.'.format(
        m=matrix.testMatrixId, e=error_dict[details_enum]))
  # Use a generic message if the enum is unknown or unspecified/unavailable.
  return _GenericErrorMessage(matrix)


def _GenericErrorMessage(matrix):
  return (
      '\nMatrix [{m}] unexpectedly reached final status {s} without returning '
      'a URL to any test results in the Firebase console. Please re-check the '
      'validity of your test files and parameters and try again.'.format(
          m=matrix.testMatrixId, s=matrix.state))

