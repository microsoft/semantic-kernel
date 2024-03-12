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

from __future__ import division

import collections
import functools
import itertools
import logging
import threading
import typing
from typing import Any, Dict, Callable, Iterable, List, Optional, Set, Tuple
import uuid

import grpc  # type: ignore

from google.api_core import bidi
from google.api_core import exceptions
from google.cloud.pubsub_v1 import types
from google.cloud.pubsub_v1.subscriber._protocol import dispatcher
from google.cloud.pubsub_v1.subscriber._protocol import heartbeater
from google.cloud.pubsub_v1.subscriber._protocol import histogram
from google.cloud.pubsub_v1.subscriber._protocol import leaser
from google.cloud.pubsub_v1.subscriber._protocol import messages_on_hold
from google.cloud.pubsub_v1.subscriber._protocol import requests
from google.cloud.pubsub_v1.subscriber.exceptions import (
    AcknowledgeError,
    AcknowledgeStatus,
)
import google.cloud.pubsub_v1.subscriber.message
from google.cloud.pubsub_v1.subscriber import futures
from google.cloud.pubsub_v1.subscriber.scheduler import ThreadScheduler
from google.pubsub_v1 import types as gapic_types
from google.rpc.error_details_pb2 import ErrorInfo  # type: ignore
from google.rpc import code_pb2  # type: ignore
from google.rpc import status_pb2

if typing.TYPE_CHECKING:  # pragma: NO COVER
    from google.cloud.pubsub_v1 import subscriber


_LOGGER = logging.getLogger(__name__)
_REGULAR_SHUTDOWN_THREAD_NAME = "Thread-RegularStreamShutdown"
_RPC_ERROR_THREAD_NAME = "Thread-OnRpcTerminated"
_RETRYABLE_STREAM_ERRORS = (
    exceptions.DeadlineExceeded,
    exceptions.ServiceUnavailable,
    exceptions.InternalServerError,
    exceptions.Unknown,
    exceptions.GatewayTimeout,
    exceptions.Aborted,
)
_TERMINATING_STREAM_ERRORS = (exceptions.Cancelled,)
_MAX_LOAD = 1.0
"""The load threshold above which to pause the incoming message stream."""

_RESUME_THRESHOLD = 0.8
"""The load threshold below which to resume the incoming message stream."""

_MIN_ACK_DEADLINE_SECS_WHEN_EXACTLY_ONCE_ENABLED = 60
"""The minimum ack_deadline, in seconds, for when exactly_once is enabled for
a subscription. We do this to reduce premature ack expiration.
"""

_DEFAULT_STREAM_ACK_DEADLINE: float = 60
"""The default stream ack deadline in seconds."""

_MAX_STREAM_ACK_DEADLINE: float = 600
"""The maximum stream ack deadline in seconds."""

_MIN_STREAM_ACK_DEADLINE: float = 10
"""The minimum stream ack deadline in seconds."""

_EXACTLY_ONCE_DELIVERY_TEMPORARY_RETRY_ERRORS = {
    code_pb2.DEADLINE_EXCEEDED,
    code_pb2.RESOURCE_EXHAUSTED,
    code_pb2.ABORTED,
    code_pb2.INTERNAL,
    code_pb2.UNAVAILABLE,
}


def _wrap_as_exception(maybe_exception: Any) -> BaseException:
    """Wrap an object as a Python exception, if needed.

    Args:
        maybe_exception: The object to wrap, usually a gRPC exception class.

    Returns:
         The argument itself if an instance of ``BaseException``, otherwise
         the argument represented as an instance of ``Exception`` (sub)class.
    """
    if isinstance(maybe_exception, grpc.RpcError):
        return exceptions.from_grpc_error(maybe_exception)
    elif isinstance(maybe_exception, BaseException):
        return maybe_exception

    return Exception(maybe_exception)


def _wrap_callback_errors(
    callback: Callable[["google.cloud.pubsub_v1.subscriber.message.Message"], Any],
    on_callback_error: Callable[[Exception], Any],
    message: "google.cloud.pubsub_v1.subscriber.message.Message",
):
    """Wraps a user callback so that if an exception occurs the message is
    nacked.

    Args:
        callback: The user callback.
        message: The Pub/Sub message.
    """
    try:
        callback(message)
    except Exception as exc:
        # Note: the likelihood of this failing is extremely low. This just adds
        # a message to a queue, so if this doesn't work the world is in an
        # unrecoverable state and this thread should just bail.
        _LOGGER.exception(
            "Top-level exception occurred in callback while processing a message"
        )
        message.nack()
        on_callback_error(exc)


def _get_status(
    exc: exceptions.GoogleAPICallError,
) -> Optional["status_pb2.Status"]:
    if not exc.response:
        _LOGGER.debug("No response obj in errored RPC call.")
        return None
    if exc.response.trailing_metadata() is None:
        return None
    for key, value in exc.response.trailing_metadata():
        if key == GRPC_DETAILS_METADATA_KEY:
            rich_status = status_pb2.Status.FromString(value)
            if exc.response.code().value[0] != rich_status.code:
                _LOGGER.debug("ValueError when parsing ErrorInfo.", exc_info=True)
                return None
            if exc.response.details() != rich_status.message:
                _LOGGER.debug("ValueError when parsing ErrorInfo.", exc_info=True)
                return None
            return rich_status
    return None


