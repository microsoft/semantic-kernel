# Copyright 2017, Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import copy
import logging
import random
import threading
import time
import typing
from typing import Dict, Iterable, Optional, Union

from google.cloud.pubsub_v1.subscriber._protocol.dispatcher import _MAX_BATCH_LATENCY

try:
    from collections.abc import KeysView

    KeysView[None]  # KeysView is only subscriptable in Python 3.9+
except TypeError:
    # Deprecated since Python 3.9, thus only use as a fallback in older Python versions
    from typing import KeysView

from google.cloud.pubsub_v1.subscriber._protocol import requests

if typing.TYPE_CHECKING:  # pragma: NO COVER
    from google.cloud.pubsub_v1.subscriber._protocol.streaming_pull_manager import (
        StreamingPullManager,
    )


_LOGGER = logging.getLogger(__name__)
_LEASE_WORKER_NAME = "Thread-LeaseMaintainer"


class _LeasedMessage(typing.NamedTuple):
    sent_time: float
    """The local time when ACK ID was initially leased in seconds since the epoch."""

    size: int
    ordering_key: Optional[str]


class Leaser(object):
    def __init__(self, manager: "StreamingPullManager"):
        self._thread: Optional[threading.Thread] = None
        self._manager = manager

        # a lock used for start/stop operations, protecting the _thread attribute
        self._operational_lock = threading.Lock()

        # A lock ensuring that add/remove operations are atomic and cannot be
        # intertwined. Protects the _leased_messages and _bytes attributes.
        self._add_remove_lock = threading.Lock()

        # Dict of ack_id -> _LeasedMessage
        self._leased_messages: Dict[str, _LeasedMessage] = {}

        self._bytes = 0
        """The total number of bytes consumed by leased messages."""

        self._stop_event = threading.Event()

    @property
    def message_count(self) -> int:
        """The number of leased messages."""
        return len(self._leased_messages)

    @property
    def ack_ids(self) -> KeysView[str]:
        """The ack IDs of all leased messages."""
        return self._leased_messages.keys()

    @property
    def bytes(self) -> int:
        """The total size, in bytes, of all leased messages."""
        return self._bytes

    def add(self, items: Iterable[requests.LeaseRequest]) -> None:
        """Add messages to be managed by the leaser."""
        with self._add_remove_lock:
            for item in items:
                # Add the ack ID to the set of managed ack IDs, and increment
                # the size counter.
                if item.ack_id not in self._leased_messages:
                    self._leased_messages[item.ack_id] = _LeasedMessage(
                        sent_time=float("inf"),
                        size=item.byte_size,
                        ordering_key=item.ordering_key,
                    )
                    self._bytes += item.byte_size
                else:
                    _LOGGER.debug("Message %s is already lease managed", item.ack_id)

    def start_lease_expiry_timer(self, ack_ids: Iterable[str]) -> None:
        """Start the lease expiry timer for `items`.

        Args:
            items: Sequence of ack-ids for which to start lease expiry timers.
        """
        with self._add_remove_lock:
            for ack_id in ack_ids:
                lease_info = self._leased_messages.get(ack_id)
                # Lease info might not exist for this ack_id because it has already
                # been removed by remove().
                if lease_info:
                    self._leased_messages[ack_id] = lease_info._replace(
                        sent_time=time.time()
                    )

    def remove(
        self,
        items: Iterable[
            Union[requests.AckRequest, requests.DropRequest, requests.NackRequest]
        ],
    ) -> None:
        """Remove messages from lease management."""
        with self._add_remove_lock:
            # Remove the ack ID from lease management, and decrement the
            # byte counter.
            for item in items:
                if self._leased_messages.pop(item.ack_id, None) is not None:
                    self._bytes -= item.byte_size
                else:
                    _LOGGER.debug("Item %s was not managed.", item.ack_id)

            if self._bytes < 0:
                _LOGGER.debug("Bytes was unexpectedly negative: %d", self._bytes)
                self._bytes = 0

    def maintain_leases(self) -> None:
        """Maintain all of the leases being managed.

        This method modifies the ack deadline for all of the managed
        ack IDs, then waits for most of that time (but with jitter), and
        repeats.
        """
        while not self._stop_event.is_set():
            # Determine the appropriate duration for the lease. This is
            # based off of how long previous messages have taken to ack, with
            # a sensible default and within the ranges allowed by Pub/Sub.
            # Also update the deadline currently used if enough new ACK data has been
            # gathered since the last deadline update.
            deadline = self._manager._obtain_ack_deadline(maybe_update=True)
            _LOGGER.debug("The current deadline value is %d seconds.", deadline)

            # Make a copy of the leased messages. This is needed because it's
            # possible for another thread to modify the dictionary while
            # we're iterating over it.
            leased_messages = copy.copy(self._leased_messages)

            # Drop any leases that are beyond the max lease time. This ensures
            # that in the event of a badly behaving actor, we can drop messages
            # and allow the Pub/Sub server to resend them.
            cutoff = time.time() - self._manager.flow_control.max_lease_duration
            to_drop = [
                requests.DropRequest(ack_id, item.size, item.ordering_key)
                for ack_id, item in leased_messages.items()
                if item.sent_time < cutoff
            ]

            if to_drop:
                _LOGGER.warning(
                    "Dropping %s items because they were leased too long.", len(to_drop)
                )
                assert self._manager.dispatcher is not None
                self._manager.dispatcher.drop(to_drop)

            # Remove dropped items from our copy of the leased messages (they
            # have already been removed from the real one by
            # self._manager.drop(), which calls self.remove()).
            for item in to_drop:
                leased_messages.pop(item.ack_id)

            # Create a modack request.
            # We do not actually call `modify_ack_deadline` over and over
            # because it is more efficient to make a single request.
            ack_ids = leased_messages.keys()
            expired_ack_ids = set()
            if ack_ids:
                _LOGGER.debug("Renewing lease for %d ack IDs.", len(ack_ids))

                # NOTE: This may not work as expected if ``consumer.active``
                #       has changed since we checked it. An implementation
                #       without any sort of race condition would require a
                #       way for ``send_request`` to fail when the consumer
                #       is inactive.
                assert self._manager.dispatcher is not None
                ack_id_gen = (ack_id for ack_id in ack_ids)
                expired_ack_ids = self._manager._send_lease_modacks(
                    ack_id_gen, deadline
                )

            start_time = time.time()
            # If exactly once delivery is enabled, we should drop all expired ack_ids from lease management.
            if self._manager._exactly_once_delivery_enabled() and len(expired_ack_ids):
                assert self._manager.dispatcher is not None
                self._manager.dispatcher.drop(
                    [
                        requests.DropRequest(
                            ack_id,
                            leased_messages.get(ack_id).size,  # type: ignore
                            leased_messages.get(ack_id).ordering_key,  # type: ignore
                        )
                        for ack_id in expired_ack_ids
                        if ack_id in leased_messages
                    ]
                )
            # Now wait an appropriate period of time and do this again.
            #
            # We determine the appropriate period of time based on a random
            # period between:
            # minimum: MAX_BATCH_LATENCY (to prevent duplicate modacks being created in one batch)
            # maximum: 90% of the deadline
            # This maximum time attempts to prevent ack expiration before new lease modacks arrive at the server.
            # This use of jitter (http://bit.ly/2s2ekL7) helps decrease contention in cases
            # where there are many clients.
            # If we spent any time iterating over expired acks, we should subtract this from the deadline.
            snooze = random.uniform(
                _MAX_BATCH_LATENCY, (deadline * 0.9 - (time.time() - start_time))
            )
            _LOGGER.debug("Snoozing lease management for %f seconds.", snooze)
            self._stop_event.wait(timeout=snooze)

        _LOGGER.debug("%s exiting.", _LEASE_WORKER_NAME)

    def start(self) -> None:
        with self._operational_lock:
            if self._thread is not None:
                raise ValueError("Leaser is already running.")

            # Create and start the helper thread.
            self._stop_event.clear()
            thread = threading.Thread(
                name=_LEASE_WORKER_NAME, target=self.maintain_leases
            )
            thread.daemon = True
            thread.start()
            _LOGGER.debug("Started helper thread %s", thread.name)
            self._thread = thread

    def stop(self) -> None:
        with self._operational_lock:
            self._stop_event.set()

            if self._thread is not None:
                # The thread should automatically exit when the consumer is
                # inactive.
                self._thread.join()

            self._thread = None
