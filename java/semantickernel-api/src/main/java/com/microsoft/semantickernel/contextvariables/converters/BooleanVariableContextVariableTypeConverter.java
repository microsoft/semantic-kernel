// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.contextvariables.converters;

import static com.microsoft.semantickernel.contextvariables.ContextVariableTypes.convert;

import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;

/**
 * A {@link ContextVariableTypeConverter} for {@link Boolean} variables. Use
 * {@code ContextVariableTypes.getDefaultVariableTypeForClass(Boolean.class)} to get an instance of
 * this class.
 *
 * @see ContextVariableTypes#getGlobalVariableTypeForClass(Class)
 */
public class BooleanVariableContextVariableTypeConverter extends
    ContextVariableTypeConverter<Boolean> {

    /**
     * Initializes a new instance of the {@link BooleanVariableContextVariableTypeConverter} class.
     */
    public BooleanVariableContextVariableTypeConverter() {
        super(
            Boolean.class,
            s -> convert(s, Boolean.class),
            Object::toString,
            Boolean::parseBoolean);
    }

}