def _get_ack_errors(
    exc: exceptions.GoogleAPICallError,
) -> Optional[Dict[str, str]]:
    status = _get_status(exc)
    if not status:
        _LOGGER.debug("Unable to get status of errored RPC.")
        return None
    for detail in status.details:
        info = ErrorInfo()
        if not (detail.Is(ErrorInfo.DESCRIPTOR) and detail.Unpack(info)):
            _LOGGER.debug("Unable to unpack ErrorInfo.")
            return None
        return info.metadata
    return None


def _process_requests(
    error_status: Optional["status_pb2.Status"],
    ack_reqs_dict: Dict[str, requests.AckRequest],
    errors_dict: Optional[Dict[str, str]],
):
    """Process requests when exactly-once delivery is enabled by referring to
    error_status and errors_dict.

    The errors returned by the server in as `error_status` or in `errors_dict`
    are used to complete the request futures in `ack_reqs_dict` (with a success
    or exception) or to return requests for further retries.
    """
    requests_completed = []
    requests_to_retry = []
    for ack_id in ack_reqs_dict:
        # Handle special errors returned for ack/modack RPCs via the ErrorInfo
        # sidecar metadata when exactly-once delivery is enabled.
        if errors_dict and ack_id in errors_dict:
            exactly_once_error = errors_dict[ack_id]
            if exactly_once_error.startswith("TRANSIENT_"):
                requests_to_retry.append(ack_reqs_dict[ack_id])
            else:
                if exactly_once_error == "PERMANENT_FAILURE_INVALID_ACK_ID":
                    exc = AcknowledgeError(AcknowledgeStatus.INVALID_ACK_ID, info=None)
                else:
                    exc = AcknowledgeError(AcknowledgeStatus.OTHER, exactly_once_error)
                future = ack_reqs_dict[ack_id].future
                if future is not None:
                    future.set_exception(exc)
                requests_completed.append(ack_reqs_dict[ack_id])
        # Temporary GRPC errors are retried
        elif (
            error_status
            and error_status.code in _EXACTLY_ONCE_DELIVERY_TEMPORARY_RETRY_ERRORS
        ):
            requests_to_retry.append(ack_reqs_dict[ack_id])
        # Other GRPC errors are NOT retried
        elif error_status:
            if error_status.code == code_pb2.PERMISSION_DENIED:
                exc = AcknowledgeError(AcknowledgeStatus.PERMISSION_DENIED, info=None)
            elif error_status.code == code_pb2.FAILED_PRECONDITION:
                exc = AcknowledgeError(AcknowledgeStatus.FAILED_PRECONDITION, info=None)
            else:
                exc = AcknowledgeError(AcknowledgeStatus.OTHER, str(error_status))
            future = ack_reqs_dict[ack_id].future
            if future is not None:
                future.set_exception(exc)
            requests_completed.append(ack_reqs_dict[ack_id])
        # Since no error occurred, requests with futures are completed successfully.
        elif ack_reqs_dict[ack_id].future:
            future = ack_reqs_dict[ack_id].future
            # success
            assert future is not None
            future.set_result(AcknowledgeStatus.SUCCESS)
            requests_completed.append(ack_reqs_dict[ack_id])
        # All other requests are considered completed.
        else:
            requests_completed.append(ack_reqs_dict[ack_id])

    return requests_completed, requests_to_retry


