// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.memory.NullMemory;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import javax.annotation.Nullable;

public class DefaultSemanticSKContext extends AbstractSKContext<SemanticSKContext>
        implements SemanticSKContext {
    public DefaultSemanticSKContext(ContextVariables variables) {
        super(variables);
    }

    public DefaultSemanticSKContext(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skillCollection) {
        super(variables, memory, skillCollection);
    }

    @Override
    protected SemanticSKContext getThis() {
        return this;
    }

    @Override
    public SemanticSKContext build(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skillCollection) {
        return new DefaultSemanticSKContext(variables, memory, skillCollection);
    }

    public static class Builder implements SKContext.Builder {

        @Override
        public SKContext build(ReadOnlySkillCollection skills) {
            return new DefaultSemanticSKContext(
                    SKBuilders.variables().build(), NullMemory.getInstance(), skills);
        }
    }
}
