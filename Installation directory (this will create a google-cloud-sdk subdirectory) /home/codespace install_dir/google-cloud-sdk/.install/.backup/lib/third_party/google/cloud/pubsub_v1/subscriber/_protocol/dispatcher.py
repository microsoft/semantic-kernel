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
from __future__ import division

import functools
import itertools
import logging
import math
import time
import threading
import typing
from typing import List, Optional, Sequence, Union
import warnings
from google.api_core.retry import exponential_sleep_generator

from google.cloud.pubsub_v1.subscriber._protocol import helper_threads
from google.cloud.pubsub_v1.subscriber._protocol import requests
from google.cloud.pubsub_v1.subscriber.exceptions import (
    AcknowledgeStatus,
)

if typing.TYPE_CHECKING:  # pragma: NO COVER
    import queue
    from google.cloud.pubsub_v1.subscriber._protocol.streaming_pull_manager import (
        StreamingPullManager,
    )


RequestItem = Union[
    requests.AckRequest,
    requests.DropRequest,
    requests.LeaseRequest,
    requests.ModAckRequest,
    requests.NackRequest,
]


_LOGGER = logging.getLogger(__name__)
_CALLBACK_WORKER_NAME = "Thread-CallbackRequestDispatcher"


_MAX_BATCH_SIZE = 100
"""The maximum number of requests to process and dispatch at a time."""

_MAX_BATCH_LATENCY = 0.01
"""The maximum amount of time in seconds to wait for additional request items
before processing the next batch of requests."""

_ACK_IDS_BATCH_SIZE = 1000
"""The maximum number of ACK IDs to send in a single StreamingPullRequest.
"""

_MIN_EXACTLY_ONCE_DELIVERY_ACK_MODACK_RETRY_DURATION_SECS = 1
"""The time to wait for the first retry of failed acks and modacks when exactly-once
delivery is enabled."""

_MAX_EXACTLY_ONCE_DELIVERY_ACK_MODACK_RETRY_DURATION_SECS = 10 * 60
"""The maximum amount of time in seconds to retry failed acks and modacks when
exactly-once delivery is enabled."""


