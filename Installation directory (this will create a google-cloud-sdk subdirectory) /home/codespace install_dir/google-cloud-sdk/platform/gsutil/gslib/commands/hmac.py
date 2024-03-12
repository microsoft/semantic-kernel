# -*- coding: utf-8 -*-
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""
Implementation of HMAC key management command for GCS.

NOTE: Any modification to this file or corresponding HMAC logic
should be submitted in its own PR and release to avoid
concurrency issues in testing.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.help_provider import CreateHelpText
from gslib.metrics import LogCommandParams
from gslib.project_id import PopulateProjectId
from gslib.utils.cloud_api_helper import GetCloudApiInstance
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils.text_util import InsistAscii
from gslib.utils import shim_util

_CREATE_SYNOPSIS = """
  gsutil hmac create [-p <project>] <service_account_email>
"""

_DELETE_SYNOPSIS = """
  gsutil hmac delete [-p <project>] <access_id>
"""

_GET_SYNOPSIS = """
  gsutil hmac get [-p <project>] <access_id>
"""

_LIST_SYNOPSIS = """
  gsutil hmac list [-a] [-l] [-p <project>] [-u <service_account_email>]
"""

_UPDATE_SYNOPSIS = """
  gsutil hmac update -s (ACTIVE|INACTIVE) [-e <etag>] [-p <project>] <access_id>
"""

_CREATE_DESCRIPTION = """
<B>CREATE</B>
  The ``hmac create`` command creates an HMAC key for the specified service
  account:

    gsutil hmac create test.service.account@test_project.iam.gserviceaccount.com

  The secret key material is only available upon creation, so be sure to store
  the returned secret along with the access_id.

<B>CREATE OPTIONS</B>
  The ``create`` sub-command has the following option

  -p <project>                Specify the ID or number of the project in which
                              to create a key.
"""

_DELETE_DESCRIPTION = """
<B>DELETE</B>
  The ``hmac delete`` command permanently deletes the specified HMAC key:

    gsutil hmac delete GOOG56JBMFZX6PMPTQ62VD2

  Note that keys must be updated to be in the ``INACTIVE`` state before they can be
  deleted.

<B>DELETE OPTIONS</B>
  The ``delete`` sub-command has the following option

  -p <project>                Specify the ID or number of the project from which to
                              delete a key.
"""

_GET_DESCRIPTION = """
<B>GET</B>
  The ``hmac get`` command retrieves the specified HMAC key's metadata:

    gsutil hmac get GOOG56JBMFZX6PMPTQ62VD2

  Note that there is no option to retrieve a key's secret material after it has
  been created.

<B>GET OPTIONS</B>
  The ``get`` sub-command has the following option

  -p <project>                Specify the ID or number of the project from which to
                              get a key.
"""

_LIST_DESCRIPTION = """
<B>LIST</B>
  The ``hmac list`` command lists the HMAC key metadata for keys in the
  specified project. If no project is specified in the command, the default
  project is used.

<B>LIST OPTIONS</B>
  The ``list`` sub-command has the following options

  -a                          Show all keys, including recently deleted
                              keys.

  -l                          Use long listing format. Shows each key's full
                              metadata excluding the secret.

  -p <project>                Specify the ID or number of the project from
                              which to list keys.

  -u <service_account_email>  Filter keys for a single service account.
"""
_UPDATE_DESCRIPTION = """
<B>UPDATE</B>
  The ``hmac update`` command sets the state of the specified key:

    gsutil hmac update -s INACTIVE -e M42da= GOOG56JBMFZX6PMPTQ62VD2

  Valid state arguments are ``ACTIVE`` and ``INACTIVE``. To set a key to state
  ``DELETED``, use the ``hmac delete`` command on an ``INACTIVE`` key. If an etag
  is set in the command, it will only succeed if the provided etag matches the etag
  of the stored key.

<B>UPDATE OPTIONS</B>
  The ``update`` sub-command has the following options

  -s <ACTIVE|INACTIVE>        Sets the state of the specified key to either
                              ``ACTIVE`` or ``INACTIVE``.

  -e <etag>                   If provided, the update will only be performed
                              if the specified etag matches the etag of the
                              stored key.

  -p <project>                Specify the ID or number of the project in
                              which to update a key.
"""

