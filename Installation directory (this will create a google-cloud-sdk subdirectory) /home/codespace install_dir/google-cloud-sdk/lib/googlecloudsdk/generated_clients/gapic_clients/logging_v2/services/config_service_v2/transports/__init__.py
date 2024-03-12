# -*- coding: utf-8 -*-
# Copyright 2023 Google LLC
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
#
from collections import OrderedDict
from typing import Dict, Type

from .base import ConfigServiceV2Transport
from .grpc import ConfigServiceV2GrpcTransport
from .grpc_asyncio import ConfigServiceV2GrpcAsyncIOTransport
from .rest import ConfigServiceV2RestTransport
from .rest import ConfigServiceV2RestInterceptor


# Compile a registry of transports.
_transport_registry = OrderedDict()  # type: Dict[str, Type[ConfigServiceV2Transport]]
_transport_registry['grpc'] = ConfigServiceV2GrpcTransport
_transport_registry['grpc_asyncio'] = ConfigServiceV2GrpcAsyncIOTransport
_transport_registry['rest'] = ConfigServiceV2RestTransport

__all__ = (
    'ConfigServiceV2Transport',
    'ConfigServiceV2GrpcTransport',
    'ConfigServiceV2GrpcAsyncIOTransport',
    'ConfigServiceV2RestTransport',
    'ConfigServiceV2RestInterceptor',
)
