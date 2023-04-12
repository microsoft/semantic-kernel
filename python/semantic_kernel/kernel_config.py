# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Type, TypeVar, Union

from semantic_kernel.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.reliability.pass_through_without_retry import (
    PassThroughWithoutRetry,
)
from semantic_kernel.reliability.retry_mechanism import RetryMechanism

if TYPE_CHECKING:
    from semantic_kernel.kernel_base import KernelBase


T = TypeVar("T")


class KernelConfig:
    def __init__(self) -> None:
        self._text_backends: Dict[
            str, Callable[["KernelBase"], TextCompletionClientBase]
        ] = {}
        self._chat_backends: Dict[
            str, Callable[["KernelBase"], ChatCompletionClientBase]
        ] = {}
        self._embedding_backends: Dict[
            str, Callable[["KernelBase"], EmbeddingGeneratorBase]
        ] = {}

        self._default_text_backend: Optional[str] = None
        self._default_chat_backend: Optional[str] = None
        self._default_embedding_backend: Optional[str] = None

        self._retry_mechanism: RetryMechanism = PassThroughWithoutRetry()

    def get_ai_backend(
        self, type: Type[T], service_id: Optional[str] = None
    ) -> Callable[["KernelBase"], T]:
        matching_type = {}
        if type == TextCompletionClientBase:
            service_id = service_id or self._default_text_backend
            matching_type = self._text_backends
        elif type == ChatCompletionClientBase:
            service_id = service_id or self._default_chat_backend
            matching_type = self._chat_backends
        elif type == EmbeddingGeneratorBase:
            service_id = service_id or self._default_embedding_backend
            matching_type = self._embedding_backends
        else:
            raise ValueError(f"Unknown backend type: {type.__name__}")

        if service_id not in matching_type:
            raise ValueError(
                f"{type.__name__} backend with service_id '{service_id}' not found"
            )

        return matching_type[service_id]

    def all_text_backends(self) -> List[str]:
        return list(self._text_backends.keys())

    def all_chat_backends(self) -> List[str]:
        return list(self._chat_backends.keys())

    def all_embedding_backends(self) -> List[str]:
        return list(self._embedding_backends.keys())

    def add_text_backend(
        self,
        service_id: str,
        backend: Union[
            TextCompletionClientBase, Callable[["KernelBase"], TextCompletionClientBase]
        ],
        overwrite: bool = True,
    ) -> "KernelConfig":
        if not service_id:
            raise ValueError("service_id must be a non-empty string")
        if not overwrite and service_id in self._text_backends:
            raise ValueError(
                f"Text backend with service_id '{service_id}' already exists"
            )

        self._text_backends[service_id] = (
            backend if isinstance(backend, Callable) else lambda _: backend
        )
        if self._default_text_backend is None:
            self._default_text_backend = service_id

        return self

    def add_chat_backend(
        self,
        service_id: str,
        backend: Union[
            ChatCompletionClientBase, Callable[["KernelBase"], ChatCompletionClientBase]
        ],
        overwrite: bool = True,
    ) -> "KernelConfig":
        if not service_id:
            raise ValueError("service_id must be a non-empty string")
        if not overwrite and service_id in self._chat_backends:
            raise ValueError(
                f"Chat backend with service_id '{service_id}' already exists"
            )

        self._chat_backends[service_id] = (
            backend if isinstance(backend, Callable) else lambda _: backend
        )
        if self._default_chat_backend is None:
            self._default_chat_backend = service_id

        return self

    def add_embedding_backend(
        self,
        service_id: str,
        backend: Union[
            EmbeddingGeneratorBase, Callable[["KernelBase"], EmbeddingGeneratorBase]
        ],
        overwrite: bool = False,
    ) -> "KernelConfig":
        if not service_id:
            raise ValueError("service_id must be a non-empty string")
        if not overwrite and service_id in self._embedding_backends:
            raise ValueError(
                f"Embedding backend with service_id '{service_id}' already exists"
            )

        self._embedding_backends[service_id] = (
            backend if isinstance(backend, Callable) else lambda _: backend
        )
        if self._default_embedding_backend is None:
            self._default_embedding_backend = service_id

        return self

    # TODO: look harder at retry stuff

    def set_default_text_backend(self, service_id: str) -> "KernelConfig":
        if service_id not in self._text_backends:
            raise ValueError(
                f"AI backend with service_id '{service_id}' does not exist"
            )

        self._default_text_backend = service_id
        return self

    def set_default_chat_backend(self, service_id: str) -> "KernelConfig":
        if service_id not in self._chat_backends:
            raise ValueError(
                f"AI backend with service_id '{service_id}' does not exist"
            )

        self._default_chat_backend = service_id
        return self

    def set_default_embedding_backend(self, service_id: str) -> "KernelConfig":
        if service_id not in self._embedding_backends:
            raise ValueError(
                f"AI backend with service_id '{service_id}' does not exist"
            )

        self._default_embedding_backend = service_id
        return self

    def get_text_backend_service_id(self, service_id: Optional[str] = None) -> str:
        if service_id is None or service_id not in self._text_backends:
            if self._default_text_backend is None:
                raise ValueError("No default text backend is set")
            return self._default_text_backend

        return service_id

    def get_chat_backend_service_id(self, service_id: Optional[str] = None) -> str:
        if service_id is None or service_id not in self._chat_backends:
            if self._default_chat_backend is None:
                raise ValueError("No default chat backend is set")
            return self._default_chat_backend

        return service_id

    def get_embedding_backend_service_id(self, service_id: Optional[str] = None) -> str:
        if service_id is None or service_id not in self._embedding_backends:
            if self._default_embedding_backend is None:
                raise ValueError("No default embedding backend is set")
            return self._default_embedding_backend

        return service_id

    def remove_text_backend(self, service_id: str) -> "KernelConfig":
        if service_id not in self._text_backends:
            raise ValueError(
                f"AI backend with service_id '{service_id}' does not exist"
            )

        del self._text_backends[service_id]
        if self._default_text_backend == service_id:
            self._default_text_backend = next(iter(self._text_backends), None)
        return self

    def remove_chat_backend(self, service_id: str) -> "KernelConfig":
        if service_id not in self._chat_backends:
            raise ValueError(
                f"AI backend with service_id '{service_id}' does not exist"
            )

        del self._chat_backends[service_id]
        if self._default_chat_backend == service_id:
            self._default_chat_backend = next(iter(self._chat_backends), None)
        return self

    def remove_embedding_backend(self, service_id: str) -> "KernelConfig":
        if service_id not in self._embedding_backends:
            raise ValueError(
                f"AI backend with service_id '{service_id}' does not exist"
            )

        del self._embedding_backends[service_id]
        if self._default_embedding_backend == service_id:
            self._default_embedding_backend = next(iter(self._embedding_backends), None)
        return self

    def clear_all_text_backends(self) -> "KernelConfig":
        self._text_backends = {}
        self._default_text_backend = None
        return self

    def clear_all_chat_backends(self) -> "KernelConfig":
        self._chat_backends = {}
        self._default_chat_backend = None
        return self

    def clear_all_embedding_backends(self) -> "KernelConfig":
        self._embedding_backends = {}
        self._default_embedding_backend = None
        return self

    def clear_all_backends(self) -> "KernelConfig":
        self._text_backends = {}
        self._chat_backends = {}
        self._embedding_backends = {}

        self._default_text_backend = None
        self._default_chat_backend = None
        self._default_embedding_backend = None

        return self
