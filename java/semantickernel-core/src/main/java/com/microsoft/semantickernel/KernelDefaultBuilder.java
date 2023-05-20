// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.templateengine.DefaultPromptTemplateEngine;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;

import javax.annotation.Nullable;

public class KernelDefaultBuilder implements Kernel.InternalBuilder {

    @Override
    public Kernel build(
            KernelConfig kernelConfig, @Nullable PromptTemplateEngine promptTemplateEngine) {
        if (promptTemplateEngine == null) {
            promptTemplateEngine = new DefaultPromptTemplateEngine();
        }

        if (kernelConfig == null) {
            throw new IllegalArgumentException();
        }

        return new KernelDefault(kernelConfig, promptTemplateEngine, null);
    }
}
