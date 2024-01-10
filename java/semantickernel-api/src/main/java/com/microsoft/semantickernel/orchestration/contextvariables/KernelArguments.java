// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration.contextvariables;

// Copyright (c) Microsoft. All rights reserved.

import com.microsoft.semantickernel.builders.Buildable;
import com.microsoft.semantickernel.builders.SemanticKernelBuilder;
import com.microsoft.semantickernel.orchestration.PromptExecutionSettings;
import java.util.Map;
import javax.annotation.Nullable;

/**
 * Context Variables is a data structure that holds temporary data while a task is being performed.
 * It is accessed by functions in the pipeline.
 */
public interface KernelArguments extends Buildable, Map<String, ContextVariable<?>> {

    /**
     * Default key for the main input
     */
    String MAIN_KEY = "input";

    /**
     * Get a clone of the variables that can be modified
     *
     * @return Writable clone of the variables
     */
    WritableKernelArguments writableClone();

    /**
     * Get the input (entry in the MAIN_KEY slot)
     *
     * @return input
     */
    @Nullable
    ContextVariable<?> getInput();

    /**
     * Create formatted string of the variables
     *
     * @return formatted string
     */
    String prettyPrint();

    /**
     * Return the variable with the given name
     *
     * @param key variable name
     * @return content of the variable
     */
    @Nullable
    <T extends ContextVariable<?>> T get(String key);

    /**
     * Return the variable with the given name
     *
     * @param key variable name
     * @return content of the variable
     */
    @Nullable
    <T> ContextVariable<T> get(String key, Class<T> clazz);

    @Nullable
    PromptExecutionSettings getExecutionSettings();

    static Builder builder() {
        return new DefaultKernelArguments.Builder();
    }

    boolean isNullOrEmpty(String key);

    /**
     * Builder for ContextVariables
     */
    interface Builder extends SemanticKernelBuilder<KernelArguments> {

        /**
         * Builds an instance with the given content in the default main key
         *
         * @param content Entry to place in the "input" slot
         * @return an instantiation of ContextVariables
         */
        <T> Builder withInput(ContextVariable<T> content);

        /**
         * Builds an instance with the given content in the default main key
         *
         * @param content Entry to place in the "input" slot
         * @return an instantiation of ContextVariables
         */
        Builder withInput(Object content);

        /**
         * Builds an instance with the given variables
         *
         * @param map Existing variables
         * @return an instantiation of ContextVariables
         */
        Builder withVariables(Map<String, ContextVariable<?>> map);

        /**
         * Set variable
         *
         * @param key   variable name
         * @param value variable value
         * @return builder for fluent chaining
         */
        <T> Builder withVariable(String key, ContextVariable<T> value);

        /**
         * Set variable
         *
         * @param key   variable name
         * @param value variable value
         * @return builder for fluent chaining
         */
        Builder withVariable(String key, Object value);
    }
}
