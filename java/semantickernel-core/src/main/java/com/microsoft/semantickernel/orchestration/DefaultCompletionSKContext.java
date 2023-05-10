// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import com.microsoft.semantickernel.textcompletion.CompletionSKContext;

import java.util.function.Supplier;

import javax.annotation.Nullable;

public class DefaultCompletionSKContext extends ImmutableSKContext<CompletionSKContext>
        implements CompletionSKContext {

    DefaultCompletionSKContext(ReadOnlyContextVariables variables) {
        super(variables);
    }

    public DefaultCompletionSKContext(
            ReadOnlyContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable Supplier<ReadOnlySkillCollection> skills) {
        super(variables, memory, skills);
    }

    @Override
    public CompletionSKContext build(
            ReadOnlyContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable Supplier<ReadOnlySkillCollection> skills) {
        return new DefaultCompletionSKContext(variables, memory, skills);
    }
}
