# Copyright 2019 Google LLC
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

import os
import pathlib
import shutil

import nox

CURRENT_DIRECTORY = pathlib.Path(__file__).parent.absolute()

# https://github.com/psf/black/issues/2964, pin click version to 8.0.4 to
# avoid incompatiblity with black.
CLICK_VERSION = "click==8.0.4"
BLACK_VERSION = "black==19.3b0"
BLACK_PATHS = [
    "google",
    "tests",
    "tests_async",
    "noxfile.py",
    "setup.py",
    "docs/conf.py",
]


@nox.session(python="3.8")
def lint(session):
    session.install(
        "flake8", "flake8-import-order", "docutils", CLICK_VERSION, BLACK_VERSION
    )
    session.install("-e", ".")
    session.run("black", "--check", *BLACK_PATHS)
    session.run(
        "flake8",
        "--import-order-style=google",
        "--application-import-names=google,tests,system_tests",
        "google",
        "tests",
        "tests_async",
    )
    session.run(
        "python", "setup.py", "check", "--metadata", "--restructuredtext", "--strict"
    )


@nox.session(python="3.8")
def blacken(session):
    """Run black.
    Format code to uniform standard.
    The Python version should be consistent with what is
    supplied in the Python Owlbot postprocessor.

    https://github.com/googleapis/synthtool/blob/master/docker/owlbot/python/Dockerfile
    """
    session.install(CLICK_VERSION, BLACK_VERSION)
    session.run("black", *BLACK_PATHS)


@nox.session(python="3.8")
def mypy(session):
    """Verify type hints are mypy compatible."""
    session.install("-e", ".")
    session.install(
        "mypy",
        "types-cachetools",
        "types-certifi",
        "types-freezegun",
        "types-pyOpenSSL",
        "types-requests",
        "types-setuptools",
        "types-six",
        "types-mock",
    )
    session.run("mypy", "google/", "tests/", "tests_async/")


@nox.session(python=["3.6", "3.7", "3.8", "3.9", "3.10", "3.11"])
def unit(session):
    constraints_path = str(
        CURRENT_DIRECTORY / "testing" / f"constraints-{session.python}.txt"
    )
    session.install("-r", "testing/requirements.txt", "-c", constraints_path)
    session.install("-e", ".", "-c", constraints_path)
    session.run(
        "pytest",
        f"--junitxml=unit_{session.python}_sponge_log.xml",
        "--cov=google.auth",
        "--cov=google.oauth2",
        "--cov=tests",
        "--cov-report=term-missing",
        "tests",
        "tests_async",
    )


@nox.session(python=["2.7"])
def unit_prev_versions(session):
    constraints_path = str(
        CURRENT_DIRECTORY / "testing" / f"constraints-{session.python}.txt"
    )
    session.install("-r", "testing/requirements.txt", "-c", constraints_path)
    session.install("-e", ".", "-c", constraints_path)
    session.run(
        "pytest",
        f"--junitxml=unit_{session.python}_sponge_log.xml",
        "--cov=google.auth",
        "--cov=google.oauth2",
        "--cov=tests",
        "--ignore=tests/test_pluggable.py",  # Pluggable auth only support 3.6+ for now.
        "tests",
        "--ignore=tests/transport/test__custom_tls_signer.py",  # enterprise cert is for python 3.6+
    )


@nox.session(python="3.8")
def cover(session):
    session.install("-r", "testing/requirements.txt")
    session.install("-e", ".")
    session.run(
        "pytest",
        "--cov=google.auth",
        "--cov=google.oauth2",
        "--cov=tests",
        "--cov=tests_async",
        "--cov-report=term-missing",
        "tests",
        "tests_async",
    )
    session.run("coverage", "report", "--show-missing", "--fail-under=100")


@nox.session(python="3.9")
def docs(session):
    """Build the docs for this library."""

    session.install("-e", ".[aiohttp]")
    session.install("sphinx", "alabaster", "recommonmark", "sphinx-docstring-typing")

    shutil.rmtree(os.path.join("docs", "_build"), ignore_errors=True)
    session.run(
        "sphinx-build",
        "-T",  # show full traceback on exception
        "-W",  # warnings as errors
        "-N",  # no colors
        "-b",
        "html",
        "-d",
        os.path.join("docs", "_build", "doctrees", ""),
        os.path.join("docs", ""),
        os.path.join("docs", "_build", "html", ""),
    )


@nox.session(python="pypy")
def pypy(session):
    session.install("-r", "test/requirements.txt")
    session.install("-e", ".")
    session.run(
        "pytest",
        f"--junitxml=unit_{session.python}_sponge_log.xml",
        "--cov=google.auth",
        "--cov=google.oauth2",
        "--cov=tests",
        "tests",
        "tests_async",
    )
