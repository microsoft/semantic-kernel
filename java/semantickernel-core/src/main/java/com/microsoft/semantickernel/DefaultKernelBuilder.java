// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.memory.MemoryStore;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.memory.VolatileMemoryStore;
import com.microsoft.semantickernel.templateengine.DefaultPromptTemplateEngine;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;

import javax.annotation.Nullable;

public class DefaultKernelBuilder implements Kernel.InternalBuilder {

    @Override
    public Kernel build(
            KernelConfig kernelConfig,
            @Nullable PromptTemplateEngine promptTemplateEngine,
            @Nullable SemanticTextMemory memory,
            @Nullable MemoryStore memoryStore) {

        return new DefaultKernel.Builder()
                .build(kernelConfig, promptTemplateEngine, memory, memoryStore);
    }
}
