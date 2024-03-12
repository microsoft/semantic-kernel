#!/usr/bin/python

import mock
import os
import re
import sys
import stat
import shutil
import tempfile
import textwrap
import unittest

from gae_ext_runtime import ext_runtime
from gae_ext_runtime import testutil

RUNTIME_DEF_ROOT = os.path.dirname(os.path.dirname(__file__))


class RuntimeTests(testutil.TestBase):

    def setUp(self):
        self.runtime_def_root = RUNTIME_DEF_ROOT
        super(RuntimeTests, self).setUp()

    def read_dist_file(self, *args):
        """Read the entire contents of the file.

        Returns the entire contents of the file identified by a set of
        arguments forming a path relative to the root of the runtime
        definition.

        TODO: Move this down into the SDK.

        Args:
            *args: A set of path components (see full_path()).  Note that
                these are relative to the runtime definition root, not the
                temporary directory.
        """
        with open(os.path.join(self.runtime_def_root, *args)) as fp:
            return fp.read()

    def test_node_js_server_js_only(self):
        self.write_file('server.js', 'fake contents')
        self.generate_configs()
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='nodejs'))

        self.generate_configs(deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            self.read_dist_file('data', 'Dockerfile') + textwrap.dedent("""\
                COPY . /app/
                CMD node server.js
                """))
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_dist_file('data', 'dockerignore'))
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'Dockerfile', '.dockerignore', 'app.yaml',
                          'server.js'})

    def test_node_js_server_js_only_no_write(self):
        """Test generate_config_data with only .js files.

        After running generate_configs(), app.yaml exists; after
        generate_config_data(), only app.yaml should exist on disk --
        Dockerfile and .dockerignore should be returned by the method."""
        self.write_file('server.js', 'fake contents')
        self.generate_configs()
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='nodejs'))

        cfg_files = self.generate_config_data(deploy=True)
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            self.read_dist_file('data', 'Dockerfile') + textwrap.dedent("""\
                COPY . /app/
                CMD node server.js
                """))
        self.assert_genfile_exists_with_contents(
            cfg_files,
            '.dockerignore',
            self.read_dist_file('data', 'dockerignore'))
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'app.yaml', 'server.js'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def _validate_docker_files_for_npm(self):
        base_dockerfile = self.read_dist_file('data', 'Dockerfile')
        self.assert_file_exists_with_contents(
            'Dockerfile',
            base_dockerfile + 'COPY . /app/\n' +
            self.read_dist_file('data', 'npm-package-json-install') +
            'CMD npm start\n')
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_dist_file('data', 'dockerignore'))

    def test_node_js_package_json_npm(self):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.generate_configs()
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='nodejs'))
        self.generate_configs(deploy=True)
        self._validate_docker_files_for_npm()
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'Dockerfile', '.dockerignore', 'app.yaml',
                          'foo.js', 'package.json'})

    def _validate_docker_files_for_yarn(self):
        base_dockerfile = self.read_dist_file('data', 'Dockerfile')
        install_yarn = self.read_dist_file('data', 'install-yarn')
        self.assert_file_exists_with_contents(
            'Dockerfile',
            base_dockerfile + install_yarn + 'COPY . /app/\n' +
            self.read_dist_file('data', 'yarn-package-json-install') +
            'CMD yarn start\n')
        self.assert_file_exists_with_contents(
            '.dockerignore',
            self.read_dist_file('data', 'dockerignore'))

    def test_node_js_package_json_yarn(self):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.write_file('yarn.lock', 'yarn overridden')
        self.generate_configs()
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='nodejs'))
        self.generate_configs(deploy=True)
        self._validate_docker_files_for_yarn()
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'Dockerfile', '.dockerignore', 'app.yaml',
                          'foo.js', 'package.json', 'yarn.lock'})

    def _validate_file_list_for_skip_yarn_lock(self):
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'Dockerfile', '.dockerignore', 'yarn.lock',
                          'foo.js', 'package.json'})

    def test_skip_yarn_lock_with_other_files(self):
        """Ensure use_yarn is False with yarn.lock present but is being skipped.

        Further, this test verifies that use_yarn is False even if multiple
        other entries are present in skip_files.

        A yarn executable is injected that passes all checks to ensure that if
        yarn.lock is set to be skipped, use_yarn is set to False even if yarn
        can be executed and reports that the yarn.lock file is valid.
        """
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.write_file('foo.js', 'fake contents')
        self.write_file('yarn.lock', 'fake contents')
        config = testutil.AppInfoFake(runtime='nodejs',
                                      skip_files=['^abc$',
                                                  '^xyz$',
                                                  '^yarn\.lock$',
                                                  '^node_modules$'])
        configurator = self.detect(appinfo=config)
        self.assertEqual(configurator.data['use_yarn'], False)
        self.generate_configs(appinfo=config, deploy=True)
        self._validate_docker_files_for_npm()
        self._validate_file_list_for_skip_yarn_lock()

    def test_only_skip_yarn_lock(self):
        """Ensure use_yarn is False with yarn.lock present but is being skipped.

        Further, this test ensures use_yarn is false if the value obtained
        from skip_files is a regex string and not a list of strings.

        A yarn executable is injected that passes all checks to ensure that if
        yarn.lock is set to be skipped, use_yarn is set to False even if yarn
        can be executed and reports that the yarn.lock file is valid.
        """
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.write_file('foo.js', 'fake contents')
        self.write_file('yarn.lock', 'fake contents')
        config = testutil.AppInfoFake(runtime='nodejs',
                                      skip_files='^yarn\.lock$')
        configurator = self.detect(appinfo=config)
        self.assertEqual(configurator.data['use_yarn'], False)
        self.generate_configs(appinfo=config, deploy=True)
        self._validate_docker_files_for_npm()
        self._validate_file_list_for_skip_yarn_lock()

    def test_do_not_skip_yarn_lock(self):
        """Ensure use_yarn is True with yarn.lock present and not skipped.
        """
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.write_file('foo.js', 'fake contents')
        self.write_file('yarn.lock', 'fake contents')
        # Here only 'node_modules' will be skipped
        config = testutil.AppInfoFake(runtime='nodejs',
                                      skip_files='^node_modules$')
        configurator = self.detect(appinfo=config)
        self.assertEqual(configurator.data['use_yarn'], True)
        self.generate_configs(appinfo=config, deploy=True)
        self._validate_docker_files_for_yarn()
        self._validate_file_list_for_skip_yarn_lock()

    def test_use_yarn_skip_files_not_present(self):
        """Ensure use_yarn is True with yarn.lock present and not skipped.

        In particular, this test ensures use_yarn is True even if app.yaml
        doesn't contain a skip_files section.
        """
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.write_file('foo.js', 'fake contents')
        self.write_file('yarn.lock', 'fake contents')
        config = testutil.AppInfoFake(runtime='nodejs')
        configurator = self.detect(appinfo=config)
        self.assertEqual(configurator.data['use_yarn'], True)
        self.generate_configs(appinfo=config, deploy=True)
        self._validate_docker_files_for_yarn()
        self._validate_file_list_for_skip_yarn_lock()

    def test_node_js_package_json_no_write(self):
        """Test generate_config_data with a nodejs file and package.json."""
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        self.generate_configs()
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='nodejs'))

        cfg_files = self.generate_config_data(deploy=True)

        base_dockerfile = self.read_dist_file('data', 'Dockerfile')
        self.assert_genfile_exists_with_contents(
            cfg_files,
            'Dockerfile',
            base_dockerfile + 'COPY . /app/\n' +
            self.read_dist_file('data', 'npm-package-json-install') +
            'CMD npm start\n')
        self.assert_genfile_exists_with_contents(
            cfg_files,
            '.dockerignore',
            self.read_dist_file('data', 'dockerignore'))
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'app.yaml', 'foo.js', 'package.json'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_detect_basic(self):
        """Ensure that appinfo will be generated in detect method."""
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        configurator = self.detect()
        self.assertEqual(configurator.generated_appinfo,
                         {u'runtime': 'nodejs',
                          u'env': 'flex'})

    def test_detect_custom(self):
        """Ensure that appinfo is correct with custom=True."""
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"start": "foo.js"}}')
        configurator = self.detect(custom=True)
        self.assertEqual(configurator.generated_appinfo,
                         {'runtime': 'custom',
                          'env': 'flex'})

    def test_detect_no_start_no_server(self):
        """Ensure that detect fails if no scripts.start field, no server.js."""
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"not-start": "foo.js"}}')
        configurator = self.detect()
        self.assertEqual(configurator, None)

    def test_detect_no_start_with_server(self):
        """Ensure appinfo generated if no scripts.start, server.js exists."""
        self.write_file('server.js', 'bogus contents')
        self.write_file('package.json', '{"scripts": {"not-start": "foo.js"}}')
        configurator = self.detect()
        self.assertEqual(configurator.generated_appinfo,
                         {'runtime': 'nodejs',
                          'env': 'flex'})

    def test_node_js_with_engines(self):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json',
                        '{"scripts": {"start": "foo.js"},'
                        '"engines": {"node": "0.12.3"}}')
        self.generate_configs(deploy=True)
        dockerfile_path = self.full_path('Dockerfile')
        self.assertTrue(os.path.exists(dockerfile_path))

        # This just verifies that the crazy node install line is generated, it
        # says nothing about whether or not it works.
        rx = re.compile(r'RUN npm install')
        for line in open(dockerfile_path):
            if rx.match(line):
                break
        else:
            self.fail('node install line not generated')

    def test_node_js_with_engines_no_write(self):
        """Test generate_config_data with 'engines' in package.json."""
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json',
                        '{"scripts": {"start": "foo.js"},'
                        '"engines": {"node": "0.12.3"}}')
        cfg_files = self.generate_config_data(deploy=True)
        self.assertIn('Dockerfile', [f.filename for f in cfg_files])

        # This just verifies that the crazy node install line is generated, it
        # says nothing about whether or not it works.
        rx = re.compile(r'RUN npm install')
        line_generated = False
        for cfg_file in cfg_files:
            if cfg_file.filename == 'Dockerfile':
                for line in cfg_file.contents.split('\n'):
                    if rx.match(line):
                        line_generated = True
        if not line_generated:
            self.fail('node install line not generated')

    def test_node_js_custom_runtime(self):
        self.write_file('server.js', 'fake contents')
        self.generate_configs(custom=True)
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='custom'))
        self.assertEqual(sorted(os.listdir(self.temp_path)),
                         ['.dockerignore', 'Dockerfile', 'app.yaml',
                          'server.js'])

    def test_node_js_custom_runtime_no_write(self):
        """Test generate_config_data with custom runtime.

        Should generate an app.yaml on disk, the Dockerfile and
        .dockerignore in memory."""
        self.write_file('server.js', 'fake contents')
        cfg_files = self.generate_config_data(custom=True)
        self.assert_file_exists_with_contents(
            'app.yaml',
            self.read_dist_file('data', 'app.yaml').format(runtime='custom'))
        self.assertEqual(set(os.listdir(self.temp_path)),
                         {'app.yaml', 'server.js'})
        self.assertEqual({f.filename for f in cfg_files},
                         {'Dockerfile', '.dockerignore'})

    def test_node_js_runtime_field(self):
        self.write_file('server.js', 'fake contents')
        config = testutil.AppInfoFake(runtime='nodejs')
        self.generate_configs(appinfo=config, deploy=True)
        self.assertTrue(os.path.exists(self.full_path('Dockerfile')))

    def test_node_js_custom_runtime_field(self):
        self.write_file('server.js', 'fake contents')
        config = testutil.AppInfoFake(runtime='custom')
        self.assertTrue(self.generate_configs(appinfo=config, deploy=True))

    def test_invalid_package_json(self):
        self.write_file('package.json', '')
        self.write_file('server.js', '')
        self.generate_configs()
        self.assertFalse(self.generate_configs())

    # Tests that verify that the generated files match verbatim output.
    # These will need to be maintained whenever the code generation changes,
    # but this ensures that any diffs we introduce in the generate files will
    # be reviewed.

    def test_node_js_with_engines_retroactive(self):
        self.write_file('foo.js', 'bogus contents')
        self.write_file('package.json',
                        '{"scripts": {"start": "foo.js"},'
                        '"engines": {"node": "0.12.3"}}')
        self.generate_configs(deploy=True)
        self.assert_file_exists_with_contents(
            'Dockerfile',
            textwrap.dedent("""\
                # Dockerfile extending the generic Node image with application files for a
                # single application.
                FROM gcr.io/google_appengine/nodejs
                # Check to see if the the version included in the base runtime satisfies
                # 0.12.3, if not then do an npm install of the latest available
                # version that satisfies it.
                RUN /usr/local/bin/install_node 0.12.3
                COPY . /app/
                # You have to specify "--unsafe-perm" with npm install
                # when running as root.  Failing to do this can cause
                # install to appear to succeed even if a preinstall
                # script fails, and may have other adverse consequences
                # as well.
                # This command will also cat the npm-debug.log file after the
                # build, if it exists.
                RUN npm install --unsafe-perm || \\
                  ((if [ -f npm-debug.log ]; then \\
                      cat npm-debug.log; \\
                    fi) && false)
                CMD npm start
                """))


