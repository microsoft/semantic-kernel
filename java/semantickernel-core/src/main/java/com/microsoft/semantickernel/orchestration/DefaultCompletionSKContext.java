// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.textcompletion.CompletionSKContext;

import javax.annotation.Nullable;

public class DefaultCompletionSKContext extends AbstractSKContext<CompletionSKContext>
        implements CompletionSKContext {

    DefaultCompletionSKContext(ContextVariables variables) {
        super(variables);
    }

    public DefaultCompletionSKContext(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skills) {
        super(variables, memory, skills);
    }

    @Override
    protected CompletionSKContext getThis() {
        return this;
    }

    @Override
    public CompletionSKContext build(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skills) {
        return new DefaultCompletionSKContext(variables, memory, skills);
    }
}
