# Copyright 2015 Google Inc. All Rights Reserved.
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

import os
import unittest
import yaml

from gae_ext_runtime import testutil

RUNTIME_DEF_ROOT = os.path.dirname(os.path.dirname(__file__))


class RuntimeTests(testutil.TestBase):

    def setUp(self):
        self.runtime_def_root = RUNTIME_DEF_ROOT
        super(RuntimeTests, self).setUp()

    def assert_no_file(self, filename):
        """Asserts that the relative path 'filename' does not exist."""
        self.assertFalse(os.path.exists(os.path.join(self.temp_path, filename)))

    def test_go_files_no_go(self):
        self.write_file('foo.notgo', 'package main\nfunc main')
        self.assertFalse(self.generate_configs())
        self.assertEqual(os.listdir(self.temp_path), ['foo.notgo'])

    def test_go_files_with_go(self):
        self.write_file('foo.go', 'package main\nfunc main')
        self.generate_configs()
        with open(self.full_path('app.yaml')) as f:
            contents = yaml.load(f)
        self.assertEqual(contents,
                         {'runtime': 'go', 'env': 'flex'})

        self.assert_no_file('Dockerfile')
        self.assert_no_file('.dockerignore')
        self.generate_configs(deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.read_runtime_def_file('data', 'Dockerfile'))
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_runtime_def_file('data',  'dockerignore'))

    def test_go_files_in_subdirs(self):
        """Test go runtime does not recognize go files in subdirectories."""
        subdir_path = os.mkdir(os.path.join(self.temp_path, 'subdir'))
        self.write_file(os.path.join('subdir', 'foo.go'),
                        'package main\nfunc main')
        self.assertEqual(None, self.generate_configs())
        self.assertFalse(os.path.exists(self.full_path('app.yaml')))

    def test_go_genfiles_with_go(self):
        """Test generate_config_data with single .go file."""
        self.write_file('foo.go', 'package main\nfunc main')
        self.generate_configs()
        with open(self.full_path('app.yaml')) as f:
            contents = yaml.load(f)
        self.assertEqual(contents,
                         {'runtime': 'go', 'env': 'flex'})

        self.assert_no_file('Dockerfile')
        self.assert_no_file('.dockerignore')
        cfg_files = self.generate_config_data(deploy=True)
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.read_runtime_def_file('data', 'Dockerfile'))
        self.assert_genfile_exists_with_contents(
            cfg_files,
            '.dockerignore',
            self.read_runtime_def_file('data', 'dockerignore'))

    def test_go_custom_runtime(self):
        self.write_file('foo.go', 'package main\nfunc main')
        self.generate_configs(custom=True)
        self.assert_file_exists_with_contents(
            'app.yaml',
            'env: flex\nruntime: go\n')
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.read_runtime_def_file('data', 'Dockerfile'))
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_runtime_def_file('data', 'dockerignore'))

    def test_go_custom_runtime_no_write(self):
        """Test generate_config_data with custom runtime."""
        self.write_file('foo.go', 'package main\nfunc main')
        cfg_files = self.generate_config_data(custom=True)
        self.assert_file_exists_with_contents(
            'app.yaml',
            'env: flex\nruntime: go\n')
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.read_runtime_def_file('data', 'Dockerfile'))
        self.assert_genfile_exists_with_contents(
            cfg_files,
            '.dockerignore',
            self.read_runtime_def_file('data',  'dockerignore'))

    def test_go_runtime_field(self):
        self.write_file('foo.go', 'package main\nfunc main')
        config = testutil.AppInfoFake(
            runtime="go",
            env=2)
        self.assertTrue(self.generate_configs(appinfo=config,
                                              deploy=True))

    def test_go_custom_runtime_field(self):
        self.write_file('foo.go', 'package main\nfunc main')
        config = testutil.AppInfoFake(
            runtime="custom",
            env=2)
        self.assertTrue(self.generate_configs(appinfo=config,
                                              deploy=True))


if __name__ == '__main__':
    unittest.main()
