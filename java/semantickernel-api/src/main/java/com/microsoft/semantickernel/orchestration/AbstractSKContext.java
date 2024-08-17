// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import javax.annotation.CheckReturnValue;
<<<<<<< AI
=======
<<<<<<< HEAD
>>>>>>> main
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/** Semantic Kernel context */
public abstract class AbstractSKContext implements SKContext {

<<<<<<< AI
=======
=======
>>>>>>> main
import reactor.util.annotation.NonNull;
import reactor.util.annotation.Nullable;

/** Semantic Kernel context */
public abstract class AbstractSKContext implements SKContext {
<<<<<<< AI
=======
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
>>>>>>> main
    private final ReadOnlySkillCollection skills;
    private final WritableContextVariables variables;
    @Nullable private final SemanticTextMemory memory;

<<<<<<< AI
=======
<<<<<<< HEAD
>>>>>>> main
    /** Whether an error occurred while executing functions in the pipeline. */
    private boolean errorOccurred;

    /** When an error occurs, this is the description of the error. */
    private String lastErrorDescription = "";

    /** When an error occurs, this is the most recent exception. */
    @Nullable private Exception lastException;

<<<<<<< AI
=======
=======
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
>>>>>>> main
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

<<<<<<< AI
=======
<<<<<<< HEAD
>>>>>>> main
    protected AbstractSKContext(SKContext toClone, String errorDescription, Exception exception) {
        this(toClone.getVariables(), toClone.getSemanticMemory(), toClone.getSkills());
        this.errorOccurred = true;
        this.lastErrorDescription = errorDescription;
        this.lastException = exception;
    }

<<<<<<< AI
=======
=======
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
>>>>>>> main
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
<<<<<<< AI
    public SKContext setVariable(@Nonnull String key, @Nonnull String content) {
    public SKContext setVariable(@NonNull String key, @NonNull String content) {
=======
<<<<<<< HEAD
    public SKContext setVariable(@Nonnull String key, @Nonnull String content) {
=======
    public SKContext setVariable(@NonNull String key, @NonNull String content) {
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
>>>>>>> main
        variables.setVariable(key, content);
        return getThis();
    }

    @Override
<<<<<<< AI
    public SKContext appendToVariable(@Nonnull String key, @Nonnull String content) {
    public SKContext appendToVariable(@NonNull String key, @NonNull String content) {
=======
<<<<<<< HEAD
    public SKContext appendToVariable(@Nonnull String key, @Nonnull String content) {
=======
    public SKContext appendToVariable(@NonNull String key, @NonNull String content) {
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
>>>>>>> main
        variables.appendToVariable(key, content);
        return getThis();
    }

    @Override
<<<<<<< AI
    public SKContext update(@Nonnull String content) {
    public SKContext update(@NonNull String content) {
=======
<<<<<<< HEAD
    public SKContext update(@Nonnull String content) {
=======
    public SKContext update(@NonNull String content) {
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
>>>>>>> main
        variables.update(content);
        return getThis();
    }

    @Override
<<<<<<< AI
    public SKContext update(@Nonnull ContextVariables newData) {
    public SKContext update(@NonNull ContextVariables newData) {
=======
<<<<<<< HEAD
    public SKContext update(@Nonnull ContextVariables newData) {
=======
    public SKContext update(@NonNull ContextVariables newData) {
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
>>>>>>> main
        variables.update(newData, true);
        return getThis();
    }

    protected abstract SKContext getThis();
<<<<<<< AI
=======
<<<<<<< HEAD
>>>>>>> main

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
<<<<<<< AI
=======
=======
>>>>>>> beeed7b7a795d8c989165740de6ddb21aeacbb6f
>>>>>>> main
}
