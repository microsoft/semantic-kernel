// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import reactor.util.annotation.NonNull;
import reactor.util.annotation.Nullable;

import java.util.Collections;

import javax.annotation.CheckReturnValue;

/// <summary>
/// Semantic Kernel context.
/// </summary>memory
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
        return SKBuilders.variables().build(Collections.unmodifiableMap(variables.asMap()));
    }

    AbstractSKContext(ContextVariables variables) {
        this(variables, null, null);
    }

    /// <summary>
    /// Constructor for the context.
    /// </summary>
    /// <param name="variables">Context variables to include in context.</param>
    /// <param name="memory">Semantic text memory unit to include in context.</param>
    /// <param name="skills">Skills to include in context.</param>
    /// <param name="logger">Logger for operations in context.</param>
    /// <param name="cancellationToken">Optional cancellation token for operations in
    // context.</param>
    protected AbstractSKContext(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skills) {
        this.variables = InternalBuildersSingleton.variables().build(variables.asMap());

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

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// </summary>
    /// <param name="content">The new input value, for the next function in the pipeline, or as a
    // result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
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