_SYNOPSIS = (_CREATE_SYNOPSIS + _DELETE_SYNOPSIS.lstrip('\n') +
             _GET_SYNOPSIS.lstrip('\n') + _LIST_SYNOPSIS.lstrip('\n') +
             _UPDATE_SYNOPSIS.lstrip('\n') + '\n\n')

_DESCRIPTION = """
  You can use the ``hmac`` command to interact with service account `HMAC keys
  <https://cloud.google.com/storage/docs/authentication/hmackeys>`_.

  The ``hmac`` command has five sub-commands:
""" + '\n'.join([
    _CREATE_DESCRIPTION,
    _DELETE_DESCRIPTION,
    _GET_DESCRIPTION,
    _LIST_DESCRIPTION,
    _UPDATE_DESCRIPTION,
])

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)

_VALID_UPDATE_STATES = ['INACTIVE', 'ACTIVE']
_TIME_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

_create_help_text = CreateHelpText(_CREATE_SYNOPSIS, _CREATE_DESCRIPTION)
_delete_help_text = CreateHelpText(_DELETE_SYNOPSIS, _DELETE_DESCRIPTION)
_get_help_text = CreateHelpText(_GET_SYNOPSIS, _GET_DESCRIPTION)
_list_help_text = CreateHelpText(_LIST_SYNOPSIS, _LIST_DESCRIPTION)
_update_help_text = CreateHelpText(_UPDATE_SYNOPSIS, _UPDATE_DESCRIPTION)


def _AccessIdException(command_name, subcommand, synopsis):
  return CommandException(
      '%s %s requires an Access ID to be specified as the last argument.\n%s' %
      (command_name, subcommand, synopsis))


def _KeyMetadataOutput(metadata):
  """Format the key metadata for printing to the console."""

  def FormatInfo(name, value, new_line=True):
    """Format the metadata name-value pair into two aligned columns."""
    width = 22
    info_str = '\t%-*s %s' % (width, name + ':', value)
    if new_line:
      info_str += '\n'
    return info_str

  message = 'Access ID %s:\n' % metadata.accessId
  message += FormatInfo('State', metadata.state)
  message += FormatInfo('Service Account', metadata.serviceAccountEmail)
  message += FormatInfo('Project', metadata.projectId)
  message += FormatInfo('Time Created',
                        metadata.timeCreated.strftime(_TIME_FORMAT))
  message += FormatInfo('Time Last Updated',
                        metadata.updated.strftime(_TIME_FORMAT))
  message += FormatInfo('Etag', metadata.etag, new_line=False)
  return message


_CREATE_COMMAND_FORMAT = ('--format=value[separator="' +
                          shim_util.get_format_flag_newline() + '"](' +
                          'format("Access ID:   {}", metadata.accessId),' +
                          'format("Secret:      {}", secret))')
_DESCRIBE_COMMAND_FORMAT = (
    '--format=value[separator="' + shim_util.get_format_flag_newline() +
    '"](format("Access ID {}:", accessId),' +
    'format("\tState:                 {}", state),' +
    'format("\tService Account:       {}", serviceAccountEmail),' +
    'format("\tProject:               {}", projectId),' +
    'format("\tTime Created:          {}",' +
    ' timeCreated.date(format="%a %d %b %Y %H:%M:%S GMT")),' +
    'format("\tTime Last Updated:     {}",' +
    ' updated.date(format="%a %d %b %Y %H:%M:%S GMT")),' +
    'format("\tEtag:                  {}", etag))')

_LIST_COMMAND_SHORT_FORMAT = (
    '--format=table[no-heading](format("{} ", accessId),'
    'state:width=11, serviceAccountEmail)')

_PROJECT_FLAG = GcloudStorageFlag('--project')

CREATE_COMMAND = GcloudStorageMap(
    gcloud_command=['storage', 'hmac', 'create', _CREATE_COMMAND_FORMAT],
    flag_map={
        '-p': _PROJECT_FLAG,
    })

DELETE_COMMAND = GcloudStorageMap(gcloud_command=['storage', 'hmac', 'delete'],
                                  flag_map={
                                      '-p': _PROJECT_FLAG,
                                  })

