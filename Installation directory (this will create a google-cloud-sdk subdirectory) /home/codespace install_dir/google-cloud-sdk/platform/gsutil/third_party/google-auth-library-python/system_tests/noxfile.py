# Copyright 2020 Google LLC
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

"""Noxfile for automating system tests.

This file handles setting up environments needed by the system tests. This
separates the tests from their environment configuration.

See the `nox docs`_ for details on how this file works:

.. _nox docs: http://nox.readthedocs.io/en/latest/
"""

import os
import pathlib
import subprocess
import shutil
import tempfile

from nox.command import which
import nox

HERE = os.path.abspath(os.path.dirname(__file__))
LIBRARY_DIR = os.path.abspath(os.path.dirname(HERE))
DATA_DIR = os.path.join(HERE, "data")
SERVICE_ACCOUNT_FILE = os.path.join(DATA_DIR, "service_account.json")
AUTHORIZED_USER_FILE = os.path.join(DATA_DIR, "authorized_user.json")
EXPLICIT_CREDENTIALS_ENV = "GOOGLE_APPLICATION_CREDENTIALS"
EXPLICIT_PROJECT_ENV = "GOOGLE_CLOUD_PROJECT"
EXPECT_PROJECT_ENV = "EXPECT_PROJECT_ID"
ALLOW_PLUGGABLE_ENV = "GOOGLE_EXTERNAL_ACCOUNT_ALLOW_EXECUTABLES"

SKIP_GAE_TEST_ENV = "SKIP_APP_ENGINE_SYSTEM_TEST"
GAE_APP_URL_TMPL = "https://{}-dot-{}.appspot.com"
GAE_TEST_APP_SERVICE = "google-auth-system-tests"

# The download location for the Cloud SDK
CLOUD_SDK_DIST_FILENAME = "google-cloud-sdk.tar.gz"
CLOUD_SDK_DOWNLOAD_URL = "https://dl.google.com/dl/cloudsdk/release/{}".format(
    CLOUD_SDK_DIST_FILENAME
)

# This environment variable is recognized by the Cloud SDK and overrides
# the location of the SDK's configuration files (which is usually at
# ${HOME}/.config).
CLOUD_SDK_CONFIG_ENV = "CLOUDSDK_CONFIG"

# If set, this is where the environment setup will install the Cloud SDK.
# If unset, it will download the SDK to a temporary directory.
CLOUD_SDK_ROOT = os.environ.get("CLOUD_SDK_ROOT")

if CLOUD_SDK_ROOT is not None:
    CLOUD_SDK_ROOT = pathlib.Path(CLOUD_SDK_ROOT)
    if not CLOUD_SDK_ROOT.exists() or not CLOUD_SDK_ROOT.is_dir():
        print("{} did not exist! Please set the CLOUD_SDK_ROOT environment variable to a directory that exists".format(CLOUD_SDK_ROOT))
        exit(1)
else:
    CLOUD_SDK_ROOT = pathlib.Path(tempfile.mkdtemp())

# The full path the cloud sdk install directory
CLOUD_SDK_INSTALL_DIR = CLOUD_SDK_ROOT.joinpath("google-cloud-sdk")

# The full path to the gcloud cli executable.
GCLOUD = str(CLOUD_SDK_INSTALL_DIR.joinpath("bin", "gcloud"))

# gcloud requires Python 2 and doesn't work on 3, so we need to tell it
# where to find 2 when we're running in a 3 environment.
CLOUD_SDK_PYTHON_ENV = "CLOUDSDK_PYTHON"
CLOUD_SDK_PYTHON = which("python2", None)

# Cloud SDK helpers


