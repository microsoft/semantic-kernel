#!/usr/bin/python
# Copyright 2016 Google Inc. All Rights Reserved.
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

import os
import textwrap
import unittest

from gae_ext_runtime import testutil

RUNTIME_DEF_ROOT = os.path.dirname(os.path.dirname(__file__))


class RuntimeTestCase(testutil.TestBase):
    """Tests for the PHP external runtime fingerprinter."""

    def license(self):
        return textwrap.dedent('''\
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

            ''')

    def preamble(self):
        return textwrap.dedent('''\
            # Dockerfile extending the generic PHP image with application files for a
            # single application.
            FROM gcr.io/google-appengine/php:latest

            # The Docker image will configure the document root according to this
            # environment variable.
            ''')

    def setUp(self):
        self.runtime_def_root = RUNTIME_DEF_ROOT
        super(RuntimeTestCase, self).setUp()

    def file_contents(self, filename):
        with open(self.full_path(filename)) as f:
            return f.read()

    def test_generate_without_php_files(self):
        self.write_file('index.html', 'index')

        self.assertFalse(self.generate_configs())

        self.assertFalse(os.path.exists(self.full_path('app.yaml')))
        self.assertFalse(os.path.exists(self.full_path('Dockerfile')))
        self.assertFalse(os.path.exists(self.full_path('.dockerignore')))

    def test_generate_with_php_files(self):
        self.write_file('index.php', 'index')
        self.generate_configs()

        app_yaml = self.file_contents('app.yaml')
        self.assertIn('runtime: php\n', app_yaml)
        self.assertIn('env: flex\n', app_yaml)
        self.assertIn('runtime_config:\n  document_root: .\n', app_yaml)
        self.assertNotIn('entrypoint', app_yaml)

        self.assertFalse(os.path.exists(self.full_path('Dockerfile')))
        self.assertFalse(os.path.exists(self.full_path('.dockerignore')))

    def test_generate_with_php_files_no_write(self):
        """Test generate_config_data with a .php file.

        Checks app.yaml contents, app.yaml is written to disk, and
        Dockerfile and .dockerignore not in the directory.
        """
        self.write_file('index.php', 'index')
        self.generate_config_data()

        app_yaml = self.file_contents('app.yaml')
        self.assertIn('runtime: php\n', app_yaml)
        self.assertIn('env: flex\n', app_yaml)
        self.assertIn('runtime_config:\n  document_root: .\n', app_yaml)

        self.assertFalse(os.path.exists(self.full_path('Dockerfile')))
        self.assertFalse(os.path.exists(self.full_path('.dockerignore')))

    def test_generate_custom_runtime(self):
        self.write_file('index.php', 'index')
        self.generate_configs(custom=True)

        dockerfile = self.file_contents('Dockerfile')
        self.assertEqual(dockerfile, self.preamble() + textwrap.dedent('''\
            ENV DOCUMENT_ROOT /app
            '''))

        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.license() + textwrap.dedent('''\
            .dockerignore
            Dockerfile
            .git
            .hg
            .svn
            '''))

    def test_generate_custom_runtime_no_write(self):
        """Tests generate_config_data with custom runtime."""
        self.write_file('index.php', 'index')
        cfg_files = self.generate_config_data(custom=True)

        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.preamble() + textwrap.dedent('''\
            ENV DOCUMENT_ROOT /app
            '''))

        self.assert_genfile_exists_with_contents(
            cfg_files,
            '.dockerignore',
            self.license() + textwrap.dedent('''\
            .dockerignore
            Dockerfile
            .git
            .hg
            .svn
            '''))

    def test_generate_with_deploy(self):
        self.write_file('index.php', 'index')
        self.generate_configs(deploy=True)

        dockerfile = self.file_contents('Dockerfile')
        self.assertEqual(dockerfile, textwrap.dedent('''\
            # Dockerfile extending the generic PHP image with application files for a
            # single application.
            FROM gcr.io/google-appengine/php:latest

            # The Docker image will configure the document root according to this
            # environment variable.
            ENV DOCUMENT_ROOT /app
            '''))

        dockerignore = self.file_contents('.dockerignore')
        self.assertEqual(dockerignore, self.license() + textwrap.dedent('''\
            .dockerignore
            Dockerfile
            .git
            .hg
            .svn
            '''))

    def test_generate_with_deploy_no_write(self):
        """Tests generate_config_data with deploy=True."""
        self.write_file('index.php', 'index')
        cfg_files = self.generate_config_data(deploy=True)

        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.preamble() + textwrap.dedent('''\
            ENV DOCUMENT_ROOT /app
            '''))

        self.assert_genfile_exists_with_contents(
            cfg_files,
            '.dockerignore',
            self.license() + textwrap.dedent('''\
            .dockerignore
            Dockerfile
            .git
            .hg
            .svn
            '''))

    def test_generate_with_existing_appinfo(self):
        self.write_file('index.php', 'index')
        appinfo = testutil.AppInfoFake(
                runtime_config={'document_root': 'wordpress'},
                entrypoint='["/bin/bash", "my-cmd.sh"]')
        self.generate_configs(deploy=True, appinfo=appinfo)

        dockerfile = self.file_contents('Dockerfile')
        self.assertEqual(dockerfile, self.preamble() + textwrap.dedent('''\
            ENV DOCUMENT_ROOT /app/wordpress

            # Allow custom CMD
            CMD ["/bin/bash", "my-cmd.sh"]
            '''))

        dockerignore = self.file_contents('.dockerignore')
        self.assertEqual(dockerignore, self.license() + textwrap.dedent('''\
            .dockerignore
            Dockerfile
            .git
            .hg
            .svn
            '''))

    def test_generate_with_existing_appinfo_no_write(self):
        """Tests generate_config_data with fake appinfo."""
        self.write_file('index.php', 'index')
        appinfo = testutil.AppInfoFake(
                runtime_config={'document_root': 'wordpress'},
                entrypoint='["/bin/bash", "my-cmd.sh"]')
        cfg_files = self.generate_config_data(deploy=True, appinfo=appinfo)

        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.preamble() + textwrap.dedent('''\
            ENV DOCUMENT_ROOT /app/wordpress

            # Allow custom CMD
            CMD ["/bin/bash", "my-cmd.sh"]
            '''))

        self.assert_genfile_exists_with_contents(
            cfg_files,
            '.dockerignore',
            self.license() + textwrap.dedent('''\
            .dockerignore
            Dockerfile
            .git
            .hg
            .svn
            '''))

    def test_generate_with_array_entrypoint(self):
        self.write_file('index.php', 'index')
        appinfo = testutil.AppInfoFake(
                runtime_config={'document_root': 'wordpress'},
                entrypoint=['/bin/bash', 'my-cmd.sh'])
        self.generate_configs(deploy=True, appinfo=appinfo)

        dockerfile = self.file_contents('Dockerfile')
        self.assertEqual(dockerfile, self.preamble() + textwrap.dedent('''\
            ENV DOCUMENT_ROOT /app/wordpress

            # Allow custom CMD
            CMD ["/bin/bash", "my-cmd.sh"]
            '''))

    def test_generate_with_array_entrypoint_no_write(self):
        """Tests generate_config_data with an array entrypoint."""
        self.write_file('index.php', 'index')
        appinfo = testutil.AppInfoFake(
                runtime_config={'document_root': 'wordpress'},
                entrypoint=["/bin/bash", "my-cmd.sh"])
        cfg_files = self.generate_config_data(deploy=True, appinfo=appinfo)

        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.preamble() + textwrap.dedent('''\
            ENV DOCUMENT_ROOT /app/wordpress

            # Allow custom CMD
            CMD ["/bin/bash", "my-cmd.sh"]
            '''))

if __name__ == '__main__':
    unittest.main()
