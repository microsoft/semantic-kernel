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

"""The implementation of generating a source context file."""

import json
import logging
import os
import re
import subprocess

from googlecloudsdk.third_party.appengine._internal import six_subset

_REMOTE_URL_PATTERN = r'remote\.(.*)\.url'

_CLOUD_REPO_PATTERN = (
    r'^https://'
    '(?P<hostname>[^/]*)/'
    '(?P<id_type>p|id)/'
    '(?P<project_or_repo_id>[^/?#]+)'
    '(/r/(?P<repo_name>[^/?#]+))?'
    '([/#?].*)?')

_GIT_PENDING_CHANGE_PATTERN = (
    '^# *('
    'Untracked files|'
    'Changes to be committed|'
    'Changes not staged for commit'
    '):')

CAPTURE_CATEGORY = 'capture'
REMOTE_REPO_CATEGORY = 'remote_repo'
CONTEXT_FILENAME = 'source-context.json'

# Keep this global name to protect against unexpected breakages.
EXT_CONTEXT_FILENAME = 'source-contexts.json'


class _ContextType(object):
  """Ordered enumeration of context types.

  The ordering is based on which context information will provide the best
  user experience. Higher numbers are considered better than lower numbers.
  Google repositories have the highest ranking because they do not require
  additional authorization to view.
  """

  # No details are known about the context.
  OTHER = 0

  # A git repository stored on an unfamiliar host.
  GIT_UNKNOWN = 1

  # An ssh link to a git repository on a known host (Github or BitBucket)
  GIT_KNOWN_HOST_SSH = 2

  # An http link to a git repository on a known host (Github or BitBucket)
  GIT_KNOWN_HOST = 3

  # A google cloud repo.
  CLOUD_REPO = 4

  # User-requested captured snapshot of source code.
  SOURCE_CAPTURE = 5


_PROTOCOL_PATTERN = re.compile(r'^(?P<protocol>\w+):')
_DOMAIN_PATTERN = re.compile(r'^\w+://([^/]*[.@])?(?P<domain>\w+\.\w+)[/:]')


def _GetGitContextTypeFromDomain(url):
  """Returns the context type for the input Git url."""

  if not url:
    return _ContextType.GIT_UNKNOWN
  if not _PROTOCOL_PATTERN.match(url):
    # Assume ssh protocol to simplify parsing.
    url = 'ssh://' + url
  domain_match = _DOMAIN_PATTERN.match(url)
  protocol = _PROTOCOL_PATTERN.match(url).group('protocol')
  if domain_match:
    domain = domain_match.group('domain')
    if domain == 'google.com':
      return _ContextType.CLOUD_REPO
    elif domain == 'github.com' or domain == 'bitbucket.org':
      if protocol == 'ssh':
        return _ContextType.GIT_KNOWN_HOST_SSH
      else:
        return _ContextType.GIT_KNOWN_HOST
  return _ContextType.GIT_UNKNOWN


def _GetContextType(context, labels):
  """Returns the _ContextType for the input extended source context.

  Args:
    context: A source context dict.
    labels: A dict containing the labels associated with the context.
  Returns:
    The context type.
  """
  if labels.get('category') == CAPTURE_CATEGORY:
    return _ContextType.SOURCE_CAPTURE
  git_context = context.get('git')
  if git_context:
    return _GetGitContextTypeFromDomain(git_context.get('url'))
  if 'cloudRepo' in context:
    return _ContextType.CLOUD_REPO
  return _ContextType.OTHER


def _IsRemoteBetter(new_name, old_name):
  """Indicates if a new remote is better than an old one, based on remote name.

  Names are ranked as follows: If either name is "origin", it is considered
  best, otherwise the name that comes last alphabetically is considered best.

  The alphabetical ordering is arbitrary, but it was chosen because it is
  stable. We prefer "origin" because it is the standard name for the origin
  of cloned repos.

  Args:
    new_name: The name to be evaluated.
    old_name: The name to compare against.
  Returns:
    True iff new_name should replace old_name.
  """
  if not new_name or old_name == 'origin':
    return False
  if not old_name or new_name == 'origin':
    return True
  return new_name > old_name


class GenerateSourceContextError(Exception):
  """An error occurred while trying to create the source context."""
  pass


def IsCaptureContext(context):
  return context.get('labels', {}).get('category', None) == CAPTURE_CATEGORY


