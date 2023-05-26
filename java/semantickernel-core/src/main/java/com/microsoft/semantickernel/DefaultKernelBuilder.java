// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.memory.MemoryStore;
import com.microsoft.semantickernel.memory.VolatileMemoryStore;
import com.microsoft.semantickernel.templateengine.DefaultPromptTemplateEngine;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;

import javax.annotation.Nullable;

public class DefaultKernelBuilder implements Kernel.InternalBuilder {

    @Override
    public Kernel build(
            KernelConfig kernelConfig,
            @Nullable PromptTemplateEngine promptTemplateEngine,
            @Nullable MemoryStore memoryStore) {
        if (promptTemplateEngine == null) {
            promptTemplateEngine = new DefaultPromptTemplateEngine();
        }

        if (kernelConfig == null) {
            throw new IllegalArgumentException();
        }
        if (memoryStore == null) {
            memoryStore = new VolatileMemoryStore();
        }

        return new DefaultKernel(kernelConfig, promptTemplateEngine, memoryStore);
    }
}
