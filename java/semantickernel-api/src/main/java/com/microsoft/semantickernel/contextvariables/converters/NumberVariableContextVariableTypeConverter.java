// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.contextvariables.converters;

import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypes;
import java.util.function.Function;

/**
 * A {@link ContextVariableTypeConverter} for {@code java.lang.Number} type variables. Use, for
 * example, {@code ContextVariableTypes.getGlobalVariableTypeForClass(Integer.class)} to get an
 * instance of this class that works with the {@code Integer} type.
 *
 * @param <T> the type of the number
 * @see ContextVariableTypes#getGlobalVariableTypeForClass(Class)
 */
public class NumberVariableContextVariableTypeConverter<T extends Number> extends
    PrimitiveVariableContextVariableTypeConverter<T> {

    /**
     * Creates a new instance of the {@link NumberVariableContextVariableTypeConverter} class.
     *
     * @param clazz            the class
     * @param fromPromptString the function to convert from a prompt string
     * @param fromNumber       the function to convert from a number
     */
    public NumberVariableContextVariableTypeConverter(
        Class<T> clazz,
        Function<String, T> fromPromptString,
        Function<Number, T> fromNumber) {
        super(
            clazz,
            fromPromptString,
            num -> {
                if (num instanceof Number) {
                    return fromNumber.apply((Number) num);
                } else {
                    return null;
                }
            },
            Number::toString);
    }

}
