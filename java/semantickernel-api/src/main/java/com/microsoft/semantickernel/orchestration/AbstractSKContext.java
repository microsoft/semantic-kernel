// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import javax.annotation.CheckReturnValue;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** Semantic Kernel context */
public abstract class AbstractSKContext implements SKContext {

    private final ReadOnlySkillCollection skills;
    private final WritableContextVariables variables;
    @Nullable private final SemanticTextMemory memory;

    /** Whether an error occurred while executing functions in the pipeline. */
    private boolean errorOccurred;

    /** When an error occurs, this is the description of the error. */
    private String lastErrorDescription = "";

    /** When an error occurs, this is the most recent exception. */
    @Nullable private Exception lastException;

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

    protected AbstractSKContext(SKContext toClone, String errorDescription, Exception exception) {
        this(toClone.getVariables(), toClone.getSemanticMemory(), toClone.getSkills());
        this.errorOccurred = true;
        this.lastErrorDescription = errorDescription;
        this.lastException = exception;
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
    public SKContext setVariable(@Nonnull String key, @Nonnull String content) {
        variables.setVariable(key, content);
        return getThis();
    }

    @Override
    public SKContext appendToVariable(@Nonnull String key, @Nonnull String content) {
        variables.appendToVariable(key, content);
        return getThis();
    }

    @Override
    public SKContext update(@Nonnull String content) {
        variables.update(content);
        return getThis();
    }

    @Override
    public SKContext update(@Nonnull ContextVariables newData) {
        variables.update(newData, true);
        return getThis();
    }

    protected abstract SKContext getThis();

    public boolean isErrorOccurred() {
        return errorOccurred;
    }

    public String getLastErrorDescription() {
        return lastErrorDescription;
    }

    @Nullable
    public Exception getLastException() {
        return new Exception(lastException);
    }
}
