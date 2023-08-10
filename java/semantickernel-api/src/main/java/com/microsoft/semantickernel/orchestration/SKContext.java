// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import com.microsoft.semantickernel.Kernel;
import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.BuildersSingleton;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;
import javax.annotation.CheckReturnValue;
import reactor.util.annotation.Nullable;

/** Semantic Kernel context. */
public interface SKContext extends Buildable {

    SKContext build(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable ReadOnlySkillCollection skills);

    /**
     * Obtain the result of the execution that produced this context. This will be the "input" entry
     * in the variables.
     *
     * @return the "input" entry in the variables
     */
    @Nullable
    String getResult();

    /**
     * Return a copy of all variables within the context
     *
     * @return a clone of the variables
     */
    ContextVariables getVariables();

    /**
     * Provides access to the context's semantic memory
     *
     * @return the semantic memory
     */
    @Nullable
    SemanticTextMemory getSemanticMemory();

    /**
     * Provides access to the skills within this context
     *
     * @return the skills
     */
    ReadOnlySkillCollection getSkills();

    /**
     * Sets the given variable
     *
     * @param key if null defaults to the "input" key
     * @param content value to set
     * @return Context for fluent calls
     */
    SKContext setVariable(String key, String content);

    /**
     * Appends data to the given key
     *
     * @param key key to set
     * @param content value to set
     * @return Context for fluent calls
     */
    SKContext appendToVariable(String key, String content);

    /**
     * Updates the input entry with the given data
     *
     * @param content value to set
     * @return Context for fluent calls
     */
    @CheckReturnValue
    SKContext update(String content);

    /**
     * Merges in the given variables. Duplicate keys provided by newData will overwrite existing
     * entries.
     *
     * @param newData variables to merge in
     * @return Context for fluent calls
     */
    @CheckReturnValue
    SKContext update(ContextVariables newData);

    /**
     * Clones the context
     *
     * @return a copy of this context
     */
    SKContext copy();

    static Builder builder() {
        return BuildersSingleton.INST.getInstance(SKContext.Builder.class);
    }

    interface Builder extends SemanticKernelBuilder<SKContext> {

        Builder setVariables(ContextVariables variables);

        /**
         * Sets the skills
         *
         * @param skills null argument will be ignored
         * @return Context for fluent calls
         */
        Builder setSkills(@Nullable ReadOnlySkillCollection skills);

        /**
         * Sets the memory
         *
         * @param memory null argument will be ignored
         * @return Context for fluent calls
         */
        Builder setMemory(@Nullable SemanticTextMemory memory);

        Builder clone(SKContext context);

        /**
         * Builds a context from the given kernel. If not explicitly set, the skills and memory will
         * be used from the kernel.
         *
         * @param kernel Kernel to use
         * @return Context
         */
        Builder withKernel(Kernel kernel);
    }
}
