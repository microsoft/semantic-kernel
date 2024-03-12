#!/usr/bin/python

import os
import unittest

from gae_ext_runtime import testutil

RUNTIME_DEF_ROOT = os.path.dirname(os.path.dirname(__file__))

class RuntimeTest(testutil.TestBase):

  def setUp(self):
    self.runtime_def_root = RUNTIME_DEF_ROOT
    super(RuntimeTest, self).setUp()

  def test_custom_runtime(self):
    self.write_file('Dockerfile', 'boring contents')
    self.generate_configs()
    self.assert_file_exists_with_contents('app.yaml',
                                          'env: flex\nruntime: custom\n')

  def test_custom_runtime_no_write(self):
    """Ensure custom runtime writes app.yaml to disk with GenerateConfigData."""
    self.write_file('Dockerfile', 'boring contents')
    self.generate_config_data()
    self.assert_file_exists_with_contents(
        'app.yaml',
        'env: flex\nruntime: custom\n')

if __name__ == '__main__':
  unittest.main()