GET_COMMAND = GcloudStorageMap(
    gcloud_command=['storage', 'hmac', 'describe', _DESCRIBE_COMMAND_FORMAT],
    flag_map={'-p': _PROJECT_FLAG})

LIST_COMMAND = GcloudStorageMap(
    gcloud_command=['storage', 'hmac', 'list', _LIST_COMMAND_SHORT_FORMAT],
    flag_map={
        '-a': GcloudStorageFlag('--all'),
        '-u': GcloudStorageFlag('--service-account'),
        '-p': _PROJECT_FLAG
    })

LIST_COMMAND_LONG_FORMAT = GcloudStorageMap(
    gcloud_command=['storage', 'hmac', 'list', _DESCRIBE_COMMAND_FORMAT],
    flag_map={
        '-a': GcloudStorageFlag('--all'),
        '-l': GcloudStorageFlag('--long'),
        '-u': GcloudStorageFlag('--service-account'),
        '-p': _PROJECT_FLAG
    })

UPDATE_COMMAND = GcloudStorageMap(
    gcloud_command=['storage', 'hmac', 'update', _DESCRIBE_COMMAND_FORMAT],
    flag_map={
        '-s':
            GcloudStorageFlag({
                'ACTIVE': '--activate',
                'INACTIVE': '--deactivate',
            }),
        '-e':
            GcloudStorageFlag('--etag'),
        '-p':
            _PROJECT_FLAG
    })


