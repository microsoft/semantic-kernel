# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Callable, Optional

from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_config import KernelConfig
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
        if config is None:
            raise ValueError("The configuration instance cannot be `None`")
        self._config = config
        return self

    def with_memory(self, memory: SemanticTextMemoryBase) -> "KernelBuilder":
        if memory is None:
            raise ValueError("The memory instance cannot be `None`")
        self._memory = memory
        return self

    def with_memory_storage(self, storage: MemoryStoreBase) -> "KernelBuilder":
        if storage is None:
            raise ValueError("The memory storage instance cannot be `None`")
        self._memory_storage = storage
        return self

    def with_logger(self, log: Logger) -> "KernelBuilder":
        if log is None:
            raise ValueError("The logger instance cannot be `None`")
        self._log = log
        return self

    def configure(
        self, config_func: Callable[[KernelConfig], KernelConfig]
    ) -> "KernelBuilder":
        self._config = config_func(self._config)
        return self

    def build(self) -> Kernel:
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
    ) -> Kernel:
        builder = KernelBuilder(KernelConfig(), NullMemory(), NullLogger())

        if config is not None:
            builder = builder.with_configuration(config)

        if log is not None:
            builder = builder.with_logger(log)

        if memory is not None:
            builder = builder.with_memory(memory)

        return builder.build()
