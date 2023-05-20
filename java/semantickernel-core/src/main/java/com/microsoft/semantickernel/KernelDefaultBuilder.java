// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel;

import com.microsoft.semantickernel.skilldefinition.DefaultSkillCollection;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.templateengine.DefaultPromptTemplateEngine;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;

import javax.annotation.Nullable;

public class KernelDefaultBuilder implements Kernel.InternalBuilder {

    @Override
    public Kernel build(
            KernelConfig kernelConfig,
            @Nullable PromptTemplateEngine promptTemplateEngine,
            @Nullable ReadOnlySkillCollection skillCollection) {
        if (promptTemplateEngine == null) {
            promptTemplateEngine = new DefaultPromptTemplateEngine();
        }

        if (skillCollection == null) {
            skillCollection = new DefaultSkillCollection();
        }

        if (kernelConfig == null) {
            throw new IllegalArgumentException();
        }

        return new KernelDefault(kernelConfig, promptTemplateEngine, skillCollection);
    }
}
