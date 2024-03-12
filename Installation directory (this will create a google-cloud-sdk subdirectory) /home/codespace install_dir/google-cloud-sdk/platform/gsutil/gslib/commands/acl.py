# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
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
"""Implementation of acl command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py import encoding
from gslib import metrics
from gslib import gcs_json_api
from gslib.cloud_api import AccessDeniedException
from gslib.cloud_api import BadRequestException
from gslib.cloud_api import PreconditionException
from gslib.cloud_api import Preconditions
from gslib.cloud_api import ServiceException
from gslib.command import Command
from gslib.command import SetAclExceptionHandler
from gslib.command import SetAclFuncWrapper
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.help_provider import CreateHelpText
from gslib.storage_url import StorageUrlFromString
from gslib.storage_url import UrlsAreForSingleProvider
from gslib.storage_url import RaiseErrorIfUrlsAreMixOfBucketsAndObjects
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils import acl_helper
from gslib.utils.constants import NO_MAX
from gslib.utils.retry_util import Retry
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap

_SET_SYNOPSIS = """
  gsutil acl set [-f] [-r] [-a] (<file-path>|<predefined-acl>) url...
"""

_GET_SYNOPSIS = """
  gsutil acl get url
"""

_CH_SYNOPSIS = """
  gsutil acl ch [-f] [-r] <grant>... url...

  where each <grant> is one of the following forms:

    -u <id>|<email>:<permission>
    -g <id>|<email>|<domain>|All|AllAuth:<permission>
    -p (viewers|editors|owners)-<project number>:<permission>
    -d <id>|<email>|<domain>|All|AllAuth|(viewers|editors|owners)-<project number>
"""

_GET_DESCRIPTION = """
<B>GET</B>
  The ``acl get`` command gets the ACL text for a bucket or object, which you
  can save and edit for the acl set command.
"""

_SET_DESCRIPTION = """
<B>SET</B>
  The ``acl set`` command allows you to set an Access Control List on one or
  more buckets and objects. As part of the command, you must specify either a
  predefined ACL or the path to a file that contains ACL text. The simplest way
  to use the ``acl set`` command is to specify one of the predefined ACLs,
  e.g.,:

    gsutil acl set private gs://example-bucket/example-object

  If you want to make an object or bucket publicly readable or writable, it is
  recommended to use ``acl ch``, to avoid accidentally removing OWNER
  permissions. See the ``acl ch`` section for details.

  See `Predefined ACLs
  <https://cloud.google.com/storage/docs/access-control/lists#predefined-acl>`_
  for a list of predefined ACLs.

  If you want to define more fine-grained control over your data, you can
  retrieve an ACL using the ``acl get`` command, save the output to a file, edit
  the file, and then use the ``acl set`` command to set that ACL on the buckets
  and/or objects. For example:

    gsutil acl get gs://bucket/file.txt > acl.txt

  Make changes to acl.txt such as adding an additional grant, then:

    gsutil acl set acl.txt gs://cats/file.txt

  Note that you can set an ACL on multiple buckets or objects at once. For
  example, to set ACLs on all .jpg files found in a bucket:

    gsutil acl set acl.txt gs://bucket/**.jpg

  If you have a large number of ACLs to update you might want to use the
  gsutil -m option, to perform a parallel (multi-threaded/multi-processing)
  update:

    gsutil -m acl set acl.txt gs://bucket/**.jpg

  Note that multi-threading/multi-processing is only done when the named URLs
  refer to objects, which happens either if you name specific objects or
  if you enumerate objects by using an object wildcard or specifying
  the acl -r flag.


<B>SET OPTIONS</B>
  The "set" sub-command has the following options

  -R, -r      Performs "acl set" request recursively, to all objects under
              the specified URL.

  -a          Performs "acl set" request on all object versions.

  -f          Normally gsutil stops at the first error. The -f option causes
              it to continue when it encounters errors. If some of the ACLs
              couldn't be set, gsutil's exit status will be non-zero even if
              this flag is set. This option is implicitly set when running
              "gsutil -m acl...".
"""

_CH_DESCRIPTION = """
<B>CH</B>
  The "acl ch" (or "acl change") command updates access control lists, similar
  in spirit to the Linux chmod command. You can specify multiple access grant
  additions and deletions in a single command run; all changes will be made
  atomically to each object in turn. For example, if the command requests
  deleting one grant and adding a different grant, the ACLs being updated will
  never be left in an intermediate state where one grant has been deleted but
  the second grant not yet added. Each change specifies a user or group grant
  to add or delete, and for grant additions, one of R, W, O (for the
  permission to be granted). A more formal description is provided in a later
  section; below we provide examples.

