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

from typing import Mapping
from urllib.parse import urlencode

from google.cloud.pubsublite.types import Partition, TopicPath, SubscriptionPath

_PARAMS_HEADER = "x-goog-request-params"


def topic_routing_metadata(topic: TopicPath, partition: Partition) -> Mapping[str, str]:
    encoded = urlencode({"partition": str(partition.value), "topic": str(topic)})
    return {_PARAMS_HEADER: encoded}


def subscription_routing_metadata(
    subscription: SubscriptionPath, partition: Partition
) -> Mapping[str, str]:
    encoded = urlencode(
        {"partition": str(partition.value), "subscription": str(subscription)}
    )
    return {_PARAMS_HEADER: encoded}
