# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""A git credential helper that provides Google git repository passwords.

Reads a session from stdin that looks a lot like:
  protocol=https
  host=code.google.com
And writes out a session to stdout that looks a lot like:
  username=me
  password=secret

Errors will be reported on stderr.

Note that spaces may be part of key names so, for example, "protocol" must not
be proceeded by leading spaces.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re
import subprocess
import sys
import textwrap

from googlecloudsdk.api_lib.auth import exceptions as auth_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import exceptions as creds_exceptions
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms

from oauth2client import client
import six


_KEYVAL_RE = re.compile(r'(.+)=(.*)')
_BLANK_LINE_RE = re.compile(r'^ *$')


@base.Hidden
class GitHelper(base.Command):
  """A git credential helper to provide access to Google git repositories."""

  GET = 'get'
  STORE = 'store'
  METHODS = [GET, STORE]

  GOOGLESOURCE = 'googlesource.com'

  @staticmethod
  def Args(parser):
    parser.add_argument('method',
                        help='The git credential helper method.')
    parser.add_argument('--ignore-unknown',
                        action='store_true',
                        help=('Produce no output and exit with 0 when given '
                              'an unknown method (e.g. store) or host.'))

  @c_exc.RaiseErrorInsteadOf(auth_exceptions.AuthenticationError, client.Error)
  def Run(self, args):
    """Run the helper command."""

    # Disable self signed jwt for this command.
    properties.VALUES.auth.service_account_use_self_signed_jwt.Set(False)

    if args.method not in GitHelper.METHODS:
      if args.ignore_unknown:
        return
      raise auth_exceptions.GitCredentialHelperError(
          'Unexpected method [{meth}]. One of [{methods}] expected.'
          .format(meth=args.method, methods=', '.join(GitHelper.METHODS)))

    info = self._ParseInput()
    credentialed_domains = [
        'source.developers.google.com',
        GitHelper.GOOGLESOURCE,  # Requires a different username value.
    ]
    credentialed_domains_suffix = [
        '.sourcemanager.dev',
        '.blueoryx.dev',
        '.'+GitHelper.GOOGLESOURCE,
    ]
    extra = properties.VALUES.core.credentialed_hosted_repo_domains.Get()
    if extra:
      credentialed_domains.extend(extra.split(','))
    host = info.get('host')

    def _ValidateHost(host):
      if host in credentialed_domains:
        return True
      for suffix in credentialed_domains_suffix:
        if host.endswith(suffix):
          return True
      return False

    if not _ValidateHost(host):
      if not args.ignore_unknown:
        raise auth_exceptions.GitCredentialHelperError(
            'Unknown host [{host}].'.format(host=host))
      return

    if args.method == GitHelper.GET:
      account = properties.VALUES.core.account.Get()
      try:
        cred = c_store.Load(account, use_google_auth=True)
        c_store.Refresh(cred)
      except creds_exceptions.Error as e:
        sys.stderr.write(textwrap.dedent("""\
            ERROR: {error}
            Run 'gcloud auth login' to log in.
            """.format(error=six.text_type(e))))
        return

      self._CheckNetrc()

      # For googlesource.com, any username beginning with "git-" is accepted
      # and the identity of the user is extracted from the token server-side.
      if (host == GitHelper.GOOGLESOURCE
          or host.endswith('.'+GitHelper.GOOGLESOURCE)):
        sent_account = 'git-account'
      else:
        sent_account = account

      if c_creds.IsOauth2ClientCredentials(cred):
        access_token = cred.access_token
      else:
        access_token = cred.token

      sys.stdout.write(
          textwrap.dedent("""\
          username={username}
          password={password}
          """).format(username=sent_account, password=access_token))
    elif args.method == GitHelper.STORE:
      # On OSX, there is an additional credential helper that gets called before
      # ours does.  When we return a token, it gets cached there.  Git continues
      # to get it from there first until it expires.  That command then fails,
      # and the token is deleted, but it does not retry the operation.  The next
      # command gets a new token from us and it starts working again, for an
      # hour.  This erases our credential from the other cache whenever 'store'
      # is called on us.  Because they are called first, the token will already
      # be stored there, and so we can successfully erase it to prevent caching.
      if (platforms.OperatingSystem.Current() ==
          platforms.OperatingSystem.MACOSX):
        log.debug('Clearing OSX credential cache.')
        try:
          input_string = 'protocol={protocol}\nhost={host}\n\n'.format(
              protocol=info.get('protocol'), host=info.get('host'))
          log.debug('Calling erase with input:\n%s', input_string)
          p = subprocess.Popen(['git-credential-osxkeychain', 'erase'],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
          (out, err) = p.communicate(input_string)
          if p.returncode:
            log.debug(
                'Failed to clear OSX keychain:\nstdout: {%s}\nstderr: {%s}',
                out, err)
        # pylint:disable=broad-except, This can fail and should only be done as
        # best effort.
        except Exception as e:
          log.debug('Failed to clear OSX keychain', exc_info=True)

  def _ParseInput(self):
    """Parse the fields from stdin.

    Returns:
      {str: str}, The parsed parameters given on stdin.
    """
    info = {}
    for line in sys.stdin:
      if _BLANK_LINE_RE.match(line):
        continue
      match = _KEYVAL_RE.match(line)
      if not match:
        raise auth_exceptions.GitCredentialHelperError(
            'Invalid input line format: [{format}].'
            .format(format=line.rstrip('\n')))
      key, val = match.groups()
      info[key] = val.strip()

    if 'protocol' not in info:
      raise auth_exceptions.GitCredentialHelperError(
          'Required key "protocol" missing.')

    if 'host' not in info:
      raise auth_exceptions.GitCredentialHelperError(
          'Required key "host" missing.')

    if info.get('protocol') != 'https':
      raise auth_exceptions.GitCredentialHelperError(
          'Invalid protocol [{p}].  "https" expected.'
          .format(p=info.get('protocol')))
    return info

  def _CheckNetrc(self):
    """Warn on stderr if ~/.netrc contains redundant credentials."""

    def Check(p):
      """Warn about other credential helpers that will be ignored."""
      if not os.path.exists(p):
        return
      try:
        data = files.ReadFileContents(p)
        if 'source.developers.google.com' in data:
          sys.stderr.write(textwrap.dedent("""\
You have credentials for your Google repository in [{path}]. This repository's
git credential helper is set correctly, so the credentials in [{path}] will not
be used, but you may want to remove them to avoid confusion.
""".format(path=p)))
      # pylint:disable=broad-except, If something went wrong, forget about it.
      except Exception:
        pass
    Check(files.ExpandHomeDir(os.path.join('~', '.netrc')))
    Check(files.ExpandHomeDir(os.path.join('~', '_netrc')))