def ExtendContextDict(context, category=REMOTE_REPO_CATEGORY, remote_name=None):
  """Converts a source context dict to an ExtendedSourceContext dict.

  Args:
    context: A SourceContext-compatible dict
    category:  string indicating the category of context (either
        CAPTURE_CATEGORY or REMOTE_REPO_CATEGORY)
    remote_name: The name of the remote in git.
  Returns:
    An ExtendedSourceContext-compatible dict.
  """
  labels = {'category': category}
  if remote_name:
    labels['remote_name'] = remote_name
  return {'context': context, 'labels': labels}


def HasPendingChanges(source_directory):
  """Checks if the git repo in a directory has any pending changes.

  Args:
    source_directory: The path to directory containing the source code.
  Returns:
    True if there are any uncommitted or untracked changes in the local repo
    for the given directory.
  """
  status = _CallGit(source_directory, 'status')
  return re.search(_GIT_PENDING_CHANGE_PATTERN, status,
                   flags=re.MULTILINE)


def CalculateExtendedSourceContexts(source_directory):
  """Generate extended source contexts for a directory.

  Scans the remotes and revision of the git repository at source_directory,
  returning one or more ExtendedSourceContext-compatible dictionaries describing
  the repositories.

  Currently, this function will return only the Google-hosted repository
  associated with the directory, if one exists.

  Args:
    source_directory: The path to directory containing the source code.
  Returns:
    One or more ExtendedSourceContext-compatible dictionaries describing
    the remote repository or repositories associated with the given directory.
  Raises:
    GenerateSourceContextError: if source context could not be generated.
  """

  # First get all of the remote URLs from the source directory.
  remote_urls = _GetGitRemoteUrls(source_directory)
  if not remote_urls:
    raise GenerateSourceContextError(
        'Could not list remote URLs from source directory: %s' %
        source_directory)

  # Then get the current revision.
  source_revision = _GetGitHeadRevision(source_directory)
  if not source_revision:
    raise GenerateSourceContextError(
        'Could not find HEAD revision from the source directory: %s' %
        source_directory)

  # Now find any remote URLs that match a Google-hosted source context.
  source_contexts = []
  for remote_name, remote_url in remote_urls.items():
    source_context = _ParseSourceContext(
        remote_name, remote_url, source_revision)
    # Only add this to the list if it parsed correctly, and hasn't been seen.
    # We'd like to do this in O(1) using a set, but Python doesn't hash dicts.
    # The number of remotes should be small anyway, so keep it simple.
    if source_context and source_context not in source_contexts:
      source_contexts.append(source_context)

  # If source context is still None or ambiguous, we have no context to go by.
  if not source_contexts:
    raise GenerateSourceContextError(
        'Could not find any repository in the remote URLs for source '
        'directory: %s' % source_directory)
  return source_contexts


def BestSourceContext(source_contexts):
  """Returns the "best" source context from a list of contexts.

  "Best" is a heuristic that attempts to define the most useful context in
  a Google Cloud Platform application. The most useful context is defined as:

  1. The capture context, if there is one. (I.e., a context with category
     'capture')
  2. The Cloud Repo context, if there is one.
  3. A repo context from another known provider (i.e. github or bitbucket), if
     there is no Cloud Repo context.
  4. The generic git repo context, if not of the above apply.

  If there are two Cloud Repo contexts and one of them is a "capture" context,
  that context is considered best.

  If two Git contexts come from the same provider, they will be evaluated based
  on remote name: "origin" is the best name, followed by the name that comes
  last alphabetically.

  If all of the above does not resolve a tie, the tied context that is
  earliest in the source_contexts list wins.

  Args:
    source_contexts: A list of extended source contexts.
  Returns:
    A single source context, or None if source_contexts is empty.
  Raises:
    KeyError if any extended source context is malformed.
  """
  source_context = None
  best_type = None
  best_remote_name = None
  for ext_ctx in source_contexts:
    candidate = ext_ctx['context']
    labels = ext_ctx.get('labels', {})
    context_type = _GetContextType(candidate, labels)
    # On the first pass, best_type is None, so both of the if statements below
    # will fail, causing the first value to be considered best until/unless
    # there is a better one.
    if best_type and context_type < best_type:
      continue
    remote_name = labels.get('remote_name')
    if context_type == best_type and not _IsRemoteBetter(remote_name,
                                                         best_remote_name):
      continue
    source_context = candidate
    best_remote_name = remote_name
    best_type = context_type
  return source_context