class FailureLoggingTests(testutil.TestBase):

    def setUp(self):
        self.runtime_def_root = RUNTIME_DEF_ROOT
        super(FailureLoggingTests, self).setUp()

        self.errors = []
        self.debug = []
        self.warnings = []

    def error_fake(self, message):
        self.errors.append(message)

    def debug_fake(self, message):
        self.debug.append(message)

    def warn_fake(self, message):
        self.warnings.append(message)

    def test_invalid_package_json(self):
        self.write_file('package.json', '')
        self.write_file('server.js', '')

        variations = [
            (testutil.AppInfoFake(runtime='nodejs'), None),
            (None, 'nodejs'),
            (None, None)
        ]
        for appinfo, runtime in variations:
            self.errors = []
            with mock.patch.dict(ext_runtime._LOG_FUNCS,
                                 {'error': self.error_fake}):
                self.generate_configs(appinfo=appinfo, runtime=runtime)

            self.assertTrue(self.errors[0].startswith(
                'node.js checker: error accessing package.json'))

    def test_no_startup_script(self):
        with mock.patch.dict(ext_runtime._LOG_FUNCS,
                             {'debug': self.debug_fake}):
            self.generate_configs()
        print self.debug
        self.assertTrue(self.debug[1].startswith(
            'node.js checker: Neither "start" in the "scripts" section '
            'of "package.json" nor the "server.js" file were found.'))

        variations = [
            (testutil.AppInfoFake(runtime='nodejs'), None),
            (None, 'nodejs')
        ]
        for appinfo, runtime in variations:
            self.errors = []
            with mock.patch.dict(ext_runtime._LOG_FUNCS,
                                 {'error': self.error_fake}):
                self.generate_configs(appinfo=appinfo, runtime=runtime)
            self.assertTrue(self.errors[0].startswith(
                'node.js checker: Neither "start" in the "scripts" section '
                'of "package.json" nor the "server.js" file were found.'))

    def test_package_json_no_startup_script(self):
        self.write_file('package.json', '{"scripts": {"not-start": "foo.js"}}')

        variations = [
            (testutil.AppInfoFake(runtime='nodejs'), None),
            (None, 'nodejs'),
            (None, None)
        ]
        for appinfo, runtime in variations:
            self.errors = []
            with mock.patch.dict(ext_runtime._LOG_FUNCS,
                                 {'error': self.error_fake}):
                self.generate_configs(appinfo=appinfo, runtime=runtime)
            self.assertTrue(self.errors[0].startswith(
                'node.js checker: Neither "start" in the "scripts" section '
                'of "package.json" nor the "server.js" file were found.'))


if __name__ == '__main__':
  unittest.main()
