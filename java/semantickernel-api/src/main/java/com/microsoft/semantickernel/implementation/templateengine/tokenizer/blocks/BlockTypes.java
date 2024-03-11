// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.implementation.templateengine.tokenizer.blocks;

/**
 * Block types
 */
public enum BlockTypes {
    /**
     * Undefined block type
     */
    UNDEFINED,
    /**
     * Text block type
     */
    TEXT,
    /**
     * Code block type
     */
    CODE,
    /**
     * Variable block type
     */
    VARIABLE,
    /**
     * Value block type
     */
    VALUE,
    /**
     * Function block type
     */
    FUNCTION_ID,
    /**
     * Named argument block type
     */
    NAMED_ARG;
}
