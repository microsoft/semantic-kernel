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

"""Classes for working with component snapshots.

A snapshot is basically a state of the world at a given point in time.  It
describes the components that exist and how they depend on each other.  This
module lets you do operations on snapshots like getting dependency closures,
as well as diff'ing snapshots.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import json
import os
import re

from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.updater import installers
from googlecloudsdk.core.updater import schemas
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms

import requests
import six


class Error(exceptions.Error):
  """Base exception for the snapshots module."""
  pass


class URLFetchError(Error):
  """Error for problems fetching via HTTP."""

  def __init__(self, code=None, malformed=False, extra_repo=None):
    msg = 'Failed to fetch component listing from server.'
    if code:
      msg += ' Received response code [{0}].'.format(code)
    elif malformed:
      msg += ' The repository URL was malformed.'
    else:
      msg += ' Check your network settings and try again.'

    if extra_repo:
      msg += ('\nPlease ensure that the additional component repository [{0}] '
              'is correct and still valid.  To remove it, run:\n'
              '  $ gcloud components repositories remove {0}'
              .format(extra_repo))
    super(URLFetchError, self).__init__(msg)


class MalformedSnapshotError(Error):
  """Error with the contents of the snapshot."""

  def __init__(self):
    super(MalformedSnapshotError, self).__init__(
        'Failed to process component listing from server.')


class IncompatibleSchemaVersionError(Error):
  """Error for when we are unable to parse the new version of the snapshot."""

  def __init__(self, schema_version):
    super(IncompatibleSchemaVersionError, self).__init__(
        'The latest version snapshot is incompatible with this installation.')
    self.schema_version = schema_version


class ComponentSnapshot(object):
  """Contains a state-of-the-world for existing components.

  A snapshot can be loaded from different sources.  It can be the latest that
  exists on the server or it can be constructed from local install state.
  Either way, it describes the components that are available, how they depend
  on each other, and other information about them like descriptions and version
  information.

  Attributes:
    revision: int, The global revision number for this snapshot.  If it was
      created from an InstallState, this will be -1 to indicate that it is
      potentially a composition of more than one snapshot.
    sdk_definition: schemas.SDKDefinition, The full definition for this
      component snapshot.
    url: str, The full URL of the file from which this snapshot was loaded.
      This could be a web address like http://internet.com/components.json or
      a local file path as a URL like file:///some/local/path/components.json.
      It may also be None if the data did not come from a file.
    components = dict from component id string to schemas.Component, All the
      Components in this snapshot.
  """
  ABSOLUTE_RE = re.compile(r'^\w+://')

  @staticmethod
  def _GetAbsoluteURL(url, value):
    """Convert the potentially relative value into an absolute URL.

    Args:
      url: str, The URL of the component snapshot this value was found in.
      value: str, The value of the field to make absolute.  If it is already an
        absolute URL, it is returned as-is.  If it is relative, it's path
        is assumed to be relative to the component snapshot URL.

    Returns:
      str, The absolute URL.
    """
    if ComponentSnapshot.ABSOLUTE_RE.search(value):
      return value
    # This is a relative path, look relative to the snapshot file.
    return os.path.dirname(url) + '/' + value

  @staticmethod
  def FromFile(snapshot_file):
    """Loads a snapshot from a local file.

    Args:
      snapshot_file: str, The path of the file to load.

    Returns:
      A ComponentSnapshot object
    """
    with files.FileReader(snapshot_file) as f:
      data = json.load(f)
    # Windows paths will start with a drive letter so they need an extra '/' up
    # front.  Also, URLs must only have forward slashes to work correctly.
    url = ('file://' +
           ('/' if not snapshot_file.startswith('/') else '') +
           snapshot_file.replace('\\', '/'))
    return ComponentSnapshot._FromDictionary((data, url))

  @staticmethod
  def FromURLs(*urls, **kwargs):
    """Loads a snapshot from a series of URLs.

    Args:
      *urls: str, The URLs to the files to load.
      **kwargs: command_path: the command path to include in the User-Agent
        header if the URL is HTTP

    Returns:
      A ComponentSnapshot object.

    Raises:
      URLFetchError: If the URL cannot be fetched.
      TypeError: If an unexpected keyword argument is given.
    """
    # Get this here so that it will break if the name of FromURLs changes
    current_function_name = ComponentSnapshot.FromURLs.__name__
    # We can't make a keyword argument for this because of *args, so we want to
    # emulate that behavior
    unexpected_args = set(kwargs) - set(['command_path'])
    if unexpected_args:
      raise TypeError("{0} got an unexpected keyword argument \'{1}\'".format(
          current_function_name, unexpected_args.pop()))
    command_path = kwargs.get('command_path', 'unknown')

    first = urls[0]
    data = [
        (ComponentSnapshot._DictFromURL(
            url, command_path, is_extra_repo=(url != first)),
         url)
        for url in urls]
    return ComponentSnapshot._FromDictionary(*data)

  @staticmethod
  def _DictFromURL(url, command_path, is_extra_repo=False):
    """Loads a json dictionary from a URL.

    Args:
      url: str, The URL to the file to load.
      command_path: the command path to include in the User-Agent header if the
        URL is HTTP
      is_extra_repo: bool, True if this is not the primary repository.

    Returns:
      A ComponentSnapshot object.

    Raises:
      URLFetchError: If the URL cannot be fetched.
    """
    extra_repo = url if is_extra_repo else None
    try:
      response = installers.MakeRequest(url, command_path)
    except requests.exceptions.HTTPError:
      log.debug('Could not fetch [{url}]'.format(url=url), exc_info=True)
      response = None

    if response is None:
      raise URLFetchError(extra_repo=extra_repo)
    code = response.status_code
    if code != requests.codes.ok:
      raise URLFetchError(code=code, extra_repo=extra_repo)

    try:
      # response.content is always in bytes
      data = json.loads(response.content.decode('utf-8'))
      return data
    except ValueError as e:
      log.debug('Failed to parse snapshot [{}]: {}'.format(url, e))
      raise MalformedSnapshotError()

  @staticmethod
  def FromInstallState(install_state):
    """Loads a snapshot from the local installation state.

    This creates a snapshot that may not have actually existed at any point in
    time.  It does, however, exactly reflect the current state of your local
    SDK.

    Args:
      install_state: install_state.InstallState, The InstallState object to load
        from.

    Returns:
      A ComponentSnapshot object.
    """
    installed = install_state.InstalledComponents()
    components = [manifest.ComponentDefinition()
                  for manifest in installed.values()]
    sdk_definition = schemas.SDKDefinition(
        revision=-1, schema_version=None, release_notes_url=None, version=None,
        gcloud_rel_path=None, post_processing_command=None,
        components=components, notifications={})
    return ComponentSnapshot(sdk_definition)

  @staticmethod
  def _FromDictionary(*data):
    """Loads a snapshot from a dictionary representing the raw JSON data.

    Args:
      *data: ({}, str), A tuple of parsed JSON data and the URL it came from.

    Returns:
      A ComponentSnapshot object.

    Raises:
      IncompatibleSchemaVersionError: If the latest snapshot cannot be parsed
        by this code.
    """
    merged = None
    for (json_dictionary, url) in data:
      # Parse just the schema version first, to see if we should continue.
      schema_version = schemas.SDKDefinition.SchemaVersion(json_dictionary)
      # Convert relative data sources into absolute URLs if a URL is given.
      if url and schema_version.url:
        schema_version.url = ComponentSnapshot._GetAbsoluteURL(
            url, schema_version.url)
      if (schema_version.version >
          config.INSTALLATION_CONFIG.snapshot_schema_version):
        raise IncompatibleSchemaVersionError(schema_version)

      sdk_def = schemas.SDKDefinition.FromDictionary(json_dictionary)

      # Convert relative data sources into absolute URLs if a URL is given.
      if url:
        if sdk_def.schema_version.url:
          sdk_def.schema_version.url = ComponentSnapshot._GetAbsoluteURL(
              url, sdk_def.schema_version.url)
        if sdk_def.release_notes_url:
          sdk_def.release_notes_url = ComponentSnapshot._GetAbsoluteURL(
              url, sdk_def.release_notes_url)
        for c in sdk_def.components:
          if not c.data or not c.data.source:
            continue
          c.data.source = ComponentSnapshot._GetAbsoluteURL(url, c.data.source)

      if not merged:
        merged = sdk_def
      else:
        merged.Merge(sdk_def)
    return ComponentSnapshot(merged)

  def __init__(self, sdk_definition):
    self.sdk_definition = sdk_definition
    self.revision = sdk_definition.revision
    self.version = sdk_definition.version
    self.components = dict((c.id, c) for c in sdk_definition.components)
    deps = dict((c.id, set(c.dependencies)) for c in sdk_definition.components)
    self.__dependencies = {}
    # Prune out unknown dependencies
    for comp, dep_ids in six.iteritems(deps):
      self.__dependencies[comp] = set(dep_id for dep_id in dep_ids
                                      if dep_id in deps)

    self.__consumers = dict((id, set()) for id in self.__dependencies)
    for component_id, dep_ids in six.iteritems(self.__dependencies):
      for dep_id in dep_ids:
        self.__consumers[dep_id].add(component_id)

  def _ClosureFor(self, ids, adjacencies, component_filter):
    """Calculates a connected closure for the components with the given ids.

    Performs a breadth first search starting with the given component ids, and
    returns the set of components reachable via the given adjacency map.

    Args:
      ids: [str], The component ids to get the closure for.
      adjacencies: {str: set}, Map of component ids to the set of their
        adjacent component ids.
      component_filter: schemas.Component -> bool, A function applied to
        components that determines whether or not to include them in the
        closure.

    Returns:
      set of str, The set of component ids in the closure.
    """
    closure = set()
    to_process = collections.deque(ids)
    while to_process:
      current = to_process.popleft()
      if current not in self.components or current in closure:
        continue
      if not component_filter(self.components[current]):
        continue
      closure.add(current)
      to_process.extend(adjacencies[current])
    return closure

  def ComponentFromId(self, component_id):
    """Gets the schemas.Component from this snapshot with the given id.

    Args:
      component_id: str, The id component to get.

    Returns:
      The corresponding schemas.Component object.
    """
    return self.components.get(component_id)

  def ComponentsFromIds(self, component_ids):
    """Gets the schemas.Component objects for each of the given ids.

    Args:
      component_ids: iterable of str, The ids of the  components to get

    Returns:
      The corresponding schemas.Component objects.
    """
    return set(self.components.get(component_id)
               for component_id in component_ids)

  def AllComponentIdsMatching(self, platform_filter):
    """Gets all components in the snapshot that match the given platform.

    Args:
      platform_filter: platforms.Platform, A platform the components must match.

    Returns:
      set(str), The matching component ids.
    """
    return set(c_id for c_id, component in six.iteritems(self.components)
               if component.platform.Matches(platform_filter))

  def DependencyClosureForComponents(self, component_ids, platform_filter=None):
    """Gets all the components that are depended on by any of the given ids.

    Args:
      component_ids: list of str, The ids of the components to get the
        dependencies of.
      platform_filter: platforms.Platform, A platform that components must
        match to be pulled into the dependency closure.

    Returns:
      set of str, All component ids that are in the dependency closure,
      including the given components.
    """
    component_filter = lambda c: c.platform.Matches(platform_filter)
    return self._ClosureFor(
        component_ids, self.__dependencies, component_filter)

  def ConsumerClosureForComponents(self, component_ids, platform_filter=None):
    """Gets all the components that depend on any of the given ids.

    Args:
      component_ids: list of str, The ids of the components to get the consumers
        of.
      platform_filter: platforms.Platform, A platform that components must
        match to be pulled into the consumer closure.

    Returns:
      set of str, All component ids that are in the consumer closure, including
      the given components.
    """
    component_filter = lambda c: c.platform.Matches(platform_filter)
    return self._ClosureFor(component_ids, self.__consumers, component_filter)

  def ConnectedComponents(self, component_ids, platform_filter=None):
    """Gets all the components that are connected to any of the given ids.

    Connected means in the connected graph of dependencies.  This is basically
    the union of the dependency and consumer closure for the given ids.

    Args:
      component_ids: list of str, The ids of the components to get the
        connected graph of.
      platform_filter: platforms.Platform, A platform that components must
        match to be pulled into the connected graph.

    Returns:
      set of str, All component ids that are connected to the given ids,
      including the given components.
    """
    adjacencies = {
        c_id: self.__dependencies[c_id] | self.__consumers[c_id]
        for c_id in self.components}
    component_filter = lambda c: c.platform.Matches(platform_filter)
    return self._ClosureFor(component_ids, adjacencies, component_filter)

  def StronglyConnectedComponents(self, component_id):
    """Gets the components strongly connected to the given component id.

    In other words, this functions returns the strongly connected "component" of
    the dependency graph for the given component id. In this context the
    strongly connected "component" is the set of ids whose components are both
    dependencies and consumers of the given component. In practice this can be
    used to determine the platform-specific subcomponent ID's for a given
    component ID, since they will always be mutually dependent.

    Args:
      component_id: str, The id of the component for which to get the strongly
        connected components.

    Returns:
      set of str, The ids of the components that are strongly connected to the
        component with the given id.
    """
    # Unlike the other functions above, we don't filter by platform since we
    # want all platform-specific subcomponents to match.
    component_filter = lambda c: True
    dependency_closure = self._ClosureFor(
        [component_id], self.__dependencies, component_filter)
    consumer_closure = self._ClosureFor(
        [component_id], self.__consumers, component_filter)

    return dependency_closure & consumer_closure

  def GetEffectiveComponentSize(self, component_id, platform_filter=None):
    """Computes the effective size of the given component.

    If the component does not exist or does not exist on this platform, the size
    is 0.

    If it has data, just use the reported size of its data.

    If there is no data, report the total size of all its direct hidden
    dependencies (that are valid on this platform).  We don't include visible
    dependencies because they will show up in the list with their own size.

    This is a best effort estimation.  It is not easily possible to accurately
    report size in all situations because complex dependency graphs (between
    hidden and visible components, as well as circular dependencies) makes it
    infeasible to correctly show size when only displaying visible components.
    The goal is mainly to not show some components as having no size at all
    when they are wrappers around platform specific components.

    Args:
      component_id: str, The component to get the size for.
      platform_filter: platforms.Platform, A platform that components must
        match in order to be considered for any operations.

    Returns:
      int, The effective size of the component.
    """
    size = 0
    component = self.ComponentFromId(component_id)

    if component and component.platform.Matches(platform_filter):
      # This is a valid component for this platform.
      if component.data:
        # This component reports its data, just return that size.
        return component.data.size

      # Get the direct dependencies that are valid on this platform, are hidden,
      # and that report data.
      deps = [self.ComponentFromId(d)
              for d in self.__dependencies[component_id]]
      deps = [d for d in deps
              if d.platform.Matches(platform_filter) and
              d.is_hidden and d.data]
      for d in deps:
        # If we get here, the component has a data section. The size should
        # always be populated, but sometimes in the local state the size is
        # deleted from the cached snapshot. The size data is not critical, so
        # just substitute in 0 if we can't find the size so things don't crash.
        size += d.data.size or 0
    return size

  def CreateDiff(self, latest_snapshot, platform_filter=None):
    """Creates a ComponentSnapshotDiff based on this snapshot and the given one.

    Args:
      latest_snapshot: ComponentSnapshot, The latest state of the world that we
        want to compare to.
      platform_filter: platforms.Platform, A platform that components must
        match in order to be considered for any operations.

    Returns:
      A ComponentSnapshotDiff object.
    """
    return ComponentSnapshotDiff(self, latest_snapshot,
                                 platform_filter=platform_filter)

  def CreateComponentInfos(self, platform_filter=None):
    all_components = self.AllComponentIdsMatching(platform_filter)
    infos = [ComponentInfo(component_id, self, platform_filter=platform_filter)
             for component_id in all_components]
    return infos

  def WriteToFile(self, path, component_id=None):
    """Writes this snapshot back out to a JSON file.

    Args:
      path: str, The path of the file to write to.
      component_id: Limit snapshot to this component.
          If not specified all components are written out.

    Raises:
      ValueError: for non existent component_id.
    """
    sdk_def_dict = self.sdk_definition.ToDictionary()
    if component_id:
      component_dict = [c for c in sdk_def_dict['components']
                        if c['id'] == component_id]
      if not component_dict:
        raise ValueError(
            'Component {} is not in this snapshot {}'
            .format(component_id,
                    ','.join([c['id'] for c in sdk_def_dict['components']])))
      if 'data' in component_dict[0]:
        # Remove non-essential/random parts from component data.
        for f in list(component_dict[0]['data'].keys()):
          if f not in ('contents_checksum', 'type', 'source'):
            del component_dict[0]['data'][f]
        # Source field is required for global snapshot, but is not for
        # component snapshot.
        component_dict[0]['data']['source'] = ''
      sdk_def_dict['components'] = component_dict
      # Remove unnecessary artifacts from snapshot.
      for key in list(sdk_def_dict.keys()):
        if key not in ('components', 'schema_version', 'revision', 'version'):
          del sdk_def_dict[key]
    files.WriteFileContents(
        path, json.dumps(sdk_def_dict, indent=2, sort_keys=True,
                         separators=(',', ': ')))

  def CheckMissingPlatformExecutable(self, component_ids, platform_filter=None):
    """Gets all the components that miss required platform-specific executables.

    Args:
      component_ids: list of str, The ids of the components to check for.
      platform_filter: platforms.Platform, A platform that components must
        match to be pulled into the dependency closure.

    Returns:
      set of str, All component ids that miss required platform-specific
        executables.
    """

    invalid_seeds = set()
    for c_id in component_ids:
      if (c_id in self.components and
          not self.components[c_id].platform.architectures and
          not self.components[c_id].platform.operating_systems and
          self.components[c_id].platform_required):
        deps = self.DependencyClosureForComponents(
            [c_id], platform_filter=platform_filter)
        qualified = [d for d in deps if str(d).startswith('{}-'.format(c_id))]
        if not qualified:
          invalid_seeds.add(c_id)
    return invalid_seeds


class ComponentSnapshotDiff(object):
  """Provides the ability to compare two ComponentSnapshots.

  This class is used to see how the current state-of-the-word compares to what
  we have installed.  It can be for informational purposes (to list available
  updates) but also to determine specifically what components need to be
  uninstalled / installed for a specific update command.

  Attributes:
    current: ComponentSnapshot, The current snapshot state.
    latest: CompnentSnapshot, The new snapshot that is being compared.
  """

  DARWIN_X86_64 = platforms.Platform(platforms.OperatingSystem.MACOSX,
                                     platforms.Architecture.x86_64)

  ROSETTA2_FILES = [
      '/Library/Apple/System/Library/LaunchDaemons/com.apple.oahd.plist',
      '/Library/Apple/usr/share/rosetta/rosetta',
      '/Library/Apple/System/Library/Receipts/com.apple.pkg.RosettaUpdateAuto.bom',
      '/Library/Apple/System/Library/Receipts/com.apple.pkg.RosettaUpdateAuto.plist'
  ]

  def __init__(self, current, latest, platform_filter=None):
    """Creates a new diff between two ComponentSnapshots.

    Args:
      current: The current ComponentSnapshot
      latest: The ComponentSnapshot representing a new state we can move to
      platform_filter: platforms.Platform, A platform that components must
        match in order to be considered for any operations.
    """
    self.current = current
    self.latest = latest
    self.__platform_filter = platform_filter
    self.__enable_fallback = self._EnableFallback()

    self.__all_components = (current.AllComponentIdsMatching(platform_filter) |
                             latest.AllComponentIdsMatching(platform_filter))

    if self.__enable_fallback:
      # Fall back to darwin_x86 version when darwin_arm version is unavailable.
      self.__all_darwin_x86_64_components = (
          current.AllComponentIdsMatching(self.DARWIN_X86_64) |
          latest.AllComponentIdsMatching(self.DARWIN_X86_64))
      self.__darwin_x86_64_components = (self.__all_darwin_x86_64_components -
                                         self.__all_components)
      self.__native_all_components = set(self.__all_components)
      self.__all_components |= self.__darwin_x86_64_components

      self.__diffs = [
          ComponentDiff(component_id, current, latest,
                        platform_filter=platform_filter)
          for component_id in self.__native_all_components]
      self.__diffs.extend([
          ComponentDiff(component_id, current, latest,
                        platform_filter=self.DARWIN_X86_64)
          for component_id in self.__darwin_x86_64_components])
    else:
      self.__diffs = [
          ComponentDiff(component_id, current, latest,
                        platform_filter=platform_filter)
          for component_id in self.__all_components]

    self.__removed_components = set(diff.id for diff in self.__diffs
                                    if diff.state is ComponentState.REMOVED)
    self.__new_components = set(diff.id for diff in self.__diffs
                                if diff.state is ComponentState.NEW)
    self.__updated_components = set(diff.id for diff in self.__diffs
                                    if diff.state is
                                    ComponentState.UPDATE_AVAILABLE)

  def _EnableFallback(self):
    # pylint: disable=line-too-long
    return (self.__platform_filter and
            self.__platform_filter.operating_system == platforms.OperatingSystem.MACOSX and
            self.__platform_filter.architecture == platforms.Architecture.arm)

  def InvalidUpdateSeeds(self, component_ids):
    """Sees if any of the given components don't exist locally or remotely.

    Args:
      component_ids: list of str, The components that the user wants to update.

    Returns:
      set of str, The component ids that do not exist anywhere.
    """
    invalid_seeds = set(component_ids) - self.__all_components
    missing_platform = self.latest.CheckMissingPlatformExecutable(
        component_ids, self.__platform_filter)
    if self._EnableFallback():
      missing_platform_x86_64 = self.latest.CheckMissingPlatformExecutable(
          component_ids, self.DARWIN_X86_64)
      missing_platform &= missing_platform_x86_64
      native_invalid_ids = set(component_ids) - self.__native_all_components
      arm_x86_ids = native_invalid_ids & self.__darwin_x86_64_components
      if arm_x86_ids:
        rosetta2_installed = self._CheckRosetta2Exists()
        if not rosetta2_installed:
          log.warning('The ARM versions of the components [{}] are not '
                      'available yet. To download and execute the x86_64 '
                      'version of the components, please install Rosetta 2 '
                      'first by running the command: '
                      'softwareupdate --install-rosetta.'
                      .format(', '.join(arm_x86_ids)))
          invalid_seeds |= arm_x86_ids
    if missing_platform:
      log.warning(
          'The platform specific binary does not exist for components [{}].'
          .format(', '.join(missing_platform)))
    return invalid_seeds | missing_platform

  def _CheckRosetta2Exists(self):
    for path in self.ROSETTA2_FILES:
      if os.path.isfile(path):
        return True
    return False

  def AllDiffs(self):
    """Gets all ComponentDiffs for this snapshot comparison.

    Returns:
      The list of all ComponentDiffs between the snapshots.
    """
    return self._FilterDiffs(None)

  def AvailableUpdates(self):
    """Gets ComponentDiffs for components where there is an update available.

    Returns:
      The list of ComponentDiffs.
    """
    return self._FilterDiffs(ComponentState.UPDATE_AVAILABLE)

  def AvailableToInstall(self):
    """Gets ComponentDiffs for new components that can be installed.

    Returns:
      The list of ComponentDiffs.
    """
    return self._FilterDiffs(ComponentState.NEW)

  def Removed(self):
    """Gets ComponentDiffs for components that no longer exist.

    Returns:
      The list of ComponentDiffs.
    """
    return self._FilterDiffs(ComponentState.REMOVED)

  def UpToDate(self):
    """Gets ComponentDiffs for installed components that are up to date.

    Returns:
      The list of ComponentDiffs.
    """
    return self._FilterDiffs(ComponentState.UP_TO_DATE)

  def _FilterDiffs(self, state):
    if not state:
      filtered = self.__diffs
    else:
      filtered = [diff for diff in self.__diffs if diff.state is state]
    return sorted(filtered, key=lambda d: d.name)

  def FilterDuplicatesArm(self, component_ids):
    """Filter out x86_64 components that are available in arm versions."""
    return set(i for i in component_ids
               if not ('darwin-x86_64' in i and
                       i.replace('x86_64', 'arm') in component_ids))

  def ToRemove(self, update_seed):
    """Calculate the components that need to be uninstalled.

    Based on this given set of components, determine what we need to remove.
    When an update is done, we update all components connected to the initial
    set.  Based on this, we need to remove things that have been updated, or
    that no longer exist.  This method works with ToInstall().  For a given
    update set the update process should remove anything from ToRemove()
    followed by installing everything in ToInstall().  It is possible (and
    likely) that a component will be in both of these sets (when a new version
    is available).

    Args:
      update_seed: list of str, The component ids that we want to update.

    Returns:
      set of str, The component ids that should be removed.
    """
    # Get the full set of everything that needs to be updated together that we
    # currently have installed
    if self._EnableFallback():
      connected = self.current.ConnectedComponents(
          update_seed, platform_filter=self.__platform_filter)
      connected |= self.latest.ConnectedComponents(
          connected | set(update_seed), platform_filter=self.__platform_filter)
      connected_darwin_x86_64 = self.current.ConnectedComponents(
          update_seed, platform_filter=self.DARWIN_X86_64)
      connected_darwin_x86_64 |= self.latest.ConnectedComponents(
          connected_darwin_x86_64 | set(update_seed),
          platform_filter=self.DARWIN_X86_64)
      connected |= connected_darwin_x86_64
      x86_removal_candidates = connected - self.FilterDuplicatesArm(connected)
      installed_components = set(self.current.components.keys())
      x86_removal_seed = x86_removal_candidates & installed_components
      if x86_removal_seed:
        log.warning('The ARM versions of the following components are '
                    'available, replacing installed x86_64 versions: [{}].'
                    .format(', '.join(x86_removal_seed)))
      removal_candidates = connected & set(self.current.components.keys())
      # We need to remove anything that no longer exists or that has been
      # updated, and existing x86_64 versions that could be updated to native
      # arm versions
      return (self.__removed_components |
              self.__updated_components |
              x86_removal_seed) & removal_candidates
    else:
      connected = self.current.ConnectedComponents(
          update_seed, platform_filter=self.__platform_filter)
      connected |= self.latest.ConnectedComponents(
          connected | set(update_seed), platform_filter=self.__platform_filter)
      removal_candidates = connected & set(self.current.components.keys())
      # We need to remove anything that no longer exists or that has been
      # updated
      return (self.__removed_components |
              self.__updated_components) & removal_candidates

  def ToInstall(self, update_seed):
    """Calculate the components that need to be installed.

    Based on this given set of components, determine what we need to install.
    When an update is done, we update all components connected to the initial
    set.  Based on this, we need to install things that have been updated or
    that are new.  This method works with ToRemove().  For a given update set
    the update process should remove anything from ToRemove() followed by
    installing everything in ToInstall().  It is possible (and likely) that a
    component will be in both of these sets (when a new version is available).

    Args:
      update_seed: list of str, The component ids that we want to update.

    Returns:
      set of str, The component ids that should be removed.
    """
    installed_components = list(self.current.components.keys())
    missing_platform = self.latest.CheckMissingPlatformExecutable(
        update_seed, self.__platform_filter)

    if self._EnableFallback():
      missing_platform_darwin_x86_64 = self.latest.CheckMissingPlatformExecutable(
          update_seed, self.DARWIN_X86_64)
      native_valid_seed = self.__native_all_components - missing_platform
      native_seed = set(update_seed) & native_valid_seed
      darwin_x86_64 = set(update_seed) - native_seed
      darwin_x86_64 -= missing_platform_darwin_x86_64
      valid_seed = native_seed | darwin_x86_64

      platform_seeds = [c_id for c_id in darwin_x86_64
                        if 'darwin' not in c_id]

      if platform_seeds:
        log.warning('The ARM versions of the following components are not '
                    'available yet, using x86_64 versions instead: [{}].'
                    .format(', '.join(platform_seeds)))

      local_connected = self.current.ConnectedComponents(
          valid_seed, platform_filter=self.__platform_filter)
      all_required = self.latest.DependencyClosureForComponents(
          local_connected | set(valid_seed),
          platform_filter=self.__platform_filter)
      local_connected_darwin_x86_64 = self.current.ConnectedComponents(
          valid_seed, platform_filter=self.DARWIN_X86_64)
      all_required |= self.latest.DependencyClosureForComponents(
          local_connected_darwin_x86_64 | valid_seed,
          platform_filter=self.DARWIN_X86_64)

      remote_connected = self.latest.ConnectedComponents(
          local_connected | valid_seed,
          platform_filter=self.__platform_filter)
      remote_connected |= self.latest.ConnectedComponents(
          local_connected_darwin_x86_64 | valid_seed,
          platform_filter=self.__platform_filter)
      all_required |= remote_connected & set(installed_components)
      all_required = self.FilterDuplicatesArm(all_required)

      dep_missing_platform = self.latest.CheckMissingPlatformExecutable(
          all_required, self.DARWIN_X86_64)
      if dep_missing_platform:
        log.warning(
            'The platform specific binary does not exist for components [{}].'
            .format(', '.join(dep_missing_platform)))
        all_required -= dep_missing_platform
    else:
      local_connected = self.current.ConnectedComponents(
          update_seed, platform_filter=self.__platform_filter)
      all_required = self.latest.DependencyClosureForComponents(
          local_connected | set(update_seed),
          platform_filter=self.__platform_filter)

      # Add in anything in the connected graph that we already have installed.
      # Even though the update seed might not depend on it, if it was already
      # installed, it might have been removed in ToRemove() if an update was
      # available so we should put it back.
      remote_connected = self.latest.ConnectedComponents(
          local_connected | set(update_seed),
          platform_filter=self.__platform_filter)
      all_required |= remote_connected & set(installed_components)

      dep_missing_platform = self.latest.CheckMissingPlatformExecutable(
          all_required, self.__platform_filter)
      if dep_missing_platform:
        log.warning(
            'The platform specific binary does not exist for components [{}].'
            .format(', '.join(dep_missing_platform)))
        all_required -= dep_missing_platform

    different = self.__new_components | self.__updated_components

    # all new or updated components, or if it has not been changed but we
    # don't have it
    return set(c for c in all_required
               if c in different or c not in installed_components)

  def DetailsForCurrent(self, component_ids):
    """Gets the schema.Component objects for all ids from the current snapshot.

    Args:
      component_ids: list of str, The component ids to get.

    Returns:
      A list of schema.Component objects sorted by component display name.
    """
    return sorted(self.current.ComponentsFromIds(component_ids),
                  key=lambda c: c.details.display_name)

  def DetailsForLatest(self, component_ids):
    """Gets the schema.Component objects for all ids from the latest snapshot.

    Args:
      component_ids: list of str, The component ids to get.

    Returns:
      A list of schema.Component objects sorted by component display name.
    """
    return sorted(self.latest.ComponentsFromIds(component_ids),
                  key=lambda c: c.details.display_name)


class ComponentInfo(object):
  """Encapsulates information to be displayed for a component.

  Attributes:
    id: str, The component id.
    platform: str, The operating system and architecture of the platform.
    name: str, The display name of the component.
    current_version_string: str, The version of the component.
    is_hidden: bool, If the component is hidden.
    is_configuration: bool, True if this should be displayed in the packages
      section of the component manager.
    platform_required: bool, True if a platform-specific executable is
      required.
  """

  def __init__(self, component_id, snapshot, platform_filter=None):
    """Create a new component info container.

    Args:
      component_id: str, The id of this component.
      snapshot: ComponentSnapshot, The snapshot from which to create info from.
      platform_filter: platforms.Platform, A platform that components must
        match in order to be considered for any operations.
    """
    self._id = component_id
    self._snapshot = snapshot
    self._component = snapshot.ComponentFromId(component_id)
    self._platform_filter = platform_filter

  @property
  def id(self):
    return self._id

  @property
  def platform(self):
    return self._platform_filter

  @property
  def current_version_string(self):
    return self._component.version.version_string

  @property
  def name(self):
    return self._component.details.display_name

  @property
  def is_hidden(self):
    return self._component.is_hidden

  @property
  def is_configuration(self):
    return self._component.is_configuration

  @property
  def platform_required(self):
    return self._component.platform_required

  @property
  def size(self):
    return self._snapshot.GetEffectiveComponentSize(
        self._id, platform_filter=self._platform_filter)

  def __str__(self):
    return (
        '{name} ({id})\t[{current_version}]'
        .format(name=self.name,
                id=self.id,
                current_version=self.current_version_string))


# pylint: disable=g-missing-from-attributes
class ComponentDiff(object):
  """Encapsulates the difference for a single component between snapshots.

  Attributes:
    id: str, The component id.
    name: str, The display name of the component.
    current: schemas.Component, The current component definition.
    latest: schemas.Component, The latest component definition that we can move
      to.
    state: ComponentState constant, The type of difference that exists for this
      component between the given snapshots.
  """

  def __init__(self, component_id, current_snapshot, latest_snapshot,
               platform_filter=None):
    """Create a new diff.

    Args:
      component_id: str, The id of this component.
      current_snapshot: ComponentSnapshot, The base snapshot to compare against.
      latest_snapshot: ComponentSnapshot, The new snapshot.
      platform_filter: platforms.Platform, A platform that components must
        match in order to be considered for any operations.
    """
    self.id = component_id
    self.__current = current_snapshot.ComponentFromId(component_id)
    self.__latest = latest_snapshot.ComponentFromId(component_id)
    self.current_version_string = (self.__current.version.version_string
                                   if self.__current else None)
    self.latest_version_string = (self.__latest.version.version_string
                                  if self.__latest else None)

    data_provider = self.__latest if self.__latest else self.__current
    self.name = data_provider.details.display_name
    self.is_hidden = data_provider.is_hidden
    self.is_configuration = data_provider.is_configuration
    self.platform_required = data_provider.platform_required
    self.state = self._ComputeState()
    self.platform = platform_filter
    active_snapshot = latest_snapshot if self.__latest else current_snapshot
    self.size = active_snapshot.GetEffectiveComponentSize(
        component_id, platform_filter=platform_filter)

  def _ComputeState(self):
    """Returns the component state."""
    if self.__current is None:
      return ComponentState.NEW
    elif self.__latest is None:
      return ComponentState.REMOVED
    elif (self.__latest.version.build_number >
          self.__current.version.build_number):
      return ComponentState.UPDATE_AVAILABLE
    # We have a more recent version than the latest.  This can happen because we
    # don't release updated components if they contained identical code.  Check
    # to see if the checksums match, and suppress the update if they are the
    # same.
    elif (self.__latest.version.build_number <
          self.__current.version.build_number):
      # Component has no data at all, don't flag it as an update.
      if self.__latest.data is None and self.__current.data is None:
        return ComponentState.UP_TO_DATE
      # One has data and the other does not.  This is clearly a change.
      elif bool(self.__latest.data) ^ bool(self.__current.data):
        return ComponentState.UPDATE_AVAILABLE
      # Both have data, check to see if they are the same.
      elif (self.__latest.data.contents_checksum !=
            self.__current.data.contents_checksum):
        return ComponentState.UPDATE_AVAILABLE
    return ComponentState.UP_TO_DATE

  def __str__(self):
    return (
        '[ {status} ]\t{name} ({id})\t[{current_version}]\t[{latest_version}]'
        .format(status=self.state.name, name=self.name, id=self.id,
                current_version=self.current_version_string,
                latest_version=self.latest_version_string))


class ComponentState(object):
  """An enum for the available update states."""

  class _ComponentState(object):

    def __init__(self, name):
      self.name = name

    def __str__(self):
      return self.name

  UP_TO_DATE = _ComponentState('Installed')
  UPDATE_AVAILABLE = _ComponentState('Update Available')
  REMOVED = _ComponentState('Deprecated')
  NEW = _ComponentState('Not Installed')

  @staticmethod
  def All():
    """Gets all the different states.

    Returns:
      list(ComponentStateTuple), All the states.
    """
    return [ComponentState.UPDATE_AVAILABLE, ComponentState.REMOVED,
            ComponentState.NEW, ComponentState.UP_TO_DATE]
