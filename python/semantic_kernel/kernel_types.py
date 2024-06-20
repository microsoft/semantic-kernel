# Copyright (c) Microsoft. All rights reserved.

from typing import TypeVar, Union

from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

AI_SERVICE_CLIENT_TYPE = TypeVar("AI_SERVICE_CLIENT_TYPE", bound=AIServiceClientBase)

T = TypeVar("T")
OneOrMany = Union[T, list[T]]
OptionalOneOrMany = Union[None, T, list[T]]
