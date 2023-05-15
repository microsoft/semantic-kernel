// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import java.util.function.Supplier;

import javax.annotation.Nullable;

public class DefaultSemanticSKContext extends AbstractSKContext<SemanticSKContext>
        implements SemanticSKContext {
    public DefaultSemanticSKContext(ContextVariables variables) {
        super(variables);
    }

    public DefaultSemanticSKContext(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable Supplier<ReadOnlySkillCollection> skills) {
        super(variables, memory, skills);
    }

    @Override
    public SemanticSKContext build(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable Supplier<ReadOnlySkillCollection> skills) {
        return new DefaultSemanticSKContext(variables, memory, skills);
    }
}
