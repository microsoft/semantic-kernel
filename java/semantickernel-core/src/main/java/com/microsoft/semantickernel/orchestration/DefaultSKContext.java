// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.SKBuilders;
<<<<<<< HEAD
=======
import com.microsoft.semantickernel.memory.NullMemory;
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import javax.annotation.Nullable;

public class DefaultSKContext extends AbstractSKContext {
<<<<<<< HEAD

    protected DefaultSKContext(SKContext toClone, String errorDescription, Exception exception) {
        super(toClone, errorDescription, exception);
    }

=======
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
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
        private SemanticTextMemory memory;

        @Override
<<<<<<< HEAD
        public SKContext failed(SKContext toClone, String errorDescription, Exception exception) {
            return new DefaultSKContext(toClone, errorDescription, exception);
        }

        @Override
=======
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
        public SKContext build() {
            if (variables == null) {
                variables = SKBuilders.variables().build();
            }
            return new DefaultSKContext(variables, memory, skills);
        }

        @Override
        public SKContext.Builder withVariables(ContextVariables variables) {
            this.variables = variables;
            return this;
        }

        @Override
        public SKContext.Builder withSkills(@Nullable ReadOnlySkillCollection skills) {
            if (skills != null) {
                this.skills = skills;
            }
            return this;
        }

        @Override
        public SKContext.Builder withMemory(@Nullable SemanticTextMemory memory) {
            if (memory != null) {
                this.memory = memory.copy();
            }
            return this;
        }

        @Override
        public SKContext.Builder clone(SKContext context) {
            return withVariables(context.getVariables())
                    .withSkills(context.getSkills())
                    .withMemory(context.getSemanticMemory());
        }

        @Override
        public SKContext.Builder withKernel(Kernel kernel) {
            if (memory == null) {
                memory = kernel.getMemory();
            }
            if (skills == null) {
                skills = kernel.getSkills();
            }
            if (variables == null) {
                variables = SKBuilders.variables().build();
            }
            return this;
        }
    }
}
