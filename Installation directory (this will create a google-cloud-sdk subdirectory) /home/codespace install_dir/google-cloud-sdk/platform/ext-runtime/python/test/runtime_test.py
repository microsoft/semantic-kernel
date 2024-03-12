# Copyright 2016 Google Inc. All Rights Reserved.
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

# Note: this file is part of the sdk-ext-runtime package.  It gets copied into
# individual GAE runtime modules so that they can be easily deployed.

import os
import textwrap
import unittest

from gae_ext_runtime import comm
from gae_ext_runtime import ext_runtime
from gae_ext_runtime import testutil

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT = comm.RuntimeDefinitionRoot(ROOT_DIR)


class FakeExecutionEnvironment(ext_runtime.DefaultExecutionEnvironment):

    def CanPrompt(self):
        return True

    def PromptResponse(self, message):
        return 'my_entrypoint'


class RuntimeTests(testutil.TestBase):

    def setUp(self):
        # This has to come before RuntimeTests.setUp()
        self.runtime_def_root = ROOT_DIR
        super(RuntimeTests, self).setUp()

        self.DOCKERFILE_PREAMBLE = (
            ROOT.read_file('data', 'Dockerfile.preamble'))
        self.DOCKERFILE_VIRTUALENV_TEMPLATE = (
            ROOT.read_file('data',
                           'Dockerfile.virtualenv.template'))
        self.DOCKERFILE_REQUIREMENTS_TXT = (
            ROOT.read_file('data', 'Dockerfile.requirements_txt'))
        self.DOCKERFILE_INSTALL_APP = (
            ROOT.read_file('data', 'Dockerfile.install_app'))
        self.set_execution_environment(FakeExecutionEnvironment())

    # XXX Move this to testutil.
    def read_file(self, *args):
        """Read the file, return the contents.

        Args:
            *args: A set of path components (see full_path()) relative to the
                temporary directory.
        """
        with open(os.path.join(self.temp_path, *args)) as fp:
            return fp.read()

    def test_python(self):
        self.write_file('requirements.txt', 'requirements')
        self.generate_configs(deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(python_version='') +
            self.DOCKERFILE_REQUIREMENTS_TXT +
            self.DOCKERFILE_INSTALL_APP +
            'CMD my_entrypoint\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'requirements.txt',
                          'app.yaml',
                          'Dockerfile',
                          '.dockerignore'})

    def test_python_no_write(self):
        """Tests generate_config_data with only requirements.txt.

        app.yaml should be written to disk, Dockerfile and .dockerignore
        returned by the method in memory. Tests that Dockerfile contents
        are correct.
        """
        self.write_file('requirements.txt', 'requirements')
        cfg_files = self.generate_config_data(deploy=True)
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(python_version='') +
            self.DOCKERFILE_REQUIREMENTS_TXT +
            self.DOCKERFILE_INSTALL_APP +
            'CMD my_entrypoint\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'requirements.txt', 'app.yaml'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_python_no_requirements_txt(self):
        self.write_file('foo.py', '# python code')
        self.generate_configs(custom=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD my_entrypoint\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'foo.py', 'app.yaml', 'Dockerfile', '.dockerignore'})

    def test_python_no_requirements_txt_no_write(self):
        """Tests generate_config_data with no requirements.txt file."""
        self.write_file('foo.py', '# python code')
        cfg_files = self.generate_config_data(custom=True)
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD my_entrypoint\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'foo.py', 'app.yaml'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_python_with_app_yaml(self):
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(
            runtime='python',
            entrypoint='run_me_some_python!')
        self.generate_configs(appinfo=config, deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD run_me_some_python!\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py', 'Dockerfile', '.dockerignore'})

    def test_python_with_app_yaml_no_write(self):
        """Tests generate_config_data with fake appinfo."""
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(
            runtime='python',
            entrypoint='run_me_some_python!')
        cfg_files = self.generate_config_data(appinfo=config, deploy=True)
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD run_me_some_python!\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_python_app_yaml_no_entrypoint(self):
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(runtime='python')
        self.generate_configs(appinfo=config, deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD my_entrypoint\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py', 'Dockerfile', '.dockerignore'})

    def test_python_app_yaml_no_entrypoint_no_write(self):
        """Tests generate_config_data with fake appinfo, no entrypoint."""
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(runtime='python')
        cfg_files = self.generate_config_data(appinfo=config, deploy=True)
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD my_entrypoint\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_python_with_runtime_config_but_no_python_version(self):
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(runtime='python',
                                      entrypoint='run_me_some_python!')
        self.generate_configs(appinfo=config, deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD run_me_some_python!\n')
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py', '.dockerignore', 'Dockerfile'})

    def test_python_with_runtime_config_but_no_python_version_no_write(self):
        """Tests generate_config_data with no python version in appinfo."""
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(runtime='python',
                                      entrypoint='run_me_some_python!')
        cfg_files = self.generate_config_data(appinfo=config, deploy=True)
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD run_me_some_python!\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_python_with_explicit_python2(self):
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(
            runtime='python',
            entrypoint='run_me_some_python!',
            runtime_config=dict(python_version='2'))
        self.generate_configs(appinfo=config, deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD run_me_some_python!\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py', '.dockerignore', 'Dockerfile'})

    def test_python_with_explicit_python2_no_write(self):
        """Tests generate_config_data with Python version '2' in appinfo."""
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(
            runtime='python',
            entrypoint='run_me_some_python!',
            runtime_config=dict(python_version='2'))
        cfg_files = self.generate_config_data(appinfo=config, deploy=True)
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD run_me_some_python!\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_python_with_explicit_python3(self):
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(runtime='python',
                                      entrypoint='run_me_some_python!',
                                      runtime_config=dict(python_version='3'))
        self.generate_configs(appinfo=config, deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='3.6') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD run_me_some_python!\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py', '.dockerignore', 'Dockerfile'})

    def test_python_with_explicit_python3_no_write(self):
        """Tests generate_config_data with python version '3' in appinfo."""
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(runtime='python',
                                      entrypoint='run_me_some_python!',
                                      runtime_config=dict(python_version='3'))
        cfg_files = self.generate_config_data(appinfo=config, deploy=True)
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='3.6') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD run_me_some_python!\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_python_with_explicit_python34(self):
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(runtime='python',
                                      entrypoint='run_me_some_python!',
                                      runtime_config=dict(python_version='3.4'))
        self.generate_configs(appinfo=config, deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='3.4') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD run_me_some_python!\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py', '.dockerignore', 'Dockerfile'})

    def test_python_with_explicit_python35(self):
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(runtime='python',
                                      entrypoint='run_me_some_python!',
                                      runtime_config=dict(python_version='3.5'))
        self.generate_configs(appinfo=config, deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='3.5') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD run_me_some_python!\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py', '.dockerignore', 'Dockerfile'})

    def test_python_with_explicit_python36(self):
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(runtime='python',
                                      entrypoint='run_me_some_python!',
                                      runtime_config=dict(python_version='3.6'))
        self.generate_configs(appinfo=config, deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.DOCKERFILE_PREAMBLE +
            self.DOCKERFILE_VIRTUALENV_TEMPLATE.format(
                python_version='3.6') +
            self.DOCKERFILE_INSTALL_APP +
            'CMD run_me_some_python!\n')

        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py', '.dockerignore', 'Dockerfile'})

    def test_python_with_invalid_version(self):
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(
            runtime='python',
            entrypoint='run_me_some_python!',
            runtime_config=dict(python_version='invalid_version'))
        self.assertRaises(testutil.InvalidRuntime,
                          self.generate_config_data, appinfo=config)

    def test_python_custom_runtime(self):
        self.write_file('test.py', 'test file')
        self.generate_configs(custom=True)
        with open(os.path.join(self.temp_path, 'app.yaml')) as f:
            app_yaml_contents = f.read()
        self.assertMultiLineEqual(
            app_yaml_contents,
            textwrap.dedent("""\
                entrypoint: my_entrypoint
                env: flex
                runtime: custom
                """))
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py', 'app.yaml', '.dockerignore', 'Dockerfile'})

    def test_python_custom_runtime_no_write(self):
        """Tests generate_config_data with custom=True."""
        self.write_file('test.py', 'test file')
        cfg_files = self.generate_config_data(custom=True)
        with open(os.path.join(self.temp_path, 'app.yaml')) as f:
            app_yaml_contents = f.read()
        self.assertMultiLineEqual(
            app_yaml_contents,
            textwrap.dedent("""\
                entrypoint: my_entrypoint
                env: flex
                runtime: custom
                """))
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'test.py', 'app.yaml'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_python_custom_runtime_field(self):
        """Verify that a runtime field of "custom" works."""
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(runtime='custom',
                                      entrypoint='my_entrypoint')
        self.assertTrue(self.generate_configs(appinfo=config, deploy=True))

    def test_python_label(self):
        """Test that a LABEL directive is added to the Dockerfile"""
        self.write_file('test.py', 'test file')
        config = testutil.AppInfoFake(
            runtime='python',
            entrypoint='run_me_some_python!',
            runtime_config=dict(python_version='3'))
        cfg_files = self.generate_config_data(appinfo=config, deploy=True)
        dockerfile = [f for f in cfg_files if f.filename == 'Dockerfile'][0]
        self.assertIn('LABEL python_version=python3.6\n', dockerfile.contents)

    # NOTE: this test is also irrelevant to the runtime, convert it to
    # something appropriate to the framework.
#    def test_python_non_interactive(self):
#        self.write_file('test.py', 'blah')
#        with mock.patch.object(console_io, 'CanPrompt', lambda: False):
#            with mock.patch.object(fingerprinting,
#                                   'GetNonInteractiveErrorMessage',
#                                   lambda: 'xx123unlikely'):
#
#        fingerprinter.IdentifyDirectory(self.temp_path)
#        self.AssertLogContains('xx123unlikely')

if __name__ == '__main__':
    unittest.main()
