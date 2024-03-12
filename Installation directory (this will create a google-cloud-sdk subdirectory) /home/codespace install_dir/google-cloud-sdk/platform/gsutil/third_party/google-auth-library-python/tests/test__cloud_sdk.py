# Copyright 2016 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io
import json
import os
import subprocess
import sys

import mock
import pytest  # type: ignore

from google.auth import _cloud_sdk
from google.auth import environment_vars
from google.auth import exceptions


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
AUTHORIZED_USER_FILE = os.path.join(DATA_DIR, "authorized_user.json")

with io.open(AUTHORIZED_USER_FILE, "rb") as fh:
    AUTHORIZED_USER_FILE_DATA = json.load(fh)

SERVICE_ACCOUNT_FILE = os.path.join(DATA_DIR, "service_account.json")

with io.open(SERVICE_ACCOUNT_FILE, "rb") as fh:
    SERVICE_ACCOUNT_FILE_DATA = json.load(fh)


@pytest.mark.parametrize(
    "data, expected_project_id",
    [(b"example-project\n", "example-project"), (b"", None)],
)
def test_get_project_id(data, expected_project_id):
    check_output_patch = mock.patch(
        "subprocess.check_output", autospec=True, return_value=data
    )

    with check_output_patch as check_output:
        project_id = _cloud_sdk.get_project_id()

    assert project_id == expected_project_id
    assert check_output.called


@mock.patch(
    "subprocess.check_output",
    autospec=True,
    side_effect=subprocess.CalledProcessError(-1, "testing"),
)
def test_get_project_id_call_error(check_output):
    project_id = _cloud_sdk.get_project_id()
    assert project_id is None
    assert check_output.called


def test__run_subprocess_ignore_stderr():
    command = [
        sys.executable,
        "-c",
        "from __future__ import print_function;"
        + "import sys;"
        + "print('error', file=sys.stderr);"
        + "print('output', file=sys.stdout)",
    ]

    # If we ignore stderr, then the output only has stdout
    output = _cloud_sdk._run_subprocess_ignore_stderr(command)
    assert output == b"output\n"

    # If we pipe stderr to stdout, then the output is mixed with stdout and stderr.
    output = subprocess.check_output(command, stderr=subprocess.STDOUT)
    assert output == b"output\nerror\n" or output == b"error\noutput\n"


@mock.patch("os.name", new="nt")
def test_get_project_id_windows():
    check_output_patch = mock.patch(
        "subprocess.check_output", autospec=True, return_value=b"example-project\n"
    )

    with check_output_patch as check_output:
        project_id = _cloud_sdk.get_project_id()

    assert project_id == "example-project"
    assert check_output.called
    # Make sure the executable is `gcloud.cmd`.
    args = check_output.call_args[0]
    command = args[0]
    executable = command[0]
    assert executable == "gcloud.cmd"


@mock.patch("google.auth._cloud_sdk.get_config_path", autospec=True)
def test_get_application_default_credentials_path(get_config_dir):
    config_path = "config_path"
    get_config_dir.return_value = config_path
    credentials_path = _cloud_sdk.get_application_default_credentials_path()
    assert credentials_path == os.path.join(
        config_path, _cloud_sdk._CREDENTIALS_FILENAME
    )


def test_get_config_path_env_var(monkeypatch):
    config_path_sentinel = "config_path"
    monkeypatch.setenv(environment_vars.CLOUD_SDK_CONFIG_DIR, config_path_sentinel)
    config_path = _cloud_sdk.get_config_path()
    assert config_path == config_path_sentinel


@mock.patch("os.path.expanduser")
def test_get_config_path_unix(expanduser):
    expanduser.side_effect = lambda path: path

    config_path = _cloud_sdk.get_config_path()

    assert os.path.split(config_path) == ("~/.config", _cloud_sdk._CONFIG_DIRECTORY)


@mock.patch("os.name", new="nt")
def test_get_config_path_windows(monkeypatch):
    appdata = "appdata"
    monkeypatch.setenv(_cloud_sdk._WINDOWS_CONFIG_ROOT_ENV_VAR, appdata)

    config_path = _cloud_sdk.get_config_path()

    assert os.path.split(config_path) == (appdata, _cloud_sdk._CONFIG_DIRECTORY)


@mock.patch("os.name", new="nt")
def test_get_config_path_no_appdata(monkeypatch):
    monkeypatch.delenv(_cloud_sdk._WINDOWS_CONFIG_ROOT_ENV_VAR, raising=False)
    monkeypatch.setenv("SystemDrive", "G:")

    config_path = _cloud_sdk.get_config_path()

    assert os.path.split(config_path) == ("G:/\\", _cloud_sdk._CONFIG_DIRECTORY)


@mock.patch("os.name", new="nt")
@mock.patch("subprocess.check_output", autospec=True)
def test_get_auth_access_token_windows(check_output):
    check_output.return_value = b"access_token\n"

    token = _cloud_sdk.get_auth_access_token()
    assert token == "access_token"
    check_output.assert_called_with(
        ("gcloud.cmd", "auth", "print-access-token"), stderr=subprocess.STDOUT
    )


@mock.patch("subprocess.check_output", autospec=True)
def test_get_auth_access_token_with_account(check_output):
    check_output.return_value = b"access_token\n"

    token = _cloud_sdk.get_auth_access_token(account="account")
    assert token == "access_token"
    check_output.assert_called_with(
        ("gcloud", "auth", "print-access-token", "--account=account"),
        stderr=subprocess.STDOUT,
    )


@mock.patch("subprocess.check_output", autospec=True)
def test_get_auth_access_token_with_exception(check_output):
    check_output.side_effect = OSError()

    with pytest.raises(exceptions.UserAccessTokenError):
        _cloud_sdk.get_auth_access_token(account="account")
