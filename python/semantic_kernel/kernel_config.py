# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Type, TypeVar, Union

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.reliability.pass_through_without_retry import (
    PassThroughWithoutRetry,
)
from semantic_kernel.reliability.retry_mechanism import RetryMechanism

if TYPE_CHECKING:
    from semantic_kernel.kernel_base import KernelBase


T = TypeVar("T")


class KernelConfig:
    def __init__(self) -> None:
        self._text_completion_services: Dict[
            str, Callable[["KernelBase"], TextCompletionClientBase]
        ] = {}
        self._chat_services: Dict[
            str, Callable[["KernelBase"], ChatCompletionClientBase]
        ] = {}
        self._text_embedding_generation_services: Dict[
            str, Callable[["KernelBase"], EmbeddingGeneratorBase]
        ] = {}

        self._default_text_completion_service: Optional[str] = None
        self._default_chat_service: Optional[str] = None
        self._default_text_embedding_generation_service: Optional[str] = None

        self._retry_mechanism: RetryMechanism = PassThroughWithoutRetry()

    def get_ai_service(
        self, type: Type[T], service_id: Optional[str] = None
    ) -> Callable[["KernelBase"], T]:
        matching_type = {}
        if type == TextCompletionClientBase:
            service_id = service_id or self._default_text_completion_service
            matching_type = self._text_completion_services
        elif type == ChatCompletionClientBase:
            service_id = service_id or self._default_chat_service
            matching_type = self._chat_services
        elif type == EmbeddingGeneratorBase:
            service_id = service_id or self._default_text_embedding_generation_service
            matching_type = self._text_embedding_generation_services
        else:
            raise ValueError(f"Unknown AI service type: {type.__name__}")

        if service_id not in matching_type:
            raise ValueError(
                f"{type.__name__} service with service_id '{service_id}' not found"
            )

        return matching_type[service_id]

    def all_text_completion_services(self) -> List[str]:
        return list(self._text_completion_services.keys())

    def all_chat_services(self) -> List[str]:
        return list(self._chat_services.keys())

    def all_text_embedding_generation_services(self) -> List[str]:
        return list(self._text_embedding_generation_services.keys())

    def add_text_completion_service(
        self,
        service_id: str,
        service: Union[
            TextCompletionClientBase, Callable[["KernelBase"], TextCompletionClientBase]
        ],
        overwrite: bool = True,
    ) -> "KernelConfig":
        if not service_id:
            raise ValueError("service_id must be a non-empty string")
        if not overwrite and service_id in self._text_completion_services:
            raise ValueError(
                f"Text service with service_id '{service_id}' already exists"
            )

        self._text_completion_services[service_id] = (
            service if isinstance(service, Callable) else lambda _: service
        )
        if self._default_text_completion_service is None:
            self._default_text_completion_service = service_id

        return self

    def add_chat_service(
        self,
        service_id: str,
        service: Union[
            ChatCompletionClientBase, Callable[["KernelBase"], ChatCompletionClientBase]
        ],
        overwrite: bool = True,
    ) -> "KernelConfig":
        if not service_id:
            raise ValueError("service_id must be a non-empty string")
        if not overwrite and service_id in self._chat_services:
            raise ValueError(
                f"Chat service with service_id '{service_id}' already exists"
            )

        self._chat_services[service_id] = (
            service if isinstance(service, Callable) else lambda _: service
        )
        if self._default_chat_service is None:
            self._default_chat_service = service_id

        if isinstance(service, TextCompletionClientBase):
            self.add_text_completion_service(service_id, service)
            if self._default_text_completion_service is None:
                self._default_text_completion_service = service_id

        return self

    def add_text_embedding_generation_service(
        self,
        service_id: str,
        service: Union[
            EmbeddingGeneratorBase, Callable[["KernelBase"], EmbeddingGeneratorBase]
        ],
        overwrite: bool = False,
    ) -> "KernelConfig":
        if not service_id:
            raise ValueError("service_id must be a non-empty string")
        if not overwrite and service_id in self._text_embedding_generation_services:
            raise ValueError(
                f"Embedding service with service_id '{service_id}' already exists"
            )

        self._text_embedding_generation_services[service_id] = (
            service if isinstance(service, Callable) else lambda _: service
        )
        if self._default_text_embedding_generation_service is None:
            self._default_text_embedding_generation_service = service_id

        return self

    # TODO: look harder at retry stuff

    def set_default_text_completion_service(self, service_id: str) -> "KernelConfig":
        if service_id not in self._text_completion_services:
            raise ValueError(
                f"AI service with service_id '{service_id}' does not exist"
            )

        self._default_text_completion_service = service_id
        return self

    def set_default_chat_service(self, service_id: str) -> "KernelConfig":
        if service_id not in self._chat_services:
            raise ValueError(
                f"AI service with service_id '{service_id}' does not exist"
            )

        self._default_chat_service = service_id
        return self

    def set_default_text_embedding_generation_service(
        self, service_id: str
    ) -> "KernelConfig":
        if service_id not in self._text_embedding_generation_services:
            raise ValueError(
                f"AI service with service_id '{service_id}' does not exist"
            )

        self._default_text_embedding_generation_service = service_id
        return self

    def get_text_completion_service_service_id(
        self, service_id: Optional[str] = None
    ) -> str:
        if service_id is None or service_id not in self._text_completion_services:
            if self._default_text_completion_service is None:
                raise ValueError("No default text service is set")
            return self._default_text_completion_service

        return service_id

    def get_chat_service_service_id(self, service_id: Optional[str] = None) -> str:
        if service_id is None or service_id not in self._chat_services:
            if self._default_chat_service is None:
                raise ValueError("No default chat service is set")
            return self._default_chat_service

        return service_id

    def get_text_embedding_generation_service_id(
        self, service_id: Optional[str] = None
    ) -> str:
        if (
            service_id is None
            or service_id not in self._text_embedding_generation_services
        ):
            if self._default_text_embedding_generation_service is None:
                raise ValueError("No default embedding service is set")
            return self._default_text_embedding_generation_service

        return service_id

    def remove_text_completion_service(self, service_id: str) -> "KernelConfig":
        if service_id not in self._text_completion_services:
            raise ValueError(
                f"AI service with service_id '{service_id}' does not exist"
            )

        del self._text_completion_services[service_id]
        if self._default_text_completion_service == service_id:
            self._default_text_completion_service = next(
                iter(self._text_completion_services), None
            )
        return self

    def remove_chat_service(self, service_id: str) -> "KernelConfig":
        if service_id not in self._chat_services:
            raise ValueError(
                f"AI service with service_id '{service_id}' does not exist"
            )

        del self._chat_services[service_id]
        if self._default_chat_service == service_id:
            self._default_chat_service = next(iter(self._chat_services), None)
        return self

    def remove_text_embedding_generation_service(
        self, service_id: str
    ) -> "KernelConfig":
        if service_id not in self._text_embedding_generation_services:
            raise ValueError(
                f"AI service with service_id '{service_id}' does not exist"
            )

        del self._text_embedding_generation_services[service_id]
        if self._default_text_embedding_generation_service == service_id:
            self._default_text_embedding_generation_service = next(
                iter(self._text_embedding_generation_services), None
            )
        return self

    def clear_all_text_completion_services(self) -> "KernelConfig":
        self._text_completion_services = {}
        self._default_text_completion_service = None
        return self

    def clear_all_chat_services(self) -> "KernelConfig":
        self._chat_services = {}
        self._default_chat_service = None
        return self

    def clear_all_text_embedding_generation_services(self) -> "KernelConfig":
        self._text_embedding_generation_services = {}
        self._default_text_embedding_generation_service = None
        return self

    def clear_all_services(self) -> "KernelConfig":
        self._text_completion_services = {}
        self._chat_services = {}
        self._text_embedding_generation_services = {}

        self._default_text_completion_service = None
        self._default_chat_service = None
        self._default_text_embedding_generation_service = None

        return self
