// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration.contextvariables;

import java.util.Map;

/**
 * Context Variables is a data structure that holds temporary data while a task is being performed.
 * It is accessed by functions in the pipeline.
 */
public interface WritableKernelArguments extends KernelArguments {

    /**
     * Set the value
     *
     * @param key     variable name
     * @param content value to set
     * @return Context for fluent calls
     */
    KernelArguments setVariable(String key, ContextVariable<?> content);

    KernelArguments setVariable(String key, Object content);

    /**
     * Updates the main input text with the new value after a function is complete.
     *
     * @param content The new input value, for the next function in the pipeline, or as a result for
     *                the user if the pipeline reached the end.
     * @return The current instance
     */
    KernelArguments update(ContextVariable<?> content);

    KernelArguments update(String content);

    /**
     * Updates the variables merging or overwriting in the new values.
     *
     * @param newData Data to merge or overwrite.
     * @param merge   Whether to merge the new data with the existing data or to replace it
     * @return The current instance
     */
    KernelArguments update(KernelArguments newData, boolean merge);

    KernelArguments remove(String key);

    interface Builder {

        /**
         * Builds an instance with the given variables
         *
         * @param map Existing variables
         * @return an instantiation of ContextVariables
         */
        WritableKernelArguments build(Map<String, ContextVariable<?>> map);
    }
}