def install_cloud_sdk(session):
    """Downloads and installs the Google Cloud SDK."""
    # Configure environment variables needed by the SDK.
    # This sets the config root to the tests' config root. This prevents
    # our tests from clobbering a developer's configuration when running
    # these tests locally.
    session.env[CLOUD_SDK_CONFIG_ENV] = str(CLOUD_SDK_ROOT)
    # This tells gcloud which Python interpreter to use (always use 2.7)
    session.env[CLOUD_SDK_PYTHON_ENV] = CLOUD_SDK_PYTHON
    # This set the $PATH for the subprocesses so they can find the gcloud
    # executable.
    session.env["PATH"] = (
        str(CLOUD_SDK_INSTALL_DIR.joinpath("bin")) + os.pathsep + os.environ["PATH"]
    )

    # If gcloud cli executable already exists, just update it.
    if pathlib.Path(GCLOUD).exists():
        session.run(GCLOUD, "components", "update", "-q")
        return

    tar_path = CLOUD_SDK_ROOT.joinpath(CLOUD_SDK_DIST_FILENAME)

    # Download the release.
    session.run("wget", CLOUD_SDK_DOWNLOAD_URL, "-O", str(tar_path), silent=True)

    # Extract the release.
    session.run("tar", "xzf", str(tar_path), "-C", str(CLOUD_SDK_ROOT))
    tar_path.unlink()

    # Run the install script.
    session.run(
        str(CLOUD_SDK_INSTALL_DIR.joinpath("install.sh")),
        "--usage-reporting",
        "false",
        "--path-update",
        "false",
        "--command-completion",
        "false",
        silent=True,
    )


def copy_credentials(credentials_path):
    """Copies credentials into the SDK root as the application default
    credentials."""
    dest = CLOUD_SDK_ROOT.joinpath("application_default_credentials.json")
    if dest.exists():
        dest.unlink()
    shutil.copyfile(pathlib.Path(credentials_path), dest)


def configure_cloud_sdk(session, application_default_credentials, project=False):
    """Installs and configures the Cloud SDK with the given application default
    credentials.

    If project is True, then a project will be set in the active config.
    If it is false, this will ensure no project is set.
    """
    install_cloud_sdk(session)

    # Setup the service account as the default user account. This is
    # needed for the project ID detection to work. Note that this doesn't
    # change the application default credentials file, which is user
    # credentials instead of service account credentials sometimes.
    session.run(
        GCLOUD, "auth", "activate-service-account", "--key-file", SERVICE_ACCOUNT_FILE
    )

    if project:
        session.run(GCLOUD, "config", "set", "project", "example-project")
    else:
        session.run(GCLOUD, "config", "unset", "project")

    # Copy the credentials file to the config root. This is needed because
    # unfortunately gcloud doesn't provide a clean way to tell it to use
    # a particular set of credentials. However, this does verify that gcloud
    # also considers the credentials valid by calling application-default
    # print-access-token
    session.run(copy_credentials, application_default_credentials)

    # Calling this forces the Cloud SDK to read the credentials we just wrote
    # and obtain a new access token with those credentials. This validates
    # that our credentials matches the format expected by gcloud.
    # Silent is set to True to prevent leaking secrets in test logs.
    session.run(
        GCLOUD, "auth", "application-default", "print-access-token", silent=True
    )


# Test sesssions

TEST_DEPENDENCIES_ASYNC = ["aiohttp", "pytest-asyncio", "nest-asyncio", "mock"]
TEST_DEPENDENCIES_SYNC = ["pytest", "requests", "mock"]
PYTHON_VERSIONS_ASYNC = ["3.7"]
PYTHON_VERSIONS_SYNC = ["2.7", "3.7"]