def GetSourceContextFilesCreator(output_dir, source_contexts, source_dir=None):
  """Returns a function to create source context files in the given directory.

  The returned creator function will produce one file: source-context.json

  Args:
    output_dir: (String) The directory to create the files (usually the yaml
        directory).
    source_contexts: ([ExtendedSourceContext-compatible json dict])
        A list of json-serializable dicts containing source contexts. If None
        or empty, output_dir will be inspected to determine if it has an
        associated Git repo, and appropriate source contexts will be created
        for that directory.
    source_dir: (String) The location of the source files, for inferring source
        contexts when source_contexts is empty or None. If not specified,
        output_dir will be used instead.
  Returns:
    callable() - A function that will create source-context.json file in the
    given directory. The creator function will return a cleanup function which
    can be used to delete any files the creator function creates.

    If there are no source_contexts associated with the directory, the creator
    function will not create any files (and the cleanup function it returns
    will also do nothing).
  """

  if not source_contexts:
    source_contexts = _GetSourceContexts(source_dir or output_dir)
  if not source_contexts:
    creators = []
  else:
    creators = [_GetContextFileCreator(output_dir, source_contexts)]
  def Generate():
    cleanups = [g() for g in creators]
    def Cleanup():
      for c in cleanups:
        c()
    return Cleanup
  return Generate


def CreateContextFiles(output_dir, source_contexts, overwrite=False,
                       source_dir=None):
  """Creates source context file in the given directory if possible.

  Currently, only source-context.json file will be produced.

  Args:
    output_dir: (String) The directory to create the files (usually the yaml
        directory).
    source_contexts:  ([ExtendedSourceContext-compatible json dict])
        A list of json-serializable dicts containing source contexts. If None
        or empty, source context will be inferred from source_dir.
    overwrite: (boolean) If true, silently replace any existing file.
    source_dir: (String) The location of the source files, for inferring
        source contexts when source_contexts is empty or None. If not
        specified, output_dir will be used instead.
  Returns:
    ([String]) A list containing the names of the files created. If there are
    no source contexts found, or if the contexts files could not be created, the
    result will be an empty.
  """
  if not source_contexts:
    source_contexts = _GetSourceContexts(source_dir or output_dir)
    if not source_contexts:
      return []
  created = []
  for context_filename, context_object in [
      (CONTEXT_FILENAME, BestSourceContext(source_contexts))]:
    context_filename = os.path.join(output_dir, context_filename)
    try:
      if overwrite or not os.path.exists(context_filename):
        with open(context_filename, 'w') as f:
          json.dump(context_object, f)
        created.append(context_filename)
    except IOError as e:
      logging.warn('Could not generate [%s]: %s', context_filename, e)

  return created


def _CallGit(cwd, *args):
  """Calls git with the given args, in the given working directory.

  Args:
    cwd: The working directory for the command.
    *args: Any arguments for the git command.
  Returns:
    The raw output of the command, or None if the command failed.
  """
  try:
    output = subprocess.check_output(['git'] + list(args), cwd=cwd)
    if six_subset.PY3:
      output = output.decode('utf-8')
    return output
  except (OSError, subprocess.CalledProcessError) as e:
    logging.debug('Could not call git with args %s: %s', args, e)
    return None


def _GetGitRemoteUrlConfigs(source_directory):
  """Calls git to output every configured remote URL.

  Args:
    source_directory: The path to directory containing the source code.
  Returns:
    The raw output of the command, or None if the command failed.
  """
  return _CallGit(
      source_directory, 'config', '--get-regexp', _REMOTE_URL_PATTERN)


def _GetGitRemoteUrls(source_directory):
  """Finds the list of git remotes for the given source directory.

  Args:
    source_directory: The path to directory containing the source code.
  Returns:
    A dictionary of remote name to remote URL, empty if no remotes are found.
  """
  remote_url_config_output = _GetGitRemoteUrlConfigs(source_directory)
  if not remote_url_config_output:
    return {}

  result = {}
  config_lines = remote_url_config_output.split('\n')
  for config_line in config_lines:
    if not config_line:
      continue  # Skip blank lines.

    # Each line looks like "remote.<name>.url <url>.
    config_line_parts = config_line.split(' ')
    if len(config_line_parts) != 2:
      logging.debug('Skipping unexpected config line, incorrect segments: %s',
                    config_line)
      continue

    # Extract the two parts, then find the name of the remote.
    remote_url_config_name = config_line_parts[0]
    remote_url = config_line_parts[1]
    remote_url_name_match = re.match(
        _REMOTE_URL_PATTERN, remote_url_config_name)
    if not remote_url_name_match:
      logging.debug('Skipping unexpected config line, could not match '
                    'remote: %s', config_line)
      continue
    remote_url_name = remote_url_name_match.group(1)

    result[remote_url_name] = remote_url
  return result


