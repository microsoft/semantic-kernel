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

"""This module implements update checking and notification to the user.

It provides a context manager around the cache file that stores information
about the last update check.  The general process is as follows:

1) This stores the last time an update check occurred, so the check will only
   be done if the update check frequency has expired.
2) When an update check is done, all notifications in the latest snapshot are
   queried to see if their condition matches the current state of the SDK.  Any
   notifications that match are "activated" and cached.
3) Every time a command is run, Notify() is called to notify the user of
   available updates.  It loops over the activated notifications and determines
   if any of the triggers match the current command invocation.  If there is a
   match, the notification is printed and the last nag time is recorded for that
   particular notification.  At most one notification is printed per command.
   The priority is determined by the order the notifications are registered
   in the component snapshot.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os
import time

from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.updater import schemas
from googlecloudsdk.core.util import files

import six


class UpdateCheckData(object):
  """A class to hold update checking data and to perform notifications."""

  UPDATE_CHECK_FREQUENCY_IN_SECONDS = 86400  # Once a day.

  def __init__(self):
    self._last_update_check_file = config.Paths().update_check_cache_path
    self._dirty = False
    self._data = self._LoadData()

  def _LoadData(self):
    """Deserializes data from the json file."""
    if not os.path.isfile(self._last_update_check_file):
      return schemas.LastUpdateCheck.FromDictionary({})

    raw_data = files.ReadFileContents(self._last_update_check_file)
    try:
      data = json.loads(raw_data)
      return schemas.LastUpdateCheck.FromDictionary(data)
    except ValueError:
      log.debug('Failed to parse update check cache file.  Using empty '
                'cache instead.')
      return schemas.LastUpdateCheck.FromDictionary({})

  def _SaveData(self):
    """Serializes data to the json file."""
    if not self._dirty:
      return
    files.WriteFileContents(self._last_update_check_file,
                            json.dumps(self._data.ToDictionary()))
    self._dirty = False

  def __enter__(self):
    return self

  def __exit__(self, *args):
    self._SaveData()

  def LastUpdateCheckRevision(self):
    """Gets the revision of the snapshot from the last update check.

    Returns:
      long, The revision of the last checked snapshot.  This is a long int but
        formatted as an actual date in seconds (i.e 20151009132504). It is *NOT*
        seconds since the epoch.
    """
    return self._data.last_update_check_revision

  def LastUpdateCheckTime(self):
    """Gets the time of the last update check as seconds since the epoch.

    Returns:
      int, The time of the last update check in seconds since the epoch.
    """
    return self._data.last_update_check_time

  def SecondsSinceLastUpdateCheck(self):
    """Gets the number of seconds since we last did an update check.

    Returns:
      int, The amount of time in seconds.
    """
    return time.time() - self._data.last_update_check_time

  def ShouldDoUpdateCheck(self):
    """Checks if it is time to do an update check.

    Returns:
      True, if enough time has elapsed and we should perform another update
      check.  False otherwise.
    """
    return (self.SecondsSinceLastUpdateCheck() >=
            UpdateCheckData.UPDATE_CHECK_FREQUENCY_IN_SECONDS)

  def UpdatesAvailable(self):
    """Returns whether we already know about updates that are available.

    Returns:
      bool, True if we know about updates, False otherwise.
    """
    return bool([
        notification for notification in self._data.notifications
        if notification.condition.check_components
    ])

  def SetFromSnapshot(self, snapshot, component_updates_available, force=False):
    """Sets that we just did an update check and found the given snapshot.

    If the given snapshot is different than the last one we saw, refresh the set
    of activated notifications for available updates for any notifications with
    matching conditions.

    You must call Save() to persist these changes or use this as a context
    manager.

    Args:
      snapshot: snapshots.ComponentSnapshot, The latest snapshot available.
      component_updates_available: bool, True if there are updates to components
        we have installed.  False otherwise.
      force: bool, True to force a recalculation of whether there are available
        updates, even if the snapshot revision has not changed.
    """
    if force or self.LastUpdateCheckRevision() != snapshot.revision:
      log.debug('Updating notification cache...')

      current_version = config.INSTALLATION_CONFIG.version
      current_revision = config.INSTALLATION_CONFIG.revision

      activated = []

      possible_notifications = snapshot.sdk_definition.notifications
      for notification in possible_notifications:
        if notification.condition.Matches(
            current_version, current_revision, component_updates_available):
          log.debug('Activating notification: [%s]', notification.id)
          activated.append(notification)

      self._data.notifications = activated
      self._CleanUpLastNagTimes()

    self._data.last_update_check_time = time.time()
    self._data.last_update_check_revision = snapshot.revision
    self._dirty = True

  def SetFromIncompatibleSchema(self):
    """Sets that we just did an update check and found a new schema version.

    An incompatible schema version means there are definitely updates available
    but we can't read the notifications to correctly notify the user.  This will
    install a default notification for the incompatible schema.

    You must call Save() to persist these changes or use this as a context
    manager.
    """
    log.debug('Incompatible schema found.  Activating default notification.')

    # Nag once a week to update if the schema changed and we don't know what's
    # going on anymore.
    notification_spec = schemas.NotificationSpec(
        id='incompatible',
        condition=schemas.Condition(None, None, None, None, False),
        trigger=schemas.Trigger(frequency=604800, command_regex=None),
        notification=schemas.Notification(None, None, None)
    )
    self._data.notifications = [notification_spec]
    self._CleanUpLastNagTimes()

    self._data.last_update_check_time = time.time()
    self._data.last_update_check_revision = 0  # Doesn't matter
    self._dirty = True

  def _CleanUpLastNagTimes(self):
    """Clean the map holding the last nag times for each notification.

    If a notification is no longer activate, it is removed from the map.  Any
    notifications that are still activated have their last nag times preserved.
    """
    activated_ids = [n.id for n in self._data.notifications]
    self._data.last_nag_times = (
        dict(
            (name, value)
            for name, value in six.iteritems(self._data.last_nag_times)
            if name in activated_ids))

  def Notify(self, command_path):
    """Notify the user of any available updates.

    This should be called for every command that is run.  It does not actually
    do an update check, and does not necessarily notify the user each time.  The
    user will only be notified if there are activated notifications and if the
    trigger for one of the activated notifications matches.  At most one
    notification will be printed per command.  Order or priority is determined
    by the order in which the notifications are registered in the component
    snapshot file.

    Args:
      command_path: str, The '.' separated path of the command that is currently
        being run (i.e. gcloud.foo.bar).
    """
    # Only nag if we are running in an interactive terminal.
    if not log.out.isatty() or not log.status.isatty():
      return

    for notification in self._data.notifications:
      name = notification.id
      last_nag_time = self._data.last_nag_times.get(name, 0)

      # Only notify if the trigger matches.  Exit as soon as one notification
      # is printed.
      if notification.trigger.Matches(last_nag_time, command_path):
        log.status.write(notification.notification.NotificationMessage())
        self._data.last_nag_times[name] = time.time()
        self._dirty = True
        break
