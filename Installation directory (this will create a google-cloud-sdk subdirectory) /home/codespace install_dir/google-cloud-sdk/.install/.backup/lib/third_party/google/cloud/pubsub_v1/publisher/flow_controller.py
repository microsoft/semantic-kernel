# Copyright 2020, Google LLC All rights reserved.
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

from collections import OrderedDict
import logging
import threading
from typing import Dict, Optional, Type
import warnings

from google.cloud.pubsub_v1 import types
from google.cloud.pubsub_v1.publisher import exceptions


_LOGGER = logging.getLogger(__name__)


MessageType = Type[types.PubsubMessage]  # type: ignore


class _QuantityReservation:
    """A (partial) reservation of quantifiable resources."""

    def __init__(self, bytes_reserved: int, bytes_needed: int, has_slot: bool):
        self.bytes_reserved = bytes_reserved
        self.bytes_needed = bytes_needed
        self.has_slot = has_slot

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"bytes_reserved={self.bytes_reserved}, "
            f"bytes_needed={self.bytes_needed}, "
            f"has_slot={self.has_slot})"
        )


class FlowController(object):
    """A class used to control the flow of messages passing through it.

    Args:
        settings: Desired flow control configuration.
    """

    def __init__(self, settings: types.PublishFlowControl):
        self._settings = settings

        # Load statistics. They represent the number of messages added, but not
        # yet released (and their total size).
        self._message_count = 0
        self._total_bytes = 0

        # A FIFO queue of threads blocked on adding a message that also tracks their
        # reservations of available flow control bytes and message slots.
        # Only relevant if the configured limit exceeded behavior is BLOCK.
        self._waiting: Dict[threading.Thread, _QuantityReservation] = OrderedDict()

        self._reserved_bytes = 0
        self._reserved_slots = 0

        # The lock is used to protect all internal state (message and byte count,
        # waiting threads to add, etc.).
        self._operational_lock = threading.Lock()

        # The condition for blocking the flow if capacity is exceeded.
        self._has_capacity = threading.Condition(lock=self._operational_lock)

    def add(self, message: MessageType) -> None:
        """Add a message to flow control.

        Adding a message updates the internal load statistics, and an action is
        taken if these limits are exceeded (depending on the flow control settings).

        Args:
            message:
                The message entering the flow control.

        Raises:
            :exception:`~pubsub_v1.publisher.exceptions.FlowControlLimitError`:
                Raised when the desired action is
                :attr:`~google.cloud.pubsub_v1.types.LimitExceededBehavior.ERROR` and
                the message would exceed flow control limits, or when the desired action
                is :attr:`~google.cloud.pubsub_v1.types.LimitExceededBehavior.BLOCK` and
                the message would block forever against the flow control limits.
        """
        if self._settings.limit_exceeded_behavior == types.LimitExceededBehavior.IGNORE:
            return

        with self._operational_lock:
            if not self._would_overflow(message):
                self._message_count += 1
                self._total_bytes += message._pb.ByteSize()
                return

            # Adding a message would overflow, react.
            if (
                self._settings.limit_exceeded_behavior
                == types.LimitExceededBehavior.ERROR
            ):
                # Raising an error means rejecting a message, thus we do not
                # add anything to the existing load, but we do report the would-be
                # load if we accepted the message.
                load_info = self._load_info(
                    message_count=self._message_count + 1,
                    total_bytes=self._total_bytes + message._pb.ByteSize(),
                )
                error_msg = "Flow control limits would be exceeded - {}.".format(
                    load_info
                )
                raise exceptions.FlowControlLimitError(error_msg)

            assert (
                self._settings.limit_exceeded_behavior
                == types.LimitExceededBehavior.BLOCK
            )

            # Sanity check - if a message exceeds total flow control limits all
            # by itself, it would block forever, thus raise error.
            if (
                message._pb.ByteSize() > self._settings.byte_limit
                or self._settings.message_limit < 1
            ):
                load_info = self._load_info(
                    message_count=1, total_bytes=message._pb.ByteSize()
                )
                error_msg = (
                    "Total flow control limits too low for the message, "
                    "would block forever - {}.".format(load_info)
                )
                raise exceptions.FlowControlLimitError(error_msg)

            current_thread = threading.current_thread()

            while self._would_overflow(message):
                if current_thread not in self._waiting:
                    reservation = _QuantityReservation(
                        bytes_reserved=0,
                        bytes_needed=message._pb.ByteSize(),
                        has_slot=False,
                    )
                    self._waiting[current_thread] = reservation  # Will be placed last.

                _LOGGER.debug(
                    "Blocking until there is enough free capacity in the flow - "
                    "{}.".format(self._load_info())
                )

                self._has_capacity.wait()

                _LOGGER.debug(
                    "Woke up from waiting on free capacity in the flow - "
                    "{}.".format(self._load_info())
                )

            # Message accepted, increase the load and remove thread stats.
            self._message_count += 1
            self._total_bytes += message._pb.ByteSize()
            self._reserved_bytes -= self._waiting[current_thread].bytes_reserved
            self._reserved_slots -= 1
            del self._waiting[current_thread]

    def release(self, message: MessageType) -> None:
        """Release a mesage from flow control.

        Args:
            message:
                The message entering the flow control.
        """
        if self._settings.limit_exceeded_behavior == types.LimitExceededBehavior.IGNORE:
            return

        with self._operational_lock:
            # Releasing a message decreases the load.
            self._message_count -= 1
            self._total_bytes -= message._pb.ByteSize()

            if self._message_count < 0 or self._total_bytes < 0:
                warnings.warn(
                    "Releasing a message that was never added or already released.",
                    category=RuntimeWarning,
                    stacklevel=2,
                )
                self._message_count = max(0, self._message_count)
                self._total_bytes = max(0, self._total_bytes)

            self._distribute_available_capacity()

            # If at least one thread waiting to add() can be unblocked, wake them up.
            if self._ready_to_unblock():
                _LOGGER.debug("Notifying threads waiting to add messages to flow.")
                self._has_capacity.notify_all()

    def _distribute_available_capacity(self) -> None:
        """Distribute available capacity among the waiting threads in FIFO order.

        The method assumes that the caller has obtained ``_operational_lock``.
        """
        available_slots = (
            self._settings.message_limit - self._message_count - self._reserved_slots
        )
        available_bytes = (
            self._settings.byte_limit - self._total_bytes - self._reserved_bytes
        )

        for reservation in self._waiting.values():
            if available_slots <= 0 and available_bytes <= 0:
                break  # Santa is now empty-handed, better luck next time.

            # Distribute any free slots.
            if available_slots > 0 and not reservation.has_slot:
                reservation.has_slot = True
                self._reserved_slots += 1
                available_slots -= 1

            # Distribute any free bytes.
            if available_bytes <= 0:
                continue

            bytes_still_needed = reservation.bytes_needed - reservation.bytes_reserved

            if bytes_still_needed < 0:  # Sanity check for any internal inconsistencies.
                msg = "Too many bytes reserved: {} / {}".format(
                    reservation.bytes_reserved, reservation.bytes_needed
                )
                warnings.warn(msg, category=RuntimeWarning)
                bytes_still_needed = 0

            can_give = min(bytes_still_needed, available_bytes)
            reservation.bytes_reserved += can_give
            self._reserved_bytes += can_give
            available_bytes -= can_give

    def _ready_to_unblock(self) -> bool:
        """Determine if any of the threads waiting to add a message can proceed.

        The method assumes that the caller has obtained ``_operational_lock``.
        """
        if self._waiting:
            # It's enough to only check the head of the queue, because FIFO
            # distribution of any free capacity.
            first_reservation = next(iter(self._waiting.values()))
            return (
                first_reservation.bytes_reserved >= first_reservation.bytes_needed
                and first_reservation.has_slot
            )

        return False

    def _would_overflow(self, message: MessageType) -> bool:
        """Determine if accepting a message would exceed flow control limits.

        The method assumes that the caller has obtained ``_operational_lock``.

        Args:
            message: The message entering the flow control.
        """
        reservation = self._waiting.get(threading.current_thread())

        if reservation:
            enough_reserved = reservation.bytes_reserved >= reservation.bytes_needed
            has_slot = reservation.has_slot
        else:
            enough_reserved = False
            has_slot = False

        bytes_taken = self._total_bytes + self._reserved_bytes + message._pb.ByteSize()
        size_overflow = bytes_taken > self._settings.byte_limit and not enough_reserved

        msg_count_overflow = not has_slot and (
            (self._message_count + self._reserved_slots + 1)
            > self._settings.message_limit
        )

        return size_overflow or msg_count_overflow

    def _load_info(
        self, message_count: Optional[int] = None, total_bytes: Optional[int] = None
    ) -> str:
        """Return the current flow control load information.

        The caller can optionally adjust some of the values to fit its reporting
        needs.

        The method assumes that the caller has obtained ``_operational_lock``.

        Args:
            message_count:
                The value to override the current message count with.
            total_bytes:
                The value to override the current total bytes with.
        """
        if message_count is None:
            message_count = self._message_count

        if total_bytes is None:
            total_bytes = self._total_bytes

        return (
            f"messages: {message_count} / {self._settings.message_limit} "
            f"(reserved: {self._reserved_slots}), "
            f"bytes: {total_bytes} / {self._settings.byte_limit} "
            f"(reserved: {self._reserved_bytes})"
        )