class Dispatcher(object):
    def __init__(self, manager: "StreamingPullManager", queue: "queue.Queue"):
        self._manager = manager
        self._queue = queue
        self._thread: Optional[threading.Thread] = None
        self._operational_lock = threading.Lock()

    def start(self) -> None:
        """Start a thread to dispatch requests queued up by callbacks.

        Spawns a thread to run :meth:`dispatch_callback`.
        """
        with self._operational_lock:
            if self._thread is not None:
                raise ValueError("Dispatcher is already running.")

            worker = helper_threads.QueueCallbackWorker(
                self._queue,
                self.dispatch_callback,
                max_items=_MAX_BATCH_SIZE,
                max_latency=_MAX_BATCH_LATENCY,
            )
            # Create and start the helper thread.
            thread = threading.Thread(name=_CALLBACK_WORKER_NAME, target=worker)
            thread.daemon = True
            thread.start()
            _LOGGER.debug("Started helper thread %s", thread.name)
            self._thread = thread

    def stop(self) -> None:
        with self._operational_lock:
            if self._thread is not None:
                # Signal the worker to stop by queueing a "poison pill"
                self._queue.put(helper_threads.STOP)
                self._thread.join()

            self._thread = None

    def dispatch_callback(self, items: Sequence[RequestItem]) -> None:
        """Map the callback request to the appropriate gRPC request.

        Args:
            items:
                Queued requests to dispatch.
        """
        lease_requests: List[requests.LeaseRequest] = []
        modack_requests: List[requests.ModAckRequest] = []
        ack_requests: List[requests.AckRequest] = []
        nack_requests: List[requests.NackRequest] = []
        drop_requests: List[requests.DropRequest] = []

        lease_ids = set()
        modack_ids = set()
        ack_ids = set()
        nack_ids = set()
        drop_ids = set()
        exactly_once_delivery_enabled = self._manager._exactly_once_delivery_enabled()

        for item in items:
            if isinstance(item, requests.LeaseRequest):
                if (
                    item.ack_id not in lease_ids
                ):  # LeaseRequests have no futures to handle.
                    lease_ids.add(item.ack_id)
                    lease_requests.append(item)
            elif isinstance(item, requests.ModAckRequest):
                if item.ack_id in modack_ids:
                    self._handle_duplicate_request_future(
                        exactly_once_delivery_enabled, item
                    )
                else:
                    modack_ids.add(item.ack_id)
                    modack_requests.append(item)
            elif isinstance(item, requests.AckRequest):
                if item.ack_id in ack_ids:
                    self._handle_duplicate_request_future(
                        exactly_once_delivery_enabled, item
                    )
                else:
                    ack_ids.add(item.ack_id)
                    ack_requests.append(item)
            elif isinstance(item, requests.NackRequest):
                if item.ack_id in nack_ids:
                    self._handle_duplicate_request_future(
                        exactly_once_delivery_enabled, item
                    )
                else:
                    nack_ids.add(item.ack_id)
                    nack_requests.append(item)
            elif isinstance(item, requests.DropRequest):
                if (
                    item.ack_id not in drop_ids
                ):  # DropRequests have no futures to handle.
                    drop_ids.add(item.ack_id)
                    drop_requests.append(item)
            else:
                warnings.warn(
                    f'Skipping unknown request item of type "{type(item)}"',
                    category=RuntimeWarning,
                )

        _LOGGER.debug("Handling %d batched requests", len(items))

        if lease_requests:
            self.lease(lease_requests)

        if modack_requests:
            self.modify_ack_deadline(modack_requests)

        # Note: Drop and ack *must* be after lease. It's possible to get both
        # the lease and the ack/drop request in the same batch.
        if ack_requests:
            self.ack(ack_requests)

        if nack_requests:
            self.nack(nack_requests)

        if drop_requests:
            self.drop(drop_requests)

    def _handle_duplicate_request_future(
        self,
        exactly_once_delivery_enabled: bool,
        item: Union[requests.AckRequest, requests.ModAckRequest, requests.NackRequest],
    ) -> None:
        _LOGGER.debug(
            "This is a duplicate %s with the same ack_id: %s.",
            type(item),
            item.ack_id,
        )
        if item.future:
            if exactly_once_delivery_enabled:
                item.future.set_exception(
                    ValueError(f"Duplicate ack_id for {type(item)}")
                )
                # Futures may be present even with exactly-once delivery
                # disabled, in transition periods after the setting is changed on
                # the subscription.
            else:
                # When exactly-once delivery is NOT enabled, acks/modacks are considered
                # best-effort, so the future should succeed even though this is a duplicate.
                item.future.set_result(AcknowledgeStatus.SUCCESS)

    def ack(self, items: Sequence[requests.AckRequest]) -> None:
        """Acknowledge the given messages.

        Args:
            items: The items to acknowledge.
        """
        # If we got timing information, add it to the histogram.
        for item in items:
            time_to_ack = item.time_to_ack
            if time_to_ack is not None:
                self._manager.ack_histogram.add(time_to_ack)

        # We must potentially split the request into multiple smaller requests
        # to avoid the server-side max request size limit.
        items_gen = iter(items)
        ack_ids_gen = (item.ack_id for item in items)
        total_chunks = int(math.ceil(len(items) / _ACK_IDS_BATCH_SIZE))

        for _ in range(total_chunks):
            ack_reqs_dict = {
                req.ack_id: req
                for req in itertools.islice(items_gen, _ACK_IDS_BATCH_SIZE)
            }
            requests_completed, requests_to_retry = self._manager.send_unary_ack(
                ack_ids=list(itertools.islice(ack_ids_gen, _ACK_IDS_BATCH_SIZE)),
                ack_reqs_dict=ack_reqs_dict,
            )

            # Remove the completed messages from lease management.
            self.drop(requests_completed)

            # Retry on a separate thread so the dispatcher thread isn't blocked
            # by sleeps.
            if requests_to_retry:
                self._start_retry_thread(
                    "Thread-RetryAcks",
                    functools.partial(self._retry_acks, requests_to_retry),
                )

    def _start_retry_thread(self, thread_name, thread_target):
        # note: if the thread is *not* a daemon, a memory leak exists due to a cpython issue.
        # https://github.com/googleapis/python-pubsub/issues/395#issuecomment-829910303
        # https://github.com/googleapis/python-pubsub/issues/395#issuecomment-830092418
        retry_thread = threading.Thread(
            name=thread_name,
            target=thread_target,
            daemon=True,
        )
        # The thread finishes when the requests succeed or eventually fail with
        # a back-end timeout error or other permanent failure.
        retry_thread.start()

    def _retry_acks(self, requests_to_retry):
        retry_delay_gen = exponential_sleep_generator(
            initial=_MIN_EXACTLY_ONCE_DELIVERY_ACK_MODACK_RETRY_DURATION_SECS,
            maximum=_MAX_EXACTLY_ONCE_DELIVERY_ACK_MODACK_RETRY_DURATION_SECS,
        )
        while requests_to_retry:
            time_to_wait = next(retry_delay_gen)
            _LOGGER.debug(
                "Retrying {len(requests_to_retry)} ack(s) after delay of "
                + str(time_to_wait)
                + " seconds"
            )
            time.sleep(time_to_wait)

            ack_reqs_dict = {req.ack_id: req for req in requests_to_retry}
            requests_completed, requests_to_retry = self._manager.send_unary_ack(
                ack_ids=[req.ack_id for req in requests_to_retry],
                ack_reqs_dict=ack_reqs_dict,
            )
            assert (
                len(requests_to_retry) <= _ACK_IDS_BATCH_SIZE
            ), "Too many requests to be retried."
            # Remove the completed messages from lease management.
            self.drop(requests_completed)

    def drop(
        self,
        items: Sequence[
            Union[requests.AckRequest, requests.DropRequest, requests.NackRequest]
        ],
    ) -> None:
        """Remove the given messages from lease management.

        Args:
            items: The items to drop.
        """
        assert self._manager.leaser is not None
        self._manager.leaser.remove(items)
        ordering_keys = (k.ordering_key for k in items if k.ordering_key)
        self._manager.activate_ordering_keys(ordering_keys)
        self._manager.maybe_resume_consumer()

    def lease(self, items: Sequence[requests.LeaseRequest]) -> None:
        """Add the given messages to lease management.

        Args:
            items: The items to lease.
        """
        assert self._manager.leaser is not None
        self._manager.leaser.add(items)
        self._manager.maybe_pause_consumer()

    def modify_ack_deadline(
        self,
        items: Sequence[requests.ModAckRequest],
        default_deadline: Optional[float] = None,
    ) -> None:
        """Modify the ack deadline for the given messages.

        Args:
            items: The items to modify.
        """
        # We must potentially split the request into multiple smaller requests
        # to avoid the server-side max request size limit.
        items_gen = iter(items)
        ack_ids_gen = (item.ack_id for item in items)
        deadline_seconds_gen = (item.seconds for item in items)
        total_chunks = int(math.ceil(len(items) / _ACK_IDS_BATCH_SIZE))

        for _ in range(total_chunks):
            ack_reqs_dict = {
                req.ack_id: req
                for req in itertools.islice(items_gen, _ACK_IDS_BATCH_SIZE)
            }
            requests_to_retry: List[requests.ModAckRequest]
            if default_deadline is None:
                # no further work needs to be done for `requests_to_retry`
                _, requests_to_retry = self._manager.send_unary_modack(
                    modify_deadline_ack_ids=list(
                        itertools.islice(ack_ids_gen, _ACK_IDS_BATCH_SIZE)
                    ),
                    modify_deadline_seconds=list(
                        itertools.islice(deadline_seconds_gen, _ACK_IDS_BATCH_SIZE)
                    ),
                    ack_reqs_dict=ack_reqs_dict,
                    default_deadline=None,
                )
            else:
                _, requests_to_retry = self._manager.send_unary_modack(
                    modify_deadline_ack_ids=itertools.islice(
                        ack_ids_gen, _ACK_IDS_BATCH_SIZE
                    ),
                    modify_deadline_seconds=None,
                    ack_reqs_dict=ack_reqs_dict,
                    default_deadline=default_deadline,
                )
            assert (
                len(requests_to_retry) <= _ACK_IDS_BATCH_SIZE
            ), "Too many requests to be retried."

            # Retry on a separate thread so the dispatcher thread isn't blocked
            # by sleeps.
            if requests_to_retry:
                self._start_retry_thread(
                    "Thread-RetryModAcks",
                    functools.partial(self._retry_modacks, requests_to_retry),
                )

    def _retry_modacks(self, requests_to_retry):
        retry_delay_gen = exponential_sleep_generator(
            initial=_MIN_EXACTLY_ONCE_DELIVERY_ACK_MODACK_RETRY_DURATION_SECS,
            maximum=_MAX_EXACTLY_ONCE_DELIVERY_ACK_MODACK_RETRY_DURATION_SECS,
        )
        while requests_to_retry:
            time_to_wait = next(retry_delay_gen)
            _LOGGER.debug(
                "Retrying {len(requests_to_retry)} modack(s) after delay of "
                + str(time_to_wait)
                + " seconds"
            )
            time.sleep(time_to_wait)

            ack_reqs_dict = {req.ack_id: req for req in requests_to_retry}
            requests_completed, requests_to_retry = self._manager.send_unary_modack(
                modify_deadline_ack_ids=[req.ack_id for req in requests_to_retry],
                modify_deadline_seconds=[req.seconds for req in requests_to_retry],
                ack_reqs_dict=ack_reqs_dict,
            )

    def nack(self, items: Sequence[requests.NackRequest]) -> None:
        """Explicitly deny receipt of messages.

        Args:
            items: The items to deny.
        """
        self.modify_ack_deadline(
            [
                requests.ModAckRequest(
                    ack_id=item.ack_id, seconds=0, future=item.future
                )
                for item in items
            ]
        )
        self.drop(
            [
                requests.DropRequest(
                    ack_id=item.ack_id,
                    byte_size=item.byte_size,
                    ordering_key=item.ordering_key,
                )
                for item in items
            ]
        )
