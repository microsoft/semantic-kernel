# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Callable, Optional

from semantic_kernel.configuration.kernel_config import KernelConfig
from semantic_kernel.diagnostics.verify import Verify
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_base import KernelBase
from semantic_kernel.kernel_extensions import KernelExtensions
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.skill_definition.skill_collection import SkillCollection
from semantic_kernel.template_engine.prompt_template_engine import PromptTemplateEngine
from semantic_kernel.utils.null_logger import NullLogger


class KernelBuilder:
    _config: KernelConfig
    _memory: SemanticTextMemoryBase
    _memory_storage: Optional[MemoryStoreBase]
    _log: Logger

    def __init__(
        self, config: KernelConfig, memory: SemanticTextMemoryBase, log: Logger
    ) -> None:
        self._config = config
        self._memory = memory
        self._memory_storage = None
        self._log = log

    def with_configuration(self, config: KernelConfig) -> "KernelBuilder":
        Verify.not_null(config, "The configuration instance provided is None")
        self._config = config
        return self

    def with_memory(self, memory: SemanticTextMemoryBase) -> "KernelBuilder":
        Verify.not_null(memory, "The memory instance provided is None")
        self._memory = memory
        return self

    def with_memory_storage(self, storage: MemoryStoreBase) -> "KernelBuilder":
        Verify.not_null(storage, "The memory storage instance provided is None")
        self._memory_storage = storage
        return self

    def with_logger(self, log: Logger) -> "KernelBuilder":
        Verify.not_null(log, "The logger instance provided is None")
        self._log = log
        return self

    def configure(
        self, config_func: Callable[[KernelConfig], KernelConfig]
    ) -> "KernelBuilder":
        self._config = config_func(self._config)
        return self

    def build(self) -> KernelBase:
        instance = Kernel(
            SkillCollection(self._log),
            PromptTemplateEngine(self._log),
            self._memory,
            self._config,
            self._log,
        )

        if self._memory_storage is not None:
            KernelExtensions.use_memory(instance, self._memory_storage)

        return instance

    @staticmethod
    def create_kernel(
        config: Optional[KernelConfig] = None,
        log: Optional[Logger] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
    ) -> KernelBase:
        builder = KernelBuilder(KernelConfig(), NullMemory(), NullLogger())

        if config is not None:
            builder = builder.with_configuration(config)

        if log is not None:
            builder = builder.with_logger(log)

        if memory is not None:
            builder = builder.with_memory(memory)

        return builder.build()
