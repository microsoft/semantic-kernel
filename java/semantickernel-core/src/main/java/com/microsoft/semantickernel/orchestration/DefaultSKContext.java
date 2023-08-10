// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.memory.NullMemory;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import javax.annotation.Nullable;

public class DefaultSKContext extends AbstractSKContext {
    public DefaultSKContext(ContextVariables variables) {
        super(variables);
    }

    public DefaultSKContext(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skillCollection) {
        super(variables, memory, skillCollection);
    }

    @Override
    protected SKContext getThis() {
        return this;
    }

    @Override
    public SKContext build(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skillCollection) {
        return new DefaultSKContext(variables, memory, skillCollection);
    }

    public static class Builder implements SKContext.Builder {

        private ContextVariables variables;
        private ReadOnlySkillCollection skills;
        private SemanticTextMemory memory = NullMemory.getInstance();

        @Override
        public SKContext build(ReadOnlySkillCollection skills) {
            return new DefaultSKContext(
                    SKBuilders.variables().build(), NullMemory.getInstance(), skills);
        }

        @Override
        public SKContext build() {
            if (variables == null) {
                variables = SKBuilders.variables().build();
            }
            return new DefaultSKContext(variables, memory, skills);
        }

        @Override
        public SKContext build(Class<? extends SKContext> clazz) {
            return null;
        }

        @Override
        public SKContext.Builder with(ContextVariables variables) {
            this.variables = variables;
            return this;
        }

        @Override
        public SKContext.Builder with(@Nullable ReadOnlySkillCollection skills) {
            if (skills != null) {
                this.skills = skills;
            }
            return this;
        }

        @Override
        public SKContext.Builder with(@Nullable SemanticTextMemory memory) {
            if (memory != null) {
                this.memory = memory.copy();
            }
            return this;
        }

        @Override
        public SKContext.Builder clone(SKContext context) {
            return with(context.getVariables())
                    .with(context.getSkills())
                    .with(context.getSemanticMemory());
        }

        @Override
        public SKContext build(Kernel kernel) {
            if (memory == null) {
                memory = kernel.getMemory();
            }
            if (skills == null) {
                skills = kernel.getSkills();
            }
            if (variables == null) {
                variables = SKBuilders.variables().build();
            }
            return build();
        }
    }
}
