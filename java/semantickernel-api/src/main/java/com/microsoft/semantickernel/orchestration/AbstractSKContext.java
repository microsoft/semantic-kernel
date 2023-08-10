// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import javax.annotation.CheckReturnValue;
import reactor.util.annotation.NonNull;
import reactor.util.annotation.Nullable;

/** Semantic Kernel context */
public abstract class AbstractSKContext implements SKContext {
    private final ReadOnlySkillCollection skills;
    private final WritableContextVariables variables;
    @Nullable private final SemanticTextMemory memory;

    @Nullable
    @Override
    public String getResult() {
        return getVariables().asMap().get(ContextVariables.MAIN_KEY);
    }

    /// <summary>
    /// User variables
    /// </summary>
    @Override
    public ContextVariables getVariables() {
        return SKBuilders.variables().withVariables(variables.asMap()).build();
    }

    AbstractSKContext(ContextVariables variables) {
        this(variables, null, null);
    }

    /**
     * Constructor for the context.
     *
     * @param variables Context variables to include in context.
     * @param memory Semantic text memory unit to include in context.
     * @param skills Skills to include in context.
     */
    protected AbstractSKContext(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skills) {
        this.variables =
                SKBuilders.variables().withVariables(variables.asMap()).build().writableClone();

        if (memory != null) {
            this.memory = memory.copy();
        } else {
            this.memory = null;
        }

        if (skills == null) {
            this.skills = SKBuilders.skillCollection().build();
        } else {
            this.skills = skills;
        }
    }

    @CheckReturnValue
    @Override
    public SKContext copy() {
        ReadOnlySkillCollection clonedSkill;
        if (skills == null) {
            clonedSkill = null;
        } else {
            clonedSkill = skills.copy();
        }
        return build(variables.writableClone(), memory, clonedSkill);
    }

    @Nullable
    @Override
    public SemanticTextMemory getSemanticMemory() {
        return memory != null ? memory.copy() : null;
    }

    @Override
    public ReadOnlySkillCollection getSkills() {
        return skills;
    }

    @Override
    public SKContext setVariable(@NonNull String key, @NonNull String content) {
        variables.setVariable(key, content);
        return getThis();
    }

    @Override
    public SKContext appendToVariable(@NonNull String key, @NonNull String content) {
        variables.appendToVariable(key, content);
        return getThis();
    }

    @Override
    public SKContext update(@NonNull String content) {
        variables.update(content);
        return getThis();
    }

    @Override
    public SKContext update(@NonNull ContextVariables newData) {
        variables.update(newData, true);
        return getThis();
    }

    protected abstract SKContext getThis();
}