def default(session, *test_paths):
    # replace 'session._runner.friendly_name' with
    # session.name once nox has released a new version
    # https://github.com/theacodes/nox/pull/386
    sponge_log = f"--junitxml=system_{str(session._runner.friendly_name)}_sponge_log.xml"
    session.run(
        "pytest", sponge_log, *test_paths,
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def service_account_sync(session):
    session.install(*TEST_DEPENDENCIES_SYNC)
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_sync/test_service_account.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def default_explicit_service_account(session):
    session.env[EXPLICIT_CREDENTIALS_ENV] = SERVICE_ACCOUNT_FILE
    session.env[EXPECT_PROJECT_ENV] = "1"
    session.install(*TEST_DEPENDENCIES_SYNC)
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_sync/test_default.py",
        "system_tests_sync/test_id_token.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def default_explicit_authorized_user(session):
    session.env[EXPLICIT_CREDENTIALS_ENV] = AUTHORIZED_USER_FILE
    session.install(*TEST_DEPENDENCIES_SYNC)
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_sync/test_default.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def default_explicit_authorized_user_explicit_project(session):
    session.env[EXPLICIT_CREDENTIALS_ENV] = AUTHORIZED_USER_FILE
    session.env[EXPLICIT_PROJECT_ENV] = "example-project"
    session.env[EXPECT_PROJECT_ENV] = "1"
    session.install(*TEST_DEPENDENCIES_SYNC)
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_sync/test_default.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def default_cloud_sdk_service_account(session):
    configure_cloud_sdk(session, SERVICE_ACCOUNT_FILE)
    session.env[EXPECT_PROJECT_ENV] = "1"
    session.install(*TEST_DEPENDENCIES_SYNC)
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_sync/test_default.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def default_cloud_sdk_authorized_user(session):
    configure_cloud_sdk(session, AUTHORIZED_USER_FILE)
    session.install(*TEST_DEPENDENCIES_SYNC)
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_sync/test_default.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def default_cloud_sdk_authorized_user_configured_project(session):
    configure_cloud_sdk(session, AUTHORIZED_USER_FILE, project=True)
    session.env[EXPECT_PROJECT_ENV] = "1"
    session.install(*TEST_DEPENDENCIES_SYNC)
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_sync/test_default.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def compute_engine(session):
    session.install(*TEST_DEPENDENCIES_SYNC)
    # unset Application Default Credentials so
    # credentials are detected from environment
    del session.virtualenv.env["GOOGLE_APPLICATION_CREDENTIALS"]
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_sync/test_compute_engine.py",
        *session.posargs,
    )