<B>CH EXAMPLES</B>
  Examples for "ch" sub-command:

  Grant anyone on the internet READ access to the object example-object:

    gsutil acl ch -u allUsers:R gs://example-bucket/example-object

  NOTE: By default, publicly readable objects are served with a Cache-Control
  header allowing such objects to be cached for 3600 seconds. If you need to
  ensure that updates become visible immediately, you should set a
  Cache-Control header of "Cache-Control:private, max-age=0, no-transform" on
  such objects. For help doing this, see "gsutil help setmeta".

  Grant the user john.doe@example.com READ access to all objects
  in example-bucket that begin with folder/:

    gsutil acl ch -r -u john.doe@example.com:R gs://example-bucket/folder/

  Grant the group admins@example.com OWNER access to all jpg files in
  example-bucket:

    gsutil acl ch -g admins@example.com:O gs://example-bucket/**.jpg

  Grant the owners of project example-project WRITE access to the bucket
  example-bucket:

    gsutil acl ch -p owners-example-project:W gs://example-bucket

  NOTE: You can replace 'owners' with 'viewers' or 'editors' to grant access
  to a project's viewers/editors respectively.

  Remove access to the bucket example-bucket for the viewers of project number
  12345:

    gsutil acl ch -d viewers-12345 gs://example-bucket

  NOTE: You cannot remove the project owners group from ACLs of gs:// buckets in
  the given project. Attempts to do so will appear to succeed, but the service
  will add the project owners group into the new set of ACLs before applying it.

  Note that removing a project requires you to reference the project by
  its number (which you can see with the acl get command) as opposed to its
  project ID string.

  Grant the service account foo@developer.gserviceaccount.com WRITE access to
  the bucket example-bucket:

    gsutil acl ch -u foo@developer.gserviceaccount.com:W gs://example-bucket

  Grant all users from the `G Suite
  <https://www.google.com/work/apps/business/>`_ domain my-domain.org READ
  access to the bucket gcs.my-domain.org:

    gsutil acl ch -g my-domain.org:R gs://gcs.my-domain.org

  Remove any current access by john.doe@example.com from the bucket
  example-bucket:

    gsutil acl ch -d john.doe@example.com gs://example-bucket

  If you have a large number of objects to update, enabling multi-threading
  with the gsutil -m flag can significantly improve performance. The
  following command adds OWNER for admin@example.org using
  multi-threading:

    gsutil -m acl ch -r -u admin@example.org:O gs://example-bucket

  Grant READ access to everyone from my-domain.org and to all authenticated
  users, and grant OWNER to admin@mydomain.org, for the buckets
  my-bucket and my-other-bucket, with multi-threading enabled:

    gsutil -m acl ch -r -g my-domain.org:R -g AllAuth:R \\
      -u admin@mydomain.org:O gs://my-bucket/ gs://my-other-bucket

<B>CH ROLES</B>
  You may specify the following roles with either their shorthand or
  their full name:

    R: READ
    W: WRITE
    O: OWNER

  For more information on these roles and the access they grant, see the
  permissions section of the `Access Control Lists page
  <https://cloud.google.com/storage/docs/access-control/lists#permissions>`_.

<B>CH ENTITIES</B>
  There are four different entity types: Users, Groups, All Authenticated Users,
  and All Users.

  Users are added with -u and a plain ID or email address, as in
  "-u john-doe@gmail.com:r". Note: Service Accounts are considered to be users.

  Groups are like users, but specified with the -g flag, as in
  "-g power-users@example.com:O". Groups may also be specified as a full
  domain, as in "-g my-company.com:r".

  allAuthenticatedUsers and allUsers are specified directly, as
  in "-g allUsers:R" or "-g allAuthenticatedUsers:O". These are case
  insensitive, and may be shortened to "all" and "allauth", respectively.

  Removing roles is specified with the -d flag and an ID, email
  address, domain, or one of allUsers or allAuthenticatedUsers.

  Many entities' roles can be specified on the same command line, allowing
  bundled changes to be executed in a single run. This will reduce the number of
  requests made to the server.

