// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

import java.util.Map;

/**
 * Context Variables is a data structure that holds temporary data while a task is being performed.
 * It is accessed by functions in the pipeline.
 */
public interface WritableContextVariables extends ContextVariables {

    /**
     * Set the value
     *
     * @param key variable name
     * @param content value to set
     * @return Context for fluent calls
     */
    ContextVariables setVariable(String key, String content);

    ContextVariables appendToVariable(String key, String content);

    /// <summary>
    /// Updates the main input text with the new value after a function is complete.
    /// </summary>
    /// <param name="content">The new input value, for the next function in the pipeline, or as a
    // result for the user
    /// if the pipeline reached the end.</param>
    /// <returns>The current instance</returns>
    ContextVariables update(String content);

    ContextVariables update(ContextVariables newData, boolean merge);

    ContextVariables remove(String key);

    interface Builder {
        /**
         * Builds an instance with the given variables
         *
         * @param map Existing varibles
         * @return an instantiation of ContextVariables
         */
        WritableContextVariables build(Map<String, String> map);
    }
}
