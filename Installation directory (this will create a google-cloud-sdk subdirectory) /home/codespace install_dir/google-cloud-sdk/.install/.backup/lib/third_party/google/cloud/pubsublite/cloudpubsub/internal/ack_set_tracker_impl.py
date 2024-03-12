# Copyright 2020 Google LLC
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

from collections import deque
from typing import Optional

from google.api_core.exceptions import FailedPrecondition

from google.cloud.pubsublite.cloudpubsub.internal.sorted_list import SortedList
from google.cloud.pubsublite.cloudpubsub.internal.ack_set_tracker import AckSetTracker
from google.cloud.pubsublite.internal.wire.committer import Committer
from google.cloud.pubsublite_v1 import Cursor


class AckSetTrackerImpl(AckSetTracker):
    _committer: Committer

    _receipts: "deque[int]"
    _acks: SortedList[int]

    def __init__(self, committer: Committer):
        super().__init__()
        self._committer = committer
        self._receipts = deque()
        self._acks = SortedList()

    def track(self, offset: int):
        if len(self._receipts) > 0:
            last = self._receipts[0]
            if last >= offset:
                raise FailedPrecondition(
                    f"Tried to track message {offset} which is before last tracked message {last}."
                )
        self._receipts.append(offset)

    def ack(self, offset: int):
        self._acks.push(offset)
        prefix_acked_offset: Optional[int] = None
        while len(self._receipts) != 0 and not self._acks.empty():
            receipt = self._receipts.popleft()
            ack = self._acks.peek()
            if receipt == ack:
                prefix_acked_offset = receipt
                self._acks.pop()
                continue
            self._receipts.appendleft(receipt)
            break
        if prefix_acked_offset is None:
            return
        # Convert from last acked to first unacked.
        cursor = Cursor()
        cursor._pb.offset = prefix_acked_offset + 1
        self._committer.commit(cursor)

    async def clear_and_commit(self):
        self._receipts.clear()
        self._acks = SortedList()
        await self._committer.wait_until_empty()

    async def __aenter__(self):
        await self._committer.__aenter__()

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._committer.__aexit__(exc_type, exc_value, traceback)
