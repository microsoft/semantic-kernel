# Copyright (c) Microsoft. All rights reserved.

from typing import Callable, Dict, List, Optional

from semantic_kernel.ai.open_ai.services.azure_open_ai_config import AzureOpenAIConfig
from semantic_kernel.ai.open_ai.services.open_ai_config import OpenAIConfig
from semantic_kernel.configuration.backend_config import BackendConfig
from semantic_kernel.configuration.backend_types import BackendType
from semantic_kernel.diagnostics.verify import Verify
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.reliability.pass_through_without_retry import (
    PassThroughWithoutRetry,
)
from semantic_kernel.reliability.retry_mechanism import RetryMechanism


class KernelConfig:
    _completion_backends: Dict[str, BackendConfig] = {}
    _embeddings_backends: Dict[str, BackendConfig] = {}
    _default_completion_backend: Optional[str] = None
    _default_embeddings_backend: Optional[str] = None
    _retry_mechanism: RetryMechanism = PassThroughWithoutRetry()

    def add_azure_openai_completion_backend(
        self,
        name: str,
        deployment_name: str,
        endpoint: str,
        api_key: str,
        api_version: str = "2022-12-01",
        overwrite: bool = False,
    ) -> "KernelConfig":
        Verify.not_empty(name, "The backend name is empty")

        if not overwrite and name in self._completion_backends:
            raise KernelException(
                KernelException.ErrorCodes.InvalidBackendConfiguration,
                f"The completion backend cannot be added twice: {name}",
            )

        self._completion_backends[name] = BackendConfig(
            backend_type=BackendType.AzureOpenAI,
            azure_open_ai=AzureOpenAIConfig(
                deployment_name, endpoint, api_key, api_version
            ),
        )

        if self._default_completion_backend is None:
            self._default_completion_backend = name

        return self

    def add_openai_completion_backend(
        self,
        name: str,
        model_id: str,
        api_key: str,
        org_id: Optional[str] = None,
        overwrite: bool = False,
    ) -> "KernelConfig":
        Verify.not_empty(name, "The backend name is empty")

        if not overwrite and name in self._completion_backends:
            raise KernelException(
                KernelException.ErrorCodes.InvalidBackendConfiguration,
                f"The completion backend cannot be added twice: {name}",
            )

        self._completion_backends[name] = BackendConfig(
            backend_type=BackendType.OpenAI,
            open_ai=OpenAIConfig(model_id, api_key, org_id),
        )

        if self._default_completion_backend is None:
            self._default_completion_backend = name

        return self

    def add_azure_open_ai_embeddings_backend(
        self,
        name: str,
        deployment_name: str,
        endpoint: str,
        api_key: str,
        api_version: str = "2022-12-01",
        overwrite: bool = False,
    ) -> "KernelConfig":
        Verify.not_empty(name, "The backend name is empty")

        if not overwrite and name in self._embeddings_backends:
            raise KernelException(
                KernelException.ErrorCodes.InvalidBackendConfiguration,
                f"The embeddings backend cannot be added twice: {name}",
            )

        self._embeddings_backends[name] = BackendConfig(
            backend_type=BackendType.AzureOpenAI,
            azure_open_ai=AzureOpenAIConfig(
                deployment_name, endpoint, api_key, api_version
            ),
        )

        if self._default_embeddings_backend is None:
            self._default_embeddings_backend = name

        return self

    def add_open_ai_embeddings_backend(
        self,
        name: str,
        model_id: str,
        api_key: str,
        org_id: Optional[str] = None,
        overwrite: bool = False,
    ) -> "KernelConfig":
        Verify.not_empty(name, "The backend name is empty")

        if not overwrite and name in self._embeddings_backends:
            raise KernelException(
                KernelException.ErrorCodes.InvalidBackendConfiguration,
                f"The embeddings backend cannot be added twice: {name}",
            )

        self._embeddings_backends[name] = BackendConfig(
            backend_type=BackendType.OpenAI,
            open_ai=OpenAIConfig(model_id, api_key, org_id),
        )

        if self._default_embeddings_backend is None:
            self._default_embeddings_backend = name

        return self

    def has_completion_backend(
        self, name: str, condition: Optional[Callable[[BackendConfig], bool]] = None
    ) -> bool:
        if condition is None:
            return name in self._completion_backends

        return any(
            [name == n and condition(v) for n, v in self._completion_backends.items()]
        )

    def has_embeddings_backend(
        self, name: str, condition: Optional[Callable[[BackendConfig], bool]] = None
    ) -> bool:
        if condition is None:
            return name in self._embeddings_backends

        return any(
            [name == n and condition(v) for n, v in self._embeddings_backends.items()]
        )

    def set_retry_mechanism(
        self, retry_mechanism: Optional[RetryMechanism]
    ) -> "KernelConfig":
        self._retry_mechanism = (
            retry_mechanism
            if retry_mechanism is not None
            else PassThroughWithoutRetry()
        )
        return self

    def set_default_completion_backend(self, name: str) -> "KernelConfig":
        if name not in self._completion_backends:
            raise KernelException(
                KernelException.ErrorCodes.BackendNotFound,
                f"The completions backend doesn't exist: {name}",
            )

        self._default_completion_backend = name
        return self

    @property
    def default_completion_backend(self) -> Optional[str]:
        return self._default_completion_backend

    def set_default_embeddings_backend(self, name: str) -> "KernelConfig":
        if name not in self._embeddings_backends:
            raise KernelException(
                KernelException.ErrorCodes.BackendNotFound,
                f"The embeddings backend doesn't exist: {name}",
            )

        self._default_embeddings_backend = name
        return self

    @property
    def default_embeddings_backend(self) -> Optional[str]:
        return self._default_embeddings_backend

    def get_completion_backend(self, name: Optional[str]) -> BackendConfig:
        if name is None or name.strip() == "":
            if self._default_completion_backend is None:
                raise KernelException(
                    KernelException.ErrorCodes.BackendNotFound,
                    f"Completion backend not found: {name}. "
                    f"No default backend available.",
                )

            return self._completion_backends[self._default_completion_backend]

        if name in self._completion_backends:
            return self._completion_backends[name]

        if self._default_completion_backend is not None:
            return self._completion_backends[self._default_completion_backend]

        raise KernelException(
            KernelException.ErrorCodes.BackendNotFound,
            f"Completion backend not found: {name}. " f"No default backend available.",
        )

    def get_embeddings_backend(self, name: Optional[str]) -> BackendConfig:
        if name is None or name.strip() == "":
            if self._default_embeddings_backend is None:
                raise KernelException(
                    KernelException.ErrorCodes.BackendNotFound,
                    f"Embeddings backend not found: {name}. "
                    f"No default backend available.",
                )

            return self._embeddings_backends[self._default_embeddings_backend]

        if name in self._embeddings_backends:
            return self._embeddings_backends[name]

        if self._default_embeddings_backend is not None:
            return self._embeddings_backends[self._default_embeddings_backend]

        raise KernelException(
            KernelException.ErrorCodes.BackendNotFound,
            f"Embeddings backend not found: {name}. " f"No default backend available.",
        )

    def get_all_completion_backends(self) -> List[BackendConfig]:
        return list(self._completion_backends.values())

    def get_all_embeddings_backends(self) -> List[BackendConfig]:
        return list(self._embeddings_backends.values())

    def remove_completion_backend(self, name: str) -> None:
        if name in self._completion_backends:
            del self._completion_backends[name]

        if name == self._default_completion_backend:
            self._default_completion_backend = (
                list(self._completion_backends.keys())[0]
                if len(self._completion_backends) > 0
                else None
            )

    def remove_embeddings_backend(self, name: str) -> None:
        if name in self._embeddings_backends:
            del self._embeddings_backends[name]

        if name == self._default_embeddings_backend:
            self._default_embeddings_backend = (
                list(self._embeddings_backends.keys())[0]
                if len(self._embeddings_backends) > 0
                else None
            )

    def remove_all_completion_backends(self) -> None:
        self._completion_backends.clear()
        self._default_completion_backend = None

    def remove_all_embeddings_backends(self) -> None:
        self._embeddings_backends.clear()
        self._default_embeddings_backend = None

    def remove_all_backends(self) -> None:
        self.remove_all_completion_backends()
        self.remove_all_embeddings_backends()