<B>CH OPTIONS</B>
  The "ch" sub-command has the following options

  -d          Remove all roles associated with the matching entity.

  -f          Normally gsutil stops at the first error. The -f option causes
              it to continue when it encounters errors. With this option the
              gsutil exit status will be 0 even if some ACLs couldn't be
              changed.

  -g          Add or modify a group entity's role.

  -p          Add or modify a project viewers/editors/owners role.

  -R, -r      Performs acl ch request recursively, to all objects under the
              specified URL.

  -u          Add or modify a user entity's role.
"""

_SYNOPSIS = (_SET_SYNOPSIS + _GET_SYNOPSIS.lstrip('\n') +
             _CH_SYNOPSIS.lstrip('\n') + '\n\n')

_DESCRIPTION = ("""
  The acl command has three sub-commands:
""" + '\n'.join([_GET_DESCRIPTION, _SET_DESCRIPTION, _CH_DESCRIPTION]))

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)

_get_help_text = CreateHelpText(_GET_SYNOPSIS, _GET_DESCRIPTION)
_set_help_text = CreateHelpText(_SET_SYNOPSIS, _SET_DESCRIPTION)
_ch_help_text = CreateHelpText(_CH_SYNOPSIS, _CH_DESCRIPTION)


def _ApplyExceptionHandler(cls, exception):
  cls.logger.error('Encountered a problem: %s', exception)
  cls.everything_set_okay = False


def _ApplyAclChangesWrapper(cls, url_or_expansion_result, thread_state=None):
  cls.ApplyAclChanges(url_or_expansion_result, thread_state=thread_state)


class AclCommand(Command):
  """Implementation of gsutil acl command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'acl',
      command_name_aliases=['getacl', 'setacl', 'chacl'],
      usage_synopsis=_SYNOPSIS,
      min_args=2,
      max_args=NO_MAX,
      supported_sub_args='afRrg:u:d:p:',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=1,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments={
          'set': [
              CommandArgument.MakeFileURLOrCannedACLArgument(),
              CommandArgument.MakeZeroOrMoreCloudURLsArgument()
          ],
          'get': [CommandArgument.MakeNCloudURLsArgument(1)],
          'ch': [CommandArgument.MakeZeroOrMoreCloudURLsArgument()],
      })
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='acl',
      help_name_aliases=['getacl', 'setacl', 'chmod', 'chacl'],
      help_type='command_help',
      help_one_line_summary='Get, set, or change bucket and/or object ACLs',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={
          'get': _get_help_text,
          'set': _set_help_text,
          'ch': _ch_help_text
      },
  )

  def _get_shim_command_group(self):
    object_or_bucket_urls = [StorageUrlFromString(url) for url in self.args]
    recurse = False
    for (flag_key, _) in self.sub_opts:
      if flag_key in ('-r', '-R'):
        recurse = True
        break
    RaiseErrorIfUrlsAreMixOfBucketsAndObjects(object_or_bucket_urls, recurse)

    if object_or_bucket_urls[0].IsBucket() and not recurse:
      return 'buckets'
    else:
      return 'objects'

  def get_gcloud_storage_args(self):
    sub_command = self.args.pop(0)
    if sub_command == 'get':
      if StorageUrlFromString(self.args[0]).IsObject():
        command_group = 'objects'
      else:
        command_group = 'buckets'
      gcloud_storage_map = GcloudStorageMap(gcloud_command=[
          'storage', command_group, 'describe',
          '--format=multi(acl:format=json)', '--raw'
      ],
                                            flag_map={})

    elif sub_command == 'set':
      # Flags must be at the start of self.args to get parsed.
      self.ParseSubOpts()
      acl_file_or_predefined_acl = self.args.pop(0)
      if os.path.isfile(acl_file_or_predefined_acl):
        acl_flag = '--acl-file=' + acl_file_or_predefined_acl
      else:
        if acl_file_or_predefined_acl in (
            gcs_json_api.FULL_PREDEFINED_ACL_XML_TO_JSON_TRANSLATION):
          predefined_acl = (
              gcs_json_api.FULL_PREDEFINED_ACL_XML_TO_JSON_TRANSLATION[
                  acl_file_or_predefined_acl])
        else:
          predefined_acl = acl_file_or_predefined_acl
        acl_flag = '--predefined-acl=' + predefined_acl

      command_group = self._get_shim_command_group()

      gcloud_storage_map = GcloudStorageMap(
          gcloud_command=['storage', command_group, 'update'] + [acl_flag],
          flag_map={
              '-a': GcloudStorageFlag('--all-versions'),
              '-f': GcloudStorageFlag('--continue-on-error'),
              '-R': GcloudStorageFlag('--recursive'),
              '-r': GcloudStorageFlag('--recursive'),
          })

    elif sub_command == 'ch':
      self.ParseSubOpts()
      self.sub_opts = acl_helper.translate_sub_opts_for_shim(self.sub_opts)
      command_group = self._get_shim_command_group()

      gcloud_storage_map = GcloudStorageMap(
          gcloud_command=['storage', command_group, 'update'],
          flag_map={
              '-g': GcloudStorageFlag('--add-acl-grant'),
              '-p': GcloudStorageFlag('--add-acl-grant'),
              '-u': GcloudStorageFlag('--add-acl-grant'),
              '-d': GcloudStorageFlag('--remove-acl-grant'),
              '-a': GcloudStorageFlag('--all-versions'),
              '-f': GcloudStorageFlag('--continue-on-error'),
              '-R': GcloudStorageFlag('--recursive'),
              '-r': GcloudStorageFlag('--recursive'),
          })

    return super().get_gcloud_storage_args(gcloud_storage_map)

  def _CalculateUrlsStartArg(self):
    if not self.args:
      self.RaiseWrongNumberOfArgumentsException()
    if (self.args[0].lower() == 'set') or (self.command_alias_used == 'setacl'):
      return 1
    else:
      return 0

  def _SetAcl(self):
    """Parses options and sets ACLs on the specified buckets/objects."""
    self.continue_on_error = False
    if self.sub_opts:
      for o, unused_a in self.sub_opts:
        if o == '-a':
          self.all_versions = True
        elif o == '-f':
          self.continue_on_error = True
        elif o == '-r' or o == '-R':
          self.recursion_requested = True
        else:
          self.RaiseInvalidArgumentException()
    try:
      self.SetAclCommandHelper(SetAclFuncWrapper, SetAclExceptionHandler)
    except AccessDeniedException as unused_e:
      self._WarnServiceAccounts()
      raise
    if not self.everything_set_okay:
      raise CommandException('ACLs for some objects could not be set.')

  def _ChAcl(self):
    """Parses options and changes ACLs on the specified buckets/objects."""
    self.parse_versions = True
    self.changes = []
    self.continue_on_error = False

    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-f':
          self.continue_on_error = True
        elif o == '-g':
          if 'gserviceaccount.com' in a:
            raise CommandException(
                'Service accounts are considered users, not groups; please use '
                '"gsutil acl ch -u" instead of "gsutil acl ch -g"')
          self.changes.append(
              acl_helper.AclChange(a, scope_type=acl_helper.ChangeType.GROUP))
        elif o == '-p':
          self.changes.append(
              acl_helper.AclChange(a, scope_type=acl_helper.ChangeType.PROJECT))
        elif o == '-u':
          self.changes.append(
              acl_helper.AclChange(a, scope_type=acl_helper.ChangeType.USER))
        elif o == '-d':
          self.changes.append(acl_helper.AclDel(a))
        elif o == '-r' or o == '-R':
          self.recursion_requested = True
        else:
          self.RaiseInvalidArgumentException()

    if not self.changes:
      raise CommandException('Please specify at least one access change '
                             'with the -g, -u, or -d flags')

    if (not UrlsAreForSingleProvider(self.args) or
        StorageUrlFromString(self.args[0]).scheme != 'gs'):
      raise CommandException(
          'The "{0}" command can only be used with gs:// URLs'.format(
              self.command_name))

    self.everything_set_okay = True
    self.ApplyAclFunc(_ApplyAclChangesWrapper,
                      _ApplyExceptionHandler,
                      self.args,
                      object_fields=['acl', 'generation', 'metageneration'])
    if not self.everything_set_okay:
      raise CommandException('ACLs for some objects could not be set.')

  def _RaiseForAccessDenied(self, url):
    self._WarnServiceAccounts()
    raise CommandException('Failed to set acl for %s. Please ensure you have '
                           'OWNER-role access to this resource.' % url)

  @Retry(ServiceException, tries=3, timeout_secs=1)
  def ApplyAclChanges(self, name_expansion_result, thread_state=None):
    """Applies the changes in self.changes to the provided URL.

    Args:
      name_expansion_result: NameExpansionResult describing the target object.
      thread_state: If present, gsutil Cloud API instance to apply the changes.
    """
    if thread_state:
      gsutil_api = thread_state
    else:
      gsutil_api = self.gsutil_api

    url = name_expansion_result.expanded_storage_url
    if url.IsBucket():
      bucket = gsutil_api.GetBucket(url.bucket_name,
                                    provider=url.scheme,
                                    fields=['acl', 'metageneration'])
      current_acl = bucket.acl
    elif url.IsObject():
      gcs_object = encoding.JsonToMessage(apitools_messages.Object,
                                          name_expansion_result.expanded_result)
      current_acl = gcs_object.acl

    if not current_acl:
      self._RaiseForAccessDenied(url)
    if self._ApplyAclChangesAndReturnChangeCount(url, current_acl) == 0:
      self.logger.info('No changes to %s', url)
      return

    try:
      if url.IsBucket():
        preconditions = Preconditions(meta_gen_match=bucket.metageneration)
        bucket_metadata = apitools_messages.Bucket(acl=current_acl)
        gsutil_api.PatchBucket(url.bucket_name,
                               bucket_metadata,
                               preconditions=preconditions,
                               provider=url.scheme,
                               fields=['id'])
      else:  # Object
        preconditions = Preconditions(gen_match=gcs_object.generation,
                                      meta_gen_match=gcs_object.metageneration)
        object_metadata = apitools_messages.Object(acl=current_acl)
        try:
          gsutil_api.PatchObjectMetadata(url.bucket_name,
                                         url.object_name,
                                         object_metadata,
                                         preconditions=preconditions,
                                         provider=url.scheme,
                                         generation=url.generation,
                                         fields=['id'])
        except PreconditionException as e:
          # Special retry case where we want to do an additional step, the read
          # of the read-modify-write cycle, to fetch the correct object
          # metadata before reattempting ACL changes.
          self._RefetchObjectMetadataAndApplyAclChanges(url, gsutil_api)

      self.logger.info('Updated ACL on %s', url)
    except BadRequestException as e:
      # Don't retry on bad requests, e.g. invalid email address.
      raise CommandException('Received bad request from server: %s' % str(e))
    except AccessDeniedException:
      self._RaiseForAccessDenied(url)
    except PreconditionException as e:
      # For objects, retry attempts should have already been handled.
      if url.IsObject():
        raise CommandException(str(e))
      # For buckets, raise PreconditionException and continue to next retry.
      raise e

  @Retry(PreconditionException, tries=3, timeout_secs=1)
  def _RefetchObjectMetadataAndApplyAclChanges(self, url, gsutil_api):
    """Reattempts object ACL changes after a PreconditionException."""
    gcs_object = gsutil_api.GetObjectMetadata(
        url.bucket_name,
        url.object_name,
        provider=url.scheme,
        fields=['acl', 'generation', 'metageneration'])
    current_acl = gcs_object.acl

    if self._ApplyAclChangesAndReturnChangeCount(url, current_acl) == 0:
      self.logger.info('No changes to %s', url)
      return

    object_metadata = apitools_messages.Object(acl=current_acl)
    preconditions = Preconditions(gen_match=gcs_object.generation,
                                  meta_gen_match=gcs_object.metageneration)
    gsutil_api.PatchObjectMetadata(url.bucket_name,
                                   url.object_name,
                                   object_metadata,
                                   preconditions=preconditions,
                                   provider=url.scheme,
                                   generation=gcs_object.generation,
                                   fields=['id'])

  def _ApplyAclChangesAndReturnChangeCount(self, storage_url, acl_message):
    modification_count = 0
    for change in self.changes:
      modification_count += change.Execute(storage_url, acl_message, 'acl',
                                           self.logger)
    return modification_count

  def RunCommand(self):
    """Command entry point for the acl command."""
    action_subcommand = self.args.pop(0)
    self.ParseSubOpts(check_args=True)

    # Commands with both suboptions and subcommands need to reparse for
    # suboptions, so we log again.
    metrics.LogCommandParams(sub_opts=self.sub_opts)
    self.def_acl = False
    if action_subcommand == 'get':
      metrics.LogCommandParams(subcommands=[action_subcommand])
      self.GetAndPrintAcl(self.args[0])
    elif action_subcommand == 'set':
      metrics.LogCommandParams(subcommands=[action_subcommand])
      self._SetAcl()
    elif action_subcommand in ('ch', 'change'):
      metrics.LogCommandParams(subcommands=[action_subcommand])
      self._ChAcl()
    else:
      raise CommandException(
          ('Invalid subcommand "%s" for the %s command.\n'
           'See "gsutil help acl".') % (action_subcommand, self.command_name))

    return 0
