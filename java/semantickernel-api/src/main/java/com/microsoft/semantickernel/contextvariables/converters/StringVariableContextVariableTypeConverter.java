// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.contextvariables.converters;

import static com.microsoft.semantickernel.contextvariables.ContextVariableTypes.convert;

import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;

/**
 * A {@link ContextVariableTypeConverter} for {@code java.lang.String} variables. Use
 * {@code ContextVariableTypes.getGlobalVariableTypeForClass(String.class)} to get an instance of
 * this class.
 *
 * @see ContextVariableTypes#getGlobalVariableTypeForClass(Class)
 */
public class StringVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<String> {

    /**
     * Creates a new instance of the {@link StringVariableContextVariableTypeConverter} class.
     */
    public StringVariableContextVariableTypeConverter() {
        super(
            String.class,
            s -> convert(s, String.class),
            Object::toString,
            s -> s);
    }
}
