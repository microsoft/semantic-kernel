#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Various utilities used in tests."""

import contextlib
import os
import shutil
import sys
import tempfile
import unittest

import six


SkipOnWindows = unittest.skipIf(
    os.name == 'nt', 'Does not run on windows')


@contextlib.contextmanager
def TempDir(change_to=False):
    if change_to:
        original_dir = os.getcwd()
    path = tempfile.mkdtemp()
    try:
        if change_to:
            os.chdir(path)
        yield path
    finally:
        if change_to:
            os.chdir(original_dir)
        shutil.rmtree(path)


@contextlib.contextmanager
def CaptureOutput():
    new_stdout, new_stderr = six.StringIO(), six.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_stdout, new_stderr
        yield new_stdout, new_stderr
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