@nox.session(python=["2.7"])
def app_engine(session):
    if SKIP_GAE_TEST_ENV in os.environ:
        session.log("Skipping App Engine tests.")
        return

    session.install(LIBRARY_DIR)
    # Unlike the default tests above, the App Engine system test require a
    # 'real' gcloud sdk installation that is configured to deploy to an
    # app engine project.
    # Grab the project ID from the cloud sdk.
    project_id = (
        subprocess.check_output(
            ["gcloud", "config", "list", "project", "--format", "value(core.project)"]
        )
        .decode("utf-8")
        .strip()
    )

    if not project_id:
        session.error(
            "The Cloud SDK must be installed and configured to deploy to App " "Engine."
        )

    application_url = GAE_APP_URL_TMPL.format(GAE_TEST_APP_SERVICE, project_id)

    # Vendor in the test application's dependencies
    session.chdir(os.path.join(HERE, "system_tests_sync/app_engine_test_app"))
    session.install(*TEST_DEPENDENCIES_SYNC)
    session.run(
        "pip", "install", "--target", "lib", "-r", "requirements.txt", silent=True
    )

    # Deploy the application.
    session.run("gcloud", "app", "deploy", "-q", "app.yaml")

    # Run the tests
    session.env["TEST_APP_URL"] = application_url
    session.chdir(HERE)
    default(
        session, "system_tests_sync/test_app_engine.py",
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def grpc(session):
    session.install(LIBRARY_DIR)
    session.install(*TEST_DEPENDENCIES_SYNC, "google-cloud-pubsub==1.7.2")
    session.env[EXPLICIT_CREDENTIALS_ENV] = SERVICE_ACCOUNT_FILE
    default(
        session,
        "system_tests_sync/test_grpc.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def requests(session):
    session.install(LIBRARY_DIR)
    session.install(*TEST_DEPENDENCIES_SYNC)
    session.env[EXPLICIT_CREDENTIALS_ENV] = SERVICE_ACCOUNT_FILE
    default(
        session,
        "system_tests_sync/test_requests.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def urllib3(session):
    session.install(LIBRARY_DIR)
    session.install(*TEST_DEPENDENCIES_SYNC)
    session.env[EXPLICIT_CREDENTIALS_ENV] = SERVICE_ACCOUNT_FILE
    default(
        session,
        "system_tests_sync/test_urllib3.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def mtls_http(session):
    session.install(LIBRARY_DIR)
    session.install(*TEST_DEPENDENCIES_SYNC, "pyopenssl")
    session.env[EXPLICIT_CREDENTIALS_ENV] = SERVICE_ACCOUNT_FILE
    default(
        session,
        "system_tests_sync/test_mtls_http.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_ASYNC)
def external_accounts(session):
    session.env[ALLOW_PLUGGABLE_ENV] = "1"
    session.install(
        *TEST_DEPENDENCIES_ASYNC,
        LIBRARY_DIR,
        "google-api-python-client",
    )
    default(
        session,
        "system_tests_sync/test_external_accounts.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_SYNC)
def downscoping(session):
    session.install(
        *TEST_DEPENDENCIES_SYNC,
        LIBRARY_DIR,
        "google-cloud-storage",
    )
    default(
        session,
        "system_tests_sync/test_downscoping.py",
        *session.posargs,
    )


# ASYNC SYSTEM TESTS

@nox.session(python=PYTHON_VERSIONS_ASYNC)
def service_account_async(session):
    session.install(*(TEST_DEPENDENCIES_SYNC + TEST_DEPENDENCIES_ASYNC))
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_async/test_service_account.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_ASYNC)
def default_explicit_service_account_async(session):
    session.env[EXPLICIT_CREDENTIALS_ENV] = SERVICE_ACCOUNT_FILE
    session.env[EXPECT_PROJECT_ENV] = "1"
    session.install(*(TEST_DEPENDENCIES_SYNC + TEST_DEPENDENCIES_ASYNC))
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_async/test_default.py",
        "system_tests_async/test_id_token.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_ASYNC)
def default_explicit_authorized_user_async(session):
    session.env[EXPLICIT_CREDENTIALS_ENV] = AUTHORIZED_USER_FILE
    session.install(*(TEST_DEPENDENCIES_SYNC + TEST_DEPENDENCIES_ASYNC))
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_async/test_default.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_ASYNC)
def default_explicit_authorized_user_explicit_project_async(session):
    session.env[EXPLICIT_CREDENTIALS_ENV] = AUTHORIZED_USER_FILE
    session.env[EXPLICIT_PROJECT_ENV] = "example-project"
    session.env[EXPECT_PROJECT_ENV] = "1"
    session.install(*(TEST_DEPENDENCIES_SYNC + TEST_DEPENDENCIES_ASYNC))
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_async/test_default.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_ASYNC)
def default_cloud_sdk_service_account_async(session):
    configure_cloud_sdk(session, SERVICE_ACCOUNT_FILE)
    session.env[EXPECT_PROJECT_ENV] = "1"
    session.install(*(TEST_DEPENDENCIES_SYNC + TEST_DEPENDENCIES_ASYNC))
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_async/test_default.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_ASYNC)
def default_cloud_sdk_authorized_user_async(session):
    configure_cloud_sdk(session, AUTHORIZED_USER_FILE)
    session.install(*(TEST_DEPENDENCIES_SYNC + TEST_DEPENDENCIES_ASYNC))
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_async/test_default.py",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS_ASYNC)
def default_cloud_sdk_authorized_user_configured_project_async(session):
    configure_cloud_sdk(session, AUTHORIZED_USER_FILE, project=True)
    session.env[EXPECT_PROJECT_ENV] = "1"
    session.install(*(TEST_DEPENDENCIES_SYNC + TEST_DEPENDENCIES_ASYNC))
    session.install(LIBRARY_DIR)
    default(
        session,
        "system_tests_async/test_default.py",
        *session.posargs,
    )
