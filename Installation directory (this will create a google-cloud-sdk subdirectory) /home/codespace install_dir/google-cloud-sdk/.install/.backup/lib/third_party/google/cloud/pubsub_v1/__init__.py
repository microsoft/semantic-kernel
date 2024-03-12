# Copyright 2017, Google LLC All rights reserved.
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

from __future__ import absolute_import

from google.cloud.pubsub_v1 import types
from google.cloud.pubsub_v1 import publisher
from google.cloud.pubsub_v1 import subscriber
from google.pubsub_v1.services import schema_service


class PublisherClient(publisher.Client):
    __doc__ = publisher.Client.__doc__


class SubscriberClient(subscriber.Client):
    __doc__ = subscriber.Client.__doc__


class SchemaServiceClient(schema_service.client.SchemaServiceClient):
    __doc__ = schema_service.client.SchemaServiceClient.__doc__


__all__ = ("types", "PublisherClient", "SubscriberClient", "SchemaServiceClient")
