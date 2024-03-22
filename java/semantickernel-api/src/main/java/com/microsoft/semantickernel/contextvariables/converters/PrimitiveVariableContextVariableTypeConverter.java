// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.contextvariables.converters;

import static com.microsoft.semantickernel.contextvariables.ContextVariableTypes.convert;

import com.microsoft.semantickernel.contextvariables.ContextVariable;
import com.microsoft.semantickernel.contextvariables.ContextVariableTypeConverter;
import java.util.function.Function;
import javax.annotation.Nullable;

/**
 * A {@link ContextVariableTypeConverter} for primative variables.
 */
public class PrimitiveVariableContextVariableTypeConverter<T> extends
    ContextVariableTypeConverter<T> {

    private final Function<Object, T> fromObject;

    /**
     * Creates a new instance of the {@link PrimitiveVariableContextVariableTypeConverter} class.
     *
     * @param clazz            the class
     * @param fromPromptString the function to convert from a prompt string
     * @param fromObject       the function to convert from an object to primative
     */
    public PrimitiveVariableContextVariableTypeConverter(
        Class<T> clazz,
        Function<String, T> fromPromptString,
        Function<Object, T> fromObject,
        Function<T, String> toPromptString) {
        super(
            clazz,
            s -> convert(s, clazz),
            toPromptString,
            fromPromptString);
        this.fromObject = fromObject;
    }

    @Override
    @Nullable
    public <U> U toObject(@Nullable Object t, Class<U> clazz) {
        if (t == null) {
            return null;
        }

        // Let the parent class have a crack at it first
        // since someone may have installed a special converter. 
        U obj = super.toObject(t, clazz);
        if (obj != null) {
            return obj;
        }
        // If the type is a string, and the object is of the same type as the
        // converter, then we can convert with the toPromptString method.
        if (clazz == String.class && t.getClass() == super.getType()) {
            return clazz.cast(toPromptString(getType().cast(t)));
        }
        return null;
    }

    @Override
    @Nullable
    public T fromObject(@Nullable Object s) {
        if (s instanceof ContextVariable) {
            s = ((ContextVariable) s).getValue();
        }

        T obj = super.fromObject(s);
        if (obj != null) {
            return obj;
        }

        try {
            T result = fromObject.apply(s);
            if (result != null) {
                return result;
            }
        } catch (Exception e) {
            // ignore
        }

        if (s instanceof String) {
            return fromPromptString((String) s);
        }
        return null;
    }

    @Override
    @Nullable
    public T fromPromptString(@Nullable String s) {
        if (s != null && !s.isEmpty()) {
            return super.fromPromptString(s);
        }
        return null;
    }

}