class HmacCommand(Command):
  """Implementation of gsutil hmac command."""
  command_spec = Command.CreateCommandSpec(
      'hmac',
      min_args=1,
      max_args=8,
      supported_sub_args='ae:lp:s:u:',
      file_url_ok=True,
      urls_start_arg=1,
      gs_api_support=[ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      usage_synopsis=_SYNOPSIS,
      argparse_arguments={
          'create': [CommandArgument.MakeZeroOrMoreCloudOrFileURLsArgument()],
          'delete': [CommandArgument.MakeZeroOrMoreCloudOrFileURLsArgument()],
          'get': [CommandArgument.MakeZeroOrMoreCloudOrFileURLsArgument()],
          'list': [CommandArgument.MakeZeroOrMoreCloudOrFileURLsArgument()],
          'update': [CommandArgument.MakeZeroOrMoreCloudOrFileURLsArgument()],
      },
  )

  help_spec = Command.HelpSpec(
      help_name='hmac',
      help_name_aliases=[],
      help_type='command_help',
      help_one_line_summary=('CRUD operations on service account HMAC keys.'),
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={
          'create': _create_help_text,
          'delete': _delete_help_text,
          'get': _get_help_text,
          'list': _list_help_text,
          'update': _update_help_text,
      })

  def get_gcloud_storage_args(self):
    if self.args[0] == 'list' and '-l' in self.args:
      gcloud_storage_map = GcloudStorageMap(
          gcloud_command={'list': LIST_COMMAND_LONG_FORMAT},
          flag_map={},
      )
    else:
      gcloud_storage_map = GcloudStorageMap(
          gcloud_command={
              'create': CREATE_COMMAND,
              'delete': DELETE_COMMAND,
              'update': UPDATE_COMMAND,
              'get': GET_COMMAND,
              'list': LIST_COMMAND
          },
          flag_map={},
      )

    return super().get_gcloud_storage_args(gcloud_storage_map)

  def _CreateHmacKey(self, thread_state=None):
    """Creates HMAC key for a service account."""
    if self.args:
      self.service_account_email = self.args[0]
    else:
      err_msg = ('%s %s requires a service account to be specified as the '
                 'last argument.\n%s')
      raise CommandException(
          err_msg %
          (self.command_name, self.action_subcommand, _CREATE_SYNOPSIS))

    gsutil_api = GetCloudApiInstance(self, thread_state=thread_state)

    response = gsutil_api.CreateHmacKey(self.project_id,
                                        self.service_account_email,
                                        provider='gs')

    print('%-12s %s' % ('Access ID:', response.metadata.accessId))
    print('%-12s %s' % ('Secret:', response.secret))

  def _DeleteHmacKey(self, thread_state=None):
    """Deletes an HMAC key."""
    if self.args:
      access_id = self.args[0]
    else:
      raise _AccessIdException(self.command_name, self.action_subcommand,
                               _DELETE_SYNOPSIS)

    gsutil_api = GetCloudApiInstance(self, thread_state=thread_state)

    gsutil_api.DeleteHmacKey(self.project_id, access_id, provider='gs')

  def _GetHmacKey(self, thread_state=None):
    """Gets HMAC key from its Access Id."""
    if self.args:
      access_id = self.args[0]
    else:
      raise _AccessIdException(self.command_name, self.action_subcommand,
                               _GET_SYNOPSIS)

    gsutil_api = GetCloudApiInstance(self, thread_state=thread_state)

    response = gsutil_api.GetHmacKey(self.project_id, access_id, provider='gs')

    print(_KeyMetadataOutput(response))

  def _ListHmacKeys(self, thread_state=None):
    """Lists HMAC keys for a project or service account."""
    if self.args:
      raise CommandException(
          '%s %s received unexpected arguments.\n%s' %
          (self.command_name, self.action_subcommand, _LIST_SYNOPSIS))

    gsutil_api = GetCloudApiInstance(self, thread_state=thread_state)

    response = gsutil_api.ListHmacKeys(self.project_id,
                                       self.service_account_email,
                                       self.show_all,
                                       provider='gs')

    short_list_format = '%s\t%-12s %s'
    if self.long_list:
      for item in response:
        print(_KeyMetadataOutput(item))
        print()
    else:
      for item in response:
        print(short_list_format %
              (item.accessId, item.state, item.serviceAccountEmail))

  def _UpdateHmacKey(self, thread_state=None):
    """Update an HMAC key's state."""
    if not self.state:
      raise CommandException(
          'A state flag must be supplied for %s %s\n%s' %
          (self.command_name, self.action_subcommand, _UPDATE_SYNOPSIS))
    elif self.state not in _VALID_UPDATE_STATES:
      raise CommandException('The state flag value must be one of %s' %
                             ', '.join(_VALID_UPDATE_STATES))
    if self.args:
      access_id = self.args[0]
    else:
      raise _AccessIdException(self.command_name, self.action_subcommand,
                               _UPDATE_SYNOPSIS)

    gsutil_api = GetCloudApiInstance(self, thread_state=thread_state)

    response = gsutil_api.UpdateHmacKey(self.project_id,
                                        access_id,
                                        self.state,
                                        self.etag,
                                        provider='gs')

    print(_KeyMetadataOutput(response))

  def RunCommand(self):
    """Command entry point for the hmac command."""

    if self.gsutil_api.GetApiSelector(provider='gs') != ApiSelector.JSON:
      raise CommandException(
          'The "hmac" command can only be used with the GCS JSON API')

    self.action_subcommand = self.args.pop(0)
    self.ParseSubOpts(check_args=True)
    # Commands with both suboptions and subcommands need to reparse for
    # suboptions, so we log again.
    LogCommandParams(sub_opts=self.sub_opts)

    self.service_account_email = None
    self.state = None
    self.show_all = False
    self.long_list = False
    self.etag = None

    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-u':
          self.service_account_email = a
        elif o == '-p':
          # Project IDs are sent as header values when using gs and s3 XML APIs.
          InsistAscii(a, 'Invalid non-ASCII character found in project ID')
          self.project_id = a
        elif o == '-s':
          self.state = a
        elif o == '-a':
          self.show_all = True
        elif o == '-l':
          self.long_list = True
        elif o == '-e':
          self.etag = a

    if not self.project_id:
      self.project_id = PopulateProjectId(None)

    method_for_arg = {
        'create': self._CreateHmacKey,
        'delete': self._DeleteHmacKey,
        'get': self._GetHmacKey,
        'list': self._ListHmacKeys,
        'update': self._UpdateHmacKey,
    }
    if self.action_subcommand not in method_for_arg:
      raise CommandException('Invalid subcommand "%s" for the %s command.\n'
                             'See "gsutil help hmac".' %
                             (self.action_subcommand, self.command_name))

    LogCommandParams(subcommands=[self.action_subcommand])
    method_for_arg[self.action_subcommand]()

    return 0
