# Copyright (c) Microsoft. All rights reserved.

from typing import TypeVar

from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

AI_SERVICE_CLIENT_TYPE = TypeVar("AI_SERVICE_CLIENT_TYPE", bound=AIServiceClientBase)
