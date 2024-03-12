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

@nox.session(python=["3.7", "3.8", "3.9", "3.10"])
def unit(session):
    # constraints_path = str(
    #     CURRENT_DIRECTORY / "testing" / f"constraints-{session.python}.txt"
    # )
    session.install("-r", "requirements.txt")
    # session.install("-e", ".")
    session.run(
        "pytest",
        f"--junitxml=unit_{session.python}_sponge_log.xml",
        "snippets_test.py",
        # "tests_async",
    )