# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Unit test support library for GAE Externalized Runtimes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import shutil
import tempfile
import unittest

from gae_ext_runtime import ext_runtime


class InvalidRuntime(Exception):
    """Raised when the runtime directory is doesn't match the runtime."""


class AppInfoFake(dict):
    """Serves as a fake for an AppInfo object."""

    def ToDict(self):
        return self


class TestBase(unittest.TestCase):
    """Unit testing base class.

    Derived classes must define a setUp() method that sets a runtime_def_root
    attribute containing the path to the root directory of the runtime.
    """

    def setUp(self):
        self.exec_env = ext_runtime.DefaultExecutionEnvironment()
        self.temp_path = tempfile.mkdtemp()
        self.assertTrue(hasattr(self, 'runtime_def_root'),
                        'Your test suite must define a setUp() method that '
                        'sets a runtime_def_root attribute to the root of the '
                        'runtime.')

    def tearDown(self):
        shutil.rmtree(self.temp_path)

    def set_execution_environment(self, exec_env):
        """Set the execution environment used by generate_configs.

        If this is not set, an instance of
        ext_runtime.DefaultExecutionEnvironment is used.

        Args:
            exec_env: (ext_runtime.ExecutionEnvironment) The execution
                environment to be used for config generation.
        """
        self.exec_env = exec_env

    def maybe_get_configurator(self, params=None, **kwargs):
        """Load the runtime definition.

        Args:
            params: (ext_runtime.Params) Runtime parameters.  DEPRECATED.
                Use the keyword args, instead.
            **kwargs: ({str: object, ...}) If specified, these are the
                arguments to the ext_runtime.Params() constructor
                (valid args are at this time are: appinfo, custom and deploy,
                check ext_runtime.Params() for full details)

        Returns:
            configurator or None if configurator didn't match
        """
        rt = ext_runtime.ExternalizedRuntime.Load(self.runtime_def_root,
                                                  self.exec_env)
        params = params or ext_runtime.Params(**kwargs)
        print(params.ToDict())
        configurator = rt.Detect(self.temp_path, params)
        return configurator

    def generate_configs(self, params=None, **kwargs):
        """Load the runtime definition and generate configs from it.

        Args:
            params: (ext_runtime.Params) Runtime parameters.  DEPRECATED.
                Use the keyword args, instead.
            **kwargs: ({str: object, ...}) If specified, these are the
                arguments to the ext_runtime.Params() constructor
                (valid args are at this time are: appinfo, custom and deploy,
                check ext_runtime.Params() for full details)

        Returns:
            (bool) Returns True if files are generated, False if not, None
            if configurator didn't match
        """
        configurator = self.maybe_get_configurator(params, **kwargs)
        if not configurator:
            return None

        configurator.Prebuild()

        return configurator.GenerateConfigs()

    def generate_config_data(self, params=None, **kwargs):
        """Load the runtime definition and generate configs from it.

        Args:
            params: (ext_runtime.Params) Runtime parameters.  DEPRECATED.
                Use the keyword args, instead.
            **kwargs: ({str: object, ...}) If specified, these are the
                arguments to the ext_runtime.Params() constructor
                (valid args are at this time are: appinfo, custom and deploy,
                check ext_runtime.Params() for full details)

        Returns:
            ([ext_runtime.GeneratedFile, ...]) Returns list of generated files.

        Raises:
            InvalidRuntime: Couldn't detect a matching runtime.
        """
        configurator = self.maybe_get_configurator(params, **kwargs)
        if not configurator:
            raise InvalidRuntime('Runtime defined in {} did not detect '
                                 'code in {}'.format(self.runtime_def_root,
                                                     self.temp_path))

        configurator.Prebuild()

        return configurator.GenerateConfigData()

    def detect(self, params=None, **kwargs):
        """Load the runtime definition and generate configs from it.

        Args:
            params: (ext_runtime.Params) Runtime parameters.  DEPRECATED.
                Use the keyword args, instead.
            **kwargs: ({str: object, ...}) If specified, these are the
                arguments to the ext_runtime.Params() constructor
                (valid args are at this time are: appinfo, custom and deploy,
                check ext_runtime.Params() for full details)

        Returns:
            (ext_runtime.Configurator or None) the identified runtime if found,
            None if not.
        """
        rt = ext_runtime.ExternalizedRuntime.Load(self.runtime_def_root,
                                                  self.exec_env)
        params = params or ext_runtime.Params(**kwargs)
        configurator = rt.Detect(self.temp_path, params)

        return configurator

    def full_path(self, *path_components):
        """Returns the fully qualified path for a relative filename.

        e.g. self.full_path('foo', 'bar', 'baz') -> '/temp/path/foo/bar/baz'

        Args:
            *path_components: ([str, ...]) Path components.

        Returns:
            (str)
        """
        return os.path.join(self.temp_path, *path_components)

    def write_file(self, filename, contents):
        with open(os.path.join(self.temp_path, filename), 'w') as fp:
            fp.write(contents)

    def read_runtime_def_file(self, *args):
        """Read the entire contents of the file.

        Returns the entire contents of the file identified by a set of
        arguments forming a path relative to the root of the runtime
        definition.

        Args:
            *args: A set of path components (see full_path()).  Note that
                these are relative to the runtime definition root, not the
                temporary directory.
        """
        with open(os.path.join(self.runtime_def_root, *args)) as fp:
            return fp.read()

    def assert_file_exists_with_contents(self, filename, contents):
        """Assert that the specified file exists with the given contents.

        Args:
            filename: (str) New file name.
            contents: (str) File contents.
        """
        full_name = self.full_path(filename)
        self.assertTrue(os.path.exists(full_name))
        with open(full_name) as fp:
            actual_contents = fp.read()
        self.assertEqual(contents, actual_contents)

    def assert_genfile_exists_with_contents(self, gen_files,
                                            filename, contents):
        for gen_file in gen_files:
          if gen_file.filename == filename:
              self.assertEqual(gen_file.contents, contents)
              break
        else:
          self.fail('filename {} not found in generated files {}'.format(
              filename, gen_files))