class StreamingPullManager(object):
    """The streaming pull manager coordinates pulling messages from Pub/Sub,
    leasing them, and scheduling them to be processed.

    Args:
        client:
            The subscriber client used to create this instance.
        subscription:
            The name of the subscription. The canonical format for this is
            ``projects/{project}/subscriptions/{subscription}``.
        flow_control:
            The flow control settings.
        scheduler:
            The scheduler to use to process messages. If not provided, a thread
            pool-based scheduler will be used.
        use_legacy_flow_control:
            If set to ``True``, flow control at the Cloud Pub/Sub server is disabled,
            though client-side flow control is still enabled. If set to ``False``
            (default), both server-side and client-side flow control are enabled.
        await_callbacks_on_shutdown:
            If ``True``, the shutdown thread will wait until all scheduler threads
            terminate and only then proceed with shutting down the remaining running
            helper threads.

            If ``False`` (default), the shutdown thread will shut the scheduler down,
            but it will not wait for the currently executing scheduler threads to
            terminate.

            This setting affects when the on close callbacks get invoked, and
            consequently, when the StreamingPullFuture associated with the stream gets
            resolved.
    """

    def __init__(
        self,
        client: "subscriber.Client",
        subscription: str,
        flow_control: types.FlowControl = types.FlowControl(),
        scheduler: ThreadScheduler = None,
        use_legacy_flow_control: bool = False,
        await_callbacks_on_shutdown: bool = False,
    ):
        self._client = client
        self._subscription = subscription
        self._exactly_once_enabled = False
        self._flow_control = flow_control
        self._use_legacy_flow_control = use_legacy_flow_control
        self._await_callbacks_on_shutdown = await_callbacks_on_shutdown
        self._ack_histogram = histogram.Histogram()
        self._last_histogram_size = 0
        self._stream_metadata = [
            ["x-goog-request-params", "subscription=" + subscription]
        ]

        # If max_duration_per_lease_extension is the default
        # we set the stream_ack_deadline to the default of 60
        if self._flow_control.max_duration_per_lease_extension == 0:
            self._stream_ack_deadline = _DEFAULT_STREAM_ACK_DEADLINE
        # We will not be able to extend more than the default minimum
        elif (
            self._flow_control.max_duration_per_lease_extension
            < _MIN_STREAM_ACK_DEADLINE
        ):
            self._stream_ack_deadline = _MIN_STREAM_ACK_DEADLINE
        # Will not be able to extend past the max
        elif (
            self._flow_control.max_duration_per_lease_extension
            > _MAX_STREAM_ACK_DEADLINE
        ):
            self._stream_ack_deadline = _MAX_STREAM_ACK_DEADLINE
        else:
            self._stream_ack_deadline = (
                self._flow_control.max_duration_per_lease_extension
            )

        self._ack_deadline = max(
            min(
                self._flow_control.min_duration_per_lease_extension,
                histogram.MAX_ACK_DEADLINE,
            ),
            histogram.MIN_ACK_DEADLINE,
        )

        self._rpc: Optional[bidi.ResumableBidiRpc] = None
        self._callback: Optional[functools.partial] = None
        self._closing = threading.Lock()
        self._closed = False
        self._close_callbacks: List[Callable[["StreamingPullManager", Any], Any]] = []
        # Guarded by self._exactly_once_enabled_lock
        self._send_new_ack_deadline = False

        # A shutdown thread is created on intentional shutdown.
        self._regular_shutdown_thread: Optional[threading.Thread] = None

        # Generate a random client id tied to this object. All streaming pull
        # connections (initial and re-connects) will then use the same client
        # id. Doing so lets the server establish affinity even across stream
        # disconncetions.
        self._client_id = str(uuid.uuid4())

        if scheduler is None:
            self._scheduler: Optional[ThreadScheduler] = ThreadScheduler()
        else:
            self._scheduler = scheduler

        # A collection for the messages that have been received from the server,
        # but not yet sent to the user callback.
        self._messages_on_hold = messages_on_hold.MessagesOnHold()

        # The total number of bytes consumed by the messages currently on hold
        self._on_hold_bytes = 0

        # A lock ensuring that pausing / resuming the consumer are both atomic
        # operations that cannot be executed concurrently. Needed for properly
        # syncing these operations with the current leaser load. Additionally,
        # the lock is used to protect modifications of internal data that
        # affects the load computation, i.e. the count and size of the messages
        # currently on hold.
        self._pause_resume_lock = threading.Lock()

        # A lock guarding the self._exactly_once_enabled variable. We may also
        # acquire the self._ack_deadline_lock while this lock is held, but not
        # the reverse. So, we maintain a simple ordering of these two locks to
        # prevent deadlocks.
        self._exactly_once_enabled_lock = threading.Lock()

        # A lock protecting the current ACK deadline used in the lease management. This
        # value can be potentially updated both by the leaser thread and by the message
        # consumer thread when invoking the internal _on_response() callback.
        self._ack_deadline_lock = threading.Lock()

        # The threads created in ``.open()``.
        self._dispatcher: Optional[dispatcher.Dispatcher] = None
        self._leaser: Optional[leaser.Leaser] = None
        self._consumer: Optional[bidi.BackgroundConsumer] = None
        self._heartbeater: Optional[heartbeater.Heartbeater] = None

    @property
    def is_active(self) -> bool:
        """``True`` if this manager is actively streaming.

        Note that ``False`` does not indicate this is complete shut down,
        just that it stopped getting new messages.
        """
        return self._consumer is not None and self._consumer.is_active

    @property
    def flow_control(self) -> types.FlowControl:
        """The active flow control settings."""
        return self._flow_control

    @property
    def dispatcher(self) -> Optional[dispatcher.Dispatcher]:
        """The dispatcher helper."""
        return self._dispatcher

    @property
    def leaser(self) -> Optional[leaser.Leaser]:
        """The leaser helper."""
        return self._leaser

    @property
    def ack_histogram(self) -> histogram.Histogram:
        """The histogram tracking time-to-acknowledge."""
        return self._ack_histogram

    @property
    def ack_deadline(self) -> float:
        """Return the current ACK deadline based on historical data without updating it.

        Returns:
            The ack deadline.
        """
        return self._obtain_ack_deadline(maybe_update=False)

    def _obtain_ack_deadline(self, maybe_update: bool) -> float:
        """The actual `ack_deadline` implementation.

        This method is "sticky". It will only perform the computations to check on the
        right ACK deadline if explicitly requested AND if the histogram with past
        time-to-ack data has gained a significant amount of new information.

        Args:
            maybe_update:
                If ``True``, also update the current ACK deadline before returning it if
                enough new ACK data has been gathered.

        Returns:
            The current ACK deadline in seconds to use.
        """
        with self._ack_deadline_lock:
            if not maybe_update:
                return self._ack_deadline

            target_size = min(
                self._last_histogram_size * 2, self._last_histogram_size + 100
            )
            hist_size = len(self.ack_histogram)

            if hist_size > target_size:
                self._last_histogram_size = hist_size
                self._ack_deadline = self.ack_histogram.percentile(percent=99)

            if self.flow_control.max_duration_per_lease_extension > 0:
                # The setting in flow control could be too low, adjust if needed.
                flow_control_setting = max(
                    self.flow_control.max_duration_per_lease_extension,
                    histogram.MIN_ACK_DEADLINE,
                )
                self._ack_deadline = min(self._ack_deadline, flow_control_setting)

            # If the user explicitly sets a min ack_deadline, respect it.
            if self.flow_control.min_duration_per_lease_extension > 0:
                # The setting in flow control could be too high, adjust if needed.
                flow_control_setting = min(
                    self.flow_control.min_duration_per_lease_extension,
                    histogram.MAX_ACK_DEADLINE,
                )
                self._ack_deadline = max(self._ack_deadline, flow_control_setting)
            elif self._exactly_once_enabled:
                # Higher minimum ack_deadline for subscriptions with
                # exactly-once delivery enabled.
                self._ack_deadline = max(
                    self._ack_deadline, _MIN_ACK_DEADLINE_SECS_WHEN_EXACTLY_ONCE_ENABLED
                )
            # If we have updated the ack_deadline and it is longer than the stream_ack_deadline
            # set the stream_ack_deadline to the new ack_deadline.
            if self._ack_deadline > self._stream_ack_deadline:
                self._stream_ack_deadline = self._ack_deadline
            return self._ack_deadline

    @property
    def load(self) -> float:
        """Return the current load.

        The load is represented as a float, where 1.0 represents having
        hit one of the flow control limits, and values between 0.0 and 1.0
        represent how close we are to them. (0.5 means we have exactly half
        of what the flow control setting allows, for example.)

        There are (currently) two flow control settings; this property
        computes how close the manager is to each of them, and returns
        whichever value is higher. (It does not matter that we have lots of
        running room on setting A if setting B is over.)

        Returns:
            The load value.
        """
        if self._leaser is None:
            return 0.0

        # Messages that are temporarily put on hold are not being delivered to
        # user's callbacks, thus they should not contribute to the flow control
        # load calculation.
        # However, since these messages must still be lease-managed to avoid
        # unnecessary ACK deadline expirations, their count and total size must
        # be subtracted from the leaser's values.
        return max(
            [
                (self._leaser.message_count - self._messages_on_hold.size)
                / self._flow_control.max_messages,
                (self._leaser.bytes - self._on_hold_bytes)
                / self._flow_control.max_bytes,
            ]
        )

    def add_close_callback(
        self, callback: Callable[["StreamingPullManager", Any], Any]
    ) -> None:
        """Schedules a callable when the manager closes.

        Args:
            The method to call.
        """
        self._close_callbacks.append(callback)

    def activate_ordering_keys(self, ordering_keys: Iterable[str]) -> None:
        """Send the next message in the queue for each of the passed-in
        ordering keys, if they exist. Clean up state for keys that no longer
        have any queued messages.

        Since the load went down by one message, it's probably safe to send the
        user another message for the same key. Since the released message may be
        bigger than the previous one, this may increase the load above the maximum.
        This decision is by design because it simplifies MessagesOnHold.

        Args:
            ordering_keys:
                A sequence of ordering keys to activate. May be empty.
        """
        with self._pause_resume_lock:
            if self._scheduler is None:
                return  # We are shutting down, don't try to dispatch any more messages.

            self._messages_on_hold.activate_ordering_keys(
                ordering_keys, self._schedule_message_on_hold
            )

    def maybe_pause_consumer(self) -> None:
        """Check the current load and pause the consumer if needed."""
        with self._pause_resume_lock:
            if self.load >= _MAX_LOAD:
                if self._consumer is not None and not self._consumer.is_paused:
                    _LOGGER.debug(
                        "Message backlog over load at %.2f, pausing.", self.load
                    )
                    self._consumer.pause()

    def maybe_resume_consumer(self) -> None:
        """Check the load and held messages and resume the consumer if needed.

        If there are messages held internally, release those messages before
        resuming the consumer. That will avoid leaser overload.
        """
        with self._pause_resume_lock:
            # If we have been paused by flow control, check and see if we are
            # back within our limits.
            #
            # In order to not thrash too much, require us to have passed below
            # the resume threshold (80% by default) of each flow control setting
            # before restarting.
            if self._consumer is None or not self._consumer.is_paused:
                return

            _LOGGER.debug("Current load: %.2f", self.load)

            # Before maybe resuming the background consumer, release any messages
            # currently on hold, if the current load allows for it.
            self._maybe_release_messages()

            if self.load < _RESUME_THRESHOLD:
                _LOGGER.debug("Current load is %.2f, resuming consumer.", self.load)
                self._consumer.resume()
            else:
                _LOGGER.debug("Did not resume, current load is %.2f.", self.load)

    def _maybe_release_messages(self) -> None:
        """Release (some of) the held messages if the current load allows for it.

        The method tries to release as many messages as the current leaser load
        would allow. Each released message is added to the lease management,
        and the user callback is scheduled for it.

        If there are currently no messages on hold, or if the leaser is
        already overloaded, this method is effectively a no-op.

        The method assumes the caller has acquired the ``_pause_resume_lock``.
        """
        released_ack_ids = []
        while self.load < _MAX_LOAD:
            msg = self._messages_on_hold.get()
            if not msg:
                break

            self._schedule_message_on_hold(msg)
            released_ack_ids.append(msg.ack_id)

        assert self._leaser is not None
        self._leaser.start_lease_expiry_timer(released_ack_ids)

    def _schedule_message_on_hold(
        self, msg: "google.cloud.pubsub_v1.subscriber.message.Message"
    ):
        """Schedule a message on hold to be sent to the user and change on-hold-bytes.

        The method assumes the caller has acquired the ``_pause_resume_lock``.

        Args:
            msg: The message to schedule to be sent to the user.
        """
        assert msg, "Message must not be None."

        # On-hold bytes goes down, increasing load.
        self._on_hold_bytes -= msg.size

        if self._on_hold_bytes < 0:
            _LOGGER.warning(
                "On hold bytes was unexpectedly negative: %s", self._on_hold_bytes
            )
            self._on_hold_bytes = 0

        _LOGGER.debug(
            "Released held message, scheduling callback for it, "
            "still on hold %s (bytes %s).",
            self._messages_on_hold.size,
            self._on_hold_bytes,
        )
        assert self._scheduler is not None
        assert self._callback is not None
        self._scheduler.schedule(self._callback, msg)

    def send_unary_ack(
        self, ack_ids, ack_reqs_dict
    ) -> Tuple[List[requests.AckRequest], List[requests.AckRequest]]:
        """Send a request using a separate unary request instead of over the stream.

        If a RetryError occurs, the manager shutdown is triggered, and the
        error is re-raised.
        """
        assert ack_ids
        assert len(ack_ids) == len(ack_reqs_dict)

        error_status = None
        ack_errors_dict = None
        try:
            self._client.acknowledge(subscription=self._subscription, ack_ids=ack_ids)
        except exceptions.GoogleAPICallError as exc:
            _LOGGER.debug(
                "Exception while sending unary RPC. This is typically "
                "non-fatal as stream requests are best-effort.",
                exc_info=True,
            )
            error_status = _get_status(exc)
            ack_errors_dict = _get_ack_errors(exc)
        except exceptions.RetryError as exc:
            exactly_once_delivery_enabled = self._exactly_once_delivery_enabled()
            # Makes sure to complete futures so they don't block forever.
            for req in ack_reqs_dict.values():
                # Futures may be present even with exactly-once delivery
                # disabled, in transition periods after the setting is changed on
                # the subscription.
                if req.future:
                    if exactly_once_delivery_enabled:
                        e = AcknowledgeError(
                            AcknowledgeStatus.OTHER, "RetryError while sending ack RPC."
                        )
                        req.future.set_exception(e)
                    else:
                        req.future.set_result(AcknowledgeStatus.SUCCESS)

            _LOGGER.debug(
                "RetryError while sending ack RPC. Waiting on a transient "
                "error resolution for too long, will now trigger shutdown.",
                exc_info=False,
            )
            # The underlying channel has been suffering from a retryable error
            # for too long, time to give up and shut the streaming pull down.
            self._on_rpc_done(exc)
            raise

        if self._exactly_once_delivery_enabled():
            requests_completed, requests_to_retry = _process_requests(
                error_status, ack_reqs_dict, ack_errors_dict
            )
        else:
            requests_completed = []
            requests_to_retry = []
            # When exactly-once delivery is NOT enabled, acks/modacks are considered
            # best-effort. So, they always succeed even if the RPC fails.
            for req in ack_reqs_dict.values():
                # Futures may be present even with exactly-once delivery
                # disabled, in transition periods after the setting is changed on
                # the subscription.
                if req.future:
                    req.future.set_result(AcknowledgeStatus.SUCCESS)
                requests_completed.append(req)

        return requests_completed, requests_to_retry

    def send_unary_modack(
        self,
        modify_deadline_ack_ids,
        modify_deadline_seconds,
        ack_reqs_dict,
        default_deadline=None,
    ) -> Tuple[List[requests.ModAckRequest], List[requests.ModAckRequest]]:
        """Send a request using a separate unary request instead of over the stream.

        If a RetryError occurs, the manager shutdown is triggered, and the
        error is re-raised.
        """
        assert modify_deadline_ack_ids
        # Either we have a generator or a single deadline.
        assert modify_deadline_seconds is None or default_deadline is None

        error_status = None
        modack_errors_dict = None
        try:
            if default_deadline is None:
                # Send ack_ids with the same deadline seconds together.
                deadline_to_ack_ids = collections.defaultdict(list)

                for n, ack_id in enumerate(modify_deadline_ack_ids):
                    deadline = modify_deadline_seconds[n]
                    deadline_to_ack_ids[deadline].append(ack_id)

                for deadline, ack_ids in deadline_to_ack_ids.items():
                    self._client.modify_ack_deadline(
                        subscription=self._subscription,
                        ack_ids=ack_ids,
                        ack_deadline_seconds=deadline,
                    )
            else:
                # We can send all requests with the default deadline.
                self._client.modify_ack_deadline(
                    subscription=self._subscription,
                    ack_ids=modify_deadline_ack_ids,
                    ack_deadline_seconds=default_deadline,
                )
        except exceptions.GoogleAPICallError as exc:
            _LOGGER.debug(
                "Exception while sending unary RPC. This is typically "
                "non-fatal as stream requests are best-effort.",
                exc_info=True,
            )
            error_status = _get_status(exc)
            modack_errors_dict = _get_ack_errors(exc)
        except exceptions.RetryError as exc:
            exactly_once_delivery_enabled = self._exactly_once_delivery_enabled()
            # Makes sure to complete futures so they don't block forever.
            for req in ack_reqs_dict.values():
                # Futures may be present even with exactly-once delivery
                # disabled, in transition periods after the setting is changed on
                # the subscription.
                if req.future:
                    if exactly_once_delivery_enabled:
                        e = AcknowledgeError(
                            AcknowledgeStatus.OTHER,
                            "RetryError while sending modack RPC.",
                        )
                        req.future.set_exception(e)
                    else:
                        req.future.set_result(AcknowledgeStatus.SUCCESS)

            _LOGGER.debug(
                "RetryError while sending modack RPC. Waiting on a transient "
                "error resolution for too long, will now trigger shutdown.",
                exc_info=False,
            )
            # The underlying channel has been suffering from a retryable error
            # for too long, time to give up and shut the streaming pull down.
            self._on_rpc_done(exc)
            raise

        if self._exactly_once_delivery_enabled():
            requests_completed, requests_to_retry = _process_requests(
                error_status, ack_reqs_dict, modack_errors_dict
            )
        else:
            requests_completed = []
            requests_to_retry = []
            # When exactly-once delivery is NOT enabled, acks/modacks are considered
            # best-effort. So, they always succeed even if the RPC fails.
            for req in ack_reqs_dict.values():
                # Futures may be present even with exactly-once delivery
                # disabled, in transition periods after the setting is changed on
                # the subscription.
                if req.future:
                    req.future.set_result(AcknowledgeStatus.SUCCESS)
                requests_completed.append(req)

        return requests_completed, requests_to_retry

    def heartbeat(self) -> bool:
        """Sends a heartbeat request over the streaming pull RPC.

        The request is empty by default, but may contain the current ack_deadline
        if the self._exactly_once_enabled flag has changed.

        Returns:
            If a heartbeat request has actually been sent.
        """
        if self._rpc is not None and self._rpc.is_active:
            send_new_ack_deadline = False
            with self._exactly_once_enabled_lock:
                send_new_ack_deadline = self._send_new_ack_deadline
                self._send_new_ack_deadline = False

            if send_new_ack_deadline:
                request = gapic_types.StreamingPullRequest(
                    stream_ack_deadline_seconds=self._stream_ack_deadline
                )
                _LOGGER.debug(
                    "Sending new ack_deadline of %d seconds.", self._stream_ack_deadline
                )
            else:
                request = gapic_types.StreamingPullRequest()

            self._rpc.send(request)
            return True

        return False

    def open(
        self,
        callback: Callable[["google.cloud.pubsub_v1.subscriber.message.Message"], Any],
        on_callback_error: Callable[[Exception], Any],
    ) -> None:
        """Begin consuming messages.

        Args:
            callback:
                A callback that will be called for each message received on the
                stream.
            on_callback_error:
                A callable that will be called if an exception is raised in
                the provided `callback`.
        """
        if self.is_active:
            raise ValueError("This manager is already open.")

        if self._closed:
            raise ValueError("This manager has been closed and can not be re-used.")

        self._callback = functools.partial(
            _wrap_callback_errors, callback, on_callback_error
        )

        # Create the RPC
        stream_ack_deadline_seconds = self._stream_ack_deadline

        get_initial_request = functools.partial(
            self._get_initial_request, stream_ack_deadline_seconds
        )
        self._rpc = bidi.ResumableBidiRpc(
            start_rpc=self._client.streaming_pull,
            initial_request=get_initial_request,
            should_recover=self._should_recover,
            should_terminate=self._should_terminate,
            metadata=self._stream_metadata,
            throttle_reopen=True,
        )
        self._rpc.add_done_callback(self._on_rpc_done)

        _LOGGER.debug(
            "Creating a stream, default ACK deadline set to {} seconds.".format(
                self._stream_ack_deadline
            )
        )

        # Create references to threads
        assert self._scheduler is not None
        scheduler_queue = self._scheduler.queue
        self._dispatcher = dispatcher.Dispatcher(self, scheduler_queue)
        self._consumer = bidi.BackgroundConsumer(self._rpc, self._on_response)
        self._leaser = leaser.Leaser(self)
        self._heartbeater = heartbeater.Heartbeater(self)

        # Start the thread to pass the requests.
        self._dispatcher.start()

        # Start consuming messages.
        self._consumer.start()

        # Start the lease maintainer thread.
        self._leaser.start()

        # Start the stream heartbeater thread.
        self._heartbeater.start()

    def close(self, reason: Any = None) -> None:
        """Stop consuming messages and shutdown all helper threads.

        This method is idempotent. Additional calls will have no effect.

        The method does not block, it delegates the shutdown operations to a background
        thread.

        Args:
            reason:
                The reason to close this. If ``None``, this is considered
                an "intentional" shutdown. This is passed to the callbacks
                specified via :meth:`add_close_callback`.
        """
        self._regular_shutdown_thread = threading.Thread(
            name=_REGULAR_SHUTDOWN_THREAD_NAME,
            daemon=True,
            target=self._shutdown,
            kwargs={"reason": reason},
        )
        self._regular_shutdown_thread.start()

    def _shutdown(self, reason: Any = None) -> None:
        """Run the actual shutdown sequence (stop the stream and all helper threads).

        Args:
            reason:
                The reason to close the stream. If ``None``, this is considered
                an "intentional" shutdown.
        """
        with self._closing:
            if self._closed:
                return

            # Stop consuming messages.
            if self.is_active:
                _LOGGER.debug("Stopping consumer.")
                assert self._consumer is not None
                self._consumer.stop()
            self._consumer = None

            # Shutdown all helper threads
            _LOGGER.debug("Stopping scheduler.")
            assert self._scheduler is not None
            dropped_messages = self._scheduler.shutdown(
                await_msg_callbacks=self._await_callbacks_on_shutdown
            )
            self._scheduler = None

            # Leaser and dispatcher reference each other through the shared
            # StreamingPullManager instance, i.e. "self", thus do not set their
            # references to None until both have been shut down.
            #
            # NOTE: Even if the dispatcher operates on an inactive leaser using
            # the latter's add() and remove() methods, these have no impact on
            # the stopped leaser (the leaser is never again re-started). Ditto
            # for the manager's maybe_resume_consumer() / maybe_pause_consumer(),
            # because the consumer gets shut down first.
            _LOGGER.debug("Stopping leaser.")
            assert self._leaser is not None
            self._leaser.stop()

            total = len(dropped_messages) + len(
                self._messages_on_hold._messages_on_hold
            )
            _LOGGER.debug(f"NACK-ing all not-yet-dispatched messages (total: {total}).")
            messages_to_nack = itertools.chain(
                dropped_messages, self._messages_on_hold._messages_on_hold
            )
            for msg in messages_to_nack:
                msg.nack()

            _LOGGER.debug("Stopping dispatcher.")
            assert self._dispatcher is not None
            self._dispatcher.stop()
            self._dispatcher = None
            # dispatcher terminated, OK to dispose the leaser reference now
            self._leaser = None

            _LOGGER.debug("Stopping heartbeater.")
            assert self._heartbeater is not None
            self._heartbeater.stop()
            self._heartbeater = None

            self._rpc = None
            self._closed = True
            _LOGGER.debug("Finished stopping manager.")

            for callback in self._close_callbacks:
                callback(self, reason)

    def _get_initial_request(
        self, stream_ack_deadline_seconds: int
    ) -> gapic_types.StreamingPullRequest:
        """Return the initial request for the RPC.

        This defines the initial request that must always be sent to Pub/Sub
        immediately upon opening the subscription.

        Args:
            stream_ack_deadline_seconds:
                The default message acknowledge deadline for the stream.

        Returns:
            A request suitable for being the first request on the stream (and not
            suitable for any other purpose).
        """
        # Put the request together.
        # We need to set streaming ack deadline, but it's not useful since we'll modack to send receipt
        # anyway. Set to some big-ish value in case we modack late.
        request = gapic_types.StreamingPullRequest(
            stream_ack_deadline_seconds=stream_ack_deadline_seconds,
            modify_deadline_ack_ids=[],
            modify_deadline_seconds=[],
            subscription=self._subscription,
            client_id=self._client_id,
            max_outstanding_messages=(
                0 if self._use_legacy_flow_control else self._flow_control.max_messages
            ),
            max_outstanding_bytes=(
                0 if self._use_legacy_flow_control else self._flow_control.max_bytes
            ),
        )

        # Return the initial request.
        return request

    def _send_lease_modacks(
        self, ack_ids: Iterable[str], ack_deadline: float, warn_on_invalid=True
    ) -> Set[str]:
        exactly_once_enabled = False
        with self._exactly_once_enabled_lock:
            exactly_once_enabled = self._exactly_once_enabled
        if exactly_once_enabled:
            items = [
                requests.ModAckRequest(ack_id, ack_deadline, futures.Future())
                for ack_id in ack_ids
            ]

            assert self._dispatcher is not None
            self._dispatcher.modify_ack_deadline(items, ack_deadline)

            expired_ack_ids = set()
            for req in items:
                try:
                    assert req.future is not None
                    req.future.result()
                except AcknowledgeError as ack_error:
                    if (
                        ack_error.error_code != AcknowledgeStatus.INVALID_ACK_ID
                        or warn_on_invalid
                    ):
                        _LOGGER.warning(
                            "AcknowledgeError when lease-modacking a message.",
                            exc_info=True,
                        )
                    if ack_error.error_code == AcknowledgeStatus.INVALID_ACK_ID:
                        expired_ack_ids.add(req.ack_id)
            return expired_ack_ids
        else:
            items = [
                requests.ModAckRequest(ack_id, self.ack_deadline, None)
                for ack_id in ack_ids
            ]
            assert self._dispatcher is not None
            self._dispatcher.modify_ack_deadline(items, ack_deadline)
            return set()

    def _exactly_once_delivery_enabled(self) -> bool:
        """Whether exactly-once delivery is enabled for the subscription."""
        with self._exactly_once_enabled_lock:
            return self._exactly_once_enabled

    def _on_response(self, response: gapic_types.StreamingPullResponse) -> None:
        """Process all received Pub/Sub messages.

        For each message, send a modified acknowledgment request to the
        server. This prevents expiration of the message due to buffering by
        gRPC or proxy/firewall. This makes the server and client expiration
        timer closer to each other thus preventing the message being
        redelivered multiple times.

        After the messages have all had their ack deadline updated, execute
        the callback for each message using the executor.
        """
        if response is None:
            _LOGGER.debug(
                "Response callback invoked with None, likely due to a "
                "transport shutdown."
            )
            return

        # IMPORTANT: Circumvent the wrapper class and operate on the raw underlying
        # protobuf message to significantly gain on attribute access performance.
        received_messages = response._pb.received_messages

        _LOGGER.debug(
            "Processing %s received message(s), currently on hold %s (bytes %s).",
            len(received_messages),
            self._messages_on_hold.size,
            self._on_hold_bytes,
        )

        with self._exactly_once_enabled_lock:
            if (
                response.subscription_properties.exactly_once_delivery_enabled
                != self._exactly_once_enabled
            ):
                self._exactly_once_enabled = (
                    response.subscription_properties.exactly_once_delivery_enabled
                )
                # Update ack_deadline, whose minimum depends on self._exactly_once_enabled
                # This method acquires the self._ack_deadline_lock lock.
                self._obtain_ack_deadline(maybe_update=True)
                self._send_new_ack_deadline = True

        # Immediately (i.e. without waiting for the auto lease management)
        # modack the messages we received, as this tells the server that we've
        # received them.
        ack_id_gen = (message.ack_id for message in received_messages)
        expired_ack_ids = self._send_lease_modacks(
            ack_id_gen, self.ack_deadline, warn_on_invalid=False
        )

        with self._pause_resume_lock:
            assert self._scheduler is not None
            assert self._leaser is not None

            for received_message in received_messages:
                if (
                    not self._exactly_once_delivery_enabled()
                    or received_message.ack_id not in expired_ack_ids
                ):
                    message = google.cloud.pubsub_v1.subscriber.message.Message(
                        received_message.message,
                        received_message.ack_id,
                        received_message.delivery_attempt,
                        self._scheduler.queue,
                        self._exactly_once_delivery_enabled,
                    )
                    self._messages_on_hold.put(message)
                    self._on_hold_bytes += message.size
                    req = requests.LeaseRequest(
                        ack_id=message.ack_id,
                        byte_size=message.size,
                        ordering_key=message.ordering_key,
                    )
                    self._leaser.add([req])

            self._maybe_release_messages()

        self.maybe_pause_consumer()

    def _should_recover(self, exception: BaseException) -> bool:
        """Determine if an error on the RPC stream should be recovered.

        If the exception is one of the retryable exceptions, this will signal
        to the consumer thread that it should "recover" from the failure.

        This will cause the stream to exit when it returns :data:`False`.

        Returns:
            Indicates if the caller should recover or shut down.
            Will be :data:`True` if the ``exception`` is "acceptable", i.e.
            in a list of retryable / idempotent exceptions.
        """
        exception = _wrap_as_exception(exception)
        # If this is in the list of idempotent exceptions, then we want to
        # recover.
        if isinstance(exception, _RETRYABLE_STREAM_ERRORS):
            _LOGGER.debug("Observed recoverable stream error %s", exception)
            return True
        _LOGGER.debug("Observed non-recoverable stream error %s", exception)
        return False

    def _should_terminate(self, exception: BaseException) -> bool:
        """Determine if an error on the RPC stream should be terminated.

        If the exception is one of the terminating exceptions, this will signal
        to the consumer thread that it should terminate.

        This will cause the stream to exit when it returns :data:`True`.

        Returns:
            Indicates if the caller should terminate or attempt recovery.
            Will be :data:`True` if the ``exception`` is "acceptable", i.e.
            in a list of terminating exceptions.
        """
        exception = _wrap_as_exception(exception)
        if isinstance(exception, _TERMINATING_STREAM_ERRORS):
            _LOGGER.debug("Observed terminating stream error %s", exception)
            return True
        _LOGGER.debug("Observed non-terminating stream error %s", exception)
        return False

    def _on_rpc_done(self, future: Any) -> None:
        """Triggered whenever the underlying RPC terminates without recovery.

        This is typically triggered from one of two threads: the background
        consumer thread (when calling ``recv()`` produces a non-recoverable
        error) or the grpc management thread (when cancelling the RPC).

        This method is *non-blocking*. It will start another thread to deal
        with shutting everything down. This is to prevent blocking in the
        background consumer and preventing it from being ``joined()``.
        """
        _LOGGER.debug("RPC termination has signaled streaming pull manager shutdown.")
        error = _wrap_as_exception(future)
        thread = threading.Thread(
            name=_RPC_ERROR_THREAD_NAME, target=self._shutdown, kwargs={"reason": error}
        )
        thread.daemon = True
        thread.start()
