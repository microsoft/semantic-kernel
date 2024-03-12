#!/usr/bin/env python
#
# Copyright 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import os
import platform
import remove_pyreadline
import setuptools.command.easy_install as easy_install
import setuptools.package_index
import shutil
import sys

EASY_INSTALL_PTH_FILENAME = 'easy-install.pth'
BACKUP_SUFFIX = '.old'


def locate_package(name):
  import pkg_resources
  try:
    pkg = setuptools.package_index.get_distribution(name)
  except pkg_resources.DistributionNotFound:
    pkg = None
  return pkg


def find_package_consumers(name, deps_to_ignore=None):
  installed_packages = list(setuptools.package_index.AvailableDistributions())
  if deps_to_ignore is None:
    deps_to_ignore = []
  consumers = []
  for package_name in installed_packages:
    if name == package_name:
      continue
    package_info = setuptools.package_index.get_distribution(package_name)
    if package_name in deps_to_ignore:
      continue
    for req in package_info.requires():
      if req.project_name == name:
        consumers.append(package_name)
        break
  return consumers


def remove_package(pkg):
  site_packages_dir, egg_name = os.path.split(pkg.location)
  easy_install_pth_filename = os.path.join(site_packages_dir,
                                           EASY_INSTALL_PTH_FILENAME)
  backup_filename = easy_install_pth_filename + BACKUP_SUFFIX
  shutil.copy2(easy_install_pth_filename, backup_filename)
  pth_file = easy_install.PthDistributions(easy_install_pth_filename)
  pth_file.remove(pkg)
  pth_file.save()
  if os.path.isdir(pkg.location):
    shutil.rmtree(pkg.location)
  else:
    os.unlink(pkg.location)


def y_or_n_p(prompt):
  response = raw_input('%s (y/n) ' % (prompt,)).strip().lower()
  while response not in ['y', 'n']:
    response = raw_input('  Please answer y or n: ').strip().lower()
  return response


def delete_pyreadline():
  pkg = locate_package('pyreadline')
  if pkg is None:
    print('pyreadline not found, exiting.')
    return

  consumers = find_package_consumers('pyreadline')
  if consumers:
    print('pyreadline is a dependency of all the following packages:')
    for p in consumers:
      print('  %s' % (p,))
    print()
  else:
    print('pyreadline is not a dependency of any installed packages.')
    print()
  response = y_or_n_p('Continue and uninstall pyreadline?')
  if response == 'n':
    print('Aborting uninstall of pyreadline.')
    return
  remove_package(pkg)
  print('pyreadline successfully uninstalled!')


def run_main():
  print('This script will attempt to remove pyreadline from your system.')
  print()
  if platform.system() == 'Windows':
    print()
    print('*** WARNING ***')
    print('This is a Windows system, and removal of pyreadline on a Windows')
    print('system is NOT recommended.')
    response = y_or_n_p('Are you SURE you want to proceed?')
    if response == 'n':
      print('Exiting.')
      exit(0)
  delete_pyreadline()


if __name__ == '__main__':
  run_main()
