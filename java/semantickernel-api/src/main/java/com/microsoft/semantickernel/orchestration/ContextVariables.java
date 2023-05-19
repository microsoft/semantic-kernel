// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration;

// Copyright (c) Microsoft. All rights reserved.

import java.util.Map;

import javax.annotation.CheckReturnValue;
import javax.annotation.Nullable;

/**
 * Context Variables is a data structure that holds temporary data while a task is being performed.
 * It is accessed by functions in the pipeline.
 */
public interface ContextVariables {

    String MAIN_KEY = "input";

    Map<String, String> asMap();

    @CheckReturnValue
    WritableContextVariables writableClone();

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
