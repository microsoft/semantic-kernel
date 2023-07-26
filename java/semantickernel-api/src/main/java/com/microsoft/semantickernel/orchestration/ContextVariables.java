// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

// Copyright (c) Microsoft. All rights reserved.

import java.util.Map;

import javax.annotation.Nullable;

/**
 * Context Variables is a data structure that holds temporary data while a task is being performed.
 * It is accessed by functions in the pipeline.
 */
public interface ContextVariables {

    /** Default key for the main input */
    String MAIN_KEY = "input";

    /**
     * Get variables as a map
     *
     * @return Map of variables
     */
    Map<String, String> asMap();

    /**
     * Get a clone of the variables that can be modified
     *
     * @return Writable clone of the variables
     */
    WritableContextVariables writableClone();

    /**
     * Get the input (entry in the MAIN_KEY slot)
     *
     * @return input
     */
    @Nullable
    String getInput();

    /**
     * Create formatted string of the variables
     *
     * @return formatted string
     */
    String prettyPrint();

    /** Builder for ContextVariables */
    interface Builder {
        ContextVariables build();

        /**
         * Builds an instance with the given content in the default main key
         *
         * @param content Entry to place in the "input" slot
         * @return an instantiation of ContextVariables
         */
        ContextVariables build(String content);

        /**
         * Builds an instance with the given variables
         *
         * @param map Existing varibles
         * @return an instantiation of ContextVariables
         */
        ContextVariables build(Map<String, String> map);

        /**
         * Builds a mutable instance with the given variables
         *
         * @return an instantiation of ContextVariables
         */
        WritableContextVariables buildWritable();

        /**
         * Set variable
         *
         * @param key variable name
         * @param value variable value
         * @return builder for fluent chaining
         */
        Builder setVariable(String key, String value);
    }

    /**
     * Return the variable with the given name
     *
     * @param key variable name
     * @return content of the variable
     */
    @Nullable
    String get(String key);
}
