# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
#

"""Contains utilities for holding and formatting install information.

This is useful for the output of 'gcloud info', which in turn is extremely
useful for debugging issues related to weird installations, out-of-date
installations, and so on.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import getpass
import io
import locale
import os
import platform as system_platform
import re
import ssl
import subprocess
import sys
import textwrap

import certifi
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.diagnostics import http_proxy_setup
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import http_proxy_types
from googlecloudsdk.core.util import platforms
import requests
import six
import urllib3


class NoopAnonymizer(object):
  """Noop anonymizer."""

  def ProcessPath(self, path):
    return path

  def ProcessAccount(self, account):
    return account

  def ProcessProject(self, project):
    return project

  def ProcessUniverseDomain(self, universe_domain):
    return universe_domain

  def ProcessUsername(self, username):
    return username

  def ProcessPassword(self, password):
    return password

  def ProcessURL(self, url):
    return url


class Anonymizer(object):
  """Remove personally identifiable info from paths, account and project."""

  def __init__(self):
    cfg_paths = config.Paths()
    # Ordered list of replacements. First match wins, more specific paths should
    # be placed before more general ones.
    self._replacements = [
        (re.escape(os.path.normpath(cfg_paths.global_config_dir)),
         '${CLOUDSDK_CONFIG}'),
        (re.escape(file_utils.GetHomeDir()), '${HOME}'),
        (re.escape(getpass.getuser()), '${USER}')
    ]
    if cfg_paths.sdk_root:
      self._replacements.append(
          (re.escape(os.path.normpath(cfg_paths.sdk_root)),
           '${SDK_ROOT}'))

  def ProcessPath(self, path):
    """Check if path prefix matches known prefixes which might have pii."""

    if not path:
      return path
    norm_path = os.path.normpath(path)
    for repl_from, repl_to in self._replacements:
      norm_path, num_matches = re.subn(repl_from, repl_to, norm_path)
      if num_matches:
        return norm_path
    return path

  def ProcessURL(self, url):
    """If url is a file URI, anonymize any pii in path."""

    prefix = 'file://'
    if not url or not url.startswith(prefix):
      return url
    return prefix + self.ProcessPath(url[len(prefix):])

  def ProcessAccount(self, account):
    """Anonymize account by leaving first and last letters."""
    if not account:
      return account
    idx = account.index('@')
    return (account[0] + '..' + account[idx-1] + '@' +
            account[idx+1] + '..' + account[-1])

  def ProcessProject(self, project):
    """Anonymize project by leaving first and last letters."""
    if not project:
      return project
    return project[0] + '..' + project[-1]

  def ProcessUsername(self, username):
    if not username:
      return username
    return username[0] + '..' + username[-1]

  def ProcessUniverseDomain(self, universe_domain: str) -> str:
    """Returns default universe domain if universe_domain is empty."""
    if not universe_domain:
      return properties.VALUES.core.universe_domain.default
    return universe_domain

  def ProcessPassword(self, password):
    if not password:
      return password
    return 'PASSWORD'


class InfoHolder(object):
  """Base object to hold all the configuration info."""

  def __init__(self, anonymizer=None):
    self.basic = BasicInfo(anonymizer)
    self.installation = InstallationInfo(anonymizer)
    self.config = ConfigInfo(anonymizer)
    self.env_proxy = ProxyInfoFromEnvironmentVars(anonymizer)
    self.logs = LogsInfo(anonymizer)
    self.tools = ToolsInfo(anonymizer)

  def __str__(self):
    out = io.StringIO()
    out.write(six.text_type(self.basic) + '\n')
    out.write(six.text_type(self.installation) + '\n')
    out.write(six.text_type(self.config) + '\n')
    if six.text_type(self.env_proxy):
      out.write(six.text_type(self.env_proxy) + '\n')
    out.write(six.text_type(self.logs) + '\n')
    out.write(six.text_type(self.tools) + '\n')
    return out.getvalue()


class BasicInfo(object):
  """Holds basic information about your system setup."""

  def __init__(self, anonymizer=None):
    anonymizer = anonymizer or NoopAnonymizer()
    platform = platforms.Platform.Current()
    self.version = config.CLOUD_SDK_VERSION
    self.operating_system = platform.operating_system
    self.architecture = platform.architecture
    self.python_location = anonymizer.ProcessPath(
        sys.executable and encoding.Decode(sys.executable))
    self.python_version = sys.version
    self.default_ca_certs_file = anonymizer.ProcessPath(certifi.where())
    self.site_packages = 'site' in sys.modules
    self.locale = self._GetDefaultLocale()

  def __str__(self):
    return textwrap.dedent("""\
        Google Cloud SDK [{version}]

        Platform: [{os}, {arch}] {uname}
        Locale: {locale}
        Python Version: [{python_version}]
        Python Location: [{python_location}]
        OpenSSL: [{openssl_version}]
        Requests Version: [{requests_version}]
        urllib3 Version: [{urllib3_version}]
        Default CA certs file: [{default_ca_certs_file}]
        Site Packages: [{site_packages}]
        """.format(
            version=self.version,
            os=(self.operating_system.name
                if self.operating_system else 'unknown'),
            arch=self.architecture.name if self.architecture else 'unknown',
            uname=system_platform.uname(),
            locale=self.locale,
            python_location=self.python_location,
            python_version=self.python_version.replace('\n', ' '),
            openssl_version=ssl.OPENSSL_VERSION,
            requests_version=requests.__version__,
            urllib3_version=urllib3.__version__,
            default_ca_certs_file=self.default_ca_certs_file,
            site_packages='Enabled' if self.site_packages else 'Disabled'))

  def _GetDefaultLocale(self):
    """Determines the locale from the program's environment.

    Returns:
      String: Default locale, with a fallback to locale environment variables.
    """
    env_vars = [
        '%s:%s' % (var, encoding.GetEncodedValue(os.environ, var))
        for var in ['LC_ALL', 'LC_CTYPE', 'LANG', 'LANGUAGE']
        if encoding.GetEncodedValue(os.environ, var)
    ]
    fallback_locale = '; '.join(env_vars)

    try:
      return locale.getlocale()
    except ValueError:
      return fallback_locale


class InstallationInfo(object):
  """Holds information about your Cloud SDK installation."""

  def __init__(self, anonymizer=None):
    anonymizer = anonymizer or NoopAnonymizer()
    self.sdk_root = anonymizer.ProcessPath(config.Paths().sdk_root)
    self.release_channel = config.INSTALLATION_CONFIG.release_channel
    self.repo_url = anonymizer.ProcessURL(
        config.INSTALLATION_CONFIG.snapshot_url)
    repos = properties.VALUES.component_manager.additional_repositories.Get(
        validate=False)
    self.additional_repos = (
        map(anonymizer.ProcessURL, repos.split(',')) if repos else [])
    # Keep it as array for structured output.
    path = encoding.GetEncodedValue(os.environ, 'PATH', '').split(os.pathsep)
    self.python_path = [anonymizer.ProcessPath(encoding.Decode(path_elem))
                        for path_elem in sys.path]

    if self.sdk_root:
      manager = update_manager.UpdateManager()
      self.components = manager.GetCurrentVersionsInformation()
      self.other_tool_paths = [anonymizer.ProcessPath(p)
                               for p in manager.FindAllOtherToolsOnPath()]
      self.duplicate_tool_paths = [
          anonymizer.ProcessPath(p)
          for p in manager.FindAllDuplicateToolsOnPath()]
      paths = [os.path.realpath(p) for p in path]
      this_path = os.path.realpath(
          os.path.join(self.sdk_root,
                       update_manager.UpdateManager.BIN_DIR_NAME))
      self.on_path = this_path in paths
    else:
      self.components = {}
      self.other_tool_paths = []
      self.duplicate_tool_paths = []
      self.on_path = False

    self.path = [anonymizer.ProcessPath(p) for p in path]
    self.kubectl = file_utils.SearchForExecutableOnPath('kubectl')
    if self.kubectl:
      self.kubectl = anonymizer.ProcessPath(self.kubectl[0])

  def __str__(self):
    out = io.StringIO()
    out.write('Installation Root: [{0}]\n'.format(
        self.sdk_root if self.sdk_root else 'N/A'))
    if config.INSTALLATION_CONFIG.IsAlternateReleaseChannel():
      out.write('Release Channel: [{0}]\n'.format(self.release_channel))
      out.write('Repository URL: [{0}]\n'.format(self.repo_url))
    if self.additional_repos:
      out.write('Additional Repositories:\n  {0}\n'.format(
          '\n  '.join(self.additional_repos)))

    if self.components:
      components = ['{0}: [{1}]'.format(name, value) for name, value in
                    six.iteritems(self.components)]
      out.write('Installed Components:\n  {0}\n'.format(
          '\n  '.join(components)))

    out.write('System PATH: [{0}]\n'.format(os.pathsep.join(self.path)))
    out.write('Python PATH: [{0}]\n'.format(os.pathsep.join(self.python_path)))
    out.write('Cloud SDK on PATH: [{0}]\n'.format(self.on_path))
    out.write('Kubectl on PATH: [{0}]\n'.format(self.kubectl or False))

    if self.other_tool_paths:
      out.write('\nWARNING: There are other instances of the Google Cloud '
                'Platform tools on your system PATH.\n  {0}\n'
                .format('\n  '.join(self.other_tool_paths)))
    if self.duplicate_tool_paths:
      out.write('There are alternate versions of the following Google Cloud '
                'Platform tools on your system PATH.\n  {0}\n'
                .format('\n  '.join(self.duplicate_tool_paths)))
    return out.getvalue()


class ConfigInfo(object):
  """Holds information about where config is stored and what values are set."""

  def __init__(self, anonymizer=None):
    anonymizer = anonymizer or NoopAnonymizer()
    cfg_paths = config.Paths()
    active_config = named_configs.ConfigurationStore.ActiveConfig()
    self.active_config_name = active_config.name
    self.paths = {
        'installation_properties_path':
            anonymizer.ProcessPath(cfg_paths.installation_properties_path),
        'global_config_dir':
            anonymizer.ProcessPath(cfg_paths.global_config_dir),
        'active_config_path': anonymizer.ProcessPath(active_config.file_path),
        'sdk_root': anonymizer.ProcessPath(cfg_paths.sdk_root)
    }
    self.account = anonymizer.ProcessAccount(
        properties.VALUES.core.account.Get(validate=False))
    self.project = anonymizer.ProcessProject(
        properties.VALUES.core.project.Get(validate=False))
    self.universe_domain = anonymizer.ProcessUniverseDomain(
        properties.VALUES.core.universe_domain.Get(validate=False)
    )
    self.properties = properties.VALUES.AllPropertyValues()
    if self.properties.get('core', {}).get('account'):
      self.properties['core']['account'].value = anonymizer.ProcessAccount(
          self.properties['core']['account'].value)
    if self.properties.get('core', {}).get('project'):
      self.properties['core']['project'].value = anonymizer.ProcessProject(
          self.properties['core']['project'].value)
    if self.properties.get('core', {}).get('universe_domain'):
      self.properties['core']['universe_domain'].value = (
          anonymizer.ProcessUniverseDomain(
              self.properties['core']['universe_domain'].value
          )
      )
    if self.properties.get('proxy', {}).get('username'):
      self.properties['proxy']['username'].value = anonymizer.ProcessUsername(
          self.properties['proxy']['username'].value)
    if self.properties.get('proxy', {}).get('password'):
      self.properties['proxy']['password'].value = anonymizer.ProcessPassword(
          self.properties['proxy']['password'].value)

  def __str__(self):
    out = io.StringIO()
    out.write('Installation Properties: [{0}]\n'
              .format(self.paths['installation_properties_path']))
    out.write('User Config Directory: [{0}]\n'
              .format(self.paths['global_config_dir']))
    out.write('Active Configuration Name: [{0}]\n'
              .format(self.active_config_name))
    out.write('Active Configuration Path: [{0}]\n\n'
              .format(self.paths['active_config_path']))

    out.write('Account: [{0}]\n'.format(self.account))
    out.write('Project: [{0}]\n'.format(self.project))

    all_cred_accounts = c_store.AllAccountsWithUniverseDomains()
    for account in all_cred_accounts:
      if account.account == self.account:
        cred_universe_domain = account.universe_domain
        break
    else:
      cred_universe_domain = None
    if cred_universe_domain and cred_universe_domain != self.universe_domain:
      domain_mismatch_warning = (
          ' WARNING: Mismatch with universe domain of account'
      )
    else:
      domain_mismatch_warning = ''
    out.write(
        'Universe Domain: [{0}]{1}\n\n'.format(
            self.universe_domain, domain_mismatch_warning
        )
    )

    out.write('Current Properties:\n')
    for section, props in six.iteritems(self.properties):
      out.write('  [{section}]\n'.format(section=section))
      for name, property_value in six.iteritems(props):
        out.write('    {name}: [{value}] ({source})\n'.format(
            name=name,
            value=str(property_value.value),
            source=property_value.source.value))

    return out.getvalue()


class ProxyInfoFromEnvironmentVars(object):
  """Proxy info if it is in the environment but not set in gcloud properties."""

  def __init__(self, anonymizer=None):
    anonymizer = anonymizer or NoopAnonymizer()
    self.type = None
    self.address = None
    self.port = None
    self.username = None
    self.password = None

    try:
      proxy_info, from_gcloud = http_proxy_setup.EffectiveProxyInfo()
    except properties.InvalidValueError:
      return

    if proxy_info and not from_gcloud:
      self.type = http_proxy_types.REVERSE_PROXY_TYPE_MAP.get(
          proxy_info.proxy_type, 'UNKNOWN PROXY TYPE')
      self.address = proxy_info.proxy_host
      self.port = proxy_info.proxy_port
      self.username = anonymizer.ProcessUsername(proxy_info.proxy_user)
      self.password = anonymizer.ProcessPassword(proxy_info.proxy_pass)

  def __str__(self):
    if not any([self.type, self.address, self.port, self.username,
                self.password]):
      return ''

    out = io.StringIO()
    out.write('Environmental Proxy Settings:\n')
    if self.type:
      out.write('  type: [{0}]\n'.format(self.type))
    if self.address:
      out.write('  address: [{0}]\n'.format(self.address))
    if self.port:
      out.write('  port: [{0}]\n'.format(self.port))
    # In Python 3, httplib2 encodes the proxy username and password when
    # initializing ProxyInfo, so we want to ensure they're decoded here before
    # displaying them.
    if self.username:
      out.write('  username: [{0}]\n'.format(encoding.Decode(self.username)))
    if self.password:
      out.write('  password: [{0}]\n'.format(encoding.Decode(self.password)))
    return out.getvalue()


def RecentLogFiles(logs_dir, num=1):
  """Finds the most recent (not current) gcloud log files.

  Args:
    logs_dir: str, The path to the logs directory being used.
    num: the number of log files to find

  Returns:
    A list of full paths to the latest num log files, excluding the current
    log file. If there are fewer than num log files, include all of
    them. They will be in chronological order.
  """
  date_dirs = FilesSortedByName(logs_dir)
  if not date_dirs:
    return []

  found_files = []
  for date_dir in reversed(date_dirs):
    log_files = reversed(FilesSortedByName(date_dir) or [])
    found_files.extend(log_files)
    if len(found_files) >= num + 1:
      return found_files[1:num+1]

  return found_files[1:]


def LastLogFile(logs_dir):
  """Finds the last (not current) gcloud log file.

  Args:
    logs_dir: str, The path to the logs directory being used.

  Returns:
    str, The full path to the last (but not the currently in use) log file
    if it exists, or None.
  """
  files = RecentLogFiles(logs_dir)
  if files:
    return files[0]
  return None


def FilesSortedByName(directory):
  """Gets the list of files in the given directory, sorted by name.

  Args:
    directory: str, The path to the directory to list.

  Returns:
    [str], The full paths of the files, sorted by file name, or None.
  """
  if not os.path.isdir(directory):
    return None
  dates = os.listdir(directory)
  if not dates:
    return None
  return [os.path.join(directory, date) for date in sorted(dates)]


class LogData(object):
  """Representation of a log file.

  Stores information such as the name of the log file, its contents, and the
  command run.
  """

  # This precedes the traceback in the log file.
  TRACEBACK_MARKER = 'BEGIN CRASH STACKTRACE\n'

  # This shows the command run in the log file
  COMMAND_REGEXP = r'Running \[(gcloud(?:\.[a-z-]+)*)\]'

  def __init__(self, filename, command, contents, traceback):
    self.filename = filename
    self.command = command
    self.contents = contents
    self.traceback = traceback

  def __str__(self):
    crash_detected = ' (crash detected)' if self.traceback else ''
    return '[{0}]: [{1}]{2}'.format(
        self.relative_path, self.command, crash_detected)

  @property
  def relative_path(self):
    """Returns path of log file relative to log directory, or the full path.

    Returns the full path when the log file is not *in* the log directory.

    Returns:
      str, the relative or full path of log file.
    """
    logs_dir = config.Paths().logs_dir
    if logs_dir is None:
      return self.filename

    rel_path = os.path.relpath(self.filename, config.Paths().logs_dir)
    if rel_path.startswith(os.path.pardir + os.path.sep):
      # That is, filename is NOT in logs_dir
      return self.filename

    return rel_path

  @property
  def date(self):
    """Return the date that this log file was created, based on its filename.

    Returns:
      datetime.datetime that the log file was created or None, if the filename
        pattern was not recognized.
    """
    datetime_string = ':'.join(os.path.split(self.relative_path))
    datetime_format = (log.DAY_DIR_FORMAT + ':' + log.FILENAME_FORMAT +
                       log.LOG_FILE_EXTENSION)
    try:
      return datetime.datetime.strptime(datetime_string, datetime_format)
    except ValueError:
      # This shouldn't happen, but it's better not to crash because of it.
      return None

  @classmethod
  def FromFile(cls, log_file):
    """Parse the file at the given path into a LogData.

    Args:
      log_file: str, the path to the log file to read

    Returns:
      LogData, representation of the log file
    """
    contents = file_utils.ReadFileContents(log_file)
    traceback = None
    command = None
    match = re.search(cls.COMMAND_REGEXP, contents)
    if match:
      # ex. gcloud.group.subgroup.command
      dotted_cmd_string, = match.groups()
      command = ' '.join(dotted_cmd_string.split('.'))
    if cls.TRACEBACK_MARKER in contents:
      traceback = (contents.split(cls.TRACEBACK_MARKER)[-1])
      # Trim any log lines that follow the traceback
      traceback = re.split(log.LOG_PREFIX_PATTERN, traceback)[0]
      traceback = traceback.strip()
    return cls(log_file, command, contents, traceback)


class LogsInfo(object):
  """Holds information about where logs are located."""

  NUM_RECENT_LOG_FILES = 5

  def __init__(self, anonymizer=None):
    anonymizer = anonymizer or NoopAnonymizer()
    paths = config.Paths()
    logs_dir = paths.logs_dir
    self.last_log = anonymizer.ProcessPath(LastLogFile(logs_dir))
    self.last_logs = [
        anonymizer.ProcessPath(f)
        for f in RecentLogFiles(logs_dir, self.NUM_RECENT_LOG_FILES)]
    self.logs_dir = anonymizer.ProcessPath(logs_dir)

  def __str__(self):
    return textwrap.dedent("""\
        Logs Directory: [{logs_dir}]
        Last Log File: [{log_file}]
        """.format(logs_dir=self.logs_dir, log_file=self.last_log))

  def LastLogContents(self):
    last_log = LastLogFile(config.Paths().logs_dir)
    if not self.last_log:
      return ''
    return file_utils.ReadFileContents(last_log)

  def GetRecentRuns(self):
    """Return the most recent runs, as reported by info_holder.LogsInfo.

    Returns:
      A list of LogData
    """
    last_logs = RecentLogFiles(config.Paths().logs_dir,
                               self.NUM_RECENT_LOG_FILES)
    return [LogData.FromFile(log_file) for log_file in last_logs]


class ToolsInfo(object):
  """Holds info about tools gcloud interacts with."""

  def __init__(self, anonymize=None):
    del anonymize  # Nothing to anonymize here.
    self.git_version = self._GitVersion()
    self.ssh_version = self._SshVersion()

  def _GitVersion(self):
    return self._GetVersion(['git', '--version'])

  def _SshVersion(self):
    return self._GetVersion(['ssh', '-V'])

  def _GetVersion(self, cmd):
    """Return tools version."""
    try:
      proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
    except OSError:
      return 'NOT AVAILABLE'
    stdoutdata, _ = proc.communicate()
    data = [f for f in stdoutdata.split(b'\n') if f]
    if len(data) != 1:
      return 'NOT AVAILABLE'
    else:
      return encoding.Decode(data[0])

  def __str__(self):
    return textwrap.dedent("""\
        git: [{git}]
        ssh: [{ssh}]
        """.format(git=self.git_version, ssh=self.ssh_version))
