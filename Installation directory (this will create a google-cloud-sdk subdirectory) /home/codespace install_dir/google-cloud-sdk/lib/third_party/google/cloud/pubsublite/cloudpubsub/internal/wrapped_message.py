from concurrent import futures
import logging
from typing import NamedTuple, Callable

from google.cloud.pubsub_v1.subscriber.message import Message
from google.pubsub_v1 import PubsubMessage
from google.cloud.pubsub_v1.subscriber.exceptions import AcknowledgeStatus


class AckId(NamedTuple):
    generation: int
    offset: int

    def encode(self) -> str:
        return str(self.generation) + "," + str(self.offset)


_SUCCESS_FUTURE = futures.Future()
_SUCCESS_FUTURE.set_result(AcknowledgeStatus.SUCCESS)


class WrappedMessage(Message):
    _id: AckId
    _ack_handler: Callable[[AckId, bool], None]

    def __init__(
        self,
        pb: PubsubMessage.meta.pb,
        ack_id: AckId,
        ack_handler: Callable[[AckId, bool], None],
    ):
        super().__init__(pb, ack_id.encode(), 1, None)
        self._id = ack_id
        self._ack_handler = ack_handler

    def ack(self):
        self._ack_handler(self._id, True)

    def ack_with_response(self) -> "futures.Future":
        self._ack_handler(self._id, True)
        return _SUCCESS_FUTURE

    def nack(self):
        self._ack_handler(self._id, False)

    def nack_with_response(self) -> "futures.Future":
        self._ack_handler(self._id, False)
        return _SUCCESS_FUTURE

    def drop(self):
        logging.warning(
            "Likely incorrect call to drop() on Pub/Sub Lite message. Pub/Sub Lite does not support redelivery in this way."
        )

    def modify_ack_deadline(self, seconds: int):
        logging.warning(
            "Likely incorrect call to modify_ack_deadline() on Pub/Sub Lite message. Pub/Sub Lite does not support redelivery in this way."
        )

    def modify_ack_deadline_with_response(self, seconds: int) -> "futures.Future":
        logging.warning(
            "Likely incorrect call to modify_ack_deadline_with_response() on Pub/Sub Lite message. Pub/Sub Lite does not support redelivery in this way."
        )
        return _SUCCESS_FUTURE