def _GetGitHeadRevision(source_directory):
  """Finds the current HEAD revision for the given source directory.

  Args:
    source_directory: The path to directory containing the source code.
  Returns:
    The HEAD revision of the current branch, or None if the command failed.
  """
  raw_output = _CallGit(source_directory, 'rev-parse', 'HEAD')
  return raw_output.strip() if raw_output else None


def _ParseSourceContext(remote_name, remote_url, source_revision):
  """Parses the URL into a source context blob, if the URL is a git or GCP repo.

  Args:
    remote_name: The name of the remote.
    remote_url: The remote URL to parse.
    source_revision: The current revision of the source directory.
  Returns:
    An ExtendedSourceContext suitable for JSON.
  """
  # Assume it's a Git URL unless proven otherwise.
  context = None

  # Now try to interpret the input as a Cloud Repo URL, and change context
  # accordingly if it looks like one. Assume any seemingly malformed URL is
  # a valid Git URL, since the inputs to this function always come from Git.
  #
  # A cloud repo URL can take three forms:
  # 1: https://<hostname>/id/<repo_id>
  # 2: https://<hostname>/p/<project_id>
  # 3: https://<hostname>/p/<project_id>/r/<repo_name>
  #
  # There are two repo ID types. The first type is the direct repo ID,
  # <repo_id>, which uniquely identifies a repository. The second is the pair
  # (<project_id>, <repo_name>) which also uniquely identifies a repository.
  #
  # Case 2 is equivalent to case 3 with <repo_name> defaulting to "default".
  match = re.match(_CLOUD_REPO_PATTERN, remote_url)
  if match:
    # It looks like a GCP repo URL. Extract the repo ID blob from it.
    id_type = match.group('id_type')
    if id_type == 'id':
      raw_repo_id = match.group('project_or_repo_id')
      # A GCP URL with an ID can't have a repo specification. If it has
      # one, it's either malformed or it's a Git URL from some other service.
      if not match.group('repo_name'):
        context = {
            'cloudRepo': {
                'repoId': {
                    'uid': raw_repo_id
                },
                'revisionId': source_revision}}
    elif id_type == 'p':
      # Treat it as a project name plus an optional repo name.
      project_id = match.group('project_or_repo_id')
      repo_name = match.group('repo_name') or 'default'
      context = {
          'cloudRepo': {
              'repoId': {
                  'projectRepoId': {
                      'projectId': project_id,
                      'repoName': repo_name}},
              'revisionId': source_revision}}
    # else it doesn't look like a GCP URL

  if not context:
    context = {'git': {'url': remote_url, 'revisionId': source_revision}}

  return ExtendContextDict(context, remote_name=remote_name)


def _GetJsonFileCreator(name, json_object):
  """Creates a creator function for an extended source context file.

  Args:
    name: (String) The name of the file to generate.
    json_object: Any object compatible with json.dump.
  Returns:
    (callable()) A creator function that will create the file and return a
    cleanup function that will delete the file.
  """
  if os.path.exists(name):
    logging.warn('%s already exists. It will not be updated.', name)
    return lambda: (lambda: None)
  def Cleanup():
    os.remove(name)
  def Generate():
    try:
      with open(name, 'w') as f:
        json.dump(json_object, f)
    except IOError as e:
      logging.warn('Could not generate [%s]: %s', name, e)
    return Cleanup
  return Generate


def _GetContextFileCreator(output_dir, contexts):
  """Creates a creator function for an old-style source context file.

  Args:
    output_dir: (String) The name of the directory in which to generate the
        file. The file will be named source-context.json.
    contexts: ([dict]) A list of ExtendedSourceContext-compatible dicts for json
        serialization.
  Returns:
    A creator function that will create the file.
  """
  name = os.path.join(output_dir, CONTEXT_FILENAME)
  return _GetJsonFileCreator(name, BestSourceContext(contexts))


def _GetSourceContexts(source_dir):
  """Gets the source contexts associated with a directory.

  This function is mostly a wrapper around CalculateExtendedSourceContexts
  which logs a message if the context could not be determined.
  Args:
    source_dir: (String) The directory to inspect.
  Returns:
    [ExtendedSourceContext-compatible json dict] A list of 0 or more source
    contexts.
  """
  try:
    source_contexts = (CalculateExtendedSourceContexts(source_dir))
  except GenerateSourceContextError:
    # No valid source contexts.
    source_contexts = []
  if not source_contexts:
    logging.info(
        'Could not find any remote repositories associated with [%s]. '
        'Cloud diagnostic tools may not be able to display the correct '
        'source code for this deployment.', source_dir)
  return source_contexts
